"""Tests for per-user check attribution and scoped history (U2 follow-up).

Verifies the connection between url_checks and user accounts:
  * insert_check(user_id=...) stamps the row and bumps User.check_count
  * get_history(user_id=...) returns only that user's checks
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.crud import get_history, insert_check  # noqa: E402
from app.database import Base  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_maker():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _result(url="http://evil.test/login"):
    return {
        "url": url,
        "score": 0.95,
        "label": "phishing",
        "reason": "typosquat",
        "features": {"is_typosquat": 1},
        "rules": None,
        "closest_domain": "obec.go.th",
        "edit_distance": 1,
    }


async def _make_user(session, email="u@test.local") -> uuid.UUID:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="x",
        role=UserRole.user,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    return user.id


def test_insert_check_attributes_user_and_increments_count():
    async def _run():
        engine, maker = await _make_maker()
        async with maker() as session:
            uid = await _make_user(session)
            row = await insert_check(session, _result(), user_id=uid)
            assert row.user_id == uid

            user = (
                await session.execute(select(User).where(User.id == uid))
            ).scalar_one()
            assert user.check_count == 1

            # A second check bumps the counter again.
            await insert_check(session, _result("http://evil2.test/verify"), user_id=uid)
            user = (
                await session.execute(select(User).where(User.id == uid))
            ).scalar_one()
            assert user.check_count == 2
        await engine.dispose()

    asyncio.run(_run())


def test_insert_check_without_user_leaves_count_untouched():
    async def _run():
        engine, maker = await _make_maker()
        async with maker() as session:
            row = await insert_check(session, _result(), user_id=None)
            assert row.user_id is None
        await engine.dispose()

    asyncio.run(_run())


def test_get_history_scopes_to_user():
    async def _run():
        engine, maker = await _make_maker()
        async with maker() as session:
            alice = await _make_user(session, "alice@test.local")
            bob = await _make_user(session, "bob@test.local")

            await insert_check(session, _result("http://a1.test/login"), user_id=alice)
            await insert_check(session, _result("http://a2.test/login"), user_id=alice)
            await insert_check(session, _result("http://b1.test/login"), user_id=bob)
            await insert_check(session, _result("http://anon.test/login"))

            total_all, _ = await get_history(session)
            assert total_all == 4  # everything, unscoped

            total_alice, rows_alice = await get_history(session, user_id=alice)
            assert total_alice == 2
            assert all(r.user_id == alice for r in rows_alice)

            total_bob, _ = await get_history(session, user_id=bob)
            assert total_bob == 1
        await engine.dispose()

    asyncio.run(_run())


def test_get_history_unknown_user_returns_empty():
    async def _run():
        engine, maker = await _make_maker()
        async with maker() as session:
            await insert_check(session, _result(), user_id=None)
            total, rows = await get_history(session, user_id=uuid.UUID(int=0))
            assert total == 0
            assert rows == []
        await engine.dispose()

    asyncio.run(_run())
