# โปสเตอร์ A1 (594 × 841 mm, แนวตั้ง) — เนื้อหาและ Layout

> ใช้ออกแบบใน Canva / Figma / PowerPoint แล้ว export เป็น PDF ส่ง
> Font แนะนำ: TH Sarabun New (Thai), Inter (English) · จุดสีหลัก: #ef4444 (แดง), #3b82f6 (น้ำเงิน), #16a34a (เขียว)
> ทุก section ต้องดูได้ในระยะ 2 เมตรจากผู้เดินผ่าน

---

## Header (1/8 of poster)

```
🛡️  ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย
    Thai Public-Sector Phishing URL Detection System
    (ML + Transparent Rules Engine + Open Threat Feed)

NSC 2026 · หมวด 23 · ระดับนักเรียน
ทีมพัฒนา: ___________ · อาจารย์ที่ปรึกษา: ___________ · สถาบัน: ___________
```

---

## Section 1: ปัญหา (1/8) — ใช้รูป info-graphic

```
30,000+ เคส/ปี  ❘  ฿5,000-10,000  ❘  ผู้สูงอายุ = เหยื่อหลัก
URL ปลอม         ความเสียหาย      
หน่วยงานราชการ   ต่อรายผู้เสียหาย   

ระบบ global พลาด — เพราะไม่มี whitelist ของไทย
```

---

## Section 2: สิ่งที่ทำ (2/8) — ใช้ architecture diagram

```
                ┌──────────────────────────────────────┐
ประชาชน        │      Citizen Report Portal           │
นักเรียน  ───→ │      Browser Extension MV3           │
ผู้สูงอายุ      │      (Chrome/Edge/Firefox/Brave)     │
                └─────────────┬────────────────────────┘
                              │
                ┌─────────────▼────────────────────────┐
หน่วยงาน  ───→ │      FastAPI Backend                 │
ราชการ         │   /check  /watchlist  /feed.stix     │
                │   /campaigns  /domain  /impact       │
                │   /learn  /report                    │ ←── นักวิจัย
                └─────────────┬────────────────────────┘    Open Source
                              │
                ┌─────────────▼────────────────────────┐
                │   ML Ensemble + Rules Engine         │
                │   schema v1.4.0 · 37 features        │
                │   RF + XGB + Isotonic Calibration    │
                └──────────────────────────────────────┘
```

---

## Section 3: ความแม่นยำ (1/8) — ใช้ตัวเลขใหญ่ๆ

```
┌──────────────────────────────────────────┐
│        Thai-targeting holdout            │
│                                          │
│              100% recall                 │   ← ตัวใหญ่สุด สีเขียว
│              (66 / 66 URL)               │
│                                          │
│   Generic holdout: 98.9% (89/90 URL)    │
│                                          │
│       CI gate ≥ 0.85 → PASS              │
│       206 automated tests → PASS         │
└──────────────────────────────────────────┘
```

---

## Section 4: เทคนิคที่ใช้ (1/8) — bullet 4 อย่าง

```
✦ ML Ensemble:    RandomForest + XGBoost + Isotonic Calibration
                  on 37 deterministic features

✦ IDN Defense:    decode Punycode → fold Unicode confusables
                  จับ chulа.com (Cyrillic) ได้เป็น distance 0

✦ Schema v1.4.0:  เพิ่ม 4 features ล่าสุด
                  num_login_keywords · query_param_count
                  path_entropy · host_token_count

✦ Rules Engine:   declarative rules โปร่งใส
                  ทุก verdict แสดง rule_id ที่ทำงาน
```

---

## Section 5: Sustainability Pillars (1/8) — 2×2 grid

```
┌─────────────────────────┬─────────────────────────┐
│ 👥  SOCIAL              │ 💰  ECONOMIC            │
│ Citizen portal no-login │ /api/v1/impact          │
│ Browser ext for elderly │ ฿7,800 × URL blocked    │
│ Accessibility-first UI  │ (ETDA median 2024-25)   │
├─────────────────────────┼─────────────────────────┤
│ 🌱  ENVIRONMENTAL       │ 🔓  OPEN                │
│ No GPU, low-resource    │ Apache 2.0 license      │
│ Single-binary deploy    │ STIX 2.1 public feed    │
│ Run on solar-VPS        │ Dataset in repo         │
└─────────────────────────┴─────────────────────────┘
```

---

## Section 6: Use Cases (1/8) — รูปคน 3 กลุ่ม

```
👵 ผู้สูงอายุ            🏛️ หน่วยงานราชการ        🔬 ชุมชน Security
- ติด ext ครั้งเดียว     - ลงทะเบียน watchlist     - ดึง STIX feed
- เห็นหน้าแดง=หยุด        - LINE Notify alert       - เอาเข้า SIEM
- พิมพ์ใน /report ก็ได้   - ดู campaigns        - ส่ง feedback
```

---

## Section 7: Demo / QR (1/8)

```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   QR: Live demo │  │   QR: GitHub   │  │   QR: คลิป     │
│   /check + UI   │  │   source code  │  │   นำเสนอ 7 นาที│
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## Footer

```
ได้รับทุนสนับสนุนจาก สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ
NSC 2026 — The 28th National Software Contest · Sustainable Innovation
```
