"""End-to-end: a signed-in user's checks land in GET /me/history.

Exercises the full per-user attribution path through the running app:
register → check (with user JWT) → /me/history scoped to that user.
"""

from __future__ import annotations

_API = "/api/v1"


def _register(client, email: str) -> str:
    resp = client.post(
        f"{_API}/auth/register",
        json={"email": email, "password": "Password1!"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def test_me_history_requires_user_auth(client):
    # No token at all → 401.
    resp = client.get(f"{_API}/me/history")
    assert resp.status_code == 401

    # The static API key is NOT a user identity → still 401.
    resp = client.get(f"{_API}/me/history", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 401


def test_me_history_returns_only_callers_checks(client):
    alice_token = _register(client, "alice-hist@example.com")
    bob_token = _register(client, "bob-hist@example.com")
    auth = lambda t: {"Authorization": f"Bearer {t}"}  # noqa: E731

    # Alice checks two URLs, Bob one.
    for url in ("http://alice-evil1.test/login", "http://alice-evil2.test/verify"):
        assert client.post(f"{_API}/check", json={"url": url}, headers=auth(alice_token)).status_code == 200
    assert client.post(
        f"{_API}/check", json={"url": "http://bob-evil.test/login"}, headers=auth(bob_token)
    ).status_code == 200

    alice_hist = client.get(f"{_API}/me/history", headers=auth(alice_token))
    assert alice_hist.status_code == 200
    alice_urls = {item["url"] for item in alice_hist.json()["items"]}
    assert "http://alice-evil1.test/login" in alice_urls
    assert "http://alice-evil2.test/verify" in alice_urls
    assert not any("bob-evil" in u for u in alice_urls)

    bob_hist = client.get(f"{_API}/me/history", headers=auth(bob_token))
    assert bob_hist.status_code == 200
    bob_urls = {item["url"] for item in bob_hist.json()["items"]}
    assert any("bob-evil" in u for u in bob_urls)
    assert not any("alice-evil" in u for u in bob_urls)


def test_check_increments_user_check_count(client):
    token = _register(client, "counter-hist@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    before = client.get(f"{_API}/auth/me", headers=auth).json()["check_count"]
    client.post(f"{_API}/check", json={"url": "http://count-evil.test/login"}, headers=auth)
    after = client.get(f"{_API}/auth/me", headers=auth).json()["check_count"]
    assert after == before + 1
