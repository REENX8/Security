"""Export confirmed feedback from the database and trigger a model retrain.

Usage:
  python -m ml_pipeline.feedback_retrain            # export + retrain
  python -m ml_pipeline.feedback_retrain --dry-run  # export only, no retrain
  python -m ml_pipeline.feedback_retrain --since-days 7

This module is also callable from the backend background task when
FEEDBACK_RETRAIN_ENABLED=true (runs every FEEDBACK_RETRAIN_INTERVAL_HOURS).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_CSV = ROOT / "data" / "feedback_labels.csv"
MIN_ROWS_FOR_RETRAIN = 5

logger = logging.getLogger("phish-feedback-retrain")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def _export(since_days: int) -> list[dict]:
    """Pull confirmed feedback rows from the DB; returns [] if DB unavailable."""
    try:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

        from app.config import settings
        from app.models import Feedback
    except ImportError as exc:
        logger.warning("app imports unavailable: %s", exc)
        return []

    since = datetime.now(timezone.utc) - timedelta(days=since_days)
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Feedback).where(Feedback.created_at >= since)
            )
            rows = result.scalars().all()
        return [
            {
                "url": r.url,
                "label": "1" if r.correct_verdict == "phishing" else "0",
                "source": "feedback",
            }
            for r in rows
        ]
    except Exception as exc:
        logger.warning("DB export failed: %s", exc)
        return []


def _write_csv(rows: list[dict]) -> None:
    FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["url", "label", "source"])
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %d rows to %s", len(rows), FEEDBACK_CSV)


def _retrain() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "ml_pipeline.train"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("retrain failed:\n%s", result.stderr[-2000:])
        return False
    logger.info("retrain completed successfully")
    return True


def run(since_days: int = 14, dry_run: bool = False) -> bool:
    rows = asyncio.run(_export(since_days))
    if not rows:
        logger.info("no feedback rows found — nothing to do")
        return True

    _write_csv(rows)

    if len(rows) < MIN_ROWS_FOR_RETRAIN:
        logger.info(
            "only %d rows (minimum %d) — skipping retrain", len(rows), MIN_ROWS_FOR_RETRAIN
        )
        return True

    if dry_run:
        logger.info("--dry-run: skipping retrain")
        return True

    return _retrain()


def main() -> None:
    parser = argparse.ArgumentParser(description="Feedback-driven model retrain")
    parser.add_argument("--since-days", type=int, default=14)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(0 if run(since_days=args.since_days, dry_run=args.dry_run) else 1)


if __name__ == "__main__":
    main()
