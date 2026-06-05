"""Tests for the committed INDEPENDENT real-world phishing holdout.

The load-bearing guarantee is `test_real_holdout_zero_train_host_overlap`: the
holdout's recall is only an honest generalisation number if NONE of its hosts
are seen during training. This is a pure-file check — no model, no network — so
it runs deterministically in offline CI.
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

from ml_pipeline.config import (
    GENERIC_HOLDOUT_CSV,
    GENERIC_PHISH_SEED_CSV,
    REAL_HOLDOUT_CSV,
    THAI_HOLDOUT_CSV,
    THAI_PHISH_SEED_CSV,
)


def _hosts(path: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    out: set[str] = set()
    for row in csv.DictReader(p.open(encoding="utf-8")):
        h = (urlparse(row["url"]).hostname or "").lower().removeprefix("www.")
        if h:
            out.add(h)
    return out


def test_real_holdout_committed_and_well_formed():
    p = Path(REAL_HOLDOUT_CSV)
    assert p.exists(), "committed independent real-world holdout is missing"
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) >= 50, f"real holdout too small ({len(rows)})"
    for r in rows:
        assert r["url"].startswith(("http://", "https://"))
        assert r["label"] == "1"


def test_real_holdout_zero_train_host_overlap():
    holdout = _hosts(REAL_HOLDOUT_CSV)
    assert holdout, "real holdout has no parseable hosts"
    for corpus in (
        GENERIC_PHISH_SEED_CSV,
        THAI_PHISH_SEED_CSV,
        GENERIC_HOLDOUT_CSV,
        THAI_HOLDOUT_CSV,
    ):
        overlap = holdout & _hosts(corpus)
        assert not overlap, (
            f"independent holdout shares {len(overlap)} host(s) with "
            f"{Path(corpus).name}: {sorted(overlap)[:5]} — it is no longer "
            "an independent generalisation check"
        )


def test_real_holdout_hosts_unique():
    # One host must not dominate the sample (the collector de-dups by host).
    rows = list(csv.DictReader(Path(REAL_HOLDOUT_CSV).open(encoding="utf-8")))
    hosts = [
        (urlparse(r["url"]).hostname or "").lower().removeprefix("www.")
        for r in rows
    ]
    assert len(hosts) == len(set(hosts)), "duplicate hosts in real holdout"
