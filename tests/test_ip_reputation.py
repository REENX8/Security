"""Tests for the IP/ASN reputation layer (B8, Stage 1).

All deterministic and offline: the default ASN provider is the no-op
NullAsnProvider, and host resolution is exercised only with IP literals so no
DNS is performed.
"""

from __future__ import annotations

import pytest
from app.database import Base
from app.integrations.asn import (
    AsnInfo,
    CymruDnsAsnProvider,
    NullAsnProvider,
    get_asn_provider,
)
from app.ip_reputation import (
    _rep_bump,
    _resolve_public_ip,
    reputation_adjustment,
    resolve_ip_asn,
)
from app.ip_reputation_store import record_ip_verdict
from app.models import AsnReputation, IpReputation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


# --- provider ---------------------------------------------------------------

def test_null_provider_returns_none():
    assert NullAsnProvider().lookup("8.8.8.8") is None


def test_get_asn_provider_defaults_to_null():
    assert isinstance(get_asn_provider("null"), NullAsnProvider)
    assert isinstance(get_asn_provider("unknown-name"), NullAsnProvider)


def test_get_asn_provider_cymru_opt_in():
    assert isinstance(get_asn_provider("cymru"), CymruDnsAsnProvider)


def test_cymru_rejects_non_ipv4_without_network():
    # IPv6 / garbage return None without any DNS work.
    p = CymruDnsAsnProvider()
    assert p.lookup("not-an-ip") is None
    assert p.lookup("2001:4860:4860::8888") is None


# --- resolution (IP literals only -> no DNS) --------------------------------

def test_resolve_public_ip_literal_public():
    assert _resolve_public_ip("8.8.8.8") == "8.8.8.8"


def test_resolve_public_ip_rejects_private():
    assert _resolve_public_ip("127.0.0.1") is None
    assert _resolve_public_ip("10.0.0.5") is None
    assert _resolve_public_ip("169.254.169.254") is None  # cloud metadata


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


# --- bump math --------------------------------------------------------------

def test_rep_bump_below_min_observations_is_zero():
    row = IpReputation(ip="1.2.3.4", total_count=3, phishing_count=3)
    assert _rep_bump(row) == 0.0


def test_rep_bump_dirty_range_is_positive_and_bounded():
    row = IpReputation(ip="1.2.3.4", total_count=10, phishing_count=10)
    bump = _rep_bump(row)
    assert 0.0 < bump <= 0.30


def test_rep_bump_clean_range_is_small_negative():
    row = IpReputation(ip="1.2.3.4", total_count=10, phishing_count=0,
                       suspicious_count=0)
    assert _rep_bump(row) == pytest.approx(-0.10)


# --- store upsert -----------------------------------------------------------

async def test_record_ip_verdict_upserts_and_counts(session):
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


async def test_record_ip_verdict_without_asn(session):
    await record_ip_verdict(session, ip="203.0.113.8", asn=None,
                            label="safe", score=0.1)
    ip_row = (
        await session.execute(
            select(IpReputation).where(IpReputation.ip == "203.0.113.8")
        )
    ).scalar_one()
    assert ip_row.total_count == 1
    assert ip_row.phishing_count == 0
    # No ASN row created when asn is unknown.
    assert (await session.execute(select(AsnReputation))).first() is None


# --- adjustment end-to-end --------------------------------------------------

async def test_adjustment_zero_for_unknown_ip(session):
    rep = {"ip": "198.51.100.1", "asn": None, "as_name": ""}
    assert await reputation_adjustment(rep, session=session) == 0.0


async def test_adjustment_zero_for_empty_rep(session):
    assert await reputation_adjustment(None, session=session) == 0.0
    assert await reputation_adjustment({}, session=session) == 0.0


async def test_adjustment_positive_for_dirty_ip(session):
    for _ in range(8):
        await record_ip_verdict(session, ip="198.51.100.9", asn=None,
                                label="phishing", score=0.95)
    rep = {"ip": "198.51.100.9", "asn": None, "as_name": ""}
    adj = await reputation_adjustment(rep, session=session)
    assert 0.0 < adj <= 0.30
