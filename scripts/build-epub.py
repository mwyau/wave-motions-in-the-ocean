#!/usr/bin/env python3
"""Build the reflowable EPUB edition from the generated canonical HTML view."""
from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
BUILD = ROOT / "build" / "epub"
INPUT = BUILD / "input"
RECON = ROOT / "reconstruction"
COVER_SVG = RECON / "figures" / "frontmatter" / "epub-cover.svg"
COVER_PNG = BUILD / "cover.png"
CSS = RECON / "styles" / "wave-epub.css"
EPUB = OUT / "wave-motions.epub"

PAGES = ["index.html", *(f"chapter{i}.html" for i in range(1, 7)), "references.html"]
NAV_RE = re.compile(r'<nav class="book-nav"[^>]*>.*?</nav>', re.S | re.I)
TOC_RE = re.compile(r'<section class="book-toc">.*?</section>', re.S | re.I)
LICENSE_RE = re.compile(r'<p class="license">.*?</p>', re.S | re.I)
BODY_RE = re.compile(r"<body[^>]*>(?P<body>.*?)</body>", re.S | re.I)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def cleaned_html(path: Path) -> str:
    text = path.read_text(errors="replace")
    match = BODY_RE.search(text)
    if not match:
        raise RuntimeError(f"missing body in {path}")
    body = NAV_RE.sub("", match.group("body"))
    if path.name == "index.html":
        body = TOC_RE.sub("", body)
        body = LICENSE_RE.sub("", body)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{path.stem}</title></head><body>{body}</body></html>\n"
    )


def prepare_inputs() -> list[Path]:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    INPUT.mkdir(parents=True)

    assets = OUT / "assets"
    if not assets.is_dir():
        raise SystemExit("missing generated HTML assets; run build-html.py first")
    shutil.copytree(assets, INPUT / "assets")

    inputs: list[Path] = []
    for name in PAGES:
        source = OUT / name
        if not source.is_file():
            raise SystemExit(f"missing generated HTML page: {source}")
        dest = INPUT / name
        dest.write_text(cleaned_html(source))
        inputs.append(dest)
    return inputs


def render_cover() -> None:
    if not COVER_SVG.is_file():
        raise SystemExit(f"missing EPUB cover source: {COVER_SVG}")
    run([
        "rsvg-convert",
        "-w", "1600",
        "-h", "2560",
        "-o", str(COVER_PNG),
        str(COVER_SVG),
    ])
    if not COVER_PNG.is_file() or COVER_PNG.stat().st_size == 0:
        raise SystemExit("EPUB cover rendering failed")


def write_metadata() -> Path:
    path = BUILD / "metadata.yaml"
    path.write_text(
        "---\n"
        "title: \"Wave Motions in the Ocean: Myrl's View\"\n"
        "author:\n"
        "  - David C. Chapman\n"
        "  - Paola Malanotte-Rizzoli\n"
        "date: \"1989\"\n"
        "lang: en-US\n"
        "rights: \"CC BY-NC-SA 4.0\"\n"
        "identifier: \"https://mwyau.github.io/wave-motions-in-the-ocean/\"\n"
        "---\n"
    )
    return path


def build_epub(inputs: list[Path], metadata: Path) -> None:
    EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB.unlink(missing_ok=True)
    run([
        "pandoc",
        *(str(path) for path in inputs),
        "-f", "html",
        "-t", "epub3",
        "--toc",
        "--toc-depth=2",
        "--split-level=1",
        "--mathml",
        "--metadata-file", str(metadata),
        "--css", str(CSS),
        "--epub-cover-image", str(COVER_PNG),
        "--resource-path", str(INPUT),
        "-o", str(EPUB),
    ])


def validate_epub() -> None:
    if not EPUB.is_file() or EPUB.stat().st_size == 0:
        raise SystemExit("EPUB output is missing or empty")
    with zipfile.ZipFile(EPUB) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        if archive.read("mimetype") != b"application/epub+zip":
            raise SystemExit("invalid EPUB mimetype")
        if "META-INF/container.xml" not in names:
            raise SystemExit("EPUB container.xml is missing")
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"corrupt EPUB member: {bad}")
    print(f"EPUB build OK: {EPUB.relative_to(ROOT)} ({EPUB.stat().st_size} bytes)")


def main() -> int:
    for command in ("pandoc", "rsvg-convert"):
        if shutil.which(command) is None:
            raise SystemExit(f"missing required command: {command}")
    if not CSS.is_file():
        raise SystemExit(f"missing EPUB stylesheet: {CSS}")
    inputs = prepare_inputs()
    render_cover()
    metadata = write_metadata()
    build_epub(inputs, metadata)
    validate_epub()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
