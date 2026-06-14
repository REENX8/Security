"""Cross-contract test: dashboard feature catalog must cover the schema.

The dashboard's feature catalog (dashboard/src/lib/features.js) is hand-written
JS, so it can silently drift from phish_features/schema.py ORDERED_FEATURES when
a new feature is appended. vitest cannot import the Python schema, so this guard
lives on the Python side: it regex-extracts the keys declared in the JS and
asserts every model feature appears in BOTH the grouped catalog and the label
map. A missing key means the DetailModal would render the feature under the raw
fallback name (or omit it from a group) — a regression worth failing on.
"""

from __future__ import annotations

import re
from pathlib import Path

from phish_features import ORDERED_FEATURES

ROOT = Path(__file__).resolve().parents[1]
_JS = ROOT / "dashboard" / "src" / "lib" / "features.js"


def _js_source() -> str:
    assert _JS.exists(), f"missing dashboard feature catalog: {_JS}"
    return _JS.read_text(encoding="utf-8")


def _group_keys(src: str) -> set[str]:
    """All quoted strings inside the FEATURE_GROUPS `keys: [ ... ]` arrays."""
    keys: set[str] = set()
    for block in re.findall(r"keys:\s*\[(.*?)\]", src, flags=re.DOTALL):
        keys.update(re.findall(r'"([a-z0-9_]+)"', block))
    return keys


def _label_keys(src: str) -> set[str]:
    """Keys of the FEATURE_LABELS object (identifier: "..." entries)."""
    body = re.search(
        r"FEATURE_LABELS\s*=\s*\{(.*?)\};", src, flags=re.DOTALL
    )
    assert body, "could not locate FEATURE_LABELS object"
    return set(re.findall(r"(\w+):\s*\"", body.group(1)))


def test_every_schema_feature_is_grouped():
    group_keys = _group_keys(_js_source())
    missing = [f for f in ORDERED_FEATURES if f not in group_keys]
    assert not missing, (
        "features missing from dashboard FEATURE_GROUPS: " + ", ".join(missing)
    )


def test_every_schema_feature_has_a_label():
    label_keys = _label_keys(_js_source())
    missing = [f for f in ORDERED_FEATURES if f not in label_keys]
    assert not missing, (
        "features missing from dashboard FEATURE_LABELS: " + ", ".join(missing)
    )


def test_no_stale_catalog_keys():
    """Every catalog key must be a real model feature (catches typos/renames)."""
    src = _js_source()
    schema = set(ORDERED_FEATURES)
    for key in _group_keys(src):
        assert key in schema, f"FEATURE_GROUPS references unknown feature: {key}"
    for key in _label_keys(src):
        assert key in schema, f"FEATURE_LABELS references unknown feature: {key}"
