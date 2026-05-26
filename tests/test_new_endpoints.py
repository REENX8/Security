"""Integration tests for the v1.0 new routers: watchlist, feed,
campaigns, domain history, and the request-context middleware."""

from __future__ import annotations


def test_version_endpoint(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert "backend" in body
    assert "phish_features" in body
    assert body["schema"] == "1.3.0"


def test_request_id_header_propagates(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_preserved_when_supplied(client):
    resp = client.get("/health", headers={"X-Request-ID": "deadbeef1234"})
    assert resp.headers.get("X-Request-ID") == "deadbeef1234"


def test_security_headers_set(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Referrer-Policy" in resp.headers


# ---------- /api/v1/feed (public) -----------------------------------------


def test_feed_json_is_public(client):
    """No API key required -- this is intentional."""
    resp = client.get("/api/v1/feed.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema"] == "phish.feed.v1"
    assert "indicators" in body


def test_feed_csv_returns_csv(client):
    resp = client.get("/api/v1/feed.csv?hours=1")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "url" in resp.content.decode("utf-8-sig")


def test_feed_stix_returns_bundle(client):
    resp = client.get("/api/v1/feed.stix?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "bundle"
    assert "objects" in body
    for obj in body["objects"]:
        assert obj["type"] == "indicator"
        assert obj["spec_version"] == "2.1"


# ---------- /api/v1/watchlist ---------------------------------------------


def test_watchlist_requires_api_key(client):
    resp = client.get("/api/v1/watchlist")
    assert resp.status_code == 401


def test_watchlist_create_list_delete(client, headers):
    add = client.post(
        "/api/v1/watchlist",
        json={
            "brand": "test-brand",
            "description": "Just a test",
            "webhook_url": None,
        },
        headers=headers,
    )
    assert add.status_code == 201
    assert add.json()["brand"] == "test-brand"

    # Duplicate brand returns 409
    dup = client.post(
        "/api/v1/watchlist", json={"brand": "test-brand"}, headers=headers,
    )
    assert dup.status_code == 409

    listing = client.get("/api/v1/watchlist", headers=headers)
    assert listing.status_code == 200
    brands = {x["brand"] for x in listing.json()["items"]}
    assert "test-brand" in brands

    rm = client.delete("/api/v1/watchlist/test-brand", headers=headers)
    assert rm.status_code == 204

    # Removing again returns 404
    rm2 = client.delete("/api/v1/watchlist/test-brand", headers=headers)
    assert rm2.status_code == 404


def test_watchlist_deliveries_list(client, headers):
    resp = client.get("/api/v1/watchlist/deliveries", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total" in body


# ---------- /api/v1/campaigns ---------------------------------------------


def test_campaigns_lists_clusters(client, headers):
    # Generate one phishing verdict so a cluster row exists
    client.post(
        "/api/v1/check",
        json={"url": "http://obec.com/login"},
        headers=headers,
    )
    resp = client.get("/api/v1/campaigns?limit=10", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    # At least one campaign should exist after the seeded check
    assert body["total"] >= 1


# ---------- /api/v1/domain/{host}/history --------------------------------


def test_domain_history_returns_404_for_unknown(client, headers):
    resp = client.get(
        "/api/v1/domain/nobody-checks-this-host.invalid/history",
        headers=headers,
    )
    assert resp.status_code == 404


def test_domain_history_returns_timeline(client, headers):
    client.post(
        "/api/v1/check",
        json={"url": "https://www.obec.go.th/page1"},
        headers=headers,
    )
    client.post(
        "/api/v1/check",
        json={"url": "https://www.obec.go.th/page2"},
        headers=headers,
    )
    resp = client.get(
        "/api/v1/domain/www.obec.go.th/history", headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["host"] == "www.obec.go.th"
    assert body["total_checks"] >= 2
    assert isinstance(body["timeline"], list)


# ---------- check response: new fields ------------------------------------


def test_check_response_includes_ml_score_and_rules(client, headers):
    resp = client.post(
        "/api/v1/check",
        json={"url": "http://obec.com/verify-account"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "ml_score" in body and 0 <= body["ml_score"] <= 1
    assert "rules" in body and "hits" in body["rules"]
    # At least one rule should have fired for this typosquat-with-login URL
    assert len(body["rules"]["hits"]) >= 1
