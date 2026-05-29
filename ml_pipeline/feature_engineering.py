"""Turn the labeled URL dataset into a numeric feature matrix.

The lexical + whitelist features are computed by the SHARED ``FeatureExtractor``
(exactly the code the backend runs at serve time). The WHOIS / TLS features are
taken from the simulated columns in ``dataset.csv`` and passed to the extractor
as ``network_overrides`` -- so no network calls happen during training.
"""

from __future__ import annotations

import pandas as pd

from phish_features import FeatureExtractor, ORDERED_FEATURES, Whitelist

from ml_pipeline.config import DATASET_CSV, WHITELIST_JSON

# Columns in dataset.csv that carry simulated WHOIS/TLS values.
_NETWORK_COLS = [
    "domain_age_days", "is_known_registrar", "has_valid_cert",
    "cert_age_days", "is_self_signed", "whois_ok", "tls_ok",
    # v1.5 simulated TLS-derived columns
    "cert_is_lets_encrypt", "cert_validity_days", "cert_san_count",
]


def _row_overrides(row: pd.Series) -> dict:
    """Build a network_overrides dict from a dataset row."""
    out: dict = {}
    for col in _NETWORK_COLS:
        val = row.get(col, "")
        if val == "" or pd.isna(val):
            continue
        out[col] = float(val)
    return out


def build_feature_frame(
    dataset_csv: str = DATASET_CSV,
    whitelist_json: str = WHITELIST_JSON,
) -> pd.DataFrame:
    """Return a DataFrame with the ordered features + label + metadata."""
    df = pd.read_csv(dataset_csv)
    wl = Whitelist.from_json(whitelist_json)
    # Network is disabled: the simulated values arrive via network_overrides.
    extractor = FeatureExtractor(wl, enable_whois=False, enable_tls=False)

    records: list[dict] = []
    for _, row in df.iterrows():
        url = str(row["url"])
        overrides = _row_overrides(row)
        feat = extractor.extract_dict(url, network_overrides=overrides)
        rec = {name: feat[name] for name in ORDERED_FEATURES}
        rec["label"] = int(row["label"])
        rec["url"] = url
        rec["closest_domain"] = feat.get("closest_domain")
        rec["tld_type"] = feat.get("tld_type")
        records.append(rec)

    out = pd.DataFrame.from_records(records)
    print(f"[features] built matrix: {out.shape[0]} rows x "
          f"{len(ORDERED_FEATURES)} features")
    return out


def main() -> None:
    frame = build_feature_frame()
    cache = DATASET_CSV.replace("dataset.csv", "features_cache.csv")
    frame.to_csv(cache, index=False)
    print(f"[features] cached -> {cache}")
    print(frame[ORDERED_FEATURES].describe().T[["mean", "min", "max"]])


if __name__ == "__main__":
    main()
