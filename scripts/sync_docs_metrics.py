#!/usr/bin/env python3
"""Inject the authoritative model metrics into the docs so they never go stale.

The headline numbers (Thai-holdout recall, holdout size, schema version,
feature count, seed-corpus size, ...) live in exactly one place each --
``reports/evaluation_summary.json``, ``models/features.json`` and the seed
CSV. Hard-coding them in prose is how README/CHANGELOG/NSC docs drifted to a
stale "66 / 100%". This script replaces the text between sentinel markers:

    <!--M:thai_recall-->100% (378/378)<!--/M-->

Usage:
    python scripts/sync_docs_metrics.py            # rewrite docs in place
    python scripts/sync_docs_metrics.py --check     # exit 1 if any drift

Add ``make sync-docs`` after ``make evaluate`` and run ``--check`` in CI so a
metrics change can never silently diverge from the docs again.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_JSON = ROOT / "reports" / "evaluation_summary.json"
FEATURES_JSON = ROOT / "models" / "features.json"
SEED_CSV = ROOT / "data" / "thai_phishing_seed.csv"

# Files scanned for <!--M:KEY-->...<!--/M--> sentinels.
DOC_FILES = [ROOT / "README.md"]

_SENTINEL_RE = re.compile(r"(<!--M:([a-z_]+)-->)(.*?)(<!--/M-->)", re.DOTALL)


def _csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as fh:
        return max(sum(1 for _ in fh) - 1, 0)  # minus header


def compute_metrics() -> dict[str, str]:
    summary = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    feats = json.loads(FEATURES_JSON.read_text(encoding="utf-8"))

    thai = summary["thai_targeting_holdout"]
    n = int(thai["sample_size"])
    caught = n - int(thai["missed_count"])
    recall_pct = thai["recall_phishing_threshold"] * 100
    ci = thai["recall_phishing_ci_95"]

    gen = summary.get("secondary_metrics", {})
    gen_n = int(gen.get("generic_real_holdout_n") or 0)
    gen_recall = gen.get("generic_real_holdout_recall")
    # The generic holdout needs live phishing feeds; offline/CI runs produce
    # null. It is also high-variance and feed-snapshot-dependent, so it is a
    # cross-check, never a headline. Render it only when actually measured.
    if gen_recall is None or gen_n == 0:
        generic = "n/a (run `make evaluate` with live feeds)"
    else:
        generic = f"{gen_recall * 100:.4g}% ({round(gen_recall * gen_n)}/{gen_n})"

    return {
        "schema_version": str(feats.get("schema_version", "")),
        "n_features": str(feats.get("n_features", len(feats.get("ordered_features", [])))),
        "seed_count": f"{_csv_rows(SEED_CSV):,}",
        "thai_holdout_n": str(n),
        "thai_recall": f"{recall_pct:.4g}% ({caught}/{n})",
        "thai_recall_pct": f"{recall_pct:.4g}%",
        "thai_recall_ci": f"[{ci[0]:.3f}, {ci[1]:.3f}]",
        "generic_recall": generic,
        "synthetic_f1": f"{summary.get('synthetic_test', {}).get('f1_score', gen.get('synthetic_f1', 0.0)):.4g}",
    }


def _apply(text: str, metrics: dict[str, str]) -> tuple[str, list[str]]:
    """Return (new_text, unknown_keys) after substituting every sentinel."""
    unknown: list[str] = []

    def repl(m: re.Match) -> str:
        key = m.group(2)
        if key not in metrics:
            unknown.append(key)
            return m.group(0)
        return f"{m.group(1)}{metrics[key]}{m.group(4)}"

    return _SENTINEL_RE.sub(repl, text), unknown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report drift and exit non-zero (no writes)")
    args = parser.parse_args()

    metrics = compute_metrics()
    drift: list[str] = []
    unknown_total: set[str] = set()

    for path in DOC_FILES:
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        updated, unknown = _apply(original, metrics)
        unknown_total.update(unknown)
        rel = path.relative_to(ROOT)
        if updated != original:
            if args.check:
                drift.append(str(rel))
            else:
                path.write_text(updated, encoding="utf-8")
                print(f"  updated {rel}")

    if unknown_total:
        print(f"error: unknown sentinel keys in docs: {sorted(unknown_total)}",
              file=sys.stderr)
        return 2

    if args.check and drift:
        print("docs out of sync with reports/evaluation_summary.json:",
              file=sys.stderr)
        for d in drift:
            print(f"  - {d}  (run: make sync-docs)", file=sys.stderr)
        return 1

    if args.check:
        print("docs metrics in sync")
    else:
        print(f"sync complete (schema v{metrics['schema_version']}, "
              f"{metrics['n_features']} features, "
              f"Thai recall {metrics['thai_recall']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
