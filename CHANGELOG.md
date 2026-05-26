# Changelog

All notable changes to this project are documented here.

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
and the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

The repository version is tracked centrally in [`VERSION`](VERSION); the
backend Python package, the `phish-features` package, the Vite dashboard
and the browser extension all derive their reported version from that file
or mirror it explicitly.

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
