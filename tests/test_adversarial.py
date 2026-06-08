"""Adversarial URL test suite (B2).

Loads data/adversarial_urls.csv and verifies the model detects >= 70% of
hand-crafted evasion URLs. Individual tests are parametrized so failures
show exactly which URL and technique broke.

Requires a trained model (models/ensemble.pkl). The test is skipped if the
model is not available so that the suite stays green on fresh clones without
a trained model.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "backend"))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

_CSV = _REPO / "data" / "adversarial_urls.csv"
_MODEL = _REPO / "models" / "ensemble.pkl"

SCORE_THRESHOLD = 0.50
SUITE_DETECTION_RATE = 0.70  # overall gate


def _load_cases() -> list[tuple[str, str, str]]:
    if not _CSV.exists():
        return []
    with _CSV.open(newline="", encoding="utf-8") as f:
        return [
            (row["url"], row.get("expected_label", "phishing"), row.get("evasion_technique", "unknown"))
            for row in csv.DictReader(f)
        ]


_CASES = _load_cases()


@pytest.fixture(scope="module")
def scorer():
    if not _MODEL.exists():
        pytest.skip("No trained model found — skipping adversarial tests")
    from app.ml.loader import load_scorer
    return load_scorer()


@pytest.mark.parametrize("url,expected,technique", _CASES, ids=[c[2] + "_" + str(i) for i, c in enumerate(_CASES)])
def test_adversarial_url_detected(scorer, url: str, expected: str, technique: str):
    """Each adversarial URL should be detected as phishing."""
    result = scorer.score(url)
    label = result.get("label", "unknown")
    score = float(result.get("score", 0.0))
    detected = (label == "phishing") or (score >= SCORE_THRESHOLD)
    assert detected, (
        f"Missed {technique}: url={url!r} got label={label!r} score={score:.3f}"
    )


def test_adversarial_overall_detection_rate(scorer):
    """Overall detection rate must be >= 70%."""
    cases = _load_cases()
    if not cases:
        pytest.skip("No adversarial CSV found")

    detected = 0
    for url, _, __ in cases:
        result = scorer.score(url)
        label = result.get("label", "unknown")
        score = float(result.get("score", 0.0))
        if label == "phishing" or score >= SCORE_THRESHOLD:
            detected += 1

    rate = detected / len(cases)
    assert rate >= SUITE_DETECTION_RATE, (
        f"Adversarial detection rate {rate:.1%} < {SUITE_DETECTION_RATE:.0%} gate "
        f"({detected}/{len(cases)} detected)"
    )
