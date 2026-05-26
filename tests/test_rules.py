"""Tests for the heuristic rules engine."""

from __future__ import annotations

import pytest

from phish_features.rules import (
    RuleHit,
    RulesEngine,
    rule_at_trick,
    rule_ip_with_login,
    rule_path_brand_impersonation,
    rule_punycode_brand_match,
    rule_typosquat_with_login,
    rule_whitelisted_exact,
    rule_cheap_tld_no_https,
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


def test_typosquat_cred_fires_with_brand_in_message():
    hit = rule_typosquat_with_login(
        "u", _feat(is_typosquat=1, has_login_keyword=1, closest_domain="obec.go.th")
    )
    assert hit and hit.rule_id == "TYPOSQUAT_CRED"
    assert "obec.go.th" in hit.message


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
