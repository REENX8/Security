# 📋 ROADMAP / TODO List — Thai Anti-Phishing System

> เอกสารนี้คือ todo list การพัฒนาแบบครบถ้วนของโปรเจกต์ (อ้างอิงสถานะ **v1.5.0**)
> แบ่งเป็น 3 หมวดหลัก: **A. Production/Deployment**, **B. Roadmap ฟีเจอร์ใหม่**, **C. คุณภาพโค้ด/ระบบ/ML**
> สัญลักษณ์ลำดับความสำคัญ: 🔴 สูง · 🟡 กลาง · 🟢 ต่อเนื่อง/ระยะยาว

## สถานะปัจจุบัน (สรุป)

- Backend FastAPI (Python 3.11) — 13 routers, ML ensemble (RF + XGBoost, 42 features, schema v1.5.0)
- `phish_features` package (shared train/serve) + Rules Engine 7 กฎ
- Browser extension (Manifest V3) + Dashboard React 18 (15 หน้า) + public threat feed (JSON/CSV/STIX)
- เทสต์ 265 เคส (pytest) · CI 5 jobs + ML gate (Thai recall ≥ 0.85)
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
- [ ] **A8. Backup & retention policy** — นโยบาย backup Postgres + retention ตาราง `url_checks`,
  `webhook_delivery`, `campaigns` (เอกสารระบุว่าโตไม่จำกัด ยังไม่มี retention)
- [ ] **A9. Load test** — ยืนยัน p95 < 250 ms ตามที่เอกสารอ้าง ด้วย locust/k6 บน staging

---

## หมวด B — Roadmap ฟีเจอร์ใหม่ 🟡

ต่อยอดคุณค่าและการเข้าถึงผู้ใช้

- [x] **B1. LINE Official Account Bot** — `line_bot.py` สมบูรณ์: signature verify, URL → ตอบผลตรวจภาษาไทย,
  unshorten ก่อน score (parity กับ `/check`); เอกสารตั้งค่า channel ใน docstring
  - _AC:_ mock LINE webhook flow ครอบการตรวจ URL จริง ✅ (`tests/test_line_bot.py`)
- [ ] **B2. SMS Report Gateway** — รับรายงาน phishing ผ่าน SMS (ผู้ไม่มี smartphone) ผ่าน provider → เข้าคิว `/report`
- [ ] **B3. Government Integration** — pluggable connector เชื่อม ETDA 1212 / ตำรวจไซเบอร์ 1441
  (ส่งต่อรายงาน + ดึง blocklist)
- [x] **B4. TAXII 2.1 Server** — `routers/taxii.py` read-only: discovery / api-root / collections /
  objects (envelope) / manifest, STIX indicators ผ่าน `app/stix.py` (deterministic id) (`tests/test_taxii.py`)
- [ ] **B5. Federated Learning** — รวม signal หลายหน่วยงานโดยไม่แชร์ raw URL (aggregate counts);
  ออกแบบ protocol + privacy review ก่อน implement
- [ ] **B6. Visual Fingerprinting** — เทียบ screenshot (headless browser) กับ template หน่วยงานจริง
  เพื่อจับ clone page; เป็น optional feature flag (latency สูง)
- [ ] **B7. SIEM/SOAR export ของ campaigns** — feed สาธารณะมีแล้ว แต่ campaign clusters ยังไม่ export;
  เพิ่ม endpoint/connector ส่ง campaign ไป SIEM/SOAR
- [ ] **B8. IP/ASN-level reputation** — ปัจจุบันตรวจระดับ URL เท่านั้น; ต่อยอด `DomainReputation` model
  ให้รองรับ reputation ระดับ IP/ASN

---

## หมวด C — คุณภาพโค้ด / ระบบ / ML 🟢

- [x] **C1. Coverage gate** — `pytest-cov` + `--cov-fail-under=75` ใน CI (`backend-tests`); เติมเทสต์
  `notifier.py`, `unshorten.py`, `content_check.py`, `net_guard`, rate-limit (cov รวม 78%)
- [x] **C2. Lint / format / type** — `ruff` config + blocking CI job `lint-type`, `mypy` (informational),
  eslint flat config + `npm run lint` ใน `dashboard-build` (ruff/eslint ผ่านสะอาด)
- [ ] **C3. ML accuracy — ลด miss generic** — ทบทวน 4 URLs ใน `reports/missed_generic_urls.csv`:
  ปรับ `min_edit_distance` ใน `phish_features`, ขยาย whitelist/seed, re-run `ml_pipeline` แล้วอัปเดต `reports/*.json`
- [ ] **C4. Model drift monitoring** — log distribution ของ feature/score ใน prod + alert เมื่อ drift;
  เอกสาร retrain cadence ผูกกับ `backend/app/routers/feedback.py`, `learn.py`
- [ ] **C5. Extension hardening** — เพิ่มเทสต์ฝั่ง extension, ลด MV3 permissions ให้น้อยที่สุด
  (ปัจจุบันขอ `<all_urls>`), จัดการ offline/error state ของ API call
- [x] **C6. Security review** — SSRF guard กลาง `app/net_guard.py` ใช้ใน `unshorten.py` / `content_check.py`
  (block private/loopback/link-local + DNS-rebinding), review injection/authz → `docs/SECURITY_REVIEW.md`
- [ ] **C7. API versioning & error contract** — รวม error shape ผ่าน `errors.py` ให้สม่ำเสมอ,
  เอกสาร OpenAPI ครบทุก endpoint, ปักหมุด schema version check
- [ ] **C8. Docs sync** — รักษา metrics ใน `docs/nsc2026` ให้ตรง CI (`tests/test_sync_docs.py`, `scripts/`),
  อัปเดต README สถาปัตยกรรมเมื่อเพิ่มฟีเจอร์ B*
- [ ] **C9. Auto feedback → retrain loop** — ปัจจุบัน retrain เป็น manual (`POST /api/v1/admin/retrain`);
  เพิ่ม trigger อัตโนมัติเมื่อ feedback ที่ยืนยันถึงเกณฑ์ (ผูก `ml_pipeline/feedback_retrain.py` + staged eval gate)
- [ ] **C10. Threshold A/B + live telemetry tuning** — holdout score polarized มาก จึงควรจูน threshold
  จาก telemetry จริง; เพิ่ม framework A/B test threshold + บันทึก score distribution
- [ ] **C11. Seed corpus refresh cadence** — กำหนดรอบ refresh `data/thai_phishing_seed.csv`
  ผ่าน `scripts/collect_thai_phishing_seed.py` ให้ทันแบรนด์/รูปแบบใหม่

---

## ตารางสรุปลำดับความสำคัญ

| Priority | งาน | เหตุผล |
|----------|-----|--------|
| 🔴 P0 | A1, A2, A3, A6, C6 | จำเป็นก่อน expose สู่สาธารณะ (secret, security, migrations) |
| 🟠 P1 | A4, A5, A7, C1, C2 | เสถียรภาพ + คุณภาพต่อเนื่อง |
| 🟡 P2 | B1, B4, C3, C4, C9, C10, C11 | ต่อยอดคุณค่า/แม่นยำ + ปิด known limitations |
| 🟢 P3 | A8, A9, B2, B3, B5, B6, B7, B8, C5, C7, C8 | ระยะยาว / ทางเลือก |

---

_อัปเดตล่าสุด: 2026-05-31 · อ้างอิง v1.5.0 — โปรดติ๊ก checkbox และปรับ priority เมื่อความคืบหน้าเปลี่ยน_
