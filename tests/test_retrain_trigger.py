"""Tests for the volume-based auto-retrain trigger (C9)."""
from __future__ import annotations

import asyncio
import os
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app import retrain_trigger  # noqa: E402
from app.database import Base  # noqa: E402
from app.models import Feedback, FeedbackSource  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


async def _add_feedback(session, n: int):
    for i in range(n):
        session.add(
            Feedback(
                url=f"http://x{i}.test",
                verdict_given="safe",
                correct_verdict="phishing",
                source=FeedbackSource.api,
            )
        )
    await session.commit()


def _state():
    return types.SimpleNamespace(retrain_in_progress=False, retrain_baseline_count=0)


def test_no_trigger_when_disabled(monkeypatch):
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", False)
            await _add_feedback(session, 50)
            assert await retrain_trigger.maybe_trigger_retrain(_state(), session) is False
        await engine.dispose()
    asyncio.run(_run())


def test_no_trigger_below_threshold(monkeypatch):
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
            monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 20)
            await _add_feedback(session, 5)
            assert await retrain_trigger.maybe_trigger_retrain(_state(), session) is False
        await engine.dispose()
    asyncio.run(_run())


def test_triggers_at_threshold(monkeypatch):
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
            monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
            await _add_feedback(session, 12)
            state = _state()
            with patch.object(retrain_trigger, "_run_retrain_bg", new=AsyncMock()) as bg:
                triggered = await retrain_trigger.maybe_trigger_retrain(state, session)
            assert triggered is True
            assert state.retrain_in_progress is True
            assert state.retrain_baseline_count == 12
            bg.assert_called_once()
        await engine.dispose()
    asyncio.run(_run())


def test_no_double_trigger_while_running(monkeypatch):
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
            monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
            await _add_feedback(session, 50)
            state = _state()
            state.retrain_in_progress = True
            assert await retrain_trigger.maybe_trigger_retrain(state, session) is False
        await engine.dispose()
    asyncio.run(_run())


def test_baseline_prevents_retrigger(monkeypatch):
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
            monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
            await _add_feedback(session, 12)
            state = _state()
            state.retrain_baseline_count = 12
            assert await retrain_trigger.maybe_trigger_retrain(state, session) is False
        await engine.dispose()
    asyncio.run(_run())
