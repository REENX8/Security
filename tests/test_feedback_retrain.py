"""Tests for feedback-driven model retrain pipeline."""
from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ml_pipeline.feedback_retrain import (
    MIN_ROWS_FOR_RETRAIN,
    _retrain,
    _write_csv,
    run,
)


def _rows(n: int) -> list[dict]:
    return [
        {"url": f"https://phish{i}.xyz/login", "label": "1", "source": "feedback"}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _write_csv
# ---------------------------------------------------------------------------

def test_write_csv_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("ml_pipeline.feedback_retrain.FEEDBACK_CSV", tmp_path / "f.csv")
    import ml_pipeline.feedback_retrain as mod
    mod.FEEDBACK_CSV = tmp_path / "f.csv"
    _write_csv(_rows(3))
    lines = list(csv.DictReader((tmp_path / "f.csv").open()))
    assert len(lines) == 3
    assert lines[0]["label"] == "1"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_no_rows_returns_true():
    with patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=[])):
        assert run(since_days=1) is True


def test_run_below_min_skips_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN - 1)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain") as mock_rt,
    ):
        result = run(since_days=1)
    mock_rt.assert_not_called()
    assert result is True


def test_run_dry_run_skips_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain") as mock_rt,
    ):
        result = run(since_days=1, dry_run=True)
    mock_rt.assert_not_called()
    assert result is True


def test_run_triggers_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain", return_value=True) as mock_rt,
    ):
        result = run(since_days=1)
    mock_rt.assert_called_once()
    assert result is True


def test_run_propagates_retrain_failure():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain", return_value=False),
    ):
        result = run(since_days=1)
    assert result is False


def test_run_respects_higher_min_rows():
    # 7 rows but accumulation threshold of 20 -> skip (no-op success).
    rows = _rows(7)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain") as mock_rt,
    ):
        result = run(since_days=1, min_rows=20)
    mock_rt.assert_not_called()
    assert result is True


def test_run_passes_enforce_gate_through():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain", return_value=True) as mock_rt,
    ):
        run(since_days=1, enforce_gate=False)
    mock_rt.assert_called_once_with(enforce_gate=False)


# ---------------------------------------------------------------------------
# staging -> gate -> promote
# ---------------------------------------------------------------------------

def _seed_staging(mod, tmp_path):
    """Point the live/staging/backup dirs at tmp_path and seed staged files."""
    live = tmp_path / "models"
    staging = tmp_path / "models" / "staging"
    backup = tmp_path / "models" / "previous"
    live.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    mod.LIVE_MODELS_DIR = live
    mod.STAGING_MODELS_DIR = staging
    mod.BACKUP_MODELS_DIR = backup
    for name in mod._PROMOTE_FILES:
        (staging / name).write_text(f"new-{name}")
        (live / name).write_text(f"old-{name}")
    return live, staging, backup


def test_promote_swaps_and_backs_up(tmp_path):
    import ml_pipeline.feedback_retrain as mod

    live, staging, backup = _seed_staging(mod, tmp_path)
    assert mod._promote() is True
    for name in mod._PROMOTE_FILES:
        assert (live / name).read_text() == f"new-{name}"   # promoted
        assert (backup / name).read_text() == f"old-{name}"  # rolled-back copy
    # no temp files left behind
    assert not list(live.glob(".*promoting"))


def test_promote_aborts_when_staged_artifact_missing(tmp_path):
    import ml_pipeline.feedback_retrain as mod

    live, staging, _ = _seed_staging(mod, tmp_path)
    (staging / "ensemble.pkl").unlink()  # one artifact missing
    assert mod._promote() is False
    # live model untouched
    assert (live / "ensemble.pkl").read_text() == "old-ensemble.pkl"


def test_retrain_promotes_when_all_steps_pass():
    with (
        patch("ml_pipeline.feedback_retrain._run_step", return_value=True) as step,
        patch("ml_pipeline.feedback_retrain._promote", return_value=True) as promote,
    ):
        assert _retrain(enforce_gate=True) is True
    promote.assert_called_once()
    # build_whitelist, collect_dataset, train, evaluate(--enforce-threshold)
    assert step.call_count == 4
    assert step.call_args_list[-1].args[0] == (
        "ml_pipeline.evaluate", "--enforce-threshold",
    )


def test_retrain_aborts_and_skips_promote_on_gate_failure():
    # evaluate (the 4th/last step) fails the gate -> no promote, rollback.
    def _fail_on_eval(module_args, env):
        return module_args[0] != "ml_pipeline.evaluate"

    with (
        patch("ml_pipeline.feedback_retrain._run_step", side_effect=_fail_on_eval),
        patch("ml_pipeline.feedback_retrain._promote") as promote,
    ):
        assert _retrain(enforce_gate=True) is False
    promote.assert_not_called()


# ---------------------------------------------------------------------------
# collect_dataset folds feedback into TRAINING (never the holdout)
# ---------------------------------------------------------------------------

class _StubGen:
    def sim_network(self, label, https):
        return {"whois_ok": 0, "tls_ok": 0}


def test_load_feedback_rows_filters_and_excludes_holdout(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd

    csv_path = tmp_path / "feedback_labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", "label", "source"])
        w.writeheader()
        w.writerows([
            {"url": "https://good.example/login", "label": "1", "source": "feedback"},
            {"url": "https://legit.example/", "label": "0", "source": "feedback"},
            {"url": "https://in-holdout.example/x", "label": "1", "source": "feedback"},
            {"url": "ftp://bad-scheme", "label": "1", "source": "feedback"},
            {"url": "https://nolabel.example/", "label": "", "source": "feedback"},
        ])
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(csv_path))

    rows = cd._load_feedback_rows(
        _StubGen(), exclude_urls={"https://in-holdout.example/x"}
    )
    urls = {r["url"] for r in rows}
    assert urls == {"https://good.example/login", "https://legit.example/"}
    assert all("whois_ok" in r and "label" in r for r in rows)


def test_load_feedback_rows_absent_file(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "missing.csv"))
    assert cd._load_feedback_rows(_StubGen(), exclude_urls=set()) == []
