"""Score telemetry + shadow threshold A/B (C10).

Every served score is recorded into a Prometheus histogram so the live score
distribution is observable (drift, threshold tuning). When threshold A/B is
enabled, the same score is also labelled under both the live (A) thresholds and
the candidate (B) thresholds, and both verdicts are counted — letting an
operator compare what a proposed threshold *would* have done against real
traffic without ever changing the verdict users see.
"""

from __future__ import annotations

from app.config import settings
from app.metrics import SCORE_DISTRIBUTION, THRESHOLD_AB


def label_for(score: float, threshold_suspicious: float, threshold_phishing: float) -> str:
    if score >= threshold_phishing:
        return "phishing"
    if score >= threshold_suspicious:
        return "suspicious"
    return "safe"


def record_score_telemetry(score: float) -> None:
    """Observe one served score, plus the shadow A/B comparison if enabled."""
    try:
        SCORE_DISTRIBUTION.observe(float(score))
    except (TypeError, ValueError):
        return

    if not settings.enable_threshold_ab:
        return

    label_a = label_for(
        score, settings.threshold_suspicious, settings.threshold_phishing
    )
    label_b = label_for(
        score,
        settings.threshold_suspicious_candidate,
        settings.threshold_phishing_candidate,
    )
    THRESHOLD_AB.labels(variant="a", label=label_a).inc()
    THRESHOLD_AB.labels(variant="b", label=label_b).inc()
