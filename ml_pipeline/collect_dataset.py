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
    FEEDBACK_CSV,
    FEED_TIMEOUT,
    GENERIC_HOLDOUT_CSV,
    GENERIC_PHISH_SEED_CSV,
    GENERIC_SEED_TRAIN_FRACTION,
    OPENPHISH_URL,
    PHISHTANK_URL,
    RANDOM_SEED,
    RAW_DIR,
    REAL_HOLDOUT_CSV,
    REAL_HOLDOUT_FRACTION,
    THAI_HOLDOUT_CSV,
    THAI_PHISH_SEED_CSV,
    THAI_SEED_TRAIN_FRACTION,
    TARGET_ROWS,
    URLHAUS_URL,
    WHITELIST_CSV,
    ensure_dirs,
)
from ml_pipeline.synthetic_generator import SyntheticGenerator

_FIELDS = [
    "url", "label", "domain_age_days", "is_known_registrar",
    "has_valid_cert", "cert_age_days", "is_self_signed", "whois_ok", "tls_ok",
    # v1.5 simulated TLS-derived columns
    "cert_is_lets_encrypt", "cert_validity_days", "cert_san_count",
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


_THAI_TLDS = (".go.th", ".ac.th", ".or.th", ".co.th")

# A small high-signal seed of 3-letter institutional codes that are too short
# to survive the "len >= 4" filter when auto-deriving brands from the whitelist
# but are nonetheless heavily impersonated (financial regulators, ministries).
_THAI_BRAND_SEED = {
    "rd", "set", "sec", "ktb", "scb", "bbl", "gsb", "ghb",
    "moe", "moi", "mof", "mot", "bot", "pea", "mwa", "dbd",
    "sso", "tat", "sat", "moc", "mod", "doh", "dlt", "dla",
    "dms", "ddc", "dop", "dpr", "doe", "dft", "dft", "dft",
    "ago", "dsi", "nhso", "nbtc",
}


def _load_thai_brands(whitelist_csv: str = WHITELIST_CSV) -> set[str]:
    """Derive Thai brand keywords from the whitelist CSV at runtime.

    Auto-deriving from the whitelist means new agencies added to the CSV
    automatically become recognised as Thai-targeting brands, so the
    routing into the Thai holdout stays in sync with the whitelist.
    """
    brands: set[str] = set(_THAI_BRAND_SEED)
    if not os.path.exists(whitelist_csv):
        return brands
    import csv as _csv
    with open(whitelist_csv, newline="", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            d = (row.get("domain") or "").strip().lower()
            if not d:
                continue
            label = d.split(".")[0]
            # Skip generic / too-short labels to avoid false-positive
            # routing of unrelated phishing into the Thai holdout.
            if len(label) >= 4 and label.isascii() and label.isalpha():
                brands.add(label)
    return brands


_THAI_BRANDS = _load_thai_brands()


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


def _load_thai_phish_seed() -> list[str]:
    """Load the curated Thai-targeting phishing seed corpus (urls only)."""
    if not os.path.exists(THAI_PHISH_SEED_CSV):
        print(f"[seed] no seed corpus at {THAI_PHISH_SEED_CSV} "
              "(run scripts/collect_thai_phishing_seed.py to build it)")
        return []
    urls: list[str] = []
    import csv as _csv
    with open(THAI_PHISH_SEED_CSV, newline="", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            u = (row.get("url") or "").strip()
            if u.startswith(("http://", "https://")):
                urls.append(u)
    print(f"[seed] loaded {len(urls)} curated Thai-targeting phishing URLs")
    return urls


def _load_generic_phish_seed() -> list[str]:
    """Load the committed real generic-phishing snapshot (urls only)."""
    if not os.path.exists(GENERIC_PHISH_SEED_CSV):
        return []
    urls: list[str] = []
    import csv as _csv
    with open(GENERIC_PHISH_SEED_CSV, newline="", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            u = (row.get("url") or "").strip()
            if u.startswith(("http://", "https://")):
                urls.append(u)
    print(f"[seed] loaded {len(urls)} real generic-phishing URLs")
    return urls


def _load_feedback_rows(gen, exclude_urls: set[str]) -> list[dict]:
    """Load confirmed-feedback labels exported from the DB as TRAINING rows.

    Rows are (url, label) pairs written by feedback_retrain.py. We attach
    simulated network features (the URLs do not resolve offline) and drop any
    URL already present in a holdout so feedback can never leak the eval set
    into training. Feedback rows are training-only by construction.
    """
    if not os.path.exists(FEEDBACK_CSV):
        return []
    import csv as _csv

    rows: list[dict] = []
    seen: set[str] = set()
    with open(FEEDBACK_CSV, newline="", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            url = (row.get("url") or "").strip()
            label_raw = (row.get("label") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            if url in exclude_urls or url in seen:
                continue
            try:
                label = int(label_raw)
            except ValueError:
                continue
            if label not in (0, 1):
                continue
            seen.add(url)
            net = gen.sim_network(label, url.startswith("https://"))
            rows.append({"url": url, "label": label, **net})
    if rows:
        print(f"[feedback] folded {len(rows)} confirmed-feedback rows into training")
    return rows


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
    thai_train: list[dict] = []
    generic_train: list[dict] = []
    generic_holdout: list[dict] = []

    # --- curated Thai-targeting seed corpus (always loaded, no network) ---
    seed_urls = _load_thai_phish_seed()
    if seed_urls:
        gen.rng.shuffle(seed_urls)
        n_train = int(round(len(seed_urls) * THAI_SEED_TRAIN_FRACTION))
        for i, url in enumerate(seed_urls):
            net = gen.sim_network(1, url.startswith("https://"))
            row = {"url": url, "label": 1, **net}
            (thai_train if i < n_train else thai_holdout).append(row)
        print(f"[seed] split: train={len(thai_train)}  holdout={len(thai_holdout)}")

    # --- committed generic-phishing snapshot: deterministic 70/30 split into
    #     TRAINING + a reproducible generic cross-check holdout (no network) ---
    generic_urls = _load_generic_phish_seed()
    if generic_urls:
        gen.rng.shuffle(generic_urls)
        g_train = int(round(len(generic_urls) * GENERIC_SEED_TRAIN_FRACTION))
        for i, url in enumerate(generic_urls):
            net = gen.sim_network(1, url.startswith("https://"))
            row = {"url": url, "label": 1, **net}
            (generic_train if i < g_train else generic_holdout).append(row)
        print(f"[seed] generic split: train={len(generic_train)}  "
              f"holdout={len(generic_holdout)}")

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

    # --- confirmed-feedback rows (training only; never the holdout) ---
    holdout_urls = {r["url"] for r in (thai_holdout + real_holdout + generic_holdout)}
    feedback_rows = _load_feedback_rows(gen, exclude_urls=holdout_urls)
    feedback_phish = [r for r in feedback_rows if r["label"] == 1]
    feedback_legit = [r for r in feedback_rows if r["label"] == 0]

    # --- synthetic phishing top-up to balance the classes (training only) ---
    need = (n_legit + len(feedback_legit)
            - len(real_train) - len(thai_train) - len(feedback_phish)
            - len(generic_train))
    synth_phish = gen.generate(n_legit=0, n_phish=max(need, 0))
    print(f"[dataset] synthetic phishing rows: {len(synth_phish)}")

    rows.extend(real_train)
    rows.extend(thai_train)
    rows.extend(generic_train)
    rows.extend(feedback_rows)
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

    # --- write the committed generic-phishing cross-check holdout ---
    if generic_holdout:
        with open(GENERIC_HOLDOUT_CSV, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FIELDS)
            writer.writeheader()
            for r in generic_holdout:
                writer.writerow({k: r.get(k, "") for k in _FIELDS})
        print(f"[dataset] wrote {len(generic_holdout)} generic-phishing holdout "
              f"rows -> {GENERIC_HOLDOUT_CSV}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the labeled dataset")
    parser.add_argument(
        "--no-feeds", action="store_true",
        help="skip live phishing feeds (fully offline)",
    )
    args = parser.parse_args()
    main(use_feeds=not args.no_feeds)
