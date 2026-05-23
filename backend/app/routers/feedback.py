"""POST /api/v1/feedback — user-reported false positives/negatives."""

from __future__ import annotations

import csv
import io
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import verify_api_key
from app.models import Feedback, FeedbackSource
from app.schemas import FeedbackCreate, FeedbackListResponse, FeedbackOut

router = APIRouter()
logger = logging.getLogger("phish-detector")


def _row_to_schema(row: Feedback) -> FeedbackOut:
    return FeedbackOut(
        id=str(row.id),
        url=row.url,
        verdict_given=row.verdict_given,
        correct_verdict=row.correct_verdict,
        comment=row.comment,
        source=row.source.value,
        created_at=row.created_at.isoformat(),
    )


@router.post(
    "/feedback",
    response_model=FeedbackOut,
    status_code=201,
    summary="Report a wrong verdict (false positive / false negative)",
)
async def create_feedback(
    payload: FeedbackCreate,
    session: AsyncSession = Depends(get_session),
) -> FeedbackOut:
    row = Feedback(
        url=payload.url,
        verdict_given=payload.verdict_given,
        correct_verdict=payload.correct_verdict,
        comment=payload.comment,
        source=FeedbackSource(payload.source),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    logger.info(
        "feedback: %s given=%s correct=%s",
        payload.url, payload.verdict_given, payload.correct_verdict,
    )
    return _row_to_schema(row)


@router.get(
    "/feedback",
    response_model=FeedbackListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="List feedback reports (admin)",
)
async def list_feedback(
    verdict_given: str = Query(default="", max_length=32),
    correct_verdict: str = Query(default="", max_length=32),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> FeedbackListResponse:
    base = select(Feedback)
    if verdict_given:
        base = base.where(Feedback.verdict_given == verdict_given)
    if correct_verdict:
        base = base.where(Feedback.correct_verdict == correct_verdict)

    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()

    rows = (
        await session.execute(
            base.order_by(Feedback.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return FeedbackListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_row_to_schema(r) for r in rows],
    )


@router.get(
    "/feedback/export",
    dependencies=[Depends(verify_api_key)],
    summary="Export all feedback as CSV",
    response_class=StreamingResponse,
)
async def export_feedback(
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    rows = (
        await session.execute(
            select(Feedback).order_by(Feedback.created_at.desc())
        )
    ).scalars().all()

    buf = io.StringIO()
    buf.write("﻿")  # UTF-8 BOM for Excel
    writer = csv.DictWriter(
        buf,
        fieldnames=["created_at", "url", "verdict_given", "correct_verdict",
                    "comment", "source"],
    )
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "created_at": r.created_at.isoformat(),
            "url": r.url,
            "verdict_given": r.verdict_given,
            "correct_verdict": r.correct_verdict,
            "comment": r.comment,
            "source": r.source.value,
        })

    content = buf.getvalue()
    return StreamingResponse(
        iter([content.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=feedback.csv"},
    )
