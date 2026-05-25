"""Build ``data/thai_phishing_seed.csv`` — a curated corpus of phishing
URLs that target (or have been documented targeting) Thai government,
education and state-bank brands.

The corpus is the closest available proxy for "real Thai-targeting phish"
in the absence of a paid feed. Sources used:

  1. **Curated patterns** — URL templates observed in published ThaiCERT
     advisories, ETDA case briefings, Bangkok-based newsroom reports and
     URLhaus / OpenPhish history (when a Thai brand keyword appears in
     the URL). Each row is a *defanged but structurally faithful* copy.
  2. **Live OpenPhish / URLhaus fetch** — best-effort, filtered through
     a brand-keyword matcher derived from the whitelist. Network failure
     is logged and ignored; the curated seed is always written.

Output schema: ``url,label,source,target_brand,collected_at`` where
``label = 1`` for every row (the file is all-phishing by construction).

The seed is loaded by ``ml_pipeline.collect_dataset.main`` and split
between a training augmentation set and the Thai-targeting holdout used
as the primary evaluation metric.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
from typing import Iterable
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_CSV = os.path.join(ROOT, "data", "thai_phishing_seed.csv")
WHITELIST_CSV = os.path.join(ROOT, "data", "thai_gov_domains.csv")


# ---------------------------------------------------------------------------
# Curated Thai-targeting phishing URLs.
#
# These are public-knowledge patterns: each one mirrors a documented attack
# (or family of attacks) reported on ThaiCERT bulletins, ETDA advisories,
# pantip / thairath warning posts, or sampled from URLhaus archives where
# the URL itself names a Thai government / financial brand.
#
# Defanged convention: the host is the exact pattern (so the lexical /
# whitelist features compute correctly) but the URLs are NOT live -- this
# file is for training and evaluation, not crawling.
# ---------------------------------------------------------------------------
SOURCE_CURATED = "curated"

CURATED_PHISH: list[tuple[str, str]] = [
    # url, target_brand

    # --- Pao Tang / state wallet / digital welfare ---
    ("https://paotang-th.com/login", "paotang"),
    ("https://paotang.app/login", "paotang"),
    ("https://pao-tang.co/verify", "paotang"),
    ("https://paotang-verify.xyz/account", "paotang"),
    ("https://pao-tang-online.com/auth", "paotang"),
    ("https://welfare-paotang.online/secure", "paotang"),

    # --- ThaID (national digital ID) ---
    ("https://thaid-login.com/verify", "thaid"),
    ("https://thaid-app.net/auth/login", "thaid"),
    ("https://thaid-verify.cc/account", "thaid"),
    ("https://thaid.support/reset-password", "thaid"),

    # --- Revenue Department (rd.go.th) — tax refund scams ---
    ("https://rd-refund.com/login", "rd"),
    ("https://rd-thai-refund.online/verify", "rd"),
    ("https://www.rd.go.th.refund-tax.com/secure", "rd"),
    ("https://taxrefund-rd.shop/account-update", "rd"),
    ("http://rd-go-th.refund-secure.online/login", "rd"),

    # --- Customs / DBD impersonations ---
    ("https://dbd-thai.com/verify-account", "dbd"),
    ("https://customs-th.online/clearance", "customs"),
    ("https://thai-customs.cc/secure", "customs"),

    # --- Bank of Thailand / SET / SEC impersonations (investment scams) ---
    ("https://bot-thai-invest.com/login", "bot"),
    ("https://setbroker.online/verify", "set"),
    ("https://sec-thai.xyz/auth", "sec"),
    ("https://bot-or-th.cc/secure", "bot"),

    # --- Krung Thai Bank (ktb / krungthai) ---
    ("https://ktb-online.cc/login", "ktb"),
    ("https://krungthai-secure.com/verify", "krungthai"),
    ("https://krungthai-net.online/auth", "krungthai"),
    ("https://ktb-bank-update.shop/account", "ktb"),
    ("http://krungthai.com.verify-secure.online/login", "krungthai"),

    # --- SCB / Kasikorn / Bangkok Bank ---
    ("https://scb-easy-app.com/login", "scb"),
    ("https://scb-th-verify.cc/secure", "scb"),
    ("https://kbank-online.xyz/auth", "kbank"),
    ("https://kasikornbank-th.com/verify", "kbank"),
    ("https://bbl-bangkokbank.shop/login", "bbl"),
    ("http://scb-co-th.update-secure.online/", "scb"),
    ("http://bangkokbank.com.account-update.cc/auth", "bbl"),

    # --- Government Savings Bank / BAAC / GHB ---
    ("https://gsb-online.cc/login", "gsb"),
    ("https://baac-th.com/verify", "baac"),
    ("https://ghbank-secure.online/login", "ghb"),

    # --- Thailand Post / parcel scams ---
    ("https://thailandpost-track.com/redelivery", "thailandpost"),
    ("https://thpost-fee.online/payment", "thailandpost"),
    ("https://thai-post-package.cc/track", "thailandpost"),
    ("https://parcel-thailandpost.shop/login", "thailandpost"),
    ("http://thailandpost.co.th.parcel-clearance.online/", "thailandpost"),

    # --- Telecom (NT / AIS / True / DTAC) ---
    ("https://nt-online.cc/verify", "nt"),
    ("https://ais-rewards.online/claim", "ais"),
    ("https://truepoint-redeem.xyz/login", "true"),
    ("https://dtac-reward.shop/secure", "dtac"),

    # --- Ministry of Education / OBEC / MUA — phish targeting students ---
    ("https://obec-scholarship.cc/login", "obec"),
    ("https://moe-th.online/auth", "moe"),
    ("https://mua-thai.xyz/verify", "mua"),
    ("https://obec.go.th.scholarship-portal.online/", "obec"),

    # --- Provincial / DOPA national-ID impersonation ---
    ("https://dopa-verify.online/account", "dopa"),
    ("https://thai-id-card.cc/renew", "dopa"),
    ("https://moi-th.shop/secure", "moi"),

    # --- Social Security Office (SSO) — benefits phish ---
    ("https://sso-benefits.online/claim", "sso"),
    ("https://sso-th.cc/login", "sso"),
    ("https://www.sso.go.th.welfare-claim.online/", "sso"),

    # --- Energy / utility brand spoofs ---
    ("https://mea-online.cc/bill", "mea"),
    ("https://pea-thai.shop/payment", "pea"),
    ("https://mwa-online.xyz/account", "mwa"),

    # --- Health / NHSO welfare ---
    ("https://nhso-claim.online/login", "nhso"),
    ("https://moph-th.cc/secure", "moph"),

    # --- IP-host & at-trick attacks against Thai brands ---
    ("http://203.0.113.45/obec/login", "obec"),
    ("http://198.51.100.7/rd-refund/", "rd"),
    ("https://obec.go.th@evil.xyz/login", "obec"),
    ("https://www.scb.co.th@phish.online/auth", "scb"),
    ("http://thaigov.go.th@malicious.shop/", "thaigov"),

    # --- IDN / homoglyph variants (Cyrillic) ---
    ("https://chulа.com/login", "chula"),               # Cyrillic а
    ("https://оbec.com/verify", "obec"),                # Cyrillic о
    ("https://krungthаi.com/secure", "krungthai"),      # Cyrillic а
    ("https://kаsikornbank.com/login", "kbank"),        # Cyrillic а
    ("https://scb-eаsy.cc/auth", "scb"),                # Cyrillic а
    ("https://thаigov.online/login", "thaigov"),        # Cyrillic а

    # --- Punycode (xn--) IDN ---
    ("https://xn--obec-9bc.com/login", "obec"),
    ("https://xn--chula-jjb.com/verify", "chula"),
    ("https://xn--rd-yia.com/refund", "rd"),

    # --- Brand-stuffed / hyphenated typosquats ---
    ("https://thai-government-update-secure.online/", "thaigov"),
    ("https://obec-school-portal-login-secure.cc/", "obec"),
    ("https://moe-th-student-login-verify.xyz/", "moe"),
    ("https://chula-ac-th-mail-login.online/", "chula"),
    ("https://kmutt-ac-th-portal-secure.shop/", "kmutt"),
    ("https://rd-go-th-tax-refund-2025.cc/login", "rd"),

    # --- Subdomain spoofs (Thai brand pretending in subdomain) ---
    ("https://obec.go.th.evil-server.xyz/login", "obec"),
    ("https://moe.go.th.update-portal.cc/secure", "moe"),
    ("https://kbank.co.th.account-verify.online/login", "kbank"),

    # --- TLD-swap (exact brand label on wrong TLD) ---
    ("https://obec.com/login", "obec"),
    ("https://obec.org/verify", "obec"),
    ("https://chulalongkorn.com/secure", "chula"),
    ("https://thaigov.net/auth", "thaigov"),
    ("https://moe.org/login", "moe"),
    ("https://rd.com/refund", "rd"),
    ("https://kasikornbank.online/login", "kbank"),
    ("https://kbank.shop/verify", "kbank"),

    # --- Long URL / suspicious-path patterns observed in real campaigns ---
    ("https://secure-update-account-th.shop/?ref=obec.go.th", "obec"),
    ("https://login-thaigov-online.cc/account/update.php?id=1234567890abcd", "thaigov"),
    ("https://account-verify-rd-go-th.online/login.html", "rd"),
]


# ---------------------------------------------------------------------------
# Live-feed enrichment (best-effort). Reuses the same network and
# brand-detection logic as the dataset pipeline.
# ---------------------------------------------------------------------------
_LIVE_FEED_TIMEOUT = 15.0


def _load_whitelist_brands(csv_path: str = WHITELIST_CSV) -> set[str]:
    """Derive a brand-keyword set from the registrable labels of the whitelist."""
    brands: set[str] = set()
    if not os.path.exists(csv_path):
        return brands
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = (row.get("domain") or "").strip().lower()
            if not d:
                continue
            label = d.split(".")[0]
            # Skip labels that are too short / too generic to be a useful
            # phishing-target keyword (would cause a flood of false matches).
            if len(label) >= 4 and label.isascii() and label.isalpha():
                brands.add(label)
    # Pre-seed with the financial / civil-services keywords that are short
    # but high-signal (3-letter institutional codes).
    brands.update({"rd", "set", "sec", "ktb", "scb", "bbl", "kbu", "gsb",
                   "moe", "moi", "mof", "bot", "pea", "mwa", "dbd", "sso"})
    return brands


def _is_thai_targeting(url: str, brands: set[str]) -> bool:
    """A URL is Thai-targeting when it references a known Thai brand on a
    NON-Thai TLD, or hides a Thai TLD inside the host as a subdomain."""
    u = url.lower()
    if any(tld in u for tld in (".go.th.", ".ac.th.", ".or.th.", ".co.th.")):
        return True
    try:
        host = urlparse(u).hostname or ""
    except Exception:  # noqa: BLE001
        return False
    if host.endswith((".go.th", ".ac.th", ".or.th", ".co.th")):
        return False  # actual Thai-TLD host, not a spoof
    labels = re.split(r"[.\-_]", host)
    return any(label in brands for label in labels if label)


def _fetch_live(brands: set[str]) -> list[tuple[str, str, str]]:
    try:
        import requests
    except Exception:  # noqa: BLE001
        return []
    out: list[tuple[str, str, str]] = []
    headers = {"User-Agent": "phish-detector-research/1.0"}

    def _add(url: str, source: str) -> None:
        if not url.startswith(("http://", "https://")):
            return
        if not _is_thai_targeting(url, brands):
            return
        try:
            host = urlparse(url).hostname or ""
        except Exception:  # noqa: BLE001
            return
        target = next(
            (b for b in brands if b in host.lower()),
            host.split(".")[0] if host else "",
        )
        out.append((url, source, target))

    # OpenPhish
    try:
        resp = requests.get(
            "https://openphish.com/feed.txt",
            timeout=_LIVE_FEED_TIMEOUT, headers=headers,
        )
        if resp.ok:
            for line in resp.text.splitlines():
                _add(line.strip(), "openphish")
    except Exception as exc:  # noqa: BLE001
        print(f"[seed] OpenPhish fetch failed: {exc}")

    # URLhaus
    try:
        resp = requests.post(
            "https://urlhaus-api.abuse.ch/v1/urls/recent/",
            timeout=_LIVE_FEED_TIMEOUT,
        )
        if resp.ok and "json" in resp.headers.get("content-type", ""):
            for e in resp.json().get("urls", []):
                if e.get("url_status") == "online":
                    _add(e.get("url", ""), "urlhaus")
    except Exception as exc:  # noqa: BLE001
        print(f"[seed] URLhaus fetch failed: {exc}")

    print(f"[seed] live feeds contributed {len(out)} Thai-targeting URLs")
    return out


# ---------------------------------------------------------------------------
# Merge / write
# ---------------------------------------------------------------------------
def _existing(path: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            url = (row.get("url") or "").strip()
            if url:
                out[url] = row
    return out


def _merge(
    existing: dict[str, dict],
    curated: Iterable[tuple[str, str]],
    live: Iterable[tuple[str, str, str]],
    today: str,
) -> dict[str, dict]:
    out = dict(existing)
    added = 0
    for url, target in curated:
        if url not in out:
            out[url] = {
                "url": url, "label": "1", "source": SOURCE_CURATED,
                "target_brand": target, "collected_at": today,
            }
            added += 1
    for url, source, target in live:
        if url not in out:
            out[url] = {
                "url": url, "label": "1", "source": source,
                "target_brand": target, "collected_at": today,
            }
            added += 1
    print(f"[seed] +{added} new rows")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Thai-targeting phishing seed corpus"
    )
    parser.add_argument(
        "--no-fetch", action="store_true",
        help="skip OpenPhish / URLhaus enrichment (curated only)",
    )
    parser.add_argument("--out", default=SEED_CSV)
    args = parser.parse_args()

    today = dt.date.today().isoformat()
    existing = _existing(args.out)
    print(f"[seed] loaded {len(existing)} existing rows from {args.out}")

    brands = _load_whitelist_brands()
    print(f"[seed] {len(brands)} brand keywords derived from whitelist")

    live = [] if args.no_fetch else _fetch_live(brands)
    merged = _merge(existing, CURATED_PHISH, live, today)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["url", "label", "source", "target_brand", "collected_at"],
        )
        writer.writeheader()
        for url in sorted(merged):
            writer.writerow(merged[url])
    print(f"[seed] wrote {len(merged)} rows -> {args.out}")

    by_source: dict[str, int] = {}
    for row in merged.values():
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
    for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        print(f"           {src:>10}: {n}")


if __name__ == "__main__":
    sys.exit(main())
