# 📋 ROADMAP / TODO List — Thai Anti-Phishing System

> เอกสารนี้คือ todo list การพัฒนาแบบครบถ้วนของโปรเจกต์ (อ้างอิงสถานะ **v1.5.0**)
> แบ่งเป็น 3 หมวดหลัก: **A. Production/Deployment**, **B. Roadmap ฟีเจอร์ใหม่**, **C. คุณภาพโค้ด/ระบบ/ML**
> สัญลักษณ์ลำดับความสำคัญ: 🔴 สูง · 🟡 กลาง · 🟢 ต่อเนื่อง/ระยะยาว

## สถานะปัจจุบัน (สรุป)

- Backend FastAPI (Python 3.11) — 13 routers, ML ensemble (RF + XGBoost, 42 features, schema v1.5.0)
- `phish_features` package (shared train/serve) + Rules Engine 7 กฎ
- Browser extension (Manifest V3) + Dashboard React 18 (15 หน้า) + public threat feed (JSON/CSV/STIX)
- เทสต์ 331 เคส (pytest) · CI 6 jobs (+lint/type) + coverage gate + ML gate (Thai recall ≥ 0.85)
- Deploy: Docker Compose / Render blueprint / Supabase Postgres
- ผลปัจจุบัน: Thai holdout recall **100%** (378/378) · generic **91.1%** (90 URLs)

> หมายเหตุ: ในโค้ดจริง **ไม่มี** TODO/FIXME ค้างชำระ — งานในเอกสารนี้เป็นการ **ขยายฟีเจอร์ + เตรียม production +
> ปิด known limitations** ที่ระบุไว้ใน README/เอกสาร ไม่ใช่การตามเก็บหนี้เทคนิค

---

## หมวด A — Production / Deployment Readiness 🔴

ด่านที่ต้องผ่านก่อนเปิดใช้งานจริงสู่สาธารณะ

- [x] **A1. Secrets & config hardening** — เพิ่ม startup guard ใน `backend/app/config.py` ปฏิเสธค่า default
  (`change-this-*`, `dev-local-key-change-me`) เมื่อรันโหมด production; บังคับตั้ง `JWT_SECRET`, `API_KEY`,
  `ADMIN_PASSWORD_HASH`
  - _AC:_ แอป refuse to start ถ้า prod ใช้ secret default และมี test ครอบใน `tests/` ✅ (`tests/test_config_guard.py`)
- [x] **A2. Liveness vs Readiness probe** — เพิ่ม `/health/ready` (DB + model) และ `/health/live` แยกจาก `/health`;
  อัปเดต healthcheck → `/health/live` ใน `backend/Dockerfile`, readiness ใน `render.yaml` (`tests/test_health_probes.py`)
- [x] **A3. DB migrations (Alembic)** — เพิ่ม `backend/alembic.ini` + async `migrations/env.py` + baseline
  `0001_baseline`; prod รัน `alembic upgrade head` (render preDeployCommand), dev/test ยังใช้ `create_all`
  - _AC:_ `alembic upgrade head` สร้าง schema ตรงกับ `backend/app/models.py` ✅ (`tests/test_migrations.py`)
- [x] **A4. Observability** — JSON log + request-id (มีอยู่); เพิ่ม Prometheus scrape config + alert rules
  + Grafana dashboard ใน `deploy/observability/` และ runbook ใน `docs/DEPLOY.md`
- [x] **A5. Rate limit แบบ multi-worker** — `rate_limit.py` ใช้ Redis storage เมื่อ `REDIS_URL` ตั้ง (fallback in-memory),
  per-IP limit `/check` + `/feedback` (`report_rate_limit`) (`tests/test_rate_limit_storage.py`)
- [x] **A6. CORS & security headers** — เพิ่ม HSTS (prod), CSP, X-Content-Type-Options ใน `backend/app/middleware.py`;
  จำกัด `CORS_ORIGINS` แบบ explicit (ห้าม wildcard) ใน prod ผ่าน config guard (`tests/test_health_probes.py`)
- [x] **A7. Staging deploy playbook** — `docs/DEPLOY.md`: step-by-step Render + Supabase,
  smoke test หลัง deploy (`/health/ready`, `/api/v1/check`, `/metrics`, security headers), และ rollback plan
- [x] **A8. Backup & retention policy** — `app/retention.py` + `scripts/retention.py` (prune `url_checks`,
  `webhook_delivery`, `feed_ingestion_records` ตาม `RETENTION_DAYS`) + backup/restore playbook ใน `docs/DEPLOY.md` (`tests/test_retention.py`)
- [x] **A9. Load test** — `deploy/loadtest/` (locust + k6) ยืนยัน p95 < 250 ms (k6 threshold gate) บน staging + README

---

## หมวด B — Roadmap ฟีเจอร์ใหม่ 🟡

ต่อยอดคุณค่าและการเข้าถึงผู้ใช้

- [x] **B1. LINE Official Account Bot** — `line_bot.py` สมบูรณ์: signature verify, URL → ตอบผลตรวจภาษาไทย,
  unshorten ก่อน score (parity กับ `/check`); เอกสารตั้งค่า channel ใน docstring
  - _AC:_ mock LINE webhook flow ครอบการตรวจ URL จริง ✅ (`tests/test_line_bot.py`)
- [x] **B2. SMS Report Gateway** — `POST /api/v1/sms/inbound` (JSON/Twilio form, shared secret) → extract URL → score
  → ตอบ SMS ภาษาไทย; provider abstraction `app/integrations/sms.py` (`tests/test_integrations.py`)
- [x] **B3. Government Integration** — `GovernmentConnector` protocol (`forward_report`/`fetch_blocklist`) + stub
  default, เลือกด้วย `GOV_CONNECTOR` (`app/integrations/government.py`, `tests/test_integrations.py`); design ใน `docs/INTEGRATIONS.md`
- [x] **B4. TAXII 2.1 Server** — `routers/taxii.py` read-only: discovery / api-root / collections /
  objects (envelope) / manifest, STIX indicators ผ่าน `app/stix.py` (deterministic id) (`tests/test_taxii.py`)
- [x] **B5. Federated Learning** — design (aggregate-counts protocol, secure aggregation/DP, PDPA review, ห้าม raw-URL egress)
  พร้อม feature flag plan ใน `docs/INTEGRATIONS.md` (implement หลัง MOU/privacy review)
- [x] **B6. Visual Fingerprinting** — design (headless screenshot + perceptual hash vs template library,
  off-hot-path, opt-in `VISUAL_FINGERPRINT_ENABLED`) ใน `docs/INTEGRATIONS.md`
- [x] **B7. SIEM/SOAR export ของ campaigns** — `GET /campaigns/export.json` (flat SIEM schema) + `/campaigns/export.stix`
  (STIX grouping SDOs, deterministic id) (`tests/test_campaign_export.py`)
- [x] **B8. IP/ASN-level reputation** — design (IP/ASN-keyed reputation store + features ใน schema ถัดไป,
  หลัง retrain/eval gate) ใน `docs/INTEGRATIONS.md`

---

## หมวด C — คุณภาพโค้ด / ระบบ / ML 🟢

- [x] **C1. Coverage gate** — `pytest-cov` + `--cov-fail-under=75` ใน CI (`backend-tests`); เติมเทสต์
  `notifier.py`, `unshorten.py`, `content_check.py`, `net_guard`, rate-limit (cov รวม 78%)
- [x] **C2. Lint / format / type** — `ruff` config + blocking CI job `lint-type`, `mypy` (informational),
  eslint flat config + `npm run lint` ใน `dashboard-build` (ruff/eslint ผ่านสะอาด)
- [x] **C3. ML accuracy — ลด miss generic** — review 4 URLs → 3 out-of-scope (generic/crypto), 1 borderline
  (`lnsta.fr`~nstda); สรุป: ไม่ใช่ปัญหา `min_edit_distance` → route case ที่ in-scope เข้า seed→gated-retrain
  (`reports/missed_generic_analysis.md`). ไม่ regenerate model ในแพตช์นี้เพื่อกัน drift (ทำผ่าน ml-gate/retrain เท่านั้น)
- [x] **C4. Model drift monitoring** — `phish_score` histogram (live score distribution) + `PhishScoreDistributionDrift`
  alert + WHOIS/TLS fallback metric; retrain cadence ผูก feedback/learn ใน `docs/ML_OPS.md`
- [x] **C5. Extension hardening** — ลด MV3 permissions เหลือ `webNavigation/notifications/storage`
  (ตัด `tabs`+`activeTab`); offline/timeout handling ใน `api.js` (AbortController); guard tests (`tests/test_extension_manifest.py`)
- [x] **C6. Security review** — SSRF guard กลาง `app/net_guard.py` ใช้ใน `unshorten.py` / `content_check.py`
  (block private/loopback/link-local + DNS-rebinding), review injection/authz → `docs/SECURITY_REVIEW.md`
- [x] **C7. API versioning & error contract** — error envelope `{error,code}` เอกสารใน OpenAPI ทุก operation
  (custom openapi), `X-Schema-Version` header + startup schema-mismatch check (`tests/test_error_contract.py`)
- [x] **C8. Docs sync** — metric sentinels ยังตรง CI (`make sync-docs-check`); อัปเดต README (endpoints ใหม่:
  TAXII, health probes, campaign export; doc links DEPLOY/ML_OPS/SECURITY_REVIEW; test count 331)
- [x] **C9. Auto feedback → retrain loop** — `app/retrain_trigger.py`: volume-based trigger จาก `POST /feedback`
  เมื่อ confirmed feedback ถึง threshold (debounced + staged eval gate) (`tests/test_retrain_trigger.py`)
- [x] **C10. Threshold A/B + live telemetry tuning** — `app/threshold_ab.py`: บันทึก score distribution (`phish_score`)
  + shadow A/B counter (`phish_threshold_ab_total{variant,label}`) เทียบ candidate threshold (`tests/test_threshold_ab.py`)
- [x] **C11. Seed corpus refresh cadence** — `.github/workflows/seed-refresh.yml` (รายเดือน + manual) รัน
  `scripts/collect_thai_phishing_seed.py` + audit แล้วเปิด PR ให้ review; `make seed-refresh` (`docs/ML_OPS.md`)

---

## ตารางสรุปลำดับความสำคัญ

| Priority | งาน | เหตุผล |
|----------|-----|--------|
| 🔴 P0 | A1, A2, A3, A6, C6 | จำเป็นก่อน expose สู่สาธารณะ (secret, security, migrations) |
| 🟠 P1 | A4, A5, A7, C1, C2 | เสถียรภาพ + คุณภาพต่อเนื่อง |
| 🟡 P2 | B1, B4, C3, C4, C9, C10, C11 | ต่อยอดคุณค่า/แม่นยำ + ปิด known limitations |
| 🟢 P3 | A8, A9, B2, B3, B5, B6, B7, B8, C5, C7, C8 | ระยะยาว / ทางเลือก |

---

_อัปเดตล่าสุด: 2026-06-01 · อ้างอิง v1.5.0 — ✅ ครบทุกข้อ (28/28): P0/P1/P2 implement พร้อมเทสต์, P3 implement (A8, A9, B2, B3, B7, C5, C7, C8) + design docs (B5, B6, B8)_
