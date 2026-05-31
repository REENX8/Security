"""Government integration connectors (B3).

Pluggable connectors to forward confirmed phishing reports to, and pull
blocklists from, Thai authorities — ETDA's 1212 Online and the Cyber Crime
Investigation Bureau's 1441. Real connectors implement :class:`GovernmentConnector`
against each agency's API/intake; the stub keeps the wiring testable and is the
default until credentials/endpoints are provisioned.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger("phish-detector")


@dataclass
class GovReport:
    url: str
    score: float
    closest_domain: str | None = None
    reason: str = ""


class GovernmentConnector(Protocol):
    """Forward reports to, and pull a blocklist from, a government service."""

    name: str

    def forward_report(self, report: GovReport) -> bool: ...

    def fetch_blocklist(self) -> list[str]: ...


@dataclass
class StubGovernmentConnector:
    """No-op connector: logs forwards and returns an empty blocklist.

    Swap for a real ETDA/police connector by implementing the same methods.
    """

    name: str = "stub"
    forwarded: list[GovReport] = field(default_factory=list)

    def forward_report(self, report: GovReport) -> bool:
        self.forwarded.append(report)
        logger.info("gov[%s]: would forward report for %s", self.name, report.url)
        return True

    def fetch_blocklist(self) -> list[str]:
        logger.info("gov[%s]: fetch_blocklist (stub -> [])", self.name)
        return []


# Registry of available connectors. Real connectors register here; selection is
# by name via configuration (GOV_CONNECTOR).
_CONNECTORS: dict[str, GovernmentConnector] = {
    "stub": StubGovernmentConnector(),
}


def get_connector(name: str) -> GovernmentConnector:
    """Return the configured connector, falling back to the stub."""
    return _CONNECTORS.get(name, _CONNECTORS["stub"])
