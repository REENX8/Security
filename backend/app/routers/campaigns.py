"""GET /api/v1/campaigns -- list + SIEM/SOAR export of phishing campaign clusters."""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import verify_api_key
from app.models import Campaign

router = APIRouter()


class CampaignOut(BaseModel):
    id: str
    fingerprint: str
    closest_domain: str | None
    tld_signature: str
    path_shape: str
    url_count: int
    first_seen: str
    last_seen: str


class CampaignListResponse(BaseModel):
    total: int
    items: list[CampaignOut]


@router.get(
    "/campaigns",
    response_model=CampaignListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List clustered phishing campaigns",
)
async def list_campaigns(
    min_urls: int = Query(default=1, ge=1, le=100),
    brand: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> CampaignListResponse:
    base = select(Campaign).where(Campaign.url_count >= min_urls)
    if brand:
        # Case-insensitive on both Postgres and SQLite (bare ilike is not).
        base = base.where(func.lower(Campaign.closest_domain).like(f"%{brand.lower()}%"))
    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()
    rows = (
        await session.execute(
            base.order_by(Campaign.last_seen.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return CampaignListResponse(
        total=total,
        items=[
            CampaignOut(
                id=str(r.id),
                fingerprint=r.fingerprint,
                closest_domain=r.closest_domain,
                tld_signature=r.tld_signature,
                path_shape=r.path_shape,
                url_count=r.url_count,
                first_seen=r.first_seen.isoformat(),
                last_seen=r.last_seen.isoformat(),
            )
            for r in rows
        ],
    )


async def _campaigns_for_export(
    session: AsyncSession, min_urls: int, limit: int
) -> list[Campaign]:
    rows = (
        await session.execute(
            select(Campaign)
            .where(Campaign.url_count >= min_urls)
            .order_by(Campaign.last_seen.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


@router.get(
    "/campaigns/export.json",
    dependencies=[Depends(verify_api_key)],
    summary="Export campaign clusters in a SIEM/SOAR-friendly flat schema",
    response_class=JSONResponse,
)
async def export_campaigns_json(
    min_urls: int = Query(default=2, ge=1, le=100),
    limit: int = Query(default=1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Flat, one-object-per-campaign feed for SIEM ingestion (Splunk, Sentinel,
    Elastic). Stable ``schema`` field so parsers can pin a version."""
    rows = await _campaigns_for_export(session, min_urls, limit)
    body = {
        "schema": "phish.campaign.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "count": len(rows),
        "campaigns": [
            {
                "id": str(r.id),
                "fingerprint": r.fingerprint,
                "brand": (r.closest_domain or "").split(".", 1)[0] or None,
                "closest_domain": r.closest_domain,
                "tld_signature": r.tld_signature,
                "path_shape": r.path_shape,
                "url_count": r.url_count,
                "first_seen": r.first_seen.isoformat(),
                "last_seen": r.last_seen.isoformat(),
            }
            for r in rows
        ],
    }
    return JSONResponse(content=body, headers={"Cache-Control": "no-store"})


@router.get(
    "/campaigns/export.stix",
    dependencies=[Depends(verify_api_key)],
    summary="Export campaign clusters as a STIX 2.1 bundle (grouping SDOs)",
    response_class=JSONResponse,
)
async def export_campaigns_stix(
    min_urls: int = Query(default=2, ge=1, le=100),
    limit: int = Query(default=1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """STIX 2.1 bundle of ``grouping`` objects — one per campaign — suitable for
    SOAR platforms that consume STIX. Deterministic ids (uuid5 of fingerprint)
    so re-exports dedupe."""
    rows = await _campaigns_for_export(session, min_urls, limit)
    ns = uuid.UUID("9f1b6e2a-5c2d-4a8e-9b7f-2e1c0a4d6b82")
    objects = []
    for r in rows:
        created = r.first_seen.isoformat().replace("+00:00", "Z")
        modified = r.last_seen.isoformat().replace("+00:00", "Z")
        objects.append({
            "type": "grouping",
            "spec_version": "2.1",
            "id": f"grouping--{uuid.uuid5(ns, r.fingerprint)}",
            "created": created,
            "modified": modified,
            "name": f"Phishing campaign targeting {r.closest_domain or 'unknown'}",
            "context": "suspicious-activity",
            "labels": [f"tld:{r.tld_signature}", f"urls:{r.url_count}"],
        })
    body = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": objects,
        "_meta": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": "thai-phishing-detector",
            "kind": "campaigns",
        },
    }
    return JSONResponse(content=body, headers={"Cache-Control": "no-store"})
