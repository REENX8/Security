"""Tests for the feed training export pipeline (F6)."""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
_REPO = str(Path(__file__).resolve().parents[1])
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from ml_pipeline.feed_training_export import (  # noqa: E402
    _append_rows,
    _load_existing_urls,
    _url_hash,
    export_feed_urls,
)


def test_url_hash_is_stable():
    h1 = _url_hash("http://phish.example.com/login")
    h2 = _url_hash("http://phish.example.com/login")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_url_hash_differs_for_different_urls():
    assert _url_hash("http://a.com") != _url_hash("http://b.com")


def test_load_existing_urls_empty_when_no_files():
    seen = _load_existing_urls("/nonexistent/path.csv")
    assert isinstance(seen, set)
    assert len(seen) == 0


def test_load_existing_urls_reads_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "label"])
        writer.writeheader()
        writer.writerow({"url": "http://phish.com/login", "label": "phishing"})
        fname = f.name
    try:
        seen = _load_existing_urls(fname)
        assert _url_hash("http://phish.com/login") in seen
    finally:
        os.unlink(fname)


def test_append_rows_creates_file_with_header():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        _append_rows(path, [{"url": "http://x.com", "label": "phishing", "source": "feed", "ingested_at": "2026-01-01"}],
                     ["url", "label", "source", "ingested_at"])
        with open(path) as f:
            content = f.read()
        assert "url" in content
        assert "http://x.com" in content


def test_append_rows_appends_without_duplicate_header():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        row = {"url": "http://a.com", "label": "phishing", "source": "feed", "ingested_at": "2026-01-01"}
        fields = ["url", "label", "source", "ingested_at"]
        _append_rows(path, [row], fields)
        _append_rows(path, [{"url": "http://b.com", **{k: v for k, v in row.items() if k != "url"}}], fields)
        with open(path) as f:
            lines = f.readlines()
        # 1 header + 2 data rows
        assert len(lines) == 3


def test_export_feed_urls_empty_db_writes_nothing():
    """With no phishing feed rows in DB, export writes nothing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_csv = os.path.join(tmpdir, "train.csv")
        holdout_csv = os.path.join(tmpdir, "holdout.csv")

        class _MockSession:
            def execute(self, stmt):
                return _MockResult([])

        class _MockResult:
            def __init__(self, rows):
                self._rows = rows
            def scalars(self):
                return self
            def all(self):
                return self._rows

        with patch("ml_pipeline.feed_training_export.LIVE_FEED_CSV", train_csv), \
             patch("ml_pipeline.feed_training_export.LIVE_FEED_HOLDOUT_CSV", holdout_csv), \
             patch("ml_pipeline.feed_training_export.THAI_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.GENERIC_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.ensure_dirs"):
            result = export_feed_urls(_MockSession(), since_hours=168, dry_run=False)

        assert result["exported_train"] == 0
        assert result["exported_holdout"] == 0
        assert not Path(train_csv).exists()
        assert not Path(holdout_csv).exists()


def test_export_feed_urls_dry_run_does_not_write():
    """dry_run=True counts but does not write files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_csv = os.path.join(tmpdir, "train.csv")
        holdout_csv = os.path.join(tmpdir, "holdout.csv")

        now = datetime.now(timezone.utc)

        class _MockRow:
            def __init__(self, url, checked_at):
                self.url = url
                self.checked_at = checked_at
                self.features = {"feed_source": "openphish"}

        rows = [_MockRow(f"http://phish{i}.com/login", now - timedelta(hours=48)) for i in range(10)]

        class _MockSession:
            def execute(self, stmt):
                return _MockResult(rows)

        class _MockResult:
            def __init__(self, data):
                self._data = data
            def scalars(self):
                return self
            def all(self):
                return self._data

        with patch("ml_pipeline.feed_training_export.LIVE_FEED_CSV", train_csv), \
             patch("ml_pipeline.feed_training_export.LIVE_FEED_HOLDOUT_CSV", holdout_csv), \
             patch("ml_pipeline.feed_training_export.THAI_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.GENERIC_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.ensure_dirs"):
            result = export_feed_urls(_MockSession(), since_hours=168, dry_run=True)

        assert result["exported_train"] == 8   # 80% of 10
        assert result["exported_holdout"] == 2  # 20% of 10
        # dry_run: no files written
        assert not Path(train_csv).exists()
        assert not Path(holdout_csv).exists()


def test_export_deduplicates_against_existing():
    """URLs already in the seed CSV should be skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        seed_csv = os.path.join(tmpdir, "seed.csv")
        train_csv = os.path.join(tmpdir, "train.csv")
        holdout_csv = os.path.join(tmpdir, "holdout.csv")

        # Write 5 URLs to the "seed" CSV
        with open(seed_csv, "w") as f:
            w = csv.DictWriter(f, fieldnames=["url", "label"])
            w.writeheader()
            for i in range(5):
                w.writerow({"url": f"http://phish{i}.com/login", "label": "phishing"})

        now = datetime.now(timezone.utc)

        class _MockRow:
            def __init__(self, url):
                self.url = url
                self.checked_at = now - timedelta(hours=48)
                self.features = {"feed_source": "openphish"}

        # 10 URLs: 5 are in seed (duplicates), 5 are new
        rows = [_MockRow(f"http://phish{i}.com/login") for i in range(10)]

        class _MockSession:
            def execute(self, stmt):
                return _MockResult(rows)

        class _MockResult:
            def __init__(self, data):
                self._data = data
            def scalars(self):
                return self
            def all(self):
                return self._data

        with patch("ml_pipeline.feed_training_export.LIVE_FEED_CSV", train_csv), \
             patch("ml_pipeline.feed_training_export.LIVE_FEED_HOLDOUT_CSV", holdout_csv), \
             patch("ml_pipeline.feed_training_export.THAI_PHISH_SEED_CSV", seed_csv), \
             patch("ml_pipeline.feed_training_export.GENERIC_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.ensure_dirs"):
            result = export_feed_urls(_MockSession(), since_hours=168, dry_run=False)

        assert result["skipped_dups"] == 5
        assert result["exported_train"] + result["exported_holdout"] == 5


def test_holdout_split_is_strictly_by_order():
    """The holdout must be the LAST 20% by ingested_at (no random leakage)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_csv = os.path.join(tmpdir, "train.csv")
        holdout_csv = os.path.join(tmpdir, "holdout.csv")

        now = datetime.now(timezone.utc)

        class _MockRow:
            def __init__(self, i):
                self.url = f"http://phish{i}.com"
                self.checked_at = now - timedelta(hours=48 + i)
                self.features = {"feed_source": "feed"}

        rows = [_MockRow(i) for i in range(100)]

        class _MockSession:
            def execute(self, stmt):
                return _MockResult(rows)

        class _MockResult:
            def __init__(self, data):
                self._data = data
            def scalars(self):
                return self
            def all(self):
                return self._data

        with patch("ml_pipeline.feed_training_export.LIVE_FEED_CSV", train_csv), \
             patch("ml_pipeline.feed_training_export.LIVE_FEED_HOLDOUT_CSV", holdout_csv), \
             patch("ml_pipeline.feed_training_export.THAI_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.GENERIC_PHISH_SEED_CSV", "/nonexistent"), \
             patch("ml_pipeline.feed_training_export.ensure_dirs"):
            result = export_feed_urls(_MockSession(), since_hours=168, dry_run=False)

        assert result["exported_train"] == 80
        assert result["exported_holdout"] == 20
