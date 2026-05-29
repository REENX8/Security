"""Unit tests for the v1.5 TLS certificate parsing helpers.

These operate on the dict shape returned by ``ssl.getpeercert()`` so they
need no network and no live handshake.
"""

from __future__ import annotations

from phish_features.schema import IMPUTED_DEFAULTS
from phish_features.tls import (
    _cert_san_count,
    _cert_validity_days,
    _issuer_is_free_ca,
)


def _cert(issuer=(), not_before=None, not_after=None, san=None) -> dict:
    cert: dict = {"issuer": issuer}
    if not_before:
        cert["notBefore"] = not_before
    if not_after:
        cert["notAfter"] = not_after
    if san is not None:
        cert["subjectAltName"] = san
    return cert


def test_issuer_free_ca_lets_encrypt():
    issuer = (
        (("countryName", "US"),),
        (("organizationName", "Let's Encrypt"),),
        (("commonName", "R3"),),
    )
    assert _issuer_is_free_ca(_cert(issuer=issuer)) == 1


def test_issuer_free_ca_intermediate_marker():
    # Some certs only carry the intermediate CN (e.g. E5) as the issuer.
    issuer = ((("commonName", "E5"),),)
    assert _issuer_is_free_ca(_cert(issuer=issuer)) == 1


def test_issuer_paid_ca_is_not_free():
    issuer = (
        (("organizationName", "DigiCert Inc"),),
        (("commonName", "DigiCert TLS RSA SHA256 2020 CA1"),),
    )
    assert _issuer_is_free_ca(_cert(issuer=issuer)) == 0


def test_issuer_empty_is_not_free():
    assert _issuer_is_free_ca(_cert()) == 0


def test_validity_days_short_lived():
    cert = _cert(
        not_before="Jan  1 00:00:00 2025 GMT",
        not_after="Apr  1 00:00:00 2025 GMT",
    )
    assert _cert_validity_days(cert) == 90


def test_validity_days_missing_dates_imputed():
    assert _cert_validity_days(_cert()) == IMPUTED_DEFAULTS["cert_validity_days"]


def test_validity_days_malformed_imputed():
    cert = _cert(not_before="not-a-date", not_after="also-bad")
    assert _cert_validity_days(cert) == IMPUTED_DEFAULTS["cert_validity_days"]


def test_san_count():
    san = (("DNS", "example.com"), ("DNS", "www.example.com"))
    assert _cert_san_count(_cert(san=san)) == 2


def test_san_count_absent_imputed():
    assert _cert_san_count(_cert()) == IMPUTED_DEFAULTS["cert_san_count"]
