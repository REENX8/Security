"""Unit tests for _probe_valid and _probe_unverified in phish_features.tls.

Both functions are network-bound; they are exercised here by mocking
socket.create_connection and ssl context wrapping so no real TCP is needed.
"""
from __future__ import annotations

import ssl
from unittest.mock import MagicMock, patch

from phish_features.tls import _probe_unverified, _probe_valid


def _make_sock_mock():
    """Return a mock socket/ssock that behaves as a context manager."""
    sock = MagicMock()
    sock.__enter__ = lambda s: s
    sock.__exit__ = MagicMock(return_value=False)
    return sock


class TestProbeValid:
    def _mock_cert(self, with_not_before=True):
        cert = {
            "issuer": ((("organizationName", "Let's Encrypt"),),),
            "subjectAltName": [("DNS", "example.com")],
            "notBefore": "Jan  1 00:00:00 2024 GMT",
            "notAfter":  "Apr  1 00:00:00 2024 GMT",
        }
        if not with_not_before:
            del cert["notBefore"]
        return cert

    def test_valid_cert_returns_tls_ok(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        ssock.getpeercert.return_value = self._mock_cert()

        with patch("socket.create_connection", return_value=sock), \
             patch.object(ssl.SSLContext, "wrap_socket", return_value=ssock):
            result = _probe_valid("example.com", 443)

        assert result["tls_ok"] == 1
        assert result["has_valid_cert"] == 1
        assert result["is_self_signed"] == 0
        assert result["cert_is_lets_encrypt"] == 1

    def test_valid_cert_without_notbefore_uses_imputed_age(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        ssock.getpeercert.return_value = self._mock_cert(with_not_before=False)

        with patch("socket.create_connection", return_value=sock), \
             patch.object(ssl.SSLContext, "wrap_socket", return_value=ssock):
            result = _probe_valid("example.com", 443)

        assert result["tls_ok"] == 1
        # cert_age_days falls back to imputed default when notBefore absent
        from phish_features.schema import IMPUTED_DEFAULTS
        assert result["cert_age_days"] == IMPUTED_DEFAULTS["cert_age_days"]

    def test_valid_cert_bad_notbefore_uses_imputed_age(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        cert = {
            "issuer": (),
            "notBefore": "not-a-real-date",
            "notAfter": "Apr  1 00:00:00 2024 GMT",
        }
        ssock.getpeercert.return_value = cert

        with patch("socket.create_connection", return_value=sock), \
             patch.object(ssl.SSLContext, "wrap_socket", return_value=ssock):
            result = _probe_valid("example.com", 443)

        from phish_features.schema import IMPUTED_DEFAULTS
        assert result["cert_age_days"] == IMPUTED_DEFAULTS["cert_age_days"]

    def test_valid_cert_empty_cert_dict(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        ssock.getpeercert.return_value = None  # getpeercert() or {} → {}

        with patch("socket.create_connection", return_value=sock), \
             patch.object(ssl.SSLContext, "wrap_socket", return_value=ssock):
            result = _probe_valid("example.com", 443)

        assert result["tls_ok"] == 1


class TestProbeUnverified:
    def test_cert_presented_is_self_signed(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        ssock.getpeercert.return_value = b"\xde\xad\xbe\xef"  # binary DER data

        ctx_mock = MagicMock()
        ctx_mock.wrap_socket.return_value = ssock

        with patch("socket.create_connection", return_value=sock), \
             patch("ssl._create_unverified_context", return_value=ctx_mock):
            result = _probe_unverified("self-signed.example", 443)

        assert result["tls_ok"] == 1
        assert result["is_self_signed"] == 1
        assert result["has_valid_cert"] == 0

    def test_no_cert_returned_is_not_self_signed(self):
        sock = _make_sock_mock()
        ssock = _make_sock_mock()
        ssock.getpeercert.return_value = b""  # empty → falsy

        ctx_mock = MagicMock()
        ctx_mock.wrap_socket.return_value = ssock

        with patch("socket.create_connection", return_value=sock), \
             patch("ssl._create_unverified_context", return_value=ctx_mock):
            result = _probe_unverified("no-cert.example", 443)

        assert result["tls_ok"] == 1
        assert result["is_self_signed"] == 0

    def test_connection_error_returns_imputed(self):
        ctx_mock = MagicMock()
        ctx_mock.wrap_socket.side_effect = OSError("connection refused")

        with patch("socket.create_connection", return_value=_make_sock_mock()), \
             patch("ssl._create_unverified_context", return_value=ctx_mock):
            result = _probe_unverified("refused.example", 443)

        assert result["tls_ok"] == 0
