"""FeatureExtractor end-to-end tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from phish_features import (
    FeatureExtractor,
    IMPUTED_DEFAULTS,
    ORDERED_FEATURES,
    Whitelist,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def extractor() -> FeatureExtractor:
    wl = Whitelist.from_json(str(ROOT / "models" / "whitelist.json"))
    return FeatureExtractor(wl, enable_whois=False, enable_tls=False)


def test_extract_dict_has_all_ordered_features(extractor):
    feat = extractor.extract_dict("https://www.obec.go.th")
    for name in ORDERED_FEATURES:
        assert name in feat, f"missing feature: {name}"


def test_extract_vector_length_matches_schema(extractor):
    v = extractor.extract_vector("https://www.obec.go.th")
    assert len(v) == len(ORDERED_FEATURES)
    assert all(isinstance(x, float) for x in v)


def test_imputed_defaults_when_network_disabled(extractor):
    feat = extractor.extract_dict("https://example.com")
    assert feat["whois_ok"] == 0
    assert feat["tls_ok"] == 0
    assert feat["domain_age_days"] == IMPUTED_DEFAULTS["domain_age_days"]
    assert feat["has_valid_cert"] == IMPUTED_DEFAULTS["has_valid_cert"]


def test_network_overrides_take_precedence(extractor):
    overrides = {
        "domain_age_days": 4242,
        "is_known_registrar": 1,
        "whois_ok": 1,
        "has_valid_cert": 1,
        "cert_age_days": 90,
        "is_self_signed": 0,
        "tls_ok": 1,
    }
    feat = extractor.extract_dict(
        "https://www.example.com", network_overrides=overrides
    )
    assert feat["domain_age_days"] == 4242
    assert feat["whois_ok"] == 1
    assert feat["tls_ok"] == 1
    assert feat["has_valid_cert"] == 1


def test_ip_host_skips_whitelist(extractor):
    feat = extractor.extract_dict("http://203.0.113.45/login")
    assert feat["has_ip"] == 1
    assert feat["is_typosquat"] == 0
    assert feat["min_edit_distance"] == 999


def test_extract_dict_has_idn_features(extractor):
    feat = extractor.extract_dict("https://www.obec.go.th")
    for name in ("has_punycode", "has_mixed_script", "homoglyph_distance"):
        assert name in feat, f"missing v1.2 feature: {name}"


def test_schema_contract_v15(extractor):
    """v1.5 schema invariants: 42 features, no dups, defaults are a subset."""
    from phish_features.schema import FEATURE_SCHEMA_VERSION, N_FEATURES

    assert FEATURE_SCHEMA_VERSION == "1.5.0"
    assert N_FEATURES == 42
    assert len(set(ORDERED_FEATURES)) == N_FEATURES
    assert set(IMPUTED_DEFAULTS).issubset(set(ORDERED_FEATURES))


def test_v15_features_present_and_imputed(extractor):
    feat = extractor.extract_dict("https://example.com")
    for name in (
        "digit_to_letter_ratio",
        "cert_is_lets_encrypt",
        "cert_validity_days",
        "cert_san_count",
        "host_has_brand_and_suspicious_tld",
    ):
        assert name in feat, f"missing v1.5 feature: {name}"
    # TLS-derived features fall back to the imputed "unknown" defaults when
    # the network is disabled.
    assert feat["cert_is_lets_encrypt"] == IMPUTED_DEFAULTS["cert_is_lets_encrypt"]
    assert feat["cert_validity_days"] == IMPUTED_DEFAULTS["cert_validity_days"]
    assert feat["cert_san_count"] == IMPUTED_DEFAULTS["cert_san_count"]


def test_digit_to_letter_ratio(extractor):
    # IP host has no letters -> ratio is the digit count.
    assert extractor.extract_dict("http://203.0.113.45/x")["digit_to_letter_ratio"] == 9.0
    # Letter-only host -> zero.
    assert extractor.extract_dict("https://obec.go.th")["digit_to_letter_ratio"] == 0.0


def test_brand_on_suspicious_tld_interaction(extractor):
    # Brand impersonated (path/typosquat) on a cheap/abused TLD fires the flag.
    spoof = extractor.extract_dict("https://www.scb.co.th@phish.online/auth")
    assert spoof["host_has_brand_and_suspicious_tld"] == 1
    # Legit brand on its real Thai TLD does not.
    legit = extractor.extract_dict("https://obec.go.th/news")
    assert legit["host_has_brand_and_suspicious_tld"] == 0


def test_v15_tls_overrides_take_precedence(extractor):
    overrides = {
        "has_valid_cert": 1,
        "tls_ok": 1,
        "cert_is_lets_encrypt": 1,
        "cert_validity_days": 90,
        "cert_san_count": 2,
    }
    feat = extractor.extract_dict(
        "https://www.example.com", network_overrides=overrides
    )
    assert feat["cert_is_lets_encrypt"] == 1
    assert feat["cert_validity_days"] == 90
    assert feat["cert_san_count"] == 2


def test_extract_batch_matches_individual(extractor):
    urls = [
        "https://www.obec.go.th",
        "http://obec.com/login",
        "https://google.com",
    ]
    batch = extractor.extract_batch(urls)
    individual = [extractor.extract_vector(u) for u in urls]
    assert batch == individual
