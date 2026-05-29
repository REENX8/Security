#!/usr/bin/env python3
"""Seed the backend with sample checks so the dashboard has data.

Two modes:

  HTTP mode (default) -- posts URLs to a running backend's /check API.
      python scripts/seed_demo.py [API_URL] [API_KEY]
      Defaults: http://localhost:8000  /  dev-local-key-change-me
      Records all land at "now", so the 7-day chart / heatmap show one spike.

  Backfill mode -- writes scored rows directly to the DB with realistic
      timestamps spread over the last 14 days (business-hour weighted) and
      clusters phishing campaigns, so every dashboard page looks alive for a
      live demo.
      python scripts/seed_demo.py --backfill
      Honours DATABASE_URL / MODEL_DIR (defaults match scripts/demo_setup.sh).

HTTP mode uses only the standard library. Backfill mode imports the backend.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

# --- shared corpus ---------------------------------------------------------

LEGIT_URLS = [
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
    "https://www.customs.go.th",
    "https://www.nstda.or.th",
    "https://www.tu.ac.th",
    "https://www.psu.ac.th",
    "https://www.dbd.go.th",
    "https://www.mhesi.go.th",
    "https://www.dlt.go.th",
    "https://krungsri.com",
    "https://www.ktb.co.th",
]

PHISH_URLS = [
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
    # campaign clusters: same kit, multiple hosts (shared fingerprint shape)
    "https://rd-go-th-refund1.online/e-service/login",
    "https://rd-go-th-refund2.online/e-service/login",
    "https://rd-go-th-refund3.online/e-service/login",
    "https://ktb-verify-secure1.icu/auth/verify",
    "https://ktb-verify-secure2.icu/auth/verify",
]

SAMPLE_URLS = LEGIT_URLS + PHISH_URLS


# === HTTP mode =============================================================

def _http_seed(api_url: str, api_key: str) -> None:
    def post(url: str) -> dict | None:
        body = json.dumps({"url": url}).encode()
        req = urllib.request.Request(
            f"{api_url}/api/v1/check",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "X-API-Key": api_key},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            print(f"  ! {url} -> HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {url} -> {exc}")
        return None

    print(f"Seeding {api_url} with {len(SAMPLE_URLS)} sample URLs ...")
    counts: dict[str, int] = {}
    for url in SAMPLE_URLS:
        result = post(url)
        if result:
            label = result["label"]
            counts[label] = counts.get(label, 0) + 1
            print(f"  {label:>10}  {result['score']:.2f}  {url}")
        time.sleep(0.05)
    print("\nDone. Verdicts:", dict(sorted(counts.items())))


# === Backfill mode =========================================================

def _backfill(days: int = 14, total: int = 240) -> None:
    """Write scored rows directly to the DB with spread-out timestamps."""
    import asyncio
    import datetime as dt
    import os
    import random
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "backend"))
    sys.path.insert(0, str(root))  # for the phish_features package

    # Match demo_setup.sh defaults unless the caller overrides via env.
    os.environ.setdefault(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{root / 'backend' / 'demo_phish.db'}",
    )
    os.environ.setdefault("MODEL_DIR", str(root / "models"))
    os.environ.setdefault("WHITELIST_PATH", str(root / "models" / "whitelist.json"))
    os.environ.setdefault("ENABLE_WHOIS", "false")
    os.environ.setdefault("ENABLE_TLS", "false")
    os.environ.setdefault("ENABLE_CACHE", "false")
    os.environ.setdefault("API_KEY", "dev-local-key-change-me")

    from app.campaigns import record_campaign  # noqa: E402
    from app.database import SessionLocal, init_db  # noqa: E402
    from app.ml.loader import load_scorer  # noqa: E402
    from app.models import Label, UrlCheck  # noqa: E402

    rng = random.Random(2026)

    def random_ts(now: dt.datetime) -> dt.datetime:
        # recency-weighted day, business-hour-weighted time
        day = int(rng.triangular(0, days, days * 0.35))
        hour = rng.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 1, 2, 4, 7, 9, 9, 8,
                     7, 7, 8, 8, 7, 6, 5, 5, 4, 3, 2, 1],
        )[0]
        return now - dt.timedelta(
            days=day, hours=hour, minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
        )

    async def run() -> None:
        print("Loading model ...")
        scorer = load_scorer()
        await init_db()

        # Score each unique URL once, then replay it many times with
        # different timestamps. Legit URLs are checked more often than phish.
        plan: list[str] = []
        for u in LEGIT_URLS:
            plan += [u] * rng.randint(5, 11)
        for u in PHISH_URLS:
            plan += [u] * rng.randint(2, 6)
        rng.shuffle(plan)
        plan = plan[:total]

        scored: dict[str, dict] = {}
        for u in set(plan):
            scored[u] = scorer.score(u)

        now = dt.datetime.now(dt.timezone.utc)
        counts: dict[str, int] = {}
        async with SessionLocal() as session:
            for i, u in enumerate(plan):
                r = scored[u]
                ts = random_ts(now)
                row = UrlCheck(
                    url=r["url"][:2048],
                    score=r["score"],
                    label=Label(r["label"]),
                    reason=r["reason"][:512],
                    features=r["features"],
                    rules=r.get("rules"),
                    closest_domain=r.get("closest_domain"),
                    edit_distance=r.get("edit_distance"),
                    checked_at=ts,
                )
                session.add(row)
                counts[r["label"]] = counts.get(r["label"], 0) + 1
                if r["label"] in ("phishing", "suspicious"):
                    await session.flush()
                    await record_campaign(
                        session,
                        url=r["url"],
                        closest_domain=r.get("closest_domain"),
                        seen_at=ts,
                    )
                if i % 40 == 0:
                    await session.commit()
            await session.commit()

        print(f"Backfilled {len(plan)} checks over {days} days.")
        print("Verdicts:", dict(sorted(counts.items())))

    asyncio.run(run())


# === entrypoint ============================================================

def main() -> None:
    args = sys.argv[1:]
    if "--backfill" in args:
        _backfill()
        return
    api_url = (args[0] if args else "http://localhost:8000").rstrip("/")
    api_key = args[1] if len(args) > 1 else "dev-local-key-change-me"
    _http_seed(api_url, api_key)


if __name__ == "__main__":
    main()
