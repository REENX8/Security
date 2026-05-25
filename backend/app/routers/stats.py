"""GET /api/v1/stats -- aggregated dashboard statistics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_stats
from app.database import get_session
from app.deps import verify_api_key
from app.schemas import StatsResponse

router = APIRouter()


@router.get(
    "/stats",
    response_model=StatsResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Aggregate detection statistics",
)
async def stats(session: AsyncSession = Depends(get_session)) -> StatsResponse:
    return StatsResponse(**await get_stats(session))
