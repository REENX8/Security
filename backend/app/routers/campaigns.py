"""GET /api/v1/campaigns -- list phishing campaign clusters."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
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
