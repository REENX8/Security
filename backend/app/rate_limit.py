"""Rate limiting (slowapi).

By default slowapi keeps counters in process memory, which under-counts when
the app runs with multiple workers/replicas (each has its own window). Set
``REDIS_URL`` to share the limit across all workers — the same Redis used for
the /check cache works. If Redis is configured but unreachable at startup we
log a warning and fall back to in-memory storage so a single-node demo / CI
never hard-depends on Redis.
"""

from __future__ import annotations

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger("phish-detector")


def _key(request) -> str:
    """Rate-limit per API key when present, otherwise per client IP."""
    api_key = request.headers.get("x-api-key")
    return api_key or get_remote_address(request)


def resolve_storage_uri(redis_url: str) -> str | None:
    """Return a usable Redis storage URI, or None to use in-memory storage.

    Pings Redis so a misconfigured/unreachable URL degrades gracefully instead
    of failing every request at limit-check time.
    """
    redis_url = (redis_url or "").strip()
    if not redis_url:
        return None
    try:
        import redis  # optional dependency, already pinned in requirements

        client = redis.Redis.from_url(
            redis_url, socket_connect_timeout=2, socket_timeout=2
        )
        client.ping()
        client.close()
        logger.info("rate-limit using shared Redis storage at %s", redis_url)
        return redis_url
    except Exception as exc:  # noqa: BLE001 - any redis/connection error
        logger.warning(
            "rate-limit Redis unavailable (%s) -- using in-memory storage "
            "(per-worker counters)",
            exc,
        )
        return None


limiter = Limiter(
    key_func=_key,
    default_limits=[settings.rate_limit],
    storage_uri=resolve_storage_uri(settings.redis_url),
)
