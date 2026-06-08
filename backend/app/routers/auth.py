"""Auth router — login, register, /me."""

# NOTE: no `from __future__ import annotations` here — the login route is
# wrapped by slowapi's `@limiter.limit`, whose wrapper does not carry this
# module's globals. Stringized annotations would make FastAPI fail to resolve
# the body param (same bug that 422'd /check). Keep them real.

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import User, UserRole
from app.rate_limit import limiter
from app.schemas import MeResponse, RegisterRequest

router = APIRouter()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _make_token(sub: str, user_id: str | None = None, role: str = "admin") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict = {"sub": sub, "exp": expire, "role": role}
    if user_id:
        payload["user_id"] = user_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate with username+password (admin) or email+password (user)."""
    # Admin path: username match first.
    if secrets.compare_digest(body.username, settings.admin_username):
        if not settings.admin_password_hash:
            raise HTTPException(
                status_code=503,
                detail="Server-side auth is not configured. Set ADMIN_PASSWORD_HASH.",
            )
        password_ok = _pwd.verify(body.password, settings.admin_password_hash)
        if not password_ok:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        token = _make_token(sub=body.username, role="admin")
        return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)

    # User path: look up by email.
    result = await session.execute(select(User).where(User.email == body.username))
    user = result.scalar_one_or_none()
    if user is None or not _pwd.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()

    token = _make_token(sub=user.email, user_id=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)


@router.post("/auth/register", response_model=TokenResponse, tags=["auth"], status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Register a new user account and immediately return a JWT."""
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        password_hash=_pwd.hash(body.password),
        display_name=body.display_name,
        role=UserRole.user,
        is_active=True,
    )
    session.add(user)
    await session.commit()

    try:
        from app.metrics import USER_REGISTRATIONS
        USER_REGISTRATIONS.inc()
    except Exception:  # noqa: BLE001
        pass

    token = _make_token(sub=user.email, user_id=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)


@router.get("/auth/me", response_model=MeResponse, tags=["auth"])
async def me(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> MeResponse:
    """Return the currently authenticated user's profile."""

    # Extract JWT manually here so we don't import a circular dep via deps.py.
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid token.")

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=403, detail="Admin accounts do not have a user profile.")

    result = await session.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return MeResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
        check_count=user.check_count,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )
