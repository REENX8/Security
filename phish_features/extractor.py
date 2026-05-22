"""The single feature-extraction orchestrator.

Both the ML pipeline and the FastAPI backend import ``FeatureExtractor`` from
here. There is no second implementation, so train/serve skew is structurally
impossible for the lexical + whitelist features. Network features (WHOIS, TLS)
are optional and degrade to imputed defaults.
"""

from __future__ import annotations

from urllib.parse import urlparse

from .domain import whois_features
from .lexical import extract_lexical, normalize_url
from .schema import (
    IMPUTED_DEFAULTS,
    ORDERED_FEATURES,
    TLD_TYPE_DEFAULT,
    TLD_TYPE_MAP,
)
from .tls import tls_features
from .whitelist import Whitelist


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

        # Typosquat distance is meaningless for raw-IP hosts.
        if feat["has_ip"] or not host:
            feat["min_edit_distance"] = 999
            feat["closest_domain"] = None
            feat["is_typosquat"] = 0
        else:
            feat.update(self.whitelist.whitelist_features(host))

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
