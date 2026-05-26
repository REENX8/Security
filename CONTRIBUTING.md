# Contributing to Thai Phishing URL Detection

Thanks for your interest! This project protects Thai citizens against
phishing of government and educational brands, and every contribution —
from a single false-positive report to a new feature schema version —
moves that goal forward.

This guide is intentionally short. Read [`README.md`](README.md) first
for the architecture and the metrics framework.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Quality bars](#quality-bars)
- [Adding URLs to the training / holdout corpora](#adding-urls-to-the-training--holdout-corpora)
- [Pull-request workflow](#pull-request-workflow)
- [Coding style](#coding-style)
- [Releasing](#releasing)
- [Reporting security issues](#reporting-security-issues)

---

## Ways to contribute

| Type of contribution | Where to start |
|----------------------|----------------|
| 🐛 Bug report | [Open a Bug issue](https://github.com/reenx8/security/issues/new?template=bug.yml) |
| ✨ Feature request | [Open a Feature issue](https://github.com/reenx8/security/issues/new?template=feature.yml) |
| ❌ False positive (safe URL flagged) | [Open a False-positive issue](https://github.com/reenx8/security/issues/new?template=false-positive.yml) |
| 🎯 False negative (phishing URL missed) | [Open a False-negative issue](https://github.com/reenx8/security/issues/new?template=false-negative.yml) |
| 📚 Documentation fix | Open a PR directly — small typo fixes don't need an issue first |
| 🔒 Security vulnerability | See [`SECURITY.md`](SECURITY.md) — **do not file a public issue** |
| 🌐 Whitelist additions (new ministries, universities) | Open a PR against `data/thai_gov_domains.csv` with a source link |

---

## Development setup

You need **Python 3.10+**, **Node 20+** and **Docker** (optional but
recommended). The repository ships with a `Makefile` that wraps the
common commands:

```bash
make install          # python deps + pre-commit hooks
make test             # pytest (142 tests, ~4 s)
make lint             # ruff check + format check
make format           # ruff format
make run              # backend (sqlite mode), no docker required
make train            # rebuild models from the committed seed corpus
make evaluate         # ML metrics + report PNGs
make dashboard        # vite dev server
make extension        # produce dist/thai-phishing-detector-vX.Y.Z.zip
make docker           # build the backend image
```

If you prefer raw commands:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r backend/requirements.txt
pip install -r ml_pipeline/requirements.txt
pip install "pytest==8.3.4" "httpx==0.28.1" "ruff==0.7.4" "pre-commit==4.0.1"
pre-commit install
```

The full end-to-end recipe is documented in [`README.md`](README.md#test-end-to-end).

---

## Quality bars

A pull request is ready to merge when **all** of the following hold:

1. **Tests pass**: `python -m pytest -ra` is green.
2. **Lint passes**: `ruff check .` and `ruff format --check .` are green.
3. **The ML primary-metric gate holds**: the Thai-targeting holdout
   recall is ≥ `THAI_RECALL_MIN_THRESHOLD` (currently 0.85). The CI
   `ml-gate` job enforces this; you can run it locally with
   `python -m ml_pipeline.evaluate --enforce-threshold`.
4. **Schema bumps are intentional**: any change to `ORDERED_FEATURES`,
   `IMPUTED_DEFAULTS` or `TLD_TYPE_MAP` in
   `phish_features/schema.py` is a breaking change. Bump
   `FEATURE_SCHEMA_VERSION` and retrain the model in the same PR.
5. **No regressions on golden tests**: the verdicts in
   `tests/test_golden.py` are pinned for known-good and known-bad URLs.
   If you have to change one, write down why in the PR description.

---

## Adding URLs to the training / holdout corpora

This is the single most valuable contribution non-developers can make.

| Goal | File to edit | Source link required? |
|------|--------------|-----------------------|
| New trusted Thai gov/edu/state-bank domain | `data/thai_gov_domains.csv` | Yes — link to the official site |
| New Thai-targeting phishing sample | `data/thai_phishing_seed.csv` | Strongly recommended — ThaiCERT advisory, news report, etc. |
| New labelled holdout URL the model should never see during training | `data/thai_phish_holdout.csv` | Yes |

After editing a CSV, run:

```bash
make train evaluate
```

and include the updated `reports/evaluation_summary.json` in your PR so
reviewers can see the metric impact.

**Never submit live credentials** even inside a phishing sample. URLs
only — no captured form input, no real PII.

---

## Pull-request workflow

1. Fork and create a topic branch off `main`:
   `git checkout -b feature/your-change`.
2. Make focused commits. Conventional-commit prefixes (`feat:`, `fix:`,
   `docs:`, `chore:`, `test:`, `refactor:`) are appreciated but not
   required.
3. Run `make lint test` before pushing.
4. Open a PR using the supplied template; tick the checklist.
5. CI runs `backend-tests`, `lint`, `ml-gate`, `dashboard-build`,
   `docker-build` and `extension-package`. All must pass.
6. A maintainer will review. We aim to give first feedback within a
   week.

PRs that grow without scope discipline tend to stall — feel free to
split a large change into a series of smaller PRs.

---

## Coding style

- **Python**: `ruff` enforces formatting and a curated lint rule set.
  The configuration lives in `pyproject.toml`. Type annotations are
  required for new public functions; we use `from __future__ import
  annotations` so postponed evaluation gives forward references for
  free.
- **JavaScript** (extension + dashboard): plain ES modules, no
  build-time framework lint at the moment. Match the surrounding style.
- **SQL / migrations**: there is no migration framework yet — schema
  changes are handled by `Base.metadata.create_all` at startup. If you
  introduce a destructive change, open an issue first.
- **Comments**: prefer self-explanatory code; only add a comment when
  the **why** is non-obvious (a constraint, a workaround, a surprising
  invariant).

---

## Releasing

Maintainer responsibility. The full procedure is in
[`MAINTAINERS.md`](MAINTAINERS.md).

In short:

1. Bump `VERSION`.
2. Update `CHANGELOG.md` (move *Unreleased* entries under the new
   version heading).
3. Tag: `git tag -a v$(cat VERSION) -m "Release v$(cat VERSION)"`.
4. Push the tag — the `extension-package` CI job attaches the built
   `.zip` to the GitHub Release automatically.

---

## Reporting security issues

Do not open a public issue. Follow [`SECURITY.md`](SECURITY.md).
