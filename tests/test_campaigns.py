"""Tests for the campaign clustering helpers."""

from __future__ import annotations

from app.campaigns import _path_shape, _tld_signature, build_fingerprint


def test_path_shape_normalises_digits():
    assert _path_shape("https://x.cc/account/12345/login") == "account/#/login"


def test_path_shape_normalises_hex_tokens():
    assert _path_shape(
        "https://x.cc/session/abcdef1234567890/login"
    ) == "session/$hex/login"


def test_tld_signature():
    assert _tld_signature("https://verify.shop/auth") == "shop"
    assert _tld_signature("https://obec.go.th") == "th"


def test_fingerprint_is_stable():
    fp = build_fingerprint(
        "https://random-1.cc/krungthai/login",
        closest_domain="krungthai.com",
    )
    fp2 = build_fingerprint(
        "https://random-2.cc/krungthai/login",
        closest_domain="krungthai.com",
    )
    # Same brand, same tld, same path skeleton -> same fingerprint even
    # though the host is different.
    assert fp == fp2
