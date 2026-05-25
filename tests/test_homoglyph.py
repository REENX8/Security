"""IDN / homoglyph feature tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from phish_features import (
    FeatureExtractor,
    Whitelist,
    decode_idn,
    fold_confusables,
    has_mixed_script,
    has_punycode,
    normalize_for_lookup,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def extractor() -> FeatureExtractor:
    wl = Whitelist.from_json(str(ROOT / "models" / "whitelist.json"))
    return FeatureExtractor(wl, enable_whois=False, enable_tls=False)


def test_decode_idn_passthrough_for_ascii():
    assert decode_idn("obec.go.th") == "obec.go.th"
    assert decode_idn("") == ""


def test_decode_idn_decodes_punycode_label():
    # "xn--mnchen-3ya" decodes to "münchen"
    decoded = decode_idn("xn--mnchen-3ya.de")
    assert decoded == "münchen.de"


def test_fold_confusables_cyrillic_a_to_a():
    # chulа with Cyrillic а should fold to ASCII chula
    assert fold_confusables("chulа") == "chula"


def test_fold_confusables_strips_accents():
    assert fold_confusables("chulá") == "chula"


def test_has_punycode():
    assert has_punycode("xn--mnchen-3ya.de") is True
    assert has_punycode("obec.go.th") is False


def test_has_mixed_script_cyrillic_in_latin():
    # Cyrillic а mixed into a Latin label
    assert has_mixed_script("chulа.com") is True


def test_has_mixed_script_pure_ascii_is_false():
    assert has_mixed_script("obec.go.th") is False


def test_normalize_for_lookup_round_trips_to_ascii():
    assert normalize_for_lookup("chulа.com") == "chula.com"


def test_extractor_catches_cyrillic_homoglyph(extractor):
    """A Cyrillic-а spoof of chula must collapse to a typosquat hit."""
    feat = extractor.extract_dict("https://chulа.com/login")
    assert feat["has_mixed_script"] == 1
    assert feat["homoglyph_distance"] == 0  # exact match after folding
    assert feat["is_typosquat"] == 1
    assert feat["closest_domain"] == "chula.ac.th"


def test_extractor_flags_punycode(extractor):
    feat = extractor.extract_dict("https://xn--mnchen-3ya.com/login")
    assert feat["has_punycode"] == 1


def test_extractor_zero_punycode_for_normal_url(extractor):
    feat = extractor.extract_dict("https://www.obec.go.th")
    assert feat["has_punycode"] == 0
    assert feat["has_mixed_script"] == 0
    assert feat["homoglyph_distance"] == 0


def test_extractor_ip_host_has_zero_idn_features(extractor):
    feat = extractor.extract_dict("http://203.0.113.45/login")
    assert feat["has_punycode"] == 0
    assert feat["has_mixed_script"] == 0
    assert feat["homoglyph_distance"] == 999
