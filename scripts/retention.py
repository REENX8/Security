"""CLI for the data-retention purge (A8).

  python -m scripts.retention                 # uses RETENTION_DAYS from settings
  python -m scripts.retention --days 90        # override window
  python -m scripts.retention --days 90 --dry-run

Schedule it (Render cron job / system cron) to keep the database bounded.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Make the backend package importable when run as a script.
BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def _run(days: int, dry_run: bool) -> int:
    import datetime as dt

    from app.database import SessionLocal
    from app.models import FeedIngestionRecord, UrlCheck, WebhookDelivery
    from app.retention import purge_old_rows
    from sqlalchemy import func, select

    if dry_run:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        async with SessionLocal() as session:
            counts = {}
            for model, col in (
                (UrlCheck, UrlCheck.checked_at),
                (WebhookDelivery, WebhookDelivery.created_at),
                (FeedIngestionRecord, FeedIngestionRecord.ingested_at),
            ):
                counts[model.__tablename__] = (
                    await session.execute(
                        select(func.count()).select_from(model).where(col < cutoff)
                    )
                ).scalar_one()
        print(f"[retention] dry-run: would delete (>{days}d): {counts}")
        return 0

    async with SessionLocal() as session:
        deleted = await purge_old_rows(session, days)
    print(f"[retention] deleted (>{days}d): {deleted}")
    return 0


def main() -> None:
    from app.config import settings

    parser = argparse.ArgumentParser(description="Prune old observability rows")
    parser.add_argument(
        "--days", type=int, default=settings.retention_days,
        help="retention window in days (default: RETENTION_DAYS setting)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.days <= 0:
        print("[retention] retention disabled (days<=0); nothing to do")
        sys.exit(0)
    sys.exit(asyncio.run(_run(args.days, args.dry_run)))


if __name__ == "__main__":
    main()
