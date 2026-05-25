#!/usr/bin/env python3
"""Seed the running backend with sample checks so the dashboard has data.

Usage:
    python scripts/seed_demo.py [API_URL] [API_KEY]

Defaults: http://localhost:8000  /  dev-local-key-change-me
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

API_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
API_KEY = sys.argv[2] if len(sys.argv) > 2 else "dev-local-key-change-me"

SAMPLE_URLS = [
    # --- legitimate ---
    "https://www.obec.go.th",
    "https://www.moe.go.th/news",
    "https://www.rd.go.th/e-service",
    "https://chula.ac.th/admission",
    "https://www.ku.ac.th",
    "https://mahidol.ac.th/th/home",
    "https://www.bot.or.th",
    "https://www.set.or.th",
    "https://www.google.com",
    "https://github.com/explore",
    "https://www.wikipedia.org",
    "https://scb.co.th",
    "https://www.thairath.co.th",
    "https://www.cmu.ac.th",
    "https://www.kku.ac.th",
    # --- typosquats / phishing ---
    "http://obec.com/verify-account",
    "http://0bec-go-th.xyz/login",
    "https://rd-go-th-refund.online/e-service/login",
    "http://203.0.113.45/obec/secure/login",
    "https://moe.go.th.verify-login.top/signin",
    "http://chula-ac-th-scholarship.info/account/update",
    "https://www.ku.ac.th@phish-site.xyz/login",
    "http://secure-bot-or-th-update.club/webscr",
    "https://set-or-th-dividend.live/confirm",
    "http://m0e.go.th.attacker.com/reset-password",
    "https://kasikornbank-verify.icu/auth/verify",
    "http://thaigov-go-th-grant.buzz/validation",
    "https://customs-go-th-payment.shop/secure/login",
    "http://obec.go.th.evil-domain.net/wp-login.php",
    "https://rsu-ac-th-login.vip/session/expired",
    # --- a few more legitimate to balance ---
    "https://www.customs.go.th",
    "https://www.nstda.or.th",
    "https://www.tu.ac.th",
    "https://www.psu.ac.th",
    "https://www.dbd.go.th",
]


def post(url: str) -> dict | None:
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
        print(f"  ! {url} -> HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {url} -> {exc}")
    return None


def main() -> None:
    print(f"Seeding {API_URL} with {len(SAMPLE_URLS)} sample URLs ...")
    counts: dict[str, int] = {}
    for url in SAMPLE_URLS:
        result = post(url)
        if result:
            label = result["label"]
            counts[label] = counts.get(label, 0) + 1
            print(f"  {label:>10}  {result['score']:.2f}  {url}")
        time.sleep(0.05)
    print("\nDone. Verdicts:", dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
