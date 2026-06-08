"""Tests for false-negative/false-positive rate gauge updates (v1.6.1)."""

from __future__ import annotations

import asyncio
import os
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("ENABLE_WHOIS", "false")
os.environ.setdefault("ENABLE_TLS", "false")

from app.database import Base
from app.models import Feedback, FeedbackSource
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _make_session_factory():
    engine = create_async_engine("sqlite+aiosqlite://")
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _setup_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _add(session, verdict_given, correct_verdict):
    session.add(
        Feedback(
            url="https://x.example",
            verdict_given=verdict_given,
            correct_verdict=correct_verdict,
            source=FeedbackSource.api,
        )
    )
    await session.commit()


def test_fn_gauge_updated_on_retrain_trigger():
    from app import retrain_trigger
    from app.metrics import FALSE_NEGATIVE_RATE, FALSE_POSITIVE_RATE

    async def _run():
        engine, maker = _make_session_factory()
        await _setup_db(engine)
        async with maker() as session:
            await _add(session, "safe", "phishing")  # 1 FN
            state = types.SimpleNamespace(
                retrain_in_progress=False, retrain_baseline_count=0
            )
            with (
                patch.object(
                    retrain_trigger.settings, "feedback_retrain_enabled", True
                ),
                patch.object(
                    retrain_trigger.settings, "feedback_accumulation_threshold", 1
                ),
                patch.object(retrain_trigger, "_run_retrain_bg", new=AsyncMock()),
            ):
                await retrain_trigger.maybe_trigger_retrain(state, session)
        await engine.dispose()

    asyncio.run(_run())

    assert FALSE_NEGATIVE_RATE._value.get() == pytest.approx(1.0, abs=1e-3)
    assert FALSE_POSITIVE_RATE._value.get() == pytest.approx(0.0, abs=1e-3)


def test_fp_gauge_updated_on_retrain_trigger():
    from app import retrain_trigger
    from app.metrics import FALSE_NEGATIVE_RATE, FALSE_POSITIVE_RATE

    async def _run():
        engine, maker = _make_session_factory()
        await _setup_db(engine)
        async with maker() as session:
            await _add(session, "phishing", "safe")  # 1 FP
            state = types.SimpleNamespace(
                retrain_in_progress=False, retrain_baseline_count=0
            )
            with (
                patch.object(
                    retrain_trigger.settings, "feedback_retrain_enabled", True
                ),
                patch.object(
                    retrain_trigger.settings, "feedback_accumulation_threshold", 1
                ),
                patch.object(retrain_trigger, "_run_retrain_bg", new=AsyncMock()),
            ):
                await retrain_trigger.maybe_trigger_retrain(state, session)
        await engine.dispose()

    asyncio.run(_run())

    assert FALSE_POSITIVE_RATE._value.get() == pytest.approx(1.0, abs=1e-3)
