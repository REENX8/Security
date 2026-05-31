"""STIX 2.1 indicator helpers shared by the /feed.stix export and the TAXII server.

Keeping a single source of truth means the one-shot STIX bundle and the TAXII
2.1 collection emit byte-identical indicator objects, and the indicator id is
deterministic (derived from the UrlCheck row id) so a TAXII consumer can dedupe
across polls and the manifest lines up with the objects.
"""

from __future__ import annotations

import uuid

from app.models import UrlCheck

# Stable namespace for deriving deterministic indicator UUIDs from row ids.
_INDICATOR_NS = uuid.UUID("9f1b6e2a-5c2d-4a8e-9b7f-2e1c0a4d6b81")

# STIX pattern values must escape backslashes and single quotes.
def _escape_pattern_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _iso_z(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def indicator_id_for(row: UrlCheck) -> str:
    return f"indicator--{uuid.uuid5(_INDICATOR_NS, str(row.id))}"


def build_indicator(row: UrlCheck) -> dict:
    """Return a STIX 2.1 ``indicator`` SDO for one phishing UrlCheck row."""
    created = _iso_z(row.checked_at)
    return {
        "type": "indicator",
        "spec_version": "2.1",
        "id": indicator_id_for(row),
        "created": created,
        "modified": created,
        "name": f"Phishing URL targeting {row.closest_domain or 'unknown'}",
        "indicator_types": ["malicious-activity"],
        "pattern_type": "stix",
        "pattern": f"[url:value = '{_escape_pattern_value(row.url)}']",
        "valid_from": created,
        "confidence": int(round(float(row.score) * 100)),
    }
