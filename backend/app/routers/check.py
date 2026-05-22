"""POST /api/v1/check -- score a single URL."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.crud import insert_check
from app.database import get_session
from app.deps import get_scorer, verify_api_key
from app.schemas import CheckRequest, CheckResponse

router = APIRouter()


@router.post(
    "/check",
    response_model=CheckResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Analyse a URL and return a phishing verdict",
)
async def check_url(
    request: Request,
    payload: CheckRequest,
    session: AsyncSession = Depends(get_session),
) -> CheckResponse:
    scorer = get_scorer(request)
    # Feature extraction may do (timeout-guarded) network I/O -- run it off
    # the event loop so concurrent requests are not blocked.
    result = await run_in_threadpool(scorer.score, payload.url)
    await insert_check(session, result)
    return CheckResponse(**result)
