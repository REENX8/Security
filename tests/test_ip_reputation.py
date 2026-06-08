"""Tests for the IP/ASN reputation layer (B8, Stage 1).

All deterministic and offline: the default ASN provider is the no-op
NullAsnProvider, and host resolution is exercised only with IP literals so no
DNS is performed.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add backend to sys.path so app.* is importable without conftest.
_BACKEND = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("API_KEY", "test-key")

from app.database import Base  # noqa: E402
from app.integrations.asn import (  # noqa: E402
    AsnInfo,
    CymruDnsAsnProvider,
    NullAsnProvider,
    get_asn_provider,
)
from app.ip_reputation import (  # noqa: E402
    _bad_share,
    _resolve_public_ip,
    reputation_feature_scores,
    resolve_ip_asn,
)
from app.ip_reputation_store import record_ip_verdict  # noqa: E402
from app.models import AsnReputation, IpReputation  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return engine, maker


# --- provider ---------------------------------------------------------------

def test_null_provider_returns_none():
    assert NullAsnProvider().lookup("8.8.8.8") is None


def test_get_asn_provider_defaults_to_null():
    assert isinstance(get_asn_provider("null"), NullAsnProvider)
    assert isinstance(get_asn_provider("unknown-name"), NullAsnProvider)


def test_get_asn_provider_cymru_opt_in():
    assert isinstance(get_asn_provider("cymru"), CymruDnsAsnProvider)


def test_cymru_rejects_non_ipv4_without_network():
    p = CymruDnsAsnProvider()
    assert p.lookup("not-an-ip") is None
    assert p.lookup("2001:4860:4860::8888") is None


# --- resolution (IP literals only -> no DNS) --------------------------------

def test_resolve_public_ip_literal_public():
    assert _resolve_public_ip("8.8.8.8") == "8.8.8.8"


def test_resolve_public_ip_rejects_private():
    assert _resolve_public_ip("127.0.0.1") is None
    assert _resolve_public_ip("10.0.0.5") is None
    assert _resolve_public_ip("169.254.169.254") is None


def test_resolve_ip_asn_with_null_provider():
    rep = resolve_ip_asn("http://8.8.8.8/login", NullAsnProvider())
    assert rep == {"ip": "8.8.8.8", "asn": None, "as_name": ""}


def test_resolve_ip_asn_unsafe_host_returns_none():
    assert resolve_ip_asn("http://127.0.0.1/x", NullAsnProvider()) is None


def test_resolve_ip_asn_uses_provider_asn():
    class _P:
        name = "fake"

        def lookup(self, ip):
            return AsnInfo(asn=64500, as_name="EVIL-AS")

    rep = resolve_ip_asn("http://8.8.8.8/x", _P())
    assert rep == {"ip": "8.8.8.8", "asn": 64500, "as_name": "EVIL-AS"}


# --- bad-share feature value ------------------------------------------------

def test_bad_share_below_min_observations_is_unknown():
    row = IpReputation(ip="1.2.3.4", total_count=3, phishing_count=3)
    assert _bad_share(row) == -1.0


def test_bad_share_none_is_unknown():
    assert _bad_share(None) == -1.0


def test_bad_share_dirty_range_is_high():
    row = IpReputation(ip="1.2.3.4", total_count=10, phishing_count=10,
                       suspicious_count=0)
    assert _bad_share(row) == pytest.approx(1.0)


def test_bad_share_clean_range_is_zero():
    row = IpReputation(ip="1.2.3.4", total_count=10, phishing_count=0,
                       suspicious_count=0)
    assert _bad_share(row) == 0.0


def test_bad_share_weights_suspicious_half():
    row = IpReputation(ip="1.2.3.4", total_count=10, phishing_count=2,
                       suspicious_count=4)
    assert _bad_share(row) == pytest.approx(0.4)


# --- store upsert -----------------------------------------------------------

def test_record_ip_verdict_upserts_and_counts():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await record_ip_verdict(session, ip="203.0.113.7", asn=64500,
                                    as_name="AS-X", label="phishing", score=0.95)
            await record_ip_verdict(session, ip="203.0.113.7", asn=64500,
                                    as_name="AS-X", label="suspicious", score=0.5)

            ip_row = (
                await session.execute(
                    select(IpReputation).where(IpReputation.ip == "203.0.113.7")
                )
            ).scalar_one()
            assert ip_row.total_count == 2
            assert ip_row.phishing_count == 1
            assert ip_row.suspicious_count == 1
            assert ip_row.asn == 64500

            asn_row = (
                await session.execute(
                    select(AsnReputation).where(AsnReputation.asn == 64500)
                )
            ).scalar_one()
            assert asn_row.total_count == 2
            assert asn_row.as_name == "AS-X"
        await engine.dispose()
    asyncio.run(_run())


def test_record_ip_verdict_without_asn():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            await record_ip_verdict(session, ip="203.0.113.8", asn=None,
                                    label="safe", score=0.1)
            ip_row = (
                await session.execute(
                    select(IpReputation).where(IpReputation.ip == "203.0.113.8")
                )
            ).scalar_one()
            assert ip_row.total_count == 1
            assert ip_row.phishing_count == 0
            assert (await session.execute(select(AsnReputation))).first() is None
        await engine.dispose()
    asyncio.run(_run())


# --- feature scores end-to-end ----------------------------------------------

def test_feature_scores_unknown_for_new_ip():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            rep = {"ip": "198.51.100.1", "asn": None, "as_name": ""}
            scores = await reputation_feature_scores(rep, session=session)
            assert scores == {"ip_reputation_score": -1.0, "asn_reputation_score": -1.0}
        await engine.dispose()
    asyncio.run(_run())


def test_feature_scores_unknown_for_empty_rep():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            assert await reputation_feature_scores(None, session=session) == {
                "ip_reputation_score": -1.0, "asn_reputation_score": -1.0
            }
            assert await reputation_feature_scores({}, session=session) == {
                "ip_reputation_score": -1.0, "asn_reputation_score": -1.0
            }
        await engine.dispose()
    asyncio.run(_run())


def test_feature_scores_high_for_dirty_ip():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            for _ in range(8):
                await record_ip_verdict(session, ip="198.51.100.9", asn=64500,
                                        label="phishing", score=0.95)
            rep = {"ip": "198.51.100.9", "asn": 64500, "as_name": ""}
            scores = await reputation_feature_scores(rep, session=session)
            assert scores["ip_reputation_score"] == pytest.approx(1.0)
            assert scores["asn_reputation_score"] == pytest.approx(1.0)
        await engine.dispose()
    asyncio.run(_run())


def test_resolve_public_ip_hostname_resolves():
    # Passing a hostname that isn't an IP literal exercises getaddrinfo path.
    # We use "localhost" which resolves to 127.0.0.1 — a blocked private addr.
    from app.ip_reputation import _resolve_public_ip
    result = _resolve_public_ip("localhost")
    assert result is None  # loopback is blocked


def test_resolve_public_ip_getaddrinfo_failure():
    from unittest.mock import patch

    from app.ip_reputation import _resolve_public_ip
    with patch("socket.getaddrinfo", side_effect=OSError("no route")):
        # The function first tries inet_aton (fails on hostname), then getaddrinfo
        result = _resolve_public_ip("unresolvable.internal")
    assert result is None


def test_asn_provider_exception_is_swallowed():
    class _BadProvider:
        name = "bad"
        def lookup(self, ip):
            raise RuntimeError("provider exploded")

    from app.ip_reputation import resolve_ip_asn
    rep = resolve_ip_asn("http://8.8.8.8/login", _BadProvider())
    # Exception must not propagate; asn/as_name fall back to defaults
    assert rep is not None
    assert rep["asn"] is None
    assert rep["as_name"] == ""


def test_resolve_public_ip_via_getaddrinfo():
    from unittest.mock import patch

    from app.ip_reputation import _resolve_public_ip
    # Mock host_is_safe=True so the host passes the guard, then make inet_aton
    # fail (it's a hostname, not a literal), and getaddrinfo returns a public IP.
    with patch("app.ip_reputation.host_is_safe", return_value=True), \
         patch("socket.inet_aton", side_effect=OSError("not a literal")), \
         patch("socket.getaddrinfo",
               return_value=[(None, None, None, None, ("8.8.8.8", 0))]):
        result = _resolve_public_ip("dns-hostname.example")
    assert result == "8.8.8.8"


def test_resolve_public_ip_all_resolved_ips_blocked():
    from unittest.mock import patch

    from app.ip_reputation import _resolve_public_ip
    # All getaddrinfo results are private IPs → function returns None (line 56)
    with patch("app.ip_reputation.host_is_safe", return_value=True), \
         patch("socket.inet_aton", side_effect=OSError("not a literal")), \
         patch("socket.getaddrinfo",
               return_value=[(None, None, None, None, ("10.0.0.1", 0))]):
        result = _resolve_public_ip("internal-host.example")
    assert result is None


def test_record_ip_verdict_empty_ip_returns_early():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            # Empty IP — must return immediately without raising or writing.
            await record_ip_verdict(session, ip="", asn=64500,
                                    label="phishing", score=0.9)
            assert (await session.execute(select(IpReputation))).first() is None
        await engine.dispose()
    asyncio.run(_run())


def test_record_ip_verdict_updates_asn_name_when_previously_empty():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            # First call: asn_row created with empty as_name
            await record_ip_verdict(session, ip="203.0.113.10", asn=64501,
                                    as_name="", label="safe", score=0.1)
            # Second call: as_name now provided — should update asn_row
            await record_ip_verdict(session, ip="203.0.113.10", asn=64501,
                                    as_name="NEW-AS", label="safe", score=0.1)
            asn_row = (
                await session.execute(
                    select(AsnReputation).where(AsnReputation.asn == 64501)
                )
            ).scalar_one()
            assert asn_row.as_name == "NEW-AS"
        await engine.dispose()
    asyncio.run(_run())


def test_record_ip_verdict_existing_ip_null_asn():
    async def _run():
        engine, maker = await _make_session()
        async with maker() as session:
            # First call: create ip_row with asn
            await record_ip_verdict(session, ip="203.0.113.11", asn=64502,
                                    as_name="AS-Y", label="safe", score=0.1)
            # Second call: asn=None — must not overwrite the existing asn
            await record_ip_verdict(session, ip="203.0.113.11", asn=None,
                                    label="phishing", score=0.9)
            ip_row = (
                await session.execute(
                    select(IpReputation).where(IpReputation.ip == "203.0.113.11")
                )
            ).scalar_one()
            assert ip_row.total_count == 2
            assert ip_row.asn == 64502  # original asn preserved
        await engine.dispose()
    asyncio.run(_run())
