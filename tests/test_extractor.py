"""FeatureExtractor end-to-end tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from phish_features import (
    IMPUTED_DEFAULTS,
    ORDERED_FEATURES,
    FeatureExtractor,
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
    """v1.8 schema invariants: 49 features, no dups, defaults are a subset."""
    from phish_features.schema import FEATURE_SCHEMA_VERSION, N_FEATURES

    assert FEATURE_SCHEMA_VERSION == "1.8.0"
    assert N_FEATURES == 49
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
    # Brand label (>= 4 chars) in path on a cheap/abused TLD fires the flag.
    # "krungthai" in path + ".online" suspicious TLD triggers both path_brand_hit
    # and has_suspicious_tld, so host_has_brand_and_suspicious_tld == 1.
    spoof = extractor.extract_dict("https://phish.online/krungthai/login")
    assert spoof["host_has_brand_and_suspicious_tld"] == 1
    assert spoof["path_brand_hit"] == 1
    assert spoof["has_suspicious_tld"] == 1
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


# --- v1.8 false-positive fixes ---

def test_login_keyword_ignores_hostname(extractor):
    """has_login_keyword must come from the PATH/QUERY only -- legitimate
    auth hosts (login.*, accounts.*, support.*) must not carry the flag."""
    for url in (
        "https://login.microsoftonline.com/",
        "https://accounts.google.com/",
        "https://support.apple.com/en-us",
        "https://secure.bangkokbank.com/",
    ):
        feat = extractor.extract_dict(url)
        assert feat["has_login_keyword"] == 0, url
        assert feat["num_strong_login_keywords"] == 0, url
    # ... while a keyword in the path still fires.
    feat = extractor.extract_dict("https://example.com/login")
    assert feat["has_login_keyword"] == 1
    assert feat["num_strong_login_keywords"] == 1


def test_strong_login_keywords_exclude_weak_tier(extractor):
    feat = extractor.extract_dict("https://example.com/customer/support/billing")
    assert feat["has_login_keyword"] == 1       # weak tier still counts here
    assert feat["num_strong_login_keywords"] == 0
    feat = extractor.extract_dict("https://example.com/verify-password?otp=1")
    assert feat["num_strong_login_keywords"] == 3


def test_high_risk_tld_is_subset_of_suspicious(extractor):
    from phish_features.schema import HIGH_RISK_TLDS, SUSPICIOUS_TLDS

    assert HIGH_RISK_TLDS < SUSPICIOUS_TLDS
    risky = extractor.extract_dict("https://evil.tk/login")
    assert risky["has_high_risk_tld"] == 1 and risky["has_suspicious_tld"] == 1
    cheap = extractor.extract_dict("https://somecafe.online/menu")
    assert cheap["has_high_risk_tld"] == 0 and cheap["has_suspicious_tld"] == 1
    com = extractor.extract_dict("https://example.com/")
    assert com["has_high_risk_tld"] == 0 and com["has_suspicious_tld"] == 0


def test_path_brand_hit_requires_full_segment(extractor):
    # Brand as its own path segment -> impersonation kit pattern.
    kit = extractor.extract_dict("https://secure-update.cc/krungthai/login")
    assert kit["path_brand_hit"] == 1
    # Brand as a sub-token of a content slug / asset name -> NOT a hit.
    for url in (
        "https://cdn.example.com/obec-logo/image.png",
        "https://news.example.co.th/news/obec-budget-2026",
    ):
        assert extractor.extract_dict(url)["path_brand_hit"] == 0, url
    # Brand as a file segment still hits.
    page = extractor.extract_dict("https://secure-update.cc/krungthai.html")
    assert page["path_brand_hit"] == 1


def test_host_brand_token_hit(extractor):
    # Brand + suffix host (too far for the proportional typosquat gate).
    assert extractor.extract_dict("https://kmitl-th.com/student-login")[
        "host_brand_token_hit"] == 1
    # Brand as a subdomain label of an attacker domain.
    assert extractor.extract_dict("http://obec.go.th.evil-domain.net/wp-login.php")[
        "host_brand_token_hit"] == 1
    # The brand's own host (any subdomain) is exempt.
    assert extractor.extract_dict("https://www.obec.go.th/news")[
        "host_brand_token_hit"] == 0
    # Unrelated hosts don't trip it.
    assert extractor.extract_dict("https://my-startup.site/login")[
        "host_brand_token_hit"] == 0


def test_extract_batch_matches_individual(extractor):
    urls = [
        "https://www.obec.go.th",
        "http://obec.com/login",
        "https://google.com",
    ]
    batch = extractor.extract_batch(urls)
    individual = [extractor.extract_vector(u) for u in urls]
    assert batch == individual
