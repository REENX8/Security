"""Tests for feedback-driven model retrain pipeline."""
from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ml_pipeline.feedback_retrain import (
    MIN_ROWS_FOR_RETRAIN,
    _retrain,
    _write_csv,
    run,
)


def _rows(n: int) -> list[dict]:
    return [
        {"url": f"https://phish{i}.xyz/login", "label": "1", "source": "feedback"}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _write_csv
# ---------------------------------------------------------------------------

def test_write_csv_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("ml_pipeline.feedback_retrain.FEEDBACK_CSV", tmp_path / "f.csv")
    import ml_pipeline.feedback_retrain as mod
    mod.FEEDBACK_CSV = tmp_path / "f.csv"
    _write_csv(_rows(3))
    lines = list(csv.DictReader((tmp_path / "f.csv").open()))
    assert len(lines) == 3
    assert lines[0]["label"] == "1"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_no_rows_returns_true():
    with patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=[])):
        assert run(since_days=1) is True


def test_run_below_min_skips_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN - 1)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain") as mock_rt,
    ):
        result = run(since_days=1)
    mock_rt.assert_not_called()
    assert result is True


def test_run_dry_run_skips_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain") as mock_rt,
    ):
        result = run(since_days=1, dry_run=True)
    mock_rt.assert_not_called()
    assert result is True


def test_run_triggers_retrain():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain", return_value=True) as mock_rt,
    ):
        result = run(since_days=1)
    mock_rt.assert_called_once()
    assert result is True


def test_run_propagates_retrain_failure():
    rows = _rows(MIN_ROWS_FOR_RETRAIN + 2)
    with (
        patch("ml_pipeline.feedback_retrain._export", new=AsyncMock(return_value=rows)),
        patch("ml_pipeline.feedback_retrain._write_csv"),
        patch("ml_pipeline.feedback_retrain._retrain", return_value=False),
    ):
        result = run(since_days=1)
    assert result is False
