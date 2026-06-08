"""Tests for HTTPS_LOOKALIKE and LOGIN_KEYWORD_DENSE rules (v1.6.1)."""

from __future__ import annotations

from phish_features.rules import (
    RulesEngine,
    rule_https_lookalike,
    rule_login_keyword_dense,
)


def _feat(**kwargs) -> dict:
    base = {
        "has_punycode": 0,
        "has_mixed_script": 0,
        "homoglyph_distance": 999,
        "is_typosquat": 0,
        "has_login_keyword": 0,
        "num_login_keywords": 0,
        "has_suspicious_tld": 0,
        "path_brand_hit": 0,
        "has_ip": 0,
        "has_https": 1,
        "cert_is_lets_encrypt": 0,
        "min_edit_distance": 999,
        "closest_domain": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# HTTPS_LOOKALIKE
# ---------------------------------------------------------------------------

def test_https_lookalike_typosquat():
    hit = rule_https_lookalike(
        "https://krungthai-bank.xyz/login",
        _feat(has_https=1, cert_is_lets_encrypt=1, is_typosquat=1),
    )
    assert hit is not None
    assert hit.rule_id == "HTTPS_LOOKALIKE"
    assert hit.pin_label == "phishing"
    assert hit.delta == 0.30


def test_https_lookalike_path_brand():
    hit = rule_https_lookalike(
        "https://random.top/ktb/login",
        _feat(has_https=1, cert_is_lets_encrypt=1, path_brand_hit=1),
    )
    assert hit is not None
    assert hit.rule_id == "HTTPS_LOOKALIKE"


def test_https_lookalike_login_keyword():
    hit = rule_https_lookalike(
        "https://update-account.xyz/verify",
        _feat(has_https=1, cert_is_lets_encrypt=1, has_login_keyword=1),
    )
    assert hit is not None
    assert hit.rule_id == "HTTPS_LOOKALIKE"


def test_https_lookalike_no_fire_without_free_cert():
    assert rule_https_lookalike(
        "u",
        _feat(has_https=1, cert_is_lets_encrypt=0, is_typosquat=1),
    ) is None


def test_https_lookalike_no_fire_without_https():
    assert rule_https_lookalike(
        "u",
        _feat(has_https=0, cert_is_lets_encrypt=1, is_typosquat=1),
    ) is None


def test_https_lookalike_no_fire_without_brand_signal():
    assert rule_https_lookalike(
        "u",
        _feat(has_https=1, cert_is_lets_encrypt=1,
              is_typosquat=0, path_brand_hit=0, has_login_keyword=0),
    ) is None


# ---------------------------------------------------------------------------
# LOGIN_KEYWORD_DENSE
# ---------------------------------------------------------------------------

def test_login_keyword_dense_fires_at_three():
    hit = rule_login_keyword_dense(
        "https://bank.example/verify/confirm/login",
        _feat(num_login_keywords=3),
    )
    assert hit is not None
    assert hit.rule_id == "LOGIN_KEYWORD_DENSE"
    assert hit.pin_label is None  # soft raise, not a hard pin
    assert hit.delta == 0.25


def test_login_keyword_dense_fires_above_three():
    assert rule_login_keyword_dense("u", _feat(num_login_keywords=5)) is not None


def test_login_keyword_dense_does_not_fire_below_three():
    assert rule_login_keyword_dense("u", _feat(num_login_keywords=2)) is None
    assert rule_login_keyword_dense("u", _feat(num_login_keywords=0)) is None


# ---------------------------------------------------------------------------
# Engine integration: new rules active in DEFAULT_RULES
# ---------------------------------------------------------------------------

def test_engine_includes_https_lookalike():
    engine = RulesEngine()
    feat = _feat(has_https=1, cert_is_lets_encrypt=1, is_typosquat=1)
    result = engine.evaluate("https://krungthai-bank.xyz/login", feat)
    assert "HTTPS_LOOKALIKE" in result.applied_ids()
    assert result.pinned_label == "phishing"


def test_engine_includes_login_keyword_dense():
    engine = RulesEngine()
    feat = _feat(num_login_keywords=4)
    result = engine.evaluate("https://example.com/verify/confirm/account/update", feat)
    assert "LOGIN_KEYWORD_DENSE" in result.applied_ids()
    assert result.score_delta > 0
