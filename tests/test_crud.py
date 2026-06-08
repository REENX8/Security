"""Unit tests for crud.py — directly exercises DB helpers."""
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

import pytest  # noqa: E402
from app.crud import get_history, get_stats, insert_check  # noqa: E402
from app.database import Base  # noqa: E402
from app.models import Label  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


def _result(url="http://evil.test/login", label="phishing"):
    return {
        "url": url,
        "score": 0.95,
        "label": label,
        "reason": "typosquat",
        "features": {"is_typosquat": 1},
        "rules": ["TYPOSQUAT_CRED"],
        "closest_domain": "obec.go.th",
        "edit_distance": 1,
    }


def test_insert_check_persists_row():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            row = await insert_check(session, _result())
            assert row.id is not None
            assert row.label == Label.phishing
            assert row.score == pytest.approx(0.95)
        await engine.dispose()
    asyncio.run(_run())


def test_get_history_returns_inserted_row():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await insert_check(session, _result())
            total, rows = await get_history(session)
            assert total == 1
            assert rows[0].url == "http://evil.test/login"
        await engine.dispose()
    asyncio.run(_run())


def test_get_history_label_filter():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await insert_check(session, _result(url="http://phish.test/", label="phishing"))
            await insert_check(session, _result(url="http://safe.test/", label="safe"))
            total, rows = await get_history(session, label="phishing")
            assert total == 1
            assert rows[0].label == Label.phishing
        await engine.dispose()
    asyncio.run(_run())


def test_get_history_search_filter():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await insert_check(session, _result(url="http://krungthai-login.xyz/"))
            await insert_check(session, _result(url="http://unrelated.com/"))
            total, rows = await get_history(session, search="krungthai")
            assert total == 1
            assert "krungthai" in rows[0].url
        await engine.dispose()
    asyncio.run(_run())


def test_get_history_date_filters():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await insert_check(session, _result())
            now = dt.datetime.now(dt.timezone.utc)
            yesterday = now - dt.timedelta(days=1)
            tomorrow = now + dt.timedelta(days=1)
            # date_from + date_to both set
            total, rows = await get_history(session, date_from=yesterday, date_to=tomorrow)
            assert total == 1
            # date_from too recent — should be empty
            total2, _ = await get_history(session, date_from=tomorrow)
            assert total2 == 0
            # date_to too old — should be empty
            total3, _ = await get_history(session, date_to=yesterday)
            assert total3 == 0
        await engine.dispose()
    asyncio.run(_run())


def test_get_stats_with_data():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await insert_check(session, _result(url="http://p1.test/", label="phishing"))
            await insert_check(session, _result(url="http://p2.test/", label="phishing"))
            await insert_check(session, _result(url="http://s.test/", label="safe"))
            stats = await get_stats(session)
            assert stats["total_checks"] == 3
            assert stats["phishing_count"] == 2
            assert stats["safe_count"] == 1
            assert stats["phishing_rate"] == pytest.approx(2 / 3, rel=0.01)
            assert len(stats["checks_per_day"]) == 7
            assert len(stats["checks_by_hour"]) == 24
        await engine.dispose()
    asyncio.run(_run())


def test_get_stats_empty_db():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            stats = await get_stats(session)
            assert stats["total_checks"] == 0
            assert stats["phishing_rate"] == 0.0
        await engine.dispose()
    asyncio.run(_run())
