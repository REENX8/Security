"""Serve-time IP / ASN reputation adjustment (B8, Stage 1).

Mirrors :mod:`app.content_check`: a bounded, fail-open score adjustment applied
on the check hot path only when ``IP_REPUTATION_ENABLED`` is set. It resolves
the URL's host to a public IP (SSRF-safe, via :mod:`app.net_guard`), looks up
the ASN through the configured pluggable provider, and reads the accumulated
verdict history from the reputation store. A range with a bad track record nudges
the score up; a well-observed clean range nudges it slightly down.

No model/schema change: this is a runtime layer on top of the existing model
(Stage 1). Promoting reputation to an ML feature is a deferred Stage 2 that would
require a schema bump + retrain behind the Thai-recall gate.
"""

from __future__ import annotations

import logging
import socket
from urllib.parse import urlparse

from starlette.concurrency import run_in_threadpool

from app.net_guard import _addr_is_blocked, host_is_safe

logger = logging.getLogger("phish-detector")

# Reputation bump bounds. Bad ranges add up to +0.30; a clean, well-observed
# range subtracts at most 0.10. Identical envelope philosophy to content_check.
_MIN_BUMP = -0.10
_MAX_BUMP = 0.30
# Don't act on a range until we've seen enough verdicts on it — a single bad
# sighting is not yet reputation.
_MIN_OBSERVATIONS = 5


def _resolve_public_ip(host: str) -> str | None:
    """Return the first public IP a host resolves to, or None.

    SSRF-safe: returns None if the host resolves to ANY private/loopback/
    link-local/reserved address (reuses net_guard's host_is_safe gate), so we
    never key reputation on internal infrastructure.
    """
    if not host or not host_is_safe(host):
        return None
    literal = host.strip("[]")
    try:
        socket.inet_aton(literal)  # already a v4 literal
        return literal
    except OSError:
        pass
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return None
    for info in infos:
        ip = str(info[4][0])
        if not _addr_is_blocked(ip):
            return ip
    return None


def resolve_ip_asn(url: str, asn_provider, timeout: float = 2.0) -> dict | None:
    """Resolve a URL's host to ``{ip, asn, as_name}`` (blocking; run in a pool).

    Returns None when the host cannot be safely resolved. ``asn``/``as_name``
    are None/"" when the provider cannot resolve the ASN (e.g. NullAsnProvider).
    """
    host = (urlparse(url).hostname or "").lower()
    ip = _resolve_public_ip(host)
    if not ip:
        return None
    asn: int | None = None
    as_name = ""
    try:
        info = asn_provider.lookup(ip) if asn_provider else None
        if info is not None:
            asn = info.asn
            as_name = info.as_name
    except Exception as exc:  # noqa: BLE001 - provider must never break a verdict
        logger.debug("asn lookup failed for %s: %s", ip, exc)
    return {"ip": ip, "asn": asn, "as_name": as_name}


async def resolve_ip_asn_async(url: str, asn_provider, timeout: float = 2.0) -> dict | None:
    return await run_in_threadpool(resolve_ip_asn, url, asn_provider, timeout)


def _rep_bump(row) -> float:
    """Map one reputation row to a bounded score bump.

    ``bad`` in [0, 1] is the share of (weighted) bad verdicts on the range;
    it linearly maps bad=0 -> _MIN_BUMP (clean range, small discount) and
    bad=1 -> _MAX_BUMP (consistently malicious range).
    """
    total = row.total_count or 0 if row is not None else 0
    if row is None or total < _MIN_OBSERVATIONS:
        return 0.0
    phishing = row.phishing_count or 0
    suspicious = row.suspicious_count or 0
    bad = (phishing + 0.5 * suspicious) / total
    bad = max(0.0, min(1.0, bad))
    return round(_MIN_BUMP + (_MAX_BUMP - _MIN_BUMP) * bad, 4)


async def reputation_adjustment(rep: dict | None, *, session=None) -> float:
    """Return a bounded score adjustment from stored IP/ASN reputation.

    Reads the strongest available signal (largest-magnitude bump of the IP and
    ASN rows). Fail-open: any error returns 0.0. When ``session`` is None a
    short-lived session is opened (so batch concurrency is safe — each call gets
    its own session, never sharing the request session across gather tasks).
    """
    if not rep or not rep.get("ip"):
        return 0.0
    try:
        if session is not None:
            return await _compute(session, rep)
        from app.database import SessionLocal

        async with SessionLocal() as own:
            return await _compute(own, rep)
    except Exception as exc:  # noqa: BLE001 - never block a verdict
        logger.debug("ip reputation adjustment skipped: %s", exc)
        return 0.0


async def _compute(session, rep: dict) -> float:
    from sqlalchemy import select

    from app.models import AsnReputation, IpReputation

    ip_row = (
        await session.execute(
            select(IpReputation).where(IpReputation.ip == rep["ip"])
        )
    ).scalar_one_or_none()
    bumps = [_rep_bump(ip_row)]
    if rep.get("asn") is not None:
        asn_row = (
            await session.execute(
                select(AsnReputation).where(AsnReputation.asn == rep["asn"])
            )
        ).scalar_one_or_none()
        bumps.append(_rep_bump(asn_row))

    nonzero = [b for b in bumps if b != 0.0]
    if not nonzero:
        return 0.0
    # Strongest signal wins; clamp to the envelope as a belt-and-braces guard.
    bump = max(nonzero, key=abs)
    return max(_MIN_BUMP, min(_MAX_BUMP, bump))
