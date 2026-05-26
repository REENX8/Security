"""Phishing campaign clustering.

A phishing campaign is a batch of URLs that share a kit, infrastructure or
template. We don't have the page content -- only URLs -- so we build a
shape fingerprint from the parts of the URL the attacker is least likely
to randomise: the impersonated brand and the URL path skeleton.

The clustering is intentionally cheap: one fingerprint = one cluster, no
distance threshold, no k-means. It runs once per check inside a request
worker, and the dashboard query reads pre-aggregated rows. This trades a
tiny bit of recall (two kits with the same skeleton get merged) for
predictability and zero cost at scale.
"""

from __future__ import annotations

import datetime as dt
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign

# The path shape is the path stripped of segment-specific content: lower-
# cased, all digit runs collapsed to ``#``, all >=8-char hex runs collapsed
# to ``$hex``, leading/trailing slash trimmed.
_DIGITS = re.compile(r"\d+")
_HEX_RUN = re.compile(r"\b[0-9a-f]{8,}\b", re.IGNORECASE)


def _path_shape(url: str) -> str:
    """Return a normalised path skeleton or '' when no path is present."""
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return ""
    path = (parsed.path or "").strip("/").lower()
    if not path:
        return ""
    path = _HEX_RUN.sub("$hex", path)
    path = _DIGITS.sub("#", path)
    return path[:120]


def _tld_signature(url: str) -> str:
    """Coarse signature of the host's last label."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001
        return ""
    return host.rsplit(".", 1)[-1] if "." in host else ""


def build_fingerprint(url: str, closest_domain: str | None) -> str:
    """Deterministic clustering key.

    ``<brand>|<tld>|<path-shape>`` is short and grep-friendly. Two URLs
    targeting the same brand on the same TLD with the same path skeleton
    are considered the same campaign.
    """
    brand = (closest_domain or "").lower()
    tld = _tld_signature(url)
    shape = _path_shape(url)
    return f"{brand}|{tld}|{shape}"[:240]


async def record_campaign(
    session: AsyncSession,
    *,
    url: str,
    closest_domain: str | None,
) -> Campaign | None:
    """Upsert a campaign row for ``url`` and bump its counters.

    Returns the campaign row (None if URL is too generic to fingerprint).
    """
    fingerprint = build_fingerprint(url, closest_domain)
    if not fingerprint or fingerprint.count("|") < 2 or fingerprint.endswith("||"):
        return None

    existing = (
        await session.execute(
            select(Campaign).where(Campaign.fingerprint == fingerprint)
        )
    ).scalar_one_or_none()

    now = dt.datetime.now(dt.timezone.utc)
    if existing:
        existing.url_count += 1
        existing.last_seen = now
        await session.commit()
        await session.refresh(existing)
        return existing

    row = Campaign(
        fingerprint=fingerprint,
        closest_domain=closest_domain,
        tld_signature=_tld_signature(url),
        path_shape=_path_shape(url),
        url_count=1,
        first_seen=now,
        last_seen=now,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
