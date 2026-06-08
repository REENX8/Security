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
from datetime import datetime, timedelta, timezone
from functools import partial

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Feedback, UrlCheck

logger = logging.getLogger("phish-detector")

# Module-level lock so concurrent feedback submissions can't both pass the
# "retrain_in_progress is False" check and launch duplicate retrains.
_retrain_lock = asyncio.Lock()


async def _feedback_count(session: AsyncSession) -> int:
    return (
        await session.execute(select(func.count()).select_from(Feedback))
    ).scalar_one()


async def _feed_phishing_count_since(session: AsyncSession, since: datetime) -> int:
    """Count url_checks rows that came from a feed and were labeled phishing."""
    try:
        return (
            await session.execute(
                select(func.count())
                .select_from(UrlCheck)
                .where(UrlCheck.label == "phishing")
                .where(UrlCheck.checked_at >= since)
                .where(UrlCheck.features["feed_source"].as_string() != None)  # noqa: E711
            )
        ).scalar_one()
    except Exception:  # noqa: BLE001
        return 0


async def _run_retrain_bg(app_state) -> None:
    """Run the gated retrain off the event loop, then hot-swap on success.

    After promotion, immediately evaluates the Thai holdout and auto-rolls
    back if recall drops below settings.recall_rollback_threshold.
    """

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
            # Auto-rollback: evaluate Thai holdout recall before accepting.
            rolled_back = False
            try:
                recall = await asyncio.get_event_loop().run_in_executor(
                    None, _check_thai_recall_sync
                )
                threshold = getattr(settings, "recall_rollback_threshold", 0.82)
                if recall is not None and recall < threshold:
                    await asyncio.get_event_loop().run_in_executor(
                        None, _rollback_model_sync
                    )
                    rolled_back = True
                    logger.warning(
                        "AUTO-ROLLBACK: post-promote recall=%.3f < threshold=%.2f, "
                        "restored previous model",
                        recall, threshold,
                    )
                    try:
                        from app.metrics import MODEL_ROLLBACK
                        MODEL_ROLLBACK.inc()
                    except Exception:  # noqa: BLE001
                        pass
            except Exception as exc:  # noqa: BLE001
                logger.warning("recall check after promotion failed (%s) -- keeping promoted model", exc)

            if not rolled_back:
                try:
                    app_state.scorer = load_scorer()
                    logger.info("scorer hot-reloaded after auto-retrain")
                except Exception as exc:  # noqa: BLE001
                    logger.error("scorer reload failed (%s) -- keeping previous model", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("auto-retrain failed: %s", exc)
    finally:
        app_state.retrain_in_progress = False


def _check_thai_recall_sync() -> float | None:
    """Synchronously evaluate Thai holdout recall on the newly promoted model."""
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    try:
        from ml_pipeline.config import THAI_HOLDOUT_CSV
        from ml_pipeline.evaluate import evaluate_thai_holdout
        from ml_pipeline.train import load_model_and_scaler
        if not __import__("os").path.exists(THAI_HOLDOUT_CSV):
            return None
        model, scaler = load_model_and_scaler()
        metrics = evaluate_thai_holdout(model, scaler)
        return metrics.get("recall_phishing_threshold")
    except Exception:  # noqa: BLE001
        return None


def _rollback_model_sync() -> None:
    """Restore the previous model from models/previous/."""
    import shutil
    from pathlib import Path

    from ml_pipeline.config import MODELS_DIR
    prev = Path(MODELS_DIR) / "previous"
    if not prev.exists():
        return
    for fname in ("ensemble.pkl", "scaler.pkl", "features.json"):
        src = prev / fname
        dst = Path(MODELS_DIR) / fname
        if src.exists():
            shutil.copy2(src, dst)


async def _update_fn_fp_gauges(session: AsyncSession) -> None:
    """Compute 7-day false-negative and false-positive rates from feedback."""
    try:
        from app.metrics import FALSE_NEGATIVE_RATE, FALSE_POSITIVE_RATE
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        rows = (
            await session.execute(
                select(Feedback).where(Feedback.created_at >= cutoff)
            )
        ).scalars().all()
        if not rows:
            return
        fn = sum(
            1 for r in rows
            if r.verdict_given == "safe" and r.correct_verdict == "phishing"
        )
        fp = sum(
            1 for r in rows
            if r.verdict_given == "phishing" and r.correct_verdict == "safe"
        )
        n = len(rows)
        FALSE_NEGATIVE_RATE.set(round(fn / n, 4))
        FALSE_POSITIVE_RATE.set(round(fp / n, 4))
        logger.info(
            "fn_rate=%.3f fp_rate=%.3f (n=%d trailing-7d feedback rows)",
            fn / n, fp / n, n,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("FN/FP gauge update failed: %s", exc)


async def check_feed_accumulation(app_state, session: AsyncSession) -> bool:
    """Trigger a retrain when enough new feed phishing URLs have accumulated.

    Separate from the feedback-volume trigger: counts url_checks rows from
    feeds since the last retrain and fires when >= settings.feed_retrain_threshold.
    """
    if not settings.feedback_retrain_enabled:
        return False

    async with _retrain_lock:
        if getattr(app_state, "retrain_in_progress", False):
            return False

        threshold = getattr(settings, "feed_retrain_threshold", 50)
        last_retrain = getattr(app_state, "last_retrain_at", None)
        since = last_retrain if last_retrain else (
            datetime.now(timezone.utc) - timedelta(days=30)
        )
        count = await _feed_phishing_count_since(session, since)
        if count < threshold:
            return False

        app_state.retrain_in_progress = True
        app_state.last_retrain_at = datetime.now(timezone.utc)

    logger.info(
        "[retrain] feed accumulation trigger: %d new feed URLs since last retrain "
        "(threshold %d)",
        count, threshold,
    )
    asyncio.create_task(_run_retrain_bg(app_state))
    return True


async def maybe_trigger_retrain(app_state, session: AsyncSession) -> bool:
    """Trigger a retrain if enough new feedback has accumulated.

    Returns True when a retrain was actually started. Safe to call on every
    feedback submission: it no-ops when disabled, below threshold, or already
    running.
    """
    if not settings.feedback_retrain_enabled:
        return False

    # Atomic check-then-set: acquire lock so two concurrent requests can't
    # both pass the `retrain_in_progress is False` check.
    async with _retrain_lock:
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
    await _update_fn_fp_gauges(session)
    asyncio.create_task(_run_retrain_bg(app_state))
    return True
