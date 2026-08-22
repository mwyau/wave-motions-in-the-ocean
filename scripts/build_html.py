#!/usr/bin/env python3
"""Build the complete chapter-split modern HTML edition.

Pandoc supplies the document markup after the shared canonical publication
preparation. This script owns dynamic publication data and final assembly; the
maintained reader shell lives in reconstruction/templates/wave-html.html.
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.parse
from pathlib import Path
from string import Template

from publication import (
    BOOK_TITLE,
    DOWNLOADS,
    LANGUAGE,
    MATHJAX_URL,
    PUBLICATION_TITLE,
    REPOSITORY_URL,
    book_structure,
    current_build,
    html_contents,
    html_license,
    prepare_assets,
    prepare_flowing_sources,
    section_slug,
)

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
BUILD = ROOT / "build" / "html-pandoc"
OUT = ROOT / "dist"
ASSETS = OUT / "assets"
HTML_TEMPLATE = RECON / "templates" / "wave-html.html"
EXPECTED_PAGES = [
    OUT / "index.html",
    *(OUT / f"chapter{i}.html" for i in range(1, 7)),
    OUT / "references.html",
]
HEADING_TRANSLATION = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "ʼ": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "\u00a0": " ",
    }
)


def require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"missing required command: {command}")


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    try:
        subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            sys.stderr.write(exc.stderr[-12000:])
        raise


def pandoc_page(source_tex: Path, output: Path, title: str) -> None:
    resource_path = os.pathsep.join((str(OUT), str(source_tex.parent), str(RECON)))
    run(
        [
            "pandoc",
            str(source_tex),
            "-f",
            "latex+smart",
            "-t",
            "html5",
            "-s",
            f"--mathjax={MATHJAX_URL}",
            "--metadata",
            f"title={title}",
            "--metadata",
            f"lang={LANGUAGE}",
            "--resource-path",
            resource_path,
            "-o",
            str(output),
        ]
    )


def page_context(path: Path) -> str:
    if path.name == "index.html":
        return "Front matter & contents"
    if path.name == "references.html":
        return "References"
    match = re.fullmatch(r"chapter([1-6])\.html", path.name)
    if match:
        number = int(match.group(1))
        chapter = next(item for item in book_structure() if item.number == number)
        return f"Chapter {chapter.number} · {chapter.title}"
    raise ValueError(f"unexpected publication page: {path.name}")


def page_index(path: Path) -> int | None:
    if path.name == "index.html":
        return None
    if path.name == "references.html":
        return 0
    match = re.fullmatch(r"chapter([1-6])\.html", path.name)
    if not match:
        raise ValueError(f"unexpected publication page: {path.name}")
    return int(match.group(1))


def navigation_state(index: int | None) -> dict[str, str]:
    previous_url = ""
    next_url = ""
    references_url = ""

    if index == 0:
        previous_url = "chapter6.html"
    elif index is not None:
        if index > 1:
            previous_url = f"chapter{index - 1}.html"
        if index < 6:
            next_url = f"chapter{index + 1}.html"
        else:
            references_url = "references.html"

    return {
        "previous_url": html.escape(previous_url, quote=True),
        "previous_hidden": "" if previous_url else " hidden",
        "next_url": html.escape(next_url, quote=True),
        "next_hidden": "" if next_url else " hidden",
        "references_url": html.escape(references_url, quote=True),
        "references_hidden": "" if references_url else " hidden",
        "chapter_nav_hidden": " hidden" if index is None else "",
    }


def reader_state(index: int | None) -> dict[str, str]:
    if index is None:
        return {
            "reader_context_hidden": " hidden",
            "reader_chapter": "",
            "reader_title": "",
            "reader_title_hidden": " hidden",
            "chapter_toc": "",
        }
    if index == 0:
        return {
            "reader_context_hidden": "",
            "reader_chapter": "References",
            "reader_title": "",
            "reader_title_hidden": " hidden",
            "chapter_toc": "",
        }

    chapter = next(item for item in book_structure() if item.number == index)
    toc_items = "".join(
        f'<li><a href="#{section_slug(section)}" data-section-link="{section_slug(section)}">'
        f"{html.escape(section)}</a></li>"
        for section in chapter.sections
    )
    return {
        "reader_context_hidden": "",
        "reader_chapter": f"Chapter {chapter.number}",
        "reader_title": html.escape(chapter.title),
        "reader_title_hidden": "",
        "chapter_toc": f"<ol>{toc_items}</ol>" if toc_items else "",
    }


def mark_chapter_title_block(page: Path) -> None:
    text = page.read_text(errors="replace")
    marker = '<header id="title-block-header">'
    if marker not in text:
        raise SystemExit(f"HTML chapter title block missing from {page.name}")
    page.write_text(
        text.replace(
            marker,
            '<header id="title-block-header" class="chapter-title-block">',
            1,
        )
    )


def build_shell(path: Path) -> None:
    text = path.read_text(errors="replace")
    index = page_index(path)
    context = page_context(path)
    title = BOOK_TITLE if path.name == "index.html" else f"{context} — {BOOK_TITLE}"
    text = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(title)}</title>",
        text,
        count=1,
        flags=re.S,
    )

    info = current_build()
    asset_version = html.escape(info.short_sha, quote=True)
    if "assets/wave.css" not in text:
        text = text.replace(
            "</head>",
            f'<link rel="stylesheet" href="assets/wave.css?v={asset_version}" />\n</head>',
            1,
        )
    if "assets/wave.js" not in text:
        text = text.replace(
            "</head>",
            f'<script defer src="assets/wave.js?v={asset_version}"></script>\n</head>',
            1,
        )

    match = re.search(r"<body>\s*(?P<body>.*?)\s*</body>", text, flags=re.S)
    if match is None or text.count("<body>") != 1 or text.count("</body>") != 1:
        raise SystemExit(f"HTML body boundaries are not unique in {path.name}")

    values = {
        "body": match.group("body"),
        "source_url": html.escape(REPOSITORY_URL, quote=True),
        "build_label": html.escape(info.label),
        "build_url": html.escape(info.commit_url, quote=True),
        **navigation_state(index),
        **reader_state(index),
    }
    shell = Template(HTML_TEMPLATE.read_text()).substitute(values)
    text = text[: match.start()] + "<body>\n" + shell + "\n</body>" + text[match.end() :]
    path.write_text(text)


def heading_text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def normalized_heading_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).translate(HEADING_TRANSLATION)
    return " ".join(normalized.split())


def install_stable_section_ids() -> None:
    heading_re = re.compile(r"<h2(?P<attrs>[^>]*)>(?P<body>.*?)</h2>", re.S | re.I)
    for chapter in book_structure():
        page = OUT / f"chapter{chapter.number}.html"
        text = page.read_text(errors="replace")
        index = 0

        def replace_heading(match: re.Match[str]) -> str:
            nonlocal index
            if index >= len(chapter.sections):
                return match.group(0)
            section = chapter.sections[index]
            rendered = heading_text(match.group("body"))
            if normalized_heading_text(rendered) != normalized_heading_text(section):
                raise SystemExit(
                    f"{page.name}: section heading {index + 1} is {rendered!r}; expected {section!r}"
                )
            index += 1
            attrs = re.sub(r'\s+id="[^"]*"', "", match.group("attrs"), flags=re.I)
            return f'<h2 id="{section_slug(section)}"{attrs}>{match.group("body")}</h2>'

        updated = heading_re.sub(replace_heading, text)
        if index != len(chapter.sections):
            raise SystemExit(
                f"{page.name}: found {index} section headings, expected {len(chapter.sections)}"
            )
        page.write_text(updated)


def build_index(source_dir: Path) -> None:
    page = OUT / "index.html"
    pandoc_page(source_dir / "frontmatter.tex", page, PUBLICATION_TITLE)
    text = page.read_text(errors="replace")
    text = text.replace("</body>", html_contents() + "\n" + html_license() + "\n</body>", 1)
    page.write_text(text)


def build_references(source_dir: Path) -> None:
    references = source_dir / "references.md"
    references.write_text(f"---\ntitle: References\nlang: {LANGUAGE}\nnocite: |\n  @*\n---\n")
    resource_path = os.pathsep.join((str(OUT), str(source_dir), str(RECON)))
    run(
        [
            "pandoc",
            str(references),
            "-s",
            "-t",
            "html5",
            "--citeproc",
            f"--bibliography={RECON / 'references.bib'}",
            "--resource-path",
            resource_path,
            "-o",
            str(OUT / "references.html"),
        ]
    )


def validate_local_references() -> None:
    pages = sorted(OUT.glob("*.html"))
    ids_by_page: dict[Path, set[str]] = {}
    broken: list[tuple[str, str]] = []
    optional_sibling_downloads = {name for name, _ in DOWNLOADS}

    def ids_for(path: Path) -> set[str]:
        if path not in ids_by_page:
            ids_by_page[path] = {
                html.unescape(value)
                for value in re.findall(
                    r'\bid=["\']([^"\']+)["\']',
                    path.read_text(errors="replace"),
                    flags=re.I,
                )
            }
        return ids_by_page[path]

    for page in pages:
        text = page.read_text(errors="replace")
        for attr in ("src", "href"):
            for raw_ref in re.findall(rf'{attr}=["\']([^"\']+)["\']', text, flags=re.I):
                ref = html.unescape(raw_ref)
                parsed = urllib.parse.urlsplit(ref)
                if parsed.scheme or parsed.netloc or ref.startswith(("mailto:", "javascript:", "data:")):
                    continue
                target = page if not parsed.path else page.parent / urllib.parse.unquote(parsed.path)
                if parsed.path and not target.exists():
                    if target.name in optional_sibling_downloads:
                        continue
                    broken.append((page.name, raw_ref))
                    continue
                if parsed.fragment and target.suffix.lower() in {".html", ".htm"} and target.is_file():
                    if urllib.parse.unquote(parsed.fragment) not in ids_for(target):
                        broken.append((page.name, raw_ref))
    if broken:
        for page, ref in broken[:40]:
            print(f"broken local HTML reference: {page}: {ref}", file=sys.stderr)
        raise SystemExit(f"{len(broken)} broken local HTML reference(s)")


def validate() -> None:
    missing = [path.name for path in EXPECTED_PAGES if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise SystemExit("missing HTML outputs: " + ", ".join(missing))
    if not HTML_TEMPLATE.is_file() or HTML_TEMPLATE.stat().st_size == 0:
        raise SystemExit(f"missing HTML reader template: {HTML_TEMPLATE}")

    combined = "\n".join(path.read_text(errors="replace") for path in EXPECTED_PAGES)
    for sentinel in ("David C. Chapman", "Paola Malanotte-Rizzoli", "CC BY-NC-SA 4.0", "Apel"):
        if sentinel not in combined:
            raise SystemExit(f"HTML sentinel missing: {sentinel}")
    info = current_build()
    label = html.escape(info.label)
    url = html.escape(info.commit_url, quote=True)
    for page in EXPECTED_PAGES:
        text = page.read_text(errors="replace")
        if not re.search(rf'<html[^>]+lang="{re.escape(LANGUAGE)}"', text, flags=re.I):
            raise SystemExit(f"HTML language metadata missing from {page.name}")
        for required in (
            '<main id="main-content">',
            'class="skip-link"',
            'class="reader-header page-shell"',
            'class="book-nav"',
            'class="appearance-control"',
            'data-theme-select',
            'data-reader-context',
            'class="build-info"',
            '>Source</a>',
            "assets/wave.css",
            "assets/wave.js",
            label,
            url,
        ):
            if required not in text:
                raise SystemExit(f"HTML requirement {required!r} is missing from {page.name}")
        if text.count('class="build-info"') != 1:
            raise SystemExit(f"HTML build stamp count is not one in {page.name}")
        if 'class="book-context"' in text or 'class="theme-toggle"' in text:
            raise SystemExit(f"obsolete HTML header controls remain in {page.name}")

    for chapter in book_structure():
        text = (OUT / f"chapter{chapter.number}.html").read_text(errors="replace")
        if text.count("data-section-link=") != len(chapter.sections):
            raise SystemExit(
                f"chapter{chapter.number}.html: chapter contents count does not match source sections"
            )
        if 'class="chapter-title-block"' not in text:
            raise SystemExit(f"chapter{chapter.number}.html: chapter title block is missing")

    index = (OUT / "index.html").read_text(errors="replace")
    if 'id="contents"' not in index or "wave-motions.epub" not in index:
        raise SystemExit("HTML Contents/Downloads block is incomplete")
    if MATHJAX_URL not in combined:
        raise SystemExit("pinned MathJax URL is missing from generated HTML")
    validate_local_references()


def main() -> int:
    for command in ("pandoc", "latexmk", "lualatex", "pdftocairo", "pdftoppm", "pdfinfo"):
        require(command)
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(ASSETS, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for page in EXPECTED_PAGES:
        page.unlink(missing_ok=True)
    BUILD.mkdir(parents=True)
    ASSETS.mkdir(parents=True)
    prepare_assets(OUT, BUILD)
    source_dir = BUILD / "source"
    prepare_flowing_sources(source_dir, OUT)
    shutil.copy2(RECON / "styles" / "wave-html.css", ASSETS / "wave.css")
    shutil.copy2(RECON / "styles" / "wave-html.js", ASSETS / "wave.js")

    build_index(source_dir)
    for chapter in book_structure():
        page = OUT / f"chapter{chapter.number}.html"
        pandoc_page(
            source_dir / f"chapter{chapter.number}.tex",
            page,
            f"Chapter {chapter.number}",
        )
        mark_chapter_title_block(page)
    build_references(source_dir)
    for page in EXPECTED_PAGES:
        build_shell(page)
    install_stable_section_ids()
    validate()
    print("HTML build OK: index + 6 chapters + references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
