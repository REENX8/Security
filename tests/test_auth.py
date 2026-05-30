"""Tests for the JWT login endpoint and the dual API-key / Bearer auth path.

The login + JWT route was added when the dashboard migrated off the static
API key. These tests cover the happy path, rejection paths, token expiry and
that a minted token actually opens a protected route.
"""

from __future__ import annotations

import datetime as dt

import pytest
from jose import jwt
from passlib.context import CryptContext

from app.config import settings

_PWD = CryptContext(schemes=["bcrypt"], deprecated="auto")
_TEST_PASSWORD = "s3cret-pw"


@pytest.fixture
def auth_config(monkeypatch):
    """Configure server-side credentials for the duration of one test."""
    monkeypatch.setattr(settings, "admin_username", "admin", raising=False)
    monkeypatch.setattr(
        settings, "admin_password_hash", _PWD.hash(_TEST_PASSWORD), raising=False
    )
    monkeypatch.setattr(settings, "jwt_secret", "unit-test-secret", raising=False)
    return settings


def test_login_accepts_valid_credentials(client, auth_config):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": _TEST_PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0

    # The token is a valid JWT carrying the username as subject.
    payload = jwt.decode(
        body["access_token"], "unit-test-secret", algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == "admin"


def test_login_rejects_wrong_password(client, auth_config):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_rejects_unknown_user(client, auth_config):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": _TEST_PASSWORD},
    )
    assert resp.status_code == 401


def test_login_503_when_auth_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_password_hash", "", raising=False)
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": _TEST_PASSWORD},
    )
    assert resp.status_code == 503


def test_jwt_token_opens_protected_route(client, auth_config):
    """A freshly minted token must authenticate a protected endpoint."""
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": _TEST_PASSWORD},
    )
    token = login.json()["access_token"]

    # /api/v1/history requires auth; Bearer token should be accepted.
    resp = client.get(
        "/api/v1/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_expired_jwt_is_rejected(client, auth_config):
    expired = jwt.encode(
        {
            "sub": "admin",
            "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1),
        },
        "unit-test-secret",
        algorithm=settings.jwt_algorithm,
    )
    resp = client.get(
        "/api/v1/history",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert resp.status_code == 401


def test_protected_route_rejects_missing_auth(client):
    resp = client.get("/api/v1/history")
    assert resp.status_code == 401
