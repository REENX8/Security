"""Tests for score telemetry + shadow threshold A/B (C10)."""
from __future__ import annotations

from app import threshold_ab
from app.metrics import THRESHOLD_AB
from app.threshold_ab import label_for, record_score_telemetry


def test_label_for_boundaries():
    assert label_for(0.05, 0.3, 0.7) == "safe"
    assert label_for(0.3, 0.3, 0.7) == "suspicious"
    assert label_for(0.69, 0.3, 0.7) == "suspicious"
    assert label_for(0.7, 0.3, 0.7) == "phishing"


def _ab_value(variant: str, label: str) -> float:
    return THRESHOLD_AB.labels(variant=variant, label=label)._value.get()


def test_ab_disabled_records_no_ab_counter(monkeypatch):
    monkeypatch.setattr(threshold_ab.settings, "enable_threshold_ab", False)
    before = _ab_value("a", "phishing")
    record_score_telemetry(0.95)  # should only touch the histogram
    assert _ab_value("a", "phishing") == before


def test_ab_enabled_counts_both_variants(monkeypatch):
    monkeypatch.setattr(threshold_ab.settings, "enable_threshold_ab", True)
    monkeypatch.setattr(threshold_ab.settings, "threshold_suspicious", 0.3)
    monkeypatch.setattr(threshold_ab.settings, "threshold_phishing", 0.7)
    # Candidate B is stricter: a 0.65 score is "suspicious" under A but
    # "phishing" under B.
    monkeypatch.setattr(threshold_ab.settings, "threshold_suspicious_candidate", 0.3)
    monkeypatch.setattr(threshold_ab.settings, "threshold_phishing_candidate", 0.6)

    a_susp = _ab_value("a", "suspicious")
    b_phish = _ab_value("b", "phishing")
    record_score_telemetry(0.65)
    assert _ab_value("a", "suspicious") == a_susp + 1
    assert _ab_value("b", "phishing") == b_phish + 1


def test_bad_score_is_ignored(monkeypatch):
    monkeypatch.setattr(threshold_ab.settings, "enable_threshold_ab", False)
    # Should not raise on a non-numeric score.
    record_score_telemetry(None)  # type: ignore[arg-type]
