"""Whitelist + typosquat detection tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from phish_features.whitelist import (
    TYPOSQUAT_MAX_DISTANCE,
    Whitelist,
    WhitelistEntry,
    brand_label,
    registrable_domain,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def wl() -> Whitelist:
    return Whitelist.from_json(str(ROOT / "models" / "whitelist.json"))


@pytest.mark.parametrize("host,expected", [
    ("www.obec.go.th", "obec.go.th"),
    ("a.b.c.obec.go.th", "obec.go.th"),
    ("chula.ac.th", "chula.ac.th"),
    ("mail.chula.ac.th", "chula.ac.th"),
    ("www.example.com", "example.com"),
    ("example.com", "example.com"),
    ("", ""),
])
def test_registrable_domain(host, expected):
    assert registrable_domain(host) == expected


@pytest.mark.parametrize("host,expected", [
    ("www.obec.go.th", "obec"),
    ("chula.ac.th", "chula"),
    ("mail.scb.co.th", "scb"),
    ("google.com", "google"),
    ("", ""),
])
def test_brand_label(host, expected):
    assert brand_label(host) == expected


def test_whitelist_loads_real_artifact(wl):
    assert len(wl.entries) >= 100
    assert "obec.go.th" in wl.domains
    assert "chula.ac.th" in wl.domains


def test_whitelist_exact_match(wl):
    feat = wl.whitelist_features("www.obec.go.th")
    assert feat["min_edit_distance"] == 0
    assert feat["is_typosquat"] == 0
    assert feat["closest_domain"] == "obec.go.th"


def test_whitelist_tld_swap_is_typosquat(wl):
    # obec.com is a perfect-label TLD swap of obec.go.th -> typosquat
    feat = wl.whitelist_features("obec.com")
    assert feat["min_edit_distance"] == 0
    assert feat["is_typosquat"] == 1
    assert feat["closest_domain"] == "obec.go.th"


def test_whitelist_classic_typosquat(wl):
    # one-character mutation
    feat = wl.whitelist_features("0bec.xyz")
    assert feat["min_edit_distance"] == 1
    assert feat["is_typosquat"] == 1


def test_whitelist_far_domain_not_typosquat(wl):
    feat = wl.whitelist_features("www.google.com")
    assert feat["min_edit_distance"] > TYPOSQUAT_MAX_DISTANCE
    assert feat["is_typosquat"] == 0


def test_whitelist_short_label_not_typosquat(wl):
    # "scb" is 3 chars and coincidentally near a whitelist short label, but
    # the 4-char minimum suppresses the false positive.
    feat = wl.whitelist_features("scb.co.th")
    assert feat["is_typosquat"] == 0


def test_closest_normalized_collapses_cyrillic_lookalike(wl):
    """The normalized closest call must fold Cyrillic а back to ASCII a
    so a homoglyph spoof of ``chula`` registers distance 0."""
    dist, dom = wl.closest_normalized("chulа.com")  # Cyrillic а
    assert dist == 0
    assert dom == "chula.ac.th"


def test_closest_normalized_passthrough_for_ascii(wl):
    dist, dom = wl.closest_normalized("obec.go.th")
    assert dist == 0
    assert dom == "obec.go.th"


@pytest.mark.parametrize("host", [
    "amazon.com",     # "amazon" is 3 edits from "amlo" (amlo.go.th) — proportional 3/4 = 0.75 > 0.5
    "twitter.com",    # "twitter" is 3 edits from "tistr" (tistr.or.th) — proportional 3/5 = 0.6 > 0.5
    "yahoo.com",      # "yahoo" is 3 edits from "ago" (ago.go.th) — closest brand too short
    "bing.com",       # "bing" is 3 edits from "ais" (ais.co.th) — closest brand too short
    "reddit.com",     # "reddit" is 3 edits from "audit" (audit.go.th) — proportional 3/5 = 0.6
    "apple.com",      # "apple" is 3 edits from "amlo" (amlo.go.th) — proportional 3/4 = 0.75
    "twitch.tv",      # "twitch" is 3 edits from "ptwit" (ptwit.ac.th) — proportional 3/5 = 0.6
    "zoom.us",        # "zoom" is 2 edits from "opm" (opm.go.th) — closest brand too short
    "slack.com",      # "slack" is 2 edits from "slc" (slc.ac.th) — closest brand too short
    "grab.com",       # "grab" is 2 edits from "dra" (dra.go.th) — closest brand too short
    "ebay.com",       # "ebay" is 2 edits from "eau" (eau.ac.th) — closest brand too short
])
def test_proportional_distance_prevents_false_positive_typosquat(wl, host):
    """Common international brands must NOT be flagged as Thai-gov typosquats.

    With TYPOSQUAT_MAX_DISTANCE=3 and 500+ whitelist entries, many well-known
    brands accidentally fall within absolute edit distance 3 of some short Thai-gov
    label. The proportional-distance gate (dist/min_len ≤ 0.50) rejects these
    accidental collisions.
    """
    feat = wl.whitelist_features(host)
    assert feat["is_typosquat"] == 0, (
        f"{host} incorrectly flagged as typosquat of {feat['closest_domain']} "
        f"(dist={feat['min_edit_distance']})"
    )


def test_whitelist_genuine_typosquat_still_detected(wl):
    """Legitimate Thai-gov typosquats must still be caught after the proportional fix."""
    # "0bec.com" — brand "0bec" vs "obec" (dist=1, proportion=1/4=0.25 ≤ 0.5) → typosquat
    feat = wl.whitelist_features("0bec.com")
    assert feat["is_typosquat"] == 1

    # "obec.xyz" — TLD swap (dist=0) → always typosquat
    feat = wl.whitelist_features("obec.xyz")
    assert feat["is_typosquat"] == 1


def test_whitelist_from_entries_dedupes():
    wl = Whitelist.from_entries([
        WhitelistEntry("Obec.go.th", "OBEC", "go.th"),
        WhitelistEntry("obec.go.th", "OBEC2", "go.th"),
    ])
    assert len(wl.entries) == 1
    assert wl.entries[0].domain == "obec.go.th"
