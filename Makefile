.PHONY: help install test cov lint typecheck format run train evaluate evaluate-gate \
        sync-docs sync-docs-check dashboard extension docker clean nsc-bundle \
        demo-setup demo-reset demo-verify seed-audit seed-refresh tune-threshold \
        migrate migrate-down migration

PY        ?= python
PIP       ?= $(PY) -m pip
PYTEST    ?= $(PY) -m pytest
RUFF      ?= $(PY) -m ruff

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python deps for backend + ML + dev tooling.
	$(PIP) install -e .
	$(PIP) install -r backend/requirements.txt
	$(PIP) install -r ml_pipeline/requirements.txt
	$(PIP) install "pytest==8.3.4" "httpx==0.28.1" "pytest-asyncio>=0.23" \
	               "pytest-cov==5.0.0" "ruff==0.8.4" "mypy==1.13.0"

test:  ## Run the full pytest suite.
	$(PYTEST) -ra

cov:  ## Run tests with the coverage gate (matches CI: fail under 75%).
	$(PYTEST) -ra --cov=backend/app --cov=phish_features \
	  --cov-report=term-missing --cov-fail-under=75

lint:  ## Ruff lint (matches the CI blocking gate).
	$(RUFF) check backend phish_features ml_pipeline scripts tests

typecheck:  ## Mypy type check (informational).
	@$(PY) -m mypy backend/app phish_features || true

format:  ## Ruff auto-format the repo.
	@$(RUFF) format .

migrate:  ## Apply DB migrations (alembic upgrade head).
	cd backend && alembic upgrade head

migrate-down:  ## Roll back the last migration (alembic downgrade -1).
	cd backend && alembic downgrade -1

migration:  ## Autogenerate a revision from model changes: make migration m="msg".
	cd backend && alembic revision --autogenerate -m "$(m)"

run:  ## Boot the backend on http://localhost:8000 (SQLite, no Docker).
	cd backend && DATABASE_URL="sqlite+aiosqlite:///./phish.db" \
	  API_KEY="dev-local-key-change-me" \
	  $(PY) -m uvicorn app.main:app --reload

train:  ## Retrain the model from the committed seed corpus.
	$(PY) -m ml_pipeline.build_whitelist
	$(PY) -m ml_pipeline.collect_dataset --no-feeds
	$(PY) -m ml_pipeline.train

evaluate:  ## Run the evaluation + write reports/.
	$(PY) -m ml_pipeline.evaluate

evaluate-gate:  ## Same as evaluate but fails CI if Thai recall < THAI_RECALL_MIN_THRESHOLD.
	$(PY) -m ml_pipeline.evaluate --enforce-threshold

tune-threshold:  ## Sweep precision/recall/F1 vs threshold on the committed holdouts.
	$(PY) -m ml_pipeline.tune_threshold

sync-docs:  ## Inject metrics from reports/evaluation_summary.json into the docs.
	$(PY) scripts/sync_docs_metrics.py

sync-docs-check:  ## Fail if docs metrics drift from evaluation_summary.json (CI).
	$(PY) scripts/sync_docs_metrics.py --check

seed-audit:  ## Print brand / TLD / pattern coverage of the Thai seed corpus.
	$(PY) scripts/audit_seed_coverage.py

seed-refresh:  ## Regenerate the Thai phishing seed (live fetch) — see C11 cadence.
	$(PY) scripts/collect_thai_phishing_seed.py
	$(PY) scripts/audit_seed_coverage.py

dashboard:  ## Start the Vite dev server for the dashboard.
	cd dashboard && npm install && npm run dev

extension:  ## Build the cross-browser extension .zip.
	$(PY) scripts/build_extension.py

docker:  ## Build the backend Docker image.
	docker build -f backend/Dockerfile -t phish-backend:dev .

clean:  ## Remove caches, coverage, build artifacts.
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ \
	       *.egg-info build dist dashboard/dist

demo-setup:  ## Boot the backend and seed it with the NSC demo URLs.
	bash scripts/demo_setup.sh

demo-reset:  ## Reset DB to seeded state (use between demo rounds).
	bash scripts/demo_reset.sh

demo-verify:  ## Verify 6 golden demo URLs return expected labels.
	$(PY) scripts/demo_verify.py

nsc-bundle:  ## Build the NSC 2026 submission ZIP (code + docs + models).
	@mkdir -p dist
	@rm -f dist/nsc2026-submission.zip
	git ls-files \
	  | grep -Ev '^(dashboard/(node_modules|dist)/|\.env)' \
	  | zip -@ dist/nsc2026-submission.zip > /dev/null
	@echo "→ dist/nsc2026-submission.zip"
	@unzip -l dist/nsc2026-submission.zip | tail -5
