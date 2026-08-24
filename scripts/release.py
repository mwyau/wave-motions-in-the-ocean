#!/usr/bin/env python3
"""Finalize and verify the publication root."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import re
import zipfile
from collections.abc import Iterable
from pathlib import Path

DEFAULT_ROOT = Path("release")
DEFAULT_FILES = (
    "wave-motions.pdf",
    "wave-motions.epub",
)
QA_ONLY_FILES = ("wave-motions-facsimile.pdf",)
MANIFEST = "SHA256SUMS"
HTML_ARCHIVE = "wave-motions-html.zip"
CHECKSUM_ASSETS = DEFAULT_FILES
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


def publication_files(root: Path) -> tuple[str, ...]:
    """Return every generated publication file except manifest/archive outputs."""
    root = root.resolve()
    excluded = {MANIFEST, HTML_ARCHIVE}
    return tuple(
        sorted(
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file() and str(path.relative_to(root)) not in excluded
        )
    )


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


def finalize_publication(root: Path) -> None:
    root = root.resolve()
    required_files = (*DEFAULT_FILES, *QA_ONLY_FILES, "index.html")
    missing = [name for name in required_files if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"publication root is missing: {', '.join(missing)}")

    (root / HTML_ARCHIVE).unlink(missing_ok=True)
    (root / MANIFEST).unlink(missing_ok=True)
    names = publication_files(root)
    write_manifest(root, names)
    verify_manifest(root, names)
    print("Publication root ready")


def archive_publication(root: Path, output: Path) -> None:
    root = root.resolve()
    output = output.resolve()
    if output.is_relative_to(root):
        raise ValueError("archive output must be outside the publication root")
    if not (root / MANIFEST).is_file():
        raise FileNotFoundError(f"publication root is not finalized: {root / MANIFEST}")
    verify_manifest(root, publication_files(root))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    included: list[str] = []
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            archive.write(path, relative)
            included.append(str(relative))

    required = {"index.html", *DEFAULT_FILES, *QA_ONLY_FILES, MANIFEST}
    missing = sorted(required - set(included))
    if missing:
        raise ValueError("tagged publication archive is missing: " + ", ".join(missing))
    print(f"Tagged publication archive ready: {output}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Finalize and verify publication artifacts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    finalize = subparsers.add_parser("finalize", help="finalize the publication root")
    finalize.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    archive = subparsers.add_parser(
        "archive", help="archive the complete publication root for a tagged release"
    )
    archive.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    archive.add_argument("--output", type=Path, default=Path(HTML_ARCHIVE))

    checksums = subparsers.add_parser(
        "checksums", help="write or verify a SHA-256 manifest"
    )
    checksums.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    action = checksums.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    checksums.add_argument("files", nargs="*")

    args = parser.parse_args(argv)
    if args.command == "finalize":
        finalize_publication(args.root)
    elif args.command == "archive":
        archive_publication(args.root, args.output)
    else:
        names = args.files or list(publication_files(args.root))
        if args.write:
            manifest = write_manifest(args.root, names)
            print(f"Wrote {manifest}")
        else:
            count = verify_manifest(args.root, names)
            print(f"Checksum manifest OK: {count} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
