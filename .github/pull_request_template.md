## Summary

<!-- Describe what this PR changes and why. Link to the issue it resolves if applicable. -->

Fixes #

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] ML / data (seed corpus, model, features)
- [ ] Other: ___

## Quality checklist

- [ ] `make lint` passes (ruff check + format check)
- [ ] `make test` passes (all tests green)
- [ ] `make evaluate-gate` passes — Thai holdout recall ≥ 0.85 (required if any ML/feature change)
- [ ] `make sync-docs` run after `make evaluate` — no metric drift in docs
- [ ] New tests added for new behaviour (or existing tests updated with explanation)
- [ ] No breaking change to `ORDERED_FEATURES` without bumping `FEATURE_SCHEMA_VERSION` and retraining
- [ ] Golden tests in `tests/test_golden.py` still pass (or change explained in PR description)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Testing done

<!-- Describe how you tested the change. Include curl examples, test names, or screenshots as relevant. -->
