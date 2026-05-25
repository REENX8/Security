"""Load + validate the model artifacts produced by the ML pipeline."""

from __future__ import annotations

import json
import os

import joblib

from phish_features import FEATURE_SCHEMA_VERSION, ORDERED_FEATURES

from app.config import settings
from app.ml.extractor import build_extractor
from app.ml.scorer import Scorer


class ModelLoadError(RuntimeError):
    """Raised when artifacts are missing or incompatible with the code."""


def load_scorer() -> Scorer:
    """Load the ensemble, scaler and feature metadata into a ``Scorer``.

    Raises ``ModelLoadError`` -- the caller (lifespan) downgrades this to a
    warning so the API still starts and reports 503 on ``/check``.
    """
    for path in (settings.model_path, settings.scaler_path,
                 settings.features_json, settings.whitelist_path):
        if not os.path.exists(path):
            raise ModelLoadError(f"artifact not found: {path}")

    with open(settings.features_json, encoding="utf-8") as fh:
        meta = json.load(fh)

    # --- guard against train/serve skew ---
    if meta.get("schema_version") != FEATURE_SCHEMA_VERSION:
        raise ModelLoadError(
            f"feature schema mismatch: model={meta.get('schema_version')} "
            f"code={FEATURE_SCHEMA_VERSION} -- retrain the model"
        )
    if meta.get("ordered_features") != ORDERED_FEATURES:
        raise ModelLoadError(
            "ordered feature list in features.json does not match the "
            "phish_features package -- retrain the model"
        )

    model = joblib.load(settings.model_path)
    scaler = joblib.load(settings.scaler_path)
    extractor = build_extractor()

    return Scorer(model=model, scaler=scaler, extractor=extractor,
                  features_meta=meta)
