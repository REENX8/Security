"""Lightweight content-based check for gray-zone URLs.

Fetches the HTML of a URL and looks for brand impersonation signals
(brand name in page title, credential-harvesting forms) without a headless
browser.  Only called when the ML score falls in the suspicious–phishing
gray zone (between threshold_suspicious and threshold_phishing).

SSRF protection: private-IP ranges and localhost are rejected before
any HTTP connection is made.
"""
from __future__ import annotations

import ipaddress
import logging
import re
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("phish-detector")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_PASSWORD_RE = re.compile(r"<input[^>]*type=['\"]password['\"]", re.IGNORECASE)
_THAI_OFFICIAL_RE = re.compile(r"(?:\.go\.th|\.ac\.th|\.or\.th)", re.IGNORECASE)

_PRIVATE_NETS = [
    ipaddress.ip_network(c)
    for c in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "::1/128",
    )
]


def _is_private_host(host: str) -> bool:
    if host in ("localhost", "localtest.me"):
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in _PRIVATE_NETS)
    except ValueError:
        return False


async def content_score_adjustment(
    url: str,
    brand_labels: frozenset[str],
    timeout: float = 5.0,
) -> float:
    """Return a score adjustment in [-0.20, +0.30] based on page content.

    Positive means more phishing evidence; negative means safer signal.
    Returns 0.0 on any fetch error (fail-open — never blocks a verdict).
    """
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if _is_private_host(host):
        return 0.0

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhishBot/1.0)"},
            max_redirects=3,
        ) as client:
            resp = await client.get(url)
            if resp.status_code not in range(200, 300):
                return 0.0
            html = resp.text[:65536]  # cap at 64 KB
    except Exception as exc:
        logger.debug("content_check fetch failed for %s: %s", url, exc)
        return 0.0

    adj = 0.0
    html_lower = html.lower()

    title_match = _TITLE_RE.search(html_lower)
    title = title_match.group(1).strip() if title_match else ""

    # Brand label appears in page title but NOT in the URL's host
    for label in brand_labels:
        if label.lower() in title and label.lower() not in host:
            adj += 0.15
            logger.debug(
                "content_check: brand '%s' in title but not in host (%s)", label, host
            )
            break  # count once even if multiple brands match

    # Password field = credential-harvesting attempt
    if _PASSWORD_RE.search(html):
        adj += 0.10

    # Legitimate Thai official domain strings in the title reduce suspicion
    if _THAI_OFFICIAL_RE.search(title):
        adj -= 0.10

    return max(-0.20, min(0.30, adj))
