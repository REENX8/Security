"""Data retention — prune unbounded observability tables (A8).

``url_checks``, ``webhook_delivery`` and ``feed_ingestion_records`` grow without
limit. This purges rows older than a retention window so the database stays
bounded. It is intentionally conservative: configuration tables (whitelist,
brand_watch, external_feed_sources) and campaign clusters are never touched.

Run via ``python -m scripts.retention --days 90`` (cron / Render cron job), or
call :func:`purge_old_rows` from application code.
"""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FeedIngestionRecord, UrlCheck, WebhookDelivery

logger = logging.getLogger("phish-detector")

# (model, timestamp column) pairs that are safe to prune by age.
_PRUNABLE = (
    (UrlCheck, UrlCheck.checked_at),
    (WebhookDelivery, WebhookDelivery.created_at),
    (FeedIngestionRecord, FeedIngestionRecord.ingested_at),
)


async def purge_old_rows(session: AsyncSession, days: int) -> dict[str, int]:
    """Delete observability rows older than ``days``; return per-table counts.

    ``days <= 0`` is a no-op (retention disabled). Deletes are committed once at
    the end so a failure leaves the data intact.
    """
    if days <= 0:
        return {}
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    deleted: dict[str, int] = {}
    for model, ts_col in _PRUNABLE:
        result = await session.execute(delete(model).where(ts_col < cutoff))
        deleted[model.__tablename__] = result.rowcount or 0
    await session.commit()
    logger.info("retention purge (>%dd): %s", days, deleted)
    return deleted
