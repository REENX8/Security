"""GET /api/v1/domain/{host}/history -- reputation timeline for a host."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.deps import verify_api_key
from app.models import UrlCheck

router = APIRouter()


class DomainHistoryDay(BaseModel):
    date: str
    checks: int
    avg_score: float
    max_score: float
    phishing: int
    suspicious: int
    safe: int


class DomainHistoryResponse(BaseModel):
    host: str
    total_checks: int
    first_seen: str | None
    last_seen: str | None
    mean_score: float
    max_score: float
    label_breakdown: dict[str, int]
    timeline: list[DomainHistoryDay]
    recent_urls: list[dict]


@router.get(
    "/domain/{host:path}/history",
    response_model=DomainHistoryResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Reputation timeline for a hostname",
)
async def domain_history(
    host: str,
    session: AsyncSession = Depends(get_session),
) -> DomainHistoryResponse:
    host = host.strip().lower()
    if not host or "/" in host or " " in host:
        raise HTTPException(400, "host must be a bare hostname")

    # Match URLs whose hostname == host. We use a LIKE on the literal URL
    # since UrlCheck does not store host separately. Bounded to recent 90
    # days so the scan stays cheap on default Postgres indexes.
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    rows = (
        await session.execute(
            select(UrlCheck)
            .where(func.lower(UrlCheck.url).like(f"%{host.lower()}%"))
            .where(UrlCheck.checked_at >= since)
            .order_by(UrlCheck.checked_at.desc())
        )
    ).scalars().all()

    # Filter to rows whose actual host matches -- the LIKE will pull in
    # partial matches we want to drop.
    def _host_matches(u: str) -> bool:
        try:
            return (urlparse(u).hostname or "").lower() == host
        except Exception:  # noqa: BLE001
            return False

    rows = [r for r in rows if _host_matches(r.url)]
    if not rows:
        raise HTTPException(404, f"no history for host '{host}'")

    breakdown: dict[str, int] = defaultdict(int)
    per_day: dict[str, list[UrlCheck]] = defaultdict(list)
    for r in rows:
        breakdown[r.label.value] += 1
        per_day[r.checked_at.date().isoformat()].append(r)

    timeline = []
    for day, day_rows in sorted(per_day.items()):
        scores = [float(x.score) for x in day_rows]
        timeline.append(DomainHistoryDay(
            date=day,
            checks=len(day_rows),
            avg_score=round(sum(scores) / len(scores), 4),
            max_score=round(max(scores), 4),
            phishing=sum(1 for x in day_rows if x.label.value == "phishing"),
            suspicious=sum(1 for x in day_rows if x.label.value == "suspicious"),
            safe=sum(1 for x in day_rows if x.label.value == "safe"),
        ))

    scores_all = [float(r.score) for r in rows]
    return DomainHistoryResponse(
        host=host,
        total_checks=len(rows),
        first_seen=rows[-1].checked_at.isoformat(),
        last_seen=rows[0].checked_at.isoformat(),
        mean_score=round(sum(scores_all) / len(scores_all), 4),
        max_score=round(max(scores_all), 4),
        label_breakdown=dict(breakdown),
        timeline=timeline,
        recent_urls=[
            {
                "url": r.url,
                "score": float(r.score),
                "label": r.label.value,
                "checked_at": r.checked_at.isoformat(),
            }
            for r in rows[:20]
        ],
    )
