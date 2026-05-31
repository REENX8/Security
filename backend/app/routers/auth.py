"""POST /api/v1/auth/login — issue a short-lived JWT for the dashboard."""

# NOTE: no `from __future__ import annotations` here — the login route is
# wrapped by slowapi's `@limiter.limit`, whose wrapper does not carry this
# module's globals. Stringized annotations would make FastAPI fail to resolve
# the `LoginRequest` body param (same bug that 422'd /check). Keep them real.

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings
from app.rate_limit import limiter

router = APIRouter()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    """Authenticate with username + password and receive a JWT access token.

    Set ``ADMIN_USERNAME`` / ``ADMIN_PASSWORD_HASH`` / ``JWT_SECRET`` in the
    server environment before deploying to production.
    Generate a bcrypt hash with::

        python -c "from passlib.context import CryptContext; \\
            print(CryptContext(['bcrypt']).hash('yourpassword'))"
    """
    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=503,
            detail="Server-side auth is not configured. Set ADMIN_PASSWORD_HASH.",
        )
    # Constant-time username + password check to resist timing attacks.
    username_ok = body.username == settings.admin_username
    password_ok = _pwd.verify(body.password, settings.admin_password_hash) if settings.admin_password_hash else False
    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    token = jwt.encode(
        {"sub": body.username, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )
