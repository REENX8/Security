# Security Policy

The Thai Phishing URL Detection System is a **defensive security tool**.
Vulnerabilities in defensive tooling matter because operators rely on the
system to protect end users from harm, so we take reports seriously and
publish fixes promptly.

## Supported versions

| Version | Status              | Security fixes |
|---------|---------------------|----------------|
| 1.0.x   | ✅ Actively supported | Yes            |
| < 1.0   | ❌ Pre-release        | No             |

Once 1.1 ships, 1.0.x will receive **security-only** fixes for at least
six months from the 1.1 release date.

## Reporting a vulnerability

**Please do not file public GitHub issues for security problems.**
Vulnerabilities should reach the maintainers privately first so end users
are protected before details become public.

Two private reporting channels are supported:

1. **GitHub Security Advisories** (preferred):
   <https://github.com/reenx8/security/security/advisories/new>
2. **Email**: contact the maintainers via the address listed in
   [`MAINTAINERS.md`](MAINTAINERS.md). Mark the subject line with
   `[SECURITY]`.

You should receive an acknowledgement within **3 business days**. We aim
to confirm or refute the report within **10 business days** and to ship a
fix within **30 days** for high-severity issues.

### What to include

A great report contains:

- a clear description of the vulnerability and its impact,
- a minimal reproducer (URL, payload, configuration),
- the version (commit hash or release tag) where the issue was observed,
- any suggested mitigation you have already verified.

### Coordinated disclosure

We follow a **90-day coordinated-disclosure window**. If we agree that
the issue is valid and reproducible:

1. We confirm a fix plan with you.
2. We prepare a patch on a private branch and a security advisory draft.
3. We request a CVE through GitHub Security Advisories when applicable.
4. The fix is released and the advisory published; we credit reporters
   who opt in.

If 90 days elapse with no fix and no negotiated extension, we welcome
public disclosure so users can mitigate.

## Out of scope

The following are **not** vulnerabilities in this project:

- A phishing URL that the model fails to flag. The README documents the
  measured recall on labelled holdouts; misses below 100% are expected.
  Please open a regular **false-negative** issue using the issue form
  instead (the report becomes a training-data candidate).
- A legitimate URL that is flagged as phishing. Same — please use the
  **false-positive** issue form.
- Findings from automated scanners that do not include a working proof
  of concept against the reference deployment.
- Vulnerabilities in third-party services you choose to integrate
  (Render, Postgres, browser stores, etc.) — please report those to the
  service operator.

## Operator security checklist

If you operate a deployment of this system, please review:

- Rotate `API_KEY` from the default `dev-local-key-change-me` **before**
  exposing the backend to any non-loopback address.
- Terminate the backend behind TLS (Caddy, nginx, Cloud Run, a managed
  load balancer, etc.).
- Restrict `CORS_ORIGINS` to the exact dashboard / extension origins you
  operate; do not leave the wildcard placeholder in `render.yaml`
  untouched.
- Lower `RATE_LIMIT` if you expect untrusted callers.
- Scrape `/metrics` and alert on `phish_model_ready == 0` so a missing
  model artifact is noticed before users are.
- Apply Postgres updates and rotate the `POSTGRES_PASSWORD` away from
  the default `phish` value in any production environment.
