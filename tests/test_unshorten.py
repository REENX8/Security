"""Tests for URL unshortener."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.unshorten import _is_shortener, unshorten_url


def test_is_shortener_known_hosts():
    assert _is_shortener("https://bit.ly/abc123")
    assert _is_shortener("https://t.co/xyz")
    assert _is_shortener("https://tinyurl.com/test")
    assert _is_shortener("https://cutt.ly/abc")
    assert _is_shortener("https://lin.ee/abc")


def test_is_shortener_unknown_hosts():
    assert not _is_shortener("https://www.obec.go.th")
    assert not _is_shortener("https://krungthai.com/login")
    assert not _is_shortener("https://revenue.go.th")


@pytest.mark.asyncio
async def test_unshorten_non_shortener_skips_http():
    url = "https://www.obec.go.th/page"
    # If it's not a shortener, no HTTP call should be made
    with patch("app.unshorten.httpx.AsyncClient") as mock:
        result = await unshorten_url(url)
    mock.assert_not_called()
    assert result == url


@pytest.mark.asyncio
async def test_unshorten_follows_redirect():
    final_url = "https://phishing-site.xyz/login"

    mock_resp = MagicMock()
    mock_resp.url = MagicMock(__str__=lambda self: final_url)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.head = AsyncMock(return_value=mock_resp)

    with patch("app.unshorten.httpx.AsyncClient", return_value=mock_client):
        result = await unshorten_url("https://bit.ly/phish123")

    assert result == final_url


@pytest.mark.asyncio
async def test_unshorten_returns_original_on_network_error():
    original = "https://bit.ly/fail"

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(side_effect=Exception("timeout"))

    with patch("app.unshorten.httpx.AsyncClient", return_value=mock_client):
        result = await unshorten_url(original)

    assert result == original


@pytest.mark.asyncio
async def test_unshorten_same_url_returned_unchanged():
    same_url = "https://bit.ly/same"

    mock_resp = MagicMock()
    mock_resp.url = MagicMock(__str__=lambda self: same_url)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.head = AsyncMock(return_value=mock_resp)

    with patch("app.unshorten.httpx.AsyncClient", return_value=mock_client):
        result = await unshorten_url(same_url)

    assert result == same_url
