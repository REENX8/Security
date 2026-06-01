"""Auto feedback -> retrain trigger (C9).

The time-based background loop (main.lifespan) retrains every N hours. This adds
a *volume*-based trigger: once enough NEW confirmed feedback rows have piled up
since the last retrain, kick one off immediately (debounced, gate-enforced, in a
background task) instead of waiting for the timer.

State lives on ``app.state``:
  * ``retrain_in_progress``     — bool lock so only one retrain runs at a time.
  * ``retrain_baseline_count``  — feedback-row count at the last trigger; the
    delta against the live count is what must cross the threshold.
"""

from __future__ import annotations

import asyncio
import logging
from functools import partial

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Feedback

logger = logging.getLogger("phish-detector")


async def _feedback_count(session: AsyncSession) -> int:
    return (
        await session.execute(select(func.count()).select_from(Feedback))
    ).scalar_one()


async def _run_retrain_bg(app_state) -> None:
    """Run the gated retrain off the event loop, then hot-swap on success."""
    from app.ml.loader import load_scorer
    from ml_pipeline.feedback_retrain import run as run_retrain

    try:
        ok = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                run_retrain,
                min_rows=settings.feedback_accumulation_threshold,
                enforce_gate=settings.feedback_promote_requires_gate,
            ),
        )
        if ok:
            try:
                app_state.scorer = load_scorer()
                logger.info("scorer hot-reloaded after auto-retrain")
            except Exception as exc:  # noqa: BLE001 - keep the old model
                logger.error("scorer reload failed (%s) -- keeping previous model", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("auto-retrain failed: %s", exc)
    finally:
        app_state.retrain_in_progress = False


async def maybe_trigger_retrain(app_state, session: AsyncSession) -> bool:
    """Trigger a retrain if enough new feedback has accumulated.

    Returns True when a retrain was actually started. Safe to call on every
    feedback submission: it no-ops when disabled, below threshold, or already
    running.
    """
    if not settings.feedback_retrain_enabled:
        return False
    if getattr(app_state, "retrain_in_progress", False):
        return False

    total = await _feedback_count(session)
    baseline = getattr(app_state, "retrain_baseline_count", 0)
    if total - baseline < settings.feedback_accumulation_threshold:
        return False

    app_state.retrain_in_progress = True
    app_state.retrain_baseline_count = total
    logger.info(
        "auto-retrain triggered: %d feedback rows (+%d since last, threshold %d)",
        total, total - baseline, settings.feedback_accumulation_threshold,
    )
    asyncio.create_task(_run_retrain_bg(app_state))
    return True
