"""Forward confirmed phishing to a government connector (B3).

Collects recent phishing verdicts from the database and hands them to the
configured GovernmentConnector (``GOV_CONNECTOR``; "email" sends a CSV digest).
Schedule it (cron / Render cron job), e.g. daily:

  python -m scripts.gov_forward --since-days 1
  python -m scripts.gov_forward --since-days 1 --dry-run   # preview, no send
  GOV_CONNECTOR=email python -m scripts.gov_forward

Deduplicates by URL within the window. Forward-only — it does not pull blocklists
(email is a push channel).
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys
from pathlib import Path

# Make the backend package importable when run as a script.
BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def _collect(since_days: int, limit: int):
    from app.database import SessionLocal
    from app.integrations.government import GovReport
    from app.models import Label, UrlCheck
    from sqlalchemy import select

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=since_days)
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(UrlCheck)
                .where(UrlCheck.label == Label.phishing)
                .where(UrlCheck.checked_at >= cutoff)
                .order_by(UrlCheck.checked_at.desc())
            )
        ).scalars().all()

    seen: set[str] = set()
    reports: list[GovReport] = []
    for r in rows:
        if r.url in seen:
            continue
        seen.add(r.url)
        reports.append(
            GovReport(
                url=r.url,
                score=float(r.score),
                closest_domain=r.closest_domain,
                reason=r.reason or "",
            )
        )
        if len(reports) >= limit:
            break
    return reports


async def _run(since_days: int, limit: int, dry_run: bool) -> int:
    from app.config import settings
    from app.integrations.government import get_connector, reports_to_csv

    try:
        reports = await _collect(since_days, limit)
    except Exception as exc:  # noqa: BLE001 - DB unreachable / not migrated
        print(f"[gov] could not read the database: {exc}")
        return 1
    if not reports:
        print(f"[gov] no phishing in the last {since_days}d — nothing to forward")
        return 0

    if dry_run:
        print(f"[gov] dry-run: {len(reports)} report(s) via '{settings.gov_connector}':")
        print(reports_to_csv(reports))
        return 0

    connector = get_connector(settings.gov_connector, settings)
    ok = connector.forward_reports(reports)
    print(f"[gov] forwarded {len(reports)} report(s) via '{connector.name}': ok={ok}")
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Forward confirmed phishing to authorities")
    parser.add_argument("--since-days", type=int, default=1)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(_run(args.since_days, args.limit, args.dry_run)))


if __name__ == "__main__":
    main()
