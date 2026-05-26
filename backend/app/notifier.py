"""Webhook notifier for the brand watchlist.

When a phishing verdict is returned for a URL whose ``closest_domain``
maps to a brand on the watchlist, we POST a compact JSON payload to the
operator's configured webhook. Delivery is best-effort with one retry --
this is observability, not a hard guarantee. Every attempt is logged to
``webhook_delivery`` so operators can see what fired.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import urllib.error
import urllib.request

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BrandWatch, WebhookDelivery

logger = logging.getLogger("phish-detector.notifier")

DELIVERY_TIMEOUT_S = 5.0
USER_AGENT = "thai-phish-detector-watchlist/1.0"


def _brand_of(closest_domain: str | None) -> str | None:
    """First label of the closest_domain -- this is the watchlist key."""
    if not closest_domain:
        return None
    return closest_domain.split(".", 1)[0].lower()


def _post_sync(url: str, payload: dict) -> tuple[int | None, str | None]:
    """Synchronous POST suitable for ``run_in_threadpool``.

    Uses the stdlib so we don't pull in extra deps; the volume is tiny.
    Returns ``(status_code | None, error | None)``.
    """
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=DELIVERY_TIMEOUT_S) as resp:
            return resp.status, None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.reason
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)[:480]


async def maybe_alert(
    session: AsyncSession,
    *,
    url: str,
    label: str,
    score: float,
    closest_domain: str | None,
    reason: str,
) -> list[WebhookDelivery]:
    """Fire watchlist webhooks for ``url`` if the verdict is phishing.

    Returns the list of delivery rows that were attempted (possibly empty).
    Errors are swallowed -- scoring must not fail because a webhook is
    unreachable.
    """
    if label != "phishing":
        return []
    brand = _brand_of(closest_domain)
    if not brand:
        return []

    watch = (
        await session.execute(
            select(BrandWatch)
            .where(BrandWatch.brand == brand)
            .where(BrandWatch.enabled.is_(True))
        )
    ).scalar_one_or_none()
    if watch is None:
        return []

    watch.hit_count += 1
    watch.last_hit_at = dt.datetime.now(dt.timezone.utc)
    await session.commit()

    if not watch.webhook_url:
        return []  # watched without a webhook = "track only"

    payload = {
        "schema": "phish.alert.v1",
        "brand": brand,
        "url": url,
        "label": label,
        "score": round(float(score), 4),
        "closest_domain": closest_domain,
        "reason": reason,
        "fired_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    # The HTTP POST is synchronous (stdlib); run it off the event loop.
    status, err = await asyncio.get_event_loop().run_in_executor(
        None, _post_sync, watch.webhook_url, payload
    )
    if err and (status is None):
        # One retry on transport failure -- network blip, dns hiccup.
        await asyncio.sleep(0.5)
        status, err = await asyncio.get_event_loop().run_in_executor(
            None, _post_sync, watch.webhook_url, payload
        )

    delivery = WebhookDelivery(
        brand=brand,
        url_checked=url[:2048],
        webhook_url=watch.webhook_url[:512],
        status_code=status,
        error=(err or None),
        attempts=2 if err else 1,
    )
    session.add(delivery)
    await session.commit()
    await session.refresh(delivery)
    logger.info(
        "watchlist webhook fired: brand=%s status=%s err=%s",
        brand, status, err,
    )
    return [delivery]
