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


def test_stub_connector_batch_forward():
    conn = StubGovernmentConnector()
    ok = conn.forward_reports(
        [GovReport(url="http://a", score=0.9), GovReport(url="http://b", score=0.8)]
    )
    assert ok is True
    assert len(conn.forwarded) == 2


def test_get_connector_falls_back_to_stub():
    conn = get_connector("does-not-exist")
    assert conn.name == "stub"


# --- Email intake connector (B3) -----------------------------------------

from types import SimpleNamespace  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from app.integrations.government import (  # noqa: E402
    EmailIntakeConnector,
    reports_to_csv,
)


def _email_settings(**over):
    base = {
        "gov_email_smtp_host": "smtp.example.com",
        "gov_email_smtp_port": 587,
        "gov_email_smtp_user": "bot@example.com",
        "gov_email_smtp_password": "pw",
        "gov_email_use_tls": True,
        "gov_email_from": "bot@example.com",
        "gov_email_to": "intake@etda.or.th, cyber@police.go.th",
    }
    base.update(over)
    return SimpleNamespace(**base)


def test_reports_to_csv_has_header_and_rows():
    csv_text = reports_to_csv(
        [GovReport(url="http://x", score=0.91, closest_domain="obec.go.th", reason="typo")]
    )
    assert csv_text.splitlines()[0] == "url,score,closest_domain,reason"
    assert "http://x" in csv_text
    assert "0.9100" in csv_text


def test_email_connector_not_configured_returns_false():
    conn = EmailIntakeConnector.from_settings(_email_settings(gov_email_smtp_host=""))
    assert conn.is_configured() is False
    assert conn.forward_reports([GovReport(url="http://x", score=0.9)]) is False


def test_email_connector_sends_csv_attachment(monkeypatch):
    conn = EmailIntakeConnector.from_settings(_email_settings())
    assert conn.is_configured() is True
    assert conn.recipients == ("intake@etda.or.th", "cyber@police.go.th")

    smtp = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = smtp
    smtp_cm.__exit__.return_value = False
    monkeypatch.setattr(
        "app.integrations.government.smtplib.SMTP", MagicMock(return_value=smtp_cm)
    )

    ok = conn.forward_reports([GovReport(url="http://phish.xyz", score=0.95)])
    assert ok is True
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("bot@example.com", "pw")
    smtp.send_message.assert_called_once()
    msg = smtp.send_message.call_args.args[0]
    assert msg["To"] == "intake@etda.or.th, cyber@police.go.th"
    # The CSV is attached.
    attachments = list(msg.iter_attachments())
    assert len(attachments) == 1
    assert "phish.xyz" in attachments[0].get_content()


def test_email_connector_send_failure_returns_false(monkeypatch):
    conn = EmailIntakeConnector.from_settings(_email_settings())
    monkeypatch.setattr(
        "app.integrations.government.smtplib.SMTP",
        MagicMock(side_effect=OSError("connection refused")),
    )
    assert conn.forward_reports([GovReport(url="http://x", score=0.9)]) is False


def test_get_connector_email_built_from_settings():
    conn = get_connector("email", _email_settings())
    assert isinstance(conn, EmailIntakeConnector)
    assert conn.smtp_host == "smtp.example.com"
