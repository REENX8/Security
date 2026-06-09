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

## 2b. Retraining locally (from scratch)

Everything below runs **offline** — `collect_dataset` builds the corpus from the
committed seed CSVs plus a synthetic generator and *simulates* the WHOIS/TLS/
reputation features, so no network is required. The pipeline is **deterministic**:
the same committed corpus + fixed `RANDOM_SEED` produces a byte-identical model
every run. A retrain therefore only changes the model when the underlying **data**
changes (see step 4).

**0. Install (once).** Optuna and seaborn are needed for `--tune` and
`evaluate`; both ship in `ml_pipeline/requirements.txt`.

```bash
pip install -e .
pip install -r backend/requirements.txt
pip install -r ml_pipeline/requirements.txt
```

**1. Standard retrain (fast, deterministic).**

```bash
make train          # build_whitelist + collect_dataset --no-feeds + train
```

Writes `models/{ensemble.pkl,scaler.pkl,features.json}`.

**2. Best-effort retrain with hyperparameter search (slow).**

```bash
make train-tune              # Optuna 100-trial search, then the final calibrated fit
make train-tune TRIALS=200   # more thorough
```

The search is seeded (reproducible). On the current corpus it lifts CV-F1 only
marginally over the defaults (~0.9991 vs ~0.9983) because the test split is at
ceiling; what matters is the **independent real-world holdout** in step 3.

**3. MANDATORY verification before keeping a retrained model.**

```bash
make evaluate                            # Thai / generic / independent holdout recall + reports/
python -m ml_pipeline.adversarial_eval   # battle test — must stay 110/110 (>=70% gate)
python -m pytest tests/test_benign_fp.py # 0 legitimate sites blocked (false-positive gate)
make test                                # full suite
```

Keep the new model **only if** all hold: Thai holdout recall ≥ 85% (currently
100%), adversarial detection unchanged, **benign false positives = 0**, and the
independent real-world holdout recall is ≥ the current model's. Otherwise discard
it: `git checkout -- models/`.

> The benign FP guard (`KNOWN_GOOD_DOMAIN` rule in `phish_features/rules.py`)
> protects legitimate brand portals **regardless of the model**, so a retrain can
> never silently reintroduce those false positives.

**4. Getting a genuinely *different* model.** Because training is deterministic
on the committed corpus, a meaningfully different model needs **new data**:

- **Real feed data** — set `EXTERNAL_FEEDS_ENABLED=true` so the backend ingests
  OpenPhish/PhishTank, then `python -m ml_pipeline.feed_training_export` writes
  `data/live_feed_phishing.csv`, which `collect_dataset` picks up automatically
  on the next `make train`.
- **User feedback** — confirmed reports drive the feedback-retrain loop (§2).

**5. Deploy.** Replace the three files in `models/`, then hot-reload without a
restart via `POST /api/v1/admin/reload-model` (or just restart the backend).
Commit the new `models/*` so the change persists.

## 3. Threshold tuning (C10)

- Offline: `make tune-threshold` (`ml_pipeline/tune_threshold.py`) sweeps
  precision/recall/F1 vs threshold on the committed holdouts and writes
  `reports/threshold_analysis.json`.
- Online shadow A/B: set `ENABLE_THRESHOLD_AB=true` with
  `THRESHOLD_*_CANDIDATE` values. The served verdict is unchanged; the candidate
  thresholds are evaluated in shadow and counted in `phish_threshold_ab_total{variant,label}`,
  so a proposed threshold can be compared against real traffic before promotion.

Example — testing a looser suspicious threshold:

```env
ENABLE_THRESHOLD_AB=true
THRESHOLD_SUSPICIOUS=0.3          # current (live)
THRESHOLD_PHISHING=0.7            # current (live)
THRESHOLD_SUSPICIOUS_CANDIDATE=0.25   # shadow candidate
THRESHOLD_PHISHING_CANDIDATE=0.65     # shadow candidate
```

Query Prometheus to compare false-positive rates before promoting. The metric
labels are `variant="a"` (the live thresholds) and `variant="b"` (the shadow
candidate) — see `app/threshold_ab.py`:

```promql
rate(phish_threshold_ab_total{variant="b",label="suspicious"}[1h])
/
rate(phish_threshold_ab_total{variant="a",label="suspicious"}[1h])
```

### Promoting a candidate threshold

The serve-time cutoffs (`THRESHOLD_PHISHING=0.7` / `THRESHOLD_SUSPICIOUS=0.3`)
are theoretical defaults. Promote a new value only with evidence, in this order:

1. **Offline evidence.** Every CI `ml-gate` run executes `tune_threshold` on the
   freshly-retrained model and uploads `reports/threshold_analysis.json` (+ PNG)
   as a build artifact. Read `f1_optimal` and `high_precision_recommended` — the
   latter is the highest-recall threshold that still keeps precision ≥ 0.99 on
   the trusted-domain negatives (operator objective: do not cry wolf on real gov
   sites). This is in-distribution guidance, not proof.
2. **Shadow it.** Set `ENABLE_THRESHOLD_AB=true` with `THRESHOLD_*_CANDIDATE` to
   the value from step 1 and deploy. The served verdict is unchanged; the
   candidate is only counted in shadow.
3. **Collect real traffic.** Observe `phish_threshold_ab_total{variant,label}`
   over a representative window (≥ a few days, ideally spanning weekday/weekend
   traffic) so the comparison is not dominated by a single campaign.
4. **Decision rule.** Promote the candidate (`b`) only if, over the window, it
   reduces the suspicious/phishing false-positive rate on legitimate traffic
   *without* lowering the phishing catch rate below the live (`a`) level. If it
   trades catch rate for fewer false positives, that is a product decision —
   document it.
5. **Promote.** Edit `THRESHOLD_SUSPICIOUS` / `THRESHOLD_PHISHING` in the
   deployment env to the promoted value, then reset `THRESHOLD_*_CANDIDATE` to
   equal the new live values (a no-op shadow) until the next experiment.

Never promote from `threshold_analysis.json` alone — it is computed on committed
holdouts and trusted-domain negatives, which is an in-distribution estimate.

### Retrain failure recovery

If `feedback_promote_requires_gate=true` and the eval gate fails, the
staging model at `models/staging/` is **not promoted** — `models/` keeps
the previous model unchanged. To inspect or discard:

```bash
# see why the gate failed
python -m ml_pipeline.evaluate --models-dir models/staging --enforce-threshold

# discard staging and start fresh
rm -rf models/staging/

# promote manually (bypasses gate — use only if you have reviewed metrics)
cp -r models/staging/* models/
```

The automatic retrain trigger backs up the previous model to `models/previous/`
before any promotion, so a one-step rollback is always available.

## 4. Seed corpus refresh (C11)

`data/thai_phishing_seed.csv` is refreshed on a fixed cadence by
`.github/workflows/seed-refresh.yml` (monthly + manual), which regenerates it via
`scripts/collect_thai_phishing_seed.py`, audits coverage, and opens a PR for
human review. New rows feed both training and the Thai holdout; the ML gate runs
on the PR.

### Holdouts: what each one measures

| Holdout | File | Built by | Host overlap with training | Role |
| --- | --- | --- | --- | --- |
| **Thai-targeting** | `data/thai_phish_holdout.csv` | 30% split of the Thai seed | shares hosts (split of same corpus) | **primary, gated** (recall ≥ 0.85) |
| **Generic snapshot** | `data/generic_phish_holdout.csv` | 30% split of the generic seed | ~24% (split of same corpus) | secondary cross-check |
| **Independent real-world** | `data/real_phish_holdout.csv` | `scripts/collect_real_phish_holdout.py` | **zero (enforced)** | honest generalisation, reported |

The independent real-world holdout is the only one whose hosts are guaranteed
**never seen during training** — the collector drops any URL whose host appears
in any seed/holdout/`dataset.csv`, and `tests/test_real_holdout.py` asserts the
disjoint-host invariant in CI. It is therefore the trustworthy generalisation
number, but it is **reported, not gated**: a tight recall floor on ~100 decaying
public URLs would flake the build on routine retrains. The zero-overlap test is
the real protection; recall is surfaced in `evaluation_summary.json` under
`secondary_metrics.independent_real_holdout_recall`. Re-curate periodically
(re-run the collector, review, commit) so the sample stays fresh.
