# 🛡️ Thai Phishing URL Detection System

ระบบตรวจจับ URL ฟิชชิงที่ปลอมแปลงเป็นเว็บไซต์หน่วยงานราชการและสถาบันการศึกษาไทย
แบบครบวงจร — ตั้งแต่ ML pipeline, REST API, ส่วนขยายเบราว์เซอร์ ไปจนถึงแดชบอร์ด

A complete, production-style phishing-URL detection platform specialised for
**Thai government (`.go.th`) and education (`.ac.th`) websites**. It ships four
integrated components built around one shared, skew-free feature contract.

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  ML Pipeline │──▶│  FastAPI     │◀──│  Browser     │   │  React       │
│  (train)     │   │  Backend     │   │  Extension   │   │  Dashboard   │
│              │   │  + Postgres  │◀──│  (MV3)       │   │              │──┐
└──────┬───────┘   └──────┬───────┘   └──────────────┘   └──────────────┘  │
       │                  │                                                │
       │           ┌──────▼───────┐                                        │
       └──────────▶│ phish_features│◀───────────────────────────────────────┘
                   │ (shared pkg) │   one feature-extraction implementation
                   └──────────────┘   used by training AND serving
```

---

## ✨ Highlights

- **21-feature ML model** — RandomForest + XGBoost soft-voting ensemble,
  **F1 = 0.996 / ROC-AUC = 1.00** on the synthetic test split AND
  **93.3 % recall** on an independent held-out set of real OpenPhish URLs
  the model has never seen.
- **Zero train/serve skew** — both the pipeline and the API import the *same*
  `phish_features` package; the backend refuses to start a model whose feature
  schema does not match the code.
- **Typosquat-aware** — brand-label edit distance catches both classic
  typosquats (`0bec.go.th`) and TLD-swap impersonation (`obec.com`),
  with a 4-char minimum so short legitimate brands (e.g. `scb.co.th`) do
  not false-positive.
- **Robust offline pipeline** — a synthetic generator builds a realistic,
  balanced dataset with no external dependency; live PhishTank / OpenPhish
  feeds are used opportunistically when reachable.
- **Graceful degradation** — WHOIS / TLS lookups are timeout-guarded; a
  failed lookup is class-neutral (appears in ~22 % of *both* classes during
  training), so the verdict never collapses when the network blips.
- **Production observability** — `/metrics` (Prometheus), enriched `/health`,
  structured request logs.
- **100 automated tests** covering features, scorer, cache and every API
  endpoint, plus golden tests pinning verdicts for known-good and
  known-phishing URLs.
- **Real anti-phishing UX** — the extension shows a full-page warning
  interstitial (not just a notification) when a phishing site is opened,
  with an explicit per-session bypass for advanced users.
- **Ready to run** — trained model artifacts are committed; `docker compose up`
  gives you a working API immediately.

---

## 📊 Model performance

### Synthetic test split (1,200 URLs, stratified)
| Metric    | Score  |
|-----------|--------|
| Accuracy  | 0.9958 |
| Precision | 0.9933 |
| Recall    | 0.9983 |
| F1-score  | 0.9958 |
| ROC-AUC   | 0.9999 |

### **Honest generalisation: 90 real OpenPhish URLs the model has never seen**
| Metric                                    | Score |
|-------------------------------------------|-------|
| Recall @ phishing threshold (≥ 0.7)       | **0.9333** (84 / 90) |
| Recall @ suspicious threshold (≥ 0.3)     | **0.9667** (87 / 90) |
| Mean score                                | 0.857 |

These are the **most important numbers** — every fetched OpenPhish URL is
randomly split 70 / 30 by `collect_dataset.py`, and the 30 % holdout is
written to `data/real_phish_holdout.csv` and ONLY consumed by `evaluate.py`,
so the metrics above measure true generalisation, not memorisation.

Confusion matrix, ROC curve, feature-importance and full metrics JSON are
in [`reports/`](reports/).

---

## 🧱 Project structure

```
Security/
├── phish_features/        # ⭐ shared feature-extraction package (the contract)
│   ├── schema.py          #    ORDERED_FEATURES, encodings, imputed defaults
│   ├── lexical.py         #    URL-string features (no network)
│   ├── whitelist.py       #    typosquat / edit-distance logic
│   ├── domain.py          #    WHOIS features (timeout-guarded)
│   ├── tls.py             #    TLS certificate features (timeout-guarded)
│   └── extractor.py       #    FeatureExtractor orchestrator
│
├── ml_pipeline/           # dataset + training
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
│   │   ├── routers/       #    /check, /stats, /history
│   │   ├── ml/            #    loader, extractor adapter, scorer
│   │   ├── models.py crud.py database.py schemas.py ...
│   └── Dockerfile
│
├── extension/             # Chrome extension (Manifest V3)
│   ├── manifest.json background.js popup.* options.* ...
│
├── dashboard/             # React 18 + Vite + Tailwind + Recharts
│   └── src/{pages,components,api}
│
├── data/                  # thai_gov_domains.csv (whitelist source)
├── models/                # committed trained artifacts
├── reports/               # evaluation plots + metrics
├── scripts/seed_demo.py   # populate the API with sample data
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick start

### Option A — Docker (recommended)

Requires the trained model in `models/` (already committed).

```bash
cp .env.example .env          # then edit API_KEY
docker compose up -d --build  # starts PostgreSQL + the API

curl http://localhost:8000/health
# {"status":"ok","model_ready":true,...}

# populate sample data so the dashboard has something to show
python scripts/seed_demo.py http://localhost:8000 "$(grep API_KEY .env | cut -d= -f2)"
```

The API is now on **http://localhost:8000** (interactive docs at `/docs`).

### Option B — Local Python (no Docker, SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .                          # install phish_features
pip install -r backend/requirements.txt

cd backend
DATABASE_URL="sqlite+aiosqlite:///./phish.db" \
API_KEY="dev-local-key-change-me" \
uvicorn app.main:app --reload
```

---

## 🤖 ML pipeline

Re-train the model end-to-end (fully offline-capable):

```bash
pip install -e . && pip install -r ml_pipeline/requirements.txt

python -m ml_pipeline.build_whitelist      # -> models/whitelist.json
python -m ml_pipeline.collect_dataset      # -> data/dataset.csv  (add --no-feeds for pure offline)
python -m ml_pipeline.train                # -> models/ensemble.pkl, scaler.pkl, features.json
python -m ml_pipeline.evaluate             # -> reports/*.png, metrics.json
```

### Feature set (21 features)

| Group      | Features |
|------------|----------|
| Lexical    | url_length, num_dots, num_hyphens, num_at, num_slash, num_digits, has_ip, entropy, has_https, num_subdomains |
| Domain     | domain_age_days, is_thai_tld, tld_type, is_known_registrar |
| Whitelist  | min_edit_distance, is_typosquat (vs. 111 trusted Thai domains) |
| TLS        | has_valid_cert, cert_age_days, is_self_signed |
| Meta       | whois_ok, tls_ok (was the lookup successful?) |

The `whois_ok` / `tls_ok` flags let the model learn that a *failed* network
lookup is uncertainty — not evidence of phishing.

---

## 🌐 Backend API

Base URL `http://localhost:8000` · all `/api/v1/*` routes require the
`X-API-Key` header · rate limited to 100 req/min per key.

### `POST /api/v1/check`

```jsonc
// request
{ "url": "https://obec.com/login" }

// response
{
  "url": "https://obec.com/login",
  "score": 0.99,
  "label": "phishing",                       // safe | suspicious | phishing
  "reason": "โดเมนคล้ายกับเว็บไซต์ทางการ obec.go.th มาก ...",
  "features": { ... },
  "closest_domain": "obec.go.th",
  "edit_distance": 0,
  "checked_at": "2026-05-22T12:00:00+00:00",
  "cached": false
}
```

Verdict thresholds: `score < 0.3` → **safe**, `0.3–0.7` → **suspicious**,
`≥ 0.7` → **phishing**. Identical URLs hitting `/check` within
`CACHE_TTL` seconds (default 60) return the same verdict from an
in-memory cache without re-extracting features or writing a duplicate
history row (response carries `"cached": true`).

### `POST /api/v1/check/batch`

```jsonc
// request
{ "urls": ["https://www.obec.go.th", "http://obec.com/verify", ...] }   // max 50

// response
{ "count": 2, "results": [ /* CheckResponse, ... */ ] }
```

### `GET /api/v1/stats`
Aggregated counts, phishing rate, top impersonated domains, 7-day series and
24-hour activity buckets.

### `GET /api/v1/history?limit=50&offset=0&label=&search=&date_from=&date_to=`
Paginated, filterable check history (`limit` up to 1000 for CSV export).

### Other
- `GET /health` — model readiness, DB health, model metrics, uptime, cache size
- `GET /metrics` — Prometheus exposition (checks per label/cache, latency
  histogram, model-ready gauge, cache size)
- `GET /docs` — OpenAPI UI

**Errors** always have the shape `{"error": "...", "code": "..."}` —
`422 VALIDATION_ERROR`, `401 INVALID_API_KEY`, `413 BATCH_TOO_LARGE`,
`429 RATE_LIMITED`, `503 MODEL_NOT_LOADED`.

---

## 🧩 Browser extension (Chrome / Edge — Manifest V3)

1. Open `chrome://extensions`, enable **Developer mode**.
2. **Load unpacked** → select the [`extension/`](extension/) folder.
3. Open the extension **Options** and set the API endpoint + API key
   (defaults: `http://localhost:8000`, `dev-local-key-change-me`).

Every top-level navigation is checked in real time:

- badge **✓ green** safe · **? yellow** suspicious · **! red** phishing
- a desktop notification is raised on a phishing verdict
- **a full-page warning interstitial intercepts the navigation** when
  `Block phishing pages` is on (the default). The user can go back or
  explicitly bypass for the rest of the browser session
- the popup shows score, verdict, reason and the impersonated domain
- 3-second timeout → falls back to "unverified" (never blocks browsing)

---

## 📈 Dashboard (React)

```bash
cd dashboard
cp .env.example .env          # set VITE_API_URL + VITE_API_KEY
npm install
npm run dev                   # http://localhost:5173
```

Four pages:

- **Overview** — stat cards, single-URL manual checker, 7-day trend, recent
  checks
- **Bulk** — paste up to 50 URLs and score them all in one batched request;
  results table is exportable as CSV
- **History** — filterable, searchable, paginated table; click any row for a
  full-detail modal (all 21 features); the current filtered set is
  exportable as CSV (Excel-friendly, UTF-8 BOM)
- **Stats** — top-targeted-domains bar, verdict distribution pie, 24-hour
  activity heatmap

A live model-status indicator in the header polls `/health` every minute.

---

## ⚙️ Configuration

All settings come from environment variables / `.env` (see
[`.env.example`](.env.example)):

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | async DB DSN (PostgreSQL or SQLite) | `postgresql+asyncpg://phish:phish@db:5432/phishdb` |
| `API_KEY` | shared secret for `X-API-Key` | `dev-local-key-change-me` |
| `CORS_ORIGINS` | allowed dashboard origins | `http://localhost:5173,...` |
| `RATE_LIMIT` | slowapi limit | `100/minute` |
| `ENABLE_WHOIS` / `ENABLE_TLS` | live enrichment lookups | `true` |
| `NETWORK_TIMEOUT` | per-lookup hard timeout (s) | `2.5` |

Dashboard: `VITE_API_URL`, `VITE_API_KEY`.

---

## 🔒 How train/serve skew is prevented

1. **One implementation** — `phish_features` is the only place feature math
   lives; the backend's `ml/extractor.py` is a thin adapter with no logic.
2. **Pinned contract** — `train.py` writes `models/features.json` with the
   ordered feature list + `FEATURE_SCHEMA_VERSION`; on startup the backend
   asserts they match the installed `phish_features` or refuses to serve.
3. **Bundled scaler** — the `StandardScaler` is fit during training and saved;
   serving applies the exact same transform.
4. **Versioned whitelist** — both sides load the same `models/whitelist.json`,
   so edit-distance results are identical.

---

## 🧪 Tests

```bash
pip install -e . && pip install -r backend/requirements.txt
pip install pytest==8.3.4 httpx==0.28.1
python -m pytest
```

100 tests covering:

| Suite              | What it checks |
|--------------------|----------------|
| `test_lexical.py`  | Shannon entropy, URL normalisation, IP detection, subdomain counting |
| `test_whitelist.py`| Registrable-domain logic, brand-label extraction, typosquat & TLD-swap rules |
| `test_extractor.py`| Full feature vector shape; network override pathway; IP-host short-circuit |
| `test_scorer.py`   | Threshold logic + scorer output shape, real model on canned URLs |
| `test_cache.py`    | TTL expiry + maxsize eviction + clear |
| `test_api.py`      | Every endpoint (`/health`, `/check`, `/check/batch`, `/stats`, `/history`, `/metrics`) + every error path |
| `test_golden.py`   | Pinned verdicts for legit Thai gov/edu, global sites, and 8 phishing archetypes |

GitHub Actions runs the suite, the dashboard build, and a Docker image build
on every push (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

---

## 🎯 Threat model — what is caught vs. what isn't

| Attack | Caught? | How |
|--------|---------|-----|
| **Brand-label typosquat** on any TLD (`0bec.go.th`, `0bec.xyz`)         | ✅ | `is_typosquat=1`, brand-label edit distance |
| **TLD swap impersonation** (`obec.com`, `chula.org`)                    | ✅ | `min_edit_distance=0` on a non-trusted TLD |
| **Brand-stuffed subdomain spoof** (`obec.go.th.evil.com`)               | ✅ | `num_subdomains`, `num_dots`, brand-stuffed lexical features |
| **IP-host phishing** (`http://203.0.113.45/obec/login`)                 | ✅ | `has_ip=1` |
| **`@`-trick** (`https://obec.go.th@evil.xyz/`)                          | ✅ | `num_at=1`, host resolves to attacker |
| **Long hyphenated brand-stuffed** (`secure-bot-or-th-update.club`)      | ✅ | `num_hyphens`, length, brand-label distance |
| **Random-string phishing on cheap TLDs** (e.g. `*.cfd`, `.fwh.is`)      | ⚠️ partial | Lexical signals only; no brand link → harder. **Holdout recall ≈ 90 %** |
| **Phishing on compromised legitimate (aged) domains**                   | ⚠️ partial | Lexical + path features only; no brand link |
| **Phishing via redirect chains / URL shorteners**                       | ❌ | We only see the entry URL; combine with a redirect resolver |
| **Visual / homograph attacks** (Cyrillic look-alike chars in IDNs)      | ❌ | Punycode normalisation would catch these — not currently extracted |
| **HTML-content-based attacks**                                          | ❌ | This is a URL-only classifier; pair with content scanning |

The system is best used as the *URL-tier* of a defence-in-depth pipeline.

---

## 🏗️ Production hardening

Before exposing this beyond a demo:

- **Secrets** — rotate `API_KEY`; serve behind TLS (Caddy / nginx / Cloud Run).
- **Distributed cache** — replace the in-process `TTLCache` with Redis when
  scaling past one replica.
- **Rate limiting** — slowapi keys by API key today; behind a load balancer,
  add per-IP limits and an upstream WAF.
- **Database** — `pgcrypto` for UUID generation, `pg_repack` for the
  `url_checks` table over time, and retention policy for old rows.
- **Observability** — scrape `/metrics`, pipe logs into your aggregator,
  alert on `phish_model_ready == 0`.
- **Model lifecycle** — retrain on a real-data corpus (registered PhishTank
  credentials, URLhaus). The synthetic-anchored model gets ~93 % real-world
  recall as shipped; expect to lift that with proper labelled data.

---

## ⚠️ Notes & limitations

- The shipped model is trained largely on **synthetic data** anchored to a real
  111-domain Thai whitelist. It is excellent for typosquat / impersonation
  detection; for broader coverage, wire in registered PhishTank credentials or
  a larger labelled corpus and re-run the pipeline.
- WHOIS / TLS values for synthetic samples are *simulated* from realistic
  distributions (synthetic URLs do not resolve). Lexical + whitelist features
  are always computed for real from the URL string.
- This is a **defensive security** project intended for awareness, research
  and protecting users from impersonation of Thai public-sector websites.

---

## 🧪 End-to-end verification

```bash
# 1. tests
python -m pytest                              # 100 tests, ~4s

# 2. pipeline
python -m ml_pipeline.build_whitelist && python -m ml_pipeline.collect_dataset \
  && python -m ml_pipeline.train && python -m ml_pipeline.evaluate

# 3. API
docker compose up -d --build && curl localhost:8000/health
curl localhost:8000/metrics

# 4. sample data
python scripts/seed_demo.py

# 5. extension: load unpacked from extension/, set API key in Options
# 6. dashboard
cd dashboard && cp .env.example .env && npm install && npm run dev
```

---

## 🛠️ Tech stack

**ML** scikit-learn · XGBoost · pandas · Levenshtein ·
**Backend** FastAPI · SQLAlchemy (async) · PostgreSQL · Pydantic v2 · slowapi ·
**Extension** Chrome Manifest V3 service worker ·
**Dashboard** React 18 · Vite · TailwindCSS · Recharts · TanStack Query
