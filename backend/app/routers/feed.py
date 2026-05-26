"""Public threat feed.

Unauthenticated, lightly rate-limited feed of high-confidence phishing URLs
flagged in the last N hours. The point is to make the verdicts useful to
other deployments and tooling without forcing a separate sign-up flow --
this is a public good.

Two formats are served:
  * ``/feed.json``  -- compact JSON list (most callers)
  * ``/feed.csv``   -- spreadsheet-friendly export
  * ``/feed.stix``  -- minimal STIX 2.1 bundle (Indicator objects only;
                       enough for ingestion into TAXII consumers)
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_session
from app.models import Label, UrlCheck

router = APIRouter()

DEFAULT_HOURS = 24
MAX_HOURS = 24 * 14  # 2 weeks


async def _recent_phishing(
    session: AsyncSession, hours: int, limit: int
) -> list[UrlCheck]:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    rows = (
        await session.execute(
            select(UrlCheck)
            .where(UrlCheck.label == Label.phishing)
            .where(UrlCheck.checked_at >= since)
            .order_by(UrlCheck.checked_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


@router.get(
    "/feed.json",
    summary="Public phishing feed (JSON; no auth)",
    response_class=JSONResponse,
)
async def feed_json(
    hours: int = Query(default=DEFAULT_HOURS, ge=1, le=MAX_HOURS),
    limit: int = Query(default=500, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    rows = await _recent_phishing(session, hours, limit)
    body = {
        "schema": "phish.feed.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_hours": hours,
        "count": len(rows),
        "indicators": [
            {
                "url": r.url,
                "score": float(r.score),
                "closest_domain": r.closest_domain,
                "edit_distance": r.edit_distance,
                "checked_at": r.checked_at.isoformat(),
            }
            for r in rows
        ],
    }
    headers = {
        # The feed is cache-friendly: clients can poll every minute.
        "Cache-Control": "public, max-age=60",
    }
    return JSONResponse(content=body, headers=headers)


@router.get(
    "/feed.csv",
    summary="Public phishing feed (CSV; no auth)",
    response_class=StreamingResponse,
)
async def feed_csv(
    hours: int = Query(default=DEFAULT_HOURS, ge=1, le=MAX_HOURS),
    limit: int = Query(default=500, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    rows = await _recent_phishing(session, hours, limit)
    buf = io.StringIO()
    buf.write("﻿")  # UTF-8 BOM for Excel
    writer = csv.writer(buf)
    writer.writerow([
        "url", "score", "closest_domain", "edit_distance", "checked_at",
    ])
    for r in rows:
        writer.writerow([
            r.url, f"{float(r.score):.4f}", r.closest_domain or "",
            r.edit_distance if r.edit_distance is not None else "",
            r.checked_at.isoformat(),
        ])
    body = buf.getvalue().encode("utf-8")
    return StreamingResponse(
        iter([body]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=phish-feed.csv",
            "Cache-Control": "public, max-age=60",
        },
    )


@router.get(
    "/feed.stix",
    summary="Public phishing feed (STIX 2.1 bundle, indicators only)",
    response_class=JSONResponse,
)
async def feed_stix(
    hours: int = Query(default=DEFAULT_HOURS, ge=1, le=MAX_HOURS),
    limit: int = Query(default=500, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Minimal STIX 2.1 bundle.

    Each row becomes an ``indicator`` SDO whose pattern matches the URL.
    The bundle is unsigned and stripped of optional fields TAXII consumers
    don't need; this is intended for one-way ingest, not negotiation.
    """
    rows = await _recent_phishing(session, hours, limit)
    bundle_id = f"bundle--{uuid.uuid4()}"
    objects = []
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    for r in rows:
        objects.append({
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid.uuid4()}",
            "created": r.checked_at.isoformat().replace("+00:00", "Z"),
            "modified": r.checked_at.isoformat().replace("+00:00", "Z"),
            "name": f"Phishing URL targeting {r.closest_domain or 'unknown'}",
            "indicator_types": ["malicious-activity"],
            "pattern_type": "stix",
            "pattern": f"[url:value = '{r.url}']",
            "valid_from": r.checked_at.isoformat().replace("+00:00", "Z"),
            "confidence": int(round(float(r.score) * 100)),
        })
    body = {
        "type": "bundle",
        "id": bundle_id,
        "objects": objects,
        "_meta": {
            "generated_at": now_iso,
            "window_hours": hours,
            "source": "thai-phishing-detector",
        },
    }
    return JSONResponse(content=body, headers={"Cache-Control": "public, max-age=60"})
