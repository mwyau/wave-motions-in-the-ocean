#!/usr/bin/env python3
"""Build the complete chapter-split modern HTML edition.

Pandoc supplies document body markup after shared publication preparation.
This script computes publication data and renders the maintained full-page
reader template in src/layout/wave-html.html.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tarfile
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from string import Template

from PIL import Image

from publication import (
    BOOK_TITLE,
    CONTACT_EMAIL,
    DOWNLOADS,
    LANGUAGE,
    MATHJAX_URL,
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
VENDOR_CACHE = ROOT / "build" / "html-vendor"
HTML_TEMPLATE = SRC / "layout" / "wave-html.html"
SOCIAL_PREVIEW_TEMPLATE = SRC / "layout" / "social-preview.tex"
COVER_SOURCE = SRC / "cover-modern.tex"
SOCIAL_PREVIEW = ASSETS / "social-preview.png"
LOCAL_MATHJAX_URL = "assets/mathjax/tex-chtml-full.js"
VENDOR_ARCHIVES = {
    "mathjax-3.2.2": (
        "https://codeload.github.com/mathjax/MathJax/tar.gz/"
        "600692ad9d3552cc25f85510d5797bc942ecc9f7"
    ),
    "source-serif-4.005": (
        "https://codeload.github.com/adobe-fonts/source-serif/tar.gz/"
        "2823e993c53fca27c5c8749f529b56a5a7c77b6b"
    ),
    "source-sans-3.052": (
        "https://codeload.github.com/adobe-fonts/source-sans/tar.gz/"
        "ed1808970eb3c7301c9a523bee26473ba0bb62fa"
    ),
}
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
MATHJAX_MATH_RE = re.compile(
    r'<span\b(?=[^>]*\bclass="math (?P<kind>inline|display)")[^>]*>.*?</span>',
    re.DOTALL | re.IGNORECASE,
)
MATHML_MATH_RE = re.compile(
    r"<math\b(?P<attrs>[^>]*)>.*?</math>",
    re.DOTALL | re.IGNORECASE,
)
MATHML_TEX_ANNOTATION_RE = re.compile(
    r'<annotation\b[^>]*\bencoding="application/x-tex"[^>]*>'
    r"(?P<tex>.*?)</annotation>",
    re.DOTALL | re.IGNORECASE,
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


def cached_vendor_archive(name: str, url: str) -> Path:
    VENDOR_CACHE.mkdir(parents=True, exist_ok=True)
    archive = VENDOR_CACHE / f"{name}.tar.gz"
    if archive.is_file() and archive.stat().st_size > 0:
        return archive

    temporary = archive.with_suffix(archive.suffix + ".part")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "wave-motions-html-builder"},
    )
    print(f"Fetching pinned HTML dependency: {name}", file=sys.stderr)
    try:
        with (
            urllib.request.urlopen(request, timeout=90) as response,
            temporary.open("wb") as destination,
        ):
            shutil.copyfileobj(response, destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise SystemExit(
            f"cannot fetch {name}; reuse build/html-vendor from a previous build "
            f"for an offline rebuild: {exc}"
        ) from exc
    if not temporary.is_file() or temporary.stat().st_size == 0:
        raise SystemExit(f"downloaded HTML dependency is empty: {name}")
    temporary.replace(archive)
    return archive


def copy_archive_file(archive: Path, member_path: str, destination: Path) -> None:
    suffix = "/" + member_path.lstrip("/")
    with tarfile.open(archive, "r:gz") as package:
        matches = [
            member
            for member in package.getmembers()
            if member.isfile() and member.name.endswith(suffix)
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"{archive.name}: expected one archive member {member_path!r}, "
                f"found {len(matches)}"
            )
        source = package.extractfile(matches[0])
        if source is None:
            raise SystemExit(f"cannot read {member_path!r} from {archive.name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)


def copy_archive_tree(archive: Path, member_dir: str, destination: Path) -> int:
    marker = "/" + member_dir.strip("/") + "/"
    count = 0
    with tarfile.open(archive, "r:gz") as package:
        for member in package.getmembers():
            if not member.isfile() or marker not in member.name:
                continue
            relative = member.name.split(marker, 1)[1]
            source = package.extractfile(member)
            if source is None:
                raise SystemExit(f"cannot read {member.name!r} from {archive.name}")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            count += 1
    if count == 0:
        raise SystemExit(f"{archive.name}: archive tree {member_dir!r} is empty")
    return count


def install_html_vendor_assets() -> None:
    archives = {
        name: cached_vendor_archive(name, url) for name, url in VENDOR_ARCHIVES.items()
    }

    mathjax = archives["mathjax-3.2.2"]
    mathjax_root = ASSETS / "mathjax"
    copy_archive_file(
        mathjax, "es5/tex-chtml-full.js", mathjax_root / "tex-chtml-full.js"
    )
    font_count = copy_archive_tree(
        mathjax,
        "es5/output/chtml/fonts/woff-v2",
        mathjax_root / "output" / "chtml" / "fonts" / "woff-v2",
    )
    if font_count < 20:
        raise SystemExit(
            f"MathJax font bundle is incomplete: found {font_count} WOFF files"
        )
    copy_archive_file(mathjax, "LICENSE", ASSETS / "licenses" / "MathJax-3.2.2.txt")

    serif = archives["source-serif-4.005"]
    copy_archive_file(
        serif,
        "WOFF2/VAR/SourceSerif4Variable-Roman.otf.woff2",
        ASSETS / "fonts" / "SourceSerif4Variable-Roman.otf.woff2",
    )
    copy_archive_file(
        serif,
        "WOFF2/VAR/SourceSerif4Variable-Italic.otf.woff2",
        ASSETS / "fonts" / "SourceSerif4Variable-Italic.otf.woff2",
    )
    copy_archive_file(
        serif, "LICENSE.md", ASSETS / "licenses" / "Source-Serif-4-OFL.txt"
    )

    sans = archives["source-sans-3.052"]
    copy_archive_file(
        sans,
        "WOFF2/VF/SourceSans3VF-Upright.otf.woff2",
        ASSETS / "fonts" / "SourceSans3VF-Upright.otf.woff2",
    )
    copy_archive_file(
        sans,
        "WOFF2/VF/SourceSans3VF-Italic.otf.woff2",
        ASSETS / "fonts" / "SourceSans3VF-Italic.otf.woff2",
    )
    copy_archive_file(sans, "LICENSE.md", ASSETS / "licenses" / "Source-Sans-3-OFL.txt")


def normalize_mathml_tex(text: str) -> str:
    """Apply compatibility changes only to generated MathML input."""
    return re.sub(r"\\ell(?![A-Za-z])", "{ℓ}", text)


def normalized_math_tex(text: str) -> str:
    """Normalize serialization-only whitespace for renderer-source comparisons."""
    return " ".join(html.unescape(text).split())


def mathjax_tex_source(markup: str, kind: str) -> str:
    opening, closing = (r"\(", r"\)") if kind == "inline" else (r"\[", r"\]")
    start = markup.find(opening)
    end = markup.rfind(closing)
    if start < 0 or end < start + len(opening):
        raise SystemExit(f"MathJax {kind} expression is missing TeX delimiters")
    return html.unescape(markup[start + len(opening) : end])


def mathml_tex_source(markup: str) -> str:
    annotation = MATHML_TEX_ANNOTATION_RE.search(markup)
    if annotation is None:
        raise SystemExit("MathML expression is missing application/x-tex annotation")
    return html.unescape(annotation.group("tex"))


def pandoc_page(
    source_tex: Path,
    output: Path,
    title: str,
    *,
    math_method: str = "mathjax",
) -> None:
    resource_path = os.pathsep.join((str(OUT), str(source_tex.parent), str(SRC)))
    if math_method == "mathjax":
        math_option = f"--mathjax={MATHJAX_URL}"
    elif math_method == "mathml":
        math_option = "--mathml"
    else:
        raise ValueError(f"unsupported HTML math method: {math_method}")
    run(
        [
            "pandoc",
            str(source_tex),
            "-f",
            "latex+smart",
            "-t",
            "html5",
            "-s",
            math_option,
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


def install_mathml_alternates(page: Path, mathml_page: Path) -> None:
    text = page.read_text(errors="replace")
    mathml_text = mathml_page.read_text(errors="replace")
    mathjax_matches = list(MATHJAX_MATH_RE.finditer(text))
    mathml_matches = list(MATHML_MATH_RE.finditer(mathml_text))
    if len(mathjax_matches) != len(mathml_matches):
        raise SystemExit(
            f"{page.name}: MathJax/MathML expression count differs: "
            f"{len(mathjax_matches)} != {len(mathml_matches)}"
        )

    chunks: list[str] = []
    cursor = 0
    for position, (mathjax, mathml) in enumerate(
        zip(mathjax_matches, mathml_matches, strict=True),
        start=1,
    ):
        kind = mathjax.group("kind").lower()
        display = re.search(
            r'\bdisplay="(?P<display>inline|block)"',
            mathml.group("attrs"),
            flags=re.IGNORECASE,
        )
        if display is None:
            raise SystemExit(
                f"{mathml_page.name}: MathML expression {position} has no display mode"
            )
        expected = "inline" if kind == "inline" else "block"
        if display.group("display").lower() != expected:
            raise SystemExit(
                f"{page.name}: expression {position} differs between MathJax "
                f"({kind}) and MathML ({display.group('display')})"
            )

        mathjax_source = normalized_math_tex(
            normalize_mathml_tex(mathjax_tex_source(mathjax.group(0), kind))
        )
        mathml_source = normalized_math_tex(mathml_tex_source(mathml.group(0)))
        if mathjax_source != mathml_source:
            raise SystemExit(
                f"{page.name}: expression {position} differs between MathJax and "
                f"MathML TeX sources: {mathjax_source!r} != {mathml_source!r}"
            )

        chunks.append(text[cursor : mathjax.start()])
        chunks.append(
            mathjax.group(0).replace(
                "<span",
                '<span data-math-renderer="mathjax"',
                1,
            )
        )
        chunks.append(
            f'<span data-math-renderer="mathml" '
            f'class="math {kind} mathml-alternate" hidden>{mathml.group(0)}</span>'
        )
        cursor = mathjax.end()
    chunks.append(text[cursor:])
    page.write_text("".join(chunks))


def dual_math_page(source_tex: Path, output: Path, title: str) -> None:
    mathml_page = BUILD / "mathml" / output.name
    mathml_source = BUILD / "mathml-source" / source_tex.name
    mathml_page.parent.mkdir(parents=True, exist_ok=True)
    mathml_source.parent.mkdir(parents=True, exist_ok=True)
    mathml_source.write_text(normalize_mathml_tex(source_tex.read_text()))
    pandoc_page(source_tex, output, title, math_method="mathjax")
    pandoc_page(mathml_source, mathml_page, title, math_method="mathml")
    install_mathml_alternates(output, mathml_page)


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
    source = source.replace("__WAVE_COVER_BLUE__", blue).replace(
        "__WAVE_COVER_PAPER__", paper
    )
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
            raise SystemExit(
                f"social preview is {image.size[0]}x{image.size[1]}, expected 1200x630"
            )


def page_metadata(path: Path) -> dict[str, str]:
    context = page_context(path)
    page_title = (
        BOOK_TITLE if path.name == "index.html" else f"{context} — {BOOK_TITLE}"
    )
    if path.name == "index.html":
        social_title = PUBLICATION_TITLE.replace("'", "’")
        page_url = f"{SITE_URL}/"
    else:
        social_title = f"{context} — {PUBLICATION_TITLE}".replace("'", "’")
        page_url = f"{SITE_URL}/{path.name}"
    image_url = f"{SITE_URL}/assets/social-preview.png"
    return {
        "language": html.escape(LANGUAGE, quote=True),
        "page_title": html.escape(page_title),
        "description": html.escape(SOCIAL_DESCRIPTION, quote=True),
        "social_title": html.escape(social_title, quote=True),
        "social_url": html.escape(page_url, quote=True),
        "social_image": html.escape(image_url, quote=True),
        "social_image_alt": html.escape(SOCIAL_IMAGE_ALT, quote=True),
        "mathjax_upstream": html.escape(MATHJAX_URL, quote=True),
        "mathjax_url": html.escape(LOCAL_MATHJAX_URL, quote=True),
    }


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
                f"index.html: front matter heading {index + 1} is {rendered!r}; "
                f"expected {expected!r}"
            )
        index += 1
        attrs = re.sub(r'\s+id="[^"]*"', "", match.group("attrs"), flags=re.IGNORECASE)
        return f'<h1 id="{anchor}"{attrs}>{match.group("body")}</h1>'

    tail = heading_re.sub(replace_heading, tail)
    if index != len(FRONTMATTER_SECTIONS):
        raise SystemExit(
            f"index.html: found {index} front matter headings, "
            f"expected {len(FRONTMATTER_SECTIONS)}"
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
        r"<h1(?P<attrs>[^>]*)>",
        text[title_end + len("</header>") :],
        re.IGNORECASE,
    )
    if heading is None:
        raise SystemExit(f"HTML chapter heading missing from {page.name}")
    absolute_start = title_end + len("</header>") + heading.start()
    absolute_end = title_end + len("</header>") + heading.end()
    attrs = re.sub(r'\s+id="[^"]*"', "", heading.group("attrs"), flags=re.IGNORECASE)
    opening = f'<h1 id="chapter-{chapter_number}"{attrs}>'
    page.write_text(text[:absolute_start] + opening + text[absolute_end:])


def build_shell(path: Path) -> None:
    generated = path.read_text(errors="replace")
    body_match = re.search(
        r"<body>\s*(?P<body>.*?)\s*</body>", generated, flags=re.DOTALL
    )
    head_match = re.search(r"<head>(?P<head>.*?)</head>", generated, flags=re.DOTALL)
    if (
        body_match is None
        or generated.count("<body>") != 1
        or generated.count("</body>") != 1
    ):
        raise SystemExit(f"HTML body boundaries are not unique in {path.name}")
    if (
        head_match is None
        or generated.count("<head>") != 1
        or generated.count("</head>") != 1
    ):
        raise SystemExit(f"HTML head boundaries are not unique in {path.name}")
    pandoc_styles = "\n".join(
        re.findall(r"<style>.*?</style>", head_match.group("head"), flags=re.DOTALL)
    )

    index = page_index(path)
    info = current_build()
    values = {
        "body": body_match.group("body"),
        "pandoc_styles": pandoc_styles,
        "asset_version": html.escape(info.short_sha, quote=True),
        "source_url": html.escape(source_url(index, info.sha), quote=True),
        "build_label": html.escape(info.label),
        "build_url": html.escape(info.commit_url, quote=True),
        "book_toc": book_toc(index),
        **page_metadata(path),
        **navigation_state(index),
        **reader_state(index),
    }
    path.write_text(Template(HTML_TEMPLATE.read_text()).substitute(values))


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
                    f"{page.name}: section heading {index + 1} is {rendered!r}; "
                    f"expected {section!r}"
                )
            index += 1
            attrs = re.sub(
                r'\s+id="[^"]*"', "", match.group("attrs"), flags=re.IGNORECASE
            )
            return f'<h2 id="{section_slug(section)}"{attrs}>{match.group("body")}</h2>'

        updated = heading_re.sub(replace_heading, text)
        if index != len(chapter.sections):
            raise SystemExit(
                f"{page.name}: found {index} section headings, "
                f"expected {len(chapter.sections)}"
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
        + f'<p>Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>'
        + "</section>"
    )


def build_index(source_dir: Path) -> None:
    page = OUT / "index.html"
    dual_math_page(source_dir / "frontmatter.tex", page, PUBLICATION_TITLE)
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
    if (
        not SOCIAL_PREVIEW_TEMPLATE.is_file()
        or SOCIAL_PREVIEW_TEMPLATE.stat().st_size == 0
    ):
        raise SystemExit(f"missing social preview template: {SOCIAL_PREVIEW_TEMPLATE}")
    if not SOCIAL_PREVIEW.is_file() or SOCIAL_PREVIEW.stat().st_size == 0:
        raise SystemExit("missing generated social preview image")
    if not (ASSETS / "mathjax" / "tex-chtml-full.js").is_file():
        raise SystemExit("missing bundled MathJax component")
    if (
        len(
            list(
                (ASSETS / "mathjax" / "output" / "chtml" / "fonts" / "woff-v2").glob(
                    "*.woff"
                )
            )
        )
        < 20
    ):
        raise SystemExit("bundled MathJax fonts are incomplete")
    for font in (
        "SourceSerif4Variable-Roman.otf.woff2",
        "SourceSerif4Variable-Italic.otf.woff2",
        "SourceSans3VF-Upright.otf.woff2",
        "SourceSans3VF-Italic.otf.woff2",
    ):
        if not (ASSETS / "fonts" / font).is_file():
            raise SystemExit(f"missing bundled HTML font: {font}")
    with Image.open(SOCIAL_PREVIEW) as image:
        if image.size != (1200, 630):
            raise SystemExit(
                f"social preview is {image.size[0]}x{image.size[1]}, expected 1200x630"
            )

    combined = "\n".join(path.read_text(errors="replace") for path in EXPECTED_PAGES)
    for sentinel in (
        "David C. Chapman",
        "Paola Malanotte-Rizzoli",
        "CC BY-NC-SA 4.0",
        "Apel",
    ):
        if sentinel not in combined:
            raise SystemExit(f"HTML sentinel missing: {sentinel}")
    if re.search(r"<mo\b[^>]*>ℓ</mo>", combined):
        raise SystemExit(
            "HTML native MathML represents ℓ as an operator instead of an identifier"
        )
    if not re.search(r"<mi\b[^>]*>ℓ</mi>", combined):
        raise SystemExit("HTML native MathML is missing identifier-form ℓ")
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
        if text.count("<head>") != 1 or text.count("</head>") != 1:
            raise SystemExit(f"HTML head boundaries are not unique in {page.name}")
        if text.count("<body>") != 1 or text.count("</body>") != 1:
            raise SystemExit(f"HTML body boundaries are not unique in {page.name}")
        for required in (
            "<!DOCTYPE html>",
            '<meta charset="utf-8">',
            'name="viewport"',
            'rel="icon"',
            "🌊",
            '<main id="main-content">',
            'class="skip-link"',
            'class="reader-header page-shell"',
            'class="book-nav"',
            "data-theme-cycle",
            "data-dev-math-controls",
            'data-math-mode="mathjax"',
            'data-math-mode="mathml"',
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
            'name="mathjax-upstream"',
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
        mathjax_count = text.count('data-math-renderer="mathjax"')
        mathml_count = text.count('data-math-renderer="mathml"')
        if mathjax_count != mathml_count:
            raise SystemExit(
                f"{page.name}: MathJax/MathML alternate count differs: "
                f"{mathjax_count} != {mathml_count}"
            )
        if page.name.startswith("chapter") and mathjax_count == 0:
            raise SystemExit(f"{page.name}: no dual-rendered mathematics found")
        if text.count("<math ") != mathml_count:
            raise SystemExit(
                f"{page.name}: native MathML element count does not match alternates"
            )
        if text.count('encoding="application/x-tex"') != mathml_count:
            raise SystemExit(
                f"{page.name}: native MathML TeX annotation count does not match alternates"
            )
        if text.count("data-toc-scope") != 2 or text.count("data-toc-expand") != 2:
            raise SystemExit(
                f"HTML Contents controls are duplicated or missing in {page.name}"
            )
        if text.count('class="build-info"') != 1:
            raise SystemExit(f"HTML build stamp count is not one in {page.name}")
        if text.count('property="og:image"') != 1:
            raise SystemExit(
                f"HTML social preview image metadata count is not one in {page.name}"
            )
        if 'class="book-context"' in text or "data-theme-select" in text:
            raise SystemExit(f"obsolete HTML header controls remain in {page.name}")

    for chapter in CHAPTERS:
        text = (OUT / f"chapter{chapter.number}.html").read_text(errors="replace")
        if text.count("data-section-link=") != 2 * len(chapter.sections):
            raise SystemExit(
                f"chapter{chapter.number}.html: active chapter contents count "
                "does not match source sections"
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
    if "Original online source" in index:
        raise SystemExit("HTML front page must not link the original online source")
    if 'id="contents"' in index:
        raise SystemExit("inline HTML Contents block must not be rendered")
    if f'href="chapter{first.number}.html"' not in index:
        raise SystemExit(
            f"front matter must navigate forward to Chapter {first.number}"
        )
    first_page = (OUT / f"chapter{first.number}.html").read_text(errors="replace")
    if 'href="index.html"' not in first_page:
        raise SystemExit(f"Chapter {first.number} must navigate back to front matter")
    references = (OUT / "references.html").read_text(errors="replace")
    if f'href="chapter{last.number}.html"' not in references:
        raise SystemExit(f"References must navigate back to Chapter {last.number}")
    if MATHJAX_URL not in combined:
        raise SystemExit("pinned MathJax URL is missing from generated HTML")
    if LOCAL_MATHJAX_URL not in combined:
        raise SystemExit("local MathJax component is missing from generated HTML")
    if 'data-math-renderer="mathml"' not in combined or "<math " not in combined:
        raise SystemExit("native MathML alternates are missing from generated HTML")
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
    install_html_vendor_assets()
    source_dir = BUILD / "source"
    prepare_flowing_sources(source_dir, OUT)
    shutil.copy2(SRC / "layout" / "wave-html.css", ASSETS / "wave.css")
    with (ASSETS / "wave.css").open("a", encoding="utf-8") as stylesheet:
        stylesheet.write("\n")
        stylesheet.write((SRC / "layout" / "wave-fonts.css").read_text())
    shutil.copy2(SRC / "layout" / "wave-html.js", ASSETS / "wave.js")
    build_social_preview()

    build_index(source_dir)
    for chapter in CHAPTERS:
        page = OUT / f"chapter{chapter.number}.html"
        dual_math_page(
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
