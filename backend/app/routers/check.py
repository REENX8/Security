"""POST /api/v1/check (single) and /api/v1/check/batch (bulk)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.campaigns import record_campaign
from app.config import settings
from app.crud import insert_check
from app.database import get_session
from app.deps import get_scorer, verify_api_key
from app.errors import AppError
from app.metrics import CACHE_SIZE, CHECK_LATENCY, CHECKS_TOTAL
from app.notifier import maybe_alert
from app.schemas import (
    BatchCheckRequest,
    BatchCheckResponse,
    CheckRequest,
    CheckResponse,
)

router = APIRouter()


async def _score_and_persist(
    request: Request, session: AsyncSession, url: str
) -> dict:
    """Score one URL with caching, persistence and metric updates."""
    scorer = get_scorer(request)
    cache = getattr(request.app.state, "cache", None)

    if cache is not None:
        cached = cache.get(url)
        if cached is not None:
            CHECKS_TOTAL.labels(label=cached["label"], cached="true").inc()
            return {**cached, "cached": True}

    with CHECK_LATENCY.time():
        result = await run_in_threadpool(scorer.score, url)
    # Persist history + cluster the campaign + maybe fire a webhook --
    # ALL of these are observability work. A failure in any one of them
    # must never block the verdict from reaching the user. Scoring is the
    # contract; everything below is best-effort.
    try:
        await insert_check(session, result)
    except Exception as exc:  # noqa: BLE001 - any DB driver/network error
        import logging
        logging.getLogger("phish-detector").warning(
            "history persist skipped (db unreachable): %s", exc
        )

    if settings.enable_campaign_tracking and result["label"] in (
        "phishing", "suspicious"
    ):
        try:
            await record_campaign(
                session,
                url=result["url"],
                closest_domain=result.get("closest_domain"),
            )
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger("phish-detector").warning(
                "campaign clustering skipped: %s", exc
            )

    try:
        await maybe_alert(
            session,
            url=result["url"],
            label=result["label"],
            score=result["score"],
            closest_domain=result.get("closest_domain"),
            reason=result.get("reason", ""),
        )
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger("phish-detector").warning(
            "watchlist alert skipped: %s", exc
        )

    if cache is not None:
        cache.set(url, result)
        CACHE_SIZE.set(len(cache))
    CHECKS_TOTAL.labels(label=result["label"], cached="false").inc()
    return {**result, "cached": False}


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
    result = await _score_and_persist(request, session, payload.url)
    return CheckResponse(**result)


@router.post(
    "/check/batch",
    response_model=BatchCheckResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Analyse a batch of URLs in one request",
)
async def check_batch(
    request: Request,
    payload: BatchCheckRequest,
    session: AsyncSession = Depends(get_session),
) -> BatchCheckResponse:
    if len(payload.urls) > settings.batch_max_size:
        raise AppError(
            f"batch is too large (max {settings.batch_max_size} URLs)",
            code="BATCH_TOO_LARGE",
            status_code=413,
        )
    results = []
    for url in payload.urls:
        result = await _score_and_persist(request, session, url)
        results.append(CheckResponse(**result))
    return BatchCheckResponse(count=len(results), results=results)
