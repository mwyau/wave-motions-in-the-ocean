#!/usr/bin/env python3
"""Build and structurally validate the reflowable EPUB edition."""
from __future__ import annotations

import html
import os
import posixpath
import re
import shutil
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
BUILD = ROOT / "build" / "epub"
HTML_SOURCE = ROOT / "build" / "html-pandoc" / "source"
RECON = ROOT / "reconstruction"
CSS = RECON / "styles" / "wave-epub.css"
EPUB = OUT / "wave-motions.epub"
COVER_DIR = BUILD / "cover"
COVER_PDF = COVER_DIR / "cover.pdf"
COVER_PNG = COVER_DIR / "cover.png"

TITLE = "Wave Motions in the Ocean: Myrl's View"
AUTHORS = ("David C. Chapman", "Paola Malanotte-Rizzoli")
EDITOR = "Albert M. W. Yau (digital editor)"
NAV_SENTINELS = (
    "Basic concepts",
    "Acoustic waves",
    "Surface gravity waves",
    "Internal gravity waves",
    "Shallow water dynamics",
    "Topographic effects",
    "References",
)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def canonical_inputs() -> list[Path]:
    frontmatter = HTML_SOURCE / "frontmatter.tex"
    chapters = [HTML_SOURCE / f"chapter{i}.tex" for i in range(1, 7)]
    paths = [frontmatter, *chapters]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit(
            "missing transformed canonical EPUB input(s): " + ", ".join(missing)
        )

    credit_source = RECON / "cover-credit.tex"
    if not credit_source.is_file():
        raise SystemExit(f"missing cover credit source: {credit_source}")
    epub_frontmatter = BUILD / "frontmatter.tex"
    text = frontmatter.read_text()
    marker = r"\wavecovercredit"
    if marker not in text:
        raise SystemExit("EPUB front matter is missing the cover-credit marker")
    text = text.replace(marker, credit_source.read_text().strip(), 1)
    epub_frontmatter.write_text(text)
    return [epub_frontmatter, *chapters]


def render_cover() -> None:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    wrapper = COVER_DIR / "cover.tex"
    wrapper.write_text(
        r"""\documentclass[11pt,oneside]{report}
\usepackage{styles/wave-modern}
\begin{document}
\input{cover-modern}
\WaveModernCover
\clearpage
\nopagecolor
\end{document}
"""
    )
    env = os.environ.copy()
    texinputs = str(RECON) + "//:"
    if env.get("TEXINPUTS"):
        texinputs += env["TEXINPUTS"]
    env["TEXINPUTS"] = texinputs
    run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-jobname=cover",
            str(wrapper),
        ],
        cwd=COVER_DIR,
        env=env,
    )
    if not COVER_PDF.is_file() or COVER_PDF.stat().st_size == 0:
        raise SystemExit("shared PDF/EPUB cover rendering failed")
    run(
        [
            "pdftoppm",
            "-f", "1",
            "-l", "1",
            "-singlefile",
            "-r", "200",
            "-png",
            str(COVER_PDF),
            str(COVER_PNG.with_suffix("")),
        ]
    )
    if not COVER_PNG.is_file() or COVER_PNG.stat().st_size == 0:
        raise SystemExit("EPUB cover rasterization failed")


def write_metadata() -> Path:
    path = BUILD / "metadata.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"title: \"{TITLE}\"\n"
        "author:\n"
        + "".join(f"  - {author}\n" for author in AUTHORS)
        + "date: \"1989\"\n"
        "lang: en-US\n"
        "rights: \"CC BY-NC-SA 4.0\"\n"
        "identifier: \"https://mwyau.github.io/wave-motions-in-the-ocean/\"\n"
        f"contributor: \"{EDITOR}\"\n"
        "---\n"
    )
    return path


def build_epub(inputs: list[Path], metadata: Path) -> None:
    EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB.unlink(missing_ok=True)
    resource_path = os.pathsep.join((str(OUT), str(HTML_SOURCE), str(RECON)))
    run(
        [
            "pandoc",
            *(str(path) for path in inputs),
            "-f", "latex",
            "-t", "epub3",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            "--mathml",
            "--citeproc",
            f"--bibliography={RECON / 'references.bib'}",
            "--metadata", "nocite=@*",
            "--metadata-file", str(metadata),
            "--metadata", f"title={TITLE}",
            "--css", str(CSS),
            "--epub-cover-image", str(COVER_PNG),
            "--resource-path", resource_path,
            "-o", str(EPUB),
        ]
    )


def text_content(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def resolved_member(base: str, ref: str) -> str | None:
    parsed = urllib.parse.urlsplit(ref)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = urllib.parse.unquote(parsed.path)
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), path))


def validate_internal_refs(archive: zipfile.ZipFile, xhtml_names: list[str]) -> None:
    names = set(archive.namelist())
    broken: list[tuple[str, str]] = []
    ref_re = re.compile(rb'(?:href|src)=["\']([^"\']+)["\']', re.I)
    for name in xhtml_names:
        content = archive.read(name)
        for raw_ref in ref_re.findall(content):
            ref = html.unescape(raw_ref.decode("utf-8", errors="replace"))
            member = resolved_member(name, ref)
            if member is not None and member not in names:
                broken.append((name, ref))
    if broken:
        for name, ref in broken[:20]:
            print(f"broken EPUB reference: {name}: {ref}")
        raise SystemExit(f"EPUB contains {len(broken)} broken internal reference(s)")


def validate_epub() -> None:
    if not EPUB.is_file() or EPUB.stat().st_size == 0:
        raise SystemExit("EPUB output is missing or empty")

    with zipfile.ZipFile(EPUB) as archive:
        names = archive.namelist()
        name_set = set(names)
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        if archive.read("mimetype") != b"application/epub+zip":
            raise SystemExit("invalid EPUB mimetype")
        if "META-INF/container.xml" not in name_set:
            raise SystemExit("EPUB container.xml is missing")
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"corrupt EPUB member: {bad}")

        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = container.find(".//{*}rootfile")
        if rootfile is None or not rootfile.get("full-path"):
            raise SystemExit("EPUB container has no package rootfile")
        opf_name = rootfile.get("full-path")
        assert opf_name is not None
        if opf_name not in name_set:
            raise SystemExit(f"EPUB package document is missing: {opf_name}")

        opf_root = ET.fromstring(archive.read(opf_name))
        metadata = opf_root.find("{*}metadata")
        manifest = opf_root.find("{*}manifest")
        spine = opf_root.find("{*}spine")
        if metadata is None or manifest is None or spine is None:
            raise SystemExit("EPUB package metadata/manifest/spine is incomplete")

        title = metadata.find("{http://purl.org/dc/elements/1.1/}title")
        if title is None or text_content(title) != TITLE:
            got = text_content(title) if title is not None else "<missing>"
            raise SystemExit(f"EPUB metadata title is incorrect: {got!r}")

        creators = [
            text_content(item)
            for item in metadata.findall("{http://purl.org/dc/elements/1.1/}creator")
        ]
        if not all(author in creators for author in AUTHORS):
            raise SystemExit(f"EPUB author metadata is incomplete: {creators!r}")
        contributors = [
            text_content(item)
            for item in metadata.findall("{http://purl.org/dc/elements/1.1/}contributor")
        ]
        if EDITOR not in contributors:
            raise SystemExit(f"EPUB editor metadata is missing: {contributors!r}")

        package_dir = posixpath.dirname(opf_name)
        manifest_items = list(manifest.findall("{*}item"))
        by_id = {item.get("id"): item for item in manifest_items if item.get("id")}
        cover_items = [
            item for item in manifest_items
            if "cover-image" in (item.get("properties") or "").split()
        ]
        if len(cover_items) != 1:
            raise SystemExit(f"expected one EPUB cover image, found {len(cover_items)}")
        cover_href = cover_items[0].get("href")
        if not cover_href:
            raise SystemExit("EPUB cover image has no href")
        cover_member = posixpath.normpath(
            posixpath.join(package_dir, urllib.parse.unquote(cover_href))
        )
        if cover_member not in name_set:
            raise SystemExit(f"EPUB cover image member is missing: {cover_member}")

        nav_items = [
            item for item in manifest_items
            if "nav" in (item.get("properties") or "").split()
        ]
        if len(nav_items) != 1 or not nav_items[0].get("href"):
            raise SystemExit("EPUB navigation document is missing or ambiguous")
        nav_name = posixpath.normpath(
            posixpath.join(package_dir, urllib.parse.unquote(nav_items[0].get("href") or ""))
        )
        if nav_name not in name_set:
            raise SystemExit(f"EPUB navigation member is missing: {nav_name}")
        nav_root = ET.fromstring(archive.read(nav_name))
        nav_text = " ".join(text_content(a) for a in nav_root.findall(".//{*}a"))
        for sentinel in NAV_SENTINELS:
            if sentinel not in nav_text:
                raise SystemExit(f"EPUB navigation is missing: {sentinel}")
        if nav_text.strip() == "References":
            raise SystemExit("EPUB navigation regressed to a References-only title")

        spine_ids = [item.get("idref") for item in spine.findall("{*}itemref")]
        if len(spine_ids) < 8 or any(item_id not in by_id for item_id in spine_ids):
            raise SystemExit("EPUB spine is unexpectedly short or references missing manifest items")

        xhtml_names = [
            posixpath.normpath(
                posixpath.join(package_dir, urllib.parse.unquote(item.get("href") or ""))
            )
            for item in manifest_items
            if item.get("media-type") == "application/xhtml+xml" and item.get("href")
        ]
        if not xhtml_names or any(name not in name_set for name in xhtml_names):
            raise SystemExit("EPUB XHTML manifest is incomplete")
        validate_internal_refs(archive, xhtml_names)

        xhtml = b"\n".join(archive.read(name) for name in xhtml_names)
        math_count = len(re.findall(rb"<math(?:\s|>)", xhtml))
        if math_count < 50:
            raise SystemExit(
                f"EPUB contains only {math_count} MathML element(s); math rendering regressed"
            )
        if b"David C. Chapman" not in xhtml or b"Paola Malanotte-Rizzoli" not in xhtml:
            raise SystemExit("EPUB text sentinel is missing")
        if b"JP1847" not in xhtml:
            raise SystemExit("EPUB cover credit is missing")
        if b"<table" not in xhtml:
            raise SystemExit("EPUB contains no table markup")

        image_count = sum(
            1 for item in manifest_items if (item.get("media-type") or "").startswith("image/")
        )
        if image_count < 5:
            raise SystemExit(f"EPUB contains only {image_count} image asset(s)")

    print(f"EPUB build OK: {EPUB.relative_to(ROOT)} ({EPUB.stat().st_size} bytes)")


def main() -> int:
    for command in ("pandoc", "pdflatex", "pdftoppm"):
        if shutil.which(command) is None:
            raise SystemExit(f"missing required command: {command}")
    if not CSS.is_file():
        raise SystemExit(f"missing EPUB stylesheet: {CSS}")
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    inputs = canonical_inputs()
    render_cover()
    metadata = write_metadata()
    build_epub(inputs, metadata)
    validate_epub()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
