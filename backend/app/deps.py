"""Shared FastAPI dependencies."""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.errors import AppError, ModelNotLoadedError

_bearer = HTTPBearer(auto_error=False)


async def optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> uuid.UUID | None:
    """Best-effort: return the authenticated user's UUID, or None.

    Used by endpoints that are usable both anonymously and signed-in (e.g.
    /check, /history). Never raises — a missing, invalid, or admin token
    (admin tokens carry no ``user_id``) simply yields None so the caller is
    treated as anonymous rather than rejected.
    """
    if not credentials:
        return None
    try:
        from jose import jwt

        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        uid = payload.get("user_id")
        return uuid.UUID(uid) if uid else None
    except Exception:  # noqa: BLE001 - any decode/parse error => anonymous
        return None


async def require_user_id(
    user_id: uuid.UUID | None = Depends(optional_user_id),
) -> uuid.UUID:
    """Require a valid *user* JWT and return its UUID.

    Stricter than :func:`require_auth` (which also accepts the static API key and
    admin tokens): this gates endpoints that are inherently per-user, such as a
    user's own check history. Admin/API-key callers carry no ``user_id`` and are
    rejected so they use the unscoped admin endpoints instead.
    """
    if user_id is None:
        raise AppError(
            "A signed-in user account is required for this endpoint.",
            code="USER_AUTH_REQUIRED",
            status_code=401,
        )
    return user_id


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
            from jose import jwt

            payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            if payload.get("sub") == settings.admin_username:
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


def get_asn_provider(request: Request):
    """Return the ASN provider built at startup (None if not configured)."""
    return getattr(request.app.state, "asn_provider", None)
