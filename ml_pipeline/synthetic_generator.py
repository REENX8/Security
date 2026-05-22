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

# Suspicious TLDs frequently abused by phishing campaigns.
_BAD_TLDS = [
    "com", "net", "org", "info", "xyz", "online", "site", "top",
    "club", "live", "vip", "cc", "icu", "buzz", "shop", "app",
]

# Paths an attacker uses to pressure a victim into entering credentials.
_PHISH_PATHS = [
    "login", "signin", "verify", "verify-account", "account/update",
    "secure/login", "auth/verify", "confirm", "update-info", "reset-password",
    "wp-login.php", "webscr", "validation", "session/expired", "e-service/login",
]

# Benign paths seen on real government / university sites.
_GOOD_PATHS = [
    "", "index.php", "news", "about", "contact", "services",
    "th/home", "en/home", "downloads", "announcement", "e-service",
    "intranet", "academic/calendar", "students", "research",
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


class SyntheticGenerator:
    def __init__(self, whitelist_domains: list[str], seed: int = 42) -> None:
        self.domains = list(whitelist_domains)
        self.rng = random.Random(seed)

    # ----- helpers ------------------------------------------------------
    def _rand_str(self, n: int) -> str:
        return "".join(self.rng.choice(string.ascii_lowercase) for _ in range(n))

    def _domain_label(self, domain: str) -> str:
        """First label of a registrable domain (e.g. ``obec`` of obec.go.th)."""
        return domain.split(".")[0]

    def _swap_tld(self, domain: str) -> str:
        label = self._domain_label(domain)
        return f"{label}.{self.rng.choice(_BAD_TLDS)}"

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
    def sim_network(self, label: int, has_https: bool) -> dict:
        """Simulated WHOIS/TLS values with realistic class overlap.

        Crucially, WHOIS/TLS lookups FAIL on a fraction of *both* classes --
        at serve time the backend uses short timeouts, so failures are common
        regardless of legitimacy. The model must therefore not read a failed
        lookup ("domain_age_days = -1") as evidence of phishing.
        """
        r = self.rng
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
            return {
                "domain_age_days": age,
                "is_known_registrar": 1 if (whois_ok and r.random() < 0.85) else 0,
                "has_valid_cert": 1 if tls_ok else 0,
                "cert_age_days": r.randint(20, 540) if tls_ok else -1,
                "is_self_signed": 0,
                "whois_ok": whois_ok,
                "tls_ok": tls_ok,
            }

        # phishing
        whois_ok = 1 if r.random() < 0.70 else 0
        if whois_ok:
            # mostly freshly registered, but ~30% on aged/compromised hosts
            age = (r.randint(0, 300) if r.random() < 0.70
                   else r.randint(300, 7000))
        else:
            age = -1
        tls_ok = 1 if (has_https and r.random() < 0.80) else 0
        valid_cert = 1 if (tls_ok and r.random() < 0.55) else 0
        return {
            "domain_age_days": age,
            "is_known_registrar": 1 if (whois_ok and r.random() < 0.15) else 0,
            "has_valid_cert": valid_cert,
            "cert_age_days": (r.randint(0, 120) if valid_cert
                              else (r.randint(0, 400) if tls_ok else -1)),
            "is_self_signed": 1 if (tls_ok and not valid_cert
                                    and r.random() < 0.5) else 0,
            "whois_ok": whois_ok,
            "tls_ok": tls_ok,
        }

    # ----- legitimate ---------------------------------------------------
    def gen_legit(self) -> dict:
        # ~60% trusted Thai gov/edu, ~40% other well-known legitimate sites.
        if self.rng.random() < 0.6:
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

    def gen_phish(self) -> dict:
        domain = self.rng.choice(self.domains)
        label = self._domain_label(domain)
        archetype = self.rng.choice(
            ["typosquat", "typosquat", "tld_swap", "subdomain_spoof",
             "ip_host", "at_trick", "brand_stuffed"]
        )
        scheme = "https" if self.rng.random() < 0.55 else "http"
        path = self.rng.choice(_PHISH_PATHS)

        if archetype == "typosquat":
            host = self._mutate_label(label) + "." + self.rng.choice(_BAD_TLDS)
        elif archetype == "tld_swap":
            # exact brand label, wrong TLD: obec.go.th -> obec.com
            host = f"{label}.{self.rng.choice(_BAD_TLDS)}"
        elif archetype == "subdomain_spoof":
            attacker = self._rand_str(self.rng.randint(5, 10))
            host = f"{domain}.{attacker}.{self.rng.choice(_BAD_TLDS)}"
        elif archetype == "ip_host":
            host = ".".join(str(self.rng.randint(1, 254)) for _ in range(4))
            scheme = "http"
        elif archetype == "at_trick":
            attacker = self._rand_str(self.rng.randint(5, 9))
            host = f"{domain}@{attacker}.{self.rng.choice(_BAD_TLDS)}"
        else:  # brand_stuffed
            words = self.rng.sample(_BRAND_WORDS, k=self.rng.randint(2, 4))
            host = "-".join([label] + words) + "." + self.rng.choice(_BAD_TLDS)

        url = f"{scheme}://{host}/{path}"
        if self.rng.random() < 0.4:  # extra junk query string
            url += f"?id={self._rand_str(self.rng.randint(8, 20))}"

        row = {"url": url, "label": 1}
        row.update(self.sim_network(1, scheme == "https"))
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
