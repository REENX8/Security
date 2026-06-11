"""Tests for HTTPS_LOOKALIKE and LOGIN_KEYWORD_DENSE rules (v1.6.1)."""

from __future__ import annotations

from phish_features.rules import (
    RulesEngine,
    rule_encoded_ip_host,
    rule_https_lookalike,
    rule_known_good_domain,
    rule_login_keyword_dense,
    rule_self_signed_login,
)


def _feat(**kwargs) -> dict:
    base = {
        "has_punycode": 0,
        "has_mixed_script": 0,
        "homoglyph_distance": 999,
        "is_typosquat": 0,
        "has_login_keyword": 0,
        "num_login_keywords": 0,
        "num_strong_login_keywords": 0,
        "has_suspicious_tld": 0,
        "has_high_risk_tld": 0,
        "path_brand_hit": 0,
        "has_ip": 0,
        "has_https": 1,
        "cert_is_lets_encrypt": 0,
        "is_self_signed": 0,
        "has_encoded_ip": 0,
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


def test_https_lookalike_path_brand_soft_raises():
    # Brand in path + free cert raises the score but does NOT force the
    # verdict -- a legit site can host brand content behind a free DV cert.
    hit = rule_https_lookalike(
        "https://random.top/ktb/login",
        _feat(has_https=1, cert_is_lets_encrypt=1, path_brand_hit=1),
    )
    assert hit is not None
    assert hit.rule_id == "HTTPS_LOOKALIKE"
    assert hit.pin_label is None
    assert hit.delta > 0


def test_https_lookalike_login_keyword_alone_does_not_fire():
    # v1.8: a free cert + login keyword describes half the legitimate web
    # (every ordinary login portal on Let's Encrypt) -- no brand signal,
    # no rule hit. The old behaviour force-blocked exactly these sites.
    assert rule_https_lookalike(
        "https://update-account.xyz/verify",
        _feat(has_https=1, cert_is_lets_encrypt=1, has_login_keyword=1,
              num_strong_login_keywords=1),
    ) is None


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
# ENCODED_IP_HOST
# ---------------------------------------------------------------------------

def test_encoded_ip_host_fires():
    hit = rule_encoded_ip_host("http://0x7f000001/login", _feat(has_encoded_ip=1))
    assert hit is not None
    assert hit.rule_id == "ENCODED_IP_HOST"
    assert hit.pin_label == "phishing"
    assert hit.delta == 0.45


def test_encoded_ip_host_no_fire_when_absent():
    assert rule_encoded_ip_host("http://example.com/login", _feat(has_encoded_ip=0)) is None


# ---------------------------------------------------------------------------
# SELF_SIGNED_CRED
# ---------------------------------------------------------------------------

def test_self_signed_login_fires():
    hit = rule_self_signed_login(
        "https://1.2.3.4/login",
        _feat(is_self_signed=1, num_strong_login_keywords=1),
    )
    assert hit is not None
    assert hit.rule_id == "SELF_SIGNED_CRED"
    assert hit.pin_label == "phishing"
    assert hit.delta == 0.35


def test_self_signed_login_no_fire_without_credential():
    assert rule_self_signed_login(
        "u", _feat(is_self_signed=1, num_strong_login_keywords=0)
    ) is None


def test_self_signed_login_no_fire_with_ca_cert():
    assert rule_self_signed_login(
        "u", _feat(is_self_signed=0, num_strong_login_keywords=1)
    ) is None


# ---------------------------------------------------------------------------
# KNOWN_GOOD_DOMAIN (false-positive guard for trusted brands)
# ---------------------------------------------------------------------------

def test_known_good_exact_host_pins_safe():
    hit = rule_known_good_domain("https://google.com", _feat())
    assert hit is not None
    assert hit.rule_id == "KNOWN_GOOD_DOMAIN"
    assert hit.pin_label == "safe"
    assert hit.delta == -0.60


def test_known_good_true_subdomain_pins_safe():
    # Legit brand portals on deep subdomains must not be blocked.
    for u in (
        "https://console.cloud.google.com",
        "https://login.microsoftonline.com",
        "https://signin.aws.amazon.com",
        "https://id.line.me",
    ):
        hit = rule_known_good_domain(u, _feat())
        assert hit is not None and hit.pin_label == "safe", u


def test_known_good_does_not_match_lookalikes():
    # Registrable domain belongs to the attacker -> must NOT be pinned safe.
    for u in (
        "https://google.com.evil.xyz/login",      # brand as a subdomain label
        "https://secure-google.com/login",         # hyphenated lookalike
        "https://notgoogle.com/login",             # substring, not a subdomain
        "http://goog1e.com/login",                 # typosquat
    ):
        assert rule_known_good_domain(u, _feat()) is None, u


def test_known_good_honours_at_trick():
    # The real host is evil.xyz; the brand before '@' must not earn a safe pin.
    assert rule_known_good_domain("https://google.com@evil.xyz/login", _feat()) is None


def test_known_good_excludes_user_content_hosts():
    # amazonaws.com / github.io host untrusted user content and are deliberately
    # NOT in the safe-list, so phishing on them is still detectable.
    assert rule_known_good_domain("https://evil.s3.amazonaws.com/login", _feat()) is None
    assert rule_known_good_domain("https://attacker.github.io/login", _feat()) is None


def test_known_good_phishing_pin_still_wins():
    # An @-trick on a known-good-looking URL: AT_TRICK pins phishing, which must
    # override any safe pin (defence in depth).
    engine = RulesEngine()
    result = engine.evaluate("https://google.com@evil.xyz/login", _feat())
    assert result.pinned_label == "phishing"


# ---------------------------------------------------------------------------
# Engine integration: new rules active in DEFAULT_RULES
# ---------------------------------------------------------------------------

def test_engine_includes_encoded_ip_host():
    engine = RulesEngine()
    result = engine.evaluate("http://0x7f000001/login", _feat(has_encoded_ip=1))
    assert "ENCODED_IP_HOST" in result.applied_ids()
    assert result.pinned_label == "phishing"


def test_engine_includes_self_signed_cred():
    engine = RulesEngine()
    result = engine.evaluate(
        "https://1.2.3.4/login",
        _feat(is_self_signed=1, num_strong_login_keywords=1),
    )
    assert "SELF_SIGNED_CRED" in result.applied_ids()
    assert result.pinned_label == "phishing"


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
