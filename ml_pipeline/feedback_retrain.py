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
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_CSV = ROOT / "data" / "feedback_labels.csv"
MIN_ROWS_FOR_RETRAIN = 5

# Train into a staging directory, evaluate it there against the gate, and
# only promote (atomic copy) into the live models/ dir if the gate passes.
# The previous live model is backed up so a bad promote can be rolled back.
LIVE_MODELS_DIR = ROOT / "models"
STAGING_MODELS_DIR = ROOT / "models" / "staging"
STAGING_REPORTS_DIR = ROOT / "reports" / "staging"
BACKUP_MODELS_DIR = ROOT / "models" / "previous"
_PROMOTE_FILES = ("ensemble.pkl", "scaler.pkl", "features.json", "whitelist.json")

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


def _run_step(module_args: tuple[str, ...], env: dict) -> bool:
    """Run ``python -m <module_args>`` and log stderr on failure."""
    result = subprocess.run(
        [sys.executable, "-m", *module_args],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        logger.error("step '%s' failed:\n%s", module_args[0], result.stderr[-2000:])
        return False
    return True


def _promote() -> bool:
    """Atomically copy staged artifacts into the live models dir.

    Backs up the current live artifacts to ``models/previous`` first so a
    regression can be rolled back by hand. Returns False (and leaves the live
    model untouched) if any staged artifact is missing.
    """
    for name in _PROMOTE_FILES:
        if not (STAGING_MODELS_DIR / name).exists():
            logger.error("promote aborted: missing staged artifact %s", name)
            return False

    BACKUP_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name in _PROMOTE_FILES:
        live = LIVE_MODELS_DIR / name
        staged = STAGING_MODELS_DIR / name
        if live.exists():
            shutil.copy2(live, BACKUP_MODELS_DIR / name)
        # Stage into a temp file on the live filesystem then os.replace, so a
        # concurrent reader never sees a half-written artifact.
        tmp = LIVE_MODELS_DIR / f".{name}.promoting"
        shutil.copy2(staged, tmp)
        os.replace(tmp, live)
    logger.info(
        "promoted staged model -> %s (previous backed up in %s)",
        LIVE_MODELS_DIR, BACKUP_MODELS_DIR,
    )
    return True


def _retrain(enforce_gate: bool = True) -> bool:
    """Train into staging, gate it, and promote on success.

    A failure at any step (training error OR the eval gate rejecting the new
    model) leaves the live model untouched -- this IS the rollback.
    """
    STAGING_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "PHISH_MODELS_DIR": str(STAGING_MODELS_DIR),
        "PHISH_REPORTS_DIR": str(STAGING_REPORTS_DIR),
    }

    eval_args = ("ml_pipeline.evaluate",)
    if enforce_gate:
        eval_args = ("ml_pipeline.evaluate", "--enforce-threshold")
    steps = (
        ("ml_pipeline.build_whitelist",),
        ("ml_pipeline.collect_dataset", "--no-feeds"),
        ("ml_pipeline.train",),
        eval_args,
    )
    for module_args in steps:
        if not _run_step(module_args, env):
            logger.error(
                "retrain aborted at '%s' -- live model left unchanged",
                module_args[0],
            )
            return False

    logger.info("staged model passed the gate -- promoting")
    return _promote()


def run(
    since_days: int = 14,
    dry_run: bool = False,
    min_rows: int = MIN_ROWS_FOR_RETRAIN,
    enforce_gate: bool = True,
) -> bool:
    rows = asyncio.run(_export(since_days))
    if not rows:
        logger.info("no feedback rows found — nothing to do")
        return True

    _write_csv(rows)

    if len(rows) < min_rows:
        logger.info(
            "only %d rows (minimum %d) — skipping retrain", len(rows), min_rows
        )
        return True

    if dry_run:
        logger.info("--dry-run: skipping retrain")
        return True

    return _retrain(enforce_gate=enforce_gate)


def main() -> None:
    parser = argparse.ArgumentParser(description="Feedback-driven model retrain")
    parser.add_argument("--since-days", type=int, default=14)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--min-rows", type=int, default=MIN_ROWS_FOR_RETRAIN,
        help="minimum accumulated feedback rows before a retrain is attempted",
    )
    parser.add_argument(
        "--no-gate", action="store_true",
        help="promote without enforcing the Thai-recall eval gate (NOT advised)",
    )
    args = parser.parse_args()
    ok = run(
        since_days=args.since_days,
        dry_run=args.dry_run,
        min_rows=args.min_rows,
        enforce_gate=not args.no_gate,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
