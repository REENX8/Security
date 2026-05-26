"""The single feature-extraction orchestrator.

Both the ML pipeline and the FastAPI backend import ``FeatureExtractor`` from
here. There is no second implementation, so train/serve skew is structurally
impossible for the lexical + whitelist features. Network features (WHOIS, TLS)
are optional and degrade to imputed defaults.
"""

from __future__ import annotations

from urllib.parse import urlparse

import re

from .domain import whois_features
from .homoglyph import has_mixed_script, has_punycode
from .lexical import extract_lexical, normalize_url
from .schema import (
    IMPUTED_DEFAULTS,
    LOGIN_KEYWORDS,
    ORDERED_FEATURES,
    SUSPICIOUS_TLDS,
    TLD_TYPE_DEFAULT,
    TLD_TYPE_MAP,
)
from .tls import tls_features
from .whitelist import Whitelist, brand_label

# Tokenise URL path on any character that's not alphanumeric. This is what
# decides whether ``login`` lives inside path segment ``/secure-login.php``.
_PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _etld(host: str) -> str:
    """Best-effort effective top-level domain (eTLD).

    For multi-label suffixes we already know about (go.th etc.), return the
    longer compound. Otherwise return the last label. We deliberately keep
    this list short -- the goal is to feed the SUSPICIOUS_TLDS lookup, not
    to compute a full Public Suffix List eTLD.
    """
    if not host:
        return ""
    h = host.lower()
    for suffix in ("go.th", "ac.th", "or.th", "co.th", "in.th", "mi.th",
                   "net.th", "com.au", "co.uk", "org.uk", "ac.uk"):
        if h == suffix or h.endswith("." + suffix):
            return suffix
    return h.rsplit(".", 1)[-1] if "." in h else h


def _path_brand_hit(url: str, host_brand: str, whitelist: Whitelist) -> int:
    """1 if a whitelisted brand label appears in the URL path *and* the host's
    brand label does NOT match it.

    Phishing kits commonly use a random/benign host and stuff the brand into
    the path: ``secure-update.cc/krungthai/login``. Legitimate sites almost
    never do this (their brand is in the host, not the path).
    """
    try:
        from urllib.parse import urlparse
        path = urlparse(normalize_url(url)).path or ""
    except Exception:  # noqa: BLE001
        return 0
    if not path or path == "/":
        return 0
    tokens = {t.lower() for t in _PATH_TOKEN_RE.findall(path) if len(t) >= 4}
    if not tokens:
        return 0
    host_brand = (host_brand or "").lower()
    for label in whitelist._labels:  # uses precomputed brand labels
        if len(label) < 4:
            continue
        if label in tokens and label != host_brand:
            return 1
    return 0


def classify_tld(host: str) -> tuple[str, int]:
    """Return ``(tld_type, is_thai_tld)`` for a host.

    ``tld_type`` is one of go.th / ac.th / or.th / co.th / other.
    """
    h = (host or "").lower()
    is_thai = int(h.endswith(".th"))
    for kind in ("go.th", "ac.th", "or.th", "co.th"):
        if h == kind or h.endswith("." + kind):
            return kind, is_thai
    return "other", is_thai


class FeatureExtractor:
    """Extract the full feature contract from a URL string."""

    def __init__(
        self,
        whitelist: Whitelist,
        enable_whois: bool = True,
        enable_tls: bool = True,
        network_timeout: float = 2.5,
    ) -> None:
        self.whitelist = whitelist
        self.enable_whois = enable_whois
        self.enable_tls = enable_tls
        self.network_timeout = network_timeout

    # ----- core ---------------------------------------------------------
    def extract_dict(
        self,
        url: str,
        network_overrides: dict | None = None,
    ) -> dict:
        """Return every feature as a raw dict.

        ``network_overrides`` lets the ML pipeline supply simulated WHOIS/TLS
        values for synthetic URLs that do not resolve. When given, no live
        network lookup is performed for the overridden keys.
        """
        norm = normalize_url(url)
        host = (urlparse(norm).hostname or "").lower()

        feat: dict = {}
        feat.update(extract_lexical(url))

        tld_type, is_thai = classify_tld(host)
        feat["tld_type"] = tld_type
        feat["tld_type_enc"] = TLD_TYPE_MAP.get(tld_type, TLD_TYPE_DEFAULT)
        feat["is_thai_tld"] = is_thai

        # --- v1.3 path / TLD impersonation features ---
        path_tokens = {
            t.lower()
            for t in _PATH_TOKEN_RE.findall(url)
            if t
        }
        feat["has_login_keyword"] = int(bool(path_tokens & LOGIN_KEYWORDS))
        feat["has_suspicious_tld"] = int(_etld(host) in SUSPICIOUS_TLDS)

        # Typosquat distance is meaningless for raw-IP hosts.
        if feat["has_ip"] or not host:
            feat["min_edit_distance"] = 999
            feat["closest_domain"] = None
            feat["is_typosquat"] = 0
            feat["homoglyph_distance"] = 999
            feat["has_punycode"] = 0
            feat["has_mixed_script"] = 0
            feat["path_brand_hit"] = 0
        else:
            feat.update(self.whitelist.whitelist_features(host))
            # IDN / homoglyph features: re-run the closest lookup against
            # the Unicode-decoded + confusable-folded label and keep the
            # smaller of the two distances. This catches xn-- spoofs and
            # Cyrillic look-alikes that the raw ASCII compare misses.
            norm_dist, norm_dom = self.whitelist.closest_normalized(host)
            raw_dist = int(feat["min_edit_distance"])
            feat["homoglyph_distance"] = min(raw_dist, int(norm_dist))
            feat["has_punycode"] = int(has_punycode(host))
            feat["has_mixed_script"] = int(has_mixed_script(host))
            # Promote a homoglyph match to typosquat when the normalized
            # form is closer than the raw form -- otherwise an attacker
            # only has to swap one letter for a Cyrillic look-alike to
            # bypass typosquat detection entirely.
            if (
                not feat["is_typosquat"]
                and norm_dist < raw_dist
                and norm_dist <= 3
                and norm_dom is not None
            ):
                feat["is_typosquat"] = 1
                feat["closest_domain"] = norm_dom
                feat["min_edit_distance"] = int(norm_dist)

            feat["path_brand_hit"] = _path_brand_hit(
                url, brand_label(host), self.whitelist
            )

        # --- WHOIS ---
        if network_overrides and "domain_age_days" in network_overrides:
            feat["domain_age_days"] = network_overrides["domain_age_days"]
            feat["is_known_registrar"] = network_overrides.get(
                "is_known_registrar", IMPUTED_DEFAULTS["is_known_registrar"]
            )
            feat["whois_ok"] = network_overrides.get("whois_ok", 1)
        elif self.enable_whois and host and not feat["has_ip"]:
            feat.update(whois_features(host, timeout=self.network_timeout))
        else:
            feat["domain_age_days"] = IMPUTED_DEFAULTS["domain_age_days"]
            feat["is_known_registrar"] = IMPUTED_DEFAULTS["is_known_registrar"]
            feat["whois_ok"] = 0

        # --- TLS ---
        if network_overrides and "has_valid_cert" in network_overrides:
            feat["has_valid_cert"] = network_overrides["has_valid_cert"]
            feat["cert_age_days"] = network_overrides.get(
                "cert_age_days", IMPUTED_DEFAULTS["cert_age_days"]
            )
            feat["is_self_signed"] = network_overrides.get(
                "is_self_signed", IMPUTED_DEFAULTS["is_self_signed"]
            )
            feat["tls_ok"] = network_overrides.get("tls_ok", 1)
        elif self.enable_tls and host and not feat["has_ip"]:
            feat.update(
                tls_features(host, timeout=self.network_timeout + 0.5)
            )
        else:
            feat["has_valid_cert"] = IMPUTED_DEFAULTS["has_valid_cert"]
            feat["cert_age_days"] = IMPUTED_DEFAULTS["cert_age_days"]
            feat["is_self_signed"] = IMPUTED_DEFAULTS["is_self_signed"]
            feat["tls_ok"] = 0

        return feat

    def extract_vector(
        self, url: str, network_overrides: dict | None = None
    ) -> list[float]:
        """Return the numeric model vector in ``ORDERED_FEATURES`` order."""
        feat = self.extract_dict(url, network_overrides=network_overrides)
        return [float(feat[name]) for name in ORDERED_FEATURES]

    def extract_batch(
        self,
        urls: list[str],
        overrides: list[dict] | None = None,
    ) -> list[list[float]]:
        """Vectorise a list of URLs (used by the training pipeline)."""
        overrides = overrides or [None] * len(urls)
        return [
            self.extract_vector(u, network_overrides=o)
            for u, o in zip(urls, overrides)
        ]


def extract_features(
    url: str,
    whitelist: Whitelist,
    enable_whois: bool = False,
    enable_tls: bool = False,
) -> dict:
    """Convenience one-shot helper."""
    return FeatureExtractor(
        whitelist, enable_whois=enable_whois, enable_tls=enable_tls
    ).extract_dict(url)
