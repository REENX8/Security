"""Evaluate the trained ensemble on the held-out test split.

Prints accuracy / precision / recall / F1 and writes the ROC curve,
confusion matrix and a metrics JSON to ``reports/``.
"""

from __future__ import annotations

import json
import os

import joblib
import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from phish_features import ORDERED_FEATURES

from ml_pipeline.config import (
    METRICS_JSON,
    MODEL_PATH,
    REAL_HOLDOUT_CSV,
    REAL_HOLDOUT_METRICS_JSON,
    REPORTS_DIR,
    SCALER_PATH,
    ensure_dirs,
)
from ml_pipeline.feature_engineering import build_feature_frame
from ml_pipeline.train import TEST_SPLIT_CSV


def main() -> None:
    ensure_dirs()
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    test = pd.read_csv(TEST_SPLIT_CSV)
    X = test[ORDERED_FEATURES].astype(float)
    y = test["label"].astype(int)
    X_s = scaler.transform(X.to_numpy())

    y_pred = model.predict(X_s)
    y_proba = model.predict_proba(X_s)[:, 1]

    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred)
    rec = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    auc = roc_auc_score(y, y_proba)

    print("=" * 52)
    print("  PHISHING DETECTOR -- EVALUATION REPORT")
    print("=" * 52)
    print(f"  Accuracy   : {acc:.4f}")
    print(f"  Precision  : {prec:.4f}")
    print(f"  Recall     : {rec:.4f}")
    print(f"  F1-score   : {f1:.4f}")
    print(f"  ROC-AUC    : {auc:.4f}")
    print("-" * 52)
    print(classification_report(y, y_pred,
                                target_names=["legitimate", "phishing"]))

    # --- confusion matrix ---
    cm = confusion_matrix(y, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ConfusionMatrixDisplay(
        cm, display_labels=["legitimate", "phishing"]
    ).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    cm_path = f"{REPORTS_DIR}/confusion_matrix.png"
    fig.savefig(cm_path, dpi=120)
    plt.close(fig)
    print(f"[eval] saved {cm_path}")

    # --- ROC curve ---
    fpr, tpr, _ = roc_curve(y, y_proba)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(fpr, tpr, color="#ef4444", lw=2, label=f"ROC (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="#94a3b8", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    roc_path = f"{REPORTS_DIR}/roc_curve.png"
    fig.savefig(roc_path, dpi=120)
    plt.close(fig)
    print(f"[eval] saved {roc_path}")

    # --- feature importance (from the RF member) ---
    try:
        rf = model.named_estimators_["rf"]
        importances = pd.Series(
            rf.feature_importances_, index=ORDERED_FEATURES
        ).sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 6))
        sns.barplot(x=importances.values, y=importances.index,
                    ax=ax, color="#3b82f6")
        ax.set_title("Feature Importance (RandomForest)")
        fig.tight_layout()
        fi_path = f"{REPORTS_DIR}/feature_importance.png"
        fig.savefig(fi_path, dpi=120)
        plt.close(fig)
        print(f"[eval] saved {fi_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"[eval] feature importance skipped ({exc})")

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "test_rows": int(len(y)),
        "confusion_matrix": cm.tolist(),
    }
    with open(METRICS_JSON, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"[eval] saved {METRICS_JSON}")
    print("=" * 52)

    # ------------------------------------------------------------------
    # HONEST GENERALISATION CHECK: recall on real-world phishing URLs
    # the model has never seen during training.
    # ------------------------------------------------------------------
    if os.path.exists(REAL_HOLDOUT_CSV):
        evaluate_real_holdout(model, scaler)
    else:
        print(f"[eval] no real-phishing holdout found at {REAL_HOLDOUT_CSV} "
              "(skipping generalisation check)")


def evaluate_real_holdout(model, scaler) -> None:
    frame = build_feature_frame(REAL_HOLDOUT_CSV)
    X = frame[ORDERED_FEATURES].astype(float)
    y_pred = model.predict(scaler.transform(X.to_numpy()))
    y_proba = model.predict_proba(scaler.transform(X.to_numpy()))[:, 1]

    flagged = (y_pred == 1).sum()
    suspicious_or_phishing = (y_proba >= 0.30).sum()
    n = len(X)

    print()
    print("=" * 52)
    print("  HOLDOUT EVAL ON UNSEEN REAL PHISHING URLS")
    print("=" * 52)
    print(f"  Sample size           : {n}")
    print(f"  Recall  (score >= 0.7): {flagged}/{n}  "
          f"= {flagged / n:.4f}")
    print(f"  Caught  (score >= 0.3): {suspicious_or_phishing}/{n}  "
          f"= {suspicious_or_phishing / n:.4f}")
    print(f"  Mean score            : {float(y_proba.mean()):.4f}")
    print(f"  Median score          : {float(pd.Series(y_proba).median()):.4f}")

    missed = frame.assign(score=y_proba)[y_proba < 0.30]
    if len(missed):
        print(f"  Examples MISSED ({min(5, len(missed))} of {len(missed)}):")
        for _, row in missed.head(5).iterrows():
            print(f"    - {row['url']}  (score={row['score']:.2f})")

    metrics = {
        "sample_size": int(n),
        "recall_phishing_threshold": round(float(flagged) / n, 4),
        "recall_suspicious_threshold": round(float(suspicious_or_phishing) / n, 4),
        "mean_score": round(float(y_proba.mean()), 4),
        "median_score": round(float(pd.Series(y_proba).median()), 4),
        "missed_count": int(len(missed)),
    }
    with open(REAL_HOLDOUT_METRICS_JSON, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"  Saved {REAL_HOLDOUT_METRICS_JSON}")
    print("=" * 52)


if __name__ == "__main__":
    main()
