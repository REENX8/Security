#!/usr/bin/env python3
"""Build ``data/real_phish_holdout.csv`` — an INDEPENDENT real-world phishing
holdout with **zero host overlap** against every training corpus.

Why a separate holdout? ``data/generic_phish_holdout.csv`` is a 30% split of the
*same* ``generic_phishing_seed.csv`` snapshot that also feeds training, so ~24%
of its hosts are seen during training. That makes its recall an optimistic,
in-distribution number. This script curates a *fresh* sample of real phishing
URLs and **drops any URL whose registered host already appears** in any training
corpus (``generic_phishing_seed.csv``, ``thai_phishing_seed.csv``,
``generic_phish_holdout.csv``, and ``dataset.csv`` when present). The result is a
genuine generalisation check: every host is novel to the model.

Like the other seed/holdout files, the URLs are used as eval DATA only — their
lexical/structural features are extracted, the sites are never crawled — so it
does not matter that the live pages decay over time. The output is committed so
CI never needs network at train/eval time.

Output schema: ``url,label,source,collected_at`` (label = 1 for every row).

Usage:
    python scripts/collect_real_phish_holdout.py            # fetch + write
    python scripts/collect_real_phish_holdout.py --max 100
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import random
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
HOLDOUT_CSV = os.path.join(DATA_DIR, "real_phish_holdout.csv")

# Training/eval corpora whose hosts the holdout must NOT overlap.
_TRAIN_CORPORA = (
    os.path.join(DATA_DIR, "generic_phishing_seed.csv"),
    os.path.join(DATA_DIR, "thai_phishing_seed.csv"),
    os.path.join(DATA_DIR, "generic_phish_holdout.csv"),
    os.path.join(DATA_DIR, "thai_phish_holdout.csv"),
    os.path.join(DATA_DIR, "dataset.csv"),  # generated; absent in a clean tree
)

_TIMEOUT = 20.0
_SEED = 42  # deterministic shuffle so the committed file is stable


def _host(url: str) -> str:
    """Registered host of a URL, lower-cased, ``www.`` stripped."""
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:  # noqa: BLE001
        return ""


def _is_thai_targeting(url: str) -> bool:
    u = url.lower()
    return ".th" in u or "thai" in u


def train_hosts() -> set[str]:
    """Collect every host present in the training/eval corpora."""
    hosts: set[str] = set()
    for path in _TRAIN_CORPORA:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                h = _host(row.get("url", ""))
                if h:
                    hosts.add(h)
    return hosts


def _fetch(max_urls: int, seen_hosts: set[str]) -> list[tuple[str, str]]:
    """Best-effort fetch of (url, source) pairs from public feeds, excluding any
    URL whose host is already in ``seen_hosts`` (the training corpora)."""
    try:
        import requests
    except Exception:  # noqa: BLE001
        print("[real-holdout] 'requests' not available", file=sys.stderr)
        return []

    out: list[tuple[str, str]] = []
    picked_hosts: set[str] = set()
    headers = {"User-Agent": "phish-detector-research/1.0"}

    def _add(url: str, source: str) -> None:
        url = url.strip()
        if not url.startswith(("http://", "https://")) or _is_thai_targeting(url):
            return
        h = _host(url)
        # Zero-overlap invariant: skip hosts seen in training, and de-dup the
        # holdout itself by host so one host can't dominate the sample.
        if not h or h in seen_hosts or h in picked_hosts:
            return
        picked_hosts.add(h)
        out.append((url, source))

    # OpenPhish (plain-text feed)
    try:
        resp = requests.get(
            "https://openphish.com/feed.txt", timeout=_TIMEOUT, headers=headers
        )
        if resp.ok:
            for line in resp.text.splitlines():
                _add(line, "openphish")
        print(f"[real-holdout] OpenPhish contributed {len(out)} novel-host URLs")
    except Exception as exc:  # noqa: BLE001
        print(f"[real-holdout] OpenPhish fetch failed: {exc}", file=sys.stderr)

    # URLhaus (best-effort)
    try:
        resp = requests.post(
            "https://urlhaus-api.abuse.ch/v1/urls/recent/", timeout=_TIMEOUT
        )
        if resp.ok and "json" in resp.headers.get("content-type", ""):
            before = len(out)
            for e in resp.json().get("urls", []):
                if e.get("url_status") == "online":
                    _add(e.get("url", ""), "urlhaus")
            print(f"[real-holdout] URLhaus contributed {len(out) - before} URLs")
    except Exception as exc:  # noqa: BLE001
        print(f"[real-holdout] URLhaus fetch skipped: {exc}", file=sys.stderr)

    random.Random(_SEED).shuffle(out)
    return out[:max_urls]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=100)
    parser.add_argument("--out", default=HOLDOUT_CSV)
    args = parser.parse_args()

    seen = train_hosts()
    print(f"[real-holdout] {len(seen)} hosts in training corpora to exclude")

    rows = _fetch(args.max, seen)
    if not rows:
        print("[real-holdout] no novel-host URLs fetched -- keeping existing file",
              file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["url", "label", "source", "collected_at"]
        )
        writer.writeheader()
        for url, source in sorted(rows):
            writer.writerow(
                {"url": url, "label": "1", "source": source, "collected_at": today}
            )
    print(f"[real-holdout] wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
