# Service Level Agreement v1.0

Thai Phishing Detector — Production SLA  
Effective: 2026-06-08 | Version: 1.7.0

---

## Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.5% monthly (≤ 3.65h downtime/month) |
| Measurement | `/health/live` endpoint, 30-second intervals |
| Maintenance window | Sundays 02:00–04:00 UTC+7 (excluded from SLA calculation) |

---

## Performance

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| p50 latency (cached) | < 50ms | > 100ms |
| p95 latency (full check) | < 500ms | > 1000ms |
| p99 latency | < 2000ms | > 5000ms |
| Throughput | > 100 req/s (single instance) | < 30 req/s |

---

## Detection Quality

| Metric | Target | Alert Threshold | Gate |
|--------|--------|----------------|------|
| Thai holdout recall | ≥ 85% | < 82% | CI gate (evaluate.py) |
| False positive rate | < 2% | > 3% | Monitored via feedback |
| False negative rate | < 10% (feedback-based) | > 15% | Monitored via feedback |
| Adversarial detection rate | ≥ 70% | < 60% | CI gate (adversarial_eval.py) |
| Adversarial per-technique floor | ≥ 50% each | any technique < 50% | CI gate (test_adversarial.py) |
| Live feed holdout recall | ≥ 80% | < 75% | evaluate.py gate |

---

## Incident Response Times

| Severity | Definition | Response Time | Resolution Target |
|----------|-----------|---------------|------------------|
| **P0 Critical** | Model down / FP rate > 10% / Service unavailable | 15 minutes | 2 hours |
| **P1 High** | FP rate > 3% / FN rate > 15% / Adversarial rate < 60% | 1 hour | 8 hours |
| **P2 Medium** | Feed polling failure / Latency > 1s p95 / Auto-rollback triggered | 4 hours | 24 hours |
| **P3 Low** | Single missed URL / Coverage gap / Model < 85% Thai recall | 48 hours | 1 week |

---

## Exclusions

The SLA does not apply to:
- Degradation caused by upstream feed provider outages (PhishTank, OpenPhish, URLhaus)
- Events caused by intentional maintenance within the declared window
- Force majeure events
- Degraded performance when the model is intentionally rolled back for investigation

---

## Model Lifecycle SLA

| Event | Commitment |
|-------|-----------|
| New model retrain (time-based) | Every 14 days (configurable) |
| New model retrain (volume trigger) | Within 1h of 50 new feed URLs accumulating |
| Model promotion | Only when Thai holdout recall ≥ 82% (auto-rollback otherwise) |
| Model rollback | Automatic, < 30s, no service interruption |
| Feature schema update | Requires full retrain; backward-incompatible |

---

## Data Retention

| Data | Retention |
|------|-----------|
| `url_checks` (check history) | 90 days (configurable) |
| `feedback` (user corrections) | 1 year |
| `ip_reputation` / `asn_reputation` | Indefinite (updated in place) |
| Training artifacts (ensemble.pkl) | Current + previous version kept |
| Holdout evaluation reports | Indefinite (small JSON files) |

---

## Contact & Escalation

| Level | Contact |
|-------|---------|
| On-call | Check PagerDuty / OpsGenie rotation |
| Engineering escalation | See RUNBOOK.md §4.1–§4.7 |
| Security incident | security@[your-org].th |
