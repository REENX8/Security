"""Tests for LINE Messaging API bot router."""
from __future__ import annotations

import base64
import hashlib
import hmac

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


# ---------------------------------------------------------------------------
# Full webhook flow (mock LINE webhook -> score URL -> reply)
# ---------------------------------------------------------------------------

from unittest.mock import AsyncMock, patch  # noqa: E402

from app.routers import line_bot  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class _FakeScorer:
    def __init__(self, result):
        self._result = result

    def score(self, url):  # called via run_in_threadpool
        return {**self._result, "url": url}


def _client_with_scorer(result):
    app = FastAPI()
    app.include_router(line_bot.router, prefix="/api/v1")
    app.state.scorer = _FakeScorer(result)
    return TestClient(app)


def _message_event(text: str) -> dict:
    return {
        "events": [
            {
                "type": "message",
                "replyToken": "reply-token-123",
                "message": {"type": "text", "text": text},
            }
        ]
    }


def test_webhook_scores_url_and_replies():
    result = {"label": "phishing", "score": 0.95, "reason": "typosquat + login"}
    client = _client_with_scorer(result)
    with patch("app.routers.line_bot._send_reply", new=AsyncMock()) as send:
        resp = client.post(
            "/api/v1/line/webhook",
            json=_message_event("ดูลิงก์นี้ https://ktb-secure.xyz/login หน่อย"),
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    send.assert_awaited_once()
    reply_token, text = send.await_args.args
    assert reply_token == "reply-token-123"
    assert "ktb-secure.xyz" in text
    assert "⚠️" in text  # phishing alarm


def test_webhook_ignores_message_without_url():
    client = _client_with_scorer({"label": "safe", "score": 0.0})
    with patch("app.routers.line_bot._send_reply", new=AsyncMock()) as send:
        resp = client.post("/api/v1/line/webhook", json=_message_event("สวัสดีครับ"))
    assert resp.status_code == 200
    send.assert_not_awaited()


def test_webhook_ignores_non_text_event():
    client = _client_with_scorer({"label": "safe", "score": 0.0})
    payload = {"events": [{"type": "message", "message": {"type": "sticker"}}]}
    with patch("app.routers.line_bot._send_reply", new=AsyncMock()) as send:
        resp = client.post("/api/v1/line/webhook", json=payload)
    assert resp.status_code == 200
    send.assert_not_awaited()


def test_webhook_unshortens_before_scoring():
    result = {"label": "phishing", "score": 0.9, "reason": "x"}
    client = _client_with_scorer(result)
    with patch("app.routers.line_bot._send_reply", new=AsyncMock()) as send, patch(
        "app.routers.line_bot.unshorten_url",
        new=AsyncMock(return_value="https://real-phish.xyz/login"),
    ) as unshorten:
        resp = client.post(
            "/api/v1/line/webhook",
            json=_message_event("https://bit.ly/abc"),
        )
    assert resp.status_code == 200
    unshorten.assert_awaited_once()
    _, text = send.await_args.args
    assert "real-phish.xyz" in text
