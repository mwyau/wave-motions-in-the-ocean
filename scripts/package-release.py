#!/usr/bin/env python3
"""Package an already-built publication artifact for a GitHub release."""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from checksums import DEFAULT_FILES, MANIFEST, verify_manifest, write_manifest

HTML_ARCHIVE = "wave-motions-html.zip"


def package_release(dist: Path, output: Path) -> None:
    dist = dist.resolve()
    output = output.resolve()
    verify_manifest(dist)

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for name in DEFAULT_FILES:
        shutil.copy2(dist / name, output / name)

    excluded = {*DEFAULT_FILES, MANIFEST}
    archive_path = output / HTML_ARCHIVE
    included: list[str] = []
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(dist.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(dist)
            if str(relative) in excluded:
                continue
            archive.write(path, relative)
            included.append(str(relative))

    if "index.html" not in included:
        raise ValueError("HTML release archive is missing index.html")

    release_files = [*DEFAULT_FILES, HTML_ARCHIVE]
    write_manifest(output, release_files)
    verify_manifest(output)
    print(f"Release assets ready: {', '.join(release_files)}, {MANIFEST}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, default=Path("release"))
    args = parser.parse_args()
    package_release(args.dist, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
