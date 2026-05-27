"""Audit the Thai-targeting phishing seed corpus and holdout split.

Prints a quick-look report showing:

  * total URLs, distinct brands, mean URLs/brand
  * top-N most-represented brands (over-representation risk)
  * spoof-TLD distribution (cheap-TLD coverage)
  * URL pattern-type distribution (subdomain-spoof, @-trick, ...)
  * holdout sample size and overlap with the seed

Run via ``make seed-audit`` or ``python -m scripts.audit_seed_coverage``.
Exits non-zero only if a *structural* invariant is violated (e.g. holdout
is missing). Coverage warnings are printed but do not fail the script —
this is a reporting tool, not a CI gate (use ``tests/test_seed_corpus``
for that).
"""

from __future__ import annotations

import collections
import csv
import os
import sys
from typing import Iterable
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_CSV = os.path.join(ROOT, "data", "thai_phishing_seed.csv")
HOLDOUT_CSV = os.path.join(ROOT, "data", "thai_phish_holdout.csv")

_THAI_CCTLDS = (".go.th", ".ac.th", ".or.th", ".co.th", ".in.th", ".net.th")


def _load_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _registrable_tld(url: str) -> str:
    """Return the rightmost label of the URL's hostname (a stand-in for
    the registrable TLD that does not require a PSL lookup)."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001
        return ""
    parts = host.split(".")
    return parts[-1] if parts else ""


def _classify_pattern(url: str) -> str:
    """Bucket each URL into a coarse phishing-pattern type. Strictly
    descriptive — order of checks matters since some URLs match more than
    one rule (e.g. an @-trick on a subdomain spoof)."""
    if "@" in (urlparse(url).netloc or ""):
        return "at_redirect"
    host = (urlparse(url).hostname or "").lower()
    if any(c in host for c in _THAI_CCTLDS):
        # ccTLD appears INSIDE the host string (not as the actual suffix)
        if not host.endswith(_THAI_CCTLDS):
            return "subdomain_spoof"
    if any(host.endswith("." + tld) for tld in ("xyz", "top", "cc", "shop",
                                                "online", "site", "icu",
                                                "click", "vip", "cfd",
                                                "bond", "live")):
        return "cheap_tld"
    if "xn--" in host:
        return "punycode"
    if host.replace(".", "").isdigit():
        return "ip_host"
    return "other"


def _print_header(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _hist(items: Iterable[str], top: int = 12) -> list[tuple[str, int]]:
    return collections.Counter(items).most_common(top)


def main() -> int:
    rows = _load_rows(SEED_CSV)
    if not rows:
        print(f"[audit] no seed corpus at {SEED_CSV}", file=sys.stderr)
        return 1

    holdout = _load_rows(HOLDOUT_CSV)

    brands = [r.get("target_brand", "") for r in rows]
    tlds = [_registrable_tld(r["url"]) for r in rows]
    patterns = [_classify_pattern(r["url"]) for r in rows]

    distinct_brands = sorted(set(b for b in brands if b))

    print("=" * 60)
    print("  Thai-targeting phishing seed corpus -- coverage audit")
    print("=" * 60)
    print(f"  Total URLs            : {len(rows)}")
    print(f"  Distinct brands       : {len(distinct_brands)}")
    print(f"  Mean URLs/brand       : "
          f"{len(rows) / max(len(distinct_brands), 1):.2f}")
    print(f"  Holdout sample size   : {len(holdout)} "
          f"({len(holdout) / max(len(rows), 1):.0%} of seed)")

    _print_header("Top 12 brands (over-representation check)")
    for brand, n in _hist(brands):
        bar = "*" * n
        print(f"  {brand:>18}  {n:>3}  {bar}")

    _print_header("Spoof-TLD distribution")
    for tld, n in _hist(tlds):
        bar = "*" * min(n // 5, 60)
        print(f"  {tld:>10}  {n:>4}  {bar}")

    _print_header("Phishing pattern type")
    for pat, n in _hist(patterns, top=10):
        bar = "*" * min(n // 5, 60)
        print(f"  {pat:>20}  {n:>4}  {bar}")

    # Holdout overlap with seed -- the dataset collector should be the
    # only writer of the holdout, and every holdout URL must come from
    # the seed. A non-overlapping URL means the pipeline drifted.
    seed_urls = {r["url"] for r in rows}
    holdout_urls = {r["url"] for r in holdout}
    if holdout_urls and not holdout_urls.issubset(seed_urls):
        leaked = sorted(holdout_urls - seed_urls)[:5]
        print()
        print(f"[warn] {len(holdout_urls - seed_urls)} holdout URLs are NOT "
              f"in the seed: {leaked}")
    elif holdout_urls:
        print()
        print(f"[ok]   holdout is a strict subset of the seed "
              f"({len(holdout_urls)}/{len(seed_urls)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
