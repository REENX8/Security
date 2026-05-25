"""Database read/write helpers for url_checks."""

from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Label, UrlCheck


async def insert_check(session: AsyncSession, result: dict) -> UrlCheck:
    """Persist a scoring result and return the stored row."""
    row = UrlCheck(
        url=result["url"][:2048],
        score=result["score"],
        label=Label(result["label"]),
        reason=result["reason"][:512],
        features=result["features"],
        closest_domain=result.get("closest_domain"),
        edit_distance=result.get("edit_distance"),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_history(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    label: str | None = None,
    search: str | None = None,
    date_from: dt.datetime | None = None,
    date_to: dt.datetime | None = None,
) -> tuple[int, list[UrlCheck]]:
    """Return ``(total, rows)`` for a filtered, paginated history query."""
    conditions = []
    if label:
        conditions.append(UrlCheck.label == Label(label))
    if search:
        conditions.append(UrlCheck.url.ilike(f"%{search}%"))
    if date_from:
        conditions.append(UrlCheck.checked_at >= date_from)
    if date_to:
        conditions.append(UrlCheck.checked_at <= date_to)

    count_stmt = select(func.count()).select_from(UrlCheck)
    rows_stmt = select(UrlCheck).order_by(UrlCheck.checked_at.desc())
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
        rows_stmt = rows_stmt.where(cond)

    total = (await session.execute(count_stmt)).scalar_one()
    rows = (
        await session.execute(rows_stmt.limit(limit).offset(offset))
    ).scalars().all()
    return total, list(rows)


async def get_stats(session: AsyncSession) -> dict:
    """Aggregate dashboard statistics."""
    # --- label counts ---
    label_rows = (
        await session.execute(
            select(UrlCheck.label, func.count()).group_by(UrlCheck.label)
        )
    ).all()
    counts = {lbl.value: 0 for lbl in Label}
    for lbl, n in label_rows:
        counts[lbl.value] = n
    total = sum(counts.values())

    # --- top impersonated (flagged) domains ---
    flagged_rows = (
        await session.execute(
            select(UrlCheck.closest_domain, func.count())
            .where(UrlCheck.label.in_([Label.suspicious, Label.phishing]))
            .where(UrlCheck.closest_domain.is_not(None))
            .group_by(UrlCheck.closest_domain)
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()
    top_flagged = [
        {"domain": dom, "count": n} for dom, n in flagged_rows if dom
    ]

    # --- time series (aggregated in Python for DB portability) ---
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    recent = (
        await session.execute(
            select(UrlCheck.checked_at, UrlCheck.label)
            .where(UrlCheck.checked_at >= since)
        )
    ).all()

    per_day: dict[str, Counter] = defaultdict(Counter)
    by_hour: Counter = Counter()
    for checked_at, lbl in recent:
        day = checked_at.date().isoformat()
        per_day[day][lbl.value] += 1
        by_hour[checked_at.hour] += 1

    today = dt.datetime.now(dt.timezone.utc).date()
    checks_per_day = []
    for i in range(6, -1, -1):
        day = (today - dt.timedelta(days=i)).isoformat()
        bucket = per_day.get(day, Counter())
        checks_per_day.append({
            "date": day,
            "safe": bucket.get("safe", 0),
            "suspicious": bucket.get("suspicious", 0),
            "phishing": bucket.get("phishing", 0),
        })

    checks_by_hour = [
        {"hour": h, "count": by_hour.get(h, 0)} for h in range(24)
    ]

    flagged = counts["phishing"] + counts["suspicious"]
    return {
        "total_checks": total,
        "phishing_count": counts["phishing"],
        "suspicious_count": counts["suspicious"],
        "safe_count": counts["safe"],
        "phishing_rate": round(flagged / total, 4) if total else 0.0,
        "top_flagged_domains": top_flagged,
        "checks_per_day": checks_per_day,
        "checks_by_hour": checks_by_hour,
    }
