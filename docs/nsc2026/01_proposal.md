# ข้อเสนอโครงการ — NSC 2026 หมวด 23 ระดับนักเรียน

**ชื่อโครงการ (ไทย):** ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานราชการและสถาบันการศึกษาไทย ด้วยการเรียนรู้ของเครื่องและกฎอ้างอิงที่โปร่งใส

**ชื่อโครงการ (อังกฤษ):** Thai Public-Sector Phishing URL Detection System using Machine Learning with a Transparent Rules Engine

---

## 1. สาระสำคัญของโครงการ (Executive Summary)

ระบบนี้คือแพลตฟอร์ม **end-to-end** สำหรับตรวจจับ URL ฟิชชิงที่เลียนแบบเว็บไซต์
หน่วยงานราชการไทย (`.go.th`) สถาบันการศึกษา (`.ac.th`) และธนาคาร/รัฐวิสาหกิจ
แบบ realtime ประกอบด้วย 5 ส่วนที่ทำงานร่วมกัน:

1. **ML pipeline** ที่ฝึก ensemble RandomForest + XGBoost บนชุด feature 42 ตัว
   (lexical, IDN/homoglyph, path-impersonation, WHOIS, TLS, whitelist, lexical patterns ใหม่)
   ได้ recall **100% (378/378)** บน Thai-targeting holdout
2. **FastAPI backend** ให้บริการ `/check`, public threat feed (JSON/CSV/STIX),
   brand watchlist + webhook (รองรับ LINE Notify), campaign clustering,
   domain reputation timeline, social-impact metrics และเนื้อหาให้ความรู้
3. **ส่วนขยายเบราว์เซอร์ (Manifest V3)** สำหรับ Chrome/Edge/Brave/Opera/Firefox
   แสดงหน้าเตือนเต็มจอก่อนเข้าเว็บฟิชชิง
4. **แดชบอร์ด React 11 หน้า** ที่ใช้บริหารระบบและ portal ให้ประชาชนแจ้งเว็บปลอม
   แบบไม่ต้อง login
5. **Heuristic Rules Engine** เลเยอร์ของกฎอ่านง่าย ทำงานเสริม ML —
   ทุก verdict บอกได้ว่ามีกฎใดบ้างที่ทำงาน เพิ่มความโปร่งใสและตรวจสอบได้

ระบบยังรองรับ **4 ความสามารถเสริม (v1.2.0):**
- **URL Unshortening** — แกะ short link (bit.ly, t.co, lin.ee ฯลฯ) อัตโนมัติก่อนส่ง feature extraction
- **LINE Messaging API Bot** — webhook `/api/v1/line/webhook` รับ URL จากแชท LINE ตอบกลับภาษาไทยพร้อม verdict
- **Content-based Fallback** — ดึง HTML ตรวจสัญญาณฟิชชิงเพิ่มเติมสำหรับ URL ที่อยู่ในโซนเทา (score 0.3–0.7)
- **Feedback-driven Auto-retrain** — export confirmed feedback จาก DB แล้ว trigger retrain อัตโนมัติ

**คำสำคัญ (Keywords):** ฟิชชิง · machine learning · ความปลอดภัยไซเบอร์ ·
หน่วยงานราชการไทย · IDN homograph · STIX · sustainable innovation ·
LINE Messaging API · Phishing Detection · Cybersecurity · Thai Government

---

## 2. หลักการและเหตุผล

สำนักงานพัฒนาธุรกรรมทางอิเล็กทรอนิกส์ (ETDA) รายงานว่าในปี 2567 มีการแจ้ง
เว็บไซต์ปลอม / SMS หลอกลวงที่อ้างชื่อหน่วยงานราชการมากกว่า **30,000 เคส**
สร้างความเสียหายเฉลี่ยกว่า **5,000–10,000 บาทต่อรายผู้เสียหาย** กลุ่ม
เป้าหมายหลักของผู้โจมตีคือ **ผู้สูงอายุ** และ **ประชาชนทั่วไปที่ไม่มีความรู้ทางเทคนิค**
ซึ่งไม่สามารถแยก URL จริงจาก URL ปลอมได้

เทคนิคที่ผู้โจมตีใช้มีหลายระดับ:

1. **TLD swap** — `obec.com` แทน `obec.go.th` (เปลี่ยน TLD จากของจริง)
2. **Typosquat** — `0bec.go.th` (พิมพ์ผิดเล็กน้อย)
3. **Subdomain spoof** — `obec.go.th.evil.com`
4. **IDN homograph** — `chulа.com` (ใช้ Cyrillic `а` แทน Latin `a`)
5. **Punycode** — `xn--obec-9bc.com` (encode IDN เป็น ASCII)
6. **Path-brand bait** — `random.cc/krungthai/login` (ใส่ชื่อแบรนด์ใน path)

ปัญหาคือ **ระบบป้องกันที่มีอยู่** (เช่น Google Safe Browsing, Microsoft SmartScreen)
ออกแบบมาเพื่อตลาดทั่วโลก ไม่ได้ระบุเว็บราชการ/การศึกษาไทยเป็นเป้าหมายโดยตรง
จึงพลาด URL ที่ปลอม `obec.go.th`, `chula.ac.th`, `paotang.go.th`,
`krungthai.com` ฯลฯ บ่อยครั้ง ระบบที่ได้รับการ "training มาเพื่อไทย" จึงจำเป็น

---

## 3. วัตถุประสงค์

1. **วัตถุประสงค์หลัก:** สร้างระบบตรวจจับ URL ฟิชชิงเฉพาะทางที่จับการปลอม
   แบรนด์ราชการ/การศึกษา/ธนาคารไทย ได้ recall ≥ 95% บนชุดข้อมูลทดสอบที่
   โมเดลไม่เคยเห็น (ปัจจุบันได้ **100%** บนชุด holdout 378 URL)
2. **วัตถุประสงค์รอง:**
   * เปิดให้ประชาชนทั่วไปและหน่วยงานเข้าถึงได้ฟรี ผ่านส่วนขยายเบราว์เซอร์
     และ public threat feed (no-auth)
   * สร้าง Citizen Report Portal ให้ประชาชนแจ้งเว็บปลอมโดยไม่ต้อง login
   * แจ้งเตือนหน่วยงานเมื่อมีการปลอมแบรนด์ของตน (Brand Watchlist + webhook)
   * เผยแพร่เนื้อหาให้ความรู้ประชาชนเกี่ยวกับฟิชชิงผ่าน `/api/v1/learn`
   * เปิด source ทั้งระบบภายใต้ Apache 2.0 เพื่อให้ขยายผลและคงอยู่ยาวนาน

---

## 4. ปัญหาหรือประโยชน์ที่เป็นเหตุผลให้ควรพัฒนาโปรแกรม

### ปัญหาที่ต้องการแก้

* คนไทยเสียเงินให้กลุ่ม phishing/scam ปีละหลายพันล้านบาท ตาม ETDA
  (2567) ส่วนใหญ่จาก URL ปลอมหน่วยงานราชการ
* ระบบป้องกัน global พลาด URL ปลอม Thai brand เพราะไม่มี whitelist ของไทย
  ภายในโมเดล
* การปลอมด้วยตัวอักษร Cyrillic / Punycode (`chulа.com`, `xn--rd-yia.com`)
  เป็นเทคนิคที่ระบบ rule-based แบบเก่าจับไม่ได้
* ประชาชนทั่วไป**ไม่มีช่องทางที่ใช้ง่าย** ในการตรวจ URL ก่อนกด

### ประโยชน์ที่ระบบนี้สร้าง (Triple bottom line)

| มิติ | ประโยชน์ที่วัดได้ |
|------|-------------------|
| **Social** | ปกป้องประชาชนกลุ่มเปราะบาง (ผู้สูงอายุ ครู นักเรียน) จากการตกเป็นเหยื่อ; portal ไม่ต้อง login เพื่อ accessibility สูงสุด |
| **Economic** | ทุก URL ฟิชชิงที่ block ได้ ลดความเสียหายเฉลี่ย ~7,800 บาท/case (median ETDA) — `/api/v1/impact` แสดงยอดสะสมแบบเรียลไทม์ |
| **Environmental** | สถาปัตยกรรม low-resource (in-process cache, no GPU, single-binary) รันบน VPS ราคาประหยัด/พลังงานต่ำได้ |
| **Open** | Apache 2.0 + Public Threat Feed (STIX 2.1) + ดาต้าเซ็ตที่ commit ใน repo — หน่วยงานอื่น deploy/ขยายผลได้ฟรี |

---

## 5. เป้าหมายและขอบเขตของโครงการ

### เป้าหมาย (Goals)

1. **ความแม่นยำ:** Recall ≥ 95% บน Thai-targeting holdout (✅ ทำได้ 100% บน 378 URL แล้ว)
2. **ความครอบคลุม:** รองรับเว็บราชการ/การศึกษา/ธนาคาร 500+ โดเมน (✅ ใส่ใน whitelist แล้ว)
3. **ความใช้งานได้จริง:** ส่วนขยายเบราว์เซอร์ติดตั้งได้ใน Chrome/Edge/Firefox (✅)
4. **ความยั่งยืน:** เปิด source, มีเอกสารครบ, มี CI/test 242 cases (✅)
5. **ผลกระทบทางสังคม:** มีหน้า portal ให้ประชาชนแจ้งเว็บปลอมไม่ต้อง login (✅)

### ขอบเขต (Scope)

| In-scope | Out-of-scope |
|----------|--------------|
| ตรวจฟิชชิงระดับ **URL** (เห็น string เท่านั้น) | ตรวจเนื้อหาในหน้าเว็บ (content scanner) |
| ตัวอักษรใน URL ทุก script (Latin, Cyrillic, Greek, Thai) | การตรวจ malware ในไฟล์ download |
| Phishing ของแบรนด์ไทย และ generic phishing เป็น cross-check | Spear-phishing email (ต้องตรวจเนื้อหาอีเมล) |
| Browser extension (MV3) + dashboard + API | ระบบโทรศัพท์/SMS gateway |

---

## 6. รายละเอียดของการพัฒนา

### 6.1 Story Board / ภาพประกอบ

```
   ผู้ใช้ปลายทาง                       หน่วยงานราชการ                    นักวิจัย / ชุมชน
        │                                    │                                  │
        ▼                                    ▼                                  ▼
  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────────────┐
  │ Extension   │  │ Citizen Report   │  │ Brand Watchlist │  │ Public Threat Feed     │
  │ MV3 (real-  │  │ Portal           │  │ + Webhook       │  │ /feed.json /feed.stix  │
  │ time check) │  │ (no login)       │  │ (LINE/Slack)    │  │ (no auth)              │
  └──────┬──────┘  └────────┬─────────┘  └────────┬────────┘  └───────────┬────────────┘
         │                  │                     │                       │
         └──────────────────┴─────────────────────┴───────────────────────┘
                                       │
                              ┌────────▼─────────┐
                              │ FastAPI Backend  │
                              │ /api/v1/check    │
                              │ + Rules Engine   │
                              │ + Campaign Cluster│
                              │ + Impact + Learn │
                              └────────┬─────────┘
                                       │
                              ┌────────▼─────────┐
                              │ ML Ensemble      │
                              │ RF + XGB         │
                              │ schema v1.5.0    │
                              │ 42 features      │
                              └──────────────────┘
```

### 6.2 เทคนิคและเทคโนโลยีที่ใช้

| ส่วน | เทคนิค / Algorithm |
|------|--------------------|
| ML model | RandomForest + XGBoost soft-voting ensemble + isotonic calibration |
| Feature extraction | Lexical 15 ตัว + IDN/Homoglyph 3 ตัว + Path-impersonation 4 ตัว + WHOIS 4 ตัว + TLS 3 ตัว + Whitelist 2 ตัว + Meta 2 ตัว + Lexical v1.4 4 ตัว + TLS/interaction v1.5 5 ตัว = **42 features** |
| IDN Defense | Punycode decode + Unicode confusable fold (TR36) + Levenshtein distance |
| Typosquat | Brand-label edit distance ≤ 3 + TLD-swap detection |
| Campaign clustering | Fingerprint = `brand|tld|path-shape` (digit → `#`, hex → `$hex`) |
| API | FastAPI + Pydantic v2 + SQLAlchemy async + slowapi (rate limit) + prometheus-client |
| Frontend | React 18 + Vite 5 + TailwindCSS + TanStack Query + Recharts |
| Extension | Manifest V3 service worker + chrome.webNavigation + warning interstitial |
| Database | PostgreSQL 16 (production) + SQLite (dev/demo) |
| Deploy | Docker Compose / Standalone Docker / Render Blueprint |

### 6.3 เครื่องมือที่ใช้ในการพัฒนา

| ประเภท | เครื่องมือ |
|--------|------------|
| ภาษา | Python 3.11, JavaScript (ES2022), JSX, HTML/CSS |
| ML library | scikit-learn 1.5, XGBoost 2.1, pandas, python-Levenshtein |
| Backend framework | FastAPI 0.115, uvicorn, SQLAlchemy 2.0 async |
| Frontend framework | React 18, Vite 5, TailwindCSS 3 |
| Testing | pytest 8.3, httpx 0.28 (TestClient) |
| CI/CD | GitHub Actions, Docker, ruff |
| IDE | VS Code (ทุกอย่างฟรี/ลิขสิทธิ์ถูกต้อง) |

> **ข้อมูลลิขสิทธิ์:** ซอฟต์แวร์ทั้งหมดที่ใช้พัฒนาเป็น open-source license ที่
> เข้ากันได้กับ Apache 2.0 — ดูรายการเต็มที่ `NOTICE` ใน repository

### 6.4 รายละเอียดโปรแกรมที่จะพัฒนา (Software Specification)

#### Input / Output
* **Input:** URL string (HTTP/HTTPS, ≤ 2048 chars) — ส่งเข้า `/api/v1/check`
* **Output:** JSON ที่มี `score` (0–1), `label` (safe/suspicious/phishing),
  `reason` (อธิบายภาษาไทย), `features` (42 ตัว), `rules.hits[]` (กฎที่ทำงาน),
  `closest_domain`, `edit_distance`, `checked_at`

#### Functional Specification (เลือกที่สำคัญ)
* `POST /api/v1/check` — ตรวจ URL เดียว latency p95 < 250 ms (รองรับ URL unshortening อัตโนมัติ)
* `POST /api/v1/check/batch` — สูงสุด 50 URLs/request
* `GET /api/v1/feed.{json,csv,stix}` — public feed (no auth)
* `GET /api/v1/impact` — social-impact metrics (no auth)
* `GET /api/v1/learn` — เนื้อหาให้ความรู้ (no auth)
* `POST /api/v1/feedback` — citizen report (no auth)
* `POST /api/v1/watchlist` — ลงทะเบียนแบรนด์เฝ้าระวัง (auth)
* `GET /api/v1/campaigns` — campaign cluster list (auth)
* `GET /api/v1/domain/{host}/history` — reputation timeline (auth)
* `POST /api/v1/line/webhook` — LINE Messaging API webhook (HMAC-SHA256 verified)

#### โครงสร้างซอฟต์แวร์ (Design)
```
phish_features/   ← shared package, ML pipeline และ backend ใช้ร่วมกัน
├── schema.py     ← single source of truth ของ 42 features + LOGIN_KEYWORDS + SUSPICIOUS_TLDS
├── lexical.py    ← computed-from-string features (เร็ว, deterministic)
├── whitelist.py  ← typosquat + brand-label edit distance
├── homoglyph.py  ← IDN decode + confusable fold
├── extractor.py  ← FeatureExtractor (orchestrator)
└── rules.py      ← Heuristic RulesEngine (transparency layer)

backend/app/
├── main.py + middleware.py     ← request-id, security headers, JSON log
├── ml/scorer.py                ← model + rules → final verdict
├── unshorten.py                ← async URL unshortener (18 providers, HEAD-only)
├── content_check.py            ← HTML content fallback for gray-zone URLs + SSRF protection
├── routers/                    ← 11 routers (check, stats, history, admin, feedback,
│                                  watchlist, campaigns, domain, feed, impact, learn, line_bot)
├── campaigns.py + notifier.py  ← clustering + webhook (LINE-compatible)
└── models.py                   ← 7 ORM tables (UrlCheck, Whitelist, Feedback,
                                   BrandWatch, WebhookDelivery, Campaign,
                                   ExternalFeedSource, FeedIngestionRecord)

ml_pipeline/
└── feedback_retrain.py         ← export confirmed feedback → trigger auto-retrain
```

### 6.5 ขอบเขตและข้อจำกัดของโปรแกรม

**จับได้:**
* Typosquat, TLD swap, subdomain spoof, IP host, @-trick
* IDN/Homoglyph (Cyrillic / Greek / Fullwidth / Thai digit substitution)
* Punycode spoofs (`xn--`)
* Path-brand bait kits
* Cheap-TLD low-effort kits

**จับได้เพิ่มเติม (v1.2.0):**
* URL shorteners — แกะ redirect chain ก่อน score (ENABLE_URL_UNSHORTENING=true)
* เว็บโซนเทาที่มี password field หรือ brand-in-title — ตรวจ HTML เพิ่ม (GRAY_ZONE_CONTENT_CHECK=true)

**จับไม่ได้ (out of scope):**
* Spear-phishing เนื้อหาอีเมล
* การโทรหลอก call-center
* Malware ในไฟล์ที่ดาวน์โหลด

---

## 7. ระยะเวลาดำเนินงาน (สำหรับการพัฒนาต่อ 3 เดือนตามกำหนด NSC)

| สัปดาห์ | กิจกรรม |
|---------|---------|
| 1–2 | Code review + เพิ่ม test coverage ให้ครบ 90% (ปัจจุบัน 242 tests) ✅ |
| 3–4 | ขยาย Thai-targeting seed corpus จาก 215 → 300 URLs จากแหล่ง ThaiCERT advisory |
| 5–6 | LINE Messaging API Bot + URL Unshortening + Content-based Fallback + Feedback Auto-retrain ✅ |
| 7–8 | เพิ่ม dashboard widget แสดง social-impact metrics แบบ public (เปิด iframe ใส่เว็บอื่นได้) |
| 9–10 | ทดสอบกับ pilot user (โรงเรียน 2 แห่ง, หน่วยงานราชการ 1 แห่ง) เก็บ feedback จริง |
| 11 | ปรับปรุงโมเดลตาม pilot feedback + retrain ด้วย feedback_retrain pipeline |
| 12 | เตรียมเอกสาร, video, poster สำหรับรอบนำเสนอ |

> **หมายเหตุ:** โครงการนี้พัฒนาต่อยอดจาก codebase ที่นักเรียนได้ทำมาก่อนล่วงหน้า
> เพื่อให้พร้อมส่งข้อเสนอ — ระหว่าง 3 เดือนหลังได้ทุน จะมุ่งเน้นการขยายผลและ
> การทดสอบกับ pilot user จริง

---

## 8. บรรณานุกรม (Bibliography)

1. ETDA, *รายงานสถานการณ์ภัยคุกคามทางไซเบอร์ของประเทศไทย ปี 2567*
   สำนักงานพัฒนาธุรกรรมทางอิเล็กทรอนิกส์, 2568. URL: <https://www.etda.or.th>
2. Unicode Consortium, *Unicode Technical Report #36: Unicode Security Considerations*,
   2024. URL: <https://www.unicode.org/reports/tr36/>
3. OASIS, *STIX™ Version 2.1 Specification*, 2021.
   URL: <https://docs.oasis-open.org/cti/stix/v2.1/>
4. T. Chen and C. Guestrin, *XGBoost: A Scalable Tree Boosting System*,
   KDD '16, 2016. DOI: 10.1145/2939672.2939785.
5. L. Breiman, *Random Forests*, Machine Learning 45 (1), pp. 5–32, 2001.
   DOI: 10.1023/A:1010933404324.
6. OpenPhish, *Live Phishing URL Feed*. URL: <https://openphish.com/>
7. URLhaus by abuse.ch, *Recent URL API*. URL: <https://urlhaus-api.abuse.ch/>
8. ThaiCERT, *Cybersecurity Advisories*. URL: <https://www.thaicert.or.th>

---

## 9. ประวัติและผลงานของผู้พัฒนา

### หัวหน้าโครงการ: REENX8 (asdawesdzd22@gmail.com)

| รายการ | รายละเอียด |
|--------|-----------|
| ระดับชั้น / สถาบัน | _________________________________ |
| ผลงานวิชาการ / โครงการที่เคยทำ | (ระบุไม่เกิน 5 รายการ — เน้นด้านวิทยาศาสตร์/เทคโนโลยี/computer programming) |
| ทักษะที่เกี่ยวข้อง | Python, JavaScript, Machine Learning, FastAPI, React, Docker (ปรับให้ตรงกับจริง) |
| ความสนใจ / แรงบันดาลใจ | (เล่าสั้น ๆ ทำไมถึงเลือกหัวข้อนี้) |

### ผู้ร่วมพัฒนา (ถ้ามี)

ทำซ้ำตารางด้านบนสำหรับผู้ร่วมพัฒนาคนอื่น
