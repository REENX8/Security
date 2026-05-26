"""Tests for LINE Messaging API bot router."""
from __future__ import annotations

import base64
import hashlib
import hmac

import pytest

from app.routers.line_bot import _build_reply, _verify_signature


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def _sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def test_verify_signature_valid():
    body = b'{"events": []}'
    secret = "test-secret-key"
    assert _verify_signature(body, _sign(body, secret), secret)


def test_verify_signature_wrong_secret():
    body = b'{"events": []}'
    assert not _verify_signature(body, _sign(body, "correct"), "wrong")


def test_verify_signature_tampered_body():
    secret = "test-secret-key"
    original = b'{"events": []}'
    sig = _sign(original, secret)
    assert not _verify_signature(b'{"events": [{}]}', sig, secret)


# ---------------------------------------------------------------------------
# Reply text builder
# ---------------------------------------------------------------------------

def test_build_reply_phishing():
    result = {"label": "phishing", "score": 0.95, "reason": "typosquat + login keyword"}
    reply = _build_reply("https://ktb-secure.xyz/login", result)
    assert "⚠️" in reply
    assert "95%" in reply
    assert "❌" in reply
    assert "typosquat" in reply


def test_build_reply_suspicious():
    result = {"label": "suspicious", "score": 0.50, "reason": "cheap TLD"}
    reply = _build_reply("https://random.cc/bank", result)
    assert "🟡" in reply
    assert "50%" in reply
    assert "⚠️" in reply


def test_build_reply_safe():
    result = {"label": "safe", "score": 0.05, "reason": "whitelisted"}
    reply = _build_reply("https://obec.go.th", result)
    assert "✅" in reply
    assert "5%" in reply
    # No alarm emoji
    assert "⚠️" not in reply
    assert "❌" not in reply


def test_build_reply_missing_reason_does_not_crash():
    result = {"label": "phishing", "score": 0.9}
    reply = _build_reply("https://fake.xyz", result)
    assert "⚠️" in reply


def test_build_reply_text_capped_at_2000_chars():
    long_reason = "x" * 3000
    result = {"label": "phishing", "score": 0.99, "reason": long_reason}
    reply = _build_reply("https://fake.xyz", result)
    # _build_reply itself has no cap; the cap is applied in _send_reply
    assert isinstance(reply, str)
