#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Checkmk extension package (.mkp) for directory_status.

The repository layout already matches the MKP package parts:

  agents/                          -> agents.tar
  cmk_addons/plugins/              -> cmk_addons_plugins.tar

Usage:
  ./scripts/build_mkp.py
  ./scripts/build_mkp.py --version 1.0.1 --output-dir dist
"""

from __future__ import annotations

import argparse
import json
import pprint
import tarfile
import time
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PACKAGE_NAME = "directory_status"
PACKAGE_TITLE = "Directory status (file count and freshness)"
PACKAGE_AUTHOR = "Checkmk Plugin Developers"
PACKAGE_DESCRIPTION = (
    "Monitors configured directories on Linux hosts. Reports the number of "
    "regular files (non-recursive) and the age of the newest file. Thresholds "
    "for both values are configurable in WATO. Directories are configured via "
    "the agent bakery or $MK_CONFDIR/directory_status.cfg."
)
PACKAGE_DOWNLOAD_URL = ""
VERSION_MIN_REQUIRED = "2.3.0"
VERSION_USABLE_UNTIL = None
VERSION_PACKAGED = "build_mkp.py"


def _collect_files(base: Path, relative_to: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {"__pycache__", ".ruff_cache", ".git"} for part in path.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(str(path.relative_to(relative_to)))
    return files


def _create_part_tar(src_dir: Path, filenames: list[str]) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name in filenames:
            full_path = src_dir / name
            tarinfo = tar.gettarinfo(str(full_path), arcname=name)
            tarinfo.uid = 0
            tarinfo.gid = 0
            tarinfo.uname = ""
            tarinfo.gname = ""
            # Agent scripts must be executable; keep other modes readable.
            if full_path.parent.name == "plugins" and full_path.is_file():
                tarinfo.mode = 0o755
            else:
                tarinfo.mode = 0o644
            with full_path.open("rb") as handle:
                tar.addfile(tarinfo, handle)
    return buffer.getvalue()


def _tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.mtime = int(time.time())
    info.uid = 0
    info.gid = 0
    info.size = size
    info.mode = 0o644
    info.type = tarfile.REGTYPE
    return info


def _create_mkp(members: list[tuple[str, bytes]]) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, content in members:
            tar.addfile(_tar_info(name, len(content)), BytesIO(content))
    return buffer.getvalue()


def build_manifest(
    *,
    version: str,
    agent_files: list[str],
    addon_files: list[str],
) -> dict[str, object]:
    files: dict[str, list[str]] = {}
    if agent_files:
        files["agents"] = agent_files
    if addon_files:
        files["cmk_addons_plugins"] = addon_files

    return {
        "author": PACKAGE_AUTHOR,
        "description": PACKAGE_DESCRIPTION,
        "download_url": PACKAGE_DOWNLOAD_URL,
        "files": files,
        "name": PACKAGE_NAME,
        "title": PACKAGE_TITLE,
        "version": version,
        "version.min_required": VERSION_MIN_REQUIRED,
        "version.packaged": VERSION_PACKAGED,
        "version.usable_until": VERSION_USABLE_UNTIL,
    }


def build(*, version: str, output_dir: Path) -> Path:
    agents_dir = REPO_ROOT / "agents"
    addons_dir = REPO_ROOT / "cmk_addons" / "plugins"

    agent_files = _collect_files(agents_dir, agents_dir)
    addon_files = _collect_files(addons_dir / PACKAGE_NAME, addons_dir)

    if not agent_files:
        raise SystemExit(f"No agent files found under {agents_dir}")
    if not addon_files:
        raise SystemExit(f"No cmk_addons files found under {addons_dir / PACKAGE_NAME}")

    manifest = build_manifest(
        version=version,
        agent_files=agent_files,
        addon_files=addon_files,
    )

    members: list[tuple[str, bytes]] = [
        ("info", f"{pprint.pformat(manifest)}\n".encode()),
        ("info.json", (json.dumps(manifest, indent=2) + "\n").encode()),
        ("agents.tar", _create_part_tar(agents_dir, agent_files)),
        ("cmk_addons_plugins.tar", _create_part_tar(addons_dir, addon_files)),
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    mkp_path = output_dir / f"{PACKAGE_NAME}-{version}.mkp"
    mkp_path.write_bytes(_create_mkp(members))
    return mkp_path


def _inspect(mkp_path: Path) -> None:
    print(f"Created {mkp_path} ({mkp_path.stat().st_size} bytes)")
    print("Contents:")
    with tarfile.open(mkp_path, mode="r:gz") as tar:
        for member in tar.getmembers():
            print(f"  {member.name}")
            if member.name.endswith(".tar"):
                extracted = tar.extractfile(member)
                assert extracted is not None
                with tarfile.open(fileobj=BytesIO(extracted.read()), mode="r:") as part:
                    for part_member in part.getmembers():
                        mode = oct(part_member.mode)[-3:]
                        print(f"    {mode} {part_member.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Package version (semantic versioning, default: 1.0.0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "dist",
        help="Directory for the generated .mkp (default: ./dist)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the output path",
    )
    args = parser.parse_args(argv)

    mkp_path = build(version=args.version, output_dir=args.output_dir.resolve())
    if args.quiet:
        print(mkp_path)
    else:
        _inspect(mkp_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
