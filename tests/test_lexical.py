"""Lexical feature extraction tests."""

from __future__ import annotations

import math

import pytest

from phish_features.lexical import (
    count_subdomains,
    extract_lexical,
    get_host,
    host_is_ip,
    normalize_url,
    registrable_suffix_len,
    shannon_entropy,
)


def test_shannon_entropy_empty_is_zero():
    assert shannon_entropy("") == 0


def test_shannon_entropy_uniform_is_log2_n():
    # "abcd" -> uniform over 4 chars -> entropy log2(4) == 2
    assert shannon_entropy("abcd") == pytest.approx(2.0)


def test_shannon_entropy_single_char_is_zero():
    assert shannon_entropy("aaaaa") == 0


def test_shannon_entropy_real_url_positive():
    assert shannon_entropy("https://www.obec.go.th") > 3.0


def test_normalize_url_adds_scheme():
    assert normalize_url("obec.go.th").startswith("http://")


def test_normalize_url_keeps_existing_scheme():
    assert normalize_url("https://obec.go.th") == "https://obec.go.th"


def test_get_host_lowercase():
    assert get_host("HTTPS://OBEC.GO.TH/path") == "obec.go.th"


def test_get_host_strips_port():
    assert get_host("http://example.com:8080/x") == "example.com"


@pytest.mark.parametrize("host,expected", [
    ("1.2.3.4", True),
    ("192.168.1.1", True),
    ("203.0.113.45", True),
    ("[2001:db8::1]", True),
    ("obec.go.th", False),
    ("example.com", False),
    ("", False),
    ("999.999.999.999", False),  # invalid IPv4 octets
])
def test_host_is_ip(host, expected):
    assert host_is_ip(host) == expected


@pytest.mark.parametrize("host,expected", [
    ("obec.go.th", 3),       # go.th is multi-label
    ("school.obec.go.th", 3),
    ("chula.ac.th", 3),
    ("example.com", 2),
    ("foo.example.com", 2),
])
def test_registrable_suffix_len(host, expected):
    assert registrable_suffix_len(host) == expected


@pytest.mark.parametrize("host,expected", [
    ("obec.go.th", 0),                      # no subdomain
    ("www.obec.go.th", 1),
    ("a.b.obec.go.th", 2),
    ("example.com", 0),
    ("foo.example.com", 1),
    ("a.b.c.example.com", 3),
    ("1.2.3.4", 0),                         # IP -> 0
])
def test_count_subdomains(host, expected):
    assert count_subdomains(host) == expected


def test_extract_lexical_legit_url():
    feat = extract_lexical("https://www.obec.go.th")
    assert feat["url_length"] == len("https://www.obec.go.th")
    assert feat["has_https"] == 1
    assert feat["has_ip"] == 0
    assert feat["num_at"] == 0
    assert feat["num_subdomains"] == 1
    assert feat["num_dots"] == 3
    assert feat["entropy"] > 0


def test_extract_lexical_ip_host():
    feat = extract_lexical("http://203.0.113.45/login")
    assert feat["has_ip"] == 1
    assert feat["has_https"] == 0
    assert feat["num_subdomains"] == 0


def test_extract_lexical_at_trick():
    feat = extract_lexical("http://obec.go.th@evil.com/login")
    assert feat["num_at"] == 1
    # urlparse correctly extracts "evil.com" as the host, not obec.go.th
    assert feat["has_https"] == 0
