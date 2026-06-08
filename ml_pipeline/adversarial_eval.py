"""Adversarial URL evaluation script.

Loads the trained ensemble model and evaluates it against the hand-crafted
adversarial URL dataset (data/adversarial_urls.csv).

Exit code 0 if detection_rate >= 0.70, exit code 1 otherwise.

Usage:
    python -m ml_pipeline.adversarial_eval
    python -m ml_pipeline.adversarial_eval --csv path/to/custom.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# Allow running as a module from the repo root.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "backend"))

DETECTION_THRESHOLD = 0.70
SCORE_THRESHOLD = 0.50  # score >= this counts as detected phishing
_DEFAULT_CSV = _REPO / "data" / "adversarial_urls.csv"
_REPORTS_DIR = _REPO / "reports"


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _score_url(scorer, url: str) -> dict:
    try:
        return scorer.score(url)
    except Exception as exc:  # noqa: BLE001
        return {"label": "error", "score": 0.0, "error": str(exc)}


def run_eval(csv_path: Path) -> dict:
    from app.ml.loader import load_scorer

    scorer = load_scorer()
    rows = _load_csv(csv_path)

    total = len(rows)
    detected = 0
    misses: list[dict] = []
    by_category: dict[str, dict] = defaultdict(lambda: {"n": 0, "detected": 0})

    for row in rows:
        url = row["url"]
        expected = row.get("expected_label", "phishing")
        technique = row.get("evasion_technique", "unknown")

        result = _score_url(scorer, url)
        label = result.get("label", "unknown")
        score = float(result.get("score", 0.0))

        cat = by_category[technique]
        cat["n"] += 1

        is_detected = expected == "phishing" and (label == "phishing" or score >= SCORE_THRESHOLD)
        if is_detected:
            detected += 1
            cat["detected"] += 1
        else:
            misses.append({
                "url": url,
                "technique": technique,
                "expected": expected,
                "got_label": label,
                "score": round(score, 4),
            })

    detection_rate = detected / total if total > 0 else 0.0

    return {
        "total": total,
        "detected": detected,
        "missed": total - detected,
        "detection_rate": round(detection_rate, 4),
        "passed": detection_rate >= DETECTION_THRESHOLD,
        "threshold": DETECTION_THRESHOLD,
        "missed_urls": misses,
        "by_category": {
            cat: {
                "n": v["n"],
                "detected": v["detected"],
                "rate": round(v["detected"] / v["n"], 4) if v["n"] else 0.0,
            }
            for cat, v in sorted(by_category.items())
        },
    }


def _print_report(report: dict) -> None:
    print("\nAdversarial Evaluation Report")
    print(f"{'='*50}")
    print(f"Total URLs : {report['total']}")
    print(f"Detected   : {report['detected']}")
    print(f"Missed     : {report['missed']}")
    print(f"Rate       : {report['detection_rate']:.1%}  (threshold {report['threshold']:.0%})")
    print(f"Status     : {'PASS' if report['passed'] else 'FAIL'}")

    print("\nBy Evasion Technique:")
    print(f"{'Technique':<30} {'N':>4} {'Detected':>8} {'Rate':>6}")
    print(f"{'-'*30} {'-'*4} {'-'*8} {'-'*6}")
    for cat, v in report["by_category"].items():
        print(f"{cat:<30} {v['n']:>4} {v['detected']:>8} {v['rate']:>6.1%}")

    if report["missed_urls"]:
        print(f"\nMissed URLs ({len(report['missed_urls'])}):")
        for m in report["missed_urls"][:20]:
            print(f"  [{m['technique']}] score={m['score']:.3f} label={m['got_label']} → {m['url'][:80]}")
        if len(report["missed_urls"]) > 20:
            print(f"  ... and {len(report['missed_urls']) - 20} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adversarial URL evaluation")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_DEFAULT_CSV,
        help="Path to adversarial CSV (default: data/adversarial_urls.csv)",
    )
    args = parser.parse_args(argv)

    if not args.csv.exists():
        print(f"[adversarial-eval] CSV not found: {args.csv}", file=sys.stderr)
        return 1

    print(f"[adversarial-eval] loading model and evaluating {args.csv}...")
    report = run_eval(args.csv)
    _print_report(report)

    _REPORTS_DIR.mkdir(exist_ok=True)
    out_path = _REPORTS_DIR / "adversarial_eval.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[adversarial-eval] report written to {out_path}")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
