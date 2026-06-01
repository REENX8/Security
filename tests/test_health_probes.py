"""Tests for liveness/readiness probes (A2) and security headers (A6)."""
from __future__ import annotations


def test_liveness_always_ok(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_readiness_ok_when_model_and_db_ready(client):
    # The test client loads the model and a SQLite DB, so it is ready.
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["model_ready"] is True
    assert body["db_ready"] is True


def test_readiness_503_when_model_missing(client):
    app = client.app
    saved = app.state.scorer
    app.state.scorer = None
    try:
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        assert resp.json()["status"] == "not_ready"
        assert resp.json()["model_ready"] is False
    finally:
        app.state.scorer = saved


def test_security_headers_present(client):
    resp = client.get("/health/live")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in resp.headers["Content-Security-Policy"]
    assert "X-Request-ID" in resp.headers


def test_csp_exempt_on_docs(client):
    # Swagger UI must not get the locked-down CSP or it cannot render.
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "Content-Security-Policy" not in resp.headers
