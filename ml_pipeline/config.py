"""Shared paths and constants for the ML pipeline."""

from __future__ import annotations

import os

# Repo root (this file lives in <root>/ml_pipeline/).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")
MODELS_DIR = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")

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
TARGET_ROWS = 6000

# Optional external phishing feeds (best-effort; pipeline works without them).
PHISHTANK_URL = "https://data.phishtank.com/data/online-valid.json"
OPENPHISH_URL = "https://openphish.com/feed.txt"
FEED_TIMEOUT = 15  # seconds


def ensure_dirs() -> None:
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR, RAW_DIR):
        os.makedirs(path, exist_ok=True)
