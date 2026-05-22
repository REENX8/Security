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
  **F1 = 0.994 / ROC-AUC = 1.00** on a 1,200-URL held-out test set.
- **Zero train/serve skew** — both the pipeline and the API import the *same*
  `phish_features` package; the backend refuses to start a model whose feature
  schema does not match the code.
- **Typosquat-aware** — brand-label edit distance catches both classic
  typosquats (`0bec.go.th`) and TLD-swap impersonation (`obec.com`).
- **Robust offline pipeline** — a synthetic generator builds a realistic,
  balanced dataset with no external dependency; live PhishTank / OpenPhish
  feeds are used opportunistically when reachable.
- **Graceful degradation** — WHOIS / TLS lookups are timeout-guarded; a
  failed lookup is class-neutral, so the verdict never collapses.
- **Ready to run** — trained model artifacts are committed; `docker compose up`
  gives you a working API immediately.

---

## 📊 Model performance

| Metric    | Score  |
|-----------|--------|
| Accuracy  | 0.9942 |
| Precision | 0.9917 |
| Recall    | 0.9967 |
| F1-score  | 0.9942 |
| ROC-AUC   | 0.9998 |

Confusion matrix, ROC curve and feature-importance plots are in
[`reports/`](reports/).

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
  "checked_at": "2026-05-22T12:00:00+00:00"
}
```

Verdict thresholds: `score < 0.3` → **safe**, `0.3–0.7` → **suspicious**,
`≥ 0.7` → **phishing**.

### `GET /api/v1/stats`
Aggregated counts, phishing rate, top impersonated domains, 7-day series and
24-hour activity buckets.

### `GET /api/v1/history?limit=50&offset=0&label=&search=&date_from=&date_to=`
Paginated, filterable check history.

### Other
`GET /health` (model readiness) · `GET /docs` (OpenAPI UI).

**Errors** always have the shape `{"error": "...", "code": "..."}` —
`422 VALIDATION_ERROR`, `401 INVALID_API_KEY`, `429 RATE_LIMITED`,
`503 MODEL_NOT_LOADED`.

---

## 🧩 Browser extension (Chrome / Edge — Manifest V3)

1. Open `chrome://extensions`, enable **Developer mode**.
2. **Load unpacked** → select the [`extension/`](extension/) folder.
3. Open the extension **Options** and set the API endpoint + API key
   (defaults: `http://localhost:8000`, `dev-local-key-change-me`).

Every top-level navigation is checked in real time:

- badge **✓ green** safe · **? yellow** suspicious · **! red** phishing
- a desktop notification is raised on a phishing verdict
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

Three pages: **Overview** (stat cards, manual URL checker, 7-day chart, recent
table), **History** (filterable/searchable paginated table) and **Stats**
(top-targeted-domains bar, verdict pie, 24-hour heatmap).

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
# 1. pipeline
python -m ml_pipeline.build_whitelist && python -m ml_pipeline.collect_dataset \
  && python -m ml_pipeline.train && python -m ml_pipeline.evaluate
# 2. API
docker compose up -d --build && curl localhost:8000/health
# 3. sample data
python scripts/seed_demo.py
# 4. extension: load unpacked from extension/
# 5. dashboard: cd dashboard && npm install && npm run dev
```

---

## 🛠️ Tech stack

**ML** scikit-learn · XGBoost · pandas · Levenshtein ·
**Backend** FastAPI · SQLAlchemy (async) · PostgreSQL · Pydantic v2 · slowapi ·
**Extension** Chrome Manifest V3 service worker ·
**Dashboard** React 18 · Vite · TailwindCSS · Recharts · TanStack Query
