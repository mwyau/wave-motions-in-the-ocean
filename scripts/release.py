#!/usr/bin/env python3
"""Canonical release assets, packaging, and SHA-256 verification."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import re
import shutil
import zipfile
from collections.abc import Iterable
from pathlib import Path

DEFAULT_FILES = (
    "wave-motions.pdf",
    "wave-motions-facsimile.pdf",
    "wave-motions.epub",
)
MANIFEST = "SHA256SUMS"
HTML_ARCHIVE = "wave-motions-html.zip"
CHECKSUM_ASSETS = (*DEFAULT_FILES, HTML_ARCHIVE)
RELEASE_ASSETS = (*CHECKSUM_ASSETS, MANIFEST)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(name: str) -> str:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or name in {"", ".", MANIFEST}:
        raise ValueError(f"unsafe checksum path: {name!r}")
    return name


def _checked_names(names: Iterable[str]) -> list[str]:
    checked = [_safe_name(name) for name in names]
    if len(checked) != len(set(checked)):
        raise ValueError("checksum file list contains duplicate paths")
    return checked


def write_manifest(root: Path, names: tuple[str, ...] | list[str]) -> Path:
    root = root.resolve()
    checked = _checked_names(names)
    missing = [name for name in checked if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing checksum inputs: {', '.join(missing)}")
    manifest = root / MANIFEST
    manifest.write_text("".join(f"{sha256(root / name)}  {name}\n" for name in checked))
    return manifest


def verify_manifest(root: Path, expected_names: Iterable[str] | None = None) -> int:
    root = root.resolve()
    manifest = root / MANIFEST
    if not manifest.is_file():
        raise FileNotFoundError(f"missing checksum manifest: {manifest}")

    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        expected, separator, name = line.partition("  ")
        if not separator or not SHA256_RE.fullmatch(expected):
            raise ValueError(f"invalid checksum line {line_no}")
        name = _safe_name(name)
        if name in seen:
            raise ValueError(f"duplicate checksum target: {name}")
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"checksum target is missing: {name}")
        actual = sha256(path)
        if not hmac.compare_digest(actual, expected):
            raise ValueError(f"checksum mismatch: {name}")
        seen.add(name)

    if not seen:
        raise ValueError("checksum manifest is empty")
    if expected_names is not None:
        expected = set(_checked_names(expected_names))
        missing = sorted(expected - seen)
        unexpected = sorted(seen - expected)
        if missing or unexpected:
            details: list[str] = []
            if missing:
                details.append(f"missing: {', '.join(missing)}")
            if unexpected:
                details.append(f"unexpected: {', '.join(unexpected)}")
            raise ValueError(
                "checksum manifest does not match expected files ("
                + "; ".join(details)
                + ")"
            )
    return len(seen)


def package_release(dist: Path, output: Path) -> None:
    dist = dist.resolve()
    output = output.resolve()
    verify_manifest(dist, DEFAULT_FILES)

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

    write_manifest(output, CHECKSUM_ASSETS)
    verify_manifest(output, CHECKSUM_ASSETS)
    print(f"Release assets ready: {', '.join(RELEASE_ASSETS)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package and verify publication release artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    package = subparsers.add_parser("package", help="prepare the canonical release asset directory")
    package.add_argument("--dist", type=Path, default=Path("dist"))
    package.add_argument("--output", type=Path, default=Path("release"))

    checksums = subparsers.add_parser("checksums", help="write or verify a SHA-256 manifest")
    checksums.add_argument("--root", type=Path, default=Path("dist"))
    action = checksums.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    checksums.add_argument("files", nargs="*")

    subparsers.add_parser("assets", help="print canonical published asset names")
    args = parser.parse_args(argv)
    if args.command == "package":
        package_release(args.dist, args.output)
    elif args.command == "assets":
        print("\n".join(RELEASE_ASSETS))
    else:
        names = args.files or list(DEFAULT_FILES)
        if args.write:
            manifest = write_manifest(args.root, names)
            print(f"Wrote {manifest}")
        else:
            count = verify_manifest(args.root, names)
            print(f"Checksum manifest OK: {count} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
