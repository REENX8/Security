"""Brand watchlist CRUD endpoints.

Operators register brand keywords and optional webhooks. The check
pipeline consults the table on every phishing verdict (see
``app.notifier``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import verify_api_key
from app.models import BrandWatch, WebhookDelivery

router = APIRouter()


class BrandWatchIn(BaseModel):
    brand: str = Field(..., min_length=2, max_length=64)
    description: str = Field(default="", max_length=256)
    webhook_url: str | None = Field(default=None, max_length=512)
    enabled: bool = True


class BrandWatchOut(BaseModel):
    id: int
    brand: str
    description: str
    webhook_url: str | None
    enabled: bool
    hit_count: int
    last_hit_at: str | None
    created_at: str


class BrandWatchListResponse(BaseModel):
    total: int
    items: list[BrandWatchOut]


class WebhookDeliveryOut(BaseModel):
    id: int
    brand: str
    url_checked: str
    webhook_url: str
    status_code: int | None
    error: str | None
    attempts: int
    created_at: str


class WebhookDeliveryListResponse(BaseModel):
    total: int
    items: list[WebhookDeliveryOut]


def _watch_to_schema(row: BrandWatch) -> BrandWatchOut:
    return BrandWatchOut(
        id=row.id,
        brand=row.brand,
        description=row.description,
        webhook_url=row.webhook_url,
        enabled=row.enabled,
        hit_count=row.hit_count,
        last_hit_at=row.last_hit_at.isoformat() if row.last_hit_at else None,
        created_at=row.created_at.isoformat(),
    )


@router.get(
    "/watchlist",
    response_model=BrandWatchListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List watched brands",
)
async def list_watchlist(
    session: AsyncSession = Depends(get_session),
) -> BrandWatchListResponse:
    rows = (
        await session.execute(select(BrandWatch).order_by(BrandWatch.brand))
    ).scalars().all()
    return BrandWatchListResponse(
        total=len(rows),
        items=[_watch_to_schema(r) for r in rows],
    )


@router.post(
    "/watchlist",
    response_model=BrandWatchOut,
    status_code=201,
    dependencies=[Depends(verify_api_key)],
    summary="Add a brand to the watchlist",
)
async def add_watch(
    payload: BrandWatchIn,
    session: AsyncSession = Depends(get_session),
) -> BrandWatchOut:
    brand = payload.brand.strip().lower()
    existing = (
        await session.execute(
            select(BrandWatch).where(BrandWatch.brand == brand)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"brand '{brand}' already watched")
    row = BrandWatch(
        brand=brand,
        description=payload.description,
        webhook_url=payload.webhook_url,
        enabled=payload.enabled,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _watch_to_schema(row)


@router.delete(
    "/watchlist/{brand}",
    status_code=204,
    response_model=None,
    dependencies=[Depends(verify_api_key)],
    summary="Remove a brand from the watchlist",
)
async def remove_watch(
    brand: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    brand = brand.strip().lower()
    row = (
        await session.execute(
            select(BrandWatch).where(BrandWatch.brand == brand)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(404, f"brand '{brand}' not watched")
    await session.delete(row)
    await session.commit()


@router.get(
    "/watchlist/deliveries",
    response_model=WebhookDeliveryListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List webhook delivery attempts (most recent first)",
)
async def list_deliveries(
    brand: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> WebhookDeliveryListResponse:
    base = select(WebhookDelivery)
    if brand:
        base = base.where(WebhookDelivery.brand == brand.lower())
    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()
    rows = (
        await session.execute(
            base.order_by(WebhookDelivery.created_at.desc())
            .limit(limit).offset(offset)
        )
    ).scalars().all()
    return WebhookDeliveryListResponse(
        total=total,
        items=[
            WebhookDeliveryOut(
                id=r.id,
                brand=r.brand,
                url_checked=r.url_checked,
                webhook_url=r.webhook_url,
                status_code=r.status_code,
                error=r.error,
                attempts=r.attempts,
                created_at=r.created_at.isoformat(),
            )
            for r in rows
        ],
    )
