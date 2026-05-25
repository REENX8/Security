"""TTLCache behavioural tests."""

from __future__ import annotations

import time

from app.cache import TTLCache


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
