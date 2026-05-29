"""TLS certificate features.

Like WHOIS, the TLS probe is network-bound and run with a hard timeout.
On failure the imputed defaults are returned and ``tls_ok`` is set to 0.
"""

from __future__ import annotations

import datetime as _dt
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeout

from .schema import IMPUTED_DEFAULTS

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tls")
_CERT_DATE_FMT = "%b %d %H:%M:%S %Y %Z"

# Lower-cased substrings that identify a free / automated DV certificate
# authority. These over-index heavily on phishing (free + instant issuance):
# Let's Encrypt issues short-lived 90-day certs via its R-/E-series
# intermediates; ZeroSSL, Google Trust Services and Buypass Go are the other
# common free issuers seen on phishing kits.
_FREE_CA_MARKERS: tuple[str, ...] = (
    "let's encrypt", "lets encrypt", "zerossl", "google trust services",
    "gts ca", "buypass go", "actalis free", "ssl.com dv",
    # Let's Encrypt intermediates appear as the issuer commonName:
    "=r3", "=r10", "=r11", "=r12", "=r13", "=r14",
    "=e1", "=e5", "=e6", "=e7", "=e8", "=e9",
)


def _imputed() -> dict:
    return {
        "has_valid_cert": IMPUTED_DEFAULTS["has_valid_cert"],
        "cert_age_days": IMPUTED_DEFAULTS["cert_age_days"],
        "is_self_signed": IMPUTED_DEFAULTS["is_self_signed"],
        "tls_ok": 0,
        "cert_is_lets_encrypt": IMPUTED_DEFAULTS["cert_is_lets_encrypt"],
        "cert_validity_days": IMPUTED_DEFAULTS["cert_validity_days"],
        "cert_san_count": IMPUTED_DEFAULTS["cert_san_count"],
    }


def _issuer_is_free_ca(cert: dict) -> int:
    """1 if the leaf cert's issuer is a free/automated DV CA.

    ``cert['issuer']`` is a tuple of RDN sequences, e.g.
    ``((('countryName', 'US'),), (('organizationName', "Let's Encrypt"),),
       (('commonName', 'R3'),))``. We flatten it to a single lowered string
    of ``key=value`` pairs and look for known free-CA markers.
    """
    issuer = cert.get("issuer") or ()
    parts: list[str] = []
    for rdn in issuer:
        for key, value in rdn:
            parts.append(f"{key}={value}".lower())
    blob = " ".join(parts)
    return int(any(marker in blob for marker in _FREE_CA_MARKERS))


def _cert_validity_days(cert: dict) -> int:
    """notAfter - notBefore in whole days, or the imputed default if unknown."""
    not_before = cert.get("notBefore")
    not_after = cert.get("notAfter")
    if not (not_before and not_after):
        return IMPUTED_DEFAULTS["cert_validity_days"]
    try:
        start = _dt.datetime.strptime(not_before, _CERT_DATE_FMT)
        end = _dt.datetime.strptime(not_after, _CERT_DATE_FMT)
    except ValueError:
        return IMPUTED_DEFAULTS["cert_validity_days"]
    return max((end - start).days, 0)


def _cert_san_count(cert: dict) -> int:
    """Number of subjectAltName entries, or the imputed default if absent."""
    san = cert.get("subjectAltName")
    if not san:
        return IMPUTED_DEFAULTS["cert_san_count"]
    try:
        return len(san)
    except TypeError:
        return IMPUTED_DEFAULTS["cert_san_count"]


def _probe_valid(host: str, port: int) -> dict:
    """Probe with full verification -- a clean handshake means a valid cert."""
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=3) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert() or {}
    age_days = IMPUTED_DEFAULTS["cert_age_days"]
    not_before = cert.get("notBefore")
    if not_before:
        try:
            issued = _dt.datetime.strptime(not_before, _CERT_DATE_FMT)
            age_days = max((_dt.datetime.utcnow() - issued).days, 0)
        except ValueError:
            pass
    return {
        "has_valid_cert": 1,
        "cert_age_days": int(age_days),
        "is_self_signed": 0,
        "tls_ok": 1,
        "cert_is_lets_encrypt": _issuer_is_free_ca(cert),
        "cert_validity_days": _cert_validity_days(cert),
        "cert_san_count": _cert_san_count(cert),
    }


def _probe_unverified(host: str, port: int) -> dict:
    """Verification already failed; check whether a cert is presented at all
    and whether it is self-signed."""
    ctx = ssl._create_unverified_context()  # noqa: SLF001 - intentional
    try:
        with socket.create_connection((host, port), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert(binary_form=True)
        # A cert was presented but verification failed: treat as self-signed
        # / untrusted.
        # Verification failed, so the cert was fetched in binary (DER) form and
        # its issuer / validity / SAN are not parsed here -- leave them imputed.
        return {
            "has_valid_cert": 0,
            "cert_age_days": IMPUTED_DEFAULTS["cert_age_days"],
            "is_self_signed": 1 if cert else 0,
            "tls_ok": 1,
            "cert_is_lets_encrypt": IMPUTED_DEFAULTS["cert_is_lets_encrypt"],
            "cert_validity_days": IMPUTED_DEFAULTS["cert_validity_days"],
            "cert_san_count": IMPUTED_DEFAULTS["cert_san_count"],
        }
    except Exception:  # noqa: BLE001
        return _imputed()


def _raw_tls(host: str, port: int) -> dict:
    try:
        return _probe_valid(host, port)
    except ssl.SSLCertVerificationError:
        return _probe_unverified(host, port)
    except Exception:  # noqa: BLE001 - no TLS at all
        return _imputed()


def tls_features(host: str, port: int = 443, timeout: float = 3.0) -> dict:
    """Return TLS features for ``host`` with a hard timeout + safe fallback."""
    if not host:
        return _imputed()
    future = _EXECUTOR.submit(_raw_tls, host, port)
    try:
        return future.result(timeout=timeout)
    except (_FutureTimeout, Exception):  # noqa: BLE001
        future.cancel()
        return _imputed()
