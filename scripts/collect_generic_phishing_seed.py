#!/usr/bin/env python3
"""Build ``data/generic_phishing_seed.csv`` — a committed snapshot of real,
non-Thai-targeting phishing URLs from public feeds (OpenPhish / URLhaus).

Why a committed snapshot? The model is trained offline + deterministically
(``make train`` uses ``--no-feeds``). Without any real *generic* phishing in
the training set the model only learns Thai-brand-impersonation patterns and
is blind to generic phishing (measured recall ~57%). Folding a committed
snapshot of generic phishing into training lifts generic recall to ~99% while
keeping the build reproducible (no network at train time) and the Thai-holdout
recall at 100%.

The URLs are used as TRAINING/eval DATA only -- their lexical/structural
features are extracted, the sites are never crawled -- so it does not matter
that the live pages go offline over time.

Output schema: ``url,label,source,collected_at`` (label = 1 for every row).

Usage:
    python scripts/collect_generic_phishing_seed.py            # fetch + write
    python scripts/collect_generic_phishing_seed.py --max 1500
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
SEED_CSV = os.path.join(ROOT, "data", "generic_phishing_seed.csv")

_TIMEOUT = 20.0
_SEED = 42  # deterministic shuffle so the committed file is stable


def _is_thai_targeting(url: str) -> bool:
    """Exclude Thai-targeting URLs -- those belong to the Thai seed/holdout."""
    u = url.lower()
    if ".th" in u or "thai" in u:
        return True
    return False


def _fetch(max_urls: int) -> list[tuple[str, str]]:
    """Best-effort fetch of (url, source) pairs from public feeds."""
    try:
        import requests
    except Exception:  # noqa: BLE001
        print("[generic-seed] 'requests' not available", file=sys.stderr)
        return []

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    headers = {"User-Agent": "phish-detector-research/1.0"}

    def _add(url: str, source: str) -> None:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return
        if url in seen or _is_thai_targeting(url):
            return
        try:
            if not (urlparse(url).hostname or ""):
                return
        except Exception:  # noqa: BLE001
            return
        seen.add(url)
        out.append((url, source))

    # OpenPhish (plain-text feed)
    try:
        resp = requests.get(
            "https://openphish.com/feed.txt", timeout=_TIMEOUT, headers=headers
        )
        if resp.ok:
            for line in resp.text.splitlines():
                _add(line, "openphish")
        print(f"[generic-seed] OpenPhish contributed {len(out)} URLs")
    except Exception as exc:  # noqa: BLE001
        print(f"[generic-seed] OpenPhish fetch failed: {exc}", file=sys.stderr)

    # URLhaus (best-effort; may require auth)
    try:
        resp = requests.post(
            "https://urlhaus-api.abuse.ch/v1/urls/recent/", timeout=_TIMEOUT
        )
        if resp.ok and "json" in resp.headers.get("content-type", ""):
            before = len(out)
            for e in resp.json().get("urls", []):
                if e.get("url_status") == "online":
                    _add(e.get("url", ""), "urlhaus")
            print(f"[generic-seed] URLhaus contributed {len(out) - before} URLs")
    except Exception as exc:  # noqa: BLE001
        print(f"[generic-seed] URLhaus fetch skipped: {exc}", file=sys.stderr)

    random.Random(_SEED).shuffle(out)
    return out[:max_urls]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=1500)
    parser.add_argument("--out", default=SEED_CSV)
    args = parser.parse_args()

    rows = _fetch(args.max)
    if not rows:
        print("[generic-seed] no URLs fetched -- keeping existing file",
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
    print(f"[generic-seed] wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
