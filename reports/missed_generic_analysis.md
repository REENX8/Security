# Missed-generic-URL review (C3)

Review of `reports/missed_generic_urls.csv` — the phishing URLs in the **generic**
real holdout (90 URLs, 91.1% recall) that the model scored below the phishing
threshold. The Thai holdout remains at 100% recall (378/378), and a positive
`alignment_score` (Thai recall − generic recall) is the **intended** behaviour
for this Thai-targeted system, so generic misses are evaluated for whether they
are *in scope*, not treated as outright regressions.

| URL | score | closest Thai brand | edit dist | verdict |
| --- | --- | --- | --- | --- |
| `diskcacambasdetroit.com.br/auth/rackespace/` | 0.00 | coj.go.th | 1 | **out of scope** — Brazilian host; the edit-distance-1 match to `coj` is coincidental (3-letter label), not Thai impersonation |
| `lnsta.fr/` | 0.02 | nstda.or.th | 2 | **borderline in scope** — plausible `nstda`→`lnsta` typosquat on a `.fr` host |
| `www.metanask.com/metamask/welcome.php` | 0.11 | smebank.co.th | 4 | **out of scope** — MetaMask (crypto) phishing, not a Thai brand |
| `www.wapluszone.com/` | 0.13 | kalasin.go.th | 6 | **out of scope** — unrelated; edit distance 6 |

## Findings

1. **Not a `min_edit_distance` tuning problem.** Three of four misses have an
   edit distance of 4–6 (or a coincidental 1) to the nearest Thai brand. Lowering
   the typosquat edit-distance threshold to catch them would inflate false
   positives on legitimate generic domains while doing nothing for the Thai
   cohort. No `min_edit_distance` change is recommended.

2. **Three are genuinely out of scope.** MetaMask/crypto and unrelated foreign
   hosts are exactly the generic phishing this system intentionally
   deprioritizes in favour of high Thai-targeting recall. Chasing them trades
   away the system's differentiator.

3. **One borderline case (`lnsta.fr` ~ `nstda`).** This is the only miss that
   resembles a Thai-brand typosquat. The right fix is **data, not threshold**:
   add `nstda` near-typosquat coverage to the seed corpus so the model learns
   the pattern.

## Action

- Queue `nstda`-typosquat seed coverage for the next **seed refresh** (C11,
  `.github/workflows/seed-refresh.yml`) → it flows into the **gated retrain**
  (C9, `ml_pipeline/feedback_retrain.py`). Promotion is atomic and only happens
  if the Thai-recall eval gate still passes, so adding the pattern cannot
  regress the 100% Thai holdout.
- **No live model regeneration in this change**: retraining is performed only
  through the gated pipeline (CI `ml-gate` / the retrain triggers), not ad-hoc,
  so the committed artifacts and the golden suite stay reproducible.

_Conclusion: the generic misses are dominated by out-of-scope phishing; the one
in-scope pattern is routed to the seed→retrain loop rather than handled by a
threshold change that would cost generic precision._
