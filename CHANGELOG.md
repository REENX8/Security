# Changelog

All notable changes to this project are documented here.

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
and the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

The repository version is tracked centrally in [`VERSION`](VERSION); the
backend Python package, the `phish-features` package, the Vite dashboard
and the browser extension all derive their reported version from that file
or mirror it explicitly.

---

## [Unreleased]

### Fixed
- **`has_login_keyword` matched the hostname, not just the path (v1.8.0 root
  FP cause).** The extractor tokenised the WHOLE URL string, so every
  legitimate auth host (`login.microsoftonline.com`, `accounts.google.com`,
  `support.apple.com`, `secure.bangkokbank.com`) carried the credential flag.
  This poisoned the model feature AND five credential rules — most damaging in
  production where TLS is on: `HTTPS_LOOKALIKE` hard-pinned *phishing* for any
  Let's Encrypt site with a login keyword anywhere in the URL. The flag now
  comes from path+query only, per the documented schema contract.
- **Benign-looking signals were phishing-only in training data.** `gen_legit`
  never produced cheap TLDs, SSO/OAuth login portals, brand mentions in
  content paths, hashed CDN asset paths, utm-heavy queries, or two-level
  subdomains — so the model learnt each as a near-deterministic phishing
  tell (e.g. `console.cloud.google.com` scored 0.87 from `num_subdomains=2`
  alone). New hard-benign archetypes in the synthetic generator cover all of
  these (~35% of legit rows).
- **`path_brand_hit` flagged incidental brand mentions.** Loose sub-token
  matching hit content slugs (`/news/obec-budget-2026`) and asset names
  (`/obec-logo.png`). The brand must now be a full path segment; the query
  string is also searched so redirect bait
  (`track.evil.com/click?url=https://obec.go.th/...`) is caught — a site
  redirecting to itself is exempt.
- **Homoglyph→typosquat promotion lacked FP guards.** The confusable-fold
  promotion now applies the same `label_len >= 4` + proportional-distance
  gates as `Whitelist.whitelist_features`, so short or only loosely similar
  non-Latin labels are no longer promoted.
- **Phishing `redirect_chain` training rows never set `path_redirect_hit`.**
  The archetype emitted bare-domain params (`?to=obec.go.th`), so the
  open-redirect feature only ever fired on benign SSO rows. The archetype now
  emits full-URL params and tracker-style hosts (`track.<rand>.com`).
- **False positives on legitimate brand portals.** With WHOIS/TLS unavailable
  (fail-open), the model alone blocked real login/console subdomains of major
  brands — `login.microsoftonline.com`, `signin.aws.amazon.com`,
  `console.cloud.google.com` — as phishing. New `KNOWN_GOOD_DOMAIN` rule pins
  safe for an exact host or *true subdomain* of a curated corporate-controlled
  domain (uses the parsed host, so the `@`-trick and lookalikes like
  `google.com.evil.xyz` / `secure-google.com` do NOT match; user-content hosts
  such as `amazonaws.com`/`github.io` are deliberately excluded). A phishing
  pin from another rule still wins. Benign FP rate on the new holdout:
  3/46 → **0/46**; adversarial detection unchanged at 110/110.
- **Feed → retrain connection was dead.** `feed_ingestion` now stamps every
  persisted feed verdict with `features["feed_source"] = <source name>`. The
  retrain trigger (`check_feed_accumulation`) and the training-corpus export
  (`ml_pipeline/feed_training_export.py`) both filter on `feed_source`; without
  the tag they saw zero feed rows and never fired.
- **Feed accumulation retrain was never invoked.** `FeedPoller.poll_once` now
  calls `check_feed_accumulation` after each poll cycle (gated + debounced
  internally), so a fresh batch of confirmed feed phishing actually drives a
  retrain instead of waiting on the periodic timer.

### Changed
- **Feature schema v1.7.0 → v1.8.0 (retrain required; model artifacts
  regenerated).** Two appended features: `num_strong_login_keywords` (count
  of strong-tier credential keywords) and `has_high_risk_tld` (free /
  heavily-abused registries). `LOGIN_KEYWORDS` is now split into
  `LOGIN_KEYWORDS_STRONG` (login/verify/password/otp/...) and
  `LOGIN_KEYWORDS_WEAK` (support/service/account/... — common on legitimate
  portals); `SUSPICIOUS_TLDS` gains the `HIGH_RISK_TLDS` subset (.tk/.ml/
  .icu/.top/... vs merely-cheap .online/.site/.info).
- **Credential rules require the strong keyword tier** (`TYPOSQUAT_CRED`,
  `IDN_CRED`, `IP_CRED`, `SELF_SIGNED_CRED`, `REDIRECT_CONFUSION`), and
  TLD-based pins require the high-risk tier (`TYPOSQUAT_CRED` extra signal,
  `PATH_BRAND_BAIT` — weak-tier TLDs now only raise the score).
  `HTTPS_LOOKALIKE` no longer fires on a bare login keyword: it pins only
  for a typosquat host and soft-raises for brand-in-path.
  `REDIRECT_CONFUSION` also fires on brand-in-redirect (`path_brand_hit`).
- Metrics after retrain: Thai-targeting holdout recall **100% (378/378)**
  (unchanged), benign-holdout FP rate **0/68** at both thresholds,
  adversarial suite 100%, generic cross-check 86/90.

### Added
- **Benign false-positive gate in the ML pipeline.** `make evaluate-gate` now
  also fails when any URL in the expanded `data/benign_holdout.csv` (68 rows;
  new hard cases: SME sites on cheap TLDs, SSO redirects, brand-in-path news
  URLs, hashed CDN assets, utm-heavy queries) scores ≥ 0.7 from the raw model
  (`BENIGN_FP_MAX_PHISHING_RATE`, env-overridable). Results land in
  `reports/benign_fp_metrics.json` and `evaluation_summary.json` under
  `benign_fp`. Previously every train-time gate measured recall only — a
  retrain could trade benign precision away unnoticed.
- **Per-user check history.** `POST /api/v1/check` and `/check/batch` attribute
  the stored check to the signed-in user (JWT `user_id`) via the new
  `optional_user_id` dependency, incrementing `User.check_count` atomically.
  New `GET /api/v1/me/history` (requires a user JWT via `require_user_id`)
  returns only the caller's own checks (`crud.get_history(user_id=...)`);
  the admin `GET /api/v1/history` remains unscoped.
- **ML detection — two high-precision rules.** `ENCODED_IP_HOST` (+0.45, pin
  phishing) consumes the previously rule-less `has_encoded_ip` feature to flag
  hex/octal IP-literal hosts; `SELF_SIGNED_CRED` (+0.35, pin phishing) flags a
  self-signed certificate on a credential-collection page.
- **Battle testing.** New `encoded_ip_host` evasion class in
  `data/adversarial_urls.csv` (100 → 110 cases); `tests/test_adversarial.py`
  gains a per-technique floor (no single technique may drop below 50%) on top
  of the existing 70% overall gate. Current rate: 110/110 (100%).
- **Benign false-positive gate** (`data/benign_holdout.csv`, 46 real
  legitimate sites incl. login/subdomain stress cases; `tests/test_benign_fp.py`):
  hard gate of 0 phishing FPs + soft cap on the suspicious rate, so a future
  change that starts blocking normal sites fails CI.
- **SLA.** Detection-quality table documents the per-technique adversarial
  floor and the benign false-positive gate.

## [1.7.0] — 2026-06-08

### Added
- **Real phishing feed → training pipeline** (`ml_pipeline/feed_training_export.py`): exports verified feed URLs from the DB to `data/live_feed_phishing.csv` (80% train / 20% holdout split, strictly by timestamp to prevent leakage)
- **User accounts** with JWT authentication: `POST /api/v1/auth/register`, unified `POST /api/v1/auth/login` (admin + user), `GET /api/v1/auth/me`; `User` model with role, active flag, check_count
- **Adversarial URL test suite** (`data/adversarial_urls.csv`): 100 hand-crafted evasion URLs across 10 techniques; CI gate via `tests/test_adversarial.py` (70% detection rate required)
- **Adversarial evaluation script** (`ml_pipeline/adversarial_eval.py`): standalone eval with per-category breakdown and `reports/adversarial_eval.json` output
- **SLA definition** (`docs/SLA.md`): availability, latency, detection quality targets, incident response times, data retention policy
- **Operational runbook** (`docs/RUNBOOK.md`): step-by-step procedures for FP incidents, FN incidents, model not ready, rollback, feed failure, DB capacity, auto-rollback events
- **Auto-rollback after promotion**: after a successful retrain, evaluates Thai holdout recall and restores the previous model if recall < `recall_rollback_threshold` (default 0.82)
- **Feed accumulation retrain trigger** (`check_feed_accumulation`): triggers retrain when ≥ 50 new feed phishing URLs accumulate since last retrain
- **Reload-model admin endpoint** (`POST /api/v1/admin/reload-model`): hot-swaps model, whitelist, and flushes cache without restart
- **User management admin endpoints**: `GET /admin/users`, `PATCH /admin/users/{id}/role`, `DELETE /admin/users/{id}`
- **New Prometheus metrics**: `phish_model_rollback_total`, `phish_user_registrations_total`, `phish_adversarial_detection_rate`
- **New alert rules**: `PhishFeedPollingFailed`, `PhishModelRolledBack`, `PhishAdversarialRateLow`
- New lexical features: `has_encoded_ip` (hex/octal IP notation), `path_redirect_hit` (open-redirect pattern)
- New rules: `SUBDOMAIN_CAMOUFLAGE` (+0.35, pin=phishing), `REDIRECT_CONFUSION` (+0.20)
- Alembic migration `0003_user_accounts` (users table + user_id FK on url_checks)
- `email-validator` dependency added

### Changed
- **Feature schema**: v1.6.0 → v1.7.0 (2 new features: 44 → 46)
- `collect_dataset.py`: consumes `data/live_feed_phishing.csv` when available
- `evaluate.py`: reports live-feed holdout recall (`data/live_feed_holdout.csv`) with 80% gate
- `config.py` (ml_pipeline): new constants `LIVE_FEED_CSV`, `LIVE_FEED_HOLDOUT_CSV`, `FEED_RETRAIN_THRESHOLD`, `FEED_EXPORT_MIN_AGE_HOURS`, `LIVE_FEED_RECALL_MIN_THRESHOLD`
- `config.py` (backend): new fields `recall_rollback_threshold`, `feed_retrain_threshold`
- `phish_features/homoglyph.py`: 11 additional confusable mappings (Devanagari, Cyrillic, IPA)
- Auth router: supports both admin credentials and user email+password login
- Model retrained against schema v1.7.0

### Security
- Rate limit on registration endpoint (3/minute per IP)
- SSRF guard applied to all webhook URLs (existing, enforced in notifier)
- JWT claims now include `user_id` and `role` for user accounts

## [Unreleased]

## [1.6.1] — ML quality, security hardening (2026-06-08)

### Added

- **HTTPS_LOOKALIKE rule** (`phish_features/rules.py`): fires when a URL uses
  HTTPS with a free DV certificate (Let's Encrypt) alongside a typosquat, brand
  path hit, or login keyword. Delta +0.30, pin phishing. Closes the biggest rule
  gap for modern phishing kits that obtain free TLS certs to appear legitimate.
- **LOGIN_KEYWORD_DENSE rule** (`phish_features/rules.py`): fires when ≥ 3
  credential keywords appear in the URL (`login`, `verify`, `account`, etc.).
  Delta +0.25, no hard pin. Catches credential-stuffed phishing kits that use
  benign-looking hosts.
- **Feedback deduplication** (`ml_pipeline/collect_dataset.py`): same URL
  reported multiple times is now deduplicated via majority-vote before training,
  preventing popular-campaign over-representation. Tied verdicts are discarded.
- **Temporal decay for feedback labels** (`ml_pipeline/collect_dataset.py`,
  `ml_pipeline/feedback_retrain.py`): each feedback row carries an exponential
  decay weight (half-life 90 days) so stale verdicts count less during training.
- **A/B model comparison before promotion** (`ml_pipeline/feedback_retrain.py`):
  before promoting a staged model, its Thai holdout recall is compared to the
  currently-live model's recall. Promotion is blocked if the staged model's recall
  drops more than 2 pp below the live model, preventing silent regressions.
- **Calibration Brier score** (`ml_pipeline/evaluate.py`): Brier score computed
  on the test split; reliability diagram saved to `reports/calibration_curve.png`.
  A WARNING is logged if Brier > 0.10.
- **Reproducible calibration CV** (`ml_pipeline/train.py`): `CalibratedClassifierCV`
  now uses `StratifiedKFold(random_state=RANDOM_SEED)` so fold splits are identical
  across runs.
- **Sample weight pass-through** (`ml_pipeline/train.py`, `feature_engineering.py`):
  `sample_weight` column from `dataset.csv` is passed to `model.fit()`, enabling
  temporal decay to influence training.
- **Global RNG seed** (`ml_pipeline/config.py`): `random.seed(42)` and
  `numpy.random.seed(42)` locked at import time to improve reproducibility.
- **Per-URL debug logging** (`backend/app/ml/scorer.py`): each scored URL emits
  a `DEBUG`-level log line with score, label, and rules that fired. Enabled with
  `LOG_LEVEL=DEBUG`; zero overhead otherwise.
- **False-negative/false-positive rate gauges** (`backend/app/metrics.py`,
  `backend/app/retrain_trigger.py`): Prometheus gauges `phish_false_negative_rate`
  and `phish_false_positive_rate` updated at each auto-retrain trigger from
  trailing 7-day feedback window.
- **Rule firing counter** (`backend/app/metrics.py`, `backend/app/ml/scorer.py`):
  `phish_rule_fired_total{rule_id}` Counter incremented each time a named rule
  fires, enabling audit of which rules are most active.

### Fixed

- **Timing-safe username comparison** (`backend/app/routers/auth.py`): replaced
  `==` with `secrets.compare_digest` to resist timing-based username enumeration.
- **JWT subject validation** (`backend/app/deps.py`): `sub` claim is now compared
  against `settings.admin_username` instead of truthy check — any non-empty JWT
  subject can no longer bypass authentication.
- **Webhook SSRF** (`backend/app/notifier.py`): webhook URL is checked with
  `net_guard.url_is_safe()` before the outbound POST; private/loopback/reserved
  addresses are rejected with a `SSRF_BLOCKED` delivery record.
- **Retrain race condition** (`backend/app/retrain_trigger.py`): the
  check-then-set on `retrain_in_progress` is now wrapped in an `asyncio.Lock`
  so concurrent feedback submissions cannot launch duplicate retrains.
- **Whitelist hot-reload thread safety** (`backend/app/routers/admin.py`,
  `backend/app/main.py`): a `threading.Lock` (stored on `app.state.whitelist_lock`)
  protects in-place whitelist replacement from concurrent reads in the scorer
  threadpool.

## [1.6.0] — visual fingerprinting + IP/ASN reputation + ML-ops gates (2026-06-07)

### Added

- **B6 — Visual fingerprinting** (`app/visual/`): gray-zone URLs can be
  screenshotted and perceptually hashed (pure-Python dHash) against a library of
  genuine agency-page templates; a close match on a non-official host raises the
  score by a bounded `[+0.15, +0.35]`. SSRF-guarded, fail-open, gray-zone only.
  Off by default (`VISUAL_FINGERPRINT_ENABLED`); pluggable renderer with a no-op
  `NullRenderer` default and an opt-in `PlaywrightRenderer` (`pip install .[visual]`).
- **B8 — IP/ASN reputation** (`app/ip_reputation*.py`, `app/integrations/asn.py`):
  per-IP and per-ASN verdict history accumulates from the verdict stream
  (migration `0002_ip_asn_reputation`) and is fed to the model as the
  `ip_reputation_score` / `asn_reputation_score` features (**schema v1.6**), so a
  hosting range with a bad track record raises a brand-new URL even on first
  sighting. Off by default (`IP_REPUTATION_ENABLED`); pluggable ASN provider
  (`NullAsnProvider` default, opt-in Team Cymru DNS). Retrain passes the
  Thai-recall ≥ 0.85 gate (unknown reputation is class-neutral).

### Changed

- **Feature schema bumped to v1.6.0** (42 → 44 features): adds
  `ip_reputation_score` and `asn_reputation_score`. The committed model is
  retrained; behaviour is unchanged when `IP_REPUTATION_ENABLED` is off (the new
  features impute to -1 / "unknown" everywhere).
- **Independent real-world holdout** (`data/real_phish_holdout.csv`,
  `scripts/collect_real_phish_holdout.py`): a curated phishing sample with
  zero training-host overlap — the honest generalisation metric (reported, not
  gated), surfaced in `evaluation_summary.json`. Guarded by
  `tests/test_real_holdout.py`.
- **Load-test CI gate**: `loadtest-e2e` job boots the backend and runs
  `deploy/loadtest/k6_check_ci.js` with a CI-appropriate p95 threshold.
- **Threshold-tuning evidence in CI**: `ml-gate` runs `tune_threshold` and
  uploads `threshold_analysis.json`; `docs/ML_OPS.md` documents the
  shadow-A/B → promote process (and fixes the `phish_threshold_ab_total`
  variant label in the PromQL example).

## [1.5.0] — schema + scale + continuous retraining + auth hardening (2026-05-30)

### Fixed

- **`/check` + `/check/batch` returned 422 for every request** — combining
  `from __future__ import annotations` with slowapi's `@limiter.limit` wrapper
  stopped FastAPI from resolving the request-body models. Dropped the future
  import in the rate-limited routers (`check`, `auth`, `feedback`).
- **SQLite backend was broken** — a hard-coded asyncpg-only connect arg
  (`statement_cache_size=0`) raised `TypeError` on aiosqlite, so the test suite
  and `make run` quickstart could not reach the DB. Now applied only when the
  URL targets asyncpg.
- **Login crashed on a fresh install** — `passlib[bcrypt]==1.7.4` left bcrypt
  unpinned; a clean install pulled bcrypt 5.x, which passlib 1.7.4 cannot read.
  Pinned `bcrypt==4.0.1`.
- **Case-insensitive search broke on SQLite** — `.ilike()` degrades to
  case-sensitive `LIKE` on SQLite; switched to `func.lower(col).like(...)` in
  history/whitelist/domain/campaign search so it works on both dialects.

### Security

- **Rate-limited `/api/v1/auth/login`** to 5/minute per IP to resist password
  brute-forcing.
- **Rate-limited `POST /api/v1/feedback`** to 10/minute per IP to resist
  feedback-table spam / model poisoning.

### Added

- **Feature schema v1.5.0 (37 → 42 features)** — 5 new features that add signal
  WITHOUT any new network lookup: `cert_is_lets_encrypt`, `cert_validity_days`,
  `cert_san_count` (parsed from the SAME TLS handshake — free 90-day DV certs
  over-index on phishing), `digit_to_letter_ratio`, and
  `host_has_brand_and_suspicious_tld` (a brand impersonated on a cheap/abused
  TLD). The previously-missed `thaid-app.net/auth/login` is now caught →
  **Thai-holdout recall 99.7% → 100% (378/378)**, 95% CI [0.990, 1.000].
- **Optional Redis-backed `/check` cache** — set `REDIS_URL` to share the cache
  across replicas; falls back silently to the in-process TTLCache when Redis is
  unset or unreachable. Added a `redis:7-alpine` service to docker-compose.
- **Continuous, gated feedback retraining** — `collect_dataset` now folds
  `data/feedback_labels.csv` into the TRAINING set; `feedback_retrain` trains
  into `models/staging`, runs the eval gate there, and promotes (atomic, with a
  `models/previous` backup) only when the gate passes. New API-key-protected
  `POST /api/v1/admin/retrain` runs it and hot-swaps the scorer with no restart.
  `PHISH_MODELS_DIR` / `PHISH_REPORTS_DIR` let train/evaluate target staging.
- **Committed generic-phishing seed + holdout** — a deterministic OpenPhish/URLhaus
  snapshot (`data/generic_phishing_seed.csv`, 300 non-Thai URLs) is split 70/30 with
  a fixed seed. Up to `PHISH_GENERIC_TRAIN_MAX` (default 90) rows feed training so
  the decision boundary stays Thai-centric; the 90-URL holdout is evaluated offline
  by `make evaluate`. This raises generic recall from ~57% to **91.11% (82/90)**
  while keeping Thai recall at 100% (378/378). NB: ~24% host overlap between the
  generic train/holdout split makes this an in-distribution cross-check, not an
  independent test of novel phishing.
- **Docs metric de-hardcoding** — `scripts/sync_docs_metrics.py` injects the
  numbers from `reports/evaluation_summary.json` into sentinel-wrapped spots in
  the docs; `make sync-docs` / `make sync-docs-check` (run in CI) keep them from
  ever drifting again.
- **Extension store-readiness check** — `build_extension.py --check` (run in CI)
  validates version + manifest references + that no docs/source-maps leak into
  the package; extension bumped to v1.2.0.

### Changed

- **Generic-phishing holdout is now a committed, reproducible cross-check rather
  than a feed-dependent headline.** The system is deliberately tuned for
  Thai-targeting (positive alignment score), so generic recall (91.11%) sits below
  the Thai holdout (100%) by design. The earlier hardcoded "98.9% (89/90)" claim —
  which came from a transient live-feed snapshot — was replaced by the deterministic
  committed-seed number that `make evaluate` reproduces offline.
- **`make install`** now also installs `pytest-asyncio` (matches CI), so the
  async tests collect locally.

---

## [1.4.0] — NSC 2026 Presentation Round prep (2026-05-28)

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

[1.6.0]: https://github.com/reenx8/security/releases/tag/v1.6.0
[1.5.0]: https://github.com/reenx8/security/releases/tag/v1.5.0
[1.4.0]: https://github.com/reenx8/security/releases/tag/v1.4.0
[1.3.0]: https://github.com/reenx8/security/releases/tag/v1.3.0
[1.2.0]: https://github.com/reenx8/security/releases/tag/v1.2.0
[1.1.0]: https://github.com/reenx8/security/releases/tag/v1.1.0
[1.0.0]: https://github.com/reenx8/security/releases/tag/v1.0.0
