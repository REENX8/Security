"""Tests for the committed generic-phishing snapshot + its dataset wiring."""

from __future__ import annotations

import csv
from pathlib import Path

import ml_pipeline.collect_dataset as cd
from ml_pipeline.config import GENERIC_PHISH_SEED_CSV, GENERIC_TRAIN_MAX


def test_generic_seed_committed_and_well_formed():
    p = Path(GENERIC_PHISH_SEED_CSV)
    assert p.exists(), "committed generic phishing seed is missing"
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) >= 100, f"generic seed too small ({len(rows)})"
    for r in rows:
        assert r["url"].startswith(("http://", "https://"))
        assert r["label"] == "1"


def test_generic_seed_excludes_thai_targeting():
    rows = list(csv.DictReader(Path(GENERIC_PHISH_SEED_CSV).open(encoding="utf-8")))
    # The generic snapshot must not contain Thai-targeting URLs (those belong
    # to the Thai seed/holdout) — guards against train/eval cohort bleed.
    assert not [r for r in rows if ".th" in r["url"].lower()]


def test_load_generic_phish_seed_reads_urls():
    urls = cd._load_generic_phish_seed()
    assert urls and all(u.startswith(("http://", "https://")) for u in urls)


def test_generic_train_cap_is_positive():
    # The cap protects the Thai cohort's decision boundary; must be sane.
    assert isinstance(GENERIC_TRAIN_MAX, int) and GENERIC_TRAIN_MAX > 0
