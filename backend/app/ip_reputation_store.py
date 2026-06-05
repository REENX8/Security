"""IP / ASN reputation store — fed from the verdict stream (B8).

Mirrors :func:`app.campaigns.record_campaign`: a cheap select-or-insert upsert
that bumps verdict counters per IP and per ASN. Called best-effort from the
check pipeline's observability path, so a failure here never blocks a verdict.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AsnReputation, IpReputation


def _aware(value: dt.datetime) -> dt.datetime:
    """Normalise a possibly-naive (SQLite) timestamp to aware UTC."""
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _bump_counts(row, *, label: str, score: float, now: dt.datetime) -> None:
    row.total_count += 1
    if label == "phishing":
        row.phishing_count += 1
    elif label == "suspicious":
        row.suspicious_count += 1
    row.last_score = float(score)
    if row.last_seen is None or _aware(row.last_seen) < now:
        row.last_seen = now
    if row.first_seen is None or _aware(row.first_seen) > now:
        row.first_seen = now


async def record_ip_verdict(
    session: AsyncSession,
    *,
    ip: str,
    asn: int | None,
    as_name: str = "",
    label: str,
    score: float,
    seen_at: dt.datetime | None = None,
) -> None:
    """Upsert IP (and ASN, when known) reputation counters for one verdict.

    Best-effort: the caller wraps this in try/except so a DB hiccup never stops
    a verdict from reaching the user.
    """
    if not ip:
        return
    now = seen_at or dt.datetime.now(dt.timezone.utc)

    ip_row = (
        await session.execute(select(IpReputation).where(IpReputation.ip == ip))
    ).scalar_one_or_none()
    if ip_row is None:
        ip_row = IpReputation(
            ip=ip, asn=asn, phishing_count=0, suspicious_count=0,
            total_count=0, first_seen=now, last_seen=now,
        )
        session.add(ip_row)
    elif asn is not None:
        ip_row.asn = asn
    _bump_counts(ip_row, label=label, score=score, now=now)

    if asn is not None:
        asn_row = (
            await session.execute(
                select(AsnReputation).where(AsnReputation.asn == asn)
            )
        ).scalar_one_or_none()
        if asn_row is None:
            asn_row = AsnReputation(
                asn=asn, as_name=as_name, phishing_count=0, suspicious_count=0,
                total_count=0, first_seen=now, last_seen=now,
            )
            session.add(asn_row)
        elif as_name and not asn_row.as_name:
            asn_row.as_name = as_name
        _bump_counts(asn_row, label=label, score=score, now=now)

    await session.commit()
