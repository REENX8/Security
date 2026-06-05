"""ASN lookup providers (B8).

Resolving a host's IP to an Autonomous System Number (ASN) lets the IP/ASN
reputation store accumulate verdict history per hosting range, so a known-bad
range can raise a brand-new URL's score even on first sighting.

Like the SMS (`integrations/sms.py`) and government (`integrations/government.py`)
connectors, this is a **pluggable provider with a no-op default**:

* ``NullAsnProvider`` (default) returns ``None`` for every lookup — no network,
  fully deterministic. This is what CI and the zero-setup demo use.
* ``CymruDnsAsnProvider`` (opt-in, ``ASN_PROVIDER=cymru``) resolves the ASN via
  Team Cymru's IP-to-ASN DNS service (``origin.asn.cymru.com``). No API key and
  no large committed IP→ASN database — a single DNS TXT lookup per IP.

A committed offline IP→ASN table is intentionally NOT shipped: a useful one is
tens of MB and licensing-encumbered, which is impractical to vendor into the
repo. Operators who want offline lookups can implement the same protocol over a
local MaxMind/pyasn database and register it here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("phish-detector")


@dataclass(frozen=True)
class AsnInfo:
    asn: int
    as_name: str = ""


class AsnProvider(Protocol):
    """Resolve an IPv4/IPv6 address to its ASN."""

    name: str

    def lookup(self, ip: str) -> AsnInfo | None: ...


@dataclass
class NullAsnProvider:
    """No-op provider: every lookup returns ``None`` (ASN unknown).

    The default. IP-level reputation still works (keyed on the IP); only the
    ASN-level aggregation is unavailable without a real provider.
    """

    name: str = "null"

    def lookup(self, ip: str) -> AsnInfo | None:  # noqa: ARG002
        return None


@dataclass
class CymruDnsAsnProvider:
    """Resolve ASN via Team Cymru's IP-to-ASN DNS service (opt-in).

    For an IPv4 ``a.b.c.d`` it queries the TXT record of
    ``d.c.b.a.origin.asn.cymru.com``; the first field of the answer is the ASN.
    Best-effort and fail-soft: any resolution/parse error returns ``None`` so a
    lookup failure never throws into the caller.
    """

    name: str = "cymru"
    timeout: float = 2.0

    def lookup(self, ip: str) -> AsnInfo | None:
        try:
            import ipaddress

            addr = ipaddress.ip_address(ip)
        except ValueError:
            return None
        # IPv6 support would need nibble-reversed origin6.asn.cymru.com; keep
        # the opt-in provider to IPv4, which covers the vast majority of hosts.
        if addr.version != 4:
            return None
        try:
            import dns.resolver  # type: ignore
        except Exception:  # noqa: BLE001 - optional dependency
            logger.debug("cymru asn lookup needs dnspython; returning None")
            return None
        reversed_ip = ".".join(reversed(ip.split(".")))
        qname = f"{reversed_ip}.origin.asn.cymru.com"
        try:
            resolver = dns.resolver.Resolver()
            resolver.lifetime = self.timeout
            answer = resolver.resolve(qname, "TXT")
            txt = str(answer[0]).strip('"')
            # Format: "<ASN> | <prefix> | <CC> | <registry> | <date>"
            asn_field = txt.split("|")[0].strip().split()[0]
            return AsnInfo(asn=int(asn_field))
        except Exception as exc:  # noqa: BLE001
            logger.debug("cymru asn lookup failed for %s: %s", ip, exc)
            return None


# "null" is a singleton; "cymru" is built on demand from settings.
_PROVIDERS: dict[str, AsnProvider] = {"null": NullAsnProvider()}


def get_asn_provider(name: str, settings=None) -> AsnProvider:
    """Return the configured ASN provider, falling back to the null provider."""
    if name == "cymru":
        timeout = getattr(settings, "ip_reputation_timeout", 2.0) if settings else 2.0
        return CymruDnsAsnProvider(timeout=timeout)
    return _PROVIDERS.get(name, _PROVIDERS["null"])
