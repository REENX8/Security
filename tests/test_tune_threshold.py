"""Guard test for the threshold-analysis script.

We don't assert a specific optimal threshold (that depends on the trained
model); we assert the analysis runs end-to-end on the committed holdouts and
produces a well-formed precision/recall/F1 curve.
"""

from __future__ import annotations

import os

import pytest

from ml_pipeline.config import (
    GENERIC_HOLDOUT_CSV,
    MODEL_PATH,
    THAI_HOLDOUT_CSV,
)

pytestmark = pytest.mark.skipif(
    not (os.path.exists(MODEL_PATH) and os.path.exists(THAI_HOLDOUT_CSV)),
    reason="model or Thai holdout not present (run `make train`)",
)


def test_threshold_analysis_runs_and_is_wellformed():
    from ml_pipeline import tune_threshold

    tune_threshold.main()

    import json

    with open(tune_threshold.THRESHOLD_ANALYSIS_JSON, encoding="utf-8") as fh:
        out = json.load(fh)

    assert out["n_positives"] > 0
    assert out["n_negatives"] > 0
    assert out["curve"], "curve must not be empty"
    for row in out["curve"]:
        assert 0.0 <= row["precision"] <= 1.0
        assert 0.0 <= row["recall"] <= 1.0
        assert 0.0 <= row["f1"] <= 1.0
        assert row["false_positives"] >= 0
        assert row["false_negatives"] >= 0

    # F1-optimal must be one of the swept thresholds.
    thresholds = {r["threshold"] for r in out["curve"]}
    assert out["f1_optimal"]["threshold"] in thresholds
    assert os.path.exists(tune_threshold.THRESHOLD_ANALYSIS_PNG)
