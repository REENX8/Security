# Operational Runbook — Thai Phishing Detector

Version: 1.7.0 | Updated: 2026-06-08

---

## 4.1 False Positive Incident

**Trigger:** FP rate > 2% over 1h (`phish_false_positive_rate > 0.02` in Prometheus)

1. Check recent misclassifications:
   ```
   GET /api/v1/history?label=phishing&since=1h
   ```
2. Check if a specific domain was recently added to a threat feed:
   ```
   GET /api/v1/admin/feeds
   ```
3. If a feed is returning bad data — disable it:
   ```
   PATCH /api/v1/admin/feeds/{id}  {"enabled": false}
   ```
4. Add the affected domain to the whitelist:
   ```
   POST /api/v1/admin/whitelist  {"domain": "example.go.th", "agency_name": "...", "category": "government"}
   ```
5. Reload whitelist immediately (no restart needed):
   ```
   POST /api/v1/admin/reload-model
   ```
6. Monitor FP rate for 15 minutes. If still elevated → proceed to §4.4 rollback.

---

## 4.2 False Negative Incident

**Trigger:** FN rate > 15% from feedback (`phish_false_negative_rate > 0.15`)

1. Query recent missed phishing reports:
   ```
   GET /api/v1/feedback?correct_verdict=phishing&limit=50
   ```
2. Determine if a new campaign is bypassing rules (look for a shared pattern: TLD, brand, redirect technique).
3. If a new campaign targets a known brand:
   ```
   POST /api/v1/admin/watchlist  {"brand": "krungthai", "webhook_url": "..."}
   ```
4. If a rule gap is found — add a rule in `phish_features/rules.py` and deploy.
5. Trigger emergency retrain:
   ```
   POST /api/v1/admin/retrain
   ```
6. Monitor Thai holdout recall in `reports/thai_holdout_metrics.json` after retrain.

---

## 4.3 Model Not Ready

**Trigger:** `phish_model_ready == 0` for > 5 minutes

1. Check container logs:
   ```
   docker logs phish-backend --tail 100
   ```
2. Verify model artifacts exist:
   ```
   ls -la models/ensemble.pkl models/scaler.pkl models/features.json
   ```
3. Restart the container:
   ```
   docker restart phish-backend
   ```
4. If persists — restore from backup and hot-reload:
   ```
   cp models/backup/* models/
   curl -X POST http://localhost:8000/api/v1/admin/reload-model \
        -H "X-API-Key: $API_KEY"
   ```

---

## 4.4 Model Rollback Procedure

Atomic rollback to the previous model (automatically done by `retrain_trigger.py` when Thai recall drops below threshold; also runnable manually):

```bash
# Restore previous model artifacts
cp models/previous/ensemble.pkl models/ensemble.pkl
cp models/previous/scaler.pkl   models/scaler.pkl
cp models/previous/features.json models/features.json

# Hot-swap without restart
curl -X POST http://localhost:8000/api/v1/admin/reload-model \
     -H "X-API-Key: $API_KEY"
```

**Verify rollback succeeded:**
```bash
curl http://localhost:8000/api/v1/health/ready
# Should return {"status": "ready", "schema_version": "..."}
```

---

## 4.5 Feed Polling Failure

**Trigger:** `phish_feed_poll_errors_total` increases for 2 consecutive polls

1. Check feed status:
   ```
   GET /api/v1/admin/feeds
   ```
2. If PhishTank API key expired:
   - Update `PHISHTANK_API_KEY` environment variable
   - Restart the container
3. If OpenPhish is down:
   - Disable the feed temporarily (it auto-recovers)
   - `PATCH /api/v1/admin/feeds/{id}  {"enabled": false}`
   - Wait 24h, then re-enable
4. Model continues serving from existing training data — no service degradation.

---

## 4.6 Database Capacity Alert

**Trigger:** `url_checks` row count > 10M OR disk usage > 80%

1. Run retention script (keeps last 90 days):
   ```bash
   python scripts/retention.py --days 90
   ```
2. Vacuum the table (PostgreSQL):
   ```bash
   psql $DATABASE_URL -c "VACUUM ANALYZE url_checks;"
   ```
3. If still critical — archive and truncate old partitions:
   ```bash
   psql $DATABASE_URL -c "DELETE FROM url_checks WHERE checked_at < NOW() - INTERVAL '90 days';"
   ```

---

## 4.7 Auto-Rollback Triggered

**Trigger:** `phish_model_rollback_total` counter increments (Prometheus alert: PhishModelRolledBack)

The system automatically rolled back the model because Thai holdout recall dropped below `recall_rollback_threshold` (default: 0.82) after a retrain promotion.

1. Check what triggered the retrain:
   - Feedback volume: `GET /api/v1/feedback?limit=100&created_since=1d`
   - Feed accumulation: `GET /api/v1/admin/feeds`
2. Inspect the rejected model metrics:
   ```
   cat reports/thai_holdout_metrics.json
   ```
3. Investigate why recall dropped (bad feedback batch, data drift, schema change).
4. If intentional model improvement: lower threshold temporarily in config:
   ```
   PHISH_RECALL_ROLLBACK_THRESHOLD=0.78
   ```
5. Re-trigger retrain: `POST /api/v1/admin/retrain`
