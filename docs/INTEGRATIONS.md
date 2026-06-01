# External integrations & roadmap connectors

Status of the "ecosystem" roadmap items (category B). Two are implemented as
tested, pluggable interfaces; three are documented designs to be built behind
feature flags once the prerequisites (partners, infra, research) are in place.

## ✅ B2 — SMS report gateway (implemented)

People without the app can text a suspicious URL and get a verdict back.

- Endpoint: `POST /api/v1/sms/inbound` (mounted only when `SMS_INBOUND_SECRET` is set).
- Accepts JSON (`{from, body, secret}`) or Twilio-style form (`From`/`Body`),
  authenticated by a shared secret (`X-SMS-Secret` header or `secret` field).
- Flow: extract URL → unshorten (SSRF-guarded) → score → persist → return a short
  Thai reply (`app/integrations/sms.py`, `routers/integrations.py`).
- Provider abstraction: `SmsProvider` protocol (`NullSmsProvider` default — the
  webhook response carries the reply; swap in Twilio/Thai aggregator to push).
- Tests: `tests/test_integrations.py`.

Provider setup: point your SMS provider's inbound webhook at
`https://<host>/api/v1/sms/inbound` and configure it to send `SMS_INBOUND_SECRET`.

## ✅ B3 — Government connector (email/CSV intake implemented)

Forward confirmed phishing to ETDA 1212 / Cyber Police 1441. Neither exposes a
public submission API, so the working channel is **email**: a CSV digest is
mailed to the agency's intake mailbox.

- `GovernmentConnector` protocol: `forward_report()`, `forward_reports()` (batch),
  `fetch_blocklist()` (`app/integrations/government.py`). Selected via
  `GOV_CONNECTOR` — `stub` (default, logs only) or `email`.
- **`EmailIntakeConnector`** builds an `EmailMessage` with a CSV attachment
  (`url,score,closest_domain,reason`) and sends it via SMTP (STARTTLS + login).
  Configured by `GOV_EMAIL_*` (host/port/user/password/from/to); returns False
  (logs a warning) when not fully configured, and never throws into the caller.
- **Forwarding job**: `python -m scripts.gov_forward --since-days 1` (or
  `make gov-forward`) collects recent phishing verdicts (deduped by URL) and
  hands them to the connector. Schedule it daily (cron / Render cron job).
  Preview without sending: `--dry-run`.
- `fetch_blocklist()` returns `[]` for email (push-only); a future HTTP/API
  connector can implement the same protocol and pull a blocklist into feed
  ingestion / the whitelist deny side.
- **Before going live**: an MOU with the agency, a PDPA review of what is sent,
  and an audit log of forwarded batches.
- Tests: `tests/test_integrations.py`.

## 🔜 B5 — Federated learning (design)

Goal: combine phishing signal across agencies **without sharing raw URLs**.

- Each participant computes **aggregate counts** over the shared 42-feature
  schema (e.g. histogram of `min_edit_distance`, rule-hit rates, label mix) on
  its local traffic and submits only those aggregates.
- A coordinator averages aggregates (optionally with secure aggregation / DP
  noise) to update shared priors or recalibrate thresholds — never exchanging
  URLs or per-record data.
- Prerequisites: a privacy review (PDPA), a signed data-sharing MOU, and a
  secure-aggregation transport. Implement behind `FEDERATED_ENABLED` once those
  exist. No raw-URL egress is the hard invariant.

## 🔜 B6 — Visual fingerprinting (design)

Goal: catch pixel-clones of real agency login pages.

- A headless-browser worker screenshots a gray-zone URL and compares a perceptual
  hash (pHash/SSIM) against a library of genuine agency-page templates; a close
  match on a non-official host raises the score.
- Cost: high latency + a browser in the path, so it must be an **opt-in feature
  flag** (`VISUAL_FINGERPRINT_ENABLED`) running asynchronously off the hot path,
  similar to the existing content-check gray-zone fallback.
- Prerequisites: a maintained template library and a sandboxed render worker.

## 🔜 B8 — IP/ASN-level reputation (design)

Goal: reputation beyond the URL/host level.

- Add a `DomainReputation`-style store keyed by **IP and ASN** (resolve host →
  IP → ASN), accumulating verdict history per IP/ASN so a known-bad hosting
  range raises new URLs' scores even on first sighting.
- Feed it from the existing verdict stream and external blocklists; expose as new
  features in a future schema version (retrain + ML gate required).
- Prerequisites: an ASN lookup source (e.g. Team Cymru / MaxMind) and a schema
  bump — sequenced after the current 42-feature schema, behind the normal
  retrain/eval gate so Thai recall cannot regress.
