"""GET /api/v1/learn -- Thai-language phishing-awareness content.

This is the educational layer that turns the detector into a long-term
behavioural intervention, not just a guard rail. The content is bundled
into the API (not a separate CMS) so a no-cost deployment ships the
entire programme without an extra service.

The content is short, evidence-based, in Thai, and structured as
machine-readable cards so a chatbot / LINE bot / dashboard widget /
extension popup can render any subset without parsing prose.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class LearningCard(BaseModel):
    id: str
    title: str
    audience: str          # general | elderly | student | public-servant
    duration_minutes: int
    body_th: str
    actions_th: list[str]
    sources: list[str]


_CARDS: list[LearningCard] = [
    LearningCard(
        id="basics-001",
        title="ฟิชชิง (Phishing) คืออะไร — อธิบายแบบสั้น",
        audience="general",
        duration_minutes=2,
        body_th=(
            "ฟิชชิงคือการ 'ตกปลา' ข้อมูลด้วย URL ปลอม ผู้โจมตีจะส่ง SMS, อีเมล "
            "หรือข้อความบน LINE ที่มีลิงก์หน้าตาเหมือนของหน่วยงานจริง (เช่น สรรพากร, "
            "ไปรษณีย์, ธนาคาร) เพื่อให้คุณกรอกรหัสผ่านหรือเลขบัตรประชาชน "
            "ลิงก์ที่ถูกออกแบบมาดีจะมีตัวอักษรหน้าตาเหมือนของจริงเกือบทุกตัว "
            "ต่างแค่ตัวอักษร 1-2 ตัวหรือ TLD (.go.th กับ .com)"
        ),
        actions_th=[
            "ตรวจ TLD ของ URL ก่อนกด — เว็บราชการต้องลงท้ายด้วย .go.th เท่านั้น",
            "ห้ามกรอกรหัสผ่านจากลิงก์ใน SMS หรือ LINE — เปิดเว็บผ่านการพิมพ์เองเสมอ",
            "ถ้าไม่แน่ใจ ใช้ระบบนี้ตรวจ URL ก่อน (หน้าแจ้งเว็บฟิชชิง)",
        ],
        sources=["https://www.etda.or.th", "https://www.thaicert.or.th"],
    ),
    LearningCard(
        id="elderly-001",
        title="กฎทอง 3 ข้อสำหรับผู้สูงอายุ",
        audience="elderly",
        duration_minutes=1,
        body_th=(
            "1) หน่วยงานราชการของไทยจะไม่ส่ง SMS หรือ LINE เรียกเก็บเงินด่วน "
            "2) ตำรวจ ไม่ขอ OTP หรือเลขหลังบัตรเดบิตทางโทรศัพท์ "
            "3) ก่อนกดลิงก์ใด ๆ ให้โทรหาลูกหลานหรือ 1212 (ศูนย์ ETDA) ก่อน"
        ),
        actions_th=[
            "บันทึก 1212 ไว้ในโทรศัพท์ — เป็นสายด่วน ETDA แจ้งเว็บปลอม",
            "ติดตั้งส่วนขยายเบราว์เซอร์ของระบบนี้ จะมีหน้าเตือนสีแดงโผล่ก่อนเข้าเว็บปลอม",
        ],
        sources=["https://www.etda.or.th/th/Useful-Resource"],
    ),
    LearningCard(
        id="signals-001",
        title="5 สัญญาณว่า URL ในมือคุณน่าสงสัย",
        audience="general",
        duration_minutes=3,
        body_th=(
            "1) ตัวอักษรในชื่อโดเมนใช้หลายภาษาผสม (Latin + Cyrillic) "
            "2) มี '@' ตรงกลาง URL (ซ่อนปลายทางจริง) "
            "3) ใช้ TLD ราคาถูก (.cc, .xyz, .icu, .top) ปลอมเป็นเว็บราชการ "
            "4) เร่งให้รีบทำ ('คลิกใน 24 ชั่วโมง', 'บัญชีจะถูกระงับ') "
            "5) ขอเลขบัตรประชาชน, รหัสผ่าน, หรือ OTP ผ่านฟอร์มในเว็บที่ส่งมาทางลิงก์"
        ),
        actions_th=[
            "ถ้าเจอแม้แค่ 1 ใน 5 ข้อ — หยุดทันที, ไปแจ้งที่ /report บนระบบนี้",
        ],
        sources=[
            "https://www.thaicert.or.th",
            "Unicode TR36 (IDN Homograph)",
        ],
    ),
    LearningCard(
        id="reporting-001",
        title="แจ้งเว็บปลอม — ทำได้ที่ไหน",
        audience="general",
        duration_minutes=2,
        body_th=(
            "แจ้งได้ 3 ช่องทาง 1) Citizen Report Portal ของระบบนี้ (ไม่ต้อง login) "
            "2) ETDA: สายด่วน 1212 หรือ https://www.etda.or.th "
            "3) ตำรวจไซเบอร์: 1441 หรือ www.thaipoliceonline.com "
            "เมื่อแจ้งให้ส่ง URL ที่พบ พร้อมที่มา (SMS / LINE / อีเมล) และเวลาที่ได้รับ"
        ),
        actions_th=[
            "Screenshot ข้อความหรือ URL ก่อนปิด — เป็นหลักฐานที่สำคัญที่สุด",
            "ห้ามคลิก URL ในข้อความ — copy เป็น text แล้วเอามาตรวจที่ระบบนี้แทน",
        ],
        sources=[
            "https://www.etda.or.th",
            "https://www.thaipoliceonline.com",
        ],
    ),
    LearningCard(
        id="for-agencies-001",
        title="สำหรับหน่วยงานราชการ / สถาบันการศึกษา",
        audience="public-servant",
        duration_minutes=4,
        body_th=(
            "ระบบนี้รองรับการเฝ้าระวังแบรนด์ของคุณโดยตรง — ใส่ชื่อหน่วยงาน "
            "ลงใน Brand Watchlist พร้อม webhook ของ SOC / SOAR / LINE Notify "
            "เมื่อมี URL ที่ปลอมเป็นหน่วยงานของคุณถูกตรวจจาก browser extension "
            "ทั่วประเทศ ระบบจะส่งข้อความแจ้งเตือนภายในไม่กี่วินาที "
            "เพื่อให้ทีมคุณ takedown หรือออกแถลงการณ์ได้ก่อนความเสียหายจะลุกลาม"
        ),
        actions_th=[
            "ดูตัวอย่างการตั้งค่าที่หน้า 'เฝ้าระวังแบรนด์' บน dashboard",
            "ใช้ /api/v1/feed.stix ส่งต่อเข้า SIEM / TAXII consumer ของหน่วยงาน",
            "ขอ Public Threat Feed (no-auth) ใส่ใน threat-intel pipeline ภายในได้ฟรี",
        ],
        sources=["docs/nsc2026/full_report.md (ระบบนี้)"],
    ),
]


class LearnListResponse(BaseModel):
    count: int
    cards: list[LearningCard]


@router.get(
    "/learn",
    response_model=LearnListResponse,
    summary="Thai phishing-awareness content (no auth)",
)
async def list_cards(
    audience: str | None = Query(default=None, max_length=32),
) -> LearnListResponse:
    cards = _CARDS
    if audience:
        cards = [c for c in cards if c.audience == audience or audience == "all"]
    return LearnListResponse(count=len(cards), cards=cards)


@router.get(
    "/learn/{card_id}",
    response_model=LearningCard,
    summary="One awareness card by id",
)
async def get_card(card_id: str) -> LearningCard:
    from fastapi import HTTPException
    for c in _CARDS:
        if c.id == card_id:
            return c
    raise HTTPException(404, f"card '{card_id}' not found")
