#!/usr/bin/env python3
"""Verify the demo backend is ready before the judges arrive.

Used by scripts/demo_setup.sh as a smoke test right after seeding. By
default it checks the 6 golden demo URLs. With ``--full`` it additionally
probes every endpoint the live demo navigates to (health, stats, impact,
feed, campaigns, learn) so a startup bug on any dashboard page is caught
here instead of in front of the judges.

Usage:
    python scripts/demo_verify.py [API_URL] [API_KEY] [--full]
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
_flags = {a for a in sys.argv[1:] if a.startswith("--")}

API_URL = (_args[0] if _args else "http://localhost:8000").rstrip("/")
API_KEY = _args[1] if len(_args) > 1 else "dev-local-key-change-me"
FULL = "--full" in _flags

GOLDEN = [
    ("https://www.bot.or.th", "safe", "Bank of Thailand (legit)"),
    ("https://chula.ac.th", "safe", "Chulalongkorn (legit)"),
    ("http://0bec-go-th.xyz/login", "phishing", "Typosquat + cheap TLD"),
    ("https://moe.go.th.verify-login.top/signin", "phishing", "Subdomain spoof"),
    ("http://203.0.113.45/obec/secure/login", "phishing", "IP host + brand-in-path"),
    ("https://www.ku.ac.th@phish-site.xyz/login", "phishing", "@-trick"),
]


def check(url: str) -> dict | None:
    body = json.dumps({"url": url}).encode()
    req = urllib.request.Request(
        f"{API_URL}/api/v1/check",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  HTTP {exc.code} on {url}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print(f"  error on {url}: {exc}", file=sys.stderr)
    return None


def get(path: str) -> dict | list | None:
    req = urllib.request.Request(
        f"{API_URL}{path}",
        method="GET",
        headers={"X-API-Key": API_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  HTTP {exc.code} on {path}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print(f"  error on {path}: {exc}", file=sys.stderr)
    return None


# (path, predicate, human label). Predicate returns True when the payload
# looks healthy — these mirror the data each dashboard page relies on.
FULL_CHECKS = [
    ("/health", lambda d: d.get("model_ready") is True, "โมเดลพร้อม (model_ready)"),
    ("/api/v1/stats", lambda d: d.get("total_checks", 0) > 0, "สถิติมีข้อมูล"),
    ("/api/v1/impact?window_days=30",
     lambda d: d.get("phishing_blocked", -1) >= 0, "ผลกระทบเชิงสังคม"),
    ("/api/v1/feed.json", lambda d: d.get("count", -1) >= 0, "Threat feed (สาธารณะ)"),
    ("/api/v1/campaigns", lambda d: isinstance(d.get("items"), list), "แคมเปญฟิชชิง"),
    ("/api/v1/learn", lambda d: len(d.get("cards", [])) > 0, "เนื้อหาให้ความรู้"),
]


def run_full_checks() -> int:
    failures = 0
    print(f"\nVerifying {len(FULL_CHECKS)} demo endpoints ...")
    for path, ok_pred, label_text in FULL_CHECKS:
        data = get(path)
        if data is None:
            print(f"  ✘  no response       {label_text}  ({path})")
            failures += 1
            continue
        try:
            healthy = ok_pred(data)
        except Exception:  # noqa: BLE001
            healthy = False
        if healthy:
            print(f"  ✔  {label_text:<28} {path}")
        else:
            print(f"  ✘  unexpected payload  {label_text}  ({path})")
            failures += 1
    return failures


def main() -> int:
    failures = 0
    print(f"Verifying {len(GOLDEN)} golden demo URLs against {API_URL} ...")
    for url, want, label_text in GOLDEN:
        result = check(url)
        if result is None:
            print(f"  ✘  no response       {url}")
            failures += 1
            continue
        got = result["label"]
        # safe vs phishing must match exactly; suspicious passes as either
        if got == want or (want == "phishing" and got == "suspicious"):
            print(
                f"  ✔  {got:<10} ({result['score']:.2f})  {label_text}"
            )
        else:
            print(
                f"  ✘  expected {want}, got {got} ({result['score']:.2f})  "
                f"{label_text}  {url}"
            )
            failures += 1

    if FULL:
        failures += run_full_checks()

    if failures:
        print(f"\n{failures} check(s) failed verification")
        return 1
    print("\nAll checks OK — demo backend is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
