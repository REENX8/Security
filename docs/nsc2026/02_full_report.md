# รายงานฉบับสมบูรณ์ — NSC 2026 หมวด 23 ระดับนักเรียน

> สำหรับใช้ส่งในรอบนำเสนอผลงาน — ตามรูปแบบ NSC 2026 Booklet หน้า 29–30

---

## หน้าปก (Cover)

ตามตัวอย่าง NSC 2026 Booklet หน้า 43:

<center>

**รหัสโครงการ:** _______________

# (ชื่อโครงการภาษาไทย)
### *(ชื่อโครงการภาษาอังกฤษ)*
หมวด 23 โปรแกรมเพื่อการประยุกต์ใช้งาน · ระดับนักเรียน

</center>

**รายงานฉบับสมบูรณ์**
เสนอต่อ
*สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ
กระทรวงการอุดมศึกษา วิทยาศาสตร์ วิจัยและนวัตกรรม*

ได้รับทุนอุดหนุนโครงการวิจัย พัฒนาและวิศวกรรม
โครงการแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28
ประจำปีงบประมาณ 2569

**โดย:** ____________ (ผู้พัฒนา) · ____________ (อาจารย์ที่ปรึกษา) · ____________ (สถาบัน, จังหวัด)

---

## กิตติกรรมประกาศ (Acknowledgement)

ขอขอบพระคุณ **สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ (สวทช.)**
ที่ได้ให้การสนับสนุนทุนแก่ "โครงการระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงาน
ราชการและสถาบันการศึกษาไทย" ภายใต้ "การแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์
แห่งประเทศไทย ครั้งที่ 28 (NSC 2026)" ทำให้โครงการนี้สำเร็จลุล่วงได้

ขอขอบพระคุณ ___________________ อาจารย์ที่ปรึกษา ที่ให้คำแนะนำตลอด
การพัฒนาโครงการ และ ___________________ หัวหน้าสถาบัน ที่ให้การสนับสนุน

---

## บทคัดย่อ (Abstract)

### ภาษาไทย

ปัจจุบันประชาชนไทยตกเป็นเหยื่อของเว็บไซต์ฟิชชิงที่เลียนแบบหน่วยงานราชการ
สถาบันการศึกษา และธนาคาร เป็นจำนวนหลายหมื่นเคสต่อปี โดยมีความเสียหายเฉลี่ย
ต่อรายผู้เสียหาย 5,000–10,000 บาท ระบบป้องกัน global ที่มีอยู่ พลาด URL ปลอม
ของแบรนด์ไทยจำนวนมากเพราะไม่มี whitelist และ training data เฉพาะของไทย

โครงการนี้นำเสนอ **แพลตฟอร์มตรวจจับ URL ฟิชชิงเฉพาะทาง** สำหรับเป้าหมาย
ที่เป็นแบรนด์ไทย ประกอบด้วย (1) ML ensemble RandomForest + XGBoost บน
37 features รวมถึง IDN/Homoglyph, Path-impersonation features และ
lexical patterns ใหม่ใน schema v1.4.0 (2) Heuristic Rules Engine เพื่อความ
โปร่งใสและตรวจสอบได้ (3) Brand Watchlist + Webhook (รองรับ LINE Notify)
สำหรับแจ้งเตือนหน่วยงาน (4) Campaign Clustering เพื่อจัดกลุ่มฟิชชิงจาก kit
เดียวกัน (5) Public Threat Feed (JSON/CSV/STIX 2.1) แชร์เป็นสาธารณะ
ไม่ต้อง API key และ (6) Citizen Report Portal ให้ประชาชนแจ้งเว็บปลอมโดย
ไม่ต้อง login

ผลการทดสอบบนชุดข้อมูล Thai-targeting holdout ที่โมเดลไม่เคยเห็น (66 URL)
ได้ recall **100% (66/66)** ที่ threshold ≥ 0.7
และผ่าน CI gate ขั้นต่ำ 0.85 ระบบนี้เปิดเป็น open source ภายใต้ Apache 2.0
และพร้อมให้หน่วยงานต่าง ๆ นำไปใช้งานหรือต่อยอดได้ทันที

**คำสำคัญ:** ฟิชชิง, machine learning, IDN homograph, STIX, Sustainable Innovation,
หน่วยงานราชการไทย, ธนาคาร, ผู้สูงอายุ

### English

Thai citizens fall victim to phishing websites impersonating government
agencies, educational institutions and banks at the scale of tens of
thousands of incidents per year, with a median loss of THB 5,000–10,000
per victim. Existing global protection systems miss many Thai-brand
phishing URLs because they lack a Thai whitelist and Thai-specific
training data.

This project presents a **specialised phishing-URL detection platform**
targeting Thai brands, consisting of (1) a RandomForest + XGBoost
ensemble on 37 features including IDN/Homoglyph, Path-impersonation
and new lexical pattern features at schema v1.4.0, (2) a Heuristic Rules
Engine for transparency and auditability, (3) Brand Watchlist + Webhook
(LINE Notify compatible) for agency alerting, (4) Campaign Clustering
to group phishing URLs from the same kit, (5) Public Threat Feed
(JSON/CSV/STIX 2.1) shared with no API key, and (6) a Citizen Report
Portal allowing the public to report suspicious URLs without login.

On the Thai-targeting holdout (66 URLs the model never sees during
training), the system achieves **100% recall (66/66)** at the
phishing threshold and clears the CI gate of 0.85. The system is
open-sourced under Apache 2.0 and is ready for agencies to adopt or extend.

**Keywords:** phishing, machine learning, IDN homograph, STIX,
sustainable innovation, Thai government, banking, elderly users

---

## บทนำ

(เนื้อหาเหมือนกับข้อเสนอโครงการ ข้อ 2-4 แต่เขียนเป็น narrative เล่าเรื่องว่า
ทำไมต้องทำ → ทำอะไร → ผลลัพธ์เป็นอย่างไร)

ตามข้อมูลของ ETDA และ ThaiCERT ในปี 2567 มีการแจ้งเว็บปลอม / SMS หลอก
ที่อ้างชื่อหน่วยงานราชการมากกว่า 30,000 เคส โดยส่วนใหญ่เป็นการเลียนแบบ
brand ราชการที่ประชาชนไว้ใจ — สรรพากร, ไปรษณีย์ไทย, ETDA, ธนาคารออมสิน,
ธนาคารกรุงไทย, ฯลฯ ผู้เสียหายส่วนใหญ่เป็นผู้สูงอายุและประชาชนที่ไม่มีความรู้
ทางเทคนิคในการแยก URL จริงจาก URL ปลอม

ระบบที่ออกแบบโดยตรงสำหรับเป้าหมายนี้ต้องการ:

1. **Whitelist ของ Thai brand** ที่ครอบคลุม → ใช้ 500+ โดเมน
2. **Feature ที่จับการปลอมในระดับ URL string ได้** → 37 features ที่ออกแบบเอง (schema v1.4.0)
3. **โมเดลที่ฝึกบน Thai-specific data** → curated seed corpus 215 URL
4. **ระบบที่โปร่งใส** → Rules Engine แสดง rule_id ที่ทำงาน
5. **ช่องทางใช้งานที่ accessible** → extension + portal ฟรี ไม่ต้อง login

---

## สารบัญ

```
1. บทคัดย่อ
2. บทนำ
3. วัตถุประสงค์และเป้าหมาย
4. รายละเอียดของการพัฒนา
   4.1 Story Board
   4.2 ทฤษฎี / Algorithm / เทคโนโลยี
   4.3 เครื่องมือที่ใช้
   4.4 Software Specification
   4.5 ขอบเขตและข้อจำกัด
   4.6 อุปกรณ์ (ถ้ามี)
5. กลุ่มผู้ใช้โปรแกรม
6. ผลการทดสอบ
7. ปัญหาและอุปสรรค
8. แนวทางการพัฒนาต่อ
9. ข้อสรุปและข้อเสนอแนะ
10. เอกสารอ้างอิง
11. สถานที่ติดต่อ
12. ภาคผนวก: คู่มือติดตั้ง · คู่มือใช้งาน · Disclaimer · โปสเตอร์
```

---

## วัตถุประสงค์และเป้าหมาย

### วัตถุประสงค์

1. **วัตถุประสงค์หลัก** — สร้างระบบตรวจจับ URL ฟิชชิงเฉพาะทางที่จับการปลอม
   แบรนด์ราชการ/การศึกษา/ธนาคารไทย ได้ recall ≥ 95% บนชุดข้อมูลทดสอบที่
   โมเดลไม่เคยเห็น (ปัจจุบันได้ **100% (66/66)** บน Thai-targeting holdout)
2. **วัตถุประสงค์รอง**
   * เปิดให้ประชาชนและหน่วยงานเข้าถึงได้ฟรี ผ่านส่วนขยายเบราว์เซอร์และ public
     threat feed (no-auth)
   * สร้าง Citizen Report Portal ให้ประชาชนแจ้งเว็บปลอมโดยไม่ต้อง login
   * แจ้งเตือนหน่วยงานเมื่อมีการปลอมแบรนด์ของตน (Brand Watchlist + webhook
     รองรับ LINE Notify / Slack)
   * เผยแพร่เนื้อหาให้ความรู้ประชาชนเกี่ยวกับฟิชชิงผ่าน `/api/v1/learn`
   * เปิด source ทั้งระบบภายใต้ Apache 2.0 เพื่อให้ขยายผลและคงอยู่ยาวนาน

### เป้าหมายเชิงปริมาณ (Goals)

| เป้าหมาย | ตัวชี้วัด | สถานะปัจจุบัน |
|----------|-----------|-----------------|
| ความแม่นยำ | Thai-targeting recall ≥ 95% | ✅ 100% (66/66) |
| ความครอบคลุม | Whitelist ราชการ/การศึกษา/ธนาคารไทย ≥ 500 โดเมน | ✅ 500+ โดเมน |
| ความใช้งานได้จริง | Extension รองรับ Chrome/Edge/Firefox/Brave/Opera | ✅ MV3 ปล่อยใช้ได้ |
| ความยั่งยืนของโค้ด | Test coverage + CI gate | ✅ 206 tests, recall ≥ 0.85 gate |
| ผลกระทบทางสังคม | Portal แจ้งฟิชชิงไม่ต้อง login | ✅ `/report` พร้อมใช้งาน |
| Latency | p95 ตรวจ 1 URL ≤ 250 ms | ✅ ~30 ms CPU inference |

---

## รายละเอียดของการพัฒนา

### 4.1 Story Board

ระบบเชื่อมต่อ 4 ช่องทางใช้งานปลายทาง (extension, citizen portal, brand
watchlist webhook, public feed) เข้ากับ FastAPI backend ซึ่งเรียก ML
ensemble + Rules Engine บน `phish_features` package เพื่อให้คะแนนและ
verdict กลับ:

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
                              │ schema v1.4.0    │
                              │ 37 features      │
                              └──────────────────┘
```

ลำดับการทำงานเมื่อมี URL ใหม่:

1. Browser extension หรือ portal ส่ง URL ไป `POST /api/v1/check`
2. Backend เรียก `URLUnshortener` (ถ้าเปิด) แกะ short-link → URL ปลายทาง
3. `FeatureExtractor` คำนวณ 37 features (lexical, IDN, whitelist, WHOIS, TLS)
4. ML ensemble (RF + XGB voting + isotonic calibration) ให้ probability score
5. `RulesEngine` ตรวจ rule hits → ปรับ score / pin label หากตรง pattern ที่
   มั่นใจ
6. Backend ส่ง JSON กลับพร้อม `score`, `label`, `reason`, `rules.hits`,
   `closest_domain`, `edit_distance`
7. หาก label = phishing และตรง brand watchlist → ส่ง webhook (LINE/Slack)
8. หาก label = phishing → เพิ่มเข้า public threat feed และ campaign clustering

### 4.2 ทฤษฎี / Algorithm / เทคโนโลยี

#### 4.2.1 Feature Schema v1.4.0 (รวม 37 features)

| กลุ่ม | จำนวน | ตัวอย่าง |
|------|------|----------|
| Lexical v1 | 10 | url_length, num_dots, has_ip, entropy |
| Lexical v1.1 | 5 | path_depth, max_digit_run, has_query_string |
| Domain | 4 | domain_age_days, is_thai_tld, tld_type, is_known_registrar |
| Whitelist | 2 | min_edit_distance, is_typosquat |
| TLS | 3 | has_valid_cert, cert_age_days, is_self_signed |
| Meta | 2 | whois_ok, tls_ok |
| **IDN v1.2** | 3 | has_punycode, has_mixed_script, homoglyph_distance |
| **Path v1.3** | 4 | has_login_keyword, has_suspicious_tld, path_brand_hit, path_length |
| **Lexical v1.4** | 4 | **num_login_keywords, query_param_count, path_entropy, host_token_count** |

#### 4.2.2 ML Ensemble + Calibration

```python
# pseudo-code
rf  = RandomForestClassifier(n_estimators=200, class_weight="balanced", ...)
xgb = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, ...)
base = VotingClassifier([("rf", rf), ("xgb", xgb)], voting="soft")
model = CalibratedClassifierCV(base, method="isotonic", cv=5)
```

**ทำไมต้อง ensemble + calibration:**
* RF ดีในการจับ non-linear interaction
* XGB ดีในการเรียนรู้ tail (URL หายาก)
* Soft voting ใช้ probability เฉลี่ย ลด variance
* Isotonic calibration ทำให้ score มี meaning เป็น probability จริง
  (ไม่ใช่แค่ ranking) → threshold 0.7/0.3 มีความหมายข้ามดาต้าเซ็ต

#### 4.2.3 IDN / Homoglyph Defense

ผู้โจมตีใช้ตัวอักษรหน้าตาเหมือนจากภาษาอื่น (Cyrillic, Greek, Fullwidth) เช่น
`chulа.com` ใช้ Cyrillic `а` (U+0430) แทน Latin `a` (U+0061) — ระบบจะ:

1. **Decode IDN** (Punycode → Unicode)
2. **Fold confusables** ตาม Unicode TR36 (า → a, о → o, ...)
3. **เทียบ Levenshtein** กับ whitelist labels หลัง fold

ผลคือ `chulа.com` จะมี `homoglyph_distance = 0` กับ `chula.ac.th`

#### 4.2.4 Path Impersonation Detection (ใหม่ v1.3.0)

OpenPhish 2024-2025 รายงานว่ารูปแบบฟิชชิงที่นิยมที่สุดคือ host ดูปกติ
แต่เอา brand ใส่ใน path:

```
random-host-abc.cc/krungthai/login
secure-update.online/obec/verify-account
```

ระบบจึงตรวจ:
* `path_brand_hit = 1` ถ้ามี brand label ของ whitelist อยู่ใน path
* `has_login_keyword = 1` ถ้าใน path มีคำอย่าง login, signin, verify, ...
* `has_suspicious_tld = 1` ถ้า eTLD อยู่ใน list `.cc, .xyz, .icu, .cfd, ...`

#### 4.2.5 Heuristic Rules Engine

ML score + rule adjustments + rule pin = final score, final label

```python
class RulesEngine:
    def evaluate(url, features):
        hits = []
        for rule in DEFAULT_RULES:
            hit = rule(url, features)
            if hit: hits.append(hit)
        return RulesResult(hits, sum(deltas), pinned_label)
```

Built-in rules:

| Rule ID | เงื่อนไข | Δ score | Pin |
|---------|----------|---------|-----|
| `WHITELIST_EXACT` | host ตรง whitelist | -0.60 | safe |
| `AT_TRICK` | URL มี `@` ซ่อนปลายทาง | +0.55 | phishing |
| `IDN_HOMOGRAPH` | Punycode + close to brand | +0.45 | phishing |
| `TYPOSQUAT_CRED` | typosquat + login keyword | +0.40 | phishing |
| `PATH_BRAND_BAIT` | brand ใน path + cheap TLD | +0.30 | phishing |
| `IP_CRED` | IP host + login keyword | +0.50 | phishing |
| `CHEAP_TLD_PLAIN` | cheap TLD ไม่มี HTTPS | +0.20 | (no pin) |

#### 4.2.6 Campaign Clustering Algorithm

```python
fingerprint = f"{brand}|{tld}|{path_shape}"
# path_shape: digits → "#", hex>=8 → "$hex"
```

URL ที่ fingerprint ตรงกันถือเป็น campaign เดียวกัน

#### 4.2.7 STIX 2.1 Output

```jsonc
{
  "type": "indicator",
  "spec_version": "2.1",
  "pattern_type": "stix",
  "pattern": "[url:value = 'https://...']",
  "indicator_types": ["malicious-activity"],
  "confidence": 97
}
```

### 4.3 เครื่องมือที่ใช้ในการพัฒนา

| ประเภท | เครื่องมือ |
|--------|------------|
| ภาษา | Python 3.11, JavaScript (ES2022), JSX, HTML/CSS |
| ML library | scikit-learn 1.5, XGBoost 2.1, pandas, python-Levenshtein |
| Backend framework | FastAPI 0.115, uvicorn, SQLAlchemy 2.0 async, slowapi, prometheus-client |
| Frontend framework | React 18, Vite 5, TailwindCSS 3, TanStack Query, Recharts |
| Browser extension | Manifest V3, chrome.webNavigation API, service worker |
| Database | PostgreSQL 16 (production) / SQLite (dev/demo) |
| Testing | pytest 8.3, httpx 0.28 (TestClient) — 206 cases |
| CI/CD | GitHub Actions, Docker, ruff, recall-gate check |
| Deploy | Docker, Docker Compose, Render Blueprint |
| IDE | VS Code |

> **ข้อมูลลิขสิทธิ์ซอฟต์แวร์:** เครื่องมือทั้งหมดที่ใช้พัฒนาเป็น open-source license
> ที่เข้ากันได้กับ Apache 2.0 — ดูรายการเต็มที่ไฟล์ `NOTICE` ใน repository

### 4.4 Software Specification

#### Input / Output

* **Input:** URL string (HTTP/HTTPS, ≤ 2048 chars) ส่งเข้า `POST /api/v1/check`
  ในรูปแบบ JSON `{"url": "https://..."}`
* **Output JSON** มีฟิลด์หลัก:
  * `score` — float 0–1 (probability ของ phishing)
  * `label` — `safe` | `suspicious` | `phishing`
  * `reason` — ข้อความภาษาไทยอธิบายว่าทำไม
  * `features` — dict 37 ฟีเจอร์ที่คำนวณได้
  * `rules.hits[]` — array ของ rule_id ที่ทำงาน + delta + pinned
  * `closest_domain`, `edit_distance` — แบรนด์ใน whitelist ที่ใกล้ที่สุด
  * `checked_at` — ISO timestamp
* **Latency:** p95 < 250 ms (CPU inference ~30 ms, ที่เหลือคือ WHOIS/TLS)

#### Functional Specification (เลือกที่สำคัญ)

| Endpoint | หน้าที่ | Auth |
|----------|---------|------|
| `POST /api/v1/check` | ตรวจ URL เดียว + unshorten อัตโนมัติ | no |
| `POST /api/v1/check/batch` | ตรวจสูงสุด 50 URLs/request | no |
| `GET /api/v1/feed.{json,csv,stix}` | Public threat feed | no |
| `GET /api/v1/impact` | Social-impact metrics | no |
| `GET /api/v1/learn` | เนื้อหาให้ความรู้ 4 audience tiers | no |
| `POST /api/v1/feedback` | Citizen report (no login) | no |
| `POST /api/v1/watchlist` | ลงทะเบียนแบรนด์เฝ้าระวัง | admin |
| `GET /api/v1/campaigns` | Campaign cluster list | admin |
| `GET /api/v1/domain/{host}/history` | Reputation timeline | admin |
| `POST /api/v1/line/webhook` | LINE Messaging API (HMAC-SHA256) | signed |

#### โครงสร้างซอฟต์แวร์ (Design)

```
phish_features/   ← shared package, ML pipeline และ backend ใช้ร่วมกัน
├── schema.py     ← single source of truth 37 features + LOGIN_KEYWORDS + SUSPICIOUS_TLDS
├── lexical.py    ← computed-from-string features (deterministic)
├── whitelist.py  ← typosquat + brand-label edit distance
├── homoglyph.py  ← IDN decode + confusable fold (Unicode TR36)
├── extractor.py  ← FeatureExtractor (orchestrator)
└── rules.py      ← Heuristic RulesEngine (transparency layer)

backend/app/
├── main.py + middleware.py     ← request-id, security headers, JSON log
├── ml/scorer.py                ← model + rules → final verdict
├── unshorten.py                ← async URL unshortener (18 providers, HEAD-only)
├── content_check.py            ← HTML content fallback for gray-zone URLs + SSRF protection
├── routers/                    ← 11 routers (check, stats, history, admin, feedback,
│                                  watchlist, campaigns, domain, feed, impact, learn, line_bot)
├── campaigns.py + notifier.py  ← clustering + webhook (LINE/Slack-compatible)
└── models.py                   ← ORM tables (UrlCheck, Whitelist, Feedback,
                                   BrandWatch, WebhookDelivery, Campaign,
                                   ExternalFeedSource, FeedIngestionRecord)

ml_pipeline/
├── train.py                    ← train RF + XGB ensemble + isotonic calibration
├── evaluate.py                 ← Thai-targeting + generic holdout + CI gate
└── feedback_retrain.py         ← export confirmed feedback → trigger retrain

dashboard/src/                  ← React 18 + Vite 5; 11 หน้า (overview, history,
                                   campaigns, watchlist, feedback, learn, report,
                                   admin, login, about, settings)

extension/                      ← Manifest V3 browser extension
├── service_worker.js           ← real-time URL check + badge
├── popup.html + popup.js       ← detailed report popup
└── warning.html                ← full-screen interstitial หน้าเตือนก่อนเข้าเว็บ
```

**ส่วนที่ผู้พัฒนาเขียนเอง:** ทุกไฟล์ใน `phish_features/`, `backend/app/`,
`ml_pipeline/`, `dashboard/src/`, `extension/` (รวม Rules Engine, IDN defense,
campaign clustering, citizen portal, public feed STIX 2.1, brand watchlist
webhook, LINE bot, unshortener, content fallback, feedback retrain)
**ส่วนที่ใช้จาก library/ตัวอย่าง open-source:** scikit-learn, XGBoost,
FastAPI, React, TailwindCSS, pandas — ใช้ตาม API public ไม่ได้คัดลอกตัวอย่าง
โค้ดของผู้อื่นแบบเป็น block ใหญ่ ๆ — มี attribution ที่ `NOTICE`

### 4.5 ขอบเขตและข้อจำกัดของโปรแกรม

**ตรวจจับได้ (in-scope):**

* Typosquat, TLD swap, subdomain spoof, IP host, @-trick
* IDN/Homoglyph (Cyrillic / Greek / Fullwidth / Thai digit substitution)
* Punycode spoofs (`xn--`)
* Path-brand bait kits (`random.cc/krungthai/login` ฯลฯ)
* Cheap-TLD low-effort kits (`.cc`, `.xyz`, `.icu`, `.cfd`)
* URL ที่ซ่อนหลัง short link (เปิด `ENABLE_URL_UNSHORTENING=true`)
* โซนเทาที่หน้าเว็บมี password field + brand-in-title (เปิด `GRAY_ZONE_CONTENT_CHECK=true`)

**ตรวจจับไม่ได้ (out-of-scope):**

* Spear-phishing เนื้อหาในอีเมล (ไม่ได้สแกน mailbox)
* การโทรหลอก (vishing) / SMS หลอก (smishing) — ระบบรับเฉพาะ URL
* Malware ในไฟล์ที่ดาวน์โหลด
* การโจมตี zero-day ที่ไม่มี URL fingerprint
* ฟิชชิงที่ใช้โดเมน legit-but-compromised — ยังต้องอาศัย threat intelligence จาก feed ภายนอก

### 4.6 อุปกรณ์ที่ใช้กับโปรแกรม

* Server: VPS ขั้นต่ำ 1 vCPU / 1 GB RAM (ทดสอบบน DigitalOcean Basic, Render free tier)
* Database: PostgreSQL 16 หรือ SQLite (สำหรับ demo)
* Browser: Chrome ≥ 108, Edge ≥ 108, Firefox ≥ 121, Brave, Opera
* ไม่ต้องการ GPU — โมเดล inference ใช้ CPU พอ (~30 ms/URL)

---

## กลุ่มผู้ใช้โปรแกรม

| กลุ่ม | ใช้งานอย่างไร |
|------|----------------|
| ประชาชนทั่วไป | ติดตั้ง browser extension หรือใช้หน้า `/report` ของ dashboard |
| ผู้สูงอายุ / กลุ่มเปราะบาง | ใช้ extension (เตือนเต็มจอ) + เนื้อหา `/learn` เป็นภาษาไทย |
| ครู / อาจารย์ | ใช้สอน digital literacy ในห้อง — content ใน `/learn` |
| ฝ่าย IT หน่วยงานราชการ | ลงทะเบียน Brand Watchlist + เชื่อม webhook กับ LINE Notify / Slack |
| นักวิจัย / ชุมชน security | ดึง public threat feed (STIX) เข้า SIEM ของหน่วยงาน |
| ฝ่าย SOC | ดู campaigns / domain history ผ่าน dashboard |

---

## ผลการทดสอบ

### Thai-targeting Holdout (Primary Metric)

| Metric | v1.2.0 baseline | v1.3.0 | **v1.4.0 (ปัจจุบัน)** |
|--------|------|------|------|
| Recall ที่ threshold ≥ 0.7 | 98.11% (52/53) | 100% (53/53) | **100% (66/66)** |
| Mean score | 0.986 | 0.994 | **0.994** |

### Generic Phishing Holdout (Cross-check Metric)

| Metric | **v1.4.0** |
|--------|-----------|
| Recall (90 URL) | **98.9% (89/90)** |

### Cross-validation (5-fold synthetic, 12000 samples)

| Metric | v1.2.0 | v1.3.0 | **v1.4.0** |
|--------|--------|--------|-----------|
| F1 mean | 0.992 ± 0.002 | 0.998 ± 0.001 | **0.9985 ± 0.0009** |

### CI Gate

ทุก commit ผ่าน `python -m ml_pipeline.evaluate --enforce-threshold`
ต้องได้ Thai recall ≥ 0.85 (ตั้งโดย `THAI_RECALL_MIN_THRESHOLD`)

### Automated Test Suite

**206 pytest cases** ครอบคลุม (เพิ่ม 29 tests สำหรับ URL unshortener, content check, LINE bot, feedback retrain):
* Feature extraction (`test_lexical.py`, `test_homoglyph.py`, `test_extractor.py`)
* Whitelist + typosquat (`test_whitelist.py`)
* Scoring (`test_scorer.py`)
* Cache (`test_cache.py`)
* Golden URLs — pin verdicts สำหรับ URL ราชการจริง + 8 phishing patterns
* Seed corpus sanity (`test_seed_corpus.py`)
* Rules engine (`test_rules.py`) — ทุก rule + clamp + pin priority
* Campaign clustering (`test_campaigns.py`)
* New endpoints (`test_new_endpoints.py`) — watchlist, feed, campaigns,
  domain, impact, learn, request-id, security headers

---

## เปรียบเทียบกับโซลูชันที่มีอยู่

| ความสามารถ | Google Safe Browsing | Microsoft SmartScreen | ETDA Phishing Alert | **ระบบนี้** |
|------------|----------------------|------------------------|---------------------|---------------|
| Thai-brand whitelist (500+ โดเมน) | ❌ | ❌ | ✅ บางส่วน | ✅ ครบ 500+ |
| IDN/Homoglyph defense (TR36) | ⚠️ บางส่วน | ⚠️ บางส่วน | ❌ | ✅ Punycode + confusable fold + Levenshtein |
| Path-impersonation detection | ⚠️ general | ⚠️ general | ❌ | ✅ `path_brand_hit` + cheap-TLD + login keywords |
| Verdict ที่อธิบายได้ (rule_id) | ❌ blackbox | ❌ blackbox | ⚠️ description manual | ✅ Rules Engine โปร่งใส ทุก verdict มี hits[] |
| Public Threat Feed (STIX 2.1) | ❌ ต้อง API key | ❌ commercial | ⚠️ portal only | ✅ no-auth JSON / CSV / STIX |
| Citizen reporting (no login) | ❌ ต้อง Google account | ❌ ต้อง MS account | ✅ web form | ✅ portal + LINE bot + extension |
| Brand Watchlist + webhook สำหรับหน่วยงาน | ❌ | ❌ | ⚠️ ผ่าน email | ✅ LINE Notify / Slack webhook ทันที |
| Campaign clustering (kit fingerprint) | ⚠️ internal | ⚠️ internal | ❌ | ✅ `brand\|tld\|path-shape` fingerprint |
| URL Unshortening | ⚠️ บางส่วน | ⚠️ บางส่วน | ❌ | ✅ 18 short-link providers, async HEAD |
| Open source / ขยายผลได้ | ❌ commercial | ❌ commercial | ❌ | ✅ Apache 2.0, fork ได้ |
| Latency ต่อ URL | ~50–300 ms (network) | ~100 ms (built-in OS) | n/a (manual) | ~30 ms CPU inference |

**สรุปจุดเด่น:** ระบบที่ออกแบบเฉพาะตลาดไทย + transparent verdict + open-source
+ มี channel เพื่อหน่วยงานราชการโดยตรง (LINE Notify) — เป็นมุมที่โซลูชัน
global ไม่ได้ลงรายละเอียด

---

## การสอดคล้องกับ Sustainable Innovation Theme ของ NSC 2026

NSC 2026 กำหนด theme **Sustainable Innovation** ครอบคลุม 3 มิติ — Social,
Economic, Environmental — บวกแนวคิด Open / Circular ระบบนี้ออกแบบให้ตอบทุกมิติ:

| มิติ | สิ่งที่ระบบนี้ทำ | ตัวชี้วัด |
|------|------------------|------------|
| **Social Sustainability** | ปกป้องประชาชนกลุ่มเปราะบาง (ผู้สูงอายุ, ครู, นักเรียน) จากการตกเป็นเหยื่อ; Citizen Portal ไม่ต้อง login; เนื้อหา `/learn` 4 audience tiers เป็นภาษาไทย | จำนวน URL ที่ block + จำนวน citizen report |
| **Economic Sustainability** | ทุก URL ฟิชชิงที่ block ลดความเสียหายเฉลี่ย ~฿7,800/case (ETDA 2024 median); `/api/v1/impact` คำนวณยอดสะสมแบบเรียลไทม์; ระบบรันบน VPS ราคาประหยัด | จำนวน ฿ ที่ป้องกันสะสม |
| **Environmental Sustainability** | สถาปัตยกรรม low-resource (no GPU, single-binary, in-process cache); CPU inference ~30 ms/URL; รันบน Render free tier ได้ | kWh ต่อ 1,000 checks |
| **Open / Circular** | Apache 2.0 license + dataset ใน repo + public STIX feed → หน่วยงานอื่น fork ขยายผลต่อได้; Feedback Auto-retrain คือ closed-loop ทำให้โมเดลดีขึ้นด้วย data จากผู้ใช้จริง | จำนวน fork + จำนวน citizen feedback ที่กลับมาฝึก |

ระบบจึงไม่ใช่แค่ "เครื่องมือตรวจ URL" แต่เป็น **ระบบนิเวศ** ที่ทำให้ผู้ใช้,
หน่วยงาน, นักวิจัย และนักพัฒนารายอื่นเป็นกำลังในการต่อต้านฟิชชิงไปพร้อมกัน

---

## ปัญหาและอุปสรรค

| ปัญหา | วิธีแก้ |
|------|---------|
| Train/serve skew: ผลตอนฝึกกับตอน deploy ต่างกัน | สร้าง `phish_features` เป็น shared package, schema version check ที่ startup |
| Phishing kit เปลี่ยน pattern ทุกเดือน | ออกแบบ Rules Engine ที่เพิ่ม rule ใหม่ได้ทันทีโดยไม่ต้อง retrain |
| Synthetic data → recall ดีจอมปลอม | แยก holdout จริง 66 URL ออกก่อน train, ใช้เป็น primary metric |
| WHOIS/TLS lookup ช้า / fail | timeout-guarded + impute defaults; feature `whois_ok`/`tls_ok` ให้โมเดลรู้ |
| ส่งของให้ผู้ใช้ทั่วไป → ติดตั้งยาก | สร้างหน้า `/report` portal ไม่ต้อง login + extension MV3 |

---

## แนวทางการพัฒนาและประยุกต์ใช้ร่วมกับงานอื่น ๆ ในขั้นต่อไป

1. **LINE Official Account bot** — ให้ผู้ใช้พิมพ์ URL ส่งใน chat เพื่อตรวจ (Thai elderly ใช้ LINE มาก)
2. **SMS report gateway** — รับแจ้งฟิชชิงผ่าน SMS จากผู้สูงอายุที่ไม่ใช้ smartphone
3. **เชื่อม ETDA 1212 / ตำรวจไซเบอร์ 1441** — ส่ง finding ผ่าน API
4. **เปิด TAXII 2.1 server** เต็มรูปแบบ ไม่ใช่แค่ STIX bundle export
5. **Federated learning** — หน่วยงานหลายแห่ง deploy แล้ว aggregate signal โดยไม่ต้องแชร์ raw URL
6. **Visual fingerprint** — ใช้ headless browser ดูหน้าเว็บแล้วเปรียบเทียบกับ template ของหน่วยงานจริง

---

## ข้อสรุปและข้อเสนอแนะ

โครงการนี้แสดงให้เห็นว่าระบบตรวจจับฟิชชิงเฉพาะทางสำหรับเป้าหมายไทย เป็นไปได้
และให้ผลแม่นกว่าระบบ global ที่มีอยู่ในชุดข้อมูลที่ออกแบบมาวัดเป้าหมายตรง
โดยการรวม ML, Rules Engine, IDN defense และ Path-impersonation features
เข้าด้วยกัน

ระบบนี้ถูกออกแบบให้ **sustainable** ตาม theme NSC 2026 ใน 4 มิติพร้อมกัน:
* **Social** — protect citizens, no-login portal, accessibility-first
* **Economic** — quantified loss prevention via `/api/v1/impact`
* **Environmental** — low-resource architecture
* **Open** — Apache 2.0 + public threat feed + committed dataset

ข้อเสนอแนะต่อหน่วยงานราชการ: ลงทะเบียน brand watchlist พร้อม LINE Notify
webhook เพื่อให้รู้ก่อนความเสียหายลุกลาม และเชื่อม STIX feed เข้า SIEM
ของหน่วยงาน

---

## เอกสารอ้างอิง

1. ETDA, *รายงานสถานการณ์ภัยคุกคามทางไซเบอร์ของประเทศไทย ปี 2567*.
   สำนักงานพัฒนาธุรกรรมทางอิเล็กทรอนิกส์ (ETDA), 2568.
   URL: <https://www.etda.or.th>
2. Unicode Consortium, *Unicode Technical Report #36: Unicode Security
   Considerations*, 2024. URL: <https://www.unicode.org/reports/tr36/>
3. OASIS, *STIX™ Version 2.1 Specification*, 2021.
   URL: <https://docs.oasis-open.org/cti/stix/v2.1/>
4. T. Chen and C. Guestrin, *XGBoost: A Scalable Tree Boosting System*,
   KDD '16, pp. 785–794, 2016. DOI: 10.1145/2939672.2939785.
5. L. Breiman, *Random Forests*, Machine Learning 45 (1), pp. 5–32, 2001.
   DOI: 10.1023/A:1010933404324.
6. OpenPhish, *Live Phishing URL Feed*.
   URL: <https://openphish.com/>
7. URLhaus by abuse.ch, *Recent URL API*.
   URL: <https://urlhaus-api.abuse.ch/>
8. ThaiCERT, *Cybersecurity Advisories*.
   URL: <https://www.thaicert.or.th>
9. PhishTank, *Verified Phishing URL Database*.
   URL: <https://phishtank.org/>
10. LINE Corporation, *LINE Messaging API documentation*, 2024.
    URL: <https://developers.line.biz/en/docs/messaging-api/>
11. NIST, *Special Publication 800-63B: Digital Identity Guidelines*, 2017.
    URL: <https://pages.nist.gov/800-63-3/sp800-63b.html>
12. Google, *Safe Browsing API v4 Reference*.
    URL: <https://developers.google.com/safe-browsing/v4>

---

## สถานที่ติดต่อของผู้พัฒนาและอาจารย์ที่ปรึกษา

| | ผู้พัฒนา | อาจารย์ที่ปรึกษา |
|---|----------|------------------|
| ชื่อ | _________ | _________ |
| สถาบัน | _________ | _________ |
| โทรศัพท์ | _________ | _________ |
| Email | _________ | _________ |

---

## ภาคผนวก

ดูไฟล์แยก:
* `docs/nsc2026/04_installation_guide.md` — คู่มือการติดตั้ง
* `docs/nsc2026/05_user_guide.md` — คู่มือการใช้งาน
* `docs/nsc2026/06_disclaimer.txt` — ข้อตกลงในการใช้ซอฟต์แวร์
* `docs/nsc2026/07_poster.md` — โปสเตอร์ A1
