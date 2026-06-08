"""Tests for A/B model comparison before promotion (v1.6.1)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def _seed_dirs(tmp_path, staged_recall, live_recall=None):
    staging_reports = tmp_path / "reports" / "staging"
    staging_reports.mkdir(parents=True, exist_ok=True)
    live_models = tmp_path / "models"
    live_models.mkdir(parents=True, exist_ok=True)

    (staging_reports / "thai_holdout_metrics.json").write_text(
        json.dumps({"recall_phishing_threshold": staged_recall})
    )
    if live_recall is not None:
        (live_models / "ensemble.pkl").write_bytes(b"fake")
        (live_models / "scaler.pkl").write_bytes(b"fake")
    return staging_reports, live_models


def _make_fake_evaluate_mod(live_recall):
    """Return a mock evaluate module that reports live_recall from _eval_holdout_csv."""
    mock_eval_mod = MagicMock()
    mock_eval_mod._eval_holdout_csv.return_value = {
        "recall_phishing_threshold": live_recall
    }
    return mock_eval_mod


def test_compare_blocks_promotion_on_regression(tmp_path, monkeypatch):
    """Staged model 3 pp worse than live → promotion blocked."""
    import ml_pipeline.feedback_retrain as mod

    staging_reports, live_models = _seed_dirs(tmp_path, staged_recall=0.80, live_recall=0.90)
    monkeypatch.setattr(mod, "STAGING_REPORTS_DIR", staging_reports)
    monkeypatch.setattr(mod, "LIVE_MODELS_DIR", live_models)

    fake_eval_mod = _make_fake_evaluate_mod(live_recall=0.90)
    with (
        patch("joblib.load", return_value=object()),
        patch.dict("sys.modules", {"ml_pipeline.evaluate": fake_eval_mod}),
    ):
        result = mod._compare_staged_vs_live()

    assert result is False


def test_compare_allows_promotion_when_within_margin(tmp_path, monkeypatch):
    """Staged model only 1 pp worse → within 2 pp margin, allow promotion."""
    import ml_pipeline.feedback_retrain as mod

    staging_reports, live_models = _seed_dirs(tmp_path, staged_recall=0.88, live_recall=0.89)
    monkeypatch.setattr(mod, "STAGING_REPORTS_DIR", staging_reports)
    monkeypatch.setattr(mod, "LIVE_MODELS_DIR", live_models)

    fake_eval_mod = _make_fake_evaluate_mod(live_recall=0.89)
    with (
        patch("joblib.load", return_value=object()),
        patch.dict("sys.modules", {"ml_pipeline.evaluate": fake_eval_mod}),
    ):
        result = mod._compare_staged_vs_live()

    assert result is True


def test_compare_allows_when_no_thai_holdout_metrics(tmp_path, monkeypatch):
    """No staged Thai holdout metrics file → skip comparison, allow promote."""
    import ml_pipeline.feedback_retrain as mod

    staging_reports = tmp_path / "reports" / "staging"
    staging_reports.mkdir(parents=True)
    monkeypatch.setattr(mod, "STAGING_REPORTS_DIR", staging_reports)

    result = mod._compare_staged_vs_live()
    assert result is True


def test_compare_allows_when_no_live_model(tmp_path, monkeypatch):
    """No live model artifacts → first-ever promote, allow unconditionally."""
    import ml_pipeline.feedback_retrain as mod

    staging_reports = tmp_path / "reports" / "staging"
    staging_reports.mkdir(parents=True)
    live_models = tmp_path / "models"
    live_models.mkdir(parents=True)
    (staging_reports / "thai_holdout_metrics.json").write_text(
        json.dumps({"recall_phishing_threshold": 0.92})
    )
    monkeypatch.setattr(mod, "STAGING_REPORTS_DIR", staging_reports)
    monkeypatch.setattr(mod, "LIVE_MODELS_DIR", live_models)

    result = mod._compare_staged_vs_live()
    assert result is True


def test_retrain_calls_ab_compare_before_promote():
    """_retrain must call _compare_staged_vs_live before _promote."""
    import ml_pipeline.feedback_retrain as mod

    call_order = []

    def _track_compare():
        call_order.append("compare")
        return True

    def _track_promote():
        call_order.append("promote")
        return True

    with (
        patch.object(mod, "_run_step", return_value=True),
        patch.object(mod, "_compare_staged_vs_live", side_effect=_track_compare),
        patch.object(mod, "_promote", side_effect=_track_promote),
    ):
        mod._retrain(enforce_gate=True)

    assert call_order == ["compare", "promote"]


def test_retrain_skips_promote_when_ab_blocks():
    """If A/B compare returns False, _promote must NOT be called."""
    import ml_pipeline.feedback_retrain as mod

    with (
        patch.object(mod, "_run_step", return_value=True),
        patch.object(mod, "_compare_staged_vs_live", return_value=False),
        patch.object(mod, "_promote") as mock_promote,
    ):
        result = mod._retrain(enforce_gate=True)

    assert result is False
    mock_promote.assert_not_called()
