"""Tests for the campaign SIEM/SOAR export endpoints (B7)."""
from __future__ import annotations


def _seed_campaign(client, headers):
    # A typosquat of a whitelisted gov domain scores phishing and is clustered.
    for path in ("verify-login", "verify-account"):
        client.post(
            "/api/v1/check",
            headers=headers,
            json={"url": f"http://obec.com/{path}"},
        )


def test_export_json_requires_auth(client):
    resp = client.get("/api/v1/campaigns/export.json")
    assert resp.status_code == 401


def test_export_json_shape(client, headers):
    _seed_campaign(client, headers)
    resp = client.get("/api/v1/campaigns/export.json?min_urls=1", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema"] == "phish.campaign.v1"
    assert body["count"] >= 1
    camp = body["campaigns"][0]
    assert {"id", "fingerprint", "brand", "closest_domain", "url_count"} <= camp.keys()
    assert resp.headers["cache-control"] == "no-store"


def test_export_stix_bundle(client, headers):
    _seed_campaign(client, headers)
    resp = client.get("/api/v1/campaigns/export.stix?min_urls=1", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "bundle"
    for obj in body["objects"]:
        assert obj["type"] == "grouping"
        assert obj["spec_version"] == "2.1"
        assert obj["id"].startswith("grouping--")
