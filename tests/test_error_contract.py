"""Tests for the unified error contract + schema-version pin (C7)."""
from __future__ import annotations

from phish_features import FEATURE_SCHEMA_VERSION


def test_schema_version_header_present(client):
    resp = client.get("/health/live")
    assert resp.headers["X-Schema-Version"] == FEATURE_SCHEMA_VERSION


def test_error_envelope_shape_on_401(client):
    # Hitting an authenticated route without a key returns the {error, code} shape.
    resp = client.get("/api/v1/admin/whitelist")
    assert resp.status_code == 401
    body = resp.json()
    assert set(body.keys()) == {"error", "code"}
    assert body["code"] == "UNAUTHORIZED"


def test_error_envelope_shape_on_validation(client, headers):
    # Missing required body field -> 422 with the same envelope.
    resp = client.post("/api/v1/check", headers=headers, json={})
    assert resp.status_code == 422
    body = resp.json()
    assert set(body.keys()) == {"error", "code"}
    assert body["code"] == "VALIDATION_ERROR"


def test_openapi_documents_error_schema(client):
    schema = client.get("/openapi.json").json()
    assert "Error" in schema["components"]["schemas"]
    err = schema["components"]["schemas"]["Error"]
    assert err["required"] == ["error", "code"]
    # A representative operation documents the 401 error response.
    check_op = schema["paths"]["/api/v1/check"]["post"]
    assert "401" in check_op["responses"]
