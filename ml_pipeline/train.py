"""Train the phishing-detection ensemble.

RandomForest + XGBoost combined with a soft-voting classifier. Produces three
artifacts the backend loads at startup:

  * models/ensemble.pkl  -- the fitted VotingClassifier
  * models/scaler.pkl    -- the fitted StandardScaler
  * models/features.json -- the pinned feature contract + provenance
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json

import joblib
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import xgboost

from phish_features import (
    FEATURE_SCHEMA_VERSION,
    IMPUTED_DEFAULTS,
    ORDERED_FEATURES,
    TLD_TYPE_MAP,
)

from ml_pipeline.config import (
    DATA_DIR,
    FEATURES_JSON,
    MODEL_PATH,
    RANDOM_SEED,
    SCALER_PATH,
    WHITELIST_CSV,
    ensure_dirs,
)
from ml_pipeline.feature_engineering import build_feature_frame

TEST_SPLIT_CSV = f"{DATA_DIR}/test_split.csv"


def _whitelist_hash() -> str:
    with open(WHITELIST_CSV, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def build_ensemble() -> VotingClassifier:
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        n_jobs=-1,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    return VotingClassifier(
        estimators=[("rf", rf), ("xgb", xgb)],
        voting="soft",
        n_jobs=-1,
    )


def main() -> None:
    ensure_dirs()
    frame = build_feature_frame()

    X = frame[ORDERED_FEATURES].astype(float)
    y = frame["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_SEED
    )
    print(f"[train] train={len(X_train)}  test={len(X_test)}")

    # Fit on plain arrays so the scaler/model carry no feature-name metadata
    # -- the backend scores raw numeric vectors, this keeps them consistent.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train.to_numpy())
    X_test_s = scaler.transform(X_test.to_numpy())

    base = build_ensemble()
    print("[train] fitting calibrated RandomForest + XGBoost ensemble (cv=5) ...")
    model = CalibratedClassifierCV(base, method="isotonic", cv=5)
    model.fit(X_train_s, y_train.to_numpy())

    train_pred = model.predict(X_train_s)
    test_pred = model.predict(X_test_s)
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, test_pred)
    test_f1 = f1_score(y_test, test_pred)
    print(f"[train] accuracy  train={train_acc:.4f}  test={test_acc:.4f}")
    print(f"[train] f1-score  test={test_f1:.4f}")

    # --- persist artifacts ---
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[train] saved model  -> {MODEL_PATH}")
    print(f"[train] saved scaler -> {SCALER_PATH}")

    features_meta = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "ordered_features": ORDERED_FEATURES,
        "n_features": len(ORDERED_FEATURES),
        "tld_type_map": TLD_TYPE_MAP,
        "imputed_defaults": IMPUTED_DEFAULTS,
        "whitelist_sha256": _whitelist_hash(),
        "trained_at": dt.datetime.utcnow().isoformat() + "Z",
        "sklearn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "metrics": {
            "train_accuracy": round(train_acc, 4),
            "test_accuracy": round(test_acc, 4),
            "test_f1": round(test_f1, 4),
        },
    }
    with open(FEATURES_JSON, "w", encoding="utf-8") as fh:
        json.dump(features_meta, fh, indent=2)
    print(f"[train] saved features.json -> {FEATURES_JSON}")

    # --- save the held-out test split for evaluate.py ---
    test_frame = X_test.copy()
    test_frame["label"] = y_test.values
    test_frame.to_csv(TEST_SPLIT_CSV, index=False)
    print(f"[train] saved test split -> {TEST_SPLIT_CSV}")


if __name__ == "__main__":
    main()
