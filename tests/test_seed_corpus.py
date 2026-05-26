"""Sanity checks on the curated Thai-targeting phishing seed corpus.

These guard against regressions that would silently degrade the primary
evaluation metric -- e.g. one over-represented brand dominating the holdout.
"""

from __future__ import annotations

import collections
import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = ROOT / "data" / "thai_phishing_seed.csv"
PER_BRAND_CAP = 8
MIN_TOTAL_ROWS = 200
MIN_DISTINCT_BRANDS = 50


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    assert SEED_CSV.exists(), f"missing {SEED_CSV}"
    with SEED_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_seed_corpus_has_minimum_size(rows):
    assert len(rows) >= MIN_TOTAL_ROWS, (
        f"seed corpus shrunk to {len(rows)} rows (min {MIN_TOTAL_ROWS}); "
        "wide CI on Thai-targeting recall metric is the risk"
    )


def test_seed_corpus_covers_many_brands(rows):
    brands = {r["target_brand"] for r in rows if r.get("target_brand")}
    assert len(brands) >= MIN_DISTINCT_BRANDS, (
        f"only {len(brands)} distinct brands in seed corpus "
        f"(min {MIN_DISTINCT_BRANDS}); broader coverage prevents overfit"
    )


def test_no_brand_exceeds_per_brand_cap(rows):
    counts = collections.Counter(
        r["target_brand"] for r in rows if r.get("target_brand")
    )
    over = {b: n for b, n in counts.items() if n > PER_BRAND_CAP}
    assert not over, (
        f"brands over cap of {PER_BRAND_CAP}: {over} -- holdout will "
        "over-weight these brands and inflate the recall metric"
    )


def test_every_row_is_phishing_label(rows):
    # The seed CSV is all-phishing by construction; a row with label != 1
    # would silently pollute the legitimate side of training.
    labels = {r.get("label") for r in rows}
    assert labels == {"1"}, (
        f"seed corpus has non-phishing labels: {labels} (expected only '1')"
    )


def test_seed_urls_have_valid_scheme(rows):
    bad = [r["url"] for r in rows if not r["url"].startswith(("http://", "https://"))]
    assert not bad, f"rows with non-http(s) URL slipped in: {bad[:5]}"
