"""GET/POST/DELETE /api/v1/admin/whitelist — whitelist management."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from phish_features import Whitelist
from phish_features.whitelist import WhitelistEntry as PhishWhitelistEntry

from app.database import get_session
from app.deps import verify_api_key
from app.models import DbWhitelistEntry
from app.schemas import (
    WhitelistEntryIn,
    WhitelistEntryOut,
    WhitelistListResponse,
)

router = APIRouter()
logger = logging.getLogger("phish-detector")


def _row_to_schema(row: DbWhitelistEntry) -> WhitelistEntryOut:
    return WhitelistEntryOut(
        id=row.id,
        domain=row.domain,
        agency_name=row.agency_name,
        category=row.category,
        added_by=row.added_by,
        is_seeded=row.is_seeded,
        created_at=row.created_at.isoformat(),
    )


async def _hot_reload_whitelist(request: Request, session: AsyncSession) -> None:
    """Replace the scorer's in-memory whitelist from the DB without restart."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        return
    rows = (await session.execute(select(DbWhitelistEntry))).scalars().all()
    entries = [
        PhishWhitelistEntry(
            domain=r.domain,
            agency_name=r.agency_name,
            category=r.category,
        )
        for r in rows
    ]
    scorer.extractor.whitelist = Whitelist.from_entries(entries)
    logger.info("whitelist hot-reloaded: %d entries", len(entries))


@router.get(
    "/admin/whitelist",
    response_model=WhitelistListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List trusted domains in the whitelist",
)
async def list_whitelist(
    search: str = Query(default="", max_length=255),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> WhitelistListResponse:
    base = select(DbWhitelistEntry)
    if search:
        base = base.where(DbWhitelistEntry.domain.ilike(f"%{search}%"))

    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()

    rows = (
        await session.execute(
            base.order_by(DbWhitelistEntry.domain).limit(limit).offset(offset)
        )
    ).scalars().all()

    return WhitelistListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_row_to_schema(r) for r in rows],
    )


@router.post(
    "/admin/whitelist",
    response_model=WhitelistEntryOut,
    status_code=201,
    dependencies=[Depends(verify_api_key)],
    summary="Add a domain to the whitelist",
)
async def add_whitelist_entry(
    request: Request,
    payload: WhitelistEntryIn,
    session: AsyncSession = Depends(get_session),
) -> WhitelistEntryOut:
    domain = payload.domain.strip().lower()
    existing = (
        await session.execute(
            select(DbWhitelistEntry).where(DbWhitelistEntry.domain == domain)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"domain '{domain}' already in whitelist")

    row = DbWhitelistEntry(
        domain=domain,
        agency_name=payload.agency_name,
        category=payload.category,
        added_by="admin",
        is_seeded=False,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    await _hot_reload_whitelist(request, session)
    logger.info("whitelist: added %s", domain)
    return _row_to_schema(row)


@router.delete(
    "/admin/whitelist/{domain:path}",
    status_code=204,
    response_model=None,
    dependencies=[Depends(verify_api_key)],
    summary="Remove a domain from the whitelist",
)
async def delete_whitelist_entry(
    request: Request,
    domain: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    domain = domain.strip().lower()
    row = (
        await session.execute(
            select(DbWhitelistEntry).where(DbWhitelistEntry.domain == domain)
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"domain '{domain}' not found")

    await session.delete(row)
    await session.commit()
    await _hot_reload_whitelist(request, session)
    logger.info("whitelist: removed %s", domain)
