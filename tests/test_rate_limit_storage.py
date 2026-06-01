"""Tests for the Redis rate-limit storage resolver (A5)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.rate_limit import resolve_storage_uri


def test_empty_redis_url_returns_none():
    assert resolve_storage_uri("") is None
    assert resolve_storage_uri("   ") is None


def test_reachable_redis_returns_uri():
    fake_client = MagicMock()
    fake_redis = MagicMock()
    fake_redis.Redis.from_url.return_value = fake_client
    with patch.dict("sys.modules", {"redis": fake_redis}):
        uri = resolve_storage_uri("redis://localhost:6379/0")
    assert uri == "redis://localhost:6379/0"
    fake_client.ping.assert_called_once()


def test_unreachable_redis_falls_back_to_none():
    fake_client = MagicMock()
    fake_client.ping.side_effect = OSError("connection refused")
    fake_redis = MagicMock()
    fake_redis.Redis.from_url.return_value = fake_client
    with patch.dict("sys.modules", {"redis": fake_redis}):
        uri = resolve_storage_uri("redis://unreachable:6379/0")
    assert uri is None
