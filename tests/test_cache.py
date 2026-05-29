"""Cache behavioural tests: in-process TTLCache, RedisCache, and build_cache."""

from __future__ import annotations

import fnmatch
import time

import pytest

from app.cache import RedisCache, TTLCache, build_cache


class _FakeRedis:
    """Minimal in-memory stand-in for the redis client (no real network).

    Supports just the surface RedisCache uses: ping / get / setex /
    scan_iter / delete. TTL is recorded but not expired (TTLCache already
    covers expiry semantics).
    """

    def __init__(self, *, fail: bool = False):
        self._fail = fail
        self._store: dict[str, str] = {}

    def ping(self):
        if self._fail:
            raise ConnectionError("redis down")
        return True

    def get(self, key):
        return self._store.get(key)

    def setex(self, key, ttl, value):
        self._store[key] = value

    def scan_iter(self, match="*"):
        for k in list(self._store):
            if fnmatch.fnmatch(k, match):
                yield k

    def delete(self, *keys):
        for k in keys:
            self._store.pop(k, None)


class _Settings:
    def __init__(self, **kw):
        self.enable_cache = kw.get("enable_cache", True)
        self.cache_ttl = kw.get("cache_ttl", 60.0)
        self.cache_maxsize = kw.get("cache_maxsize", 2048)
        self.redis_url = kw.get("redis_url", "")
        self.redis_namespace = kw.get("redis_namespace", "phish:cache:")


def test_set_and_get():
    c = TTLCache(ttl=10)
    c.set("a", 1)
    assert c.get("a") == 1


def test_missing_key_returns_none():
    c = TTLCache(ttl=10)
    assert c.get("missing") is None


def test_expired_entry_is_evicted():
    c = TTLCache(ttl=0.05)
    c.set("a", 1)
    assert c.get("a") == 1
    time.sleep(0.08)
    assert c.get("a") is None
    assert len(c) == 0


def test_maxsize_evicts_oldest():
    c = TTLCache(ttl=10, maxsize=3)
    c.set("a", 1); time.sleep(0.01)
    c.set("b", 2); time.sleep(0.01)
    c.set("c", 3); time.sleep(0.01)
    assert len(c) == 3
    c.set("d", 4)
    assert len(c) == 3
    assert c.get("a") is None      # oldest, evicted
    assert c.get("d") == 4


def test_clear():
    c = TTLCache(ttl=10)
    c.set("a", 1); c.set("b", 2)
    assert len(c) == 2
    c.clear()
    assert len(c) == 0
    assert c.get("a") is None


# --- RedisCache (against the fake client) -------------------------------

def _redis_cache():
    return RedisCache(ttl=10, namespace="phish:cache:", client=_FakeRedis())


def test_redis_set_and_get_roundtrips_dict():
    c = _redis_cache()
    payload = {"label": "phishing", "score": 0.97, "url": "http://x"}
    c.set("http://x", payload)
    assert c.get("http://x") == payload  # JSON round-trip preserves the dict


def test_redis_missing_key_returns_none():
    assert _redis_cache().get("nope") is None


def test_redis_clear_and_len():
    c = _redis_cache()
    c.set("a", 1); c.set("b", 2)
    assert len(c) == 2
    c.clear()
    assert len(c) == 0
    assert c.get("a") is None


def test_redis_namespacing_isolates_keys():
    client = _FakeRedis()
    c = RedisCache(ttl=10, namespace="phish:cache:", client=client)
    c.set("k", {"v": 1})
    # Stored under the namespace, not the bare key.
    assert "phish:cache:k" in client._store
    assert "k" not in client._store


# --- build_cache backend selection + fallback --------------------------

def test_build_cache_disabled_returns_none():
    assert build_cache(_Settings(enable_cache=False)) is None


def test_build_cache_no_redis_url_uses_ttlcache():
    assert isinstance(build_cache(_Settings(redis_url="")), TTLCache)


def test_build_cache_unreachable_redis_falls_back(monkeypatch):
    import app.cache as cache_mod

    # Simulate a configured-but-unreachable Redis: RedisCache.__init__ pings
    # and raises, so build_cache must silently fall back to TTLCache.
    def _boom(*a, **k):
        raise ConnectionError("refused")

    monkeypatch.setattr(cache_mod.RedisCache, "__init__", _boom)
    cache = build_cache(_Settings(redis_url="redis://localhost:6390/0"))
    assert isinstance(cache, TTLCache)
