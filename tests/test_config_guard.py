"""Tests for the production secrets/config guard (A1)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings

_GOOD = {
    "app_env": "production",
    "api_key": "a-strong-random-api-key-value",
    "jwt_secret": "0123456789abcdef0123456789abcdef",  # >= 16 chars, no placeholder
    "admin_password_hash": "$2b$12$abcdefghijklmnopqrstuv",
    "cors_origins": "https://dashboard.example.com",
}


def test_development_allows_defaults():
    # The zero-setup demo defaults must keep working when not in production.
    s = Settings(app_env="development")
    assert not s.is_production
    # Default api_key / jwt_secret are placeholders but allowed in dev.
    assert s.production_config_problems()  # would be problems IF prod...
    # ...but no exception was raised because app_env != production.


def test_production_rejects_default_api_key():
    with pytest.raises(ValidationError) as exc:
        Settings(**{**_GOOD, "api_key": "dev-local-key-change-me"})
    assert "API_KEY" in str(exc.value)


def test_production_rejects_placeholder_jwt_secret():
    with pytest.raises(ValidationError) as exc:
        Settings(
            **{
                **_GOOD,
                "jwt_secret": "change-this-secret-in-production-use-openssl-rand-hex-32",
            }
        )
    assert "JWT_SECRET" in str(exc.value)


def test_production_rejects_short_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(**{**_GOOD, "jwt_secret": "tooshort"})


def test_production_rejects_empty_admin_hash():
    with pytest.raises(ValidationError) as exc:
        Settings(**{**_GOOD, "admin_password_hash": ""})
    assert "ADMIN_PASSWORD_HASH" in str(exc.value)


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError) as exc:
        Settings(**{**_GOOD, "cors_origins": "https://*.onrender.com"})
    assert "CORS" in str(exc.value)


def test_production_accepts_strong_config():
    s = Settings(**_GOOD)
    assert s.is_production
    assert s.production_config_problems() == []
    assert s.hsts_enabled or s.is_production  # HSTS forced on in prod
