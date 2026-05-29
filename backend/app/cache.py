"""Caching for /check to dedupe rapid repeated checks.

Two interchangeable backends with the SAME interface (``get`` / ``set`` /
``clear`` / ``len``):

  * :class:`TTLCache` -- in-process, per-replica. Zero setup; the default.
  * :class:`RedisCache` -- shared across replicas for a horizontally-scaled
    deployment. Selected automatically when ``REDIS_URL`` is configured.

:func:`build_cache` picks the backend from settings and -- crucially --
falls back to the in-process cache if Redis is configured but unreachable,
so a single-node demo (and CI) never depends on a live Redis.
"""

from __future__ import annotations

import json
import logging
import time
from threading import Lock

logger = logging.getLogger("phish-detector")


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


class RedisCache:
    """Redis-backed cache with the same interface as :class:`TTLCache`.

    Values are JSON-serialised (the /check result is a plain dict) and stored
    with ``SETEX`` so Redis enforces the TTL. Keys are namespaced so ``clear``
    and ``len`` only touch this app's entries and never ``FLUSHDB``.

    A synchronous client is used on purpose: the interface mirrors TTLCache so
    no call site changes, and a localhost/VPC Redis ``GET``/``SETEX`` is
    sub-millisecond -- negligible next to the WHOIS/TLS lookups that scoring
    already runs in a worker thread.
    """

    def __init__(
        self,
        ttl: float,
        redis_url: str | None = None,
        namespace: str = "phish:cache:",
        client=None,
    ) -> None:
        self.ttl = ttl
        self._ns = namespace
        if client is not None:
            self._r = client
        else:
            import redis  # local import keeps redis an optional dependency

            self._r = redis.Redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
        # Fail fast so build_cache() can fall back to the in-process cache.
        self._r.ping()

    def _key(self, key: str) -> str:
        return f"{self._ns}{key}"

    def get(self, key: str):
        raw = self._r.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    def set(self, key: str, value) -> None:
        self._r.setex(
            self._key(key), max(int(self.ttl), 1), json.dumps(value, default=str)
        )

    def clear(self) -> None:
        keys = list(self._r.scan_iter(match=f"{self._ns}*"))
        if keys:
            self._r.delete(*keys)

    def __len__(self) -> int:
        return sum(1 for _ in self._r.scan_iter(match=f"{self._ns}*"))


def build_cache(settings):
    """Construct the cache backend from settings.

    Returns ``None`` when caching is disabled, a :class:`RedisCache` when a
    reachable ``redis_url`` is configured, and a :class:`TTLCache` otherwise
    (including when Redis is configured but cannot be reached).
    """
    if not getattr(settings, "enable_cache", True):
        return None

    redis_url = (getattr(settings, "redis_url", "") or "").strip()
    if redis_url:
        try:
            cache = RedisCache(
                ttl=settings.cache_ttl,
                redis_url=redis_url,
                namespace=getattr(settings, "redis_namespace", "phish:cache:"),
            )
            logger.info("using Redis cache at %s", redis_url)
            return cache
        except Exception as exc:  # noqa: BLE001 - any redis/connection error
            logger.warning(
                "Redis cache unavailable (%s) -- falling back to in-process "
                "TTLCache",
                exc,
            )

    return TTLCache(ttl=settings.cache_ttl, maxsize=settings.cache_maxsize)
