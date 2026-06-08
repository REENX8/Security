"""URL check history.

``GET /history``      — admin/API-key scoped, all checks (observability).
``GET /me/history``  — user-scoped, only the signed-in user's own checks.
"""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_history
from app.database import get_session
from app.deps import require_user_id, verify_api_key
from app.schemas import HistoryItem, HistoryResponse

router = APIRouter()


def _to_response(total, limit, offset, rows) -> HistoryResponse:
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
            features=r.features,
            rules=r.rules,
        )
        for r in rows
    ]
    return HistoryResponse(total=total, limit=limit, offset=offset, items=items)


@router.get(
    "/history",
    response_model=HistoryResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List past URL checks (admin/API-key, all users)",
)
async def history(
    limit: int = Query(default=50, ge=1, le=1000),
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
    return _to_response(total, limit, offset, rows)


@router.get(
    "/me/history",
    response_model=HistoryResponse,
    summary="List the signed-in user's own URL checks",
)
async def my_history(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    label: str | None = Query(default=None, pattern="^(safe|suspicious|phishing)$"),
    search: str | None = Query(default=None, max_length=255),
    date_from: dt.datetime | None = Query(default=None),
    date_to: dt.datetime | None = Query(default=None),
    current_user: uuid.UUID = Depends(require_user_id),
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
        user_id=current_user,
    )
    return _to_response(total, limit, offset, rows)
