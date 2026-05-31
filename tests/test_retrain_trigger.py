"""Tests for the volume-based auto-retrain trigger (C9)."""
from __future__ import annotations

import types
from unittest.mock import AsyncMock, patch

import pytest
from app import retrain_trigger
from app.database import Base
from app.models import Feedback, FeedbackSource
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


@pytest.mark.asyncio
async def test_no_trigger_when_disabled(session, monkeypatch):
    monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", False)
    await _add_feedback(session, 50)
    assert await retrain_trigger.maybe_trigger_retrain(_state(), session) is False


@pytest.mark.asyncio
async def test_no_trigger_below_threshold(session, monkeypatch):
    monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
    monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 20)
    await _add_feedback(session, 5)
    assert await retrain_trigger.maybe_trigger_retrain(_state(), session) is False


@pytest.mark.asyncio
async def test_triggers_at_threshold(session, monkeypatch):
    monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
    monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
    await _add_feedback(session, 12)
    state = _state()
    with patch.object(retrain_trigger, "_run_retrain_bg", new=AsyncMock()) as bg:
        triggered = await retrain_trigger.maybe_trigger_retrain(state, session)
    assert triggered is True
    assert state.retrain_in_progress is True
    assert state.retrain_baseline_count == 12
    # give the scheduled task a tick to be created
    bg.assert_called_once()


@pytest.mark.asyncio
async def test_no_double_trigger_while_running(session, monkeypatch):
    monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
    monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
    await _add_feedback(session, 50)
    state = _state()
    state.retrain_in_progress = True  # a retrain is already running
    assert await retrain_trigger.maybe_trigger_retrain(state, session) is False


@pytest.mark.asyncio
async def test_baseline_prevents_retrigger(session, monkeypatch):
    monkeypatch.setattr(retrain_trigger.settings, "feedback_retrain_enabled", True)
    monkeypatch.setattr(retrain_trigger.settings, "feedback_accumulation_threshold", 10)
    await _add_feedback(session, 12)
    state = _state()
    state.retrain_baseline_count = 12  # already retrained at 12 rows
    assert await retrain_trigger.maybe_trigger_retrain(state, session) is False
