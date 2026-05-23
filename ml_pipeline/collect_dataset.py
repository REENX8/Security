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
    REAL_HOLDOUT_CSV,
    REAL_HOLDOUT_FRACTION,
    THAI_HOLDOUT_CSV,
    TARGET_ROWS,
    URLHAUS_URL,
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


def _fetch_urlhaus(max_urls: int) -> list[str]:
    """Best-effort fetch from URLhaus recent-URLs API (no API key required)."""
    try:
        import requests
    except Exception:  # noqa: BLE001
        return []
    try:
        resp = requests.post(URLHAUS_URL, timeout=FEED_TIMEOUT)
        if resp.ok and "json" in resp.headers.get("content-type", ""):
            data = resp.json()
            urls = [
                e["url"]
                for e in data.get("urls", [])
                if e.get("url") and e.get("url_status") == "online"
                and e["url"].startswith(("http://", "https://"))
            ]
            print(f"[feeds] URLhaus: +{len(urls)} online urls")
            return urls[:max_urls]
    except Exception as exc:  # noqa: BLE001
        print(f"[feeds] URLhaus unavailable ({exc}) -- skipping")
    return []


_THAI_BRANDS = {
    "moe", "obec", "rd", "dbd", "dopa", "dsi", "ago", "parliament",
    "senate", "thaigov", "mahidol", "chula", "kasetsart", "kmutt",
    "kmitl", "kbank", "scb", "ktb", "bbl", "gsb", "bot", "set",
    "sec", "egat", "pea", "mwa", "pwa", "ntplc", "airportthai",
    "thaipost", "moph", "moi", "mof", "mfa", "mnre",
}
_THAI_TLDS = (".go.th", ".ac.th", ".or.th", ".co.th")


def _is_thai_targeting(url: str) -> bool:
    """Return True if url appears to impersonate a Thai government/financial brand."""
    url_lower = url.lower()
    # Subdomain-spoof pattern: contains a Thai TLD sub-string (not as the actual TLD)
    for tld in _THAI_TLDS:
        idx = url_lower.find(tld)
        if idx != -1 and idx + len(tld) < len(url_lower):
            return True
    # Brand label appears in the registered domain on a non-.th TLD
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        if host.endswith(_THAI_TLDS):
            return False  # actual Thai TLD — legitimate candidate, not a spoof
        labels = host.lower().split(".")
        for label in labels:
            if label in _THAI_BRANDS:
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


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

    # --- real phishing (optional) -- split into training + held-out test ---
    real_train: list[dict] = []
    real_holdout: list[dict] = []
    thai_holdout: list[dict] = []
    if use_feeds:
        feed_urls = _fetch_feed_urls(max_urls=n_each // 2)
        feed_urls += _fetch_urlhaus(max_urls=n_each // 4)
        # Deduplicate after combining feeds.
        seen: set[str] = set()
        feed_urls = [u for u in feed_urls if not (u in seen or seen.add(u))]  # type: ignore[func-returns-value]

        # Separate Thai-targeting URLs into their own always-held-out set.
        thai_urls = [u for u in feed_urls if _is_thai_targeting(u)]
        non_thai_urls = [u for u in feed_urls if not _is_thai_targeting(u)]
        print(f"[feeds] Thai-targeting URLs found: {len(thai_urls)}")

        for url in thai_urls:
            net = gen.sim_network(1, url.startswith("https://"))
            thai_holdout.append({"url": url, "label": 1, **net})

        gen.rng.shuffle(non_thai_urls)
        n_holdout = int(round(len(non_thai_urls) * REAL_HOLDOUT_FRACTION))
        for i, url in enumerate(non_thai_urls):
            net = gen.sim_network(1, url.startswith("https://"))
            row = {"url": url, "label": 1, **net}
            (real_holdout if i < n_holdout else real_train).append(row)
    print(f"[dataset] real phishing -- train: {len(real_train)}  "
          f"holdout: {len(real_holdout)}  thai-holdout: {len(thai_holdout)}")

    # --- synthetic phishing top-up to balance the classes (training only) ---
    need = n_legit - len(real_train)
    synth_phish = gen.generate(n_legit=0, n_phish=max(need, 0))
    print(f"[dataset] synthetic phishing rows: {len(synth_phish)}")

    rows.extend(real_train)
    rows.extend(synth_phish)
    gen.rng.shuffle(rows)

    with open(DATASET_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in _FIELDS})

    n_phish = sum(r["label"] == 1 for r in rows)
    print(f"[dataset] wrote {len(rows)} training rows -> {DATASET_CSV}")
    print(f"[dataset]   legitimate={len(rows) - n_phish}  phishing={n_phish}")

    # --- write the held-out real-phishing test set ---
    if real_holdout:
        with open(REAL_HOLDOUT_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FIELDS)
            writer.writeheader()
            for r in real_holdout:
                writer.writerow({k: r.get(k, "") for k in _FIELDS})
        print(f"[dataset] wrote {len(real_holdout)} real-phishing holdout "
              f"rows -> {REAL_HOLDOUT_CSV}")
    else:
        print("[dataset] no real-phishing holdout written (no feed URLs)")

    # --- write the Thai-specific phishing holdout (always held-out, never trained) ---
    if thai_holdout:
        with open(THAI_HOLDOUT_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FIELDS)
            writer.writeheader()
            for r in thai_holdout:
                writer.writerow({k: r.get(k, "") for k in _FIELDS})
        print(f"[dataset] wrote {len(thai_holdout)} Thai-targeting phishing holdout "
              f"rows -> {THAI_HOLDOUT_CSV}")
    else:
        print("[dataset] no Thai-specific phishing holdout written "
              "(none found in feeds — expected for most environments)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the labeled dataset")
    parser.add_argument(
        "--no-feeds", action="store_true",
        help="skip live phishing feeds (fully offline)",
    )
    args = parser.parse_args()
    main(use_feeds=not args.no_feeds)
