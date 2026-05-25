"""Shared pytest fixtures.

The backend app is configured against a temporary SQLite database and the
trained model in ``models/`` before being imported. Caching, WHOIS and TLS
lookups are disabled so tests are deterministic and fast.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# --- ensure ``app`` (the backend package) is importable ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# --- configure runtime BEFORE importing the FastAPI app ---
_TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB.name}"
os.environ["API_KEY"] = "test-key"
os.environ["ENABLE_WHOIS"] = "false"
os.environ["ENABLE_TLS"] = "false"
os.environ["RATE_LIMIT"] = "100000/minute"
os.environ["ENABLE_CACHE"] = "false"
os.environ["MODEL_DIR"] = str(ROOT / "models")
os.environ["WHITELIST_PATH"] = str(ROOT / "models" / "whitelist.json")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """A TestClient with full lifespan (model loading) executed."""
    with TestClient(app) as c:
        yield c
    try:
        os.unlink(_TEST_DB.name)
    except OSError:
        pass


@pytest.fixture
def headers() -> dict:
    return {"X-API-Key": "test-key"}
