"""POST /api/v1/check (single) and /api/v1/check/batch (bulk)."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.campaigns import record_campaign
from app.config import settings
from app.content_check import content_score_adjustment
from app.crud import insert_check
from app.database import get_session
from app.deps import get_scorer
from app.errors import AppError
from app.metrics import CACHE_SIZE, CHECK_LATENCY, CHECKS_TOTAL
from app.notifier import maybe_alert
from app.rate_limit import limiter
from app.unshorten import unshorten_url
from app.schemas import (
    BatchCheckRequest,
    BatchCheckResponse,
    CheckRequest,
    CheckResponse,
)

router = APIRouter()

_log = logging.getLogger("phish-detector")

# Bound the number of URLs scored concurrently in a batch. Scoring runs in a
# threadpool (sklearn inference + optional network), so a small ceiling keeps
# latency low without exhausting the default threadpool.
_BATCH_CONCURRENCY = 8


async def _score_url(request: Request, url: str) -> dict:
    """Score one URL (cache, unshorten, model, content fallback). No DB I/O."""
    scorer = get_scorer(request)
    cache = getattr(request.app.state, "cache", None)

    # Expand known short-link URLs (bit.ly, t.co, etc.) before scoring
    if settings.enable_url_unshortening:
        url = await unshorten_url(url, timeout=settings.unshorten_timeout)

    if cache is not None:
        cached = cache.get(url)
        if cached is not None:
            CHECKS_TOTAL.labels(label=cached["label"], cached="true").inc()
            return {**cached, "cached": True}

    with CHECK_LATENCY.time():
        result = await run_in_threadpool(scorer.score, url)

    # Content-based fallback for gray-zone URLs (opt-in, never blocks verdict)
    if (
        settings.gray_zone_content_check
        and settings.threshold_suspicious < result["score"] < settings.threshold_phishing
    ):
        closest = result.get("closest_domain") or ""
        brand_labels = frozenset({closest.split(".")[0]}) if closest else frozenset()
        adj = await content_score_adjustment(
            url, brand_labels, timeout=settings.content_check_timeout
        )
        if adj != 0.0:
            from app.ml.scorer import label_from_score
            new_score = max(0.0, min(1.0, result["score"] + adj))
            result = {**result, "score": new_score, "label": label_from_score(new_score)}

    if cache is not None:
        cache.set(url, result)
        CACHE_SIZE.set(len(cache))
    CHECKS_TOTAL.labels(label=result["label"], cached="false").inc()
    return {**result, "cached": False}


async def _persist_observability(session: AsyncSession, result: dict) -> None:
    """Best-effort history + campaign + webhook work. Never blocks a verdict.

    Persisting history, clustering the campaign and firing a webhook are all
    observability concerns. A failure in any one of them must never stop the
    verdict from reaching the user. Scoring is the contract; this is extra.
    """
    try:
        await insert_check(session, result)
    except Exception as exc:  # noqa: BLE001 - any DB driver/network error
        _log.warning("history persist skipped (db unreachable): %s", exc)

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
            _log.warning("campaign clustering skipped: %s", exc)

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
        _log.warning("watchlist alert skipped: %s", exc)


async def _score_and_persist(
    request: Request, session: AsyncSession, url: str
) -> dict:
    """Score one URL with caching, persistence and metric updates."""
    result = await _score_url(request, url)
    # Cache hits were already persisted on their first sighting; don't dup.
    if not result.get("cached"):
        await _persist_observability(session, result)
    return result


@router.post(
    "/check",
    response_model=CheckResponse,
    summary="Analyse a URL and return a phishing verdict",
)
@limiter.limit(settings.public_check_rate_limit)
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
    summary="Analyse a batch of URLs in one request",
)
@limiter.limit(settings.public_check_rate_limit)
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

    # Score concurrently (CPU/network-bound, threadpool) with a bounded
    # semaphore; gather preserves input order. Persist sequentially afterwards
    # because the AsyncSession is not safe for concurrent use.
    sem = asyncio.Semaphore(_BATCH_CONCURRENCY)

    async def _score_one(u: str) -> dict:
        async with sem:
            return await _score_url(request, u)

    scored = await asyncio.gather(*[_score_one(u) for u in payload.urls])

    results = []
    for result in scored:
        if not result.get("cached"):
            await _persist_observability(session, result)
        results.append(CheckResponse(**result))
    return BatchCheckResponse(count=len(results), results=results)
