"""Tests for visual fingerprinting (B6).

All deterministic and offline: the perceptual hash is pure-Python and the
renderer is the NullRenderer or an in-test stub, so no browser/Pillow/network
is ever needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.visual.fingerprint import (
    load_templates,
    visual_fingerprint_adjustment,
)
from app.visual.phash import dhash, hamming, is_degenerate
from app.visual.renderer import NullRenderer, get_renderer

TEMPLATES_JSON = Path(__file__).resolve().parents[1] / "data" / "visual_templates" / "templates.json"


@pytest.fixture(autouse=True)
def _allow_ssrf(monkeypatch):
    """Bypass the SSRF/DNS guard so tests exercise the fingerprint logic, not
    live name resolution (mirrors how test_content_check stubs the guard)."""
    async def _ok(_url):
        return True

    monkeypatch.setattr("app.visual.fingerprint.url_is_safe_async", _ok)


# --- pure-Python hash -------------------------------------------------------

def _grid(rows, cols, fn):
    return [[fn(r, c) for c in range(cols)] for r in range(rows)]


def _bal(r, c):
    """Spatially-hashed value with good bit spread, so dhash is non-degenerate
    (a smooth gradient hashes to a near-uniform, degenerate value)."""
    return ((r * 73856093) ^ (c * 19349663)) % 256


def test_dhash_identical_grids_zero_distance():
    g = _grid(32, 32, lambda r, c: (r * 7 + c * 3) % 256)
    assert hamming(dhash(g), dhash(g)) == 0


def test_dhash_differs_for_different_images():
    g1 = _grid(32, 32, lambda r, c: (r * 7 + c * 3) % 256)
    g2 = _grid(32, 32, lambda r, c: (c * 11 + r) % 256)
    assert hamming(dhash(g1), dhash(g2)) > 0


def test_dhash_is_64_bits():
    g = _grid(16, 16, lambda r, c: (r + c) % 256)
    assert 0 <= dhash(g, size=8) < (1 << 64)


def test_dhash_empty_grid_raises():
    with pytest.raises(ValueError):
        dhash([])


# --- renderer registry ------------------------------------------------------

def test_get_renderer_defaults_to_null():
    assert isinstance(get_renderer("null"), NullRenderer)
    assert isinstance(get_renderer("unknown"), NullRenderer)


async def test_null_renderer_returns_none():
    assert await NullRenderer().render_gray("https://x.test", 5.0) is None


# --- template library -------------------------------------------------------

def test_committed_templates_json_well_formed():
    payload = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))
    assert isinstance(payload.get("templates"), list)
    for t in payload["templates"]:
        assert isinstance(t["dhash"], int)
        assert t["official_host"]


def test_committed_templates_are_non_degenerate_and_load():
    # The committed library must not carry blank/near-uniform hashes (they would
    # match any blank render). load_templates filters them, so the loaded count
    # must equal the raw count — i.e. nothing committed is degenerate.
    payload = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))
    raw = payload["templates"]
    loaded = load_templates(str(TEMPLATES_JSON))
    assert len(loaded) == len(raw), "a committed template hash is degenerate"
    for t in raw:
        assert not is_degenerate(t["dhash"])


def test_is_degenerate():
    assert is_degenerate(0)  # blank page
    assert is_degenerate((1 << 64) - 1)  # all bits set
    # A balanced hash is not degenerate.
    assert not is_degenerate(dhash(_grid(32, 32, _bal)))


def test_load_templates_filters_degenerate(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"templates": [
        {"agency": "blank", "official_host": "x.go.th", "dhash": 0},
        {"agency": "good", "official_host": "y.go.th",
         "dhash": dhash(_grid(32, 32, _bal))},
    ]}), encoding="utf-8")
    loaded = load_templates(str(p))
    assert len(loaded) == 1
    assert loaded[0]["agency"] == "good"


def test_load_templates_missing_file_returns_empty():
    assert load_templates("/nonexistent/templates.json") == []


# --- adjustment -------------------------------------------------------------

class _StubRenderer:
    """Returns a fixed grid so tests are deterministic without a browser."""

    name = "stub"

    def __init__(self, grid):
        self._grid = grid

    async def render_gray(self, url, timeout):  # noqa: ARG002
        return self._grid


class _RaisingRenderer:
    name = "boom"

    async def render_gray(self, url, timeout):  # noqa: ARG002
        raise RuntimeError("render exploded")


def _template_for(grid, official_host):
    return [{"agency": "X", "official_host": official_host, "dhash": dhash(grid)}]


async def test_no_templates_returns_zero():
    grid = _grid(32, 32, lambda r, c: (r + c) % 256)
    adj = await visual_fingerprint_adjustment(
        "https://clone.cc/login", renderer=_StubRenderer(grid), templates=[]
    )
    assert adj == 0.0


async def test_null_renderer_no_match_returns_zero():
    tmpl = _template_for(_grid(32, 32, lambda r, c: (r + c) % 256), "obec.go.th")
    adj = await visual_fingerprint_adjustment(
        "https://clone.cc/login", renderer=NullRenderer(), templates=tmpl
    )
    assert adj == 0.0


async def test_close_match_on_foreign_host_raises_score():
    grid = _grid(32, 32, _bal)
    tmpl = _template_for(grid, "obec.go.th")
    # Same pixels, clone host -> strong match -> positive bump.
    adj = await visual_fingerprint_adjustment(
        "https://obec-login.cc/verify",
        renderer=_StubRenderer(grid),
        templates=tmpl,
    )
    assert 0.0 < adj <= 0.35


async def test_match_on_official_host_not_flagged():
    grid = _grid(32, 32, _bal)
    tmpl = _template_for(grid, "obec.go.th")
    adj = await visual_fingerprint_adjustment(
        "https://www.obec.go.th/login",
        renderer=_StubRenderer(grid),
        templates=tmpl,
    )
    assert adj == 0.0


async def test_render_error_fails_open():
    grid = _grid(32, 32, lambda r, c: (r + c) % 256)
    tmpl = _template_for(grid, "obec.go.th")
    adj = await visual_fingerprint_adjustment(
        "https://clone.cc/login", renderer=_RaisingRenderer(), templates=tmpl
    )
    assert adj == 0.0


async def test_distant_image_no_match():
    grid_a = _grid(32, 32, _bal)
    grid_b = _grid(32, 32, lambda r, c: ((r * 12582917) ^ (c * 6291469)) % 256)
    tmpl = _template_for(grid_a, "obec.go.th")
    adj = await visual_fingerprint_adjustment(
        "https://clone.cc/login",
        renderer=_StubRenderer(grid_b),
        templates=tmpl,
        max_distance=2,
    )
    assert adj == 0.0
