"""Build the shipped whitelist artifact from the curated CSV.

Run this first. It produces ``models/whitelist.json`` -- the single whitelist
artifact loaded by BOTH the training pipeline and the backend, guaranteeing
identical edit-distance computations on both sides.
"""

from __future__ import annotations

from phish_features import Whitelist

from ml_pipeline.config import WHITELIST_CSV, WHITELIST_JSON, ensure_dirs


def main() -> None:
    ensure_dirs()
    wl = Whitelist.from_csv(WHITELIST_CSV)
    wl.to_json(WHITELIST_JSON)
    print(f"[whitelist] loaded {len(wl.entries)} domains from {WHITELIST_CSV}")
    by_cat: dict[str, int] = {}
    for e in wl.entries:
        by_cat[e.category] = by_cat.get(e.category, 0) + 1
    for cat, n in sorted(by_cat.items()):
        print(f"           {cat:>8}: {n}")
    print(f"[whitelist] wrote artifact -> {WHITELIST_JSON}")


if __name__ == "__main__":
    main()
