# ML Operations — drift, retraining & threshold tuning

How the deployed model is monitored and kept fresh. Ties together the
feedback loop (`routers/feedback.py`), the learning content (`routers/learn.py`),
the retrain pipeline (`ml_pipeline/feedback_retrain.py`) and the live telemetry.

## 1. Drift monitoring (C4)

Every served `/check` score is recorded into the Prometheus histogram
`phish_score` (`app/metrics.py`). This exposes the **live score distribution**,
which is the primary drift signal:

- Grafana panel "Phishing score distribution" (`deploy/observability/grafana-dashboard.json`).
- Alert `PhishScoreDistributionDrift` fires when the top-bucket (≥0.9) share over
  1h diverges >2x from its 1-day baseline (`deploy/observability/alert.rules.yml`).

Feature-quality drift is tracked separately: `phish_network_timeout_total{kind}`
counts WHOIS/TLS lookups that fell back to imputed defaults. A rising rate means
those features are silently degrading (provider blocking, network), which also
shifts scores.

## 2. Retrain cadence

Two complementary triggers, both gated on the Thai-recall eval gate
(`feedback_promote_requires_gate`, default on) and both promoting atomically
into `models/` only if the gate passes:

| Trigger | Where | When |
| --- | --- | --- |
| **Time-based** | `main.lifespan` background loop | every `FEEDBACK_RETRAIN_INTERVAL_HOURS` (default 14d) |
| **Volume-based (C9)** | `app/retrain_trigger.py`, fired from `POST /feedback` | once `FEEDBACK_ACCUMULATION_THRESHOLD` new confirmed-feedback rows accumulate |
| **Manual** | `POST /api/v1/admin/retrain` | on demand (admin) |

All paths are disabled unless `FEEDBACK_RETRAIN_ENABLED=true`. The feedback that
drives them comes from users via the dashboard/extension/API (`routers/feedback.py`),
and `routers/learn.py` teaches users what to report — together they close the
loop from "user spots a miss" → "model improves".

## 3. Threshold tuning (C10)

- Offline: `make tune-threshold` (`ml_pipeline/tune_threshold.py`) sweeps
  precision/recall/F1 vs threshold on the committed holdouts and writes
  `reports/threshold_analysis.json`.
- Online shadow A/B: set `ENABLE_THRESHOLD_AB=true` with
  `THRESHOLD_*_CANDIDATE` values. The served verdict is unchanged; the candidate
  thresholds are evaluated in shadow and counted in `phish_threshold_ab_total{variant,label}`,
  so a proposed threshold can be compared against real traffic before promotion.

## 4. Seed corpus refresh (C11)

`data/thai_phishing_seed.csv` is refreshed on a fixed cadence by
`.github/workflows/seed-refresh.yml` (monthly + manual), which regenerates it via
`scripts/collect_thai_phishing_seed.py`, audits coverage, and opens a PR for
human review. New rows feed both training and the Thai holdout; the ML gate runs
on the PR.
