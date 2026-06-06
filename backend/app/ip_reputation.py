"""Serve-time IP / ASN reputation (B8, Stage 2).

When ``IP_REPUTATION_ENABLED`` is set, the check pipeline resolves the URL's host
to a public IP (SSRF-safe, via :mod:`app.net_guard`), looks up the ASN through
the configured pluggable provider, and reads the accumulated bad-verdict share of
that IP / ASN from the reputation store. Those shares are fed to the model as the
``ip_reputation_score`` / ``asn_reputation_score`` features (schema v1.6) — so a
hosting range with a bad track record raises a brand-new URL even on first
sighting. The store itself is fed best-effort from the verdict stream
(:mod:`app.ip_reputation_store`).

Fail-open throughout: any resolution / DB error yields "unknown" (-1) reputation
so a verdict is never blocked.
"""

from __future__ import annotations

import logging
import socket
from urllib.parse import urlparse

from starlette.concurrency import run_in_threadpool

from app.net_guard import _addr_is_blocked, host_is_safe

logger = logging.getLogger("phish-detector")

# Don't report a reputation until we've seen enough verdicts on a range — a
# single bad sighting is not yet reputation (below this it stays "unknown").
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


def _bad_share(row) -> float:
    """Accumulated bad-verdict share of a reputation row, or -1.0 if unknown.

    This is the value fed to the model as the ``*_reputation_score`` feature
    (B8 Stage 2); -1.0 mirrors the training/imputed "unknown" convention and is
    used until a range has at least ``_MIN_OBSERVATIONS`` verdicts.
    """
    total = (row.total_count or 0) if row is not None else 0
    if row is None or total < _MIN_OBSERVATIONS:
        return -1.0
    bad = ((row.phishing_count or 0) + 0.5 * (row.suspicious_count or 0)) / total
    return round(max(0.0, min(1.0, bad)), 4)


async def reputation_feature_scores(rep: dict | None, *, session=None) -> dict:
    """Return ``{ip_reputation_score, asn_reputation_score}`` for the model.

    Values are accumulated bad-verdict shares in [0, 1], or -1.0 ("unknown").
    Fail-open: any error yields both unknown so scoring is never blocked. Opens
    a short-lived session when none is supplied (safe under batch concurrency).
    """
    unknown = {"ip_reputation_score": -1.0, "asn_reputation_score": -1.0}
    if not rep or not rep.get("ip"):
        return unknown
    try:
        if session is not None:
            return await _compute_scores(session, rep)
        from app.database import SessionLocal

        async with SessionLocal() as own:
            return await _compute_scores(own, rep)
    except Exception as exc:  # noqa: BLE001 - never block a verdict
        logger.debug("ip reputation feature lookup skipped: %s", exc)
        return unknown


async def _compute_scores(session, rep: dict) -> dict:
    from sqlalchemy import select

    from app.models import AsnReputation, IpReputation

    ip_row = (
        await session.execute(
            select(IpReputation).where(IpReputation.ip == rep["ip"])
        )
    ).scalar_one_or_none()
    asn_score = -1.0
    if rep.get("asn") is not None:
        asn_row = (
            await session.execute(
                select(AsnReputation).where(AsnReputation.asn == rep["asn"])
            )
        ).scalar_one_or_none()
        asn_score = _bad_share(asn_row)
    return {
        "ip_reputation_score": _bad_share(ip_row),
        "asn_reputation_score": asn_score,
    }
