"""Threshold analysis on the COMMITTED holdouts (reproducible, offline).

The serve-time labels use hard-coded cutoffs (``THRESHOLD_PHISHING=0.7`` /
``THRESHOLD_SUSPICIOUS=0.3``). Those numbers were never justified against held-out
data. This script sweeps the decision threshold over a real precision/recall
curve built from:

  * POSITIVES — the committed Thai + generic phishing holdouts (label=1), the
    same URLs ``evaluate.py`` reports recall on.
  * NEGATIVES — the trusted Thai gov/edu/state domains (label=0). These never
    enter training as negatives via this path, so they are a fair stand-in for
    "legitimate traffic the model must not flag".

It writes ``reports/threshold_analysis.json`` (precision/recall/F1 at each
candidate threshold, plus the F1-optimal point and the high-precision point)
and a PNG. It does NOT change any runtime default — picking a new threshold is
a deliberate follow-up, and this script gives the evidence to do it.

Run:  python -m ml_pipeline.tune_threshold
"""

from __future__ import annotations

import json
import os

import joblib
import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phish_features import ORDERED_FEATURES

from ml_pipeline.config import (
    GENERIC_HOLDOUT_CSV,
    MODEL_PATH,
    REPORTS_DIR,
    SCALER_PATH,
    THAI_HOLDOUT_CSV,
    WHITELIST_CSV,
    ensure_dirs,
)
from ml_pipeline.feature_engineering import build_feature_frame

THRESHOLD_ANALYSIS_JSON = os.path.join(REPORTS_DIR, "threshold_analysis.json")
THRESHOLD_ANALYSIS_PNG = os.path.join(REPORTS_DIR, "threshold_analysis.png")


def _score_frame(model, scaler, frame: pd.DataFrame) -> np.ndarray:
    X = frame[ORDERED_FEATURES].astype(float)
    X_s = scaler.transform(X.to_numpy())
    return model.predict_proba(X_s)[:, 1]


def _trusted_negatives_frame() -> pd.DataFrame:
    """Wrap the trusted-domain list as an all-negative URL CSV for scoring.

    The trusted list is bare hostnames; build_feature_frame expects a `url`
    column. We synthesise https:// URLs and label them 0 (legitimate). No
    network columns are present, so WHOIS/TLS features fall back to the same
    imputed defaults the backend uses when a lookup is unavailable.
    """
    doms = pd.read_csv(WHITELIST_CSV)["domain"].dropna().astype(str)
    tmp = os.path.join(REPORTS_DIR, "_trusted_neg_urls.csv")
    pd.DataFrame(
        {"url": ["https://" + d.strip() + "/" for d in doms], "label": 0}
    ).to_csv(tmp, index=False)
    frame = build_feature_frame(tmp)
    os.remove(tmp)
    return frame


def main() -> None:
    ensure_dirs()
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    # --- positives: committed phishing holdouts ---
    pos_frames = []
    for csv_path in (THAI_HOLDOUT_CSV, GENERIC_HOLDOUT_CSV):
        if os.path.exists(csv_path):
            pos_frames.append(build_feature_frame(csv_path))
    if not pos_frames:
        raise SystemExit("no holdout CSVs found; run `make train` first")
    pos = pd.concat(pos_frames, ignore_index=True)

    # --- negatives: trusted Thai domains ---
    neg = _trusted_negatives_frame()

    y_true = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))])
    y_score = np.concatenate(
        [_score_frame(model, scaler, pos), _score_frame(model, scaler, neg)]
    )

    # --- sweep candidate thresholds ---
    grid = [round(t, 2) for t in np.arange(0.05, 1.0, 0.05)]
    rows = []
    for t in grid:
        pred = y_score >= t
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        rows.append(
            {
                "threshold": t,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "false_positives": fp,
                "false_negatives": fn,
            }
        )

    best_f1 = max(rows, key=lambda r: r["f1"])
    # Highest-recall threshold that still keeps precision >= 0.99 (operator
    # objective: do not cry wolf on legitimate gov sites).
    high_prec = max(
        (r for r in rows if r["precision"] >= 0.99),
        key=lambda r: r["recall"],
        default=best_f1,
    )

    out = {
        "n_positives": int(len(pos)),
        "n_negatives": int(len(neg)),
        "negatives_source": os.path.basename(WHITELIST_CSV),
        "current_runtime_threshold": 0.7,
        "f1_optimal": best_f1,
        "high_precision_recommended": high_prec,
        "curve": rows,
        "note": (
            "Positives are the committed phishing holdouts; negatives are the "
            "trusted Thai domain list. This is an in-distribution estimate — "
            "treat thresholds as guidance, validate on live telemetry before "
            "changing THRESHOLD_PHISHING."
        ),
    }
    with open(THRESHOLD_ANALYSIS_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    # --- plot ---
    ts = [r["threshold"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ts, [r["precision"] for r in rows], label="precision", marker="o")
    ax.plot(ts, [r["recall"] for r in rows], label="recall", marker="s")
    ax.plot(ts, [r["f1"] for r in rows], label="F1", marker="^")
    ax.axvline(0.7, color="grey", linestyle="--", label="current (0.70)")
    ax.axvline(
        best_f1["threshold"], color="green", linestyle=":",
        label=f"F1-optimal ({best_f1['threshold']})",
    )
    ax.set_xlabel("threshold")
    ax.set_ylabel("score")
    ax.set_title("Precision / Recall / F1 vs threshold (committed holdouts)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(THRESHOLD_ANALYSIS_PNG, dpi=120)

    print(f"[threshold] positives={len(pos)} negatives={len(neg)}")
    print(f"[threshold] F1-optimal: {best_f1}")
    print(f"[threshold] high-precision (>=0.99): {high_prec}")
    print(f"[threshold] wrote {THRESHOLD_ANALYSIS_JSON} + PNG")


if __name__ == "__main__":
    main()
