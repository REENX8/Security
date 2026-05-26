# Rubric Mapping — เกณฑ์การให้คะแนน NSC 2026 → ส่วนของระบบ

> เอกสารนี้ใช้ภายในทีมเพื่อตรวจว่าทุกเกณฑ์ของคณะกรรมการ มีหลักฐานใน
> ระบบจริงรองรับ และมีจุดเด่นที่จะหยิบเล่าให้กรรมการเห็น

---

## รอบที่ 1 — ข้อเสนอโครงการ (100 คะแนน)

### 1. ความสมบูรณ์ของข้อเสนอ (20)

✅ `docs/nsc2026/01_proposal.md` ครอบคลุมทุกหัวข้อที่ booklet กำหนด:
สาระสำคัญ · หลักการ · วัตถุประสงค์ · ปัญหา/ประโยชน์ · เป้าหมาย/ขอบเขต ·
Story Board · เทคนิค · เครื่องมือ · Spec · ขอบเขต · บรรณานุกรม 8 รายการ ·
ประวัติผู้พัฒนา

### 2. ความยากง่ายในการพัฒนา (20)

✅ **เทคนิคที่ซับซ้อนและซ้อนกันหลายชั้น:**

| ชั้น | สิ่งที่ทำ | หลักฐาน |
|------|-----------|----------|
| Feature Engineering | 37 features หลายกลุ่ม + ออกแบบใหม่ schema v1.4.0 | `phish_features/schema.py`, `extractor.py` |
| IDN Defense | Punycode decode + Unicode confusable fold + Levenshtein | `phish_features/homoglyph.py` |
| ML Ensemble | RF + XGB voting + Isotonic Calibration + 5-fold CV | `ml_pipeline/train.py` |
| Rules Engine | declarative rule system + pin priority + clamping | `phish_features/rules.py` |
| Backend | async FastAPI + 11 routers + middleware stack + 5 ORM tables | `backend/app/` |
| Frontend | React 18 + 11 pages + TanStack Query + Tailwind | `dashboard/src/` |
| Extension | Manifest V3 + service worker + warning interstitial + bypass | `extension/` |
| DevOps | Docker, Compose, Render Blueprint, GitHub Actions CI gate | `Dockerfile`, `render.yaml`, `.github/workflows/ci.yml` |

### 3. ความคิดสร้างสรรค์ (20)

✅ **5 ส่วนใหม่ที่ไม่ใช่ของเดิมและไม่ใช่ทำซ้ำ:**

* **Heuristic Rules Engine ที่โปร่งใส** — ผสาน ML + rules ด้วย pin priority,
  ทุก verdict บอก rule_id ที่ทำงาน → audit ได้, override โดยไม่ retrain
* **Brand Watchlist + LINE Notify integration** — ส่ง alert เป็นภาษาไทย
  รูปแบบ LINE Notify โดยอัตโนมัติ (ตรวจ host แล้ว switch format)
* **Public Threat Feed STIX 2.1** — TAXII-compatible indicators, no auth,
  cache 60s
* **Campaign Clustering** — fingerprint = brand|tld|path-shape (digit → #,
  hex → $hex)
* **Citizen Report Portal** — anonymous, no login, Thai-first UI
* **/api/v1/impact** — quantified social impact (median × blocked count)
* **/api/v1/learn** — bundled awareness content (4 audience tiers)

### 4. ประโยชน์ใช้งาน (25) ← **highest weight**

✅ **กลุ่มเป้าหมายชัดเจน 6 กลุ่ม** + **ใช้ได้จริงตอนนี้:**

| กลุ่ม | ประโยชน์ที่ได้ |
|-------|----------------|
| ประชาชนทั่วไป | extension ฟรี + portal no-login |
| ผู้สูงอายุ | หน้าเตือนเต็มจอ ไม่ต้อง config |
| ครู/อาจารย์ | content `/learn` ใช้สอนได้ |
| ฝ่าย IT หน่วยงาน | Brand Watchlist + LINE alert |
| นักวิจัย | STIX feed → SIEM |
| SOC | dashboard 11 หน้า + metrics |

**ผลกระทบที่ quantify ได้:** `/api/v1/impact` คำนวณ ฿7,800 × blocked count
(median ETDA 2024-25) เป็น public-facing JSON ที่ใครก็เรียกได้

**ขยายผลได้:** Apache 2.0 + ดาต้าเซ็ตเปิดใน repo → หน่วยงานใดก็ตาม fork
+ deploy + ปรับ whitelist ของตนเองได้

### 5. ความน่าจะพัฒนาได้เสร็จ (15)

✅ **ระบบทำงานได้แล้ว ณ ตอนส่งข้อเสนอ:**

* 206 automated tests ผ่านทั้งหมด
* CI gate Thai recall ≥ 0.85 → ปัจจุบัน 100% (66/66) (PASS)
* Docker image build PASS
* Dashboard build PASS
* Extension package PASS
* Render Blueprint deployed already

3 เดือนถัดไปจะเน้น **ขยายผล** (LINE bot, pilot user, retrain ด้วย live
telemetry) ไม่ใช่ "เริ่มสร้าง" ความเสี่ยงจึงต่ำมาก

---

## รอบที่ 2 — นำเสนอผลงาน (100 คะแนน)

### รายงาน + ติดตั้งโปรแกรม (25)

✅ `docs/nsc2026/02_full_report.md` ครอบคลุมทุกหัวข้อ booklet กำหนด
✅ `04_installation_guide.md` มี 9 ส่วน รวม Docker, Python, Dashboard,
Extension, Train, Deploy, ตรวจสอบ, Troubleshooting
✅ การติดตั้งสามารถทำตามขั้นตอนได้จริง (verified ในเครื่อง dev)

### Look & Feel (15)

✅ **Dashboard 11 หน้า**: dark theme, Tailwind, responsive, accessibility
ตามแนวทาง shadcn
✅ **Extension**: badge สี + popup สวยงาม + warning interstitial เต็มจอ
✅ **API docs ที่ `/docs`**: OpenAPI/Swagger UI สวย ลองได้

### Technique (15)

✅ ดูข้อ "ความยากง่ายในการพัฒนา" ของรอบ 1 — เทคนิคที่ใช้ละเอียดและซ้อนกัน

### Creativity (20)

✅ 5+ ส่วนใหม่ที่ไม่ใช่ของเดิม (ดู rubric 3 ของรอบ 1)

### Economic + Social Impact (20)

✅ Triple bottom line + Open pillar (4 pillars in `/api/v1/impact`)
✅ Quantified: ฿7,800/block × N → social impact metric เรียลไทม์
✅ Citizen Portal accessibility-first

### Presentation (5)

ขึ้นกับการพูดของทีมในวันนั้น — ใช้สคริปต์ `08_video_script.md` ซ้อมจนคล่อง

---

## รอบที่ 3 — ชิงชนะเลิศ (100 คะแนน)

### Look & Feel (20)

✅ extension warning page + dashboard + Swagger UI

### Technique (20)

✅ 37-feature schema + IDN defense + Rules Engine + Campaign clustering + External Feed Ingestion

### Creativity (25) ← **highest weight**

✅ Open Threat Feed STIX 2.1 (เทียบกับ commercial threat intel แพง ๆ)
✅ LINE Notify integration ที่ออกแบบมาสำหรับสังคมไทยโดยตรง
✅ Citizen Portal no-login + bundled `/learn` content

### Economic + Social Impact (25) ← **highest weight**

✅ ป้องกันความเสียหายที่ ETDA วัดแล้วได้ปีละหลายพันล้าน
✅ เป้าหมายชัด: ผู้สูงอายุ, ครู, หน่วยงานราชการ
✅ Open source + STIX feed → ขยายผลได้ฟรี

### Presentation (10)

7-minute video script เน้นจุดเด่น (`08_video_script.md`)

---

## สรุปจุดที่ทีมต้องเตรียมเพิ่มก่อนส่ง

1. **กรอกข้อมูลส่วนตัว** ใน `00_cover_proposal.md`, `02_full_report.md`,
   `03_summary_form.md`, `06_disclaimer.txt`
2. **ลายเซ็นอาจารย์ที่ปรึกษา + หัวหน้าสถาบัน** ในหน้าปก
3. **แปลง .md → .docx/.pdf** ด้วย pandoc:
   ```bash
   pandoc docs/nsc2026/01_proposal.md -o proposal.docx
   pandoc docs/nsc2026/02_full_report.md -o full_report.docx
   pandoc docs/nsc2026/03_summary_form.md -o 28p23cXXXX.pdf
   ```
4. **โปสเตอร์ A1**: ออกแบบใน Canva ตาม `07_poster.md`
5. **คลิป 7 นาที**: บันทึกด้วย OBS ตามสคริปต์ `08_video_script.md`
6. **ภาพทีม**: ถ่ายในชุดสุภาพ
7. **Demo URL**: deploy backend + dashboard ที่ public URL พร้อมให้กรรมการ ลองได้
