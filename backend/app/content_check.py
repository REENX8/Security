"""Lightweight content-based check for gray-zone URLs.

Fetches the HTML of a URL and looks for brand impersonation signals
(brand name in page title, credential-harvesting forms) without a headless
browser.  Only called when the ML score falls in the suspicious–phishing
gray zone (between threshold_suspicious and threshold_phishing).

SSRF protection: the hostname is resolved and rejected before any HTTP
connection is made if it points at a private / loopback / link-local /
reserved address (see :mod:`app.net_guard`). Redirects are NOT followed,
so a 30x response cannot bounce the fetch to an internal address.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import httpx

from app.net_guard import url_is_safe_async

logger = logging.getLogger("phish-detector")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_PASSWORD_RE = re.compile(r"<input[^>]*type=['\"]password['\"]", re.IGNORECASE)
_THAI_OFFICIAL_RE = re.compile(r"(?:\.go\.th|\.ac\.th|\.or\.th)", re.IGNORECASE)
_FORM_ACTION_RE = re.compile(
    r"<form[^>]*\baction=['\"]([^'\"]+)['\"]", re.IGNORECASE
)
_META_REFRESH_RE = re.compile(
    r"<meta[^>]*http-equiv=['\"]refresh['\"][^>]*url=([^'\"> ]+)",
    re.IGNORECASE,
)

async def content_score_adjustment(
    url: str,
    brand_labels: frozenset[str],
    timeout: float = 5.0,
) -> float:
    """Return a score adjustment in [-0.20, +0.40] based on page content.

    Positive means more phishing evidence; negative means safer signal.
    Signals: brand-in-title, password field, login form posting to a foreign
    host (form-jacking), meta-refresh to a foreign host, and a Thai-official
    title (reduces suspicion). Returns 0.0 on any fetch error (fail-open —
    never blocks a verdict).
    """
    host = urlparse(url).netloc.lower().removeprefix("www.")
    # SSRF guard: resolve the host and bail on any non-public address.
    if not await url_is_safe_async(url):
        return 0.0

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhishBot/1.0)"},
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
    has_password = bool(_PASSWORD_RE.search(html))
    if has_password:
        adj += 0.10

    # A login form whose action posts to a DIFFERENT host is a classic
    # credential-exfiltration / form-jacking signal. Only meaningful when the
    # page is actually collecting a password.
    if has_password:
        for action in _FORM_ACTION_RE.findall(html):
            action_host = urlparse(action.strip()).netloc.lower().removeprefix("www.")
            if action_host and action_host != host:
                adj += 0.15
                logger.debug(
                    "content_check: form posts to foreign host %s (page %s)",
                    action_host, host,
                )
                break

    # An immediate meta-refresh to another host is a cloaking/redirect trick.
    refresh = _META_REFRESH_RE.search(html)
    if refresh:
        target_host = urlparse(refresh.group(1).strip()).netloc.lower().removeprefix("www.")
        if target_host and target_host != host:
            adj += 0.10

    # Legitimate Thai official domain strings in the title reduce suspicion
    if _THAI_OFFICIAL_RE.search(title):
        adj -= 0.10

    return max(-0.20, min(0.40, adj))
