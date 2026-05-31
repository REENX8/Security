"""Async URL unshortener — follows redirects for known short-link services.

Redirects are followed MANUALLY (not by httpx's ``follow_redirects``) so the
SSRF guard runs on every hop: a short link that redirects to an internal
address (``http://169.254.169.254/...``) is refused and the original URL is
returned unchanged.
"""
from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

import httpx

from app.net_guard import url_is_safe_async

logger = logging.getLogger("phish-detector")

_SHORTENER_HOSTS: frozenset[str] = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "ow.ly", "tiny.cc",
    "is.gd", "buff.ly", "short.link", "rb.gy", "lnkd.in", "shorturl.at",
    "goo.gl", "t.me", "fb.me", "adf.ly", "v.gd", "trib.al",
    "s.id", "lin.ee",
})

# Safety ceiling on the redirect chain we will follow.
_MAX_HOPS = 5


def _is_shortener(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host in _SHORTENER_HOSTS


async def unshorten_url(url: str, timeout: float = 5.0) -> str:
    """Return the final URL after following redirects, or the original URL on error.

    Each hop is vetted by the SSRF guard; if a redirect points at a private /
    loopback / link-local address we stop and return the original URL.
    """
    if not _is_shortener(url):
        return url
    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhishBot/1.0)"},
        ) as client:
            current = url
            for _ in range(_MAX_HOPS):
                resp = await client.head(current)
                location = resp.headers.get("location")
                if not (resp.is_redirect and location):
                    break
                nxt = urljoin(current, location)
                # Refuse to chase a redirect into a non-public address.
                if not await url_is_safe_async(nxt):
                    logger.warning(
                        "unshorten: refusing unsafe redirect %s -> %s", current, nxt
                    )
                    return url
                current = nxt
            if current != url:
                logger.info("unshortened %s → %s", url, current)
            return current
    except Exception as exc:
        logger.debug("unshorten failed for %s: %s", url, exc)
        return url
