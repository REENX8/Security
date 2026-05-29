"""Feature contract shared by the ML pipeline and the backend.

This module is the SINGLE SOURCE OF TRUTH for:
  * the ordered list of model features (column order is part of the contract)
  * deterministic categorical encodings
  * imputed default values used when a network feature cannot be obtained

Changing anything here is a breaking change: bump ``FEATURE_SCHEMA_VERSION``
and retrain the model. The backend refuses to serve a model whose
``features.json`` does not match this schema.
"""

from __future__ import annotations

# Bump on ANY change to ORDERED_FEATURES / encodings / defaults.
#
# History:
#   v1.0.0 -- initial 20-feature set (lexical + WHOIS + TLS + whitelist).
#   v1.1.0 -- 5 path / port / digit-run lexical features.
#   v1.2.0 -- IDN + homoglyph + Punycode features (Cyrillic look-alikes).
#   v1.3.0 -- path-impersonation features. Close the gap on phishing kits
#             that reuse benign-looking hosts but stuff brand / credential
#             keywords into the URL path (~40% of OpenPhish misses had this
#             pattern), and on URLs sitting on the long tail of cheap
#             abused TLDs the ML had learnt only through indirect signals.
#   v1.4.0 -- 4 new lexical features: num_login_keywords (count, not binary),
#             query_param_count, path_entropy, host_token_count. These give
#             the model richer signal on credential-stuffed paths and
#             brand-stuffed hostnames without adding any network lookups.
#   v1.5.0 -- 5 new features that add signal WITHOUT new network lookups:
#             three are parsed from the SAME TLS handshake the model already
#             performs (cert_is_lets_encrypt, cert_validity_days,
#             cert_san_count) -- free DV certs with short 90-day validity
#             over-index heavily on phishing; two are deterministic
#             (digit_to_letter_ratio, host_has_brand_and_suspicious_tld --
#             a brand impersonated on a cheap/abused TLD).
FEATURE_SCHEMA_VERSION = "1.5.0"

# The exact, ordered list of numeric features fed to the model.
# Index position IS the contract -- never reorder, only append + bump version.
ORDERED_FEATURES: list[str] = [
    # --- lexical (deterministic, no network) ---
    "url_length",
    "num_dots",
    "num_hyphens",
    "num_at",
    "num_slash",
    "num_digits",
    "has_ip",
    "entropy",
    "has_https",
    "num_subdomains",
    # --- domain / whois ---
    "domain_age_days",
    "is_thai_tld",
    "tld_type_enc",
    "is_known_registrar",
    # --- whitelist / typosquat ---
    "min_edit_distance",
    "is_typosquat",
    # --- tls ---
    "has_valid_cert",
    "cert_age_days",
    "is_self_signed",
    # --- meta: did the optional network lookups succeed? ---
    "whois_ok",
    "tls_ok",
    # --- new lexical features (v1.1) ---
    "path_depth",           # segments in URL path (not counting empty)
    "domain_label_max_len", # longest label in the hostname
    "has_port",             # 1 if non-standard port (not 80/443) present
    "max_digit_run",        # length of longest consecutive-digit run in host
    "has_query_string",     # 1 if '?' present in URL
    # --- IDN / homoglyph features (v1.2) ---
    # All three target attacks that disguise a brand using non-ASCII look-alikes:
    "has_punycode",         # 1 if any host label starts with xn-- (IDN encoded)
    "has_mixed_script",     # 1 if a label mixes Unicode scripts (e.g. Latin+Cyrillic)
    "homoglyph_distance",   # min_edit_distance AFTER confusable fold;
                            # collapses below min_edit_distance for spoofs.
    # --- v1.3 path-impersonation features ---
    "has_login_keyword",    # 1 if URL path/query contains a credential-collection keyword
    "has_suspicious_tld",   # 1 if eTLD is in a curated cheap/abused list
    "path_brand_hit",       # 1 if a trusted brand label appears in the URL path
                            #   while the host's brand label does not
                            #   (e.g. ``random.cc/bot.go.th/login``)
    "path_length",          # total characters in URL path (>120 is rare on legit sites)
    # --- v1.4 richer lexical features ---
    "num_login_keywords",   # count of LOGIN_KEYWORDS tokens in path+query (int ≥ 0)
    "query_param_count",    # number of query parameters (& separators + 1 if ? present)
    "path_entropy",         # Shannon entropy of the URL path string
    "host_token_count",     # alphanumeric tokens in hostname (split on - and .)
    # --- v1.5 features (no new network lookups) ---
    "digit_to_letter_ratio",          # host digits / host letters (algorithmic hosts skew high)
    "cert_is_lets_encrypt",           # 1 if leaf cert issuer is a free DV CA (Let's Encrypt et al.)
    "cert_validity_days",             # notAfter - notBefore in days (90 = LE; legit DV/OV longer)
    "cert_san_count",                 # number of subjectAltName entries on the leaf cert
    "host_has_brand_and_suspicious_tld",  # trusted brand impersonated on a cheap/abused TLD
]

N_FEATURES = len(ORDERED_FEATURES)

# Deterministic categorical encoding for the TLD type. The raw string is kept
# for the API response / DB; the model consumes ``tld_type_enc``.
TLD_TYPE_MAP: dict[str, int] = {
    "go.th": 0,
    "ac.th": 1,
    "or.th": 2,
    "co.th": 3,
    "other": 4,
}
TLD_TYPE_DEFAULT = TLD_TYPE_MAP["other"]

# Values used when an optional network feature is unavailable. These are the
# SAME constants used for training rows where the lookup failed, so the model
# learns one consistent representation of "unknown".
IMPUTED_DEFAULTS: dict[str, float] = {
    "domain_age_days": -1,
    "is_known_registrar": 0,
    "has_valid_cert": 0,
    "cert_age_days": -1,
    "is_self_signed": 0,
    "whois_ok": 0,
    "tls_ok": 0,
    # v1.5 TLS-derived: -1/0 = "unknown", same convention as cert_age_days.
    "cert_is_lets_encrypt": 0,
    "cert_validity_days": -1,
    "cert_san_count": -1,
}

# Known Thai domain registrars (lower-cased substrings matched against the
# WHOIS registrar field).
KNOWN_THAI_REGISTRARS: tuple[str, ...] = (
    "thnic",
    "t.h.nic",
    "thai network information center",
    "dotarai",
    "netway",
    "z.com",
    "casbay",
    "name.com",
    "godaddy",
    "cloudflare",
)

# --- v1.3 lookup tables --------------------------------------------------
# Credential-collection / pressure keywords that show up in the URL path or
# query string of the overwhelming majority of phishing kits. Order doesn't
# matter; the lookup is a frozenset for O(1) checks.
LOGIN_KEYWORDS: frozenset[str] = frozenset({
    "login", "signin", "sign-in", "log-in", "logon",
    "verify", "verification", "validate", "validation",
    "account", "accounts", "myaccount",
    "secure", "security", "session", "auth", "authenticate",
    "update", "updated", "confirm", "confirmation",
    "password", "passwd", "credential", "credentials",
    "wallet", "recover", "recovery", "reset", "unlock",
    "support", "billing", "invoice", "refund",
    "webscr", "ebay", "service", "client", "customer",
    "twofactor", "otp", "kyc",
})

# Cheap / commonly abused TLDs. OpenPhish + URLhaus 2024-2025 over-index
# heavily on these compared to .com base rates. A 1/0 flag is enough --
# the model decides the weight.
SUSPICIOUS_TLDS: frozenset[str] = frozenset({
    "xyz", "top", "icu", "buzz", "click", "click", "loan",
    "online", "site", "store", "shop", "vip", "live", "work",
    "fit", "lol", "rest", "cfd", "sbs", "bond", "monster",
    "cc", "tk", "ml", "ga", "cf", "gq",
    "club", "support", "win", "biz", "info",
    "you", "cv", "uno", "country", "stream", "review", "party",
    "racing", "download", "fyi", "page", "host", "space",
})


def vector_from_dict(feat: dict) -> list[float]:
    """Project a raw feature dict onto the ordered numeric model vector."""
    return [float(feat[name]) for name in ORDERED_FEATURES]
