"""Inbound SMS report gateway (B2): POST /api/v1/sms/inbound.

Provider-agnostic: accepts either JSON ({"from","body","secret"}) or a
Twilio-style form (From/Body). Authenticated by a shared secret. Extracts a URL,
scores it (reusing the loaded model), persists the check, and returns a short
Thai reply the provider can SMS back to the sender.
"""

import logging

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.crud import insert_check
from app.database import get_session
from app.errors import AppError
from app.integrations.sms import build_reply, extract_url
from app.unshorten import unshorten_url

router = APIRouter(prefix="/sms", tags=["sms"])
logger = logging.getLogger("phish-detector")


async def _parse_inbound(request: Request) -> tuple[str, str, str]:
    """Return (sender, body, secret) from JSON or form-encoded providers.

    Parses the raw body directly (no python-multipart dependency): Twilio and
    most aggregators post ``application/x-www-form-urlencoded``.
    """
    ctype = request.headers.get("content-type", "")
    raw = await request.body()
    if "application/json" in ctype:
        import json

        data = json.loads(raw or b"{}")
        return (
            str(data.get("from", "")),
            str(data.get("body", "")),
            str(data.get("secret", "")),
        )
    from urllib.parse import parse_qs

    form = {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "ignore")).items()}
    return (
        form.get("From", form.get("from", "")),
        form.get("Body", form.get("body", "")),
        form.get("secret", ""),
    )


@router.post("/inbound", summary="Inbound SMS report/check (provider webhook)")
async def sms_inbound(request: Request) -> dict:
    sender, body, body_secret = await _parse_inbound(request)
    secret = request.headers.get("x-sms-secret", "") or body_secret
    if not settings.sms_inbound_secret or secret != settings.sms_inbound_secret:
        raise AppError("invalid SMS secret", code="UNAUTHORIZED", status_code=401)

    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise AppError(
            "model not loaded", code="MODEL_NOT_LOADED", status_code=503
        )

    url = extract_url(body)
    if not url:
        return {"reply": "ไม่พบลิงก์ในข้อความ กรุณาส่ง URL ที่ต้องการตรวจสอบ", "url": None}

    if settings.enable_url_unshortening:
        url = await unshorten_url(url, timeout=settings.unshorten_timeout)

    result = await run_in_threadpool(scorer.score, url)

    # Persist the citizen-reported check (best-effort; never fail the reply).
    try:
        async for session in get_session():
            await insert_check(session, result)
            break
    except Exception as exc:  # noqa: BLE001
        logger.warning("sms inbound: persist skipped: %s", exc)

    logger.info("sms inbound from %s: %s -> %s", sender or "?", url, result.get("label"))
    return {"reply": build_reply(url, result), "url": url, "label": result.get("label")}
