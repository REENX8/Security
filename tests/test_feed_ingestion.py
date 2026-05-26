"""Tests for external threat feed ingestion (FeedPoller)."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.feed_ingestion import FeedPoller, _url_hash
from app.models import ExternalFeedSource, ExternalFeedSourceType, FeedIngestionRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source(
    name="openphish",
    source_type=ExternalFeedSourceType.openphish,
    feed_url="https://openphish.com/feed.txt",
    api_key=None,
    poll_interval_minutes=60,
) -> ExternalFeedSource:
    src = ExternalFeedSource()
    src.id = 1
    src.name = name
    src.source_type = source_type
    src.feed_url = feed_url
    src.api_key = api_key
    src.poll_interval_minutes = poll_interval_minutes
    src.enabled = True
    src.total_urls_ingested = 0
    src.last_polled_at = None
    src.last_error = None
    return src


def _make_scorer(label="phishing", score=0.95):
    scorer = MagicMock()
    scorer.score.return_value = {
        "url": "http://evil.example.com/login",
        "score": score,
        "label": label,
        "reason": "test",
        "features": {},
        "closest_domain": "kasikornbank.com",
        "edit_distance": 3,
    }
    return scorer


def _make_state(label="phishing", score=0.95):
    return SimpleNamespace(scorer=_make_scorer(label, score))


# ---------------------------------------------------------------------------
# _url_hash
# ---------------------------------------------------------------------------

def test_url_hash_is_sha256():
    url = "http://phishing.example.com/login"
    expected = hashlib.sha256(url.encode()).hexdigest()
    assert _url_hash(url) == expected


def test_url_hash_deterministic():
    url = "http://example.com"
    assert _url_hash(url) == _url_hash(url)


def test_url_hash_different_urls():
    assert _url_hash("http://a.com") != _url_hash("http://b.com")


# ---------------------------------------------------------------------------
# _poll_openphish
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openphish_parse_and_ingest(client):
    """FeedPoller ingests URLs from a mocked OpenPhish plain-text feed."""
    state = _make_state()
    poller = FeedPoller(state)
    source = _make_source()

    feed_text = "\n".join([
        "http://phish1.example.com/login",
        "http://phish2.example.com/verify",
        "not-a-url",
        "",
    ])

    mock_resp = MagicMock()
    mock_resp.text = feed_text
    mock_resp.raise_for_status = MagicMock()

    with patch("app.feed_ingestion.insert_check", new_callable=AsyncMock) as mock_insert, \
         patch("app.feed_ingestion.record_campaign", new_callable=AsyncMock), \
         patch("app.feed_ingestion.maybe_alert", new_callable=AsyncMock), \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        mock_insert.return_value = MagicMock()

        from app.database import SessionLocal
        async with SessionLocal() as session:
            count = await poller._poll_openphish(source, session)

    assert count == 2  # only 2 valid http:// URLs


@pytest.mark.asyncio
async def test_openphish_network_error_propagates(client):
    """Network error from OpenPhish raises so _poll_source can catch it."""
    state = _make_state()
    poller = FeedPoller(state)
    source = _make_source()

    with patch("httpx.AsyncClient") as mock_client_cls:
        import httpx as _httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=_httpx.ConnectError("timeout"))
        mock_client_cls.return_value = mock_client

        from app.database import SessionLocal
        async with SessionLocal() as session:
            with pytest.raises(_httpx.ConnectError):
                await poller._poll_openphish(source, session)


# ---------------------------------------------------------------------------
# _poll_phishtank
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_phishtank_parse_and_ingest(client):
    """FeedPoller ingests URLs from a mocked PhishTank JSON response."""
    state = _make_state()
    poller = FeedPoller(state)
    source = _make_source(
        name="phishtank",
        source_type=ExternalFeedSourceType.phishtank,
        feed_url="https://data.phishtank.com/data/{api_key}/online-valid.json",
    )

    feed_json = [
        {"url": "http://phish3.example.com/verify", "phish_detail_url": "..."},
        {"url": "http://phish4.example.com/login", "phish_detail_url": "..."},
        {"url": "not-a-url"},
    ]

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=feed_json)
    mock_resp.raise_for_status = MagicMock()

    with patch("app.feed_ingestion.insert_check", new_callable=AsyncMock) as mock_insert, \
         patch("app.feed_ingestion.record_campaign", new_callable=AsyncMock), \
         patch("app.feed_ingestion.maybe_alert", new_callable=AsyncMock), \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        mock_insert.return_value = MagicMock()

        from app.database import SessionLocal
        async with SessionLocal() as session:
            count = await poller._poll_phishtank(source, session)

    assert count == 2


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplication_skips_seen_url(client):
    """Same URL from same source is not re-scored on second poll."""
    state = _make_state()
    poller = FeedPoller(state)
    source = _make_source()
    url = "http://phish-dup.example.com/login"

    feed_text = url

    mock_resp = MagicMock()
    mock_resp.text = feed_text
    mock_resp.raise_for_status = MagicMock()

    with patch("app.feed_ingestion.insert_check", new_callable=AsyncMock) as mock_insert, \
         patch("app.feed_ingestion.record_campaign", new_callable=AsyncMock), \
         patch("app.feed_ingestion.maybe_alert", new_callable=AsyncMock), \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client
        mock_insert.return_value = MagicMock()

        from app.database import SessionLocal
        async with SessionLocal() as session:
            count1 = await poller._poll_openphish(source, session)
        async with SessionLocal() as session:
            count2 = await poller._poll_openphish(source, session)

    assert count1 == 1
    assert count2 == 0  # already in FeedIngestionRecord


# ---------------------------------------------------------------------------
# Batch size limit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_size_limit(client):
    """Only external_feed_batch_size URLs are processed per poll."""
    state = _make_state()
    poller = FeedPoller(state)
    source = _make_source(name="openphish-batch")
    source.id = 99

    many_urls = "\n".join(f"http://phish{i}.example.com/login" for i in range(200))

    mock_resp = MagicMock()
    mock_resp.text = many_urls
    mock_resp.raise_for_status = MagicMock()

    with patch("app.feed_ingestion.insert_check", new_callable=AsyncMock) as mock_insert, \
         patch("app.feed_ingestion.record_campaign", new_callable=AsyncMock), \
         patch("app.feed_ingestion.maybe_alert", new_callable=AsyncMock), \
         patch("app.feed_ingestion.settings") as mock_settings, \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_settings.external_feed_batch_size = 10
        mock_settings.enable_campaign_tracking = True

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client
        mock_insert.return_value = MagicMock()

        from app.database import SessionLocal
        async with SessionLocal() as session:
            count = await poller._poll_openphish(source, session)

    assert count <= 10


# ---------------------------------------------------------------------------
# One source failure doesn't stop other sources
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_one_source_failure_others_continue(client):
    """If one source fails to poll, the other source still runs."""
    state = _make_state()
    poller = FeedPoller(state)

    openphish_src = _make_source(name="openphish-err", source_type=ExternalFeedSourceType.openphish)
    openphish_src.id = 10
    phishtank_src = _make_source(
        name="phishtank-ok",
        source_type=ExternalFeedSourceType.phishtank,
        feed_url="https://data.phishtank.com/data/{api_key}/online-valid.json",
    )
    phishtank_src.id = 11

    poll_calls = []

    async def fake_poll_source(src):
        if src.name == "openphish-err":
            raise RuntimeError("network error")
        poll_calls.append(src.name)

    poller._poll_source = fake_poll_source

    with patch("app.feed_ingestion.SessionLocal") as mock_sl:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[openphish_src, phishtank_src])))
        ))
        mock_sl.return_value = mock_session

        await poller.poll_once()

    assert "phishtank-ok" in poll_calls


# ---------------------------------------------------------------------------
# Source stats are updated after poll
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_source_stats_updated(client):
    """last_polled_at and total_urls_ingested are updated after ingestion."""
    from app.database import SessionLocal
    from app.models import ExternalFeedSource, ExternalFeedSourceType

    # Insert a real source into the test DB
    async with SessionLocal() as session:
        src = ExternalFeedSource(
            name="openphish-stats-test",
            source_type=ExternalFeedSourceType.openphish,
            feed_url="https://openphish.com/feed.txt",
            poll_interval_minutes=60,
        )
        session.add(src)
        await session.commit()
        await session.refresh(src)
        src_id = src.id

    state = _make_state()
    poller = FeedPoller(state)

    async with SessionLocal() as session:
        src_row = (await session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(ExternalFeedSource)
            .where(ExternalFeedSource.id == src_id)
        )).scalar_one()
        await poller._update_source_stats(src_id, 5, None, session)

    async with SessionLocal() as session:
        from sqlalchemy import select as _select
        updated = (await session.execute(
            _select(ExternalFeedSource).where(ExternalFeedSource.id == src_id)
        )).scalar_one()

    assert updated.last_polled_at is not None
    assert updated.total_urls_ingested == 5
    assert updated.last_error is None
