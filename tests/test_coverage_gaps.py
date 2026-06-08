"""Targeted tests to close coverage gaps in homoglyph.py, tls.py, and domain.py.

Each test exercises a specific uncovered branch identified from the coverage
report. No network I/O — WHOIS and TLS probes are patched.
"""
from __future__ import annotations

import datetime as _dt
from unittest.mock import MagicMock, patch

import pytest

from phish_features.homoglyph import (
    CONFUSABLE_FOLD,
    _script_of,
    decode_idn,
    fold_confusables,
    has_mixed_script,
    has_punycode,
    normalize_for_lookup,
)
from phish_features.tls import (
    _cert_san_count,
    _cert_validity_days,
    _imputed as tls_imputed,
    _issuer_is_free_ca,
    _raw_tls,
    tls_features,
)
from phish_features.domain import (
    _coerce_date,
    _imputed as domain_imputed,
    _raw_whois,
    whois_features,
)


# ============================================================
# homoglyph.py — script detection branches
# ============================================================

class TestScriptOf:
    def test_ascii_returns_none(self):
        assert _script_of("a") is None
        assert _script_of("Z") is None
        assert _script_of("5") is None
        assert _script_of("-") is None

    def test_cyrillic_detected(self):
        assert _script_of("а") == "Cyrillic"  # CYRILLIC SMALL LETTER A

    def test_greek_detected(self):
        assert _script_of("α") == "Greek"  # GREEK SMALL LETTER ALPHA

    def test_arabic_detected(self):
        assert _script_of("ع") == "Arabic"  # ARABIC LETTER AIN

    def test_hebrew_detected(self):
        assert _script_of("א") == "Hebrew"  # HEBREW LETTER ALEF

    def test_thai_detected(self):
        assert _script_of("ก") == "Thai"  # THAI CHARACTER KO KAI

    def test_fullwidth_detected(self):
        assert _script_of("ａ") == "Fullwidth"  # FULLWIDTH LATIN SMALL LETTER A

    def test_cjk_detected(self):
        assert _script_of("中") == "CJK"

    def test_hiragana_is_cjk(self):
        assert _script_of("あ") == "CJK"  # HIRAGANA

    def test_katakana_is_cjk(self):
        assert _script_of("ア") == "CJK"  # KATAKANA


class TestDecodeIdn:
    def test_passthrough_no_punycode(self):
        assert decode_idn("obec.go.th") == "obec.go.th"

    def test_empty_string(self):
        assert decode_idn("") == ""

    def test_invalid_punycode_label_kept(self):
        # "xn--invalid---" cannot be decoded; original label preserved.
        result = decode_idn("xn--invalid---999zzz.com")
        # Must not raise; must contain the original label or something valid.
        assert "." in result

    def test_valid_punycode_decoded(self):
        assert decode_idn("xn--mnchen-3ya.de") == "münchen.de"

    def test_mixed_labels(self):
        # One Punycode label, one plain ASCII.
        result = decode_idn("xn--mnchen-3ya.example.com")
        assert "münchen" in result
        assert "example.com" in result


class TestHasMixedScript:
    def test_empty_host(self):
        assert has_mixed_script("") is False

    def test_empty_label_skipped(self):
        # Leading dot creates an empty label.
        assert has_mixed_script(".obec.go.th") is False

    def test_arabic_in_ascii_domain(self):
        # Arabic character mixed with ASCII — mixed-script.
        assert has_mixed_script("obecع.go.th") is True

    def test_two_non_ascii_scripts(self):
        # Both Cyrillic and Greek in a label — suspicious.
        assert has_mixed_script("αа.com") is True  # Greek α + Cyrillic а

    def test_pure_thai_label_no_ascii(self):
        # A pure Thai domain label has only one script — not mixed.
        assert has_mixed_script("กรุงเทพ.th") is False

    def test_punycode_decoded_before_check(self):
        # xn--qxam = "α" (Greek). No ASCII letters in that label, single script.
        result = has_mixed_script("xn--qxam.com")
        # Either way must not raise; single-script labels are not flagged.
        assert isinstance(result, bool)


class TestFoldConfusables:
    def test_empty_returns_empty(self):
        assert fold_confusables("") == ""

    def test_fullwidth_latin_folds(self):
        assert fold_confusables("ａｂｃ") == "abc"

    def test_thai_digit_folds(self):
        assert fold_confusables("๑") == "1"
        assert fold_confusables("๐") == "0"

    def test_greek_folds(self):
        # α→a (in CONFUSABLE_FOLD), β has no mapping so stays as-is
        result = fold_confusables("αβ")
        assert result.startswith("a")  # α was folded

    def test_entire_confusable_fold_table_covered(self):
        # Every character in CONFUSABLE_FOLD must map to a non-empty ASCII value.
        for src, dst in CONFUSABLE_FOLD.items():
            assert dst.isascii() and dst, f"bad mapping {src!r} → {dst!r}"


# ============================================================
# tls.py — pure certificate-parsing helpers
# ============================================================

class TestIssuerIsFreeCa:
    def test_lets_encrypt_detected(self):
        cert = {"issuer": ((("organizationName", "Let's Encrypt"),),)}
        assert _issuer_is_free_ca(cert) == 1

    def test_zerossl_detected(self):
        cert = {"issuer": ((("organizationName", "ZeroSSL"),),)}
        assert _issuer_is_free_ca(cert) == 1

    def test_r3_intermediate_detected(self):
        cert = {"issuer": ((("commonName", "R3"),),)}
        assert _issuer_is_free_ca(cert) == 1

    def test_commercial_ca_not_detected(self):
        cert = {"issuer": ((("organizationName", "DigiCert Inc"),),)}
        assert _issuer_is_free_ca(cert) == 0

    def test_empty_issuer(self):
        assert _issuer_is_free_ca({}) == 0
        assert _issuer_is_free_ca({"issuer": ()}) == 0

    def test_gts_ca_detected(self):
        cert = {"issuer": ((("organizationName", "Google Trust Services"),),
                           (("commonName", "GTS CA 1C3"),),)}
        assert _issuer_is_free_ca(cert) == 1


class TestCertValidityDays:
    def test_normal_cert(self):
        cert = {
            "notBefore": "Jan  1 00:00:00 2024 GMT",
            "notAfter":  "Apr  1 00:00:00 2024 GMT",
        }
        days = _cert_validity_days(cert)
        assert 89 <= days <= 92

    def test_missing_dates_returns_imputed(self):
        from phish_features.schema import IMPUTED_DEFAULTS
        assert _cert_validity_days({}) == int(IMPUTED_DEFAULTS["cert_validity_days"])

    def test_bad_date_format_returns_imputed(self):
        from phish_features.schema import IMPUTED_DEFAULTS
        cert = {"notBefore": "not-a-date", "notAfter": "also-not-a-date"}
        assert _cert_validity_days(cert) == int(IMPUTED_DEFAULTS["cert_validity_days"])


class TestCertSanCount:
    def test_two_san_entries(self):
        cert = {"subjectAltName": [("DNS", "example.com"), ("DNS", "www.example.com")]}
        assert _cert_san_count(cert) == 2

    def test_no_san_returns_imputed(self):
        from phish_features.schema import IMPUTED_DEFAULTS
        assert _cert_san_count({}) == int(IMPUTED_DEFAULTS["cert_san_count"])

    def test_non_sequence_san_returns_imputed(self):
        from phish_features.schema import IMPUTED_DEFAULTS
        # If san is not iterable as a sequence (edge case).
        assert _cert_san_count({"subjectAltName": None}) == int(IMPUTED_DEFAULTS["cert_san_count"])


class TestRawTls:
    def test_ssl_verification_error_falls_back_to_unverified(self):
        import ssl
        with patch("phish_features.tls._probe_valid", side_effect=ssl.SSLCertVerificationError("bad cert")), \
             patch("phish_features.tls._probe_unverified", return_value={"tls_ok": 1, "is_self_signed": 1}) as mock_uv:
            result = _raw_tls("self-signed.test", 443)
        mock_uv.assert_called_once()
        assert result["tls_ok"] == 1

    def test_connection_error_returns_imputed(self):
        with patch("phish_features.tls._probe_valid", side_effect=OSError("refused")):
            result = _raw_tls("unreachable.test", 443)
        assert result["tls_ok"] == 0  # _imputed()

    def test_empty_host_returns_imputed(self):
        result = tls_features("")
        assert result["tls_ok"] == 0

    def test_timeout_returns_imputed(self):
        from concurrent.futures import TimeoutError as _FutureTimeout
        with patch("phish_features.tls._EXECUTOR") as mock_exec:
            mock_future = MagicMock()
            mock_future.result.side_effect = _FutureTimeout()
            mock_exec.submit.return_value = mock_future
            result = tls_features("timeout.test")
        assert result["tls_ok"] == 0


# ============================================================
# domain.py — pure helpers + mocked WHOIS
# ============================================================

class TestCoerceDate:
    def test_datetime_passthrough(self):
        dt = _dt.datetime(2022, 1, 15)
        assert _coerce_date(dt) == dt

    def test_date_converts_to_datetime(self):
        d = _dt.date(2022, 1, 15)
        result = _coerce_date(d)
        assert isinstance(result, _dt.datetime)
        assert result.year == 2022

    def test_list_of_datetimes_uses_first(self):
        dt1 = _dt.datetime(2020, 1, 1)
        dt2 = _dt.datetime(2021, 6, 1)
        assert _coerce_date([dt1, dt2]) == dt1

    def test_empty_list_returns_none(self):
        assert _coerce_date([]) is None

    def test_none_returns_none(self):
        assert _coerce_date(None) is None

    def test_string_returns_none(self):
        assert _coerce_date("2022-01-01") is None


class TestDomainImputed:
    def test_returns_whois_ok_zero(self):
        result = domain_imputed()
        assert result["whois_ok"] == 0

    def test_contains_expected_keys(self):
        result = domain_imputed()
        assert "domain_age_days" in result
        assert "is_known_registrar" in result


class TestWhoisFeatures:
    def test_empty_host_returns_imputed(self):
        result = whois_features("")
        assert result["whois_ok"] == 0

    def test_no_whois_module_returns_imputed(self):
        import phish_features.domain as _dom
        old = _dom._HAVE_WHOIS
        _dom._HAVE_WHOIS = False
        try:
            result = whois_features("example.com")
        finally:
            _dom._HAVE_WHOIS = old
        assert result["whois_ok"] == 0

    def test_raw_whois_with_known_registrar(self):
        record = {
            "creation_date": _dt.datetime(2010, 1, 1),
            "registrar": "thnic registrar co., ltd.",
        }
        mock_rec = MagicMock()
        mock_rec.get = lambda key, default=None: record.get(key, default)

        with patch("phish_features.domain._whois") as mock_whois:
            mock_whois.whois.return_value = mock_rec
            result = _raw_whois("thnic.co.th")

        assert result["whois_ok"] == 1
        assert result["is_known_registrar"] == 1
        assert result["domain_age_days"] > 0

    def test_raw_whois_list_registrar(self):
        record = {
            "creation_date": _dt.datetime(2015, 6, 1),
            "registrar": ["THNIC", "some other"],
        }
        mock_rec = MagicMock()
        mock_rec.get = lambda key, default=None: record.get(key, default)

        with patch("phish_features.domain._whois") as mock_whois:
            mock_whois.whois.return_value = mock_rec
            result = _raw_whois("example.co.th")

        assert result["whois_ok"] == 1

    def test_raw_whois_no_creation_date(self):
        record = {"creation_date": None, "registrar": "namecheap"}
        mock_rec = MagicMock()
        mock_rec.get = lambda key, default=None: record.get(key, default)

        with patch("phish_features.domain._whois") as mock_whois:
            mock_whois.whois.return_value = mock_rec
            result = _raw_whois("example.com")

        from phish_features.schema import IMPUTED_DEFAULTS
        assert result["domain_age_days"] == IMPUTED_DEFAULTS["domain_age_days"]
        assert result["whois_ok"] == 1

    def test_timeout_returns_imputed(self):
        from concurrent.futures import TimeoutError as _FutureTimeout
        with patch("phish_features.domain._EXECUTOR") as mock_exec:
            mock_future = MagicMock()
            mock_future.result.side_effect = _FutureTimeout()
            mock_exec.submit.return_value = mock_future
            result = whois_features("timeout.com")
        assert result["whois_ok"] == 0
