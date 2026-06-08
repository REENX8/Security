"""Tests for the watchlist webhook notifier (C1 coverage)."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.database import Base  # noqa: E402
from app.models import BrandWatch, WebhookDelivery  # noqa: E402
from app.notifier import _brand_of, _is_line_notify, _line_payload, maybe_alert  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


def test_brand_of():
    assert _brand_of("krungthai.com") == "krungthai"
    assert _brand_of("OBEC.go.th") == "obec"
    assert _brand_of(None) is None
    assert _brand_of("") is None


def test_is_line_notify():
    assert _is_line_notify("https://notify-api.line.me/api/notify")
    assert not _is_line_notify("https://hooks.slack.com/x")
    assert not _is_line_notify("")


def test_line_payload_contains_fields():
    body = _line_payload({"brand": "krungthai", "url": "http://x", "score": 0.9})
    text = body.decode("utf-8")
    assert "krungthai" in text
    assert "message=" in text


def test_no_alert_when_not_phishing():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            out = await maybe_alert(
                session, url="http://x", label="safe", score=0.1,
                closest_domain="krungthai.com", reason="",
            )
            assert out == []
        await engine.dispose()
    asyncio.run(_run())


def test_no_alert_when_brand_not_watched():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            out = await maybe_alert(
                session, url="http://x", label="phishing", score=0.9,
                closest_domain="unwatched.com", reason="",
            )
            assert out == []
        await engine.dispose()
    asyncio.run(_run())


def test_track_only_watch_increments_but_no_webhook():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            session.add(BrandWatch(brand="krungthai", webhook_url=None, enabled=True))
            await session.commit()
            out = await maybe_alert(
                session, url="http://phish", label="phishing", score=0.95,
                closest_domain="krungthai.com", reason="lookalike",
            )
            assert out == []
            watch = (
                await session.execute(sa.select(BrandWatch).where(BrandWatch.brand == "krungthai"))
            ).scalar_one()
            assert watch.hit_count == 1
            assert watch.last_hit_at is not None
        await engine.dispose()
    asyncio.run(_run())


def test_webhook_fires_and_logs_delivery():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            session.add(
                BrandWatch(brand="krungthai", webhook_url="https://hook.example/x", enabled=True)
            )
            await session.commit()

            # Bypass SSRF guard so we can test webhook delivery logic in isolation.
            with patch("app.net_guard.url_is_safe", return_value=True), \
                    patch("app.notifier._post_sync", return_value=(200, None)) as posted:
                out = await maybe_alert(
                    session, url="http://phish", label="phishing", score=0.95,
                    closest_domain="krungthai.com", reason="lookalike",
                )
            posted.assert_called_once()
            assert len(out) == 1
            assert out[0].status_code == 200

            deliveries = (await session.execute(sa.select(WebhookDelivery))).scalars().all()
            assert len(deliveries) == 1
        await engine.dispose()
    asyncio.run(_run())


def test_webhook_retries_on_transport_failure():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            session.add(
                BrandWatch(brand="obec", webhook_url="https://hook.example/y", enabled=True)
            )
            await session.commit()

            with patch("app.net_guard.url_is_safe", return_value=True), \
                    patch("app.notifier._post_sync", side_effect=[(None, "dns"), (200, None)]) as posted, \
                    patch("app.notifier.asyncio.sleep", return_value=None):
                out = await maybe_alert(
                    session, url="http://phish2", label="phishing", score=0.9,
                    closest_domain="obec.go.th", reason="",
                )
            assert posted.call_count == 2
            assert out[0].attempts == 1
        await engine.dispose()
    asyncio.run(_run())


def test_ssrf_blocked_returns_delivery_with_error():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            session.add(
                BrandWatch(brand="krungthai", webhook_url="http://192.168.1.1/hook", enabled=True)
            )
            await session.commit()

            # SSRF guard returns False (private IP) — must return an error delivery.
            with patch("app.net_guard.url_is_safe", return_value=False):
                out = await maybe_alert(
                    session, url="http://phish", label="phishing", score=0.95,
                    closest_domain="krungthai.com", reason="lookalike",
                )
            assert len(out) == 1
            assert out[0].error == "SSRF_BLOCKED"
            assert out[0].attempts == 0
        await engine.dispose()
    asyncio.run(_run())
