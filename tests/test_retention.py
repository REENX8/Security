"""Tests for the data-retention purge (A8)."""
from __future__ import annotations

import datetime as dt

import pytest
from app.database import Base
from app.models import Label, UrlCheck
from app.retention import purge_old_rows
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _add_check(session, *, age_days: int):
    ts = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=age_days)
    session.add(
        UrlCheck(url="http://x.test", score=0.9, label=Label.phishing, checked_at=ts)
    )
    await session.commit()


@pytest.mark.asyncio
async def test_purge_deletes_old_and_keeps_recent(session):
    await _add_check(session, age_days=120)
    await _add_check(session, age_days=10)

    deleted = await purge_old_rows(session, days=90)
    assert deleted["url_checks"] == 1

    remaining = (
        await session.execute(select(func.count()).select_from(UrlCheck))
    ).scalar_one()
    assert remaining == 1  # the 10-day-old row survives


@pytest.mark.asyncio
async def test_zero_days_is_noop(session):
    await _add_check(session, age_days=999)
    assert await purge_old_rows(session, days=0) == {}
    remaining = (
        await session.execute(select(func.count()).select_from(UrlCheck))
    ).scalar_one()
    assert remaining == 1
