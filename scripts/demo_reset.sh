#!/usr/bin/env bash
#
# scripts/demo_reset.sh — รีเซ็ตระบบกลับ seed state สำหรับสาธิตซ้ำ
#
# Usage:
#   scripts/demo_reset.sh              # local SQLite mode
#   scripts/demo_reset.sh --docker     # docker mode (truncate Postgres tables)
#
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="${1:---local}"
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-local-key-change-me}"

log() { printf '\033[1;36m▶\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m✔\033[0m %s\n' "$*"; }

case "$MODE" in
  --docker)
    log "Truncating tables in Postgres container ..."
    docker compose exec -T db psql -U "${POSTGRES_USER:-phish}" -d "${POSTGRES_DB:-phishdb}" <<'SQL'
TRUNCATE TABLE
    feedback,
    url_checks,
    webhook_deliveries,
    brand_watches,
    campaigns,
    feed_ingestion_records
RESTART IDENTITY CASCADE;
SQL
    ok "Postgres tables truncated"
    ;;
  --local|"")
    log "Removing local SQLite demo DB ..."
    rm -f backend/demo_phish.db backend/demo_phish.db-wal backend/demo_phish.db-shm
    ok "SQLite cleared"
    log "Restart backend (Ctrl-C the running uvicorn then run demo_setup.sh again)"
    ;;
esac

log "Re-seeding demo data ..."
python scripts/seed_demo.py "$API_URL" "$API_KEY" || true

ok "Demo state reset."
