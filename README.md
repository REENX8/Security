# 🛡️ ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานไทย

ระบบนี้สร้างมาเพื่อตรวจว่า URL ที่ได้รับมานั้น "ของจริง" หรือ "ของปลอม" โดยเน้นที่เว็บไซต์ราชการ (`.go.th`) และสถาบันการศึกษา (`.ac.th`) ของไทยเป็นหลัก เพราะมักถูกใช้หลอกลวงประชาชนบ่อยที่สุด

ระบบประกอบด้วย 4 ส่วนที่ทำงานร่วมกัน — AI สำหรับฝึกโมเดล, API backend, ส่วนขยายเบราว์เซอร์ และแดชบอร์ดสำหรับดูข้อมูล

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  ML Pipeline │──▶│  FastAPI     │◀──│  Browser     │   │  React       │
│  (ฝึกโมเดล) │   │  Backend     │   │  Extension   │   │  Dashboard   │
│              │   │  + Postgres  │◀──│  (MV3)       │   │              │──┐
└──────┬───────┘   └──────┬───────┘   └──────────────┘   └──────────────┘  │
       │                  │                                                │
       │           ┌──────▼───────┐                                        │
       └──────────▶│ phish_features│◀───────────────────────────────────────┘
                   │ (shared pkg) │   ใช้โค้ดดึง feature เดียวกันทั้งตอนฝึกและตอนใช้งานจริง
                   └──────────────┘
```

---

## จุดเด่น

**ความแม่นยำสูง** — โมเดลใช้ feature 26 ตัวร่วมกับ ensemble ของ RandomForest และ XGBoost จับ phishing URL ที่เลียนแบบเว็บรัฐ/การศึกษาไทยจาก holdout ได้ **98.1%** (52/53 ที่ threshold ≥ 0.7, 95% CI [0.90, 1.00]) บน Thai-targeting corpus ที่โมเดลไม่เคยเห็น และ generic real phishing recall อยู่ที่ **92.2%** (ดีขึ้นจาก 87.8% หลังขยาย seed)

**จับการปลอมแปลงโดเมนได้** — ระบบวัดความใกล้เคียงระหว่างชื่อโดเมนกับโดเมนราชการ/การศึกษา/ธนาคารรัฐที่เชื่อถือได้ **500+ รายการ** ไม่ว่าจะเป็นการพิมพ์ผิดเล็กน้อย (`0bec.go.th`) เปลี่ยน TLD (`obec.com`) หรือใช้ตัวอักษรซีริลลิกหน้าตาเหมือนกัน (`chulа.com` ที่ а เป็น Cyrillic) ก็จับได้

**ไม่พังเมื่อเน็ตช้า** — การค้นหาข้อมูล WHOIS และ TLS มี timeout ป้องกัน ถ้าดึงข้อมูลไม่ได้ระบบจะใช้ค่า default แทน ไม่ block การตรวจสอบ

**พร้อมใช้งานทันที** — โมเดลที่ฝึกแล้วถูก commit ไว้ใน repo แล้ว แค่ `docker compose up` ก็ได้ API ที่ใช้งานได้เลย

**100 automated tests** ครอบคลุมตั้งแต่ feature extraction, cache, ไปจนถึงทุก endpoint และ golden tests ที่ pin ผลลัพธ์สำหรับ URL ที่รู้อยู่แล้วว่าดีหรือแย่

**UX จริงจัง** — extension จะแสดงหน้าเตือนเต็มจอ (ไม่ใช่แค่ notification) เมื่อพบเว็บฟิชชิง พร้อมให้ผู้ใช้ขั้นสูง bypass ได้ถ้าต้องการ

---

## ความแม่นยำของโมเดล

ระบบนี้ทำมาเพื่อจับ phishing ที่เลียนแบบเว็บราชการ/การศึกษาไทย **metric หลัก**จึงเป็นค่า recall บนชุด Thai-targeting (ไม่ใช่ค่า recall บน phishing ทั่วโลกแบบสุ่ม)

### 🎯 Primary metric — Thai-targeting phishing holdout (53 URLs, โมเดลไม่เคยเห็น)
| เกณฑ์                              | ผลลัพธ์ |
|------------------------------------|---------|
| Recall ที่ threshold ≥ 0.7         | **98.11%** (52 / 53) |
| Recall ที่ threshold ≥ 0.3         | **100%** (53 / 53) |
| 95% CI (phishing threshold)        | [0.901, 0.997] |
| คะแนนเฉลี่ย                        | 0.986 |

ชุดทดสอบนี้คือ 30% ของ curated Thai-targeting phishing seed (`data/thai_phishing_seed.csv`, 175 รายการ ครอบคลุม 90+ brands) ที่ split ออกก่อนการฝึกและไม่ถูกใช้ในการเทรน

มี **CI gate** ที่ `THAI_RECALL_MIN_THRESHOLD = 0.85` — ถ้า primary metric ตกต่ำกว่าค่านี้ CI จะ fail ทันที (`python -m ml_pipeline.evaluate --enforce-threshold`)

### Secondary — Generic real phishing holdout (90 URLs จาก OpenPhish, ไม่ใช่ Thai-targeting)
| เกณฑ์                              | ผลลัพธ์ |
|------------------------------------|---------|
| Recall ที่ threshold ≥ 0.7         | **92.22%** (83 / 90) |
| Recall ที่ threshold ≥ 0.3         | **95.56%** (86 / 90) |

ตัวเลขนี้ใช้เป็น cross-check ว่าการปรับให้แม่นกับ Thai-targeting ไม่ทำให้ทั่วไปแย่ลงเกินไป

### Alignment score
`thai_recall − generic_recall = +0.0589` — โมเดลทำงานดีกว่าบนกลุ่มเป้าหมายที่ตั้งใจไว้ (Thai gov/edu) มากกว่ากลุ่มทั่วไป **+5.9 percentage points** ซึ่งเป็นพฤติกรรมที่ออกแบบไว้

### ชุดทดสอบสังเคราะห์ (1,200 URLs)
| Metric    | Score  |
|-----------|--------|
| F1-score  | 0.989  |
| ROC-AUC   | 0.999  |
| CV F1 (5-fold) | 0.992 ± 0.002 |

ตัวเลขนี้สูงเป็นปกติเพราะ train/test มาจาก SyntheticGenerator ตัวเดียวกัน — ใช้เป็น sanity check ภายในเท่านั้น

กราฟ Confusion Matrix, ROC Curve, Feature Importance และ Thai-vs-Generic recall bar chart อยู่ใน [`reports/`](reports/)

---

## โครงสร้างโปรเจกต์

```
Security/
├── phish_features/        # ⭐ package กลางที่ทั้งฝึกและ serve ใช้ร่วมกัน
│   ├── schema.py          #    รายชื่อ feature ทั้ง 21 ตัว + encoding + default
│   ├── lexical.py         #    feature จากโครงสร้าง URL (ไม่ต้องต่อเน็ต)
│   ├── whitelist.py       #    ตรวจ typosquat และวัด edit distance
│   ├── domain.py          #    ดึงข้อมูล WHOIS (มี timeout)
│   ├── tls.py             #    ตรวจ TLS certificate (มี timeout)
│   └── extractor.py       #    ตัวรวม FeatureExtractor
│
├── ml_pipeline/           # สร้างชุดข้อมูลและฝึกโมเดล
│   ├── build_whitelist.py
│   ├── synthetic_generator.py
│   ├── collect_dataset.py
│   ├── feature_engineering.py
│   ├── train.py
│   └── evaluate.py
│
├── backend/               # FastAPI service
│   ├── app/
│   │   ├── main.py        #    app, lifespan, middleware
│   │   ├── routers/       #    /check, /stats, /history, /admin, /feedback
│   │   ├── ml/            #    โหลดโมเดล, extractor adapter, scorer
│   │   └── models.py crud.py database.py schemas.py ...
│   └── Dockerfile
│
├── extension/             # Chrome extension (Manifest V3)
│   ├── manifest.json background.js popup.* options.* ...
│
├── dashboard/             # React 18 + Vite + Tailwind + Recharts
│   └── src/{pages,components,api}
│
├── data/                          # whitelist + Thai phishing seed corpus
│   ├── thai_gov_domains.csv       #   500+ Thai gov/edu/state-bank domains
│   └── thai_phishing_seed.csv     #   curated Thai-targeting phishing URLs
├── models/                # โมเดลที่ฝึกแล้ว (commit ไว้ใน repo)
├── reports/               # กราฟและ metrics ผลการประเมิน (รวม thai_vs_generic_recall.png)
├── scripts/
│   ├── seed_demo.py                       # เติมข้อมูลตัวอย่างให้ API
│   ├── expand_whitelist.py                # ขยาย whitelist จาก curated list + Wikipedia
│   └── collect_thai_phishing_seed.py      # สร้าง Thai-targeting phishing corpus
├── docker-compose.yml
└── .env.example
```

---

## เริ่มต้นใช้งาน

### วิธีที่ 1 — Docker (แนะนำ)

```bash
cp .env.example .env          # แล้วแก้ API_KEY
docker compose up -d --build  # เปิด PostgreSQL + API

curl http://localhost:8000/health
# {"status":"ok","model_ready":true,...}

# เติมข้อมูลตัวอย่างให้แดชบอร์ดมีอะไรแสดง
python scripts/seed_demo.py http://localhost:8000 "$(grep API_KEY .env | cut -d= -f2)"
```

API จะอยู่ที่ **http://localhost:8000** และดู API docs แบบ interactive ได้ที่ `/docs`

### วิธีที่ 2 — Python โดยตรง (ไม่ต้องใช้ Docker, ใช้ SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .                          # ติดตั้ง phish_features
pip install -r backend/requirements.txt

cd backend
DATABASE_URL="sqlite+aiosqlite:///./phish.db" \
API_KEY="dev-local-key-change-me" \
uvicorn app.main:app --reload
```

---

## ML Pipeline

ฝึกโมเดลใหม่ทั้งหมด (ทำได้แบบ offline ได้เกือบทั้งหมด):

```bash
pip install -e . && pip install -r ml_pipeline/requirements.txt

# ขั้นเตรียมข้อมูล (script ทั้งสองทำงาน offline ได้ถ้าใส่ --no-fetch)
python scripts/expand_whitelist.py             # -> data/thai_gov_domains.csv (500+ โดเมน)
python scripts/collect_thai_phishing_seed.py   # -> data/thai_phishing_seed.csv

# ขั้นฝึกและประเมิน
python -m ml_pipeline.build_whitelist      # -> models/whitelist.json
python -m ml_pipeline.collect_dataset      # -> data/dataset.csv (ใส่ --no-feeds ถ้าไม่ต้องการดึง feed)
python -m ml_pipeline.train                # -> models/ensemble.pkl, scaler.pkl, features.json
python -m ml_pipeline.evaluate             # -> reports/*.png, metrics.json, evaluation_summary.json
```

`expand_whitelist.py` รวม curated list ของหน่วยงานราชการ/มหาวิทยาลัย/รัฐวิสาหกิจไทย ~400 รายการ และเสริมจาก Wikipedia แบบ best-effort

`collect_thai_phishing_seed.py` มี URL phishing ที่เลียน Thai gov/edu/ธนาคาร ~95 รายการ ที่ตามรอยจาก ThaiCERT advisory และ public feeds — เป็น ground truth สำหรับ Thai-targeting holdout metric

### Feature ทั้ง 26 ตัว (schema v1.2.0)

| กลุ่ม     | Feature |
|-----------|---------|
| Lexical (v1) | url_length, num_dots, num_hyphens, num_at, num_slash, num_digits, has_ip, entropy, has_https, num_subdomains |
| Lexical (v1.1) | path_depth, domain_label_max_len, has_port, max_digit_run, has_query_string |
| Domain    | domain_age_days, is_thai_tld, tld_type, is_known_registrar |
| Whitelist | min_edit_distance, is_typosquat (เทียบกับ **500+ โดเมนไทย** ใน `data/thai_gov_domains.csv`) |
| **IDN/Homoglyph (v1.2)** | **has_punycode** (`xn--...`), **has_mixed_script** (Latin+Cyrillic เป็นต้น), **homoglyph_distance** (edit distance หลัง normalize confusables) |
| TLS       | has_valid_cert, cert_age_days, is_self_signed |
| Meta      | whois_ok, tls_ok (ดึงข้อมูลสำเร็จไหม) |

`whois_ok` / `tls_ok` มีไว้เพื่อให้โมเดลรู้ว่า "ดึงข้อมูลไม่ได้" ≠ "เป็นฟิชชิง" เพราะสองอย่างนี้ปรากฏในทั้งชุดปลอดภัยและชุดฟิชชิงพอๆ กัน (~22% ของทั้งสองฝั่ง)

Feature v1.2 (IDN/Homoglyph) จับการโจมตีที่แทนตัวอักษรด้วยตัวที่หน้าตาเหมือนกันจากภาษาอื่น (เช่น Cyrillic `а`, `о`, `е` แทน ASCII) — `homoglyph_distance` คำนวณ Levenshtein หลัง fold ตัวอักษรเหล่านี้กลับเป็น ASCII แล้ว ทำให้ `chulа.com` (а เป็น Cyrillic) ถูกตรวจเป็นการเลียน `chula.ac.th` ที่ distance 0

---

## Backend API

Base URL `http://localhost:8000` · ทุก route ใต้ `/api/v1/*` ต้องส่ง header `X-API-Key` · จำกัด 100 req/min ต่อ key

### `POST /api/v1/check` — ตรวจ URL เดียว

```jsonc
// request
{ "url": "https://obec.com/login" }

// response
{
  "url": "https://obec.com/login",
  "score": 0.99,
  "label": "phishing",            // safe | suspicious | phishing
  "reason": "โดเมนคล้ายกับเว็บไซต์ทางการ obec.go.th มาก ...",
  "features": { ... },
  "closest_domain": "obec.go.th",
  "edit_distance": 0,
  "checked_at": "2026-05-22T12:00:00+00:00",
  "cached": false
}
```

เกณฑ์การตัดสิน: `score < 0.3` → **safe**, `0.3–0.7` → **suspicious**, `≥ 0.7` → **phishing**

URL เดิมที่ถูกตรวจในช่วง `CACHE_TTL` วินาที (default 60) จะได้ผลจาก cache เลย ไม่คำนวณซ้ำ (response จะมี `"cached": true`)

### `POST /api/v1/check/batch` — ตรวจหลาย URL พร้อมกัน (สูงสุด 50)

```jsonc
{ "urls": ["https://www.obec.go.th", "http://obec.com/verify", ...] }
```

### `GET /api/v1/stats`
ยอดรวม, อัตราฟิชชิง, โดเมนที่ถูกปลอมมากที่สุด, กราฟ 7 วันย้อนหลัง และกิจกรรมแต่ละชั่วโมง

### `GET /api/v1/history`
ประวัติการตรวจสอบแบบ paginate กรองได้ด้วย `label`, `search`, `date_from`, `date_to`

### `GET /api/v1/admin/whitelist` / `POST` / `DELETE /{domain}`
จัดการ whitelist โดเมนที่เชื่อถือได้ผ่าน API (ต้องการ API key) — การเพิ่ม/ลบมีผลทันทีโดยไม่ต้อง restart

### `POST /api/v1/feedback`
รายงานผลที่ระบบตัดสินผิด (false positive / false negative) — ไม่ต้องการ API key เพื่อให้ผู้ใช้ทั่วไปรายงานได้ง่าย

### `GET /api/v1/feedback` / `GET /api/v1/feedback/export`
ดูรายการ feedback และ export เป็น CSV (ต้องการ API key)

### อื่นๆ
- `GET /health` — สถานะโมเดล, database, uptime, cache size
- `GET /metrics` — Prometheus format (checks per label, latency histogram, model-ready gauge)
- `GET /docs` — OpenAPI interactive UI

**Error responses** มีรูปแบบเดียวกันเสมอ: `{"error": "...", "code": "..."}` —
`422 VALIDATION_ERROR`, `401 INVALID_API_KEY`, `413 BATCH_TOO_LARGE`, `429 RATE_LIMITED`, `503 MODEL_NOT_LOADED`

---

## ส่วนขยายเบราว์เซอร์

รองรับ Chrome, Edge, Brave, Opera และ Firefox 121+ (Manifest V3)

### ติดตั้งแบบ Developer Mode

1. รัน `python scripts/build_extension.py` จะได้ไฟล์ `dist/thai-phishing-detector-v{VERSION}.zip`
2. แตกไฟล์ zip ไว้ที่ใดที่หนึ่งแบบถาวร
3. เปิด `chrome://extensions` → เปิด **Developer mode** → **Load unpacked** → เลือกโฟลเดอร์ที่แตกไว้
   สำหรับ Firefox: `about:debugging` → **Load Temporary Add-on…** → `manifest.json`
4. เข้าไปที่ **Options** ตั้งค่า API endpoint และ API key (ค่าเริ่มต้น: `http://localhost:8000`, `dev-local-key-change-me`)

ดูรายละเอียดการติดตั้งแต่ละเบราว์เซอร์, checklist สำหรับ Chrome Web Store และ troubleshooting ได้ที่ [`extension/README.md`](extension/README.md)

### การทำงาน

ทุกครั้งที่เปิดหน้าเว็บใหม่ ส่วนขยายจะตรวจ URL นั้นแบบ real-time:

- badge บน icon: **✓ เขียว** = ปลอดภัย · **? เหลือง** = น่าสงสัย · **! แดง** = ฟิชชิง
- ถ้าพบฟิชชิงและเปิดโหมด Block ไว้ จะ**แสดงหน้าเตือนเต็มจอ**ก่อนเข้าเว็บ พร้อมปุ่ม "ยืนยันว่าจะเข้าต่อ" สำหรับผู้ที่รู้ตัวเองว่ากำลังทำอะไรอยู่
- popup แสดงคะแนน, ผลการตัดสิน, เหตุผล และโดเมนราชการที่ถูกปลอมแปลง
- timeout 3 วินาที → ถ้าตรวจไม่เสร็จจะขึ้น "ตรวจสอบไม่ได้" แทน ไม่ block การท่องเว็บ

---

## Dashboard

```bash
cd dashboard
cp .env.example .env          # ตั้ง VITE_API_URL + VITE_API_KEY
npm install
npm run dev                   # http://localhost:5173
```

มี 6 หน้า:

- **ภาพรวม** — stat cards, ช่องตรวจ URL เดี่ยว, กราฟ 7 วัน, รายการล่าสุด
- **ตรวจหลาย URL** — วางได้สูงสุด 50 URLs แล้วตรวจพร้อมกัน, export CSV ได้
- **ประวัติ** — ตารางกรอง/ค้นหา/paginate, กดแถวเพื่อดู feature ทั้ง 21 ตัว, export CSV
- **สถิติเชิงลึก** — โดเมนถูกปลอมมากที่สุด, สัดส่วน verdict, heatmap รายชั่วโมง
- **จัดการ Whitelist** — เพิ่ม/ลบโดเมนที่เชื่อถือได้ มีผลทันทีโดยไม่ต้อง restart
- **รายงานผลผิด** — ดู feedback จากผู้ใช้ทั้งหมด กรองและ export CSV ได้

---

## Configuration

ค่าทั้งหมดมาจาก environment variables หรือไฟล์ `.env` (ดูตัวอย่างที่ [`.env.example`](.env.example)):

| Variable | ความหมาย | Default |
|----------|----------|---------|
| `DATABASE_URL` | connection string (PostgreSQL หรือ SQLite) | `postgresql+asyncpg://phish:phish@db:5432/phishdb` |
| `API_KEY` | รหัสสำหรับ `X-API-Key` header | `dev-local-key-change-me` |
| `CORS_ORIGINS` | origins ที่อนุญาต | `http://localhost:5173,...` |
| `RATE_LIMIT` | จำนวน request สูงสุดต่อนาที | `100/minute` |
| `ENABLE_WHOIS` / `ENABLE_TLS` | เปิด/ปิดการดึงข้อมูลเพิ่มเติม | `true` |
| `NETWORK_TIMEOUT` | timeout ต่อ lookup (วินาที) | `2.5` |

Dashboard: `VITE_API_URL`, `VITE_API_KEY`

---

## ทำไมผลตอนฝึกกับตอนใช้งานจริงถึงตรงกัน

ปัญหาที่พบบ่อยใน ML คือโมเดลทำงานดีตอนทดสอบ แต่พอ deploy จริงผลเปลี่ยนไป เพราะโค้ดที่ดึง feature ตอนฝึกกับตอนใช้งานไม่เหมือนกัน ระบบนี้ป้องกันปัญหานั้นด้วย:

1. **โค้ดเดียว** — `phish_features` เป็นที่เดียวที่มี feature math ทั้งหมด ทั้ง pipeline และ API import package นี้ ไม่มีโค้ดแยก
2. **ล็อก contract** — `train.py` เขียน `models/features.json` พร้อม `FEATURE_SCHEMA_VERSION` ไว้ เมื่อ backend start จะเช็คว่า schema ตรงกับโค้ดปัจจุบัน ถ้าไม่ตรงจะปฏิเสธ start
3. **Scaler ชุดเดียวกัน** — `StandardScaler` ถูก fit ตอนฝึกและ save ไว้ serving ใช้ตัวเดิม ไม่ fit ใหม่
4. **Whitelist ชุดเดียวกัน** — ทั้งฝึกและ serve โหลด `models/whitelist.json` เดียวกัน ผล edit distance จึงเหมือนกันเสมอ

---

## Tests

```bash
pip install -e . && pip install -r backend/requirements.txt
pip install pytest==8.3.4 httpx==0.28.1
python -m pytest
```

108 tests ครอบคลุม:

| Suite               | ครอบคลุมอะไร |
|---------------------|-------------|
| `test_lexical.py`   | Shannon entropy, URL normalisation, ตรวจ IP, นับ subdomain |
| `test_whitelist.py` | Registrable domain, brand label, typosquat และ TLD-swap rules |
| `test_extractor.py` | shape ของ feature vector, network override, IP-host short-circuit |
| `test_scorer.py`    | threshold logic, output shape, โมเดลจริงบน URL ตัวอย่าง |
| `test_cache.py`     | TTL expiry, maxsize eviction, clear |
| `test_api.py`       | ทุก endpoint + error path + whitelist CRUD + feedback |
| `test_golden.py`    | pin verdict ของ URL ราชการ/การศึกษาจริง และ phishing 8 รูปแบบ |

GitHub Actions รัน test suite, build dashboard และ build Docker image ทุก push (ดูที่ [`.github/workflows/ci.yml`](.github/workflows/ci.yml))

---

## ระบบนี้จับอะไรได้บ้าง และอะไรจับไม่ได้

| ประเภทการโจมตี | จับได้? | วิธีที่ระบบตรวจ |
|----------------|---------|----------------|
| พิมพ์ชื่อโดเมนผิดนิดหน่อย (`0bec.go.th`, `0bec.xyz`) | ✅ | typosquat + brand-label edit distance |
| เปลี่ยน TLD (`obec.com`, `chula.org`) | ✅ | min_edit_distance = 0 บน TLD ที่ไม่ใช่ของรัฐ |
| ยัดชื่อราชการไว้ใน subdomain (`obec.go.th.evil.com`) | ✅ | num_subdomains, num_dots, lexical features |
| ใช้ IP แทนโดเมน (`http://203.0.113.45/obec/login`) | ✅ | has_ip = 1 |
| ใช้ @ หลอก (`https://obec.go.th@evil.xyz/`) | ✅ | num_at = 1 |
| โดเมนยาวมีขีดเยอะ (`secure-bot-or-th-update.club`) | ✅ | num_hyphens, length, brand distance |
| **ใช้ตัวอักษรซีริลลิก/Greek/Fullwidth** (`chulа.com` ที่ а เป็น Cyrillic) | ✅ | `has_mixed_script`, `homoglyph_distance` (confusable fold + edit distance) |
| **Punycode IDN spoofing** (`xn--obec-9bc.com`) | ✅ | `has_punycode`, IDN decode → confusable fold → edit distance |
| **เลียน Thai brand บน TLD ผิด** (`paotang-th.com`, `kasikornbank.online`) | ✅ | whitelist ขยายเป็น 500+ โดเมนรวมธนาคาร/telecom ที่ถูกเลียนบ่อย |
| URL แปลกๆ บน TLD ถูก (`.cfd`, `.fwh.is`) โดยไม่เลียนแบบใคร | ⚠️ บางส่วน | พึ่ง lexical signals เท่านั้น — generic holdout recall ≈ 88% |
| โดเมนเก่าที่ถูกแฮ็ก (อายุโดเมนดี แต่เนื้อหาไม่ดี) | ⚠️ บางส่วน | เห็นแค่ URL ไม่เห็นเนื้อหา |
| ผ่าน URL shortener หรือ redirect chain | ❌ | ระบบเห็นแค่ URL ต้นทาง ต้องใช้ redirect resolver ช่วย |
| เว็บปลอมที่ URL ดูปกติ แต่หน้าเว็บเป็นฟิชชิง | ❌ | ระบบนี้ดู URL อย่างเดียว ต้องใช้ content scanner เสริม |

ระบบนี้ทำงานได้ดีที่สุดในฐานะ "ชั้นแรก" ของการป้องกัน ไม่ใช่ชั้นเดียว

---

## ก่อน deploy จริง

ถ้าจะเอาไปใช้งานจริงนอกสภาพแวดล้อม demo ควรทำเพิ่ม:

- **Secrets** — เปลี่ยน `API_KEY` ใหม่ และ serve ผ่าน HTTPS (Caddy / nginx / Cloud Run)
- **Cache** — ถ้า scale เกิน 1 replica ให้เปลี่ยนจาก in-process `TTLCache` เป็น Redis
- **Rate limiting** — slowapi ปัจจุบัน key ด้วย API key ถ้าอยู่หลัง load balancer ให้เพิ่ม per-IP limit และ WAF ด้วย
- **Database** — ควรมี retention policy สำหรับ `url_checks` ที่เก่า และใช้ `pg_repack` ไม่ให้ table bloat
- **Observability** — scrape `/metrics`, ส่ง log เข้า aggregator และตั้ง alert เมื่อ `phish_model_ready == 0`
- **โมเดล** — ควร retrain บนชุดข้อมูลจริง (PhishTank credentials, URLhaus) โมเดลที่ ship มาได้ ~93% recall จากข้อมูลสังเคราะห์ แต่ชุดข้อมูลจริงจะยกระดับขึ้นได้อีก

---

## ข้อจำกัดที่ควรรู้

โมเดลที่ ship มาฝึกบน**ข้อมูลผสม** — synthetic จำนวนมาก (anchored กับ whitelist 500+ โดเมนไทย) + curated Thai-targeting phishing seed (95 URLs จากการรวบรวม case จริง) + real generic phishing จาก OpenPhish (210 URLs สำหรับ train + 90 URLs สำหรับ holdout) จุดแข็งของมันอยู่ที่การจับการปลอมแปลงโดเมนราชการ/การศึกษา/ธนาคารไทย ถ้าต้องการครอบคลุมฟิชชิงทั่วไปในวงกว้างขึ้น ให้ต่อ PhishTank หรือ URLhaus แล้วรัน pipeline ใหม่

ค่า WHOIS / TLS ในชุดข้อมูลสังเคราะห์เป็นการจำลอง (เพราะ URL ปลอมไม่มี DNS record จริง) — lexical, whitelist และ IDN/homoglyph features ทุกตัวคำนวณจาก URL string จริงเสมอ

**Thai-targeting seed corpus** (`data/thai_phishing_seed.csv`) เป็น 95 รายการที่ผมรวบรวมจาก pattern ที่ปรากฏใน ThaiCERT/ETDA advisories, ข่าว และ URLhaus archive เมื่อเลี้ยว Thai brand เข้าไปใน URL — ในการ deploy จริงควรเสริมด้วย feed จาก ThaiCERT โดยตรง หรือ telemetry จากการใช้งานจริง

---

## ทดสอบ end-to-end

```bash
# 1. tests
python -m pytest                              # 108 tests, ~4 วินาที

# 2. ฝึกโมเดลใหม่
python -m ml_pipeline.build_whitelist && python -m ml_pipeline.collect_dataset \
  && python -m ml_pipeline.train && python -m ml_pipeline.evaluate

# 3. API
docker compose up -d --build && curl localhost:8000/health

# 4. ข้อมูลตัวอย่าง
python scripts/seed_demo.py

# 5. extension: load unpacked จาก extension/ แล้วตั้ง API key ใน Options
# 6. dashboard
cd dashboard && cp .env.example .env && npm install && npm run dev
```

---

## Tech stack

**ML** — scikit-learn · XGBoost · pandas · python-Levenshtein

**Backend** — FastAPI · SQLAlchemy async · PostgreSQL · Pydantic v2 · slowapi · prometheus-client

**Extension** — Chrome Manifest V3 service worker · plain JavaScript (ไม่มี build step)

**Dashboard** — React 18 · Vite · TailwindCSS · Recharts · TanStack Query · React Router
