# Changelog

All notable changes to this project are documented here.

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
and the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

The repository version is tracked centrally in [`VERSION`](VERSION); the
backend Python package, the `phish-features` package, the Vite dashboard
and the browser extension all derive their reported version from that file
or mirror it explicitly.

---

## [Unreleased] — NSC 2026 Presentation Round prep (2026-05-28)

### Added

- **Disclaimer endpoint + UI integration** — `GET /api/v1/disclaimer` คืนข้อความ
  ข้อตกลงในการใช้ซอฟต์แวร์สองภาษาตามที่ NSC booklet หน้า 44 กำหนด;
  dashboard มีหน้า `/about` ใหม่ที่แสดง disclaimer + ข้อมูลโครงการ; popup
  ของ extension มีลิงก์ "เกี่ยวกับ / Disclaimer" ไปยังหน้า `/about`; README.md
  มี section Disclaimer
- **Demo automation scripts** — `scripts/demo_setup.sh` boot backend +
  seed + verify; `scripts/demo_reset.sh` reset DB ก่อนสาธิตรอบใหม่;
  `scripts/demo_verify.py` ตรวจ 6 golden URL ว่า verdict ตรงตามคาด;
  Makefile target `demo-setup` / `demo-reset` / `demo-verify`
- **NSC presentation-day documents** — `docs/nsc2026/11_demo_flashcards.md`
  (ลำดับ demo + backup plan + URL ตัวอย่าง 7 patterns) และ
  `docs/nsc2026/12_qa_cheatsheet.md` (คำตอบ Q&A กรรมการ พิมพ์ A5)

### Changed

- **`02_full_report.md`** — เติมเนื้อหาเต็มในทุก section ที่เคย placeholder ว่า
  "(เหมือนข้อเสนอ)": วัตถุประสงค์/เป้าหมาย, story board (พร้อม ASCII
  architecture), เครื่องมือพัฒนา, software specification (I/O + 11 endpoints
  + design tree), ขอบเขต/ข้อจำกัด, เอกสารอ้างอิง 12 รายการ; เพิ่ม section
  ใหม่ "เปรียบเทียบกับโซลูชันที่มีอยู่" (vs Google Safe Browsing / SmartScreen
  / ETDA) และ "การสอดคล้องกับ Sustainable Innovation Theme" 4 มิติ

---

## [1.3.0] — 2026-05-27

### Added

- **Thai phishing seed corpus expanded 215 → 1,261 URLs** — `scripts/collect_thai_phishing_seed.py` ได้ programmatic brand-expander (`_BRAND_DEFS` + `_expand_brand`) ที่ผลิต 8 รูปแบบ phishing-style URL ต่อแบรนด์อย่าง deterministic ครอบคลุม 160+ แบรนด์ไทย (commercial banks, state banks, mobile wallets, 14 ministries, central banks, universities, utilities, telecom, logistics, e-commerce); hand-curated list เดิม 215 รายการยังถูกเก็บไว้และมาก่อน expansion เสมอ
- **Thai-targeting holdout 66 → 378 URLs** — 30% split ของ seed ใหม่; 95% CI ของ recall แคบลงจาก [0.95, 1.00] → [0.985, 1.000] ทำให้ตัวเลข 99.7% ไม่ใช่ผลของ sample เล็กอีกต่อไป
- **`scripts/audit_seed_coverage.py`** — รายงานสถิติแบรนด์/ccTLD/pattern type ของ seed + holdout (ไว้ตรวจว่าไม่มีแบรนด์ครอบงำ และครอบคลุม `go.th`/`ac.th`/`or.th`/`co.th` ครบทั้ง 4); เรียกได้ที่ `make seed-audit` หรือ `python -m scripts.audit_seed_coverage`
- **`test_thai_holdout_has_minimum_size`** ใน `tests/test_seed_corpus.py` — guard ใหม่ที่ fail ถ้า holdout หล่นต่ำกว่า 300 rows
- **Makefile target `seed-audit`** — เรียก `python scripts/audit_seed_coverage.py` แบบทางลัด

### Changed

- `PER_BRAND_CAP` ใน `scripts/collect_thai_phishing_seed.py` 4 → **8** — ตรงกับ test guard เดิมที่ตั้งไว้แล้ว และเปิดทางให้ seed expansion ทำงานได้เต็มที่
- `tests/test_seed_corpus.py` MIN_TOTAL_ROWS 200 → **900**, MIN_DISTINCT_BRANDS 50 → **130** — lock-in การขยายของ v1.3.0
- Test suite: 206 → **207 tests** (+1 holdout-size guard)
- Thai-targeting recall: **99.7% (377/378)** บน holdout ที่ใหญ่ขึ้น 5.7 เท่า — 1 missed URL (`thaid-app.net/auth/login`) score 0.19 (suspicious-TLD ไม่ทำงานเพราะ `.net` ไม่ใช่ cheap TLD); production target ≥ 0.85 ยังคงเดิม
- README badge Thai recall: 100% (66/66) → **99.7% (377/378)**

### Notes

- Schema version ของ `phish_features` ยังเป็น v1.4.0 (37 features) ไม่เปลี่ยน — v1.3.0 เป็น data + dataset release ล้วน ๆ ไม่กระทบสัญญา feature-matrix
- `data/dataset.csv`, `data/thai_phish_holdout.csv` regenerate แล้วใน commit นี้; โมเดล `.pkl` ใน `models/` retrain ใหม่บน corpus 12,000 rows

---

## [1.2.0] — 2026-05-26

### Added

- **URL Unshortener** — `backend/app/unshorten.py` ขยาย short link (bit.ly, t.co, cutt.ly, lin.ee, t.me ฯลฯ 18 providers) ด้วย async HEAD request ก่อนส่ง feature extraction; เปิดด้วย `ENABLE_URL_UNSHORTENING=true` (default on)
- **LINE Messaging API Bot** — `backend/app/routers/line_bot.py` webhook ที่ `/api/v1/line/webhook`; ตรวจ URL ที่ผู้ใช้ส่งใน LINE chat → ตอบกลับเป็นภาษาไทยพร้อม verdict + เหตุผล; รองรับ HMAC-SHA256 signature validation; เปิดด้วย `LINE_CHANNEL_TOKEN` + `LINE_CHANNEL_SECRET`
- **Content-based Fallback** — `backend/app/content_check.py` ดึง HTML ของหน้าเว็บสำหรับ URL ในโซนเทา (score 0.3–0.7) และตรวจ brand-in-title, password field; SSRF protection ด้วยการ reject private IP; เปิดด้วย `GRAY_ZONE_CONTENT_CHECK=true`
- **Feedback-driven Auto-retrain** — `ml_pipeline/feedback_retrain.py` export confirmed feedback จาก DB → trigger `ml_pipeline.train` อัตโนมัติ; รันด้วยมือด้วย `python -m ml_pipeline.feedback_retrain [--dry-run]`; เปิด background task ด้วย `FEEDBACK_RETRAIN_ENABLED=true`
- Settings ใหม่: `ENABLE_URL_UNSHORTENING`, `UNSHORTEN_TIMEOUT`, `GRAY_ZONE_CONTENT_CHECK`, `CONTENT_CHECK_TIMEOUT`, `LINE_CHANNEL_TOKEN`, `LINE_CHANNEL_SECRET`, `FEEDBACK_RETRAIN_ENABLED`, `FEEDBACK_RETRAIN_INTERVAL_HOURS`

### Changed

- Test suite: 177 → **206 tests** (+29: unshorten, content_check, line_bot, feedback_retrain)

---

## [1.1.0] — 2026-05-26

### Added

- **Feature schema v1.4.0** — 4 features ใหม่คำนวณจาก URL string ล้วน: `num_login_keywords` (count), `query_param_count`, `path_entropy`, `host_token_count` (index 33–36)
- **Real-time external threat feed ingestion** — `FeedPoller` background service poll OpenPhish + PhishTank ทุก N นาที; deduplication ผ่าน `FeedIngestionRecord`; เปิดด้วย `EXTERNAL_FEEDS_ENABLED=true`
- New models `ExternalFeedSource` และ `FeedIngestionRecord` ใน database schema
- Admin endpoints `GET /api/v1/feed/sources` และ `POST /api/v1/feed/sources/{id}/poll`
- Prometheus counters `phish_feed_urls_ingested_total` และ `phish_feed_poll_errors_total`
- 3 synthetic phishing archetypes: `long_random_subdomain`, `double_dash_stuffed`, `token_stuffed_path`
- Optuna hyperparameter search: `python -m ml_pipeline.train --tune`
- Thai phishing seed corpus 175 → **215 URLs** (+40 ครอบคลุม 10 แบรนด์)
- `httpx>=0.27` ใน backend/requirements.txt สำหรับ async HTTP

### Changed

- Training dataset 6,000 → **12,000 rows** (balanced)
- Thai holdout recall: 100% บน **66 URLs** (เพิ่มจาก 53)
- Generic phishing recall: **98.9% (89/90)** — metric ใหม่จาก real feed cache
- Test suite: 162 → **177 tests** (10 ใหม่สำหรับ feed ingestion)

### Fixed

- `FeedPoller` ใช้ `asyncio.gather` + `return_exceptions=True` ป้องกัน 1 source ล้มเหลวทำให้ source อื่นหยุดทำงาน

---

## [1.0.0] — 2026-05-25

First public release. The system is **production-ready** for protecting
Thai government, educational and state-bank brands against URL-level
phishing, with documented limits and a hardening checklist for operators.

### Highlights

- **End-to-end detection stack**: shared `phish_features` package (single
  source of truth for the 26-feature model contract), FastAPI backend
  with rate limiting and Prometheus metrics, Chrome / Edge / Brave /
  Opera / Firefox 121+ Manifest V3 extension with full-page interstitial,
  and a 6-page React 18 dashboard.
- **Thai-targeting recall 98.1%** (52/53) on a 53-URL Thai-targeting
  holdout the model has never seen, with a CI gate that fails any pull
  request that drops below 0.85. Generic-phishing recall is 92.2% as a
  cross-check.
- **IDN / homoglyph defence** (feature schema v1.2.0): Punycode (`xn--`)
  decoding, mixed-script detection (Latin + Cyrillic / Greek / Fullwidth)
  and a confusable-fold edit distance so `chulа.com` (Cyrillic `а`)
  collapses to distance 0 against `chula.ac.th`.
- **500+ trusted Thai-domain whitelist** auto-seeded into the database
  on first start, hot-reloadable through the admin API without restart.
- **Operator-grade defaults**: dual deploy paths (Docker Compose,
  standalone Docker image, Render Blueprint with one-click button),
  PostgreSQL with SQLite fallback, structured JSON logging via
  `LOG_FORMAT=json`, per-request `X-Request-ID` middleware, security
  response headers, graceful degradation if the database is unreachable.
- **142 automated tests** (unit + integration + golden + corpus) on every
  push, plus a dashboard build, Docker image build, extension package
  build and the ML primary-metric gate.

### Added

- `LICENSE` (Apache 2.0) and `NOTICE` with third-party attributions.
- `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `MAINTAINERS.md`.
- `VERSION` file as the single source of truth for the release number.
- GitHub issue forms (`bug`, `feature`, `false-positive`,
  `false-negative`), pull-request template, `dependabot.yml`,
  `CODEOWNERS`.
- `Makefile` with `install`, `test`, `lint`, `format`, `run`, `train`,
  `evaluate`, `extension`, `dashboard`, `docker`, `clean` targets.
- `.editorconfig`, `.pre-commit-config.yaml` and `ruff` configuration
  in `pyproject.toml`.
- Backend `app/middleware.py`: request-ID propagation, security headers
  (`X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`,
  `X-Frame-Options`), structured JSON access logs gated by `LOG_FORMAT`.
- Backend `/version` endpoint that returns the package + schema +
  feature-set version triple.
- CI `lint` job (ruff check + format-check) and an extension package
  artifact attached to every release tag.

### Changed

- `README.md` rewritten as a release-ready document with badges, a
  table of contents, a deploy button, a screenshots reference and
  consolidated metric tables.
- `backend/app/__init__.py` reads its version from `VERSION` so the
  package version always matches the published release.
- Extension manifest version bumped to **1.1.1** and the manifest
  description aligned with the store-listing copy.

### Security

- Default API key is `dev-local-key-change-me`; the README, the
  `.env.example`, the Docker entrypoint and the Render Blueprint all
  highlight the requirement to rotate this before exposing the API.
- Outbound network calls (WHOIS, TLS) are timeout-guarded and silently
  fall back to "unknown" defaults — they never block scoring.
- Rate limiting is per-API-key by default, with a per-IP fallback when
  no key is supplied.

---

## Pre-1.0 milestones (for context)

The pre-1.0 commit history captures the path to this release:

- Synthetic + curated Thai phishing seed corpus that survives the
  primary-metric gate.
- WHOIS / TLS network features with timeout protection.
- IDN / homoglyph schema v1.2.0 closing the Cyrillic-lookalike gap.
- Render Blueprint with cross-region resilience.
- Chrome Web Store submission pack (zip builder, privacy policy,
  permission justification).

[1.0.0]: https://github.com/reenx8/security/releases/tag/v1.0.0
