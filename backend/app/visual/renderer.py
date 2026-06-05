"""Pluggable page renderers for visual fingerprinting (B6).

Mirrors the no-op-default provider pattern (`integrations/sms.py`,
`integrations/asn.py`):

* ``NullRenderer`` (default) renders nothing — returns ``None`` for every URL.
  No browser, no image library, fully deterministic. This is the CI/demo path.
* ``PlaywrightRenderer`` (opt-in, ``VISUAL_RENDERER=playwright``) screenshots the
  page with headless Chromium and downsamples it to a small grayscale grid.
  Playwright and Pillow are imported **lazily inside the method**, so importing
  this module never requires them and the default path stays dependency-free.

A renderer returns a grayscale pixel grid (``list[list[int]]``) or ``None``; the
perceptual hash is computed from the grid by ``app/visual/phash.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("phish-detector")

# Grid the screenshot is downsampled to before hashing. Generous enough for a
# stable dHash, small enough to stay cheap.
_GRID_W = 32
_GRID_H = 32


class Renderer(Protocol):
    """Render a URL to a small grayscale pixel grid (or None)."""

    name: str

    async def render_gray(self, url: str, timeout: float) -> list[list[int]] | None: ...


@dataclass
class NullRenderer:
    """No-op renderer: never produces pixels (the default)."""

    name: str = "null"

    async def render_gray(self, url: str, timeout: float) -> list[list[int]] | None:  # noqa: ARG002
        return None


@dataclass
class PlaywrightRenderer:
    """Headless-Chromium screenshot renderer (opt-in).

    Heavy + slow (a browser in the path), so it is only ever used behind the
    feature flag and off the hot path (gray-zone only). Imports are lazy so the
    dependency is required only when this renderer is actually selected.
    """

    name: str = "playwright"
    width: int = 1280
    height: int = 800

    async def render_gray(self, url: str, timeout: float) -> list[list[int]] | None:
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except Exception:  # noqa: BLE001 - optional dependency
            logger.warning("visual: playwright not installed; install .[visual]")
            return None
        png_bytes: bytes | None = None
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    page = await browser.new_page(
                        viewport={"width": self.width, "height": self.height}
                    )
                    await page.goto(
                        url, timeout=int(timeout * 1000), wait_until="domcontentloaded"
                    )
                    png_bytes = await page.screenshot(type="png")
                finally:
                    await browser.close()
        except Exception as exc:  # noqa: BLE001 - never break a verdict
            logger.debug("visual: render failed for %s: %s", url, exc)
            return None
        return _png_to_gray_grid(png_bytes)


def _png_to_gray_grid(png_bytes: bytes | None) -> list[list[int]] | None:
    """Decode PNG bytes into a downsampled grayscale grid (lazy Pillow import)."""
    if not png_bytes:
        return None
    try:
        import io

        from PIL import Image  # type: ignore
    except Exception:  # noqa: BLE001 - optional dependency
        logger.warning("visual: Pillow not installed; install .[visual]")
        return None
    try:
        img = Image.open(io.BytesIO(png_bytes)).convert("L").resize((_GRID_W, _GRID_H))
        px = list(img.getdata())
        return [px[r * _GRID_W:(r + 1) * _GRID_W] for r in range(_GRID_H)]
    except Exception as exc:  # noqa: BLE001
        logger.debug("visual: decode failed: %s", exc)
        return None


_RENDERERS: dict[str, Renderer] = {"null": NullRenderer()}


def get_renderer(name: str, settings=None) -> Renderer:  # noqa: ARG001
    """Return the configured renderer, falling back to the null renderer."""
    if name == "playwright":
        return PlaywrightRenderer()
    return _RENDERERS.get(name, _RENDERERS["null"])
