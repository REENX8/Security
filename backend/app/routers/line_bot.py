"""LINE Messaging API webhook — phishing URL detection in Thai.

Setup:
  1. Create a LINE Messaging API channel at https://developers.line.biz/
  2. Set environment variables:
       LINE_CHANNEL_TOKEN=<channel access token>
       LINE_CHANNEL_SECRET=<channel secret>
  3. Set the webhook URL in LINE console to:
       https://<your-domain>/api/v1/line/webhook
  4. Send any URL to the bot and it replies with a Thai-language verdict.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger("phish-detector")
router = APIRouter(prefix="/line", tags=["line"])

_URL_RE = re.compile(r"https?://[^\s　-￿]+", re.IGNORECASE)
_LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def _verify_signature(body: bytes, signature: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


def _build_reply(url: str, result: dict) -> str:
    label = result["label"]
    pct = f"{result['score']:.0%}"
    reason = result.get("reason", "-") or "-"
    if label == "phishing":
        return (
            f"⚠️ เว็บนี้น่าสงสัยมาก!\n"
            f"URL: {url}\n"
            f"คะแนนความเสี่ยง: {pct}\n"
            f"เหตุผล: {reason}\n\n"
            "❌ ไม่ควรคลิกหรือกรอกข้อมูลใดๆ ในลิงก์นี้"
        )
    if label == "suspicious":
        return (
            f"🟡 โปรดระวัง — ลิงก์น่าสงสัย\n"
            f"URL: {url}\n"
            f"คะแนนความเสี่ยง: {pct}\n"
            f"เหตุผล: {reason}\n\n"
            "⚠️ ควรตรวจสอบให้แน่ใจก่อนกรอกข้อมูลส่วนตัว"
        )
    return (
        f"✅ ลิงก์นี้ดูปลอดภัย\n"
        f"URL: {url}\n"
        f"คะแนนความเสี่ยง: {pct}"
    )


async def _send_reply(reply_token: str, text: str) -> None:
    if not settings.line_channel_token:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                _LINE_REPLY_URL,
                headers={"Authorization": f"Bearer {settings.line_channel_token}"},
                json={
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": text[:2000]}],
                },
            )
    except Exception as exc:
        logger.warning("LINE reply failed: %s", exc)


@router.post("/webhook", summary="LINE Messaging API webhook for URL checks")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(alias="x-line-signature", default=""),
) -> dict:
    body = await request.body()

    if settings.line_channel_secret:
        if not _verify_signature(body, x_line_signature, settings.line_channel_secret):
            raise HTTPException(status_code=400, detail="invalid LINE signature")

    data = await request.json()
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        return {"status": "no scorer"}

    for event in data.get("events", []):
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("type") != "text":
            continue

        text = msg.get("text", "")
        reply_token = event.get("replyToken", "")
        urls = _URL_RE.findall(text)
        if not urls:
            continue

        url = urls[0]
        result = await run_in_threadpool(scorer.score, url)
        await _send_reply(reply_token, _build_reply(url, result))

    return {"status": "ok"}
