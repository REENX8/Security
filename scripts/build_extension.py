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
    args = parser.parse_args()
    build(Path(args.outdir).resolve())


if __name__ == "__main__":
    main()
