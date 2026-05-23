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


def test_whitelist_from_entries_dedupes():
    wl = Whitelist.from_entries([
        WhitelistEntry("Obec.go.th", "OBEC", "go.th"),
        WhitelistEntry("obec.go.th", "OBEC2", "go.th"),
    ])
    assert len(wl.entries) == 1
    assert wl.entries[0].domain == "obec.go.th"
