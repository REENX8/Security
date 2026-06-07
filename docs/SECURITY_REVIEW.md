# Security Review — ROADMAP C6

Scope: SSRF in outbound fetches, injection in WHOIS/TLS feature extraction,
and authorization of admin routes. Reviewed against the v1.6.0 codebase
(re-checked for the v1.6.0 additions — B6 visual fingerprinting and B8 IP/ASN
reputation, both of which add outbound network paths; see finding 6).

## Findings & resolutions

### 1. SSRF in `unshorten.py` — FIXED (high)
The unshortener followed short-link redirects with httpx
`follow_redirects=True`, so a short link redirecting to
`http://169.254.169.254/…` (cloud metadata) or an internal host could make the
server issue that request.

**Fix:** redirects are now followed manually, and every hop is vetted by
`app.net_guard.url_is_safe_async` before it is fetched. A redirect to a
private / loopback / link-local / reserved address aborts the chain and the
original short URL is returned. Capped at 5 hops.

### 2. SSRF in `content_check.py` — FIXED (high)
The gray-zone content check rejected only literal private IPs and a hard-coded
localhost list. A public DNS name resolving to an internal address (DNS
rebinding) bypassed it, and `follow_redirects=True` could bounce to an internal
host.

**Fix:** the host is now resolved via `app.net_guard` and rejected if **any**
resolved address is non-public; redirect following is disabled.

### 3. WHOIS/TLS injection in feature extraction — NO ISSUE (reviewed)
`phish_features/domain.py` uses `python-whois` (≥0.9.4), which talks to WHOIS
servers over **sockets** — it does not shell out, so there is no command
injection vector. The host passed in is a `urlparse` hostname.
`phish_features/tls.py` uses the stdlib `ssl`/`socket` modules (no subprocess).
No change required.

### 4. Admin route authorization — OK (reviewed)
All `/admin/*`, `/feedback` (write), and `/watchlist` routes depend on
`verify_api_key`, which accepts a static API key **or** a valid JWT. The
production config guard (C-A1) now refuses to boot with a placeholder
`API_KEY`/`JWT_SECRET`, closing the "default credentials in prod" gap.

### 5. LIKE-pattern wildcard in `domain.py` — LOW (accepted)
`GET /domain/{host}/history` builds a `LIKE '%{host}%'` *bound parameter*
(no SQL injection). A `host` containing `%`/`_` would broaden the match, but
the route is authenticated and bounded to 90 days / 20 rows, and results are
re-filtered by exact parsed hostname. Accepted as low risk.

### 6. SSRF in v1.6.0 outbound paths (B6 renderer / B8 IP resolution) — OK (reviewed)
The v1.6.0 features each add an outbound path and both reuse the shared guard:
- **B6 visual fingerprinting** screenshots a gray-zone URL. The renderer is
  off by default (`VISUAL_FINGERPRINT_ENABLED`), runs only on the gray-zone
  fallback, fails open, and the target host is vetted by `app.net_guard` before
  rendering — same control as `content_check.py`.
- **B8 IP/ASN reputation** resolves the host to a public IP before recording /
  reading reputation; resolution is SSRF-safe via `app.net_guard`, and the
  optional Team Cymru ASN lookup is a fixed DNS query (no attacker-controlled
  URL). Off by default (`IP_REPUTATION_ENABLED`).
No new injection or authz surface: both consume the existing `urlparse`
hostname and write only aggregate counters.

## Shared control
`app.net_guard` centralizes the SSRF allow/deny decision (literal-IP and
DNS-resolution checks for private/loopback/link-local/reserved/multicast/
unspecified ranges) and is unit-tested in `tests/test_net_guard.py`.
