"""Tests for the docs metric-injection (de-hardcoding) script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def sd():
    spec = importlib.util.spec_from_file_location(
        "sync_docs_metrics", ROOT / "scripts" / "sync_docs_metrics.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_metrics_match_evaluation_summary(sd):
    import json

    m = sd.compute_metrics()
    summary = json.loads(sd.EVAL_JSON.read_text(encoding="utf-8"))
    n = summary["thai_targeting_holdout"]["sample_size"]
    assert m["thai_holdout_n"] == str(n)
    assert f"/{n})" in m["thai_recall"]
    # schema version + feature count come from the model metadata
    feats = json.loads(sd.FEATURES_JSON.read_text(encoding="utf-8"))
    assert m["schema_version"] == feats["schema_version"]


def test_generic_recall_is_optional(sd, tmp_path, monkeypatch):
    # When the feed-dependent generic holdout is absent it must not crash and
    # must render as n/a rather than a fabricated number.
    real = sd.json.loads(sd.EVAL_JSON.read_text(encoding="utf-8"))
    real["secondary_metrics"]["generic_real_holdout_recall"] = None
    real["secondary_metrics"]["generic_real_holdout_n"] = 0
    fake = tmp_path / "eval.json"
    fake.write_text(sd.json.dumps(real), encoding="utf-8")
    monkeypatch.setattr(sd, "EVAL_JSON", fake)
    assert "n/a" in sd.compute_metrics()["generic_recall"]


def test_apply_substitutes_known_sentinel(sd):
    text = "recall is <!--M:thai_recall-->OLD<!--/M--> today"
    out, unknown = sd._apply(text, {"thai_recall": "100% (378/378)"})
    assert out == "recall is <!--M:thai_recall-->100% (378/378)<!--/M--> today"
    assert unknown == []


def test_apply_flags_unknown_key(sd):
    out, unknown = sd._apply("<!--M:bogus-->x<!--/M-->", {"thai_recall": "y"})
    assert unknown == ["bogus"]


def test_docs_are_in_sync(sd):
    # The committed README sentinels must already match the committed metrics
    # (the same invariant CI enforces via `make sync-docs-check`).
    metrics = sd.compute_metrics()
    for path in sd.DOC_FILES:
        updated, _ = sd._apply(path.read_text(encoding="utf-8"), metrics)
        assert updated == path.read_text(encoding="utf-8"), f"{path} out of sync"
