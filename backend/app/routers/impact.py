"""GET /api/v1/impact -- public social-impact metrics.

This is the "Sustainable Innovation" face of the system. The NSC 2026
theme rewards work that demonstrates measurable benefit to society;
this endpoint surfaces that benefit in a single, public-facing JSON
object so judges, journalists and partner agencies can quote it
without needing API credentials.

Numbers are computed live from the database so there is no risk of
stale marketing copy. Estimates that depend on outside assumptions
(eg. average loss per phishing victim) are clearly tagged so the
caller can substitute their own figures.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import BrandWatch, Campaign, Feedback, Label, UrlCheck

router = APIRouter()

# Public-source estimates (ETDA / ThaiCERT / Bangkok Post 2024-2025 reports
# on financial losses per phishing victim in Thailand). The figure is the
# MEDIAN reported loss, not the mean -- the mean is dominated by a long
# tail of corporate breaches that this tool doesn't claim to prevent.
THB_PER_PHISHING_BLOCKED = 7800  # median reported per-incident loss


class ImpactResponse(BaseModel):
    schema_: str
    window_days: int
    total_checks: int
    phishing_blocked: int
    suspicious_warned: int
    safe_confirmed: int
    unique_attackers: int
    brands_protected: int
    campaigns_identified: int
    citizens_who_reported: int
    estimated_thb_loss_prevented: int
    estimated_thb_loss_prevented_note: str
    sustainability_pillars: dict
    generated_at: str


@router.get(
    "/impact",
    response_model=ImpactResponse,
    summary="Public social-impact metrics (no auth)",
    response_model_by_alias=True,
)
async def public_impact(
    window_days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> ImpactResponse:
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)

    # --- core counts ---
    label_counts = dict(
        (
            await session.execute(
                select(UrlCheck.label, func.count())
                .where(UrlCheck.checked_at >= since)
                .group_by(UrlCheck.label)
            )
        ).all()
    )
    blocked = int(label_counts.get(Label.phishing, 0))
    suspicious = int(label_counts.get(Label.suspicious, 0))
    safe = int(label_counts.get(Label.safe, 0))

    # --- distinct hosts that the system flagged (proxy for attackers) ---
    attackers = (
        await session.execute(
            select(func.count(func.distinct(UrlCheck.closest_domain)))
            .where(UrlCheck.checked_at >= since)
            .where(UrlCheck.label == Label.phishing)
            .where(UrlCheck.closest_domain.is_not(None))
        )
    ).scalar_one() or 0

    # --- brands explicitly being protected (watchlist size) ---
    brands = (
        await session.execute(select(func.count()).select_from(BrandWatch))
    ).scalar_one() or 0

    # --- campaign count in window ---
    campaigns = (
        await session.execute(
            select(func.count()).select_from(Campaign)
            .where(Campaign.last_seen >= since)
        )
    ).scalar_one() or 0

    # --- citizen feedback in window ---
    citizens = (
        await session.execute(
            select(func.count()).select_from(Feedback)
            .where(Feedback.created_at >= since)
        )
    ).scalar_one() or 0

    estimated_loss = blocked * THB_PER_PHISHING_BLOCKED

    return ImpactResponse(
        schema_="phish.impact.v1",
        window_days=window_days,
        total_checks=blocked + suspicious + safe,
        phishing_blocked=blocked,
        suspicious_warned=suspicious,
        safe_confirmed=safe,
        unique_attackers=int(attackers),
        brands_protected=int(brands),
        campaigns_identified=int(campaigns),
        citizens_who_reported=int(citizens),
        estimated_thb_loss_prevented=estimated_loss,
        estimated_thb_loss_prevented_note=(
            f"คำนวณจาก จำนวน URL ฟิชชิงที่ block × {THB_PER_PHISHING_BLOCKED:,} "
            "บาท (median per-incident loss จากรายงาน ETDA/ThaiCERT 2024-2025) "
            "— เป็นค่าโดยประมาณเพื่อสื่อสารผลกระทบ ไม่ใช่ค่าทางบัญชี"
        ),
        sustainability_pillars={
            "social": (
                "ปกป้องประชาชนกลุ่มเปราะบาง (ผู้สูงอายุ, ผู้ใช้ดิจิทัลครั้งแรก) "
                "จากการถูกหลอกขโมยข้อมูลและทรัพย์สิน ผ่านส่วนขยายเบราว์เซอร์, "
                "Citizen Report Portal และ Public Threat Feed ที่ทุกคนเข้าถึงได้ฟรี"
            ),
            "economic": (
                "ลดความเสียหายต่อระบบเศรษฐกิจดิจิทัลของไทย เช่น "
                "การโจมตีเว็บไซต์ราชการและธนาคาร โดยใช้ความเสียหายต่อ incident "
                "ตาม ETDA เป็นฐาน"
            ),
            "environmental": (
                "สถาปัตยกรรมที่ใช้ทรัพยากรน้อย: in-process cache, "
                "single-binary deploy, graceful degradation ทำให้รันบน VPS "
                "ราคาประหยัด/พลังงานต่ำได้, ไม่ต้องการ GPU"
            ),
            "openness": (
                "เปิด source ทั้งหมดภายใต้ Apache 2.0 + Public Threat Feed "
                "(STIX 2.1) + ดาต้าเซ็ตที่ commit ไว้ใน repo "
                "หน่วยงานใดก็ตามนำไป deploy/แก้ไข/ขยายผลได้"
            ),
        },
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    )
