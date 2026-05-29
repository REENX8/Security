"""Store-readiness checks for the browser-extension packaging script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def be():
    spec = importlib.util.spec_from_file_location(
        "build_extension", ROOT / "scripts" / "build_extension.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_extension_passes_store_readiness_check(be):
    assert be.check() == []


def test_manifest_version_is_valid_semver(be):
    assert be._SEMVER_RE.match(be.read_version())


def test_no_markdown_or_sourcemaps_in_package(be):
    packed = be._packed_arcnames()
    assert "manifest.json" in packed
    assert not [p for p in packed if p.endswith((".md", ".map"))]


def test_check_flags_missing_manifest_reference(be, monkeypatch):
    # Pretend a referenced file is missing -> check() must report it.
    monkeypatch.setattr(be, "required_files_present", lambda: ["popup.html"])
    problems = be.check()
    assert any("popup.html" in p for p in problems)
