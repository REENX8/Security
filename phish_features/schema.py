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
FEATURE_SCHEMA_VERSION = "1.1.0"

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


def vector_from_dict(feat: dict) -> list[float]:
    """Project a raw feature dict onto the ordered numeric model vector."""
    return [float(feat[name]) for name in ORDERED_FEATURES]
