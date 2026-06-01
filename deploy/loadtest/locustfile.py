"""Locust load test for the phishing detector (A9).

Validates the documented p95 < 250 ms SLO for /check under load. Run against a
STAGING deployment, not production:

    locust -f deploy/loadtest/locustfile.py --host https://staging.example.com

Then open http://localhost:8089 and drive e.g. 200 users. Or headless:

    locust -f deploy/loadtest/locustfile.py --host https://$HOST \
      --headless -u 200 -r 20 -t 2m --csv loadtest

Set API_KEY in the environment for the authenticated endpoints.
"""

from __future__ import annotations

import os
import random

from locust import HttpUser, between, task

API_KEY = os.environ.get("API_KEY", "")

# A mix of safe / suspicious / phishing-looking URLs so scoring is exercised
# across the label space (not just cache hits).
_SAFE = ["https://www.obec.go.th", "https://chula.ac.th", "https://www.bot.or.th"]
_RISKY = [
    "http://obec-verify.xyz/login",
    "http://krungthai-secure.top/account",
    "https://rd-go-th.cc/refund",
]


class CheckUser(HttpUser):
    wait_time = between(0.1, 1.0)

    @task(5)
    def check(self):
        url = random.choice(_SAFE + _RISKY)
        # Add a cache-busting query so a fraction of requests miss the cache.
        if random.random() < 0.3:
            url = f"{url}?n={random.randint(0, 100000)}"
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        with self.client.post(
            "/api/v1/check",
            json={"url": url},
            headers=headers,
            name="/check",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and "label" in resp.text:
                resp.success()
            else:
                resp.failure(f"unexpected {resp.status_code}")

    @task(1)
    def health(self):
        self.client.get("/health/ready", name="/health/ready")
