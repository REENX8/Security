"""Small in-process TTL cache used by /check to dedupe rapid repeated checks.

In a multi-replica deployment this should be replaced with Redis -- see
README.md for the production-hardening notes.
"""

from __future__ import annotations

import time
from threading import Lock


class TTLCache:
    def __init__(self, ttl: float, maxsize: int = 2048) -> None:
        self.ttl = ttl
        self.maxsize = maxsize
        self._data: dict[str, tuple[object, float]] = {}
        self._lock = Lock()

    def get(self, key: str):
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, ts = entry
            if now - ts >= self.ttl:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value) -> None:
        with self._lock:
            if len(self._data) >= self.maxsize:
                # evict the oldest entry (O(n) but n is small)
                oldest = min(self._data, key=lambda k: self._data[k][1])
                self._data.pop(oldest, None)
            self._data[key] = (value, time.time())

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
