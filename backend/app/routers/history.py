"""GET /api/v1/history -- paginated, filterable check history."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_history
from app.database import get_session
from app.deps import verify_api_key
from app.schemas import HistoryItem, HistoryResponse

router = APIRouter()


@router.get(
    "/history",
    response_model=HistoryResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List past URL checks",
)
async def history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    label: str | None = Query(default=None, pattern="^(safe|suspicious|phishing)$"),
    search: str | None = Query(default=None, max_length=255),
    date_from: dt.datetime | None = Query(default=None),
    date_to: dt.datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> HistoryResponse:
    total, rows = await get_history(
        session,
        limit=limit,
        offset=offset,
        label=label,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    items = [
        HistoryItem(
            id=str(r.id),
            url=r.url,
            score=r.score,
            label=r.label.value,
            reason=r.reason,
            closest_domain=r.closest_domain,
            edit_distance=r.edit_distance,
            checked_at=r.checked_at.isoformat(),
        )
        for r in rows
    ]
    return HistoryResponse(total=total, limit=limit, offset=offset, items=items)
