"""SSRF guard for outbound URL fetches.

Two modules fetch attacker-controlled URLs from inside the network:
``unshorten.py`` (follows short-link redirects) and ``content_check.py``
(downloads page HTML for gray-zone URLs). Both must refuse to connect to
private / loopback / link-local / reserved addresses, otherwise a crafted
URL (or a redirect chain ending at one) could probe internal services —
the classic Server-Side Request Forgery (SSRF) hole.

The check resolves the hostname and inspects EVERY resolved address, so a
public DNS name that points at ``127.0.0.1`` / ``169.254.169.254`` (cloud
metadata) is caught too, not just literal-IP URLs.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def _addr_is_blocked(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True  # not parseable -> treat as unsafe
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local      # 169.254.0.0/16 incl. cloud metadata
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified     # 0.0.0.0 / ::
    )


def host_is_safe(host: str) -> bool:
    """True only if ``host`` resolves exclusively to public IP addresses.

    Performs a blocking DNS lookup, so callers on the event loop should wrap
    this in a threadpool (see :func:`url_is_safe_async`).
    """
    if not host:
        return False
    host = host.strip().lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return False

    # Literal IP (v4/v6, optionally bracketed) — check directly, no DNS.
    literal = host.strip("[]")
    try:
        ipaddress.ip_address(literal)
        return not _addr_is_blocked(literal)
    except ValueError:
        pass

    # Hostname — resolve and reject if ANY address is non-public.
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False  # cannot resolve -> do not connect
    if not infos:
        return False
    return all(not _addr_is_blocked(info[4][0]) for info in infos)


def url_is_safe(url: str) -> bool:
    """True if the URL is http(s) and its host resolves to public IPs only."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    return host_is_safe(parsed.hostname or "")


async def url_is_safe_async(url: str) -> bool:
    """Async wrapper that runs the blocking DNS resolution off the event loop."""
    from starlette.concurrency import run_in_threadpool

    return await run_in_threadpool(url_is_safe, url)
