"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, Request

from app.config import settings
from app.errors import AppError, ModelNotLoadedError


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject requests without a valid ``X-API-Key`` header."""
    if not x_api_key or x_api_key != settings.api_key:
        raise AppError(
            "Missing or invalid API key.",
            code="INVALID_API_KEY",
            status_code=401,
        )


def get_scorer(request: Request):
    """Return the loaded scorer, or raise 503 if the model is unavailable."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise ModelNotLoadedError()
    return scorer
