"""Rate limiting (slowapi)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _key(request) -> str:
    """Rate-limit per API key when present, otherwise per client IP."""
    api_key = request.headers.get("x-api-key")
    return api_key or get_remote_address(request)


limiter = Limiter(key_func=_key, default_limits=[settings.rate_limit])
