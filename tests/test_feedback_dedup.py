"""Tests for feedback deduplication and temporal decay (v1.6.1)."""

from __future__ import annotations

import csv
from math import exp, log


class _StubGen:
    def sim_network(self, label, https):
        return {"whois_ok": 0, "tls_ok": 0}


def _write_feedback_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", "label", "source", "created_at"])
        w.writeheader()
        w.writerows(rows)


def test_dedup_keeps_majority_vote_phishing(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://a.xyz/login", "label": "1", "source": "feedback", "created_at": ""},
        {"url": "https://a.xyz/login", "label": "1", "source": "feedback", "created_at": ""},
        {"url": "https://a.xyz/login", "label": "0", "source": "feedback", "created_at": ""},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 1
    assert rows[0]["label"] == 1


def test_dedup_keeps_majority_vote_safe(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://b.example/page", "label": "1", "source": "feedback", "created_at": ""},
        {"url": "https://b.example/page", "label": "0", "source": "feedback", "created_at": ""},
        {"url": "https://b.example/page", "label": "0", "source": "feedback", "created_at": ""},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 1
    assert rows[0]["label"] == 0


def test_dedup_discards_ties(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://tie.example/", "label": "1", "source": "feedback", "created_at": ""},
        {"url": "https://tie.example/", "label": "0", "source": "feedback", "created_at": ""},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 0


def test_dedup_multiple_urls_deduplicated_independently(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://x.xyz/login", "label": "1", "source": "fb", "created_at": ""},
        {"url": "https://x.xyz/login", "label": "1", "source": "fb", "created_at": ""},
        {"url": "https://y.xyz/page", "label": "0", "source": "fb", "created_at": ""},
        {"url": "https://y.xyz/page", "label": "0", "source": "fb", "created_at": ""},
        {"url": "https://y.xyz/page", "label": "1", "source": "fb", "created_at": ""},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 2
    by_url = {r["url"]: r["label"] for r in rows}
    assert by_url["https://x.xyz/login"] == 1
    assert by_url["https://y.xyz/page"] == 0


def test_temporal_decay_recent_entry_gets_high_weight(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    from datetime import datetime, timezone

    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    recent = datetime.now(timezone.utc).isoformat()
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://c.xyz/login", "label": "1", "source": "fb", "created_at": recent},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 1
    # A very recent entry should have weight very close to 1.0.
    assert rows[0]["sample_weight"] > 0.99


def test_temporal_decay_old_entry_gets_low_weight(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    from datetime import datetime, timedelta, timezone

    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    # ~270 days ago = 3 half-lives, expected weight ≈ 0.125
    old = (datetime.now(timezone.utc) - timedelta(days=270)).isoformat()
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://d.xyz/old", "label": "1", "source": "fb", "created_at": old},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 1
    assert rows[0]["sample_weight"] < 0.20


def test_temporal_decay_missing_timestamp_defaults_to_one(tmp_path, monkeypatch):
    import ml_pipeline.collect_dataset as cd
    monkeypatch.setattr(cd, "FEEDBACK_CSV", str(tmp_path / "fb.csv"))
    _write_feedback_csv(tmp_path / "fb.csv", [
        {"url": "https://e.xyz/", "label": "1", "source": "fb", "created_at": ""},
    ])
    rows = cd._load_feedback_rows(_StubGen(), exclude_urls=set())
    assert len(rows) == 1
    assert rows[0]["sample_weight"] == 1.0


def test_invalid_correct_verdict_rejected_by_schema():
    """correct_verdict must be one of safe / suspicious / phishing."""
    import sys
    from pathlib import Path
    import pytest
    from pydantic import ValidationError

    # Add backend to path so app.schemas is importable independently of conftest.
    backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from app.schemas import FeedbackCreate

    with pytest.raises(ValidationError):
        FeedbackCreate(
            url="https://example.com",
            verdict_given="safe",
            correct_verdict="INVALID_VALUE",
        )
