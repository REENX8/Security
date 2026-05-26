"""Background service that polls external threat feeds (OpenPhish, PhishTank).

URLs fetched from external sources are scored through the same pipeline as
user-submitted URLs: extract features → ML verdict → persist → campaign cluster
→ brand watchlist alert.  FeedIngestionRecord prevents the same URL from being
re-scored on every poll cycle.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.campaigns import record_campaign
from app.config import settings
from app.crud import insert_check
from app.database import SessionLocal
from app.metrics import FEED_POLL_ERRORS, FEED_URLS_INGESTED
from app.models import ExternalFeedSource, ExternalFeedSourceType, FeedIngestionRecord
from app.notifier import maybe_alert

logger = logging.getLogger("phish-detector.feed-ingestion")

FETCH_TIMEOUT = httpx.Timeout(30.0)


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8", errors="replace")).hexdigest()


class FeedPoller:
    def __init__(self, app_state) -> None:
        self._state = app_state

    async def run_forever(self) -> None:
        logger.info("feed poller started (interval=%dm)", settings.external_feed_poll_interval)
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.error("feed poller unhandled error: %s", exc)
            await asyncio.sleep(settings.external_feed_poll_interval * 60)

    async def poll_once(self) -> None:
        async with SessionLocal() as session:
            sources = (
                await session.execute(
                    select(ExternalFeedSource).where(ExternalFeedSource.enabled.is_(True))
                )
            ).scalars().all()

        if not sources:
            logger.debug("feed poller: no enabled sources")
            return

        await asyncio.gather(
            *[self._poll_source(src) for src in sources],
            return_exceptions=True,
        )

    # ------------------------------------------------------------------
    # Per-source dispatch
    # ------------------------------------------------------------------

    async def _poll_source(self, source: ExternalFeedSource) -> None:
        try:
            async with SessionLocal() as session:
                if source.source_type == ExternalFeedSourceType.openphish:
                    count = await self._poll_openphish(source, session)
                else:
                    count = await self._poll_phishtank(source, session)
            logger.info("feed poll complete: source=%s ingested=%d", source.name, count)
        except Exception as exc:  # noqa: BLE001
            FEED_POLL_ERRORS.labels(source=source.name).inc()
            logger.error("feed poll failed: source=%s error=%s", source.name, exc)
            async with SessionLocal() as session:
                await self._update_source_stats(source.id, 0, str(exc)[:480], session)

    # ------------------------------------------------------------------
    # OpenPhish: plain-text feed, one URL per line
    # ------------------------------------------------------------------

    async def _poll_openphish(self, source: ExternalFeedSource, session) -> int:
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
            resp = await client.get(source.feed_url)
            resp.raise_for_status()

        urls = [line.strip() for line in resp.text.splitlines() if line.strip().startswith("http")]
        return await self._ingest_urls(urls, source, session)

    # ------------------------------------------------------------------
    # PhishTank: JSON API
    # ------------------------------------------------------------------

    async def _poll_phishtank(self, source: ExternalFeedSource, session) -> int:
        api_key = source.api_key or settings.phishtank_api_key
        feed_url = source.feed_url
        if api_key:
            feed_url = feed_url.replace("{api_key}", api_key)

        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "thai-phish-detector/1.1"})
            resp.raise_for_status()

        entries = resp.json()
        if isinstance(entries, dict):
            entries = entries.get("entries", [])

        urls = [
            e.get("url") or e.get("phish_detail_url", "")
            for e in entries
            if isinstance(e, dict)
        ]
        urls = [u for u in urls if u and u.startswith("http")]
        return await self._ingest_urls(urls, source, session)

    # ------------------------------------------------------------------
    # Common ingestion loop
    # ------------------------------------------------------------------

    async def _ingest_urls(
        self, urls: list[str], source: ExternalFeedSource, session
    ) -> int:
        scorer = getattr(self._state, "scorer", None)
        if scorer is None:
            logger.warning("feed ingest skipped: scorer not ready")
            return 0

        ingested = 0
        batch = urls[: settings.external_feed_batch_size]

        for url in batch:
            url_hash = _url_hash(url)
            if not await self._is_new_url(url_hash, source.id, session):
                continue

            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, scorer.score, url
                )
                row = await insert_check(session, result)

                if settings.enable_campaign_tracking and result.get("label") == "phishing":
                    await record_campaign(
                        session,
                        url=url,
                        closest_domain=result.get("closest_domain"),
                    )

                await maybe_alert(
                    session,
                    url=url,
                    label=result["label"],
                    score=result["score"],
                    closest_domain=result.get("closest_domain"),
                    reason=result.get("reason", ""),
                )

                await self._mark_ingested(url_hash, source.id, session)
                FEED_URLS_INGESTED.labels(source=source.name).inc()
                ingested += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("feed ingest: failed to score %s: %s", url[:120], exc)

        await self._update_source_stats(source.id, ingested, None, session)
        return ingested

    # ------------------------------------------------------------------
    # Deduplication helpers
    # ------------------------------------------------------------------

    async def _is_new_url(self, url_hash: str, source_id: int, session) -> bool:
        existing = (
            await session.execute(
                select(FeedIngestionRecord).where(
                    FeedIngestionRecord.url_hash == url_hash,
                    FeedIngestionRecord.source_id == source_id,
                )
            )
        ).scalar_one_or_none()
        return existing is None

    async def _mark_ingested(self, url_hash: str, source_id: int, session) -> None:
        record = FeedIngestionRecord(url_hash=url_hash, source_id=source_id)
        session.add(record)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()

    async def _update_source_stats(
        self, source_id: int, count: int, error: str | None, session
    ) -> None:
        src = (
            await session.execute(
                select(ExternalFeedSource).where(ExternalFeedSource.id == source_id)
            )
        ).scalar_one_or_none()
        if src is None:
            return
        src.last_polled_at = dt.datetime.now(dt.timezone.utc)
        src.last_error = error
        if count > 0:
            src.total_urls_ingested += count
        await session.commit()
