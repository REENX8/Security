"""Synthetic URL generator.

Produces a realistic, balanced, fully-offline dataset:

  * legitimate URLs  -> real Thai gov/edu domains with plausible paths
  * phishing URLs    -> typosquats, subdomain spoofs, IP hosts, @-tricks,
                        long hyphenated brand-stuffed domains

Because synthetic URLs do not resolve, each row also carries *simulated*
WHOIS / TLS feature values drawn from realistic distributions. The lexical
and whitelist features are always derived deterministically from the URL
string itself (by ``feature_engineering.py``), so they are never faked.
"""

from __future__ import annotations

import random
import string

# Suspicious TLDs frequently abused by phishing campaigns. Half the list is
# expanded with the cheap-TLD set the v1.3 schema scores via has_suspicious_tld
# so the model sees positive correlation with the flag during training.
_BAD_TLDS = [
    "com", "net", "org", "info", "xyz", "online", "site", "top",
    "club", "live", "vip", "cc", "icu", "buzz", "shop", "app",
    "cfd", "sbs", "bond", "monster", "fit", "work", "stream",
    "click", "fyi", "page", "you", "cv", "uno",
]

# 70% chance an attacker pulls from this curated short list -- biases the
# generator toward the tail SUSPICIOUS_TLDS so the model learns the signal.
_CHEAP_TLDS = [
    "xyz", "top", "icu", "cfd", "sbs", "bond", "cc", "click",
    "online", "site", "shop", "vip", "live", "work", "fit",
    "you", "cv",
]

# Paths an attacker uses to pressure a victim into entering credentials.
_PHISH_PATHS = [
    "login", "signin", "verify", "verify-account", "account/update",
    "secure/login", "auth/verify", "confirm", "update-info", "reset-password",
    "wp-login.php", "webscr", "validation", "session/expired", "e-service/login",
]

# Benign paths seen on real government / university sites. A meaningful
# minority of these contain "login" / "secure" / "account" so the model
# does not equate the v1.3 has_login_keyword flag with phishing on its
# own -- legitimate gov/edu portals frequently host /login pages.
_GOOD_PATHS = [
    "", "index.php", "news", "about", "contact", "services",
    "th/home", "en/home", "downloads", "announcement", "e-service",
    "intranet", "academic/calendar", "students", "research",
    "login", "auth/login", "secure/login", "myaccount",
    "verify-citizen-id", "service/login", "portal/signin",
    "auth/sso", "support/contact", "session/start",
    # weak-tier keyword paths (v1.8): generic portal words legit sites use
    # constantly -- lets num_strong_login_keywords separate the classes.
    "customer/service", "billing/history", "account/settings",
    "support/faq", "service/update",
]

_BRAND_WORDS = ["secure", "login", "verify", "account", "service", "online",
                "support", "update", "th", "gov"]

# Well-known LEGITIMATE domains that are NOT on the Thai gov/edu whitelist.
# Including these teaches the model that "not whitelisted" does not mean
# "phishing" -- otherwise it would flag every ordinary website.
_LEGIT_OTHER = [
    # global
    "google.com", "youtube.com", "facebook.com", "wikipedia.org",
    "github.com", "microsoft.com", "apple.com", "amazon.com",
    "netflix.com", "linkedin.com", "instagram.com", "reddit.com",
    "stackoverflow.com", "cloudflare.com", "mozilla.org", "office.com",
    "zoom.us", "dropbox.com", "wordpress.com", "adobe.com",
    "paypal.com", "bbc.com", "nytimes.com", "canva.com",
    # Thai commercial / news / services
    "thairath.co.th", "kapook.com", "sanook.com", "pantip.com",
    "mthai.com", "dailynews.co.th", "matichon.co.th", "posttoday.com",
    "thaipbs.or.th", "line.me", "ais.co.th", "truecorp.co.th",
    "dtac.co.th", "lazada.co.th", "shopee.co.th", "central.co.th",
    "bigc.co.th", "kasikornbank.com", "scb.co.th", "bangkokbank.com",
    "krungsri.com", "grab.com", "agoda.com", "traveloka.com",
    "ookbee.com", "wongnai.com", "jobthai.com", "blockdit.com",
    # Thai SME / commercial long tail (v1.8 hard-benign coverage)
    "makewebeasy.com", "tarad.com", "weloveshopping.com", "priceza.com",
    "thaiware.com", "siamzone.com", "dek-d.com", "exteen.com",
    "longdo.com", "tlcthai.com", "thaifranchisecenter.com", "chillpainai.com",
    "edtguide.com", "soccersuck.com", "flashfly.net", "beartai.com",
]

# Word pools for the v1.8 hard-benign legit archetypes. The combined SME
# labels are >= 8 chars so they never collide with a whitelisted brand
# within typosquat distance.
_SME_WORDS_A = [
    "coffee", "bangkok", "siam", "smile", "happy", "golden", "sabai",
    "thonglor", "sukhumvit", "chiangmai", "phuket", "garden", "river",
]
_SME_WORDS_B = [
    "bakery", "studio", "market", "travel", "fitness", "design", "clinic",
    "resort", "kitchen", "flowers", "organic", "wedding", "printing",
]
# Cheap-but-legit TLDs: real small businesses use these constantly. The
# phishing generator also uses them, so the model must separate the classes
# on signals other than the TLD alone.
_SME_TLDS = ["online", "site", "shop", "store", "xyz", "info", "biz", "club", "cc"]

# Benign SSO / login-portal hosts and paths: huge numbers of legitimate
# services run login.<brand> / accounts.<brand> with OAuth redirect params.
_SSO_SUBS = ["login.", "accounts.", "sso.", "auth.", "id.", "signin."]
_SSO_PATHS = [
    "oauth2/authorize?client_id={cid}&redirect_uri=https%3A%2F%2F{dom}%2Fcallback&scope=openid",
    "oauth2/v2/auth?client_id={cid}&response_type=code",
    "realms/main/protocol/openid-connect/auth?client_id={cid}",
    "login?next=https%3A%2F%2F{dom}%2Fdashboard",
    "signin?return=https%3A%2F%2F{dom}%2Faccount",
    "adfs/ls/?wa=wsignin1.0&wtrealm=https%3A%2F%2F{dom}",
    "cas/login?service=https%3A%2F%2F{dom}%2Fportal",
]

# Content paths that mention a trusted brand (news article, logo asset, tag
# page). Teaches the model that a brand token in the path is NOT conclusive.
_BRAND_PATH_TEMPLATES = [
    "news/{brand}-budget-2026",
    "news/{brand}-announcement",
    "images/{brand}-logo.png",
    "tag/{brand}",
    "blog/{brand}-cooperation-project",
    "gallery/{brand}/2026",
]

# utm / search query strings for the query-heavy benign archetype.
_QUERY_HEAVY = [
    "search?q={q}&utm_source=facebook&utm_medium=cpc&utm_campaign=summer&page=2",
    "products?category={q}&sort=price&order=asc&page=3&per_page=24",
    "result?q={q}&lang=th&region=bkk&utm_source=line&utm_medium=social",
    "list?type={q}&filter=new&min=100&max=5000&rating=4&instock=1",
]

_HOMOGLYPHS = {
    "o": "0", "l": "1", "i": "1", "e": "3", "a": "@", "s": "5",
}

# Latin -> Unicode confusable swaps for the IDN homoglyph archetype.
# These mirror the confusables FoldedMap in phish_features.homoglyph so the
# new feature actually fires on the generated examples.
_IDN_SWAPS: dict[str, str] = {
    "a": "а",  # Cyrillic а
    "e": "е",  # Cyrillic е
    "o": "о",  # Cyrillic о
    "p": "р",  # Cyrillic р
    "c": "с",  # Cyrillic с
    "x": "х",  # Cyrillic х
    "i": "і",  # Cyrillic і
    "h": "һ",
    "y": "у",
    "s": "ѕ",
}


class SyntheticGenerator:
    def __init__(self, whitelist_domains: list[str], seed: int = 42) -> None:
        self.domains = list(whitelist_domains)
        self.rng = random.Random(seed)

    # ----- helpers ------------------------------------------------------
    def _rand_str(self, n: int) -> str:
        return "".join(self.rng.choice(string.ascii_lowercase) for _ in range(n))

    def _pick_bad_tld(self) -> str:
        """Bias toward cheap/abused TLDs the v1.3 schema knows about."""
        if self.rng.random() < 0.70:
            return self.rng.choice(_CHEAP_TLDS)
        return self.rng.choice(_BAD_TLDS)

    def _domain_label(self, domain: str) -> str:
        """First label of a registrable domain (e.g. ``obec`` of obec.go.th)."""
        return domain.split(".")[0]

    def _swap_tld(self, domain: str) -> str:
        label = self._domain_label(domain)
        return f"{label}.{self._pick_bad_tld()}"

    # ----- mutations (typosquatting) -----------------------------------
    def _mutate_label(self, label: str) -> str:
        """Apply 1-2 character-level edits to a domain label."""
        edits = self.rng.randint(1, 2)
        chars = list(label)
        for _ in range(edits):
            if not chars:
                break
            op = self.rng.choice(["sub", "del", "ins", "dup", "swap", "homo"])
            i = self.rng.randrange(len(chars))
            if op == "sub":
                chars[i] = self.rng.choice(string.ascii_lowercase)
            elif op == "del" and len(chars) > 2:
                chars.pop(i)
            elif op == "ins":
                chars.insert(i, self.rng.choice(string.ascii_lowercase))
            elif op == "dup":
                chars.insert(i, chars[i])
            elif op == "swap" and i + 1 < len(chars):
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
            elif op == "homo" and chars[i] in _HOMOGLYPHS:
                chars[i] = _HOMOGLYPHS[chars[i]]
        mutated = "".join(chars)
        return mutated if mutated != label else mutated + self.rng.choice("xz")

    # ----- network feature simulation ----------------------------------
    def _sim_reputation(self, label: int) -> dict:
        """Simulated IP/ASN reputation (B8 Stage 2), matching serve-time semantics.

        At serve time the value is the accumulated bad-verdict share of the
        host's IP / ASN, or -1 when there is no history. Most hosts have NO
        history, so -1 dominates and must be class-neutral; only a minority of
        rows carry a real reputation, and there it correlates with the label
        (with deliberate overlap: clean sites on noisy shared ASNs, fresh
        phishing on not-yet-flagged ranges).
        """
        r = self.rng
        if r.random() < 0.70:  # no accumulated history -> unknown, class-neutral
            return {"ip_reputation_score": -1, "asn_reputation_score": -1}
        if label == 0:  # legitimate: low bad share
            ip = round(r.uniform(0.0, 0.20), 3)
            asn = round(r.uniform(0.0, 0.15), 3)
            if r.random() < 0.10:  # clean site on a so-so shared range
                asn = round(r.uniform(0.20, 0.50), 3)
            return {"ip_reputation_score": ip, "asn_reputation_score": asn}
        # phishing: high bad share
        ip = round(r.uniform(0.40, 1.00), 3)
        asn = round(r.uniform(0.30, 0.90), 3)
        if r.random() < 0.15:  # fresh host on a not-yet-flagged range
            ip = round(r.uniform(0.10, 0.40), 3)
        return {"ip_reputation_score": ip, "asn_reputation_score": asn}

    def sim_network(self, label: int, has_https: bool) -> dict:
        """Simulated WHOIS/TLS values with realistic class overlap.

        Crucially, WHOIS/TLS lookups FAIL on a fraction of *both* classes --
        at serve time the backend uses short timeouts, so failures are common
        regardless of legitimacy. The model must therefore not read a failed
        lookup ("domain_age_days = -1") as evidence of phishing.
        """
        r = self.rng
        rep = self._sim_reputation(label)
        # ~22% of the time BOTH lookups fail completely (short serve-time
        # timeouts). This state is class-neutral on purpose -- it must carry
        # no signal, so the model falls back on lexical + whitelist features.
        if r.random() < 0.22:
            return {
                "domain_age_days": -1,
                "is_known_registrar": 0,
                "has_valid_cert": 0,
                "cert_age_days": -1,
                "is_self_signed": 0,
                "whois_ok": 0,
                "tls_ok": 0,
                # both lookups failed -> TLS-derived features are "unknown"
                "cert_is_lets_encrypt": 0,
                "cert_validity_days": -1,
                "cert_san_count": -1,
                **rep,
            }
        if label == 0:  # legitimate
            whois_ok = 1 if r.random() < 0.80 else 0
            if whois_ok:
                # mostly aged, occasionally a younger legit site
                age = (r.randint(1200, 9000) if r.random() < 0.85
                       else r.randint(120, 1200))
            else:
                age = -1
            tls_ok = 1 if (has_https and r.random() < 0.90) else 0
            # Legit sites use a mix of CAs; ~35% are on free DV (Let's Encrypt)
            # but most carry longer validity (OV / 1-year DV) and a small,
            # purpose-built SAN list.
            le_legit = 1 if (tls_ok and r.random() < 0.35) else 0
            return {
                "domain_age_days": age,
                "is_known_registrar": 1 if (whois_ok and r.random() < 0.85) else 0,
                "has_valid_cert": 1 if tls_ok else 0,
                "cert_age_days": r.randint(20, 540) if tls_ok else -1,
                "is_self_signed": 0,
                "whois_ok": whois_ok,
                "tls_ok": tls_ok,
                "cert_is_lets_encrypt": le_legit,
                "cert_validity_days": (
                    (90 if le_legit else r.randint(180, 397)) if tls_ok else -1
                ),
                "cert_san_count": (r.randint(1, 4) if tls_ok else -1),
                **rep,
            }

        # phishing — distributions updated to match 2024 reality:
        # attackers increasingly use major registrars and Let's Encrypt certs.
        whois_ok = 1 if r.random() < 0.70 else 0
        if whois_ok:
            # 55% freshly registered, 45% on aged/compromised hosts (was 70/30)
            age = (r.randint(0, 300) if r.random() < 0.55
                   else r.randint(300, 7000))
        else:
            age = -1
        tls_ok = 1 if (has_https and r.random() < 0.80) else 0
        # 72% of TLS-ok phishing has a valid cert (Let's Encrypt is free; was 55%)
        valid_cert = 1 if (tls_ok and r.random() < 0.72) else 0
        # ~80% of valid-cert phishing is on a free DV CA (Let's Encrypt),
        # which issues short-lived 90-day certs -- the dominant phishing CA.
        le_phish = 1 if (valid_cert and r.random() < 0.80) else 0
        return {
            "domain_age_days": age,
            # 35% of WHOIS-ok phishing uses a known registrar (was 15%)
            "is_known_registrar": 1 if (whois_ok and r.random() < 0.35) else 0,
            "has_valid_cert": valid_cert,
            "cert_age_days": (r.randint(0, 120) if valid_cert
                              else (r.randint(0, 400) if tls_ok else -1)),
            "is_self_signed": 1 if (tls_ok and not valid_cert
                                    and r.random() < 0.5) else 0,
            "whois_ok": whois_ok,
            "tls_ok": tls_ok,
            "cert_is_lets_encrypt": le_phish,
            "cert_validity_days": (
                (90 if le_phish else r.randint(90, 397)) if valid_cert else -1
            ),
            # bulk phishing certs occasionally bundle many hostnames (SAN),
            # but most are single-host -- skew small with an occasional spike.
            "cert_san_count": (
                (r.randint(1, 2) if r.random() < 0.85 else r.randint(3, 30))
                if valid_cert else -1
            ),
            **rep,
        }

    # ----- legitimate ---------------------------------------------------
    def gen_legit(self) -> dict:
        """Generate one legitimate URL.

        v1.8: besides the dominant trusted-domain arm, a set of HARD-BENIGN
        archetypes covers legitimate sites that share surface features with
        phishing (cheap TLDs, login portals, brand mentions in content paths,
        hashed asset paths, utm-heavy queries). Without them the model only
        ever saw those signals on the phishing side and learnt each one as a
        near-deterministic phishing tell -- the main source of false
        positives on ordinary websites.
        """
        r = self.rng
        archetype = r.choices(
            ["trusted", "cheap_tld", "login_portal", "brand_in_path",
             "deep_asset", "query_heavy"],
            weights=[65, 10, 8, 6, 6, 5],
        )[0]
        scheme = "https" if r.random() < 0.96 else "http"

        if archetype == "cheap_tld":
            # SME on a cheap-but-legit TLD, typically aged WHOIS + free DV cert.
            sep = "-" if r.random() < 0.25 else ""
            host = (r.choice(_SME_WORDS_A) + sep + r.choice(_SME_WORDS_B)
                    + "." + r.choice(_SME_TLDS))
            if r.random() < 0.3:
                host = "www." + host
            # A minority carry member-area paths: real SMEs on cheap TLDs run
            # /login and /account pages too -- the TLD+keyword combination
            # alone must not condemn them.
            path = r.choice(["", "menu", "about-us", "contact", "booking",
                             "gallery", "promotion", "th/home",
                             "login", "account", "member/login"])
            url = f"{scheme}://{host}" + (f"/{path}" if path else "")
            row = {"url": url, "label": 0}
            row.update(self.sim_network(0, scheme == "https"))
            # Small legit sites over-index on Let's Encrypt vs the big brands.
            if row["tls_ok"] and not row["cert_is_lets_encrypt"] and r.random() < 0.45:
                row["cert_is_lets_encrypt"] = 1
                row["cert_validity_days"] = 90
            return row

        if archetype == "login_portal":
            # Real SSO/OAuth portal: login subdomain + redirect query params.
            domain = r.choice(_LEGIT_OTHER if r.random() < 0.6 else self.domains)
            sub = r.choice(_SSO_SUBS)
            path = r.choice(_SSO_PATHS).format(
                cid=self._rand_str(r.randint(8, 16)), dom=domain
            )
            url = f"https://{sub}{domain}/{path}"
            row = {"url": url, "label": 0}
            row.update(self.sim_network(0, True))
            return row

        if archetype == "brand_in_path":
            # News/content site mentioning a trusted brand in the path.
            domain = r.choice(_LEGIT_OTHER)
            brand = self._domain_label(r.choice(self.domains))
            path = r.choice(_BRAND_PATH_TEMPLATES).format(brand=brand)
            url = f"{scheme}://www.{domain}/{path}"
            row = {"url": url, "label": 0}
            row.update(self.sim_network(0, scheme == "https"))
            return row

        if archetype == "deep_asset":
            # CDN-style hashed asset path: long + high entropy but benign.
            domain = r.choice(_LEGIT_OTHER)
            sub = r.choice(["cdn.", "static.", "assets.", "img."])
            h1 = "".join(r.choice("0123456789abcdef") for _ in range(16))
            h2 = "".join(r.choice("0123456789abcdef") for _ in range(8))
            ext = r.choice(["js", "css", "png", "woff2"])
            url = f"https://{sub}{domain}/static/{h1}/{h2}.{ext}"
            row = {"url": url, "label": 0}
            row.update(self.sim_network(0, True))
            return row

        if archetype == "query_heavy":
            # Search/listing page with many utm/filter params.
            domain = r.choice(_LEGIT_OTHER)
            q = r.choice(["shoes", "notebook", "hotel", "mobile", "ticket"])
            path = r.choice(_QUERY_HEAVY).format(q=q)
            url = f"https://www.{domain}/{path}"
            row = {"url": url, "label": 0}
            row.update(self.sim_network(0, True))
            return row

        # trusted arm: ~60% Thai gov/edu, ~40% other well-known sites.
        if r.random() < 0.6:
            domain = r.choice(self.domains)
        else:
            domain = r.choice(_LEGIT_OTHER)
        sub = r.choice(["", "", "", "www.", "www.", "service.",
                        "e.", "reg.", "intranet."])
        # ~12% two-level subdomains: big providers run console.cloud.* /
        # signin.aws.* style hosts. Without these, num_subdomains >= 2 only
        # ever appeared on the phishing side (subdomain_spoof archetype) and
        # the model read subdomain depth alone as a phishing tell.
        if r.random() < 0.12:
            sub = r.choice(["console.cloud.", "portal.service.", "app.intranet.",
                            "mail.student.", "api.data.", "signin.id.",
                            "sso.account.", "admin.e."])
        path = r.choice(_GOOD_PATHS)
        url = f"{scheme}://{sub}{domain}"
        if path:
            url += f"/{path}"
        row = {"url": url, "label": 0}
        row.update(self.sim_network(0, scheme == "https"))
        return row

    def gen_phish(self) -> dict:
        domain = self.rng.choice(self.domains)
        label = self._domain_label(domain)
        archetype = self.rng.choices(
            ["typosquat", "tld_swap", "subdomain_spoof", "ip_host",
             "at_trick", "brand_stuffed", "https_ip_host", "redirect_chain",
             "idn_homoglyph", "punycode_spoof", "path_brand_spoof",
             "long_random_subdomain", "double_dash_stuffed", "token_stuffed_path",
             "brand_expansion"],
            # v1.4: 3 new archetypes teach the model num_login_keywords,
            # host_token_count, and path_entropy signals.
            # v1.8: brand_expansion teaches host_brand_token_hit -- the brand
            # embedded in a longer label (kmitl-th.com, chulalongkorn-style
            # name expansions) that edit distance cannot catch.
            weights=[18, 9, 9, 8, 8, 9, 4, 5, 4, 4, 10, 6, 5, 9, 7],
        )[0]
        scheme = "https" if self.rng.random() < 0.55 else "http"
        path = self.rng.choice(_PHISH_PATHS)

        if archetype == "typosquat":
            host = self._mutate_label(label) + "." + self._pick_bad_tld()
        elif archetype == "tld_swap":
            # exact brand label, wrong TLD: obec.go.th -> obec.com
            host = f"{label}.{self._pick_bad_tld()}"
        elif archetype == "subdomain_spoof":
            attacker = self._rand_str(self.rng.randint(5, 10))
            host = f"{domain}.{attacker}.{self._pick_bad_tld()}"
        elif archetype == "ip_host":
            host = ".".join(str(self.rng.randint(1, 254)) for _ in range(4))
            scheme = "http"
        elif archetype == "https_ip_host":
            # Attacker uses a VPS with HTTPS; model must not rely on HTTP alone
            host = ".".join(str(self.rng.randint(1, 254)) for _ in range(4))
            scheme = "https"
        elif archetype == "at_trick":
            attacker = self._rand_str(self.rng.randint(5, 9))
            host = f"{domain}@{attacker}.{self._pick_bad_tld()}"
        elif archetype == "redirect_chain":
            # attacker.xyz/redirect?to=legitimate.go.th — redirect with query param
            attacker = self._rand_str(self.rng.randint(5, 10))
            # Redirect bait also lives on plain .com hosts behind tracker-style
            # subdomains (track.evil.com) -- the TLD must not carry the signal.
            tld = "com" if self.rng.random() < 0.30 else self._pick_bad_tld()
            host = f"{attacker}.{tld}"
            if self.rng.random() < 0.50:
                host = self.rng.choice(
                    ["track.", "link.", "go.", "click.", "out.", "api."]
                ) + host
        elif archetype == "idn_homoglyph":
            # Swap one Latin letter in the brand label for a Cyrillic look-alike.
            # The resulting host displays identically to the legitimate brand
            # but does not match it in raw-ASCII edit distance.
            candidates = [i for i, ch in enumerate(label) if ch in _IDN_SWAPS]
            if candidates:
                idx = self.rng.choice(candidates)
                spoofed = list(label)
                spoofed[idx] = _IDN_SWAPS[label[idx]]
                host = "".join(spoofed) + "." + self._pick_bad_tld()
            else:
                # Fall back to a plain typosquat for labels with no swap-able chars.
                host = self._mutate_label(label) + "." + self._pick_bad_tld()
        elif archetype == "punycode_spoof":
            # Encode an IDN homoglyph version of the label as Punycode so the
            # raw host begins with xn--. Falls back gracefully if encoding fails.
            candidates = [i for i, ch in enumerate(label) if ch in _IDN_SWAPS]
            unicode_label = label
            if candidates:
                idx = self.rng.choice(candidates)
                tmp = list(label)
                tmp[idx] = _IDN_SWAPS[label[idx]]
                unicode_label = "".join(tmp)
            try:
                encoded = unicode_label.encode("idna").decode("ascii")
            except Exception:  # noqa: BLE001
                encoded = "xn--" + label + "-zzz"
            host = encoded + "." + self._pick_bad_tld()
        elif archetype == "path_brand_spoof":
            # Random benign-looking host on a cheap TLD; the brand we want
            # to impersonate lives in the URL path so the user sees it in
            # the address bar. This is the dominant 2024-2025 OpenPhish kit.
            attacker = self._rand_str(self.rng.randint(6, 11))
            host = f"{attacker}.{self.rng.choice(_CHEAP_TLDS)}"
        elif archetype == "long_random_subdomain":
            # Bot-generated hex subdomain in front of the brand label:
            # a1b2c3d4.brand.xyz  — exercises host_token_count + max_digit_run
            rand_sub = "".join(
                self.rng.choice("0123456789abcdef")
                for _ in range(self.rng.randint(6, 12))
            )
            host = f"{rand_sub}.{label}.{self.rng.choice(_CHEAP_TLDS)}"
        elif archetype == "double_dash_stuffed":
            # brand--secure--verify--login.xyz pattern common in 2025 Thai phishing
            # exercises host_token_count and num_hyphens
            kws = self.rng.sample(_BRAND_WORDS, k=self.rng.randint(2, 4))
            host = "--".join([label] + kws) + "." + self._pick_bad_tld()
        elif archetype == "brand_expansion":
            # Brand embedded in a longer host label: kmitl-th.com,
            # thaipolice-verify.shop, chulalongkorn-style name expansions.
            # Plain .com is common here -- the host label IS the lure.
            suffix = self.rng.choice(
                ["th", "thai", "thailand", "online", "official",
                 "center", "portal", "verify", "promo", "uni-th"]
            )
            sep = self.rng.choice(["-", "-", ""])
            tld = ("com" if self.rng.random() < 0.40 else self._pick_bad_tld())
            host = f"{label}{sep}{suffix}.{tld}"
            if self.rng.random() < 0.30:
                # prefix form: thai-customs.cc, energy-thai.cc
                pre = self.rng.choice(["thai", "th", "gov"])
                host = f"{pre}-{label}.{tld}"
            path = self.rng.choice(
                ["secure", "account", "admission", "subsidy", "redeem",
                 "register", "portal", "student-login", "e-service"]
            )
        else:  # brand_stuffed
            words = self.rng.sample(_BRAND_WORDS, k=self.rng.randint(2, 4))
            host = "-".join([label] + words) + "." + self._pick_bad_tld()

        if archetype == "redirect_chain":
            # Most real redirect bait carries a full URL in the param (so the
            # path_redirect_hit feature fires, same as at serve time); keep a
            # minority bare-domain form for variety.
            param = self.rng.choice(["to", "url", "next", "goto", "redirect"])
            endpoint = self.rng.choice(["redirect", "click", "go", "track", "out"])
            if self.rng.random() < 0.75:
                target_path = self.rng.choice(["", "/login", "/account", "/verify"])
                url = (f"{scheme}://{host}/{endpoint}"
                       f"?{param}=https://{domain}{target_path}")
            else:
                url = f"{scheme}://{host}/{endpoint}?{param}={domain}"
        elif archetype == "path_brand_spoof":
            extra = self.rng.choice(_PHISH_PATHS)
            url = f"{scheme}://{host}/{label}/{extra}"
        elif archetype == "long_random_subdomain":
            url = f"{scheme}://{host}/{path}"
            if self.rng.random() < 0.5:
                url += f"?id={self._rand_str(self.rng.randint(8, 20))}"
        elif archetype == "double_dash_stuffed":
            url = f"{scheme}://{host}/{path}"
        elif archetype == "token_stuffed_path":
            # Benign-ish host; long credential-keyword-stuffed path
            # exercises path_entropy + num_login_keywords + path_length
            attacker = self._rand_str(self.rng.randint(5, 10))
            host = f"{attacker}.{self.rng.choice(_CHEAP_TLDS)}"
            segments = self.rng.sample(_PHISH_PATHS, k=self.rng.randint(3, 5))
            hex_token = "".join(
                self.rng.choice("0123456789abcdef") for _ in range(16)
            )
            url = f"{scheme}://{host}/{label}/" + "/".join(segments) + f"/{hex_token}"
        else:
            url = f"{scheme}://{host}/{path}"
            if self.rng.random() < 0.4:  # extra junk query string
                url += f"?id={self._rand_str(self.rng.randint(8, 20))}"

        row = {"url": url, "label": 1}
        net = self.sim_network(1, scheme == "https")
        # HTTPS IP-host: ensure TLS is attempted with a self-signed cert
        if archetype == "https_ip_host" and not net["tls_ok"]:
            net.update({
                "tls_ok": 1,
                "has_valid_cert": 0,
                "is_self_signed": 1,
                "cert_age_days": self.rng.randint(0, 90),
            })
        row.update(net)
        return row

    # ----- driver -------------------------------------------------------
    def generate(self, n_legit: int, n_phish: int) -> list[dict]:
        rows: list[dict] = []
        seen: set[str] = set()
        guard = 0
        while sum(r["label"] == 0 for r in rows) < n_legit and guard < n_legit * 40:
            r = self.gen_legit()
            guard += 1
            if r["url"] not in seen:
                seen.add(r["url"])
                rows.append(r)
        guard = 0
        while sum(r["label"] == 1 for r in rows) < n_phish and guard < n_phish * 40:
            r = self.gen_phish()
            guard += 1
            if r["url"] not in seen:
                seen.add(r["url"])
                rows.append(r)
        self.rng.shuffle(rows)
        return rows
