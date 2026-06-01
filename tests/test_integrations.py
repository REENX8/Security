"""Tests for the SMS gateway (B2) and government connectors (B3)."""
from __future__ import annotations

import app.config as config_mod
from app.errors import register_error_handlers
from app.integrations.government import (
    GovReport,
    StubGovernmentConnector,
    get_connector,
)
from app.integrations.sms import build_reply, extract_url
from app.routers import integrations
from fastapi import FastAPI
from fastapi.testclient import TestClient

# --- SMS url extraction / reply formatting -------------------------------

def test_extract_url_with_scheme():
    assert extract_url("ดูลิงก์ https://evil.xyz/login นะ") == "https://evil.xyz/login"


def test_extract_url_without_scheme_gets_http():
    assert extract_url("เช็คให้หน่อย bad-bank.co/login") == "http://bad-bank.co/login"


def test_extract_url_none():
    assert extract_url("สวัสดีไม่มีลิงก์") is None
    assert extract_url("") is None


def test_build_reply_labels():
    assert "อันตราย" in build_reply("http://x", {"label": "phishing", "score": 0.9})
    assert "ระวัง" in build_reply("http://x", {"label": "suspicious", "score": 0.5})
    assert "ปลอดภัย" in build_reply("http://x", {"label": "safe", "score": 0.02})


# --- SMS inbound webhook flow --------------------------------------------

class _FakeScorer:
    def score(self, url):
        return {
            "url": url, "score": 0.95, "label": "phishing", "reason": "typosquat",
            "features": {}, "rules": None, "closest_domain": "obec.go.th",
            "edit_distance": 1,
        }


def _sms_client(monkeypatch, secret="s3cret"):
    monkeypatch.setattr(config_mod.settings, "sms_inbound_secret", secret)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(integrations.router, prefix="/api/v1")
    app.state.scorer = _FakeScorer()
    return TestClient(app)


def test_sms_inbound_rejects_bad_secret(monkeypatch):
    client = _sms_client(monkeypatch, secret="right")
    resp = client.post(
        "/api/v1/sms/inbound",
        json={"from": "+66811111111", "body": "http://obec.com/verify", "secret": "wrong"},
    )
    assert resp.status_code == 401


def test_sms_inbound_scores_and_replies(monkeypatch):
    client = _sms_client(monkeypatch, secret="right")
    resp = client.post(
        "/api/v1/sms/inbound",
        headers={"X-SMS-Secret": "right"},
        json={"from": "+66811111111", "body": "เช็ค http://obec.com/verify ให้หน่อย"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "phishing"
    assert "อันตราย" in body["reply"]


def test_sms_inbound_no_url(monkeypatch):
    client = _sms_client(monkeypatch, secret="right")
    resp = client.post(
        "/api/v1/sms/inbound",
        headers={"X-SMS-Secret": "right"},
        json={"from": "x", "body": "สวัสดีครับ"},
    )
    assert resp.status_code == 200
    assert resp.json()["url"] is None


def test_sms_inbound_twilio_form(monkeypatch):
    client = _sms_client(monkeypatch, secret="right")
    resp = client.post(
        "/api/v1/sms/inbound",
        headers={"X-SMS-Secret": "right"},
        data={"From": "+66822222222", "Body": "http://krungthai-secure.top/login"},
    )
    assert resp.status_code == 200
    assert resp.json()["label"] in {"phishing", "suspicious", "safe"}


# --- Government connector (B3) -------------------------------------------

def test_stub_connector_forwards_and_records():
    conn = StubGovernmentConnector(name="etda-1212")
    ok = conn.forward_report(GovReport(url="http://x", score=0.9, reason="typo"))
    assert ok is True
    assert len(conn.forwarded) == 1
    assert conn.fetch_blocklist() == []


def test_get_connector_falls_back_to_stub():
    conn = get_connector("does-not-exist")
    assert conn.name == "stub"
