"""Tests for the SSRF guard (app.net_guard)."""
from __future__ import annotations

from unittest.mock import patch

from app.net_guard import host_is_safe, url_is_safe


def test_literal_private_ips_blocked():
    assert not host_is_safe("127.0.0.1")
    assert not host_is_safe("10.0.0.1")
    assert not host_is_safe("192.168.1.100")
    assert not host_is_safe("172.16.0.1")
    assert not host_is_safe("169.254.169.254")  # cloud metadata
    assert not host_is_safe("0.0.0.0")
    assert not host_is_safe("::1")


def test_localhost_names_blocked():
    assert not host_is_safe("localhost")
    assert not host_is_safe("db.localhost")
    assert not host_is_safe("")


def test_literal_public_ip_allowed():
    assert host_is_safe("8.8.8.8")
    assert host_is_safe("1.1.1.1")


def test_hostname_resolving_to_private_blocked():
    # Simulate a public DNS name that resolves to a loopback address.
    fake = [(2, 1, 6, "", ("127.0.0.1", 0))]
    with patch("app.net_guard.socket.getaddrinfo", return_value=fake):
        assert not host_is_safe("evil.example.com")


def test_hostname_resolving_to_public_allowed():
    fake = [(2, 1, 6, "", ("93.184.216.34", 0))]
    with patch("app.net_guard.socket.getaddrinfo", return_value=fake):
        assert host_is_safe("example.com")


def test_unresolvable_host_blocked():
    with patch("app.net_guard.socket.getaddrinfo", side_effect=OSError):
        assert not host_is_safe("nope.invalid")


def test_url_is_safe_rejects_non_http_scheme():
    assert not url_is_safe("file:///etc/passwd")
    assert not url_is_safe("ftp://8.8.8.8/x")


def test_url_is_safe_public_https():
    fake = [(2, 1, 6, "", ("93.184.216.34", 0))]
    with patch("app.net_guard.socket.getaddrinfo", return_value=fake):
        assert url_is_safe("https://example.com/path")
