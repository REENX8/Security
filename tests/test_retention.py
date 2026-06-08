"""Tests for the data-retention purge (A8)."""
from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.database import Base  # noqa: E402
from app.models import Label, UrlCheck  # noqa: E402
from app.retention import purge_old_rows  # noqa: E402
from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def _add_check(session, *, age_days: int):
    ts = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=age_days)
    session.add(
        UrlCheck(url="http://x.test", score=0.9, label=Label.phishing, checked_at=ts)
    )
    await session.commit()


def test_purge_deletes_old_and_keeps_recent():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await _add_check(session, age_days=120)
            await _add_check(session, age_days=10)

            deleted = await purge_old_rows(session, days=90)
            assert deleted["url_checks"] == 1

            remaining = (
                await session.execute(select(func.count()).select_from(UrlCheck))
            ).scalar_one()
            assert remaining == 1
        await engine.dispose()
    asyncio.run(_run())


def test_zero_days_is_noop():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await _add_check(session, age_days=999)
            assert await purge_old_rows(session, days=0) == {}
            remaining = (
                await session.execute(select(func.count()).select_from(UrlCheck))
            ).scalar_one()
            assert remaining == 1
        await engine.dispose()
    asyncio.run(_run())
