# 🛡️ ระบบตรวจจับเว็บไซต์ฟิชชิงสำหรับหน่วยงานไทย

[![CI](https://github.com/reenx8/security/actions/workflows/ci.yml/badge.svg)](https://github.com/reenx8/security/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Schema](https://img.shields.io/badge/feature%20schema-v1.3.0-informational)](phish_features/schema.py)
[![Thai recall](https://img.shields.io/badge/Thai%20holdout%20recall-100%25%20(53%2F53)-success)](reports/evaluation_summary.json)
[![Tests](https://img.shields.io/badge/tests-162%20passing-success)](tests/)

ระบบ **end-to-end** สำหรับตรวจว่า URL หนึ่ง ๆ เป็นเว็บไซต์ฟิชชิงที่ปลอมหน่วยงานราชการ (`.go.th`) สถาบันการศึกษา (`.ac.th`) หรือธนาคาร/รัฐวิสาหกิจไทยหรือไม่ — ครอบคลุมตั้งแต่ ML pipeline, FastAPI backend, ส่วนขยายเบราว์เซอร์ Manifest V3, แดชบอร์ด React, public threat feed, brand watchlist + webhook, จัดกลุ่มแคมเปญฟิชชิง และ portal ให้ประชาชนแจ้งเว็บปลอมแบบไม่ต้อง login

```
                       ┌────────────────────────────────────────┐
                       │      Citizens / Operators / Bots       │
                       └──┬──────────┬──────────┬──────────┬────┘
                          │          │          │          │
                  Browser ext   Dashboard   API client   Public feed
                          │          │          │          │
                          └──────────▼──────────▼──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │  FastAPI backend   │ ──► PostgreSQL
                          │  /api/v1/*         │
                          │  + rules engine    │
                          │  + campaign cluster│
                          │  + webhook notifier│
                          └─────────┬──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │ phish_features pkg │  (single source of truth:
                          │ • lexical 16       │   ML pipeline & backend
                          │ • whois / tls      │   import the SAME code)
                          │ • IDN / homoglyph  │
                          │ • path / TLD       │
                          │ • RulesEngine      │
                          └─────────┬──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │ scikit-learn + XGB │
                          │ ensemble (.pkl)    │  schema v1.3.0 · 33 features
                          └────────────────────┘
```

---

## สารบัญ

- [จุดเด่นในเวอร์ชัน 1.0](#จุดเด่นในเวอร์ชัน-10)
- [ความแม่นยำของโมเดล](#ความแม่นยำของโมเดล)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [Quickstart — เริ่มต้นใช้งาน](#quickstart--เริ่มต้นใช้งาน)
- [ML Pipeline](#ml-pipeline)
- [Backend API](#backend-api)
- [Rules Engine (ใหม่ใน v1)](#rules-engine-ใหม่ใน-v1)
- [Brand Watchlist + Webhook (ใหม่ใน v1)](#brand-watchlist--webhook-ใหม่ใน-v1)
- [Campaign Clustering (ใหม่ใน v1)](#campaign-clustering-ใหม่ใน-v1)
- [Public Threat Feed (ใหม่ใน v1)](#public-threat-feed-ใหม่ใน-v1)
- [Domain Reputation Lookup (ใหม่ใน v1)](#domain-reputation-lookup-ใหม่ใน-v1)
- [ส่วนขยายเบราว์เซอร์](#ส่วนขยายเบราว์เซอร์)
- [Dashboard](#dashboard)
- [Citizen Report Portal (ใหม่ใน v1)](#citizen-report-portal-ใหม่ใน-v1)
- [Configuration](#configuration)
- [Tests](#tests)
- [ก่อน Deploy จริง](#ก่อน-deploy-จริง)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## จุดเด่นในเวอร์ชัน 1.0

**ความแม่นยำสูงและตรงเป้า** — โมเดลฝึกบน Thai-targeting seed corpus + synthetic anchored กับ 500+ Thai gov/edu/state-bank domains
จับ phishing ที่เลียนแบบเว็บราชการ/การศึกษา/ธนาคารไทยจาก holdout ได้ **100% (53/53)** ที่ threshold ≥ 0.7 บน schema v1.3.0
มี **CI gate ที่ recall ≥ 0.85** — ถ้าโมเดลใหม่ตกต่ำกว่าค่านี้ build จะ fail ทันที

**Feature Schema v1.3.0 ใหม่** — เพิ่ม 4 features จับ phishing kit ปัจจุบัน:
- `has_login_keyword` (login, signin, verify, account...)
- `has_suspicious_tld` (.cc, .xyz, .icu, .top, .cfd ที่ถูกใช้ปลอมบ่อย)
- `path_brand_hit` (แบรนด์ทางการอยู่ใน path แต่ไม่ใช่ host — รูปแบบฟิชชิงหลักของปี 2024-2025)
- `path_length` (path ยาวผิดปกติ)

**Rules Engine โปร่งใส** — declarative rules layer ทับบน ML — แต่ละ verdict บอกได้ว่ามี **rule ID ใดบ้างที่ทำงาน** พร้อมข้อความอธิบายภาษาไทย ใช้ override ผลของ ML ได้ในกรณีฉุกเฉินโดยไม่ต้องเทรนใหม่

**Brand Watchlist + Webhook** — operators ลงทะเบียนแบรนด์ที่ต้องเฝ้าระวัง + URL webhook (Slack/Line/SOAR) ระบบจะส่ง alert ทันทีที่ตรวจเจอ URL ฟิชชิงที่ปลอมแบรนด์นั้น (พร้อม retry และ delivery log)

**Campaign Clustering อัตโนมัติ** — จัดกลุ่ม URL ฟิชชิงที่มาจาก kit เดียวกัน (โดยใช้ fingerprint = แบรนด์ + TLD + path skeleton) — ใช้บล็อกทั้งกลุ่มแทนทีละ URL

**Public Threat Feed** — `/api/v1/feed.{json,csv,stix}` ฟีดสาธารณะ (ไม่ต้อง API key) แชร์ verdict ใน 24 ชั่วโมงล่าสุด — STIX 2.1 bundle สำหรับ TAXII consumers

**Citizen Report Portal** — หน้าให้ประชาชนแจ้ง URL ฟิชชิงแบบ **ไม่ต้อง login** เห็นผลของระบบทันที + รายงานผลผิดพลาดได้

**Browser extension ครบเครื่อง** — Chrome/Edge/Brave/Opera/Firefox 121+ Manifest V3 พร้อมหน้าเตือนเต็มจอ, popup feedback button, bypass-per-session, badge สี

**Production-grade observability** — `/health`, `/version`, `/metrics` (Prometheus), structured JSON logs (`LOG_FORMAT=json`), `X-Request-ID` propagation, security response headers ทุก response

**162 automated tests** — feature extraction, rules engine, campaign clustering, scorer, middleware, ทุก API endpoint, golden URLs, Thai seed corpus + holdout split

---

## ความแม่นยำของโมเดล

ระบบนี้ทำมาเพื่อจับ phishing ที่เลียนแบบเว็บราชการ/การศึกษา/ธนาคารไทย **metric หลัก**จึงเป็นค่า recall บนชุด Thai-targeting

### 🎯 Primary — Thai-targeting phishing holdout (53 URLs, schema v1.3.0)
| เกณฑ์                              | v1.2.0 | **v1.3.0** |
|------------------------------------|--------|------------|
| Recall ที่ threshold ≥ 0.7         | 98.11% (52/53) | **100% (53/53)** |
| Recall ที่ threshold ≥ 0.3         | 100% (53/53)   | **100% (53/53)** |
| 95% CI (phishing threshold)        | [0.90, 1.00]   | **[0.93, 1.00]** |
| คะแนนเฉลี่ย                        | 0.986          | **0.994** |
| CV F1 (5-fold synthetic)           | 0.992 ± 0.002  | **0.998 ± 0.001** |

ชุดทดสอบนี้คือ 30% ของ curated Thai-targeting phishing seed (`data/thai_phishing_seed.csv`, 175 รายการ) ที่ถูก hold out ก่อนการฝึก

**CI gate** ที่ `THAI_RECALL_MIN_THRESHOLD = 0.85` — ถ้าตกต่ำกว่าค่านี้ CI fail (`python -m ml_pipeline.evaluate --enforce-threshold`)

### Secondary — ทดสอบสังเคราะห์ (1,200 URLs)
| Metric    | Score  |
|-----------|--------|
| F1-score  | 0.999  |
| ROC-AUC   | 1.000  |
| Precision | 1.000  |
| Recall    | 0.998  |

ตัวเลขนี้สูงเป็นปกติเพราะ train/test มาจาก SyntheticGenerator ตัวเดียวกัน — ใช้เป็น sanity check ภายใน

กราฟ Confusion Matrix, ROC Curve, Feature Importance อยู่ใน [`reports/`](reports/)

---

## โครงสร้างโปรเจกต์

```
Security/
├── phish_features/           # ⭐ shared package (ทั้ง train และ serve ใช้ร่วมกัน)
│   ├── schema.py             #    33 features + LOGIN_KEYWORDS + SUSPICIOUS_TLDS
│   ├── lexical.py            #    feature จาก URL string
│   ├── whitelist.py          #    typosquat + edit distance
│   ├── homoglyph.py          #    IDN decode + confusable fold
│   ├── domain.py / tls.py    #    WHOIS / TLS (timeout-guarded)
│   ├── extractor.py          #    FeatureExtractor
│   └── rules.py              #    🆕 Heuristic RulesEngine
│
├── ml_pipeline/              # สร้าง dataset + ฝึก + ประเมิน
│   ├── synthetic_generator.py
│   ├── collect_dataset.py
│   ├── feature_engineering.py
│   ├── train.py
│   └── evaluate.py
│
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── middleware.py     #    🆕 X-Request-ID + security headers + JSON log
│   │   ├── campaigns.py      #    🆕 fingerprint clustering
│   │   ├── notifier.py       #    🆕 webhook delivery
│   │   ├── routers/
│   │   │   ├── check.py
│   │   │   ├── stats.py history.py admin.py feedback.py
│   │   │   ├── watchlist.py  #    🆕 brand watch CRUD + deliveries
│   │   │   ├── campaigns.py  #    🆕 campaign listing
│   │   │   ├── domain.py     #    🆕 reputation timeline
│   │   │   └── feed.py       #    🆕 public threat feed (JSON/CSV/STIX)
│   │   └── ml/
│   └── Dockerfile
│
├── extension/                # Chrome MV3 + popup + warning interstitial
│
├── dashboard/                # React 18 + Vite + Tailwind + Recharts
│   └── src/pages/
│       ├── Overview.jsx Bulk.jsx History.jsx Stats.jsx
│       ├── Admin.jsx Feedback.jsx
│       ├── Watchlist.jsx     #    🆕
│       ├── Campaigns.jsx     #    🆕
│       ├── Feed.jsx          #    🆕 (Threat Feed viewer)
│       ├── DomainLookup.jsx  #    🆕
│       └── Report.jsx        #    🆕 (Citizen reporting portal)
│
├── data/
│   ├── thai_gov_domains.csv          #  500+ trusted Thai domains
│   ├── thai_phishing_seed.csv        #  175 curated Thai-targeting phishing URLs
│   └── thai_phish_holdout.csv        #  53-URL holdout (auto-generated)
├── models/
│   ├── ensemble.pkl scaler.pkl features.json (committed, ready-to-serve)
│   └── whitelist.json
├── reports/                          #  evaluation PNGs + metrics JSON
├── scripts/
│   ├── seed_demo.py
│   ├── expand_whitelist.py
│   ├── collect_thai_phishing_seed.py
│   └── build_extension.py
├── Makefile                          #  🆕 make install test lint run train ...
├── docker-compose.yml
├── render.yaml                       #  Render Blueprint (one-click deploy)
├── LICENSE NOTICE CHANGELOG.md       #  🆕 release artifacts
├── SECURITY.md CONTRIBUTING.md
├── VERSION                           #  🆕 single source of truth (1.0.0)
└── tests/                            #  162 tests
```

---

## Quickstart — เริ่มต้นใช้งาน

### วิธีที่ 1 — Docker Compose (แนะนำ)

```bash
cp .env.example .env          # แก้ API_KEY (สำคัญ)
docker compose up -d --build  # PostgreSQL + API

curl http://localhost:8000/version
# {"backend":"1.0.0","phish_features":"1.1.0","schema":"1.3.0"}

curl -H "X-API-Key: $(grep API_KEY .env | cut -d= -f2)" \
     -X POST http://localhost:8000/api/v1/check \
     -H "Content-Type: application/json" \
     -d '{"url":"https://secure-update.cc/krungthai/login"}'
```

API อยู่ที่ **http://localhost:8000**, API docs ที่ **/docs**

### วิธีที่ 2 — Python อย่างเดียว (SQLite, ไม่ต้อง Docker)

```bash
make install
make run                      # → http://localhost:8000
```

### วิธีที่ 3 — Render Blueprint (cloud, one-click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

`render.yaml` สร้าง backend + Postgres (cross-region resilient) ในคลิกเดียว

---

## ML Pipeline

```bash
make train               # build_whitelist → collect_dataset (offline) → train
make evaluate            # → reports/*.png, metrics.json, evaluation_summary.json
make evaluate-gate       # ⚠️  ออกด้วย exit-code != 0 ถ้า Thai recall < 0.85
```

### Feature ทั้ง 33 ตัว (schema v1.3.0)

| กลุ่ม     | Feature |
|-----------|---------|
| Lexical (v1) | url_length, num_dots, num_hyphens, num_at, num_slash, num_digits, has_ip, entropy, has_https, num_subdomains |
| Lexical (v1.1) | path_depth, domain_label_max_len, has_port, max_digit_run, has_query_string |
| Domain    | domain_age_days, is_thai_tld, tld_type, is_known_registrar |
| Whitelist | min_edit_distance, is_typosquat |
| TLS       | has_valid_cert, cert_age_days, is_self_signed |
| Meta      | whois_ok, tls_ok |
| **IDN/Homoglyph (v1.2)** | **has_punycode, has_mixed_script, homoglyph_distance** |
| **🆕 Path-impersonation (v1.3)** | **has_login_keyword, has_suspicious_tld, path_brand_hit, path_length** |

---

## Backend API

ทุก route ใต้ `/api/v1/*` ต้องส่ง header `X-API-Key` ยกเว้น `/feedback` (POST), `/feed.*` (public) และ `/health`, `/version`, `/metrics`

### Core

| Method + Path | คำอธิบาย |
|---------------|----------|
| `POST /api/v1/check` | ตรวจ URL เดียว — return score, label, reason, **rules.hits[]**, features |
| `POST /api/v1/check/batch` | สูงสุด 50 URLs ต่อ request |
| `GET  /api/v1/stats` | aggregate metrics สำหรับ dashboard |
| `GET  /api/v1/history` | paginated history พร้อม filter (label, search, date_from/to) |

### Whitelist & Feedback

| Method + Path | คำอธิบาย |
|---------------|----------|
| `GET / POST / DELETE /api/v1/admin/whitelist[/{domain}]` | จัดการ whitelist (hot-reload) |
| `POST /api/v1/feedback` | รายงานผลผิด (ไม่ต้อง API key) |
| `GET  /api/v1/feedback`, `/api/v1/feedback/export` | ดู + export CSV |

### 🆕 ของใหม่ใน v1

| Method + Path | คำอธิบาย |
|---------------|----------|
| `GET / POST / DELETE /api/v1/watchlist[/{brand}]` | brand watch + webhook |
| `GET  /api/v1/watchlist/deliveries` | ดู delivery log ของ webhook (success/error) |
| `GET  /api/v1/campaigns` | campaign clusters (filter ด้วย brand, min_urls) |
| `GET  /api/v1/domain/{host}/history` | reputation timeline ของ host |
| `GET  /api/v1/feed.json` | public phishing feed (no auth) |
| `GET  /api/v1/feed.csv`  | spreadsheet-friendly |
| `GET  /api/v1/feed.stix` | STIX 2.1 bundle (indicators only) |

### Observability

| Method + Path | คำอธิบาย |
|---------------|----------|
| `GET /health` | model_ready, db_ok, uptime, schema_version, cache size |
| `GET /version` | `{"backend": ..., "phish_features": ..., "schema": ...}` |
| `GET /metrics` | Prometheus (checks_total, latency histogram, model_ready gauge, cache size) |

**Response headers** ทุก response: `X-Request-ID`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: interest-cohort=()`

**Error responses** มี shape เดียวกัน: `{"error": "...", "code": "..."}` — `422 VALIDATION_ERROR`, `401 INVALID_API_KEY`, `413 BATCH_TOO_LARGE`, `429 RATE_LIMITED`, `503 MODEL_NOT_LOADED`

---

## Rules Engine (ใหม่ใน v1)

โมดูล [`phish_features/rules.py`](phish_features/rules.py) เป็นชั้น **declarative rules** ทับบน ML ทุก `/check` response จะมี field `rules.hits[]` แสดงว่า rule ไหนทำงานบ้าง

ตัวอย่าง response:

```jsonc
{
  "url": "https://secure-update.cc/krungthai/login",
  "score": 0.99,
  "ml_score": 0.97,
  "label": "phishing",
  "reason": "ชื่อแบรนด์ทางการ (krungthai.com) ปรากฏใน path... · โดเมนคล้ายกับ krungthai.com และ URL ขอข้อมูล login...",
  "rules": {
    "score_delta": 0.7,
    "pinned_label": "phishing",
    "hits": [
      {"rule_id": "TYPOSQUAT_CRED",  "delta": 0.40, "pin_label": "phishing", "message": "..."},
      {"rule_id": "PATH_BRAND_BAIT", "delta": 0.30, "pin_label": "phishing", "message": "..."}
    ]
  }
}
```

### Built-in rules

| Rule ID | เงื่อนไข | Pin label |
|---------|----------|-----------|
| `WHITELIST_EXACT` | host ตรง whitelist (ไม่ใช่ typosquat / homograph) | **safe** (safety net) |
| `AT_TRICK` | URL มี `://...@...` ซ่อนปลายทาง | **phishing** |
| `IDN_HOMOGRAPH` | Punycode + homoglyph_distance ≤ 2 | **phishing** |
| `TYPOSQUAT_CRED` | typosquat + login keyword | **phishing** |
| `PATH_BRAND_BAIT` | brand ใน path + cheap TLD | **phishing** |
| `IP_CRED` | IP host + login keyword | **phishing** |
| `CHEAP_TLD_PLAIN` | cheap TLD + ไม่มี HTTPS | (boost ไม่ pin) |

เพิ่ม rule ใหม่ได้ทันที — เป็นแค่ฟังก์ชัน `(url, features) → RuleHit | None`

---

## Brand Watchlist + Webhook (ใหม่ใน v1)

```bash
# ลงทะเบียนแบรนด์
curl -X POST http://localhost:8000/api/v1/watchlist \
  -H "X-API-Key: $KEY" \
  -d '{"brand":"krungthai","webhook_url":"https://hooks.slack.com/services/..."}'

# ดูประวัติ delivery
curl http://localhost:8000/api/v1/watchlist/deliveries -H "X-API-Key: $KEY"
```

เมื่อ `/check` เจอ URL ฟิชชิงที่ `closest_domain` มี brand label ตรงกับที่ลงไว้
ระบบจะ POST payload แบบนี้ไปยัง webhook ทันที (พร้อม retry 1 ครั้ง):

```json
{
  "schema": "phish.alert.v1",
  "brand": "krungthai",
  "url": "https://krungthai-secure.online/login",
  "label": "phishing",
  "score": 0.98,
  "closest_domain": "krungthai.com",
  "reason": "...",
  "fired_at": "2026-05-26T..."
}
```

ทุก delivery (สำเร็จ/error) เก็บใน `webhook_delivery` ดูได้จาก API หรือ dashboard

---

## Campaign Clustering (ใหม่ใน v1)

```bash
curl http://localhost:8000/api/v1/campaigns?min_urls=2 -H "X-API-Key: $KEY"
```

ทุก URL ที่ `label ∈ {phishing, suspicious}` จะถูกสร้าง **fingerprint** = `<brand>|<tld>|<path-shape>`
URL ที่ fingerprint ตรงกันถือเป็น campaign เดียวกัน (มาจาก kit เดียวกัน)
ตัวอย่าง:

| brand | tld | path_shape | url_count |
|-------|-----|------------|-----------|
| krungthai.com | cc | krungthai/login | 47 |
| obec.go.th    | online | secure/login/$hex | 23 |

ดูใน dashboard ที่หน้า **แคมเปญฟิชชิง** ได้

---

## Public Threat Feed (ใหม่ใน v1)

```bash
# JSON
curl https://your-deployment/api/v1/feed.json?hours=24
# CSV (Excel-ready)
curl https://your-deployment/api/v1/feed.csv?hours=24
# STIX 2.1 bundle (TAXII-compatible indicators)
curl https://your-deployment/api/v1/feed.stix?hours=72
```

**ไม่ต้อง API key** — เป็น public good สำหรับชุมชน Cache ที่ 60 วินาทีเพื่อให้ poll ได้บ่อย ปิดได้ด้วย `ENABLE_PUBLIC_FEED=false`

---

## Domain Reputation Lookup (ใหม่ใน v1)

```bash
curl http://localhost:8000/api/v1/domain/www.obec.go.th/history -H "X-API-Key: $KEY"
```

Response:
```jsonc
{
  "host": "www.obec.go.th",
  "total_checks": 142,
  "mean_score": 0.04,
  "max_score": 0.11,
  "label_breakdown": {"safe": 142, "suspicious": 0, "phishing": 0},
  "timeline": [{"date": "2026-05-26", "checks": 7, "avg_score": 0.03, ...}],
  "recent_urls": [...]
}
```

ใช้ดูได้ว่า host หนึ่งเคยถูก flag ไหม, score มีแนวโน้มอย่างไร — ใช้ตรวจสอบ false positive ได้ดี

---

## ส่วนขยายเบราว์เซอร์

รองรับ Chrome, Edge, Brave, Opera, Firefox 121+ (Manifest V3)

```bash
make extension                # → dist/thai-phishing-detector-v{ver}.zip
```

ดูรายละเอียดการติดตั้ง, Chrome Web Store submission checklist, troubleshooting ที่ [`extension/README.md`](extension/README.md) — Privacy policy: [`extension/PRIVACY.md`](extension/PRIVACY.md)

**Behavior**: ทุกการ navigate จะส่ง URL ไป backend (timeout 3 วินาที) แล้ว
- 🟢 badge เขียว = safe · 🟡 เหลือง = suspicious · 🔴 แดง = phishing
- ถ้าเป็น phishing + เปิดโหมด Block → **หน้าเตือนเต็มจอ** พร้อมปุ่ม bypass per-session
- popup มีปุ่ม "รายงานผลผิด" ส่งกลับมายัง `/api/v1/feedback`

---

## Dashboard

```bash
make dashboard                # → http://localhost:5173
```

**11 หน้า**: ภาพรวม · ตรวจหลาย URL · ประวัติ · สถิติเชิงลึก · **แคมเปญฟิชชิง** 🆕 · **เฝ้าระวังแบรนด์** 🆕 · **ตรวจประวัติโดเมน** 🆕 · **Threat Feed** 🆕 · จัดการ Whitelist · รายงานผลผิด · **แจ้งเว็บฟิชชิง** 🆕

---

## Citizen Report Portal (ใหม่ใน v1)

หน้า `/report` ในแดชบอร์ด — ออกแบบมาสำหรับ **ประชาชนทั่วไป ไม่ต้อง login**:

1. กรอก URL ที่สงสัย
2. กดปุ่ม "ตรวจสอบก่อนแจ้ง" — เห็นคะแนน + เหตุผล + rule ที่ทำงาน
3. ระบุว่าเชื่อว่าเป็นอะไร (phishing / suspicious / safe)
4. ใส่รายละเอียดเพิ่มเติม (ไม่จำเป็น)
5. ส่ง → เก็บไว้ที่ `/api/v1/feedback` ใช้ปรับปรุงโมเดล

---

## Configuration

ค่าทั้งหมดมาจาก env หรือ `.env` (ดู [`.env.example`](.env.example)):

| Variable | ความหมาย | Default |
|----------|----------|---------|
| `DATABASE_URL` | PostgreSQL หรือ SQLite | `postgresql+asyncpg://phish:phish@db:5432/phishdb` |
| `API_KEY` | รหัส `X-API-Key` header | `dev-local-key-change-me` ⚠️ **เปลี่ยนก่อน deploy** |
| `CORS_ORIGINS` | origins ที่อนุญาต | localhost dashboard |
| `RATE_LIMIT` | requests per minute | `100/minute` |
| `ENABLE_WHOIS` / `ENABLE_TLS` | network lookups | `true` |
| `NETWORK_TIMEOUT` | timeout ต่อ lookup | `2.5` |
| `THRESHOLD_PHISHING` / `THRESHOLD_SUSPICIOUS` | label cutoffs | `0.7` / `0.3` |
| `LOG_FORMAT` | `text` หรือ `json` | `text` |
| `ENABLE_PUBLIC_FEED` | เปิด `/api/v1/feed.*` | `true` |
| `ENABLE_CAMPAIGN_TRACKING` | เปิด campaign clustering | `true` |

Dashboard: `VITE_API_URL`, `VITE_API_KEY`

---

## Tests

```bash
make test                     # 162 tests, ~16 วินาที
```

| Suite                  | ครอบคลุม |
|------------------------|---------|
| `test_lexical.py`      | URL normalisation, entropy, IP, subdomain |
| `test_whitelist.py`    | registrable domain, brand label, typosquat, TLD-swap |
| `test_homoglyph.py`    | IDN decode, confusable fold, mixed script |
| `test_extractor.py`    | feature vector shape, network override |
| `test_scorer.py`       | thresholds, real model on examples |
| `test_cache.py`        | TTL, eviction |
| `test_api.py`          | ทุก endpoint เดิม + error path |
| `test_golden.py`       | pin verdicts สำหรับ URL ราชการ/การศึกษาจริง + 8 phishing patterns |
| `test_seed_corpus.py`  | sanity check Thai seed corpus |
| **🆕 `test_rules.py`** | rules engine: ทุก rule + clamp + pin priority |
| **🆕 `test_campaigns.py`** | fingerprint + path shape normalisation |
| **🆕 `test_new_endpoints.py`** | watchlist, feed (JSON/CSV/STIX), campaigns, domain history, middleware, request-id |

GitHub Actions รัน test suite + dashboard build + Docker build + extension package + ML primary-metric gate ทุก push

---

## ก่อน Deploy จริง

| ต้องทำ | ทำไม |
|--------|------|
| เปลี่ยน `API_KEY` ใหม่ | default คือค่า dev — เห็นในซอร์สโค้ด |
| HTTPS termination | API key เดินทางใน plaintext ถ้าไม่ทำ TLS |
| ใช้ Redis แทน in-process cache | ถ้าจะ scale เกิน 1 replica |
| ใส่ WAF / per-IP limit เพิ่ม | ปัจจุบัน rate-limit per-key เท่านั้น |
| ตั้ง `LOG_FORMAT=json` + ส่งเข้า aggregator | structured logs ใช้ alert ง่ายกว่า |
| Scrape `/metrics` + alert `phish_model_ready==0` | จับโมเดลหายตอน boot |
| Retention policy บน `url_checks`, `webhook_delivery`, `campaigns` | ตารางพวกนี้โตเรื่อย ๆ |
| Retrain ด้วยข้อมูลจริงจาก deployment | seed corpus มี 175 รายการ — เสริมด้วย live telemetry จะดีกว่า |
| review Permissions extension store | ใช้ list ใน [`extension/README.md`](extension/README.md) |

ดูเพิ่มที่ [`SECURITY.md`](SECURITY.md)

---

## Tech Stack

**ML** — scikit-learn 1.5 · XGBoost 2.1 · pandas · python-Levenshtein

**Backend** — FastAPI 0.115 · SQLAlchemy 2.0 async · PostgreSQL 16 · Pydantic v2 · slowapi · prometheus-client

**Frontend** — React 18 · Vite 5 · TailwindCSS · Recharts · TanStack Query · React Router

**Extension** — Chrome Manifest V3 service worker · plain JavaScript

**Infra** — Docker · Docker Compose · Render Blueprint

---

## License

[Apache 2.0](LICENSE) · เห็นรายการ third-party dependencies ที่ [`NOTICE`](NOTICE)

ดู [`CHANGELOG.md`](CHANGELOG.md) สำหรับการเปลี่ยนแปลงทุกเวอร์ชัน, [`SECURITY.md`](SECURITY.md) สำหรับ vulnerability disclosure, และ [`CONTRIBUTING.md`](CONTRIBUTING.md) สำหรับการมีส่วนร่วม
