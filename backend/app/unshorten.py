"""Async URL unshortener — follows redirects for known short-link services."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("phish-detector")

_SHORTENER_HOSTS: frozenset[str] = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "ow.ly", "tiny.cc",
    "is.gd", "buff.ly", "short.link", "rb.gy", "lnkd.in", "shorturl.at",
    "goo.gl", "t.me", "fb.me", "adf.ly", "v.gd", "trib.al",
    "s.id", "lin.ee",
})


def _is_shortener(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host in _SHORTENER_HOSTS


async def unshorten_url(url: str, timeout: float = 5.0) -> str:
    """Return the final URL after following redirects, or the original URL on error."""
    if not _is_shortener(url):
        return url
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhishBot/1.0)"},
        ) as client:
            resp = await client.head(url)
            final = str(resp.url)
            if final != url:
                logger.info("unshortened %s → %s", url, final)
            return final
    except Exception as exc:
        logger.debug("unshorten failed for %s: %s", url, exc)
        return url
