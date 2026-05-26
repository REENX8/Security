# Changelog

All notable changes to this project are documented here.

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
and the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

The repository version is tracked centrally in [`VERSION`](VERSION); the
backend Python package, the `phish-features` package, the Vite dashboard
and the browser extension all derive their reported version from that file
or mirror it explicitly.

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
