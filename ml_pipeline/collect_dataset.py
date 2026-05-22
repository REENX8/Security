"""Build the labeled dataset (hybrid: synthetic + optional live feeds).

Strategy
--------
1. Always generate a large, balanced synthetic dataset offline -- this is the
   reliable default and makes the pipeline reproducible with no network.
2. *Optionally* enrich the phishing class with real URLs from PhishTank /
   OpenPhish. Any network failure is logged and ignored; the pipeline still
   produces a complete dataset.

Output: ``data/dataset.csv`` with columns
``url,label,domain_age_days,is_known_registrar,has_valid_cert,
cert_age_days,is_self_signed,whois_ok,tls_ok``.
"""

from __future__ import annotations

import csv
import os

from phish_features import Whitelist

from ml_pipeline.config import (
    DATASET_CSV,
    FEED_TIMEOUT,
    OPENPHISH_URL,
    PHISHTANK_URL,
    RANDOM_SEED,
    RAW_DIR,
    TARGET_ROWS,
    WHITELIST_CSV,
    ensure_dirs,
)
from ml_pipeline.synthetic_generator import SyntheticGenerator

_FIELDS = [
    "url", "label", "domain_age_days", "is_known_registrar",
    "has_valid_cert", "cert_age_days", "is_self_signed", "whois_ok", "tls_ok",
]


def _fetch_feed_urls(max_urls: int) -> list[str]:
    """Best-effort download of real phishing URLs. Returns [] on any failure."""
    try:
        import requests  # local import keeps the dep optional
    except Exception:  # noqa: BLE001
        print("[feeds] 'requests' not available -- skipping live feeds")
        return []

    urls: list[str] = []
    headers = {"User-Agent": "phish-detector-research/1.0"}

    # --- OpenPhish (plain text feed) ---
    try:
        resp = requests.get(OPENPHISH_URL, timeout=FEED_TIMEOUT, headers=headers)
        if resp.ok:
            lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
            urls.extend(lines)
            print(f"[feeds] OpenPhish: +{len(lines)} urls")
    except Exception as exc:  # noqa: BLE001
        print(f"[feeds] OpenPhish unavailable ({exc}) -- skipping")

    # --- PhishTank (JSON; usually needs a registered API key) ---
    try:
        resp = requests.get(PHISHTANK_URL, timeout=FEED_TIMEOUT, headers=headers)
        ct = resp.headers.get("content-type", "")
        if resp.ok and "json" in ct:
            data = resp.json()
            feed = [item["url"] for item in data if item.get("url")]
            urls.extend(feed)
            print(f"[feeds] PhishTank: +{len(feed)} urls")
        else:
            print(f"[feeds] PhishTank returned {resp.status_code} "
                  f"({ct or 'no content-type'}) -- skipping")
    except Exception as exc:  # noqa: BLE001
        print(f"[feeds] PhishTank unavailable ({exc}) -- skipping")

    # Deduplicate, keep http(s) only.
    clean = []
    seen = set()
    for u in urls:
        if u.startswith(("http://", "https://")) and u not in seen:
            seen.add(u)
            clean.append(u)
    if clean:
        os.makedirs(RAW_DIR, exist_ok=True)
        with open(os.path.join(RAW_DIR, "feed_urls.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write("\n".join(clean))
    return clean[:max_urls]


def main(use_feeds: bool = True) -> None:
    ensure_dirs()
    wl = Whitelist.from_csv(WHITELIST_CSV)
    gen = SyntheticGenerator(wl.domains, seed=RANDOM_SEED)

    n_each = TARGET_ROWS // 2
    rows: list[dict] = []

    # --- legitimate (synthetic, derived from the real whitelist) ---
    rows.extend(gen.generate(n_legit=n_each, n_phish=0))
    n_legit = len(rows)
    print(f"[dataset] legitimate rows: {n_legit}")

    # --- real phishing (optional) ---
    real_rows: list[dict] = []
    if use_feeds:
        feed_urls = _fetch_feed_urls(max_urls=n_each // 2)
        for url in feed_urls:
            net = gen.sim_network(1, url.startswith("https://"))
            real_rows.append({"url": url, "label": 1, **net})
    print(f"[dataset] real phishing rows: {len(real_rows)}")

    # --- synthetic phishing top-up to balance the classes ---
    need = n_legit - len(real_rows)
    synth_phish = gen.generate(n_legit=0, n_phish=max(need, 0))
    print(f"[dataset] synthetic phishing rows: {len(synth_phish)}")

    rows.extend(real_rows)
    rows.extend(synth_phish)

    gen.rng.shuffle(rows)

    with open(DATASET_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in _FIELDS})

    n_phish = sum(r["label"] == 1 for r in rows)
    print(f"[dataset] wrote {len(rows)} rows -> {DATASET_CSV}")
    print(f"[dataset]   legitimate={len(rows) - n_phish}  phishing={n_phish}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the labeled dataset")
    parser.add_argument(
        "--no-feeds", action="store_true",
        help="skip live phishing feeds (fully offline)",
    )
    args = parser.parse_args()
    main(use_feeds=not args.no_feeds)
