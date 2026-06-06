"""Visual fingerprint adjustment for gray-zone URLs (B6).

Mirrors :mod:`app.content_check`: a bounded, fail-open, SSRF-guarded score
adjustment, applied off the hot path (gray-zone only) behind
``VISUAL_FINGERPRINT_ENABLED``. It screenshots the page (via the configured
renderer), computes a perceptual hash, and compares it against a library of
genuine agency-page templates. A close visual match to a real agency page hosted
on a **non-official** host is a strong pixel-clone signal and raises the score.
"""

from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlparse

from app.net_guard import url_is_safe_async
from app.visual.phash import dhash, hamming, is_degenerate

logger = logging.getLogger("phish-detector")

_MIN_BUMP = 0.15
_MAX_BUMP = 0.35


def load_templates(path: str) -> list[dict]:
    """Load the committed template library (``{agency, official_host, dhash}``).

    Returns an empty list (feature is a no-op) if the file is missing or
    malformed, so a bad library never breaks scoring.
    """
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        templates = payload.get("templates", [])
        # Drop malformed and degenerate (near-blank) template hashes — the
        # latter would match any blank render and cause false positives.
        return [
            t for t in templates
            if isinstance(t.get("dhash"), int) and not is_degenerate(t["dhash"])
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("visual: failed to load templates from %s: %s", path, exc)
        return []


def _host_matches_official(host: str, official: str) -> bool:
    host = host.lower().removeprefix("www.")
    official = official.lower().removeprefix("www.")
    return bool(official) and (host == official or host.endswith("." + official))


async def visual_fingerprint_adjustment(
    url: str,
    *,
    renderer,
    templates: list[dict],
    timeout: float = 8.0,
    max_distance: int = 10,
) -> float:
    """Return a bounded ``[0.0, +0.35]`` adjustment from a visual clone match.

    Fail-open: returns 0.0 on any SSRF rejection, render error, or empty
    library. A match on the template's own official host is ignored (it's the
    real site, not a clone).
    """
    if not templates:
        return 0.0
    if not await url_is_safe_async(url):
        return 0.0
    try:
        grid = await renderer.render_gray(url, timeout)
    except Exception as exc:  # noqa: BLE001
        logger.debug("visual: renderer raised for %s: %s", url, exc)
        return 0.0
    if not grid:
        return 0.0
    try:
        page_hash = dhash(grid)
    except Exception as exc:  # noqa: BLE001
        logger.debug("visual: hash failed for %s: %s", url, exc)
        return 0.0
    # A blank / unpainted render carries no structural signal; matching it would
    # produce false positives against any low-bit template.
    if is_degenerate(page_hash):
        return 0.0

    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    best: int | None = None
    for tmpl in templates:
        dist = hamming(page_hash, tmpl["dhash"])
        if dist > max_distance:
            continue
        if _host_matches_official(host, tmpl.get("official_host", "")):
            continue  # genuine site — not a clone
        if best is None or dist < best:
            best = dist

    if best is None:
        return 0.0
    # Closer match -> stronger signal. d=0 -> _MAX_BUMP, d=max_distance -> _MIN_BUMP.
    frac = 1.0 - (best / max(1, max_distance))
    return round(_MIN_BUMP + (_MAX_BUMP - _MIN_BUMP) * frac, 4)
