#!/usr/bin/env python3
"""Verify the 6 golden demo URLs return the expected labels.

Used by scripts/demo_setup.sh as a smoke test right after seeding, so
the team knows the system is ready before the judges arrive.

Usage:
    python scripts/demo_verify.py [API_URL] [API_KEY]
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

API_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
API_KEY = sys.argv[2] if len(sys.argv) > 2 else "dev-local-key-change-me"

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

    if failures:
        print(f"\n{failures}/{len(GOLDEN)} golden URLs failed verification")
        return 1
    print(f"\nAll {len(GOLDEN)}/{len(GOLDEN)} golden URLs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
