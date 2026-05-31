"""Tests for the watchlist webhook notifier (C1 coverage)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
import sqlalchemy as sa
from app.database import Base
from app.models import BrandWatch, WebhookDelivery
from app.notifier import _brand_of, _is_line_notify, _line_payload, maybe_alert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


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


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_no_alert_when_not_phishing(session: AsyncSession):
    out = await maybe_alert(
        session, url="http://x", label="safe", score=0.1,
        closest_domain="krungthai.com", reason="",
    )
    assert out == []


@pytest.mark.asyncio
async def test_no_alert_when_brand_not_watched(session: AsyncSession):
    out = await maybe_alert(
        session, url="http://x", label="phishing", score=0.9,
        closest_domain="unwatched.com", reason="",
    )
    assert out == []


@pytest.mark.asyncio
async def test_track_only_watch_increments_but_no_webhook(session: AsyncSession):
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


@pytest.mark.asyncio
async def test_webhook_fires_and_logs_delivery(session: AsyncSession):
    session.add(
        BrandWatch(brand="krungthai", webhook_url="https://hook.example/x", enabled=True)
    )
    await session.commit()

    with patch("app.notifier._post_sync", return_value=(200, None)) as posted:
        out = await maybe_alert(
            session, url="http://phish", label="phishing", score=0.95,
            closest_domain="krungthai.com", reason="lookalike",
        )
    posted.assert_called_once()
    assert len(out) == 1
    assert out[0].status_code == 200

    deliveries = (await session.execute(sa.select(WebhookDelivery))).scalars().all()
    assert len(deliveries) == 1


@pytest.mark.asyncio
async def test_webhook_retries_on_transport_failure(session: AsyncSession):
    session.add(
        BrandWatch(brand="obec", webhook_url="https://hook.example/y", enabled=True)
    )
    await session.commit()

    # First call: transport failure (status None) -> one retry that succeeds.
    with patch("app.notifier._post_sync", side_effect=[(None, "dns"), (200, None)]) as posted, \
            patch("app.notifier.asyncio.sleep", return_value=None):
        out = await maybe_alert(
            session, url="http://phish2", label="phishing", score=0.9,
            closest_domain="obec.go.th", reason="",
        )
    assert posted.call_count == 2
    assert out[0].attempts == 1  # err is None after the successful retry
