#!/usr/bin/env python3
"""Build the complete chapter-split modern HTML edition.

Pandoc supplies the document markup after the shared publication
preparation. This script owns dynamic publication data and final assembly; the
maintained reader shell lives in src/templates/wave-html.html.
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

from PIL import Image

from publication import (
    BOOK_TITLE,
    CONTACT_EMAIL,
    DOWNLOADS,
    LANGUAGE,
    MATHJAX_URL,
    ORIGINAL_SOURCE_URL,
    PUBLICATION_TITLE,
    REPOSITORY_URL,
    SITE_URL,
    book_structure,
    current_build,
    html_license,
    prepare_assets,
    prepare_flowing_sources,
    section_slug,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD = ROOT / "build" / "html-pandoc"
OUT = ROOT / "dist"
ASSETS = OUT / "assets"
HTML_TEMPLATE = SRC / "templates" / "wave-html.html"
SOCIAL_PREVIEW_TEMPLATE = SRC / "templates" / "social-preview.tex"
COVER_SOURCE = SRC / "cover-modern.tex"
SOCIAL_PREVIEW = ASSETS / "social-preview.png"
SOCIAL_DESCRIPTION = (
    "Digital edition of Wave Motions in the Ocean: Myrl’s View by David C. Chapman "
    "and Paola Malanotte-Rizzoli, edited by Albert M. W. Yau."
)
SOCIAL_IMAGE_ALT = (
    "Wave Motions in the Ocean: Myrl’s View, by David C. Chapman and "
    "Paola Malanotte-Rizzoli, edited by Albert M. W. Yau."
)
CHAPTERS = book_structure()
if not CHAPTERS:
    raise SystemExit("book structure has no chapters")
CHAPTER_BY_NUMBER = {chapter.number: chapter for chapter in CHAPTERS}
if len(CHAPTER_BY_NUMBER) != len(CHAPTERS):
    raise SystemExit("book structure contains duplicate chapter numbers")
CHAPTER_POSITION = {
    chapter.number: position for position, chapter in enumerate(CHAPTERS)
}
CHAPTER_PAGE_RE = re.compile(r"chapter(?P<number>\d+)\.html")
EXPECTED_PAGES = [
    OUT / "index.html",
    *(OUT / f"chapter{chapter.number}.html" for chapter in CHAPTERS),
    OUT / "references.html",
]
HTML_DOWNLOADS = tuple(
    item for item in DOWNLOADS if item[0] != "wave-motions-facsimile.pdf"
)
FRONTMATTER_SECTIONS = (
    ("preface-david-c-chapman", "Preface — David C. Chapman"),
    ("preface-paola-malanotte-rizzoli", "Preface — Paola Malanotte-Rizzoli"),
    ("editors-note", "Editor's note"),
)
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
    resource_path = os.pathsep.join((str(OUT), str(source_tex.parent), str(SRC)))
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


def chapter_for_page(path: Path):
    match = CHAPTER_PAGE_RE.fullmatch(path.name)
    if match is None:
        return None
    return CHAPTER_BY_NUMBER.get(int(match.group("number")))


def page_context(path: Path) -> str:
    if path.name == "index.html":
        return "Front matter"
    if path.name == "references.html":
        return "References"
    chapter = chapter_for_page(path)
    if chapter is not None:
        return f"Chapter {chapter.number} · {chapter.title}"
    raise ValueError(f"unexpected publication page: {path.name}")


def page_index(path: Path) -> int | None:
    if path.name == "index.html":
        return None
    if path.name == "references.html":
        return 0
    chapter = chapter_for_page(path)
    if chapter is None:
        raise ValueError(f"unexpected publication page: {path.name}")
    return chapter.number


def navigation_state(index: int | None) -> dict[str, str]:
    previous_url = ""
    previous_label = ""
    next_url = ""
    next_label = ""

    if index is None:
        first = CHAPTERS[0]
        next_url = f"chapter{first.number}.html"
        next_label = f"Chapter {first.number}"
    elif index == 0:
        last = CHAPTERS[-1]
        previous_url = f"chapter{last.number}.html"
        previous_label = f"Chapter {last.number}"
    else:
        position = CHAPTER_POSITION.get(index)
        if position is None:
            raise ValueError(f"unexpected chapter number: {index}")
        if position == 0:
            previous_url = "index.html"
            previous_label = "Front matter"
        else:
            previous = CHAPTERS[position - 1]
            previous_url = f"chapter{previous.number}.html"
            previous_label = f"Chapter {previous.number}"
        if position + 1 < len(CHAPTERS):
            next_chapter = CHAPTERS[position + 1]
            next_url = f"chapter{next_chapter.number}.html"
            next_label = f"Chapter {next_chapter.number}"
        else:
            next_url = "references.html"
            next_label = "References"

    return {
        "previous_url": html.escape(previous_url, quote=True),
        "previous_label": html.escape(previous_label),
        "previous_hidden": "" if previous_url else " hidden",
        "next_url": html.escape(next_url, quote=True),
        "next_label": html.escape(next_label),
        "next_hidden": "" if next_url else " hidden",
    }


def reader_state(index: int | None) -> dict[str, str]:
    if index is None:
        return {
            "reader_chapter": "Front matter",
            "reader_title": "",
            "reader_title_hidden": " hidden",
        }
    if index == 0:
        return {
            "reader_chapter": "References",
            "reader_title": "",
            "reader_title_hidden": " hidden",
        }

    chapter = CHAPTER_BY_NUMBER.get(index)
    if chapter is None:
        raise ValueError(f"unexpected chapter number: {index}")
    return {
        "reader_chapter": f"Chapter {chapter.number}",
        "reader_title": html.escape(chapter.title),
        "reader_title_hidden": "",
    }


def book_toc(index: int | None) -> str:
    def current_page(active: bool) -> str:
        return ' class="is-current" aria-current="page"' if active else ""

    front_sections = "".join(
        f'<li><a href="index.html#{anchor}"'
        + (f' data-section-link="{anchor}"' if index is None else "")
        + f">{html.escape(title)}</a></li>"
        for anchor, title in FRONTMATTER_SECTIONS
    )
    items = [
        '<li class="book-toc-page">'
        + f'<details class="book-toc-group"{" open" if index is None else ""}>'
        + '<summary><a href="index.html"'
        + current_page(index is None)
        + ">Front matter</a></summary>"
        + f"<ol>{front_sections}</ol></details></li>"
    ]

    for chapter in CHAPTERS:
        active = index == chapter.number
        sections = "".join(
            f'<li><a href="chapter{chapter.number}.html#{section_slug(section)}"'
            + (f' data-section-link="{section_slug(section)}"' if active else "")
            + f">{html.escape(section)}</a></li>"
            for section in chapter.sections
        )
        items.append(
            '<li class="book-toc-page">'
            + f'<details class="book-toc-group"{" open" if active else ""}>'
            + f'<summary><a href="chapter{chapter.number}.html#chapter-{chapter.number}"'
            + current_page(active)
            + f">{chapter.number} · {html.escape(chapter.title)}</a></summary>"
            + f"<ol>{sections}</ol></details></li>"
        )

    items.append(
        '<li class="book-toc-page"><a href="references.html"'
        + current_page(index == 0)
        + ">References</a></li>"
    )
    return '<ol class="book-toc-list">' + "".join(items) + "</ol>"


def source_url(index: int | None, sha: str) -> str:
    if index is None:
        source_path = "src/frontmatter-modern.tex"
    elif index == 0:
        source_path = "src/references.bib"
    else:
        source_path = f"src/chapter{index}.tex"
    revision = sha if sha != "unknown" else "main"
    return f"{REPOSITORY_URL}/blob/{revision}/{source_path}"


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


def cover_palette() -> tuple[str, str]:
    source = COVER_SOURCE.read_text()

    def color(name: str) -> str:
        match = re.search(
            rf"\\definecolor\{{{re.escape(name)}\}}\{{HTML\}}\{{([0-9A-Fa-f]{{6}})\}}",
            source,
        )
        if match is None:
            raise SystemExit(f"cover color {name} is missing from {COVER_SOURCE}")
        return match.group(1).upper()

    return color("WaveCoverBlue"), color("WaveCoverPaper")


def build_social_preview() -> None:
    if not SOCIAL_PREVIEW_TEMPLATE.is_file():
        raise SystemExit(f"missing social preview template: {SOCIAL_PREVIEW_TEMPLATE}")
    blue, paper = cover_palette()
    work = BUILD / "social-preview"
    work.mkdir(parents=True, exist_ok=True)
    source = SOCIAL_PREVIEW_TEMPLATE.read_text()
    source = source.replace("__WAVE_COVER_BLUE__", blue).replace("__WAVE_COVER_PAPER__", paper)
    tex = work / "social-preview.tex"
    tex.write_text(source)
    run(
        [
            "lualatex",
            "-interaction=batchmode",
            "-halt-on-error",
            f"-output-directory={work}",
            str(tex),
        ],
        cwd=ROOT,
    )
    pdf = work / "social-preview.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise SystemExit("social preview PDF was not generated")
    run(
        [
            "pdftoppm",
            "-f",
            "1",
            "-singlefile",
            "-png",
            "-r",
            "72",
            str(pdf),
            str(ASSETS / "social-preview"),
        ]
    )
    if not SOCIAL_PREVIEW.is_file() or SOCIAL_PREVIEW.stat().st_size == 0:
        raise SystemExit("social preview PNG was not generated")
    with Image.open(SOCIAL_PREVIEW) as image:
        if image.size != (1200, 630):
            raise SystemExit(f"social preview is {image.size[0]}x{image.size[1]}, expected 1200x630")


def social_metadata(path: Path) -> str:
    if path.name == "index.html":
        title = PUBLICATION_TITLE.replace("'", "’")
        page_url = f"{SITE_URL}/"
    else:
        title = f"{page_context(path)} — {PUBLICATION_TITLE}".replace("'", "’")
        page_url = f"{SITE_URL}/{path.name}"
    image_url = f"{SITE_URL}/assets/social-preview.png"
    values = {
        "title": html.escape(title, quote=True),
        "description": html.escape(SOCIAL_DESCRIPTION, quote=True),
        "url": html.escape(page_url, quote=True),
        "image": html.escape(image_url, quote=True),
        "image_alt": html.escape(SOCIAL_IMAGE_ALT, quote=True),
    }
    return "\n".join(
        (
            f'<meta name="description" content="{values["description"]}" />',
            f'<meta property="og:title" content="{values["title"]}" />',
            '<meta property="og:type" content="website" />',
            f'<meta property="og:url" content="{values["url"]}" />',
            f'<meta property="og:image" content="{values["image"]}" />',
            '<meta property="og:image:width" content="1200" />',
            '<meta property="og:image:height" content="630" />',
            '<meta property="og:image:type" content="image/png" />',
            f'<meta property="og:image:alt" content="{values["image_alt"]}" />',
            '<meta name="twitter:card" content="summary_large_image" />',
            f'<meta name="twitter:title" content="{values["title"]}" />',
            f'<meta name="twitter:description" content="{values["description"]}" />',
            f'<meta name="twitter:image" content="{values["image"]}" />',
            f'<meta name="twitter:image:alt" content="{values["image_alt"]}" />',
        )
    )


def heading_text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def normalized_heading_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).translate(HEADING_TRANSLATION)
    return " ".join(normalized.split())


def install_frontmatter_ids(page: Path) -> None:
    text = page.read_text(errors="replace")
    title_end = text.find("</header>")
    if title_end < 0:
        raise SystemExit("HTML front matter title block is missing")
    prefix = text[: title_end + len("</header>")]
    tail = text[title_end + len("</header>") :]
    heading_re = re.compile(
        r"<h1(?P<attrs>[^>]*)>(?P<body>.*?)</h1>", re.DOTALL | re.IGNORECASE
    )
    index = 0

    def replace_heading(match: re.Match[str]) -> str:
        nonlocal index
        if index >= len(FRONTMATTER_SECTIONS):
            return match.group(0)
        anchor, expected = FRONTMATTER_SECTIONS[index]
        rendered = heading_text(match.group("body"))
        if normalized_heading_text(rendered) != normalized_heading_text(expected):
            raise SystemExit(
                f"index.html: front matter heading {index + 1} is {rendered!r}; expected {expected!r}"
            )
        index += 1
        attrs = re.sub(r'\s+id="[^"]*"', "", match.group("attrs"), flags=re.IGNORECASE)
        return f'<h1 id="{anchor}"{attrs}>{match.group("body")}</h1>'

    tail = heading_re.sub(replace_heading, tail)
    if index != len(FRONTMATTER_SECTIONS):
        raise SystemExit(
            f"index.html: found {index} front matter headings, expected {len(FRONTMATTER_SECTIONS)}"
        )
    page.write_text(prefix + tail)


def install_chapter_id(page: Path, chapter_number: int) -> None:
    text = page.read_text(errors="replace")
    marker = '<header id="title-block-header" class="chapter-title-block">'
    title_start = text.find(marker)
    title_end = text.find("</header>", title_start)
    if title_start < 0 or title_end < 0:
        raise SystemExit(f"HTML chapter title block missing from {page.name}")
    heading = re.search(
        r"<h1(?P<attrs>[^>]*)>", text[title_end + len("</header>") :], re.IGNORECASE
    )
    if heading is None:
        raise SystemExit(f"HTML chapter heading missing from {page.name}")
    absolute_start = title_end + len("</header>") + heading.start()
    absolute_end = title_end + len("</header>") + heading.end()
    attrs = re.sub(r'\s+id="[^"]*"', "", heading.group("attrs"), flags=re.IGNORECASE)
    opening = f'<h1 id="chapter-{chapter_number}"{attrs}>'
    page.write_text(text[:absolute_start] + opening + text[absolute_end:])


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
        flags=re.DOTALL,
    )

    if 'property="og:image"' in text or 'name="twitter:card"' in text:
        raise SystemExit(f"social metadata already exists in {path.name}")
    text = text.replace("</head>", social_metadata(path) + "\n</head>", 1)

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

    match = re.search(r"<body>\s*(?P<body>.*?)\s*</body>", text, flags=re.DOTALL)
    if match is None or text.count("<body>") != 1 or text.count("</body>") != 1:
        raise SystemExit(f"HTML body boundaries are not unique in {path.name}")

    values = {
        "body": match.group("body"),
        "source_url": html.escape(source_url(index, info.sha), quote=True),
        "build_label": html.escape(info.label),
        "build_url": html.escape(info.commit_url, quote=True),
        "book_toc": book_toc(index),
        **navigation_state(index),
        **reader_state(index),
    }
    shell = Template(HTML_TEMPLATE.read_text()).substitute(values)
    text = (
        text[: match.start()] + "<body>\n" + shell + "\n</body>" + text[match.end() :]
    )
    path.write_text(text)


def install_stable_section_ids() -> None:
    heading_re = re.compile(
        r"<h2(?P<attrs>[^>]*)>(?P<body>.*?)</h2>", re.DOTALL | re.IGNORECASE
    )
    for chapter in CHAPTERS:
        page = OUT / f"chapter{chapter.number}.html"
        text = page.read_text(errors="replace")
        index = 0

        def replace_heading(match: re.Match[str], chapter=chapter, page=page) -> str:
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
            attrs = re.sub(
                r'\s+id="[^"]*"', "", match.group("attrs"), flags=re.IGNORECASE
            )
            return f'<h2 id="{section_slug(section)}"{attrs}>{match.group("body")}</h2>'

        updated = heading_re.sub(replace_heading, text)
        if index != len(chapter.sections):
            raise SystemExit(
                f"{page.name}: found {index} section headings, expected {len(chapter.sections)}"
            )
        page.write_text(updated)


def html_frontmatter_footer() -> str:
    links = "".join(
        f'<li><a href="{filename}">{html.escape(label)}</a></li>'
        for filename, label in HTML_DOWNLOADS
    )
    return (
        '<section class="edition-links"><h2>Read and download</h2><ul>'
        + links
        + "</ul>"
        + f'<p><a href="{ORIGINAL_SOURCE_URL}">Original online source</a></p>'
        + f'<p>Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>'
        + "</section>"
    )


def build_index(source_dir: Path) -> None:
    page = OUT / "index.html"
    pandoc_page(source_dir / "frontmatter.tex", page, PUBLICATION_TITLE)
    text = page.read_text(errors="replace")
    text = text.replace(
        "</body>",
        html_frontmatter_footer() + "\n" + html_license() + "\n</body>",
        1,
    )
    page.write_text(text)
    install_frontmatter_ids(page)


def build_references(source_dir: Path) -> None:
    references = source_dir / "references.md"
    references.write_text(
        f"---\ntitle: References\nlang: {LANGUAGE}\nnocite: |\n  @*\n---\n"
    )
    resource_path = os.pathsep.join((str(OUT), str(source_dir), str(SRC)))
    run(
        [
            "pandoc",
            str(references),
            "-s",
            "-t",
            "html5",
            "--citeproc",
            f"--bibliography={SRC / 'references.bib'}",
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
    optional_sibling_downloads = {name for name, _ in HTML_DOWNLOADS}

    def ids_for(path: Path) -> set[str]:
        if path not in ids_by_page:
            ids_by_page[path] = {
                html.unescape(value)
                for value in re.findall(
                    r'\bid=["\']([^"\']+)["\']',
                    path.read_text(errors="replace"),
                    flags=re.IGNORECASE,
                )
            }
        return ids_by_page[path]

    for page in pages:
        text = page.read_text(errors="replace")
        for attr in ("src", "href"):
            for raw_ref in re.findall(
                rf'{attr}=["\']([^"\']+)["\']', text, flags=re.IGNORECASE
            ):
                ref = html.unescape(raw_ref)
                parsed = urllib.parse.urlsplit(ref)
                if (
                    parsed.scheme
                    or parsed.netloc
                    or ref.startswith(("mailto:", "javascript:", "data:"))
                ):
                    continue
                target = (
                    page
                    if not parsed.path
                    else page.parent / urllib.parse.unquote(parsed.path)
                )
                if parsed.path and not target.exists():
                    if target.name in optional_sibling_downloads:
                        continue
                    broken.append((page.name, raw_ref))
                    continue
                if (
                    parsed.fragment
                    and target.suffix.lower() in {".html", ".htm"}
                    and target.is_file()
                    and urllib.parse.unquote(parsed.fragment) not in ids_for(target)
                ):
                    broken.append((page.name, raw_ref))
    if broken:
        for page, ref in broken[:40]:
            print(f"broken local HTML reference: {page}: {ref}", file=sys.stderr)
        raise SystemExit(f"{len(broken)} broken local HTML reference(s)")


def validate() -> None:
    missing = [
        path.name
        for path in EXPECTED_PAGES
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise SystemExit("missing HTML outputs: " + ", ".join(missing))
    if not HTML_TEMPLATE.is_file() or HTML_TEMPLATE.stat().st_size == 0:
        raise SystemExit(f"missing HTML reader template: {HTML_TEMPLATE}")
    if not SOCIAL_PREVIEW_TEMPLATE.is_file() or SOCIAL_PREVIEW_TEMPLATE.stat().st_size == 0:
        raise SystemExit(f"missing social preview template: {SOCIAL_PREVIEW_TEMPLATE}")
    if not SOCIAL_PREVIEW.is_file() or SOCIAL_PREVIEW.stat().st_size == 0:
        raise SystemExit("missing generated social preview image")
    with Image.open(SOCIAL_PREVIEW) as image:
        if image.size != (1200, 630):
            raise SystemExit(f"social preview is {image.size[0]}x{image.size[1]}, expected 1200x630")

    combined = "\n".join(path.read_text(errors="replace") for path in EXPECTED_PAGES)
    for sentinel in (
        "David C. Chapman",
        "Paola Malanotte-Rizzoli",
        "CC BY-NC-SA 4.0",
        "Apel",
    ):
        if sentinel not in combined:
            raise SystemExit(f"HTML sentinel missing: {sentinel}")
    info = current_build()
    label = html.escape(info.label)
    build_url = html.escape(info.commit_url, quote=True)
    for page in EXPECTED_PAGES:
        text = page.read_text(errors="replace")
        index = page_index(page)
        if not re.search(
            rf'<html[^>]+lang="{re.escape(LANGUAGE)}"', text, flags=re.IGNORECASE
        ):
            raise SystemExit(f"HTML language metadata missing from {page.name}")
        for required in (
            '<main id="main-content">',
            'class="skip-link"',
            'class="reader-header page-shell"',
            'class="book-nav"',
            "data-theme-cycle",
            "data-reader-context",
            "data-book-toc-rail",
            "data-toc-scope",
            "data-toc-expand",
            'class="book-contents-rail"',
            'class="book-contents-popover"',
            'class="build-info"',
            ">Source</a>",
            "Front matter",
            "References",
            "assets/wave.css",
            "assets/wave.js",
            'property="og:title"',
            'property="og:url"',
            'property="og:image"',
            'property="og:image:width" content="1200"',
            'property="og:image:height" content="630"',
            'name="twitter:card" content="summary_large_image"',
            f"{SITE_URL}/assets/social-preview.png",
            label,
            build_url,
            html.escape(source_url(index, info.sha), quote=True),
        ):
            if required not in text:
                raise SystemExit(
                    f"HTML requirement {required!r} is missing from {page.name}"
                )
        if text.count("data-toc-scope") != 2 or text.count("data-toc-expand") != 2:
            raise SystemExit(f"HTML Contents controls are duplicated or missing in {page.name}")
        if text.count('class="build-info"') != 1:
            raise SystemExit(f"HTML build stamp count is not one in {page.name}")
        if text.count('property="og:image"') != 1:
            raise SystemExit(f"HTML social preview image metadata count is not one in {page.name}")
        if 'class="book-context"' in text or 'data-theme-select' in text:
            raise SystemExit(f"obsolete HTML header controls remain in {page.name}")

    for chapter in CHAPTERS:
        text = (OUT / f"chapter{chapter.number}.html").read_text(errors="replace")
        if text.count("data-section-link=") != 2 * len(chapter.sections):
            raise SystemExit(
                f"chapter{chapter.number}.html: active chapter contents count does not match source sections"
            )
        if f'id="chapter-{chapter.number}"' not in text:
            raise SystemExit(
                f"chapter{chapter.number}.html: stable chapter anchor is missing"
            )
        if 'class="chapter-title-block"' not in text:
            raise SystemExit(
                f"chapter{chapter.number}.html: chapter title block is missing"
            )

    first = CHAPTERS[0]
    last = CHAPTERS[-1]
    index = (OUT / "index.html").read_text(errors="replace")
    for anchor, _ in FRONTMATTER_SECTIONS:
        if f'id="{anchor}"' not in index:
            raise SystemExit(f"HTML front matter anchor {anchor!r} is missing")
    if "wave-motions.pdf" not in index or "wave-motions.epub" not in index:
        raise SystemExit("HTML download links are incomplete")
    if "wave-motions-facsimile.pdf" in index:
        raise SystemExit("HTML front page must not link the facsimile PDF")
    if 'id="contents"' in index:
        raise SystemExit("inline HTML Contents block must not be rendered")
    if f'href="chapter{first.number}.html"' not in index:
        raise SystemExit(
            f"front matter must navigate forward to Chapter {first.number}"
        )
    first_page = (OUT / f"chapter{first.number}.html").read_text(errors="replace")
    if 'href="index.html"' not in first_page:
        raise SystemExit(
            f"Chapter {first.number} must navigate back to front matter"
        )
    references = (OUT / "references.html").read_text(errors="replace")
    if f'href="chapter{last.number}.html"' not in references:
        raise SystemExit(
            f"References must navigate back to Chapter {last.number}"
        )
    if MATHJAX_URL not in combined:
        raise SystemExit("pinned MathJax URL is missing from generated HTML")
    validate_local_references()


def main() -> int:
    for command in (
        "pandoc",
        "latexmk",
        "lualatex",
        "pdftocairo",
        "pdftoppm",
        "pdfinfo",
    ):
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
    shutil.copy2(SRC / "styles" / "wave-html.css", ASSETS / "wave.css")
    shutil.copy2(SRC / "styles" / "wave-html.js", ASSETS / "wave.js")
    build_social_preview()

    build_index(source_dir)
    for chapter in CHAPTERS:
        page = OUT / f"chapter{chapter.number}.html"
        pandoc_page(
            source_dir / f"chapter{chapter.number}.tex",
            page,
            f"Chapter {chapter.number}",
        )
        mark_chapter_title_block(page)
        install_chapter_id(page, chapter.number)
    build_references(source_dir)
    for page in EXPECTED_PAGES:
        build_shell(page)
    install_stable_section_ids()
    validate()
    print(
        f"HTML build OK: front matter + {len(CHAPTERS)} chapters + "
        "references + social preview"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
