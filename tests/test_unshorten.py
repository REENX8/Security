"""Tests for the URL unshortener (manual redirect following + SSRF guard)."""
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


def _redirect(location: str):
    resp = MagicMock()
    resp.is_redirect = True
    resp.headers = {"location": location}
    return resp


def _final():
    resp = MagicMock()
    resp.is_redirect = False
    resp.headers = {}
    return resp


def _client_returning(*responses):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.head = AsyncMock(side_effect=list(responses))
    return mock_client


@pytest.mark.asyncio
async def test_unshorten_non_shortener_skips_http():
    url = "https://www.obec.go.th/page"
    with patch("app.unshorten.httpx.AsyncClient") as mock:
        result = await unshorten_url(url)
    mock.assert_not_called()
    assert result == url


@pytest.mark.asyncio
async def test_unshorten_follows_redirect():
    final_url = "https://phishing-site.xyz/login"
    client = _client_returning(_redirect(final_url), _final())
    with patch("app.unshorten.httpx.AsyncClient", return_value=client), \
            patch("app.unshorten.url_is_safe_async", AsyncMock(return_value=True)):
        result = await unshorten_url("https://bit.ly/phish123")
    assert result == final_url


@pytest.mark.asyncio
async def test_unshorten_refuses_redirect_to_internal_address():
    """A short link that 30x-es to a private/metadata address is not followed."""
    client = _client_returning(_redirect("http://169.254.169.254/latest/meta-data/"))
    with patch("app.unshorten.httpx.AsyncClient", return_value=client), \
            patch("app.unshorten.url_is_safe_async", AsyncMock(return_value=False)):
        result = await unshorten_url("https://bit.ly/ssrf")
    # Falls back to the original short URL, never exposing the internal target.
    assert result == "https://bit.ly/ssrf"


@pytest.mark.asyncio
async def test_unshorten_returns_original_on_network_error():
    original = "https://bit.ly/fail"
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
    with patch("app.unshorten.httpx.AsyncClient", return_value=mock_client):
        result = await unshorten_url(original)
    assert result == original


@pytest.mark.asyncio
async def test_unshorten_no_redirect_returns_original():
    same_url = "https://bit.ly/same"
    client = _client_returning(_final())
    with patch("app.unshorten.httpx.AsyncClient", return_value=client):
        result = await unshorten_url(same_url)
    assert result == same_url
