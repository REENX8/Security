#!/usr/bin/env python3
"""Generate / append visual-fingerprint templates (B6) from real agency pages.

Screenshots a genuine agency page with the opt-in Playwright renderer, computes
its perceptual hash, and appends an entry to data/visual_templates/templates.json
so the visual-fingerprint check can flag pixel-clones of that page on other hosts.

This is an OPERATOR tool, run offline when curating the template library — it is
NOT part of CI and needs the optional visual extra installed:

    pip install -e ".[visual]"
    python -m playwright install chromium
    python scripts/build_visual_templates.py \
        --url https://www.<agency>.go.th --agency "<agency>" --label "login page"

The repo ships templates.json empty because it cannot render real pages; this
script is how a deployment populates it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

TEMPLATES_JSON = os.path.join(ROOT, "data", "visual_templates", "templates.json")


async def _hash_url(url: str, timeout: float) -> int | None:
    from app.visual.phash import dhash
    from app.visual.renderer import PlaywrightRenderer

    grid = await PlaywrightRenderer().render_gray(url, timeout)
    if not grid:
        return None
    return dhash(grid)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="genuine agency page URL")
    parser.add_argument("--agency", required=True, help="agency name")
    parser.add_argument("--label", default="", help="optional note")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--out", default=TEMPLATES_JSON)
    args = parser.parse_args()

    h = asyncio.run(_hash_url(args.url, args.timeout))
    if h is None:
        print("[visual] render failed (need .[visual] + chromium?)", file=sys.stderr)
        return 1

    official_host = (urlparse(args.url).hostname or "").lower().removeprefix("www.")
    with open(args.out, encoding="utf-8") as fh:
        payload = json.load(fh)
    payload.setdefault("templates", []).append(
        {
            "agency": args.agency,
            "official_host": official_host,
            "dhash": h,
            "label": args.label,
        }
    )
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f"[visual] appended {args.agency} ({official_host}) dhash={h} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
