"""Tests for the TAXII 2.1 server (B4)."""
from __future__ import annotations

from app.routers.taxii import API_ROOT, COLLECTION_ID, TAXII_MEDIA_TYPE

BASE = "/api/v1/taxii2"
ROOT = f"{BASE}/{API_ROOT}"
COLL = f"{ROOT}/collections/{COLLECTION_ID}"


def _seed_phishing(client, headers):
    # A typosquat of a whitelisted gov domain reliably scores as phishing.
    client.post(
        "/api/v1/check",
        headers=headers,
        json={"url": "http://obec.com/verify-login"},
    )


def test_discovery(client):
    resp = client.get(f"{BASE}/")
    assert resp.status_code == 200
    assert TAXII_MEDIA_TYPE in resp.headers["content-type"]
    body = resp.json()
    assert body["api_roots"]
    assert body["default"].endswith(f"/taxii2/{API_ROOT}/")


def test_api_root_info(client):
    resp = client.get(f"{ROOT}/")
    assert resp.status_code == 200
    assert TAXII_MEDIA_TYPE in resp.json()["versions"]


def test_unknown_api_root_404(client):
    resp = client.get(f"{BASE}/nope/")
    assert resp.status_code == 404


def test_list_collections(client):
    resp = client.get(f"{ROOT}/collections/")
    assert resp.status_code == 200
    cols = resp.json()["collections"]
    assert any(c["id"] == COLLECTION_ID for c in cols)
    assert cols[0]["can_read"] is True
    assert cols[0]["can_write"] is False


def test_collection_metadata(client):
    resp = client.get(f"{COLL}/")
    assert resp.status_code == 200
    assert resp.json()["id"] == COLLECTION_ID


def test_unknown_collection_404(client):
    resp = client.get(f"{ROOT}/collections/deadbeef/")
    assert resp.status_code == 404


def test_objects_envelope(client, headers):
    _seed_phishing(client, headers)
    resp = client.get(f"{COLL}/objects/?hours=24&limit=50")
    assert resp.status_code == 200
    assert TAXII_MEDIA_TYPE in resp.headers["content-type"]
    body = resp.json()
    assert body["more"] is False
    assert isinstance(body["objects"], list)
    assert len(body["objects"]) >= 1
    ind = body["objects"][0]
    assert ind["type"] == "indicator"
    assert ind["spec_version"] == "2.1"
    assert ind["id"].startswith("indicator--")
    assert ind["pattern"].startswith("[url:value = '")


def test_manifest_ids_match_objects(client, headers):
    _seed_phishing(client, headers)
    objs = client.get(f"{COLL}/objects/?limit=50").json()["objects"]
    man = client.get(f"{COLL}/manifest/?limit=50").json()["objects"]
    obj_ids = {o["id"] for o in objs}
    man_ids = {m["id"] for m in man}
    # Deterministic indicator ids mean manifest and objects line up.
    assert man_ids == obj_ids
    for m in man:
        assert m["media_type"] == "application/stix+json;version=2.1"


def test_invalid_added_after_400(client):
    resp = client.get(f"{COLL}/objects/?added_after=not-a-date")
    assert resp.status_code == 400
