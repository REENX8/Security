"""Tests for user registration, login, and /me endpoint (U9)."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import sqlalchemy as sa

_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.database import Base  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.schemas import RegisterRequest  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


def test_register_request_schema_validates():
    req = RegisterRequest(email="user@example.com", password="Password1!")
    assert req.email == "user@example.com"


def test_register_request_rejects_weak_password():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", password="nodigits")


def test_register_request_rejects_short_password():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", password="Sh0rt!")


def test_user_model_defaults():
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="$2b$12$fakehash",
        role=UserRole.user,
        is_active=True,
        check_count=0,
        display_name="",
    )
    assert user.role == UserRole.user
    assert user.is_active is True
    assert user.check_count == 0
    assert user.display_name == ""


def test_user_role_enum():
    assert UserRole("user") == UserRole.user
    assert UserRole("admin") == UserRole.admin


def test_user_created_in_db():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            user = User(
                id=uuid.uuid4(),
                email="alice@example.com",
                password_hash="$2b$12$fakehash",
                display_name="Alice",
            )
            session.add(user)
            await session.commit()

            found = (
                await session.execute(
                    sa.select(User).where(User.email == "alice@example.com")
                )
            ).scalar_one()
            assert found.display_name == "Alice"
            assert found.role == UserRole.user
            assert found.check_count == 0
        await engine.dispose()
    asyncio.run(_run())


def test_user_email_is_unique():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            u1 = User(id=uuid.uuid4(), email="dup@example.com", password_hash="h1")
            u2 = User(id=uuid.uuid4(), email="dup@example.com", password_hash="h2")
            session.add(u1)
            await session.commit()
            session.add(u2)
            import pytest
            from sqlalchemy.exc import IntegrityError
            with pytest.raises(IntegrityError):
                await session.commit()
        await engine.dispose()
    asyncio.run(_run())


def test_user_check_count_increments():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            user = User(id=uuid.uuid4(), email="counter@example.com", password_hash="h")
            session.add(user)
            await session.commit()

            user.check_count += 1
            await session.commit()

            found = (
                await session.execute(
                    sa.select(User).where(User.email == "counter@example.com")
                )
            ).scalar_one()
            assert found.check_count == 1
        await engine.dispose()
    asyncio.run(_run())


def test_user_role_can_be_changed():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            user = User(id=uuid.uuid4(), email="role@example.com", password_hash="h")
            session.add(user)
            await session.commit()

            user.role = UserRole.admin
            await session.commit()

            found = (
                await session.execute(
                    sa.select(User).where(User.email == "role@example.com")
                )
            ).scalar_one()
            assert found.role == UserRole.admin
        await engine.dispose()
    asyncio.run(_run())


def test_user_can_be_deactivated():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            user = User(id=uuid.uuid4(), email="inactive@example.com", password_hash="h")
            session.add(user)
            await session.commit()

            user.is_active = False
            await session.commit()

            found = (
                await session.execute(
                    sa.select(User).where(User.email == "inactive@example.com")
                )
            ).scalar_one()
            assert found.is_active is False
        await engine.dispose()
    asyncio.run(_run())
