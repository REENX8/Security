#!/usr/bin/env python3
"""Package the extension/ directory into a versioned, store-ready .zip.

Output:
    dist/thai-phishing-detector-v{VERSION}.zip

Usage:
    python scripts/build_extension.py [--outdir DIR]

The script reads the version from extension/manifest.json. Markdown
documentation, this build script, and OS junk files are excluded from the
package so the upload stays minimal and review-friendly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_DIR = ROOT / "extension"
DEFAULT_OUTDIR = ROOT / "dist"

# Files/patterns excluded from the published .zip.
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep"}
EXCLUDE_SUFFIXES = (".md",)
EXCLUDE_DIRS = {"__pycache__", ".git", ".idea", ".vscode"}

_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+){0,2}$")


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def read_version() -> str:
    with (EXT_DIR / "manifest.json").open(encoding="utf-8") as fh:
        return json.load(fh)["version"]


def required_files_present() -> list[str]:
    """Sanity-check that the files the manifest references actually exist."""
    with (EXT_DIR / "manifest.json").open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    referenced = set()
    bg = manifest.get("background", {}).get("service_worker")
    if bg:
        referenced.add(bg)
    action = manifest.get("action", {})
    if action.get("default_popup"):
        referenced.add(action["default_popup"])
    for size, p in (action.get("default_icon") or {}).items():
        referenced.add(p)
    for size, p in (manifest.get("icons") or {}).items():
        referenced.add(p)
    if (manifest.get("options_ui") or {}).get("page"):
        referenced.add(manifest["options_ui"]["page"])
    for war in manifest.get("web_accessible_resources", []):
        for res in war.get("resources", []):
            if "*" not in res:
                referenced.add(res)

    missing = [r for r in referenced if not (EXT_DIR / r).exists()]
    return missing


def check() -> list[str]:
    """Validate store-readiness WITHOUT writing a .zip.

    Returns a list of problems (empty = ready). Catches the mistakes that get
    a Chrome Web Store upload rejected or that ship a bloated/leaky package:
      * a manifest version that is missing or not a valid dotted number,
      * manifest-referenced files that do not exist,
      * documentation / source junk that would otherwise leak into the zip.
    """
    problems: list[str] = []

    with (EXT_DIR / "manifest.json").open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    version = manifest.get("version", "")
    if not _SEMVER_RE.match(str(version)):
        problems.append(f"manifest version '{version}' is not a valid dotted-int version")

    problems += [f"manifest references missing file: {m}" for m in required_files_present()]

    # Inspect the exact file list that build() would pack and reject anything
    # that should never reach the store (docs / source maps slipping through
    # if EXCLUDE_SUFFIXES is ever loosened).
    disallowed = (".md", ".map")
    for rel in _packed_arcnames():
        if rel.endswith(disallowed):
            problems.append(f"disallowed file would ship in zip: {rel}")
    return problems


def _packed_arcnames() -> list[str]:
    """The relative paths build() would write into the zip."""
    out: list[str] = []
    for root, dirs, files in os.walk(EXT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            src = Path(root) / name
            if not should_skip(src):
                out.append(src.relative_to(EXT_DIR).as_posix())
    return out


def build(outdir: Path) -> Path:
    if not EXT_DIR.is_dir():
        sys.exit(f"error: {EXT_DIR} does not exist")

    missing = required_files_present()
    if missing:
        sys.exit("error: manifest references missing files: "
                 + ", ".join(missing))

    version = read_version()
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"thai-phishing-detector-v{version}.zip"

    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(EXT_DIR):
            # in-place skip of excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for name in files:
                src = Path(root) / name
                if should_skip(src):
                    continue
                # arcname is the path RELATIVE to extension/, so the zip
                # contains manifest.json at the root -- which is what Chrome
                # / Edge / Firefox expect.
                arcname = src.relative_to(EXT_DIR).as_posix()
                zf.write(src, arcname)
                count += 1

    size_kb = out_path.stat().st_size / 1024
    print(f"  packed {count} files")
    print(f"  wrote  {out_path}  ({size_kb:.1f} KB, v{version})")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--outdir", default=str(DEFAULT_OUTDIR),
        help=f"output directory (default: {DEFAULT_OUTDIR.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="validate store-readiness and exit non-zero on problems (no zip)",
    )
    args = parser.parse_args()

    if args.check:
        problems = check()
        if problems:
            print("extension check FAILED:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        print(f"extension check OK (v{read_version()}, "
              f"{len(_packed_arcnames())} files ready to pack)")
        return

    build(Path(args.outdir).resolve())


if __name__ == "__main__":
    main()
