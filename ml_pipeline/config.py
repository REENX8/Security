"""Shared paths and constants for the ML pipeline."""

from __future__ import annotations

import os

# Repo root (this file lives in <root>/ml_pipeline/).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")
# MODELS_DIR / REPORTS_DIR honour env overrides so a retrain can write to a
# staging directory and be evaluated there WITHOUT overwriting the live
# model -- the feedback-driven retrain promotes staging -> models only after
# the eval gate passes (see ml_pipeline/feedback_retrain.py).
MODELS_DIR = os.environ.get("PHISH_MODELS_DIR") or os.path.join(ROOT, "models")
REPORTS_DIR = os.environ.get("PHISH_REPORTS_DIR") or os.path.join(ROOT, "reports")

# Inputs / outputs.
WHITELIST_CSV = os.path.join(DATA_DIR, "thai_gov_domains.csv")
WHITELIST_JSON = os.path.join(MODELS_DIR, "whitelist.json")
DATASET_CSV = os.path.join(DATA_DIR, "dataset.csv")
RAW_DIR = os.path.join(DATA_DIR, "raw")

REAL_HOLDOUT_CSV = os.path.join(DATA_DIR, "real_phish_holdout.csv")

MODEL_PATH = os.path.join(MODELS_DIR, "ensemble.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
FEATURES_JSON = os.path.join(MODELS_DIR, "features.json")
METRICS_JSON = os.path.join(REPORTS_DIR, "metrics.json")
REAL_HOLDOUT_METRICS_JSON = os.path.join(REPORTS_DIR, "real_holdout_metrics.json")

# Fraction of fetched real phishing URLs reserved as a held-out test set
# that the model never sees during training.
REAL_HOLDOUT_FRACTION = 0.30

# Reproducibility.
RANDOM_SEED = 42

# Dataset target size (balanced across the two classes).
TARGET_ROWS = 12000

# Optional external phishing feeds (best-effort; pipeline works without them).
PHISHTANK_URL = "https://data.phishtank.com/data/online-valid.json"
OPENPHISH_URL = "https://openphish.com/feed.txt"
URLHAUS_URL = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
FEED_TIMEOUT = 15  # seconds

THAI_HOLDOUT_CSV = os.path.join(DATA_DIR, "thai_phish_holdout.csv")
THAI_HOLDOUT_METRICS_JSON = os.path.join(REPORTS_DIR, "thai_holdout_metrics.json")
EVALUATION_SUMMARY_JSON = os.path.join(REPORTS_DIR, "evaluation_summary.json")

# Confirmed-feedback labels exported from the DB by feedback_retrain.py.
# When present, collect_dataset folds these real user-confirmed URLs into
# the TRAINING set (never the holdout) so continuous retraining actually
# learns from production feedback.
FEEDBACK_CSV = os.path.join(DATA_DIR, "feedback_labels.csv")

# Curated Thai-targeting phishing seed corpus (committed to repo, no network).
THAI_PHISH_SEED_CSV = os.path.join(DATA_DIR, "thai_phishing_seed.csv")
# Fraction of the seed corpus routed into training; rest goes to the
# Thai-targeting holdout used as the primary alignment metric.
THAI_SEED_TRAIN_FRACTION = 0.70

# Committed snapshot of real, NON-Thai generic phishing (built by
# scripts/collect_generic_phishing_seed.py). Folded into TRAINING so the model
# is not blind to generic phishing; a deterministic 30% split is held out as a
# reproducible generic cross-check (no live feed needed at train/eval time).
GENERIC_PHISH_SEED_CSV = os.path.join(DATA_DIR, "generic_phishing_seed.csv")
GENERIC_HOLDOUT_CSV = os.path.join(DATA_DIR, "generic_phish_holdout.csv")
GENERIC_SEED_TRAIN_FRACTION = 0.70

# CI gate: minimum recall on the Thai-targeting holdout at the phishing
# threshold (score >= 0.7). evaluate.py exits non-zero when run with
# --enforce-threshold and the measured value drops below this. The env
# variable lets CI raise the bar over time without editing source.
THAI_RECALL_MIN_THRESHOLD = float(
    os.environ.get("THAI_RECALL_MIN_THRESHOLD", "0.85")
)


def ensure_dirs() -> None:
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR, RAW_DIR):
        os.makedirs(path, exist_ok=True)
