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
]

_HOMOGLYPHS = {
    "o": "0", "l": "1", "i": "1", "e": "3", "a": "@", "s": "5",
}

# --- v1.9 archetype building blocks ---------------------------------------
# Second-level labels + foreign ccTLDs used by the cctld_clone archetype:
# brand.com.kz / brand.co.pl — the registrable domain becomes ``com.kz``
# (brand label "com", too short for any typosquat gate), so the brand is
# visually intact while the host is a cheap foreign registration. This is the
# shape that scored 0.0 on the independent holdout (roblox.com.kz class).
_CCTLD_CLONE_SLDS = ["com", "co", "net"]
_CCTLD_CLONE_TLDS = [
    "kz", "pl", "ru", "br", "in", "id", "ng", "at", "ve", "ua", "land",
]

# User-content / serverless platforms that delegate subdomains to arbitrary
# users. Phishing kits abuse these because the platform's reputation rubs off
# on the attacker's subdomain. They are DELIBERATELY excluded from
# KNOWN_GOOD_DOMAINS in rules.py, so the model must learn to read the path /
# lure tokens, not the platform suffix. Benign examples on the SAME platforms
# are generated in gen_legit so the suffix itself never becomes a phishing tell.
_USER_CONTENT_HOSTS = [
    "pages.dev", "github.io", "web.app", "workers.dev",
    "sealos.app", "netlify.app", "weebly.com",
]
_USER_CONTENT_LURES = [
    "customer", "center", "appeal", "secure", "account",
    "wallet", "support", "verify", "billing", "service",
]
_USER_CONTENT_PHISH_PATHS = [
    "vc/xv/login.php", "appeals/submit-appeal-form", "login",
    "account/verify", "secure/session/login.php", "appeals/submit-appeal-form/return",
]
# Benign paths on the same user-content platforms — portfolios, docs, blogs.
_USER_CONTENT_GOOD_PATHS = [
    "", "portfolio", "docs/intro", "blog/post-1", "about",
    "projects", "index.html", "resume",
]
_B64_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
)

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
        roll = self.rng.random()
        # ~5% benign user-content hosts (portfolios/docs/blogs on the SAME
        # platforms the user_content_host phishing archetype abuses). This
        # keeps the platform suffix class-neutral: only the path/lure tokens
        # separate benign from phishing, never ``pages.dev`` itself.
        if roll < 0.05:
            return self._gen_legit_user_content()
        # ~57% trusted Thai gov/edu, ~38% other well-known legitimate sites.
        if roll < 0.62:
            domain = self.rng.choice(self.domains)
        else:
            domain = self.rng.choice(_LEGIT_OTHER)
        sub = self.rng.choice(["", "", "", "www.", "www.", "service.",
                               "e.", "reg.", "intranet."])
        path = self.rng.choice(_GOOD_PATHS)
        scheme = "https" if self.rng.random() < 0.96 else "http"
        url = f"{scheme}://{sub}{domain}"
        if path:
            url += f"/{path}"
        row = {"url": url, "label": 0}
        row.update(self.sim_network(0, scheme == "https"))
        return row

    def _gen_legit_user_content(self) -> dict:
        """A legitimate site hosted on a user-content platform (benign path)."""
        platform = self.rng.choice(_USER_CONTENT_HOSTS)
        name = self.rng.choice([
            self._rand_str(self.rng.randint(5, 9)),
            f"{self._rand_str(self.rng.randint(4, 7))}-dev",
            f"{self.rng.choice(['my', 'the', 'team', 'open'])}-{self._rand_str(5)}",
        ])
        path = self.rng.choice(_USER_CONTENT_GOOD_PATHS)
        # User-content platforms serve over HTTPS almost universally.
        scheme = "https" if self.rng.random() < 0.98 else "http"
        url = f"{scheme}://{name}.{platform}"
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
             # v1.9: brand-clone on a foreign ccTLD, phishing on user-content
             # hosts, and base64-blob query strings — the three patterns the
             # independent holdout (zero train host overlap) was blind to.
             "cctld_clone", "user_content_host", "query_blob"],
            # v1.4: 3 new archetypes teach the model num_login_keywords,
            # host_token_count, and path_entropy signals.
            weights=[19, 9, 9, 8, 8, 9, 4, 5, 4, 4, 10, 6, 5, 10, 6, 6, 4],
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
            host = f"{attacker}.{self._pick_bad_tld()}"
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
        elif archetype == "cctld_clone":
            # brand.com.kz — half the brands come from the whitelist, half from
            # the well-known-but-not-whitelisted set (roblox-class). The selling
            # point is the SHAPE (brand.<sld>.<foreign-cc>), not the brand: the
            # registrable domain collapses to ``com.kz`` (label "com"), which is
            # too short for every typosquat gate.
            if self.rng.random() < 0.5:
                brand = label
            else:
                brand = self.rng.choice(_LEGIT_OTHER).split(".")[0]
            sld = self.rng.choice(_CCTLD_CLONE_SLDS)
            cc = self.rng.choice(_CCTLD_CLONE_TLDS)
            host = f"{brand}.{sld}.{cc}"
        elif archetype == "user_content_host":
            platform = self.rng.choice(_USER_CONTENT_HOSTS)
            lure = self.rng.choice(_USER_CONTENT_LURES)
            host_label = self.rng.choice([
                f"customer-sp-{self._rand_str(4)}",
                f"center-{lure}-adminpage",
                f"{lure}-{self._rand_str(5)}",
                f"{lure}-verify-{self._rand_str(3)}",
            ])
            host = f"{host_label}.{platform}"
            # These platforms serve over HTTPS almost universally.
            scheme = "https" if self.rng.random() < 0.9 else "http"
        elif archetype == "query_blob":
            attacker = self._rand_str(self.rng.randint(6, 11))
            host = f"{attacker}.{self.rng.choice(_CHEAP_TLDS)}"
        else:  # brand_stuffed
            words = self.rng.sample(_BRAND_WORDS, k=self.rng.randint(2, 4))
            host = "-".join([label] + words) + "." + self._pick_bad_tld()

        if archetype == "redirect_chain":
            url = f"{scheme}://{host}/redirect?to={domain}"
        elif archetype == "path_brand_spoof":
            extra = self.rng.choice(_PHISH_PATHS)
            url = f"{scheme}://{host}/{label}/{extra}"
        elif archetype == "long_random_subdomain":
            url = f"{scheme}://{host}/{path}"
            if self.rng.random() < 0.5:
                url += f"?id={self._rand_str(self.rng.randint(8, 20))}"
        elif archetype == "double_dash_stuffed":
            url = f"{scheme}://{host}/{path}"
        elif archetype == "cctld_clone":
            extra = self.rng.choice([
                "login", "account",
                f"users/{self.rng.randint(1000, 99999)}/profile",
            ])
            url = f"{scheme}://{host}/{extra}"
        elif archetype == "user_content_host":
            p = self.rng.choice(_USER_CONTENT_PHISH_PATHS)
            url = f"{scheme}://{host}/{p}"
        elif archetype == "query_blob":
            blob_len = self.rng.randint(80, 200)
            blob = "".join(self.rng.choice(_B64_ALPHABET) for _ in range(blob_len))
            key = self.rng.choice(["data", "token", "q", "s", "redirect"])
            deep = self.rng.choice([
                "auth/v2/session/login.php", "secure/login.php",
                "account/verify/login.php",
            ])
            url = f"{scheme}://{host}/{deep}?{key}={blob}"
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
