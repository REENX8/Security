# Deployment & Staging Playbook (Render + Supabase)

Step-by-step for a public **staging** deploy of the backend (Render, Docker)
with **Supabase** Postgres, plus smoke tests, observability, and rollback.
The Render Blueprint is `render.yaml`; this doc is the runbook around it.

> Production checklist in one line: `APP_ENV=production` is set, all secrets are
> real (the config guard refuses to boot otherwise), CORS lists the explicit
> dashboard origin, and `/health/ready` returns 200 after deploy.

---

## 1. Provision the database (Supabase)

1. Create a Supabase project (region close to the Render region — `singapore`).
2. Project Settings → Database → Connection string → **URI** (use the
   **Session pooler** string, port 5432).
3. Keep it for `DATABASE_URL`. The app auto-rewrites `postgresql://` →
   `postgresql+asyncpg://` (see `config.py`), and disables prepared-statement
   caching for Supavisor/PgBouncer transaction mode.

## 2. Prepare secrets

| Variable | How to generate |
| --- | --- |
| `JWT_SECRET` | `openssl rand -hex 32` (Render `generateValue` does this) |
| `API_KEY` | `openssl rand -hex 24` (Render `generateValue` does this) |
| `ADMIN_PASSWORD_HASH` | `python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('YOURPASS'))"` |

## 3. Deploy to Render

1. Push to GitHub.
2. Render dashboard → **New + → Blueprint** → pick this repo. It reads
   `render.yaml` and creates `phish-backend` (Docker) + `phish-dashboard`
   (static).
3. On `phish-backend` set the `sync:false` env vars:
   - `DATABASE_URL` = Supabase URI
   - `ADMIN_PASSWORD_HASH` = bcrypt hash from step 2
   - `CORS_ORIGINS` = the dashboard URL, e.g. `https://phish-dashboard.onrender.com`
     (explicit — **no wildcards**, the guard rejects them)
   - `LINE_CHANNEL_TOKEN` / `LINE_CHANNEL_SECRET` (optional)
4. `APP_ENV=production` is already set in the blueprint → the **config guard**
   runs at boot and the deploy fails fast if any secret is still a placeholder.
5. DB migrations run automatically before each release via the blueprint's
   `preDeployCommand: alembic upgrade head`.
6. Render gates traffic on `healthCheckPath: /health/ready` (model + DB).

## 4. Smoke test (after deploy)

Replace `$HOST` with the backend URL and `$KEY` with `API_KEY`:

```bash
# Liveness + readiness
curl -sf https://$HOST/health/live
curl -sf https://$HOST/health/ready          # 200 = ready, 503 = not ready

# A known phishing-style URL should classify as phishing
curl -sf -X POST https://$HOST/api/v1/check \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"url":"http://obec.com/verify"}' | grep -q phishing && echo "check OK"

# Metrics are exposed for Prometheus
curl -sf https://$HOST/metrics | grep -q phish_checks_total && echo "metrics OK"

# Security headers present
curl -sfI https://$HOST/health/live | grep -i "content-security-policy\|strict-transport-security"
```

All four should succeed. If `/health/ready` is 503, check the logs:
`model_ready=false` → model artifacts missing; `db_ready=false` → DATABASE_URL.

## 5. Observability

The backend emits Prometheus metrics at `/metrics` and structured JSON access
logs when `LOG_FORMAT=json` (every line carries `request_id`, also returned in
the `X-Request-ID` response header).

- Scrape config: `deploy/observability/prometheus.yml`
- Alert rules: `deploy/observability/alert.rules.yml`
  (model-not-ready, p95 latency > 250 ms SLO, WHOIS/TLS degradation, feed errors)
- Grafana dashboard: import `deploy/observability/grafana-dashboard.json`

## 6. Rollback

1. **App code:** Render → `phish-backend` → *Events/Deploys* → pick the last
   known-good deploy → **Rollback**. Render redeploys that image.
2. **Database:** migrations are forward-only by default. To undo the most
   recent migration manually:
   ```bash
   # from the backend image / a shell with DATABASE_URL set
   alembic downgrade -1
   ```
   The baseline (`0001_baseline`) creates the full schema; never edit it —
   add a new revision (`make migration m="..."`) for changes.
3. **Verify** with the step-4 smoke test after any rollback.

## 7. Local parity (docker-compose)

`docker-compose up` runs the same image with Postgres + Redis. It defaults to
`APP_ENV` unset (development) so the demo secrets work; set `APP_ENV=production`
plus real secrets to rehearse the production guard locally.
