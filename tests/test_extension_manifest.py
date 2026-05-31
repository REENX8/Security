"""Extension hardening guards (C5).

Locks in the minimal MV3 permission set and the offline/error handling in the
API client so a future change can't silently re-broaden the extension.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "extension"


def _manifest() -> dict:
    return json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))


def test_minimal_permission_set():
    perms = set(_manifest()["permissions"])
    # Only what the service worker actually uses.
    assert perms == {"webNavigation", "notifications", "storage"}
    # tabs/activeTab were dropped — popup reads only tab.id, which needs neither.
    assert "tabs" not in perms
    assert "activeTab" not in perms


def test_no_unexpected_broad_api_permissions():
    # Guard against re-adding high-risk permissions.
    perms = set(_manifest()["permissions"])
    for risky in ("<all_urls>", "cookies", "history", "webRequest", "scripting", "debugger"):
        assert risky not in perms


def test_api_client_handles_offline_and_timeout():
    src = (EXT / "api.js").read_text(encoding="utf-8")
    # Hard timeout via AbortController.
    assert "AbortController" in src and "TIMEOUT_MS" in src
    # Never blocks navigation: failures resolve to a non-throwing result.
    assert '"unverified"' in src
    assert "AbortError" in src  # timeout path distinguished


def test_background_ignores_non_http_urls():
    src = (EXT / "background.js").read_text(encoding="utf-8")
    assert "isCheckable" in src
    assert 'startsWith("http://")' in src and 'startsWith("https://")' in src
