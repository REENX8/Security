"""SMS report gateway (B2).

Lets people without a smartphone app report (or check) a suspicious URL by text
message. An SMS provider (Twilio, Thai aggregators) is configured to POST inbound
messages to ``/api/v1/sms/inbound``; the handler extracts a URL, scores it, and
returns a short Thai reply the provider sends back.

The provider integration is a small Protocol so the inbound handling and reply
formatting are testable without a live SMS account; an outbound reply provider is
optional (the common case is the provider replying with the webhook's response).
"""

from __future__ import annotations

import re
from typing import Protocol

# Generous URL matcher; SMS bodies are plain text and may omit the scheme.
_URL_RE = re.compile(r"\b((?:https?://)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)", re.IGNORECASE)


class SmsProvider(Protocol):
    """Outbound SMS sender. Implementations wrap Twilio / a Thai aggregator."""

    def send(self, to: str, body: str) -> None: ...


class NullSmsProvider:
    """Default no-op provider: the webhook response carries the reply instead."""

    def send(self, to: str, body: str) -> None:  # noqa: D401 - stub
        return None


def extract_url(body: str) -> str | None:
    """Return the first URL-like token in an SMS body, normalised to http(s)."""
    if not body:
        return None
    match = _URL_RE.search(body)
    if not match:
        return None
    candidate = match.group(1).strip().rstrip(".")
    if not candidate.lower().startswith(("http://", "https://")):
        candidate = "http://" + candidate
    return candidate


def build_reply(url: str, result: dict) -> str:
    """Short SMS-length Thai verdict (kept within ~1 160-char segment where possible)."""
    label = result.get("label")
    pct = f"{float(result.get('score', 0)):.0%}"
    if label == "phishing":
        return f"อันตราย! {url} เสี่ยงฟิชชิง {pct} อย่าคลิก/กรอกข้อมูล"
    if label == "suspicious":
        return f"ระวัง {url} น่าสงสัย {pct} ตรวจสอบก่อนกรอกข้อมูล"
    return f"ปลอดภัย {url} ความเสี่ยง {pct}"
