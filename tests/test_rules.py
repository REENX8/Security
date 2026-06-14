"""Tests for the heuristic rules engine."""

from __future__ import annotations

from phish_features.lexical import _has_encoded_ip, _has_redirect_in_path
from phish_features.rules import (
    RulesEngine,
    rule_at_trick,
    rule_cheap_tld_no_https,
    rule_ip_with_login,
    rule_path_brand_impersonation,
    rule_punycode_brand_match,
    rule_redirect_confusion,
    rule_subdomain_camouflage,
    rule_typosquat_with_login,
    rule_whitelisted_exact,
)


def _feat(**kwargs) -> dict:
    base = {
        "has_punycode": 0,
        "has_mixed_script": 0,
        "homoglyph_distance": 999,
        "is_typosquat": 0,
        "has_login_keyword": 0,
        "has_suspicious_tld": 0,
        "path_brand_hit": 0,
        "has_ip": 0,
        "has_https": 1,
        "min_edit_distance": 999,
        "closest_domain": None,
    }
    base.update(kwargs)
    return base


def test_at_trick_fires():
    hit = rule_at_trick("https://bank.com@evil.xyz/login", _feat())
    assert hit and hit.rule_id == "AT_TRICK" and hit.pin_label == "phishing"


def test_at_trick_does_not_fire_on_plain_url():
    assert rule_at_trick("https://example.com/page", _feat()) is None


def test_idn_homograph_requires_both_features():
    assert rule_punycode_brand_match("u", _feat(has_punycode=0)) is None
    assert rule_punycode_brand_match(
        "u", _feat(has_punycode=1, homoglyph_distance=2)
    ).rule_id == "IDN_HOMOGRAPH"
    # Punycode but the closest brand is far away -- not a homograph attack.
    assert rule_punycode_brand_match(
        "u", _feat(has_punycode=1, homoglyph_distance=5)
    ) is None


def test_typosquat_cred_hard_pins_with_cheap_tld():
    # Typosquat + login keyword + suspicious TLD → hard pin phishing.
    hit = rule_typosquat_with_login(
        "u", _feat(is_typosquat=1, has_login_keyword=1,
                   has_suspicious_tld=1, closest_domain="obec.go.th")
    )
    assert hit and hit.rule_id == "TYPOSQUAT_CRED"
    assert hit.pin_label == "phishing"
    assert "obec.go.th" in hit.message


def test_typosquat_cred_hard_pins_without_https():
    # Typosquat + login keyword + plain HTTP → hard pin phishing.
    hit = rule_typosquat_with_login(
        "u", _feat(is_typosquat=1, has_login_keyword=1,
                   has_https=0, closest_domain="obec.go.th")
    )
    assert hit and hit.rule_id == "TYPOSQUAT_CRED"
    assert hit.pin_label == "phishing"


def test_typosquat_cred_soft_raises_on_https_safe_tld():
    # Typosquat + login keyword on HTTPS .com/.me → raise score but no hard pin.
    # Avoids false-positive phishing verdict for legitimate services whose brand
    # name happens to be within edit distance of a Thai-gov domain (e.g. line.me).
    hit = rule_typosquat_with_login(
        "u", _feat(is_typosquat=1, has_login_keyword=1,
                   has_https=1, has_suspicious_tld=0, closest_domain="life.ac.th")
    )
    assert hit and hit.rule_id == "TYPOSQUAT_CRED"
    assert hit.pin_label is None
    assert hit.delta > 0


def test_path_brand_bait_requires_cheap_tld():
    assert rule_path_brand_impersonation(
        "u", _feat(path_brand_hit=1, has_suspicious_tld=0)
    ) is None
    assert rule_path_brand_impersonation(
        "u", _feat(path_brand_hit=1, has_suspicious_tld=1)
    ).rule_id == "PATH_BRAND_BAIT"


def test_ip_cred():
    assert rule_ip_with_login(
        "u", _feat(has_ip=1, has_login_keyword=1)
    ).rule_id == "IP_CRED"


def test_whitelist_safety_net_pins_safe():
    hit = rule_whitelisted_exact(
        "https://www.obec.go.th", _feat(min_edit_distance=0)
    )
    assert hit and hit.pin_label == "safe"


def test_whitelist_does_not_pin_safe_if_homograph():
    """A Punycode lookalike at distance 0 must NOT be force-safe."""
    assert rule_whitelisted_exact(
        "u",
        _feat(min_edit_distance=0, has_punycode=1)
    ) is None


def test_cheap_tld_no_https_does_not_pin_label():
    hit = rule_cheap_tld_no_https(
        "u", _feat(has_suspicious_tld=1, has_https=0)
    )
    assert hit and hit.pin_label is None and hit.delta > 0


def test_engine_combines_hits_and_clamps_delta():
    engine = RulesEngine()
    feat = _feat(
        has_ip=1,
        has_login_keyword=1,
        is_typosquat=1,
        closest_domain="krungthai.com",
    )
    result = engine.evaluate("http://1.2.3.4/login", feat)
    assert "IP_CRED" in result.applied_ids()
    assert result.pinned_label == "phishing"
    assert 0 < result.score_delta <= 1.0  # clamped


def test_engine_phishing_pin_overrules_safe_pin():
    """An attack signal must win over the whitelist safety net."""
    engine = RulesEngine()
    feat = _feat(
        min_edit_distance=0,    # would fire WHITELIST_EXACT...
        has_punycode=1,
        homoglyph_distance=1,   # ...but this is an IDN homograph attack
    )
    result = engine.evaluate("u", feat)
    assert result.pinned_label == "phishing"


# --- v1.7 new features ---

def test_hex_ip_detected():
    assert _has_encoded_ip("0x5f0a0b01") == 1
    assert _has_encoded_ip("0xdeadbeef") == 1
    assert _has_encoded_ip("0x4014d2ab") == 1
    assert _has_encoded_ip("0x7f000001") == 1


def test_octal_ip_detected():
    assert _has_encoded_ip("0337.012.013.001") == 1
    assert _has_encoded_ip("0177.0000.0000.0001") == 1
    assert _has_encoded_ip("010.020.030.040") == 1


def test_normal_host_not_flagged_as_encoded_ip():
    assert _has_encoded_ip("krungthai.com") == 0
    assert _has_encoded_ip("8.8.8.8") == 0
    assert _has_encoded_ip("192.168.1.1") == 0
    assert _has_encoded_ip("") == 0


def test_redirect_in_path_detected():
    assert _has_redirect_in_path("http://evil.xyz/redirect?url=https://krungthai.com/login") == 1
    assert _has_redirect_in_path("http://safe.com/safe/https://evil.com/phish") == 1
    assert _has_redirect_in_path("http://track.com/go?next=https://bank.com") == 1
    assert _has_redirect_in_path("http://cdn.com/?goto=https://obec.go.th") == 1


def test_redirect_in_path_not_false_positive():
    assert _has_redirect_in_path("https://krungthai.com/login") == 0
    assert _has_redirect_in_path("http://evil.xyz/page?user=foo&pass=bar") == 0


def test_mixed_script_credential_raises_without_pin():
    from phish_features.rules import rule_mixed_script_credential
    feat = _feat(has_mixed_script=1, has_login_keyword=1)
    hit = rule_mixed_script_credential("http://truemоney.com/wallet", feat)
    assert hit is not None
    assert hit.rule_id == "MIXED_SCRIPT_CRED"
    assert hit.pin_label is None
    assert hit.delta > 0


def test_mixed_script_credential_needs_both_signals():
    from phish_features.rules import rule_mixed_script_credential
    # Mixed script but no login keyword -> no fire (avoids FP on legit IDN).
    assert rule_mixed_script_credential("u", _feat(has_mixed_script=1)) is None
    # Login keyword but ASCII host -> no fire.
    assert rule_mixed_script_credential("u", _feat(has_login_keyword=1)) is None


def test_subdomain_camouflage_rule_fires():
    feat = _feat(num_subdomains=3, path_brand_hit=1, is_typosquat=0)
    hit = rule_subdomain_camouflage("http://krungthai.com.evil.xyz/login", feat)
    assert hit is not None
    assert hit.rule_id == "SUBDOMAIN_CAMOUFLAGE"
    assert hit.pin_label == "phishing"


def test_subdomain_camouflage_does_not_fire_without_brand_in_path():
    feat = _feat(num_subdomains=3, path_brand_hit=0, is_typosquat=0)
    assert rule_subdomain_camouflage("u", feat) is None


def test_subdomain_camouflage_does_not_fire_for_typosquat():
    # When is_typosquat=1 the TYPOSQUAT_CRED rule handles it; no double-fire.
    feat = _feat(num_subdomains=3, path_brand_hit=1, is_typosquat=1)
    assert rule_subdomain_camouflage("u", feat) is None


def test_subdomain_camouflage_fires_on_whitelist_domain_in_subdomain():
    # v1.9 arm: a full agency domain embedded as a subdomain prefix fires
    # even without path_brand_hit and even for short brands (sso).
    feat = _feat(
        num_subdomains=0, path_brand_hit=0, is_typosquat=0,
        has_whitelist_domain_in_subdomain=1,
    )
    hit = rule_subdomain_camouflage(
        "http://www.sso.go.th.welfare-claim.online/login", feat
    )
    assert hit is not None
    assert hit.rule_id == "SUBDOMAIN_CAMOUFLAGE"
    assert hit.pin_label == "phishing"


def test_redirect_confusion_rule_fires():
    feat = _feat(path_redirect_hit=1, has_login_keyword=1)
    hit = rule_redirect_confusion("http://evil.xyz/go?redirect=http://bank.com/login", feat)
    assert hit is not None
    assert hit.rule_id == "REDIRECT_CONFUSION"
    assert hit.pin_label is None  # raise score but don't force label


def test_redirect_confusion_does_not_fire_without_login_keyword():
    feat = _feat(path_redirect_hit=1, has_login_keyword=0)
    assert rule_redirect_confusion("u", feat) is None
