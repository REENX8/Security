"""Tests for content-based gray-zone fallback check."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.content_check import _is_private_host, content_score_adjustment


def test_private_host_loopback():
    assert _is_private_host("127.0.0.1")
    assert _is_private_host("::1")
    assert _is_private_host("localhost")
    assert _is_private_host("localtest.me")


def test_private_host_rfc1918():
    assert _is_private_host("192.168.1.100")
    assert _is_private_host("10.0.0.1")
    assert _is_private_host("172.16.0.1")
    assert _is_private_host("172.31.255.255")


def test_public_host_not_private():
    assert not _is_private_host("8.8.8.8")
    assert not _is_private_host("phishing.xyz")


@pytest.mark.asyncio
async def test_private_host_returns_zero_no_fetch():
    with patch("app.content_check.httpx.AsyncClient") as mock:
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
    with patch("app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)):
        adj = await content_score_adjustment(
            "https://random-abc123.xyz/login",
            frozenset({"krungthai"}),
        )
    assert adj > 0.0


@pytest.mark.asyncio
async def test_password_field_raises_score():
    html = "<html><title>ระบบ</title><input type='password' name='pass'/></html>"
    with patch("app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)):
        adj = await content_score_adjustment(
            "https://somesite.xyz/login",
            frozenset(),
        )
    assert adj >= 0.10


@pytest.mark.asyncio
async def test_thai_official_in_title_lowers_score():
    html = "<html><title>portal.moph.go.th ระบบ</title></html>"
    with patch("app.content_check.httpx.AsyncClient", return_value=_make_mock_client(html)):
        adj = await content_score_adjustment(
            "https://legit.moph.go.th/system",
            frozenset(),
        )
    assert adj < 0.0


@pytest.mark.asyncio
async def test_fetch_error_returns_zero():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
    with patch("app.content_check.httpx.AsyncClient", return_value=mock_client):
        adj = await content_score_adjustment(
            "https://safe.obec.go.th", frozenset({"obec"})
        )
    assert adj == 0.0


@pytest.mark.asyncio
async def test_non_200_returns_zero():
    with patch("app.content_check.httpx.AsyncClient", return_value=_make_mock_client("", 404)):
        adj = await content_score_adjustment("https://example.xyz", frozenset())
    assert adj == 0.0


def _make_mock_client(html: str, status: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.text = html

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


def _make_mock_fetch(html: str, status: int = 200):
    pass  # helper kept for readability — actual mock built inline
