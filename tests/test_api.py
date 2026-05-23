"""FastAPI endpoint tests using TestClient against the real model."""

from __future__ import annotations


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "endpoints" in body
    assert any("/check" in e for e in body["endpoints"])


def test_health_reports_model_ready(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_ready"] is True
    assert body["db_ok"] is True
    assert body["schema_version"] == "1.0.0"
    assert isinstance(body["model_metrics"], dict)


def test_metrics_endpoint_returns_prometheus(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert b"phish_model_ready" in resp.content


def test_check_requires_api_key(client):
    resp = client.post("/api/v1/check", json={"url": "https://example.com"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "INVALID_API_KEY"
    assert body["error"]


def test_check_rejects_invalid_url(client, headers):
    resp = client.post("/api/v1/check",
                       json={"url": "not a url"}, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_check_returns_safe_for_whitelisted_domain(client, headers):
    resp = client.post("/api/v1/check",
                       json={"url": "https://www.obec.go.th"},
                       headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "safe"
    assert body["score"] < 0.3
    assert body["closest_domain"] == "obec.go.th"
    assert body["edit_distance"] == 0
    assert body["reason"]
    assert "url_length" in body["features"]


def test_check_flags_tld_swap_typosquat(client, headers):
    resp = client.post("/api/v1/check",
                       json={"url": "http://obec.com/verify-account"},
                       headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "phishing"
    assert body["features"]["is_typosquat"] == 1
    assert "obec.go.th" in body["reason"]


def test_check_batch(client, headers):
    payload = {"urls": [
        "https://www.obec.go.th",
        "http://obec.com/login",
        "https://www.google.com",
    ]}
    resp = client.post("/api/v1/check/batch", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert len(body["results"]) == 3
    assert body["results"][0]["label"] == "safe"
    assert body["results"][1]["label"] == "phishing"


def test_check_batch_too_large_rejected(client, headers):
    payload = {"urls": ["https://example.com"] * 60}
    resp = client.post("/api/v1/check/batch", json=payload, headers=headers)
    assert resp.status_code == 413
    assert resp.json()["code"] == "BATCH_TOO_LARGE"


def test_stats_response_shape(client, headers):
    resp = client.get("/api/v1/stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_checks", "phishing_count", "suspicious_count",
                "safe_count", "phishing_rate", "top_flagged_domains",
                "checks_per_day", "checks_by_hour"):
        assert key in body
    assert len(body["checks_per_day"]) == 7
    assert len(body["checks_by_hour"]) == 24


def test_history_pagination_and_search(client, headers):
    # ensure at least one row exists
    client.post("/api/v1/check",
                json={"url": "https://www.search-marker.go.th"},
                headers=headers)
    resp = client.get(
        "/api/v1/history?limit=5&offset=0&search=search-marker",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 5
    assert body["offset"] == 0
    assert body["total"] >= 1
    assert all("search-marker" in item["url"] for item in body["items"])


def test_history_filter_by_label(client, headers):
    client.post("/api/v1/check",
                json={"url": "http://obec.com/verify"},
                headers=headers)
    resp = client.get("/api/v1/history?label=phishing&limit=5", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["label"] == "phishing" for i in items)
