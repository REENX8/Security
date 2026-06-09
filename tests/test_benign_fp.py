"""Benign false-positive gate.

Scores a curated corpus of real, legitimate websites (data/benign_holdout.csv)
through the FULL pipeline (model + rules) and asserts none are blocked as
phishing. Several entries deliberately resemble risky patterns — login/signin
subdomains, deep subdomains, credential keywords in the path — to stress the
false-positive surface.

WHOIS/TLS are off in the test environment, so this exercises the conservative
fail-open path (no domain-age / CA-cert signal to vouch for the host); the
trusted-brand safe-guard rule must hold the line without them.

Skipped if the trained model is unavailable so fresh clones stay green.
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
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("ENABLE_WHOIS", "false")
os.environ.setdefault("ENABLE_TLS", "false")

_CSV = _REPO / "data" / "benign_holdout.csv"
_MODEL = _REPO / "models" / "ensemble.pkl"

# Hard gate: legitimate sites must NEVER be blocked as phishing.
MAX_PHISHING_FP = 0
# Soft gate: a small number of "suspicious" warnings is tolerable, but a flood
# would mean the warning band is mis-tuned against real sites.
MAX_SUSPICIOUS_RATE = 0.15


def _load() -> list[tuple[str, str]]:
    if not _CSV.exists():
        return []
    with _CSV.open(newline="", encoding="utf-8") as f:
        return [(r["url"], r.get("category", "")) for r in csv.DictReader(f)]


_CASES = _load()


@pytest.fixture(scope="module")
def scorer():
    if not _MODEL.exists():
        pytest.skip("No trained model found — skipping benign FP gate")
    from app.ml.loader import load_scorer
    return load_scorer()


@pytest.mark.parametrize("url,category", _CASES, ids=[f"{c}_{i}" for i, (_, c) in enumerate(_CASES)])
def test_benign_url_not_blocked(scorer, url: str, category: str):
    """No individual legitimate URL may be labelled phishing."""
    result = scorer.score(url)
    assert result["label"] != "phishing", (
        f"FALSE POSITIVE [{category}]: {url} blocked as phishing "
        f"(score={result['score']:.3f})"
    )


def test_benign_overall_false_positive_rate(scorer):
    cases = _load()
    if not cases:
        pytest.skip("No benign CSV found")

    phishing = 0
    suspicious = 0
    for url, _ in cases:
        label = scorer.score(url)["label"]
        if label == "phishing":
            phishing += 1
        elif label == "suspicious":
            suspicious += 1

    assert phishing <= MAX_PHISHING_FP, (
        f"{phishing} legitimate site(s) blocked as phishing (gate {MAX_PHISHING_FP})"
    )
    susp_rate = suspicious / len(cases)
    assert susp_rate <= MAX_SUSPICIOUS_RATE, (
        f"suspicious rate {susp_rate:.0%} on benign sites exceeds "
        f"{MAX_SUSPICIOUS_RATE:.0%}"
    )
