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

# Cap any single ``target_brand`` to this many examples so the holdout
# evaluation does not over-fit to the most-typed brands (obec, rd, ...).
PER_BRAND_CAP = 4

CURATED_PHISH: list[tuple[str, str]] = [
    # url, target_brand

    # === Cabinet / portal / digital ID ===
    ("https://thaigov.net/auth", "thaigov"),
    ("https://thai-government-update-secure.online/", "thaigov"),
    ("https://login-thaigov-online.cc/account/update.php?id=1234567890abcd", "thaigov"),
    ("https://thаigov.online/login", "thaigov"),                # Cyrillic а
    ("https://thaid-login.com/verify", "thaid"),
    ("https://thaid-app.net/auth/login", "thaid"),
    ("https://thaid-verify.cc/account", "thaid"),
    ("https://thaid.support/reset-password", "thaid"),
    ("https://paotang-th.com/login", "paotang"),
    ("https://paotang-verify.xyz/account", "paotang"),
    ("https://welfare-paotang.online/secure", "paotang"),
    ("https://pao-tang.co/verify", "paotang"),

    # === Revenue / Customs / Excise / Comptroller-General ===
    ("https://rd-refund.com/login", "rd"),
    ("https://www.rd.go.th.refund-tax.com/secure", "rd"),
    ("http://rd-go-th.refund-secure.online/login", "rd"),
    ("https://xn--rd-yia.com/refund", "rd"),                    # Punycode
    ("https://customs-th.online/clearance", "customs"),
    ("https://thai-customs.cc/secure", "customs"),
    ("https://customs-go-th.shop/clearance-fee", "customs"),
    ("https://excise-th.cc/pay", "excise"),
    ("https://excise-go-th.online/duty-payment", "excise"),
    ("https://cgd-go-th.online/verify", "cgd"),
    ("https://cgd-thai.cc/payroll", "cgd"),
    ("https://amlo-thai.online/verify-account", "amlo"),

    # === DBD / Trade Department / Intellectual Property ===
    ("https://dbd-thai.com/verify-account", "dbd"),
    ("https://dbd-go-th.cc/business-registration", "dbd"),
    ("https://ditp-thai.online/login", "ditp"),
    ("https://ipthailand-th.cc/trademark-verify", "ipthailand"),

    # === Central bank / SET / SEC / Insurance regulator ===
    ("https://bot-thai-invest.com/login", "bot"),
    ("https://bot-or-th.cc/secure", "bot"),
    ("https://setbroker.online/verify", "set"),
    ("https://set-or-th.cc/portfolio", "set"),
    ("https://sec-thai.xyz/auth", "sec"),
    ("https://sec-or-th.shop/verify-investor", "sec"),
    ("https://oic-thai.cc/insurance-claim", "oic"),
    ("https://dpa-claim.online/secure", "dpa"),

    # === Major commercial banks (KBank / SCB / BBL / Krungthai / Krungsri / TTB / UOB) ===
    ("https://kasikornbank-th.com/verify", "kbank"),
    ("https://kbank-online.xyz/auth", "kbank"),
    ("https://kаsikornbank.com/login", "kbank"),                # Cyrillic а
    ("https://kbank-2025.shop/secure", "kbank"),
    ("https://scb-easy-app.com/login", "scb"),
    ("http://scb-co-th.update-secure.online/", "scb"),
    ("https://scb-eаsy.cc/auth", "scb"),                        # Cyrillic а
    ("https://www.scb.co.th@phish.online/auth", "scb"),
    ("https://bbl-bangkokbank.shop/login", "bbl"),
    ("http://bangkokbank.com.account-update.cc/auth", "bbl"),
    ("https://bbl-secure.online/transfer", "bbl"),
    ("https://krungthai-secure.com/verify", "krungthai"),
    ("https://krungthai-net.online/auth", "krungthai"),
    ("http://krungthai.com.verify-secure.online/login", "krungthai"),
    ("https://krungthаi.com/secure", "krungthai"),              # Cyrillic а
    ("https://ktb-online.cc/login", "ktb"),
    ("https://ktb-bank-update.shop/account", "ktb"),
    ("https://krungsri-secure.cc/login", "krungsri"),
    ("https://krungsri-online.shop/verify", "krungsri"),
    ("https://ttb-online.cc/login", "ttb"),
    ("https://ttb-secure.shop/auth", "ttb"),
    ("https://uob-secure.cc/verify", "uob"),

    # === State banks (GSB / BAAC / GHB / EXIM / SME) ===
    ("https://gsb-online.cc/login", "gsb"),
    ("https://gsb-secure.shop/account", "gsb"),
    ("https://baac-th.com/verify", "baac"),
    ("https://baac-online.cc/farmer-loan", "baac"),
    ("https://ghbank-secure.online/login", "ghb"),
    ("https://ghb-online.cc/mortgage", "ghb"),
    ("https://exim-thai.cc/trade-finance", "exim"),
    ("https://smebank-th.online/loan", "smebank"),
    ("https://ibank-thai.cc/login", "ibank"),

    # === Ministries (broad coverage) ===
    ("https://moe-th.online/auth", "moe"),
    ("https://moe.go.th.update-portal.cc/secure", "moe"),
    ("https://moe-th-student-login-verify.xyz/", "moe"),
    ("https://mfa-thai.online/visa", "mfa"),
    ("https://mfa-go-th.cc/passport-renewal", "mfa"),
    ("https://moi-th.shop/secure", "moi"),
    ("https://moi-go-th.online/citizen-portal", "moi"),
    ("https://mof-thai.cc/treasury", "mof"),
    ("https://moph-th.cc/secure", "moph"),
    ("https://moph-vaccine.online/register", "moph"),
    ("https://mol-thai.cc/welfare", "mol"),
    ("https://mol-go-th.shop/labour-claim", "mol"),
    ("https://mot-thai.cc/transport-permit", "mot"),
    ("https://moac-thai.online/farmer-aid", "moac"),
    ("https://mnre-thai.cc/forestry-permit", "mnre"),
    ("https://mots-thai.cc/tourist-license", "mots"),
    ("https://mod-thai.cc/recruit", "mod"),
    ("https://moj-thai.cc/legal-aid", "moj"),
    ("https://m-culture-thai.cc/grant", "culture"),
    ("https://industry-thai.online/factory-permit", "industry"),
    ("https://energy-thai.cc/subsidy", "energy"),
    ("https://m-society-thai.online/welfare-claim", "society"),

    # === MHESI / Higher education agencies ===
    ("https://mhesi-th.online/scholarship", "mhesi"),
    ("https://mua-thai.xyz/verify", "mua"),
    ("https://mua-go-th.cc/student-loan", "mua"),

    # === OBEC / vocational / school portals (covered moe above, keep obec separate) ===
    ("https://obec-scholarship.cc/login", "obec"),
    ("https://obec.go.th.scholarship-portal.online/", "obec"),
    ("https://obec.com/login", "obec"),                         # TLD swap
    ("https://оbec.com/verify", "obec"),                        # Cyrillic о
    ("https://ovec-thai.cc/student-grant", "ovec"),
    ("https://opec-thai.online/private-school", "opec"),

    # === Public universities (Chulalongkorn / Mahidol / KU / Thammasat / others) ===
    ("https://chulalongkorn.com/secure", "chula"),
    ("https://chula-ac-th-mail-login.online/", "chula"),
    ("https://chulа.com/login", "chula"),                       # Cyrillic а
    ("https://xn--chula-jjb.com/verify", "chula"),              # Punycode
    ("https://mahidol-th.com/student-portal", "mahidol"),
    ("https://mu-online.cc/login", "mahidol"),
    ("https://ku-online.com/student-login", "ku"),
    ("https://kasetsart-th.online/admission", "ku"),
    ("https://tu-online.com/login", "tu"),
    ("https://thammasat-th.cc/student-portal", "tu"),
    ("https://kku-online.com/login", "kku"),
    ("https://khonkaen-uni-th.cc/admission", "kku"),
    ("https://psu-online.com/portal", "psu"),
    ("https://cmu-online.com/login", "cmu"),
    ("https://chiangmai-uni-th.cc/student", "cmu"),
    ("https://kmutt-ac-th-portal-secure.shop/", "kmutt"),
    ("https://kmutt-online.cc/login", "kmutt"),
    ("https://kmitl-th.com/student-login", "kmitl"),
    ("https://swu-online.com/student", "swu"),
    ("https://ramkhamhaeng-th.com/portal", "ru"),
    ("https://nida-thai.cc/login", "nida"),
    ("https://mfu-online.cc/portal", "mfu"),

    # === Provincial / Bangkok / DOPA / local admin ===
    ("https://dopa-verify.online/account", "dopa"),
    ("https://thai-id-card.cc/renew", "dopa"),
    ("https://dopa-go-th.shop/card-renewal", "dopa"),
    ("https://bma-online.cc/citizen", "bangkok"),
    ("https://bangkok-services.online/permit", "bangkok"),
    ("https://dla-thai.cc/local-permit", "dla"),

    # === Royal Thai Police / Immigration / Cybercrime ===
    ("https://rtp-online.cc/verify", "police"),
    ("https://thaipolice-verify.shop/account", "police"),
    ("https://imm-th.online/visa-extension", "immigration"),
    ("https://immigration-verify.cc/secure", "immigration"),
    ("https://tcsd-thai.cc/cyber-report", "tcsd"),

    # === Welfare / Social Security / NHSO ===
    ("https://sso-benefits.online/claim", "sso"),
    ("https://sso-th.cc/login", "sso"),
    ("https://www.sso.go.th.welfare-claim.online/", "sso"),
    ("https://sso-go-th.shop/unemployment", "sso"),
    ("https://nhso-claim.online/login", "nhso"),
    ("https://nhso-vaccine.cc/register", "nhso"),
    ("https://fda-thai.cc/license", "fda"),
    ("https://ddc-vaccine.online/register", "ddc"),
    ("https://ddc-thai.cc/disease-report", "ddc"),

    # === State enterprises (utilities, post, transport, telecom) ===
    ("https://mea-online.cc/bill", "mea"),
    ("https://mea-thai.shop/payment", "mea"),
    ("https://pea-thai.shop/payment", "pea"),
    ("https://pea-bill.cc/online", "pea"),
    ("https://mwa-online.xyz/account", "mwa"),
    ("https://mwa-bill.online/pay", "mwa"),
    ("https://pwa-bill.online/pay", "pwa"),
    ("https://egat-online.cc/contractor", "egat"),
    ("https://egat-thai.shop/auction", "egat"),
    ("https://thailandpost-track.com/redelivery", "thailandpost"),
    ("https://thpost-fee.online/payment", "thailandpost"),
    ("https://thai-post-package.cc/track", "thailandpost"),
    ("http://thailandpost.co.th.parcel-clearance.online/", "thailandpost"),
    ("https://nt-online.cc/verify", "nt"),
    ("https://nt-mobile.cc/recharge", "nt"),
    ("https://railway-thai.cc/refund", "railway"),
    ("https://airportthai-claim.online/lost-baggage", "airportthai"),

    # === Telecom (private carriers) ===
    ("https://ais-rewards.online/claim", "ais"),
    ("https://ais-mobile.cc/topup", "ais"),
    ("https://truepoint-redeem.xyz/login", "true"),
    ("https://true-online.cc/secure", "true"),
    ("https://dtac-reward.shop/secure", "dtac"),
    ("https://dtac-mobile.cc/topup", "dtac"),

    # === Logistics / parcel scams (Kerry / Flash / JT) ===
    ("https://kerry-th.cc/redelivery", "kerry"),
    ("https://kerryexpress-redelivery.online/fee", "kerry"),
    ("https://flash-th.cc/redelivery", "flash"),
    ("https://flashexpress-fee.online/payment", "flash"),
    ("https://jt-th.cc/track", "jt"),
    ("https://jtexpress-fee.online/clearance", "jt"),

    # === E-commerce coupon / promo scams ===
    ("https://lazada-coupon.cc/redeem", "lazada"),
    ("https://lazada-secure.online/login", "lazada"),
    ("https://shopee-promo.cc/redeem", "shopee"),
    ("https://shopee-coin.online/claim", "shopee"),

    # === Tourism / sports / culture ===
    ("https://tat-thai.cc/registration", "tat"),
    ("https://sat-thai.online/athlete-grant", "sat"),

    # === Generic IP-host / @-trick attacks against Thai brands ===
    ("http://203.0.113.45/obec/login", "obec"),
    ("http://198.51.100.7/rd-refund/", "rd"),
    ("https://obec.go.th@evil.xyz/login", "obec"),
    ("http://thaigov.go.th@malicious.shop/", "thaigov"),
    ("https://obec.go.th.evil-server.xyz/login", "obec"),
    ("https://kbank.co.th.account-verify.online/login", "kbank"),

    # === Brand-stuffed / hyphenated typosquats (mixed brands) ===
    ("https://obec-school-portal-login-secure.cc/", "obec"),
    ("https://rd-go-th-tax-refund-2025.cc/login", "rd"),
    ("https://secure-update-account-th.shop/?ref=obec.go.th", "obec"),
    ("https://account-verify-rd-go-th.online/login.html", "rd"),
]


def _cap_per_brand(rows: list[tuple[str, str]], cap: int) -> list[tuple[str, str]]:
    """Trim ``rows`` so no single brand appears more than ``cap`` times.

    Order is preserved -- the first ``cap`` URLs for each brand survive,
    so list-position is how we curate which examples represent each brand.
    """
    seen: dict[str, int] = {}
    out: list[tuple[str, str]] = []
    dropped: list[tuple[str, str]] = []
    for url, brand in rows:
        if seen.get(brand, 0) >= cap:
            dropped.append((url, brand))
            continue
        seen[brand] = seen.get(brand, 0) + 1
        out.append((url, brand))
    if dropped:
        over = {b: c for b, c in seen.items() if c == cap}
        print(f"[seed] capped {len(dropped)} URLs across {len(over)} brands "
              f"at {cap} examples each")
    return out


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
    """Rebuild the corpus from ``curated + live``.

    ``existing`` is consulted only to preserve ``collected_at`` for URLs
    that survive the rebuild -- so re-running on a different day does not
    churn the audit trail. URLs that drop out of the curated list (e.g.
    when a brand's cap is lowered) are dropped from the CSV.
    """
    out: dict[str, dict] = {}
    for url, target in curated:
        prior = existing.get(url, {})
        out[url] = {
            "url": url, "label": "1", "source": SOURCE_CURATED,
            "target_brand": target,
            "collected_at": prior.get("collected_at") or today,
        }
    for url, source, target in live:
        if url in out:
            continue  # curated entry already wins
        prior = existing.get(url, {})
        out[url] = {
            "url": url, "label": "1", "source": source,
            "target_brand": target,
            "collected_at": prior.get("collected_at") or today,
        }
    print(f"[seed] {len(out)} total rows "
          f"({sum(1 for r in out.values() if r['source'] == SOURCE_CURATED)} curated"
          f" + {sum(1 for r in out.values() if r['source'] != SOURCE_CURATED)} live)")
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
    # Always rebuild from CURATED_PHISH so editing the source list takes effect
    # immediately. Existing rows are kept only for their collected_at value if
    # the URL is still in the curated list (so re-running on a different day
    # does not churn the audit trail).
    existing = _existing(args.out)
    print(f"[seed] loaded {len(existing)} existing rows from {args.out}")

    brands = _load_whitelist_brands()
    print(f"[seed] {len(brands)} brand keywords derived from whitelist")

    # Cap curated list per-brand BEFORE merging so a single brand cannot
    # dominate the holdout evaluation.
    capped_curated = _cap_per_brand(CURATED_PHISH, PER_BRAND_CAP)

    live = [] if args.no_fetch else _fetch_live(brands)
    # Cap live additions too (per-brand across the full corpus, accounting for
    # the curated allocation that already filled some brands' budgets).
    if live:
        budget = {b: sum(1 for _, b2 in capped_curated if b2 == b) for _, _, b in live}
        live_capped: list[tuple[str, str, str]] = []
        for url, source, brand in live:
            used = budget.get(brand, 0)
            if used >= PER_BRAND_CAP:
                continue
            budget[brand] = used + 1
            live_capped.append((url, source, brand))
        live = live_capped

    merged = _merge(existing, capped_curated, live, today)

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
