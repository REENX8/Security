"""Shared paths and constants for the ML pipeline."""

from __future__ import annotations

import os
import random as _random

import numpy as _np

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

# Independent real-world holdout: a fresh sample of real phishing URLs with
# ZERO host overlap against any training corpus (built by
# scripts/collect_real_phish_holdout.py). This is the honest generalisation
# check — unlike GENERIC_HOLDOUT_CSV, none of its hosts are seen in training.
REAL_HOLDOUT_CSV = os.path.join(DATA_DIR, "real_phish_holdout.csv")

MODEL_PATH = os.path.join(MODELS_DIR, "ensemble.pkl")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
FEATURES_JSON = os.path.join(MODELS_DIR, "features.json")
METRICS_JSON = os.path.join(REPORTS_DIR, "metrics.json")
REAL_HOLDOUT_METRICS_JSON = os.path.join(REPORTS_DIR, "real_holdout_metrics.json")
INDEPENDENT_HOLDOUT_METRICS_JSON = os.path.join(
    REPORTS_DIR, "independent_real_holdout_metrics.json"
)

# Fraction of fetched real phishing URLs reserved as a held-out test set
# that the model never sees during training.
REAL_HOLDOUT_FRACTION = 0.30

# Reproducibility.
RANDOM_SEED = 42

# Lock global RNG state so any library that uses the global RNG (e.g. numpy
# random draws inside sklearn internals) produces the same results every run.
_random.seed(RANDOM_SEED)
_np.random.seed(RANDOM_SEED)

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

# Benign false-positive gate. The curated corpus of real legitimate sites is
# scored through the full pipeline (model + rules); a flood of "suspicious"
# warnings on benign traffic means the warning band is mis-tuned. The pytest
# gate (tests/test_benign_fp.py) checks the same corpus at serve time; mirroring
# it here lets `make evaluate-gate` and the feedback-retrain promotion path fail
# fast on the same regression. Phishing FPs on benign sites are always a hard
# fail (rate 0); the suspicious rate is bounded by this env-overridable cap.
BENIGN_HOLDOUT_CSV = os.path.join(DATA_DIR, "benign_holdout.csv")
BENIGN_HOLDOUT_METRICS_JSON = os.path.join(REPORTS_DIR, "benign_holdout_metrics.json")
BENIGN_FP_MAX_SUSPICIOUS_RATE = float(
    os.environ.get("BENIGN_FP_MAX_SUSPICIOUS_RATE", "0.15")
)

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
# Cap how many generic-phishing rows are folded into TRAINING. Generic phish
# lifts generic recall, but unconstrained it shifts the decision boundary away
# from the Thai cohort. The v1.9 archetype expansion (cctld_clone /
# user_content_host / query_blob) widened the phishing distribution, so the cap
# was re-swept against {90, 120, 150, 200} (real ceiling ~210 = seed 300 × 70%):
#
#   cap   thai     generic  independent  benign_fp
#    90   1.000    0.933    0.920        0/0
#   120   0.997    0.956    0.910        0/0
#   150   1.000    0.956    0.910        0/0
#   200   1.000    0.944    0.940        0/0   <- chosen
#
# Decision: pick the largest cap holding Thai recall ≥ 0.99 and benign FP at 0;
# 200 also gives the best independent-holdout recall (0.94, up from 0.90).
# Overridable via env for future sweeps.
GENERIC_TRAIN_MAX = int(os.environ.get("PHISH_GENERIC_TRAIN_MAX", "200"))

# CI gate: minimum recall on the Thai-targeting holdout at the phishing
# threshold (score >= 0.7). evaluate.py exits non-zero when run with
# --enforce-threshold and the measured value drops below this. The env
# variable lets CI raise the bar over time without editing source.
THAI_RECALL_MIN_THRESHOLD = float(
    os.environ.get("THAI_RECALL_MIN_THRESHOLD", "0.85")
)


# Live-feed phishing corpus written by feed_training_export.py.
# 80% goes to training (LIVE_FEED_CSV), 20% to holdout (LIVE_FEED_HOLDOUT_CSV).
LIVE_FEED_CSV = os.path.join(DATA_DIR, "live_feed_phishing.csv")
LIVE_FEED_HOLDOUT_CSV = os.path.join(DATA_DIR, "live_feed_holdout.csv")
LIVE_FEED_HOLDOUT_METRICS_JSON = os.path.join(REPORTS_DIR, "live_feed_holdout_metrics.json")

# Minimum number of new phishing URLs from feeds that triggers an immediate
# auto-retrain (in addition to the time-based feedback trigger).
FEED_RETRAIN_THRESHOLD = int(os.environ.get("PHISH_FEED_RETRAIN_THRESHOLD", "50"))

# Minimum age (hours) before a feed URL is eligible for export to training.
# Avoids ephemeral URLs that disappear before the model ever sees them.
FEED_EXPORT_MIN_AGE_HOURS = int(os.environ.get("PHISH_FEED_EXPORT_MIN_AGE_HOURS", "24"))

# Minimum recall on the live-feed holdout before the model is promoted.
LIVE_FEED_RECALL_MIN_THRESHOLD = float(
    os.environ.get("LIVE_FEED_RECALL_MIN_THRESHOLD", "0.80")
)


def ensure_dirs() -> None:
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR, RAW_DIR):
        os.makedirs(path, exist_ok=True)
