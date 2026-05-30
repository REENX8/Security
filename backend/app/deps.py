"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.errors import AppError, ModelNotLoadedError

_bearer = HTTPBearer(auto_error=False)


async def require_auth(
    x_api_key: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """Accept either a static X-API-Key (extension/CLI) or a JWT Bearer token (dashboard).

    Both paths are supported so existing integrations (browser extension, cron jobs)
    keep working while the dashboard migrates to token-based login.
    """
    # --- Static API key path (browser extension, CLI, cron) ---
    if x_api_key and x_api_key == settings.api_key:
        return

    # --- JWT Bearer path (dashboard) ---
    if credentials:
        try:
            from jose import JWTError, jwt

            payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            if payload.get("sub"):
                return
        except Exception:  # noqa: BLE001
            pass

    raise AppError(
        "Authentication required. Provide a valid Bearer token or X-API-Key.",
        code="UNAUTHORIZED",
        status_code=401,
    )


# Alias so all existing routers (which import verify_api_key) need no changes.
verify_api_key = require_auth


def get_scorer(request: Request):
    """Return the loaded scorer, or raise 503 if the model is unavailable."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise ModelNotLoadedError()
    return scorer
