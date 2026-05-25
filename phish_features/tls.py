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


def _imputed() -> dict:
    return {
        "has_valid_cert": IMPUTED_DEFAULTS["has_valid_cert"],
        "cert_age_days": IMPUTED_DEFAULTS["cert_age_days"],
        "is_self_signed": IMPUTED_DEFAULTS["is_self_signed"],
        "tls_ok": 0,
    }


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
        return {
            "has_valid_cert": 0,
            "cert_age_days": IMPUTED_DEFAULTS["cert_age_days"],
            "is_self_signed": 1 if cert else 0,
            "tls_ok": 1,
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
