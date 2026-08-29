#!/usr/bin/env python3
"""Build the complete chapter-split modern HTML edition.

Pandoc renders each final HTML page through the maintained reader template in
``src/layout/wave-html.html`` after shared publication preparation.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from PIL import Image

from publication import (
    AUTHORS,
    BOOK_TITLE,
    CACHE,
    CONTACT_EMAIL,
    DOI_URL,
    DOWNLOADS,
    EDITOR,
    LANGUAGE,
    LICENSE_URL,
    MATHJAX_URL,
    ONLINE_PUBLICATION_YEAR,
    PUBLICATION_TITLE,
    PUBLICATION_YEAR,
    REPOSITORY_URL,
    SITE_URL,
    book_structure,
    current_build,
    html_license,
    page_switchable_figure_stems,
    prepare_assets,
    prepare_flowing_sources,
    reader_punctuation,
    section_slug,
)
from webapp import (
    APPLE_TOUCH_ICON_PATH,
    ARTWORK_ASSET_PATHS,
    SERVICE_WORKER_FILENAME,
    WEB_MANIFEST_FILENAME,
    all_reader_resources,
    offline_reader_resource_stats,
    offline_reader_resources,
    prepare_application_icons,
    service_worker_text,
    validate_application_icons,
    web_app_manifest,
    write_service_worker,
    write_web_app_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD = ROOT / "build" / "html-pandoc"
OUT = ROOT / "release"
ASSETS = OUT / "assets"
VENDOR_CACHE = CACHE / "html-vendor"
HTML_TEMPLATE = SRC / "layout" / "wave-html.html"
AMS_CSL = SRC / "layout" / "wave-ams.csl"
SOCIAL_PREVIEW_TEMPLATE = SRC / "layout" / "social-preview.tex"
COVER_SOURCE = SRC / "cover-modern.tex"
SOCIAL_PREVIEW = ASSETS / "social-preview.png"
SITEMAP = OUT / "sitemap.xml"
WEB_MANIFEST = OUT / WEB_MANIFEST_FILENAME
SERVICE_WORKER = OUT / SERVICE_WORKER_FILENAME
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
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
MODERN_PDF_FILENAME = next(
    filename for filename, label in HTML_DOWNLOADS if label == "PDF"
)
FRONTMATTER_SECTIONS = (
    ("preface-david-c-chapman", "Preface — David C. Chapman"),
    ("preface-paola-malanotte-rizzoli", "Preface — Paola Malanotte-Rizzoli"),
    ("editors-note", "Editor's note"),
)
FRONTMATTER_TITLE_BLOCK_RE = re.compile(
    r'(?P<open><div class="center">\s*)'
    r"<p>\s*<strong>.*?</strong>\s*</p>\s*"
    r"<p>\s*<em>.*?</em>\s*</p>\s*",
    re.DOTALL | re.IGNORECASE,
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
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
MATHML_TAG = f"{{{MATHML_NS}}}"
BOUNDARY_TEXT_RE = re.compile(r"^(?:at|as)\b", re.IGNORECASE)
ALIGNED_ANNOTATION_RE = re.compile(r"\\begin\{aligned\}")
ET.register_namespace("", MATHML_NS)


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
            f"cannot fetch {name}; reuse {VENDOR_CACHE} from a previous build "
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


def _empty_mathml_cell(cell: ET.Element) -> bool:
    return not "".join(cell.itertext()).strip()


def _boundary_mathml_cell(cell: ET.Element) -> bool:
    for node in cell.iter(f"{MATHML_TAG}mtext"):
        text = " ".join("".join(node.itertext()).split())
        if BOUNDARY_TEXT_RE.match(text):
            return True
    return False


def _mathml_annotation_text(root: ET.Element) -> str:
    return " ".join(
        " ".join("".join(node.itertext()).split())
        for node in root.findall(f".//{MATHML_TAG}annotation")
    )


def _aligned_mathml_tables(root: ET.Element) -> list[ET.Element]:
    if not ALIGNED_ANNOTATION_RE.search(_mathml_annotation_text(root)):
        return []
    semantics = root.find(f"./{MATHML_TAG}semantics")
    if semantics is not None:
        tables = semantics.findall(MATHML_TAG + "mtable")
        if tables:
            return tables
    return root.findall(f".//{MATHML_TAG}mtable")[:1]


def normalize_mathml_alignment(markup: str) -> str:
    """Normalize native MathML alignment for generated ``aligned`` tables.

    Pandoc/texmath serializes ``lhs &= rhs && \\text{at } condition`` as four
    MathML table cells, including an empty spacer cell.  That extra table
    column changes how browser MathML centers the whole alignment.  Ordinary
    ``aligned`` tables also need explicit alternating right/left column
    alignment so native MathML uses the same alignment points as MathJax.
    The TeX annotation gates both changes; arrays, cases, and unrelated
    MathML tables remain untouched.
    """
    try:
        root = ET.fromstring(markup)
    except ET.ParseError as exc:
        raise SystemExit(f"invalid generated MathML: {exc}") from exc

    changed = False
    for table in _aligned_mathml_tables(root):
        rows = table.findall(MATHML_TAG + "mtr")
        candidates: list[tuple[ET.Element, list[ET.Element]]] = []
        supported = True
        for row in rows:
            cells = row.findall(MATHML_TAG + "mtd")
            if len(cells) == 2:
                continue
            if (
                len(cells) != 4
                or not _empty_mathml_cell(cells[2])
                or not _boundary_mathml_cell(cells[3])
            ):
                supported = False
                break
            candidates.append((row, cells))

        if supported and candidates:
            for row, cells in candidates:
                rhs, condition = cells[1], cells[3]
                combined = ET.Element(MATHML_TAG + "mrow")
                combined.extend(list(rhs))
                combined.append(ET.Element(MATHML_TAG + "mspace", {"width": "1em"}))
                combined.extend(list(condition))
                rhs[:] = [combined]
                row.remove(cells[2])
                row.remove(cells[3])
                changed = True

        width = max(
            (len(row.findall(MATHML_TAG + "mtd")) for row in rows),
            default=0,
        )
        if width:
            columnalign = " ".join(
                "right" if index % 2 == 0 else "left" for index in range(width)
            )
            if table.get("columnalign") != columnalign:
                table.set("columnalign", columnalign)
                changed = True

    if not changed:
        return markup
    return ET.tostring(root, encoding="unicode")


def normalize_mathml_page(text: str) -> str:
    """Normalize recognized alignment tables in generated MathML HTML."""
    return MATHML_MATH_RE.sub(
        lambda match: normalize_mathml_alignment(match.group(0)), text
    )


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
    command = [
        "pandoc",
        str(source_tex),
        "-f",
        "latex+smart",
        "-t",
        "html5",
    ]
    if math_method == "mathjax":
        command.extend(
            [
                "-s",
                "--template",
                str(HTML_TEMPLATE),
                *template_variable_args(template_variables(output)),
            ]
        )
    command.extend(
        [
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
    run(command)


def install_mathml_alternates(page: Path, mathml_page: Path) -> None:
    text = page.read_text(errors="replace")
    mathml_text = normalize_mathml_page(mathml_page.read_text(errors="replace"))
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
                '<span data-math-renderer="mathjax" hidden',
                1,
            )
        )
        chunks.append(
            f'<span data-math-renderer="mathml" '
            f'class="math {kind} mathml-alternate">{mathml.group(0)}</span>'
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


@dataclass(frozen=True)
class PageMetadata:
    """Raw metadata shared by the HTML head, structured data, and sitemap."""

    page_title: str
    description: str
    canonical_url: str
    social_title: str
    social_url: str
    social_image: str
    social_image_alt: str
    structured_data: dict[str, object]
    scholar_tags: tuple[tuple[str, str], ...] = ()


def canonical_page_url(path: Path) -> str:
    """Return the clean public URL for one member of the HTML page inventory."""
    base = SITE_URL.rstrip("/")
    return f"{base}/" if path.name == "index.html" else f"{base}/{path.name}"


def _schema_person(name: str) -> dict[str, str]:
    return {"@type": "Person", "name": name}


def _book_reference() -> dict[str, str]:
    book_url = canonical_page_url(EXPECTED_PAGES[0])
    return {
        "@type": "Book",
        "@id": book_url,
        "name": PUBLICATION_TITLE,
        "url": book_url,
    }


def page_metadata_record(path: Path) -> PageMetadata:
    """Build one raw, authoritative metadata record for a public HTML page."""
    context = page_context(path)
    canonical_url = canonical_page_url(path)
    display_title = reader_punctuation(PUBLICATION_TITLE)
    author_text = " and ".join(AUTHORS)
    page_title = (
        PUBLICATION_TITLE if path.name == "index.html" else f"{context} — {BOOK_TITLE}"
    )
    social_title = (
        display_title if path.name == "index.html" else f"{context} — {display_title}"
    )
    social_image = f"{SITE_URL.rstrip('/')}/assets/social-preview.png"
    social_image_alt = f"{display_title}, by {author_text}, edited by {EDITOR}."

    if path.name == "index.html":
        description = (
            f"Digital edition of {display_title} by {author_text}, edited by {EDITOR}."
        )
        structured_data: dict[str, object] = {
            "@context": "https://schema.org",
            "@type": "Book",
            "@id": canonical_url,
            "name": PUBLICATION_TITLE,
            "author": [_schema_person(author) for author in AUTHORS],
            "editor": _schema_person(EDITOR),
            "inLanguage": LANGUAGE,
            "datePublished": PUBLICATION_YEAR,
            "url": canonical_url,
            "license": LICENSE_URL,
            "identifier": DOI_URL,
        }
        scholar_tags = (
            ("citation_title", PUBLICATION_TITLE),
            *(("citation_author", author) for author in AUTHORS),
            ("citation_publication_date", PUBLICATION_YEAR),
            ("citation_online_date", ONLINE_PUBLICATION_YEAR),
            ("citation_pdf_url", f"{canonical_url}{MODERN_PDF_FILENAME}"),
        )
    else:
        chapter = chapter_for_page(path)
        if chapter is not None:
            description = chapter.description
            structured_data = {
                "@context": "https://schema.org",
                "@type": "Chapter",
                "name": chapter.title,
                "position": chapter.number,
                "url": canonical_url,
                "isPartOf": _book_reference(),
            }
        else:
            description = f"References for {display_title}."
            structured_data = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": "References",
                "url": canonical_url,
            }
        scholar_tags = ()

    return PageMetadata(
        page_title=page_title,
        description=description,
        canonical_url=canonical_url,
        social_title=social_title,
        social_url=canonical_url,
        social_image=social_image,
        social_image_alt=social_image_alt,
        structured_data=structured_data,
        scholar_tags=scholar_tags,
    )


def structured_data_json(payload: dict[str, object]) -> str:
    """Serialize JSON-LD safely for an inline script element."""
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (
        serialized.replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
    )


def scholar_metadata_html(tags: tuple[tuple[str, str], ...]) -> str:
    return "\n".join(
        f'<meta name="{html.escape(name, quote=True)}" '
        f'content="{html.escape(value, quote=True)}">'
        for name, value in tags
    )


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
        "next_url": html.escape(next_url, quote=True),
        "next_label": html.escape(next_label),
    }


def reader_state(index: int | None) -> dict[str, str]:
    if index is None:
        return {
            "reader_chapter": "Front matter",
            "reader_chapter_url": "#top",
            "reader_title": "",
        }
    if index == 0:
        return {
            "reader_chapter": "References",
            "reader_chapter_url": "#top",
            "reader_title": "",
        }

    chapter = CHAPTER_BY_NUMBER.get(index)
    if chapter is None:
        raise ValueError(f"unexpected chapter number: {index}")
    return {
        "reader_chapter": f"Chapter {chapter.number}",
        "reader_chapter_url": "#top",
        "reader_title": html.escape(chapter.title),
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
        + f'<summary{' class="is-current-chapter"' if index is None else ""}><a href="index.html"'
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
            + f'<summary{' class="is-current-chapter"' if active else ""}><a href="chapter{chapter.number}.html#chapter-{chapter.number}"'
            + current_page(active)
            + f">{chapter.number} · {html.escape(chapter.title)}</a></summary>"
            + f"<ol>{sections}</ol></details></li>"
        )

    references_active = index == 0
    artwork = (
        '<li><a href="references.html#artwork"'
        + (' data-section-link="artwork"' if references_active else "")
        + ">Artwork</a></li>"
    )
    items.append(
        '<li class="book-toc-page">'
        + f'<details class="book-toc-group"{" open" if references_active else ""}>'
        + f'<summary{' class="is-current-chapter"' if references_active else ""}><a href="references.html"'
        + current_page(references_active)
        + ">References</a></summary>"
        + f"<ol>{artwork}</ol></details></li>"
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
    metadata = page_metadata_record(path)
    return {
        "language": html.escape(LANGUAGE, quote=True),
        "page_title": html.escape(metadata.page_title, quote=True),
        "description": html.escape(metadata.description, quote=True),
        "canonical_url": html.escape(metadata.canonical_url, quote=True),
        "social_title": html.escape(metadata.social_title, quote=True),
        "social_url": html.escape(metadata.social_url, quote=True),
        "social_image": html.escape(metadata.social_image, quote=True),
        "social_image_alt": html.escape(metadata.social_image_alt, quote=True),
        "mathjax_upstream": html.escape(MATHJAX_URL, quote=True),
        "mathjax_url": html.escape(LOCAL_MATHJAX_URL, quote=True),
        "manifest_url": html.escape(WEB_MANIFEST_FILENAME, quote=True),
        "apple_touch_icon_url": html.escape(APPLE_TOUCH_ICON_PATH, quote=True),
        "artwork_cover_url": html.escape(
            f"{SITE_URL.rstrip('/')}/{ARTWORK_ASSET_PATHS[0]}", quote=True
        ),
        "artwork_closing_url": html.escape(
            f"{SITE_URL.rstrip('/')}/{ARTWORK_ASSET_PATHS[1]}", quote=True
        ),
        "scholar_metadata": scholar_metadata_html(metadata.scholar_tags),
        "structured_data": structured_data_json(metadata.structured_data),
    }


def template_variables(path: Path) -> dict[str, str]:
    index = page_index(path)
    info = current_build()
    values = {
        "asset_version": html.escape(info.short_sha, quote=True),
        "source_url": html.escape(source_url(index, info.sha), quote=True),
        "repository_url": html.escape(REPOSITORY_URL, quote=True),
        "build_label": html.escape(info.label),
        "build_url": html.escape(info.commit_url, quote=True),
        "book_toc": book_toc(index),
        **page_metadata(path),
        **navigation_state(index),
        **reader_state(index),
    }
    if chapter_for_page(path) is not None:
        values["chapter_title_block"] = "true"
    if index is None:
        values["page_extra"] = html_frontmatter_footer() + "\n" + html_license()
    return values


def template_variable_args(values: dict[str, str]) -> list[str]:
    args: list[str] = []
    for name, value in values.items():
        if value:
            args.extend(["--variable", f"{name}:{value}"])
    return args


def canonical_page_urls() -> tuple[str, ...]:
    return tuple(page_metadata_record(page).canonical_url for page in EXPECTED_PAGES)


def sitemap_urls() -> tuple[str, ...]:
    """Return the HTML inventory followed by the reader download resources."""
    base = SITE_URL.rstrip("/")
    resources = tuple(f"{base}/{filename}" for filename, _ in HTML_DOWNLOADS)
    return (*canonical_page_urls(), *resources)


def sitemap_text() -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<urlset xmlns="{SITEMAP_NAMESPACE}">',
    ]
    for url in sitemap_urls():
        lines.extend(
            (
                "  <url>",
                f"    <loc>{xml_escape(url)}</loc>",
                "  </url>",
            )
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write_sitemap() -> None:
    SITEMAP.write_text(sitemap_text(), encoding="utf-8")


def write_pwa_files() -> None:
    """Write the manifest and offline-reader service worker."""
    write_web_app_manifest(OUT)
    resources = offline_reader_resources(OUT)
    write_service_worker(OUT, current_build())
    total_bytes, largest = offline_reader_resource_stats(OUT, resources)
    previous_total_bytes, _ = offline_reader_resource_stats(
        OUT, all_reader_resources(OUT)
    )
    saved_bytes = max(previous_total_bytes - total_bytes, 0)
    reduction = saved_bytes / previous_total_bytes * 100 if previous_total_bytes else 0
    print(
        f"Offline reader precache: {len(resources)} files, "
        f"{total_bytes} uncompressed bytes"
    )
    print(
        "Offline reader precache policy: "
        f"previous full-asset total={previous_total_bytes} bytes; "
        f"current={total_bytes} bytes; saved={saved_bytes} bytes "
        f"({reduction:.2f}%)"
    )
    for name, size in largest[:10]:
        print(f"  {name}: {size} bytes")


READER_CONTEXT_RE = re.compile(
    r'<span class="reader-context"[^>]*>(?P<body>.*?)</span>\s*'
    r'<span class="reader-nav-slot">',
    re.DOTALL,
)


def validate_reader_context() -> None:
    """Validate the page-start link and section-only context slot."""
    for page in EXPECTED_PAGES:
        text = page.read_text(errors="replace")
        matches = READER_CONTEXT_RE.findall(text)
        if len(matches) != 1:
            raise SystemExit(
                f"{page.name}: reader context is missing or has changed structure"
            )
        body = matches[0]
        if body.count('class="reader-context-chapter"') != 1:
            raise SystemExit(
                f"{page.name}: reader context chapter label is missing or duplicated"
            )
        if body.count('class="reader-context-title"') != 1:
            raise SystemExit(
                f"{page.name}: reader context section slot is missing or duplicated"
            )

        chapter = chapter_for_page(page)
        label = (
            f"Chapter {chapter.number}"
            if chapter is not None
            else "Front matter"
            if page.name == "index.html"
            else "References"
        )
        expected = f'<a class="reader-context-chapter" href="#top">{label}</a>'
        if body.count(expected) != 1 or len(re.findall(r"<a\b", body)) != 1:
            raise SystemExit(
                f"{page.name}: reader context label must link only to the page start"
            )


def heading_text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def normalized_heading_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).translate(HEADING_TRANSLATION)
    return " ".join(normalized.split())


def remove_html_frontmatter_duplicate_title(page: Path) -> None:
    """Remove the semantic title block duplicated by the HTML page title."""
    text = page.read_text(errors="replace")
    title_start = text.find('<header id="title-block-header">')
    title_end = text.find("</header>", title_start)
    if title_start < 0 or title_end < 0:
        raise SystemExit("HTML front matter title block is missing")

    tail_start = title_end + len("</header>")
    tail = text[tail_start:]
    stripped_tail = tail.lstrip()
    match = FRONTMATTER_TITLE_BLOCK_RE.match(stripped_tail)
    if match is None:
        raise SystemExit(
            "index.html: semantic front matter title block is missing or changed"
        )
    leading = tail[: len(tail) - len(stripped_tail)]
    replacement = match.group("open") + stripped_tail[match.end() :]
    page.write_text(text[:tail_start] + leading + replacement)


def install_frontmatter_ids(page: Path) -> None:
    text = page.read_text(errors="replace")
    title_start = text.find('<header id="title-block-header">')
    title_end = text.find("</header>", title_start)
    if title_start < 0 or title_end < 0:
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


FIGURE_IMAGE_MARK_RE = re.compile(
    r'<div class="center">\s*<p>(?P<img><img[^>]*>)</p>\s*'
    r'<div class="center">\s*<p><span class="sans-serif">'
    r"(?P<label>Figure [1-6][.][0-9]+)</span></p>\s*</div>\s*</div>",
    re.DOTALL,
)
FIGURE_IMAGE_RE = re.compile(
    r"<p>(?P<img><img[^>]*>)</p>\s*"
    r'<div class="center">\s*<p><span class="sans-serif">'
    r"(?P<label>Figure [1-6][.][0-9]+)</span></p>\s*</div>",
    re.DOTALL,
)
FIGURE_IMAGE_AFTER_CONTENT_RE = re.compile(
    r"(?P<prefix><p>.+?)\s*(?P<img><img[^>]*>)\s*</p>\s*"
    r'<div class="center">\s*<p><span class="sans-serif">'
    r"(?P<label>Figure [1-6][.][0-9]+)</span></p>\s*</div>",
    re.DOTALL,
)
FIGURE_LABEL_RE = re.compile(
    r'<span class="sans-serif">Figure [1-6][.][0-9]+</span>',
    re.DOTALL,
)
FIGURE_IMAGE_SRC_RE = re.compile(r'\bsrc="([^"]+)"', re.IGNORECASE)
FIGURE_CONTROL_RE = re.compile(
    r"<button\b[^>]*\bdata-figure-cycle\b[^>]*>(.*?)</button>",
    re.DOTALL | re.IGNORECASE,
)
FIGURE_LABEL_VALUE_RE = re.compile(
    r"<span\b[^>]*\bdata-figure-label\b[^>]*>(.*?)</span>",
    re.DOTALL | re.IGNORECASE,
)


def _figure_image_src(image_tag: str) -> str:
    match = FIGURE_IMAGE_SRC_RE.search(image_tag)
    if match is None:
        raise SystemExit("HTML figure image is missing src")
    return html.unescape(match.group(1))


def _switchable_image_tag(image_tag: str, stem: str) -> str:
    src = _figure_image_src(image_tag)
    if "data-vector-src=" in image_tag or "data-original-src=" in image_tag:
        raise SystemExit(f"HTML figure image already contains switch metadata: {src}")
    original = f"assets/figures/{stem}.png"
    replacement = (
        f'src="{html.escape(original, quote=True)}" '
        f'data-vector-src="{html.escape(src, quote=True)}" '
        f'data-original-src="{html.escape(original, quote=True)}"'
    )
    updated, count = re.subn(
        r'\bsrc="[^"]+"', replacement, image_tag, count=1, flags=re.IGNORECASE
    )
    if count != 1:
        raise SystemExit(f"could not add switch metadata to HTML figure image: {src}")
    return updated


def _figure_markup(image_tag: str, label: str, switchable: set[str]) -> str:
    src = _figure_image_src(image_tag)
    match = re.fullmatch(r"assets/figures/(?P<stem>[^/]+)\.svg", src)
    stem = match.group("stem") if match is not None else None
    is_switchable = stem is not None and stem in switchable
    if is_switchable:
        image_tag = _switchable_image_tag(image_tag, stem)
    class_name = (
        "wave-figure wave-figure-switchable" if is_switchable else "wave-figure"
    )
    action = ""
    if is_switchable:
        action = (
            '<button type="button" class="figure-view-toggle js-only" '
            'data-figure-toggle aria-label="Switch to reconstructed vector figure">'
            "Switch to Vector</button>"
        )
    return (
        f'<figure class="{class_name}"'
        + (' data-figure-view="original"' if is_switchable else "")
        + ">\n"
        + image_tag
        + f'\n<figcaption><span class="figure-label">{html.escape(label)}</span>'
        + action
        + "</figcaption>\n</figure>"
    )


def install_figure_markup(page: Path, assets_root: Path = OUT) -> None:
    """Wrap Pandoc's marked scientific figures in semantic HTML figures."""
    text = page.read_text(errors="replace")
    expected = len(FIGURE_LABEL_RE.findall(text))
    switchable = set(page_switchable_figure_stems(page, assets_root))

    text = FIGURE_IMAGE_MARK_RE.sub(
        lambda match: _figure_markup(
            match.group("img"), match.group("label"), switchable
        ),
        text,
    )
    text = FIGURE_IMAGE_AFTER_CONTENT_RE.sub(
        lambda match: (
            match.group("prefix").rstrip()
            + "</p>\n"
            + _figure_markup(match.group("img"), match.group("label"), switchable)
        ),
        text,
    )
    text = FIGURE_IMAGE_RE.sub(
        lambda match: _figure_markup(
            match.group("img"), match.group("label"), switchable
        ),
        text,
    )
    installed = len(re.findall(r'<figure class="wave-figure(?: [^"]+)?"', text))
    if installed != expected or FIGURE_LABEL_RE.search(text):
        raise SystemExit(
            f"{page.name}: wrapped {installed} of {expected} marked HTML figures"
        )
    page.write_text(text)


FIGURE_BLOCK_RE = re.compile(
    r'<figure class="wave-figure(?: [^"]+)?"[^>]*>.*?</figure>',
    re.DOTALL,
)
FIGURE_IMAGE_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
FIGURE_DATA_ATTR_RE = re.compile(
    r'\b(?:src|data-vector-src|data-original-src)="([^"]+)"',
    re.IGNORECASE,
)


def validate_figure_markup() -> None:
    """Validate generated HTML figure pairs and progressive enhancement."""
    for page in EXPECTED_PAGES:
        text = page.read_text(errors="replace")
        expected_switchable = set(page_switchable_figure_stems(page, OUT))
        controls = FIGURE_CONTROL_RE.findall(text)
        if (
            len(controls) != 1
            or text.count("data-figure-cycle") != 1
            or text.count("data-figure-label") != 1
        ):
            raise SystemExit(
                f"{page.name}: expected one global figure rendering preference"
            )
        control = controls[0]
        labels = FIGURE_LABEL_VALUE_RE.findall(control)
        label = re.sub(r"<[^>]+>", "", labels[0]).strip() if len(labels) == 1 else ""
        if label != "Original":
            raise SystemExit(
                f"{page.name}: global figure rendering preference must start at Original"
            )
        if not re.search(
            r'\baria-label="Default figure rendering: Original"',
            text,
            re.IGNORECASE,
        ):
            raise SystemExit(
                f"{page.name}: global figure preference has the wrong label"
            )
        blocks = FIGURE_BLOCK_RE.findall(text)
        for block in blocks:
            images = FIGURE_IMAGE_TAG_RE.findall(block)
            if len(images) != 1 or block.count("<figcaption>") != 1:
                raise SystemExit(
                    f"{page.name}: figure must contain exactly one image and caption"
                )
            image = images[0]
            if not re.search(r'\balt="[^"]*"', image, re.IGNORECASE):
                raise SystemExit(f"{page.name}: figure image is missing alt text")
            values = FIGURE_DATA_ATTR_RE.findall(image)
            for value in values:
                target = (OUT / value).resolve()
                if (
                    value.startswith("/")
                    or ".." in Path(value).parts
                    or not target.is_relative_to(OUT.resolve())
                ):
                    raise SystemExit(
                        f"{page.name}: figure asset escapes publication tree: {value}"
                    )

            switchable = "wave-figure-switchable" in block
            if not switchable:
                if "data-figure" in block or "figure-view-toggle" in block:
                    raise SystemExit(
                        f"{page.name}: unswitchable figure exposes a switch control"
                    )
                continue

            vector = re.search(r'\bdata-vector-src="([^"]+)"', image)
            original = re.search(r'\bdata-original-src="([^"]+)"', image)
            src = re.search(r'\bsrc="([^"]+)"', image)
            if not vector or not original or not src:
                raise SystemExit(
                    f"{page.name}: switchable figure is missing paired image URLs"
                )
            if src.group(1) != original.group(1) or not original.group(1).endswith(
                ".png"
            ):
                raise SystemExit(
                    f"{page.name}: switchable figure must default to its original PNG"
                )
            vector_stem = Path(vector.group(1)).stem
            expected_original = f"assets/figures/{vector_stem}.png"
            if original.group(1) != expected_original:
                raise SystemExit(
                    f"{page.name}: switchable figure does not preserve its asset stem"
                )
            if vector_stem not in expected_switchable:
                raise SystemExit(
                    f"{page.name}: switchable figure has no generated source pair"
                )
            if (
                not (OUT / vector.group(1)).is_file()
                or not (OUT / original.group(1)).is_file()
            ):
                raise SystemExit(
                    f"{page.name}: switchable figure asset is missing on disk"
                )
            toggles = re.findall(
                r"<button\b[^>]*\bdata-figure-toggle\b[^>]*>(.*?)</button>",
                block,
                flags=re.DOTALL | re.IGNORECASE,
            )
            toggle_text = (
                re.sub(r"<[^>]+>", "", toggles[0]).strip() if len(toggles) == 1 else ""
            )
            if len(toggles) != 1 or toggle_text != "Switch to Vector":
                raise SystemExit(
                    f"{page.name}: switchable figure is missing its local action"
                )
            if 'aria-label="Switch to reconstructed vector figure"' not in block:
                raise SystemExit(
                    f"{page.name}: switchable figure has the wrong initial action label"
                )


def html_frontmatter_footer() -> str:
    links = "".join(
        f'<li><a href="{filename}">{html.escape(label)}</a></li>'
        for filename, label in HTML_DOWNLOADS
    )
    return (
        '<section class="edition-links"><h2>Read and download</h2><ul>'
        '<li><a href="chapter1.html">Start reading</a></li>'
        + links
        + "</ul>"
        + f'<p>Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>'
        + "</section>"
    )


def build_index(source_dir: Path) -> None:
    page = OUT / "index.html"
    dual_math_page(source_dir / "frontmatter.tex", page, PUBLICATION_TITLE)
    remove_html_frontmatter_duplicate_title(page)
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
            "-f",
            "markdown",
            "-s",
            "-t",
            "html5",
            "--template",
            str(HTML_TEMPLATE),
            *template_variable_args(template_variables(OUT / "references.html")),
            "--citeproc",
            "--csl",
            str(AMS_CSL),
            f"--bibliography={SRC / 'references.bib'}",
            "--metadata",
            "title=References",
            "--metadata",
            f"lang={LANGUAGE}",
            "--resource-path",
            resource_path,
            "-o",
            str(OUT / "references.html"),
        ]
    )


def validate_pwa_files() -> None:
    """Check that generated PWA files match the current publication output."""
    if not WEB_MANIFEST.is_file() or WEB_MANIFEST.stat().st_size == 0:
        raise SystemExit("missing generated web app manifest")
    try:
        actual_manifest = json.loads(WEB_MANIFEST.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"generated web app manifest is invalid JSON: {exc}") from exc
    if actual_manifest != web_app_manifest():
        raise SystemExit("generated web app manifest is not current")

    if not SERVICE_WORKER.is_file() or SERVICE_WORKER.stat().st_size == 0:
        raise SystemExit("missing generated service worker")
    expected_worker = service_worker_text(OUT, current_build())
    if SERVICE_WORKER.read_text() != expected_worker:
        raise SystemExit("generated service worker is not current")


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
    try:
        validate_application_icons(ASSETS / "icons")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    validate_pwa_files()

    for page in EXPECTED_PAGES:
        text = page.read_text(errors="replace")
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
        mathjax_openings = re.findall(
            r'<span\b[^>]*data-math-renderer="mathjax"[^>]*>', text
        )
        mathml_openings = re.findall(
            r'<span\b[^>]*data-math-renderer="mathml"[^>]*>', text
        )
        if not all(re.search(r"\bhidden\b", opening) for opening in mathjax_openings):
            raise SystemExit(f"{page.name}: MathJax alternates must start hidden")
        if any(re.search(r"\bhidden\b", opening) for opening in mathml_openings):
            raise SystemExit(f"{page.name}: MathML alternates must start visible")

    validate_reader_context()
    validate_figure_markup()

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
        for section in chapter.sections:
            anchor = section_slug(section)
            if f'id="{anchor}"' not in text:
                raise SystemExit(
                    f"chapter{chapter.number}.html: stable section anchor is missing: {anchor}"
                )
        if 'class="chapter-title-block"' not in text:
            raise SystemExit(
                f"chapter{chapter.number}.html: chapter title block is missing"
            )


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
    SITEMAP.unlink(missing_ok=True)
    BUILD.mkdir(parents=True)
    ASSETS.mkdir(parents=True)
    prepare_assets(OUT, BUILD, include_originals=True)
    prepare_application_icons(OUT)
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
        install_chapter_id(page, chapter.number)
        install_figure_markup(page)
    build_references(source_dir)
    install_stable_section_ids()
    write_sitemap()
    write_pwa_files()
    validate()
    print(
        f"HTML build OK: front matter + {len(CHAPTERS)} chapters + "
        "references + social preview"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
