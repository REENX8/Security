"""WHOIS-derived domain features.

WHOIS lookups are slow and unreliable; ``python-whois`` also ignores socket
timeouts on some code paths. Every lookup is therefore run inside a worker
thread with a hard deadline. On ANY failure the imputed defaults from
``schema.py`` are returned and ``whois_ok`` is set to 0 -- the model is
trained to treat that as "unknown".
"""

from __future__ import annotations

import datetime as _dt
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeout

from .schema import IMPUTED_DEFAULTS, KNOWN_THAI_REGISTRARS

try:  # python-whois is optional
    import whois as _whois  # type: ignore

    _HAVE_WHOIS = True
except Exception:  # pragma: no cover
    _HAVE_WHOIS = False

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="whois")


def _imputed() -> dict:
    return {
        "domain_age_days": IMPUTED_DEFAULTS["domain_age_days"],
        "is_known_registrar": IMPUTED_DEFAULTS["is_known_registrar"],
        "whois_ok": 0,
    }


def _coerce_date(value) -> _dt.datetime | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, _dt.date):
        return _dt.datetime(value.year, value.month, value.day)
    return None


def _raw_whois(host: str) -> dict:
    """Blocking WHOIS call -- always invoked inside a worker thread."""
    record = _whois.whois(host)
    created = _coerce_date(record.get("creation_date"))
    age_days = IMPUTED_DEFAULTS["domain_age_days"]
    if created is not None:
        age_days = max((_dt.datetime.now() - created).days, 0)

    registrar = (record.get("registrar") or "")
    if isinstance(registrar, list):
        registrar = registrar[0] if registrar else ""
    registrar = str(registrar).lower()
    known = any(name in registrar for name in KNOWN_THAI_REGISTRARS)

    return {
        "domain_age_days": int(age_days),
        "is_known_registrar": int(known),
        "whois_ok": 1,
    }


def whois_features(host: str, timeout: float = 2.5) -> dict:
    """Return WHOIS features for ``host`` with a hard timeout + safe fallback."""
    if not host or not _HAVE_WHOIS:
        return _imputed()
    future = _EXECUTOR.submit(_raw_whois, host)
    try:
        return future.result(timeout=timeout)
    except (_FutureTimeout, Exception):  # noqa: BLE001 - degrade gracefully
        future.cancel()
        return _imputed()
