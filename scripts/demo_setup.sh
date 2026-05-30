#!/usr/bin/env bash
#
# scripts/demo_setup.sh — เตรียมระบบสำหรับสาธิตวันนำเสนอ NSC 2026
#
# ใช้ได้แม้ไม่มีอินเทอร์เน็ต — ใช้ image ที่ build ไว้แล้ว + SQLite + seed data
# ที่ผูกอยู่กับ repository
#
# Usage:
#   scripts/demo_setup.sh              # boot backend + seed
#   scripts/demo_setup.sh --docker     # boot ด้วย docker-compose (PostgreSQL)
#
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="${1:---local}"
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-local-key-change-me}"

log() { printf '\033[1;36m▶\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m✔\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✘ %s\033[0m\n' "$*" >&2; exit 1; }

wait_for_health() {
    log "Waiting for backend health at ${API_URL}/health ..."
    for i in $(seq 1 30); do
        if curl -fsS "${API_URL}/health" >/dev/null 2>&1; then
            ok "backend is healthy"
            return 0
        fi
        sleep 1
    done
    die "backend did not become healthy in 30s"
}

case "$MODE" in
  --docker)
    log "Starting docker-compose stack (db + backend) ..."
    docker compose up -d --build
    wait_for_health
    ;;
  --local|"")
    log "Backfilling 14 days of demo history (charts, heatmap, campaigns) ..."
    DATABASE_URL="sqlite+aiosqlite:///$(pwd)/backend/demo_phish.db" \
      python scripts/seed_demo.py --backfill || \
      log "backfill skipped (continuing with live seed only)"

    log "Starting backend locally with SQLite ..."
    if pgrep -f "uvicorn app.main:app" >/dev/null; then
        ok "backend already running"
    else
        ( cd backend && \
          DATABASE_URL="sqlite+aiosqlite:///./demo_phish.db" \
          API_KEY="${API_KEY}" \
          python -m uvicorn app.main:app \
            --host 0.0.0.0 --port 8000 \
            >../demo_backend.log 2>&1 ) &
        sleep 2
    fi
    wait_for_health
    ;;
  *)
    die "unknown mode: $MODE (use --local or --docker)"
    ;;
esac

log "Seeding a few live demo URLs (legitimate + typosquat + IDN/homoglyph) ..."
python scripts/seed_demo.py "$API_URL" "$API_KEY"

log "Verifying golden demo URLs ..."
python scripts/demo_verify.py "$API_URL" "$API_KEY" --full

# Start the dashboard so the presenter has the full stack with one command.
# Disable with START_DASHBOARD=0 (eg. when serving a pre-built static bundle).
if [ "${START_DASHBOARD:-1}" = "1" ] && [ "$MODE" != "--docker" ]; then
    if pgrep -f "vite" >/dev/null 2>&1; then
        ok "dashboard already running at http://localhost:5173"
    elif command -v npm >/dev/null 2>&1; then
        log "Starting dashboard (Vite dev) on http://localhost:5173 ..."
        ( cd dashboard && npm run dev >../demo_dashboard.log 2>&1 ) &
        sleep 3
        ok "dashboard started — http://localhost:5173 (log: demo_dashboard.log)"
    else
        log "npm not found — start the dashboard manually: cd dashboard && npm run dev"
    fi
fi

ok "Demo system ready."
cat <<EOF

  ─────────────────────────────────────────────
   พร้อมสาธิตที่:
     Backend:     ${API_URL}
     Swagger:     ${API_URL}/docs
     Dashboard:   http://localhost:5173
     Threat feed: ${API_URL}/api/v1/feed.json
     Disclaimer:  ${API_URL}/api/v1/disclaimer
  ─────────────────────────────────────────────

EOF
