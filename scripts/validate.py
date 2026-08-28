#!/usr/bin/env python3
"""Publication validation with EPUB, math, artifact, release, and all modes."""

from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from functools import cache
from pathlib import Path

from build_epub import (
    ACCESSIBILITY_METADATA,
    COVER_ALTERNATIVE,
    DC_NS,
    EPUB_TYPE,
    FRONTISPIECE_ALTERNATIVE,
    SVG_NS,
    XML_NS,
    cover_image_basename,
    first_bodymatter_member,
    manifest_member,
    manifest_xhtml_members,
    navigation_member,
    package_document,
    ref_basename,
    svg_image_ref,
    text_content,
    validate_structure,
)
from publication import (
    AUTHORS,
    DOWNLOADS,
    EDITOR,
    LANGUAGE,
    REPOSITORY_URL,
    SITE_URL,
    book_structure,
    current_build,
    equation_asset_errors,
    equation_ledger_errors,
    figure_ledger_errors,
    page_switchable_figure_stems,
    section_slug,
    summarize_equation_asset_errors,
    validate_maintained_figure_assets,
)
from publication import (
    MATHJAX_URL as MATHJAX_PINNED,
)
from publication import PUBLICATION_TITLE as TITLE
from release import publication_files, verify_manifest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BUILD = ROOT / "build"
PUBLICATION = ROOT / "release"
README = ROOT / "README.md"
EPUB = PUBLICATION / "wave-motions.epub"
MODERN_PDF = PUBLICATION / "wave-motions.pdf"
FACSIMILE_PDF = PUBLICATION / "wave-motions-facsimile.pdf"
LATEX_CACHE = (
    Path(os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions")))
    / "latex"
)
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
FACSIMILE_EXPECTED_PAGES = 184
FACSIMILE_FRONT_MATTER_PAGES = 10
FACSIMILE_BODY_BOUNDARIES = 170
FACSIMILE_HEADROOM_WARNING_PT = 10.0
FACSIMILE_BOUNDARY_RE = re.compile(
    r"^FACSIMILE_B n=(\d+) p=(\d+) s=(-?\d+(?:\.\d+)?)pt$"
)
FACSIMILE_SHIPOUT_RE = re.compile(r"^FACSIMILE_P n=(\d+) p=(\d+)$")

# Paola's preface is a compact cross-format sentinel because it intentionally
# distinguishes ordinary prose from mathematical variable glyphs.
PAOLA_SOURCE_SENTINELS = (
    r"put $\ell$ ($x$ wavenumber) before $k$ ($y$ wavenumber)",
    r"letters $j,k,x,y,w$ do not exist",
    r"$k$ coming before or after",
    r"$\ell$ was supremely unimportant",
)
README_MATH_SENTINELS = (r"\ell", "x", "k", "y", "j,k,x,y,w")
EPUB_VARIABLE_SENTINELS = ("σ", "ρ", "ℓ", "k", "m", "x", "y", "t")
EPUB_OPERATOR_SENTINELS = ("sin", "cos", "tanh")
EPUB_NAV_SENTINELS = (
    "Basic concepts",
    "Acoustic waves",
    "Surface gravity waves",
    "Internal gravity waves",
    "Shallow water dynamics",
    "Topographic effects",
    "References",
)
EPUB_FALSE_ACCESSIBILITY_FEATURES = {"alternativeText", "longDescription", "taggedPDF"}
EPUB_GENERIC_ALT_TEXT = {"image", "figure"}
NAMED_FUNCTIONS = ("sin", "cos", "tan", "sinh", "cosh", "tanh", "exp", "log", "ln")
NUMBERED_ENV_RE = re.compile(r"\\begin\{(?:waveequation|wavealign)\}")
NATIVE_TAG_RE = re.compile(r"\\tag\{(?P<tag>\d+\.\d+)\}")
MATH_ENV_RE = re.compile(
    r"\\begin\{(?P<env>waveequation|wavealign|align\*?|equation\*?|gather\*?|multline\*?)\}"
    r"(?P<body>.*?)\\end\{(?P=env)\}",
    re.DOTALL,
)
MATHML_ELEMENT_RE = re.compile(r"<math\b[^>]*>.*?</math>", re.DOTALL | re.IGNORECASE)
MATH_TEXT_COMMAND_RE = re.compile(
    r"\\(?:text|textrm|textsf|texttt|textit|textbf|mathrm|operatorname)\{[^{}]*\}"
)
SMART_PUNCTUATION_RE = re.compile(r"[“”‘’–—…−]")
PUNCTUATION_ENTITY_RE = re.compile(r"&(?:ldquo|rdquo|lsquo|rsquo|ndash|mdash|hellip);")
SMART_ANCHOR_RE = re.compile(r'\bid=["\'][^"\']*[“”‘’–—…−]')
LOCAL_MATHJAX_URL = "assets/mathjax/tex-chtml-full.js"
HTML_DOWNLOADS = tuple(
    item for item in DOWNLOADS if item[0] != "wave-motions-facsimile.pdf"
)
TEXT_SIZE_ACTIONS = ("decrease", "reset", "increase")
TEXT_SIZE_PERCENTAGES = ("50%", "100%", "200%")
FRONTMATTER_SECTIONS = (
    ("preface-david-c-chapman", "Preface — David C. Chapman"),
    ("preface-paola-malanotte-rizzoli", "Preface — Paola Malanotte-Rizzoli"),
    ("editors-note", "Editor's note"),
)
CHAPTERS = book_structure()
CHAPTER_BY_NUMBER = {chapter.number: chapter for chapter in CHAPTERS}
EXPECTED_HTML_PAGES = (
    PUBLICATION / "index.html",
    *(PUBLICATION / f"chapter{chapter.number}.html" for chapter in CHAPTERS),
    PUBLICATION / "references.html",
)
REMOTE_SCHEMES = {"http", "https"}
FETCHING_LINK_RELS = {
    "dns-prefetch",
    "icon",
    "manifest",
    "modulepreload",
    "preconnect",
    "prefetch",
    "preload",
    "stylesheet",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"missing required generated artifact: {path}")


def warning(title: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title={title}::{message}")
    else:
        print(f"warning: {message}", file=sys.stderr)


def strip_tex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        # Ignore unescaped percent signs; sufficient for source-lint purposes.
        m = re.search(r"(?<!\\)%", line)
        lines.append(line[: m.start()] if m else line)
    return "\n".join(lines)


def tex_math_regions(text: str) -> list[str]:
    """Return TeX regions that are actually interpreted as mathematics."""
    regions = [m.group(1) for m in re.finditer(r"\\\[(.*?)\\\]", text, re.DOTALL)]
    regions.extend(m.group("body") for m in MATH_ENV_RE.finditer(text))
    regions.extend(
        m.group(1)
        for m in re.finditer(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", text, re.DOTALL)
    )
    return regions


def bare_named_functions(text: str) -> tuple[str, ...]:
    """Return named math functions that are not written as TeX operators."""
    math_text = "\n".join(
        MATH_TEXT_COMMAND_RE.sub("", region) for region in tex_math_regions(text)
    )
    return tuple(
        function
        for function in NAMED_FUNCTIONS
        if re.search(rf"(?<![\\A-Za-z]){function}(?![A-Za-z])", math_text)
    )


def check_canonical_source() -> None:
    frontmatter = (SRC / "frontmatter-modern.tex").read_text()
    for sentinel in PAOLA_SOURCE_SENTINELS:
        if sentinel not in frontmatter:
            fail(f"Paola preface math sentinel changed or lost: {sentinel}")

    for chapter in sorted(SRC.glob("chapter[1-6].tex")):
        text = strip_tex_comments(chapter.read_text())
        occurrences = re.findall(r"\\rm(?:\s|\{|$)", text)
        if occurrences:
            fail(
                f"{chapter.name}: found {len(occurrences)} legacy \\rm declaration(s); "
                "replace with semantic math commands"
            )

        for function in bare_named_functions(text):
            fail(
                f"{chapter.name}: named math function {function!r} appears without a TeX operator command"
            )

    print("TeX math audit OK")


def check_equation_ledger() -> None:
    ledger_errors = equation_ledger_errors()
    if ledger_errors:
        fail("equation ledger validation failed:\n- " + "\n- ".join(ledger_errors))
    errors = equation_asset_errors()
    if errors:
        fail(
            "equation asset validation failed:\n- "
            + "\n- ".join(summarize_equation_asset_errors(errors))
        )
    print(
        "Equation ledgers and SHA manifests are current; all equation PNG assets "
        "are regenerated v2 assets with matching pixels, renderer, and source-page metadata"
    )


def check_figure_ledger() -> None:
    errors = figure_ledger_errors()
    if errors:
        fail("figure ledger validation failed:\n- " + "\n- ".join(errors))
    print("Figure audit landing page and chapter ledgers are current")


def check_punctuation() -> None:
    canonical_paths = [
        SRC / "frontmatter-modern.tex",
        SRC / "frontmatter-modern-book.tex",
        SRC / "frontmatter-facsimile.tex",
        *(SRC / f"chapter{number}.tex" for number in range(1, 7)),
    ]
    for path in canonical_paths:
        text = strip_tex_comments(path.read_text())
        if SMART_PUNCTUATION_RE.search(text):
            fail(
                f"{path.name}: literal smart punctuation is not valid TeX source syntax"
            )
        if "Attribution--NonCommercial--ShareAlike" in text:
            fail(
                f"{path.name}: Creative Commons license name uses TeX en dashes instead of hyphens"
            )
        if any("−" in region for region in tex_math_regions(text)):
            fail(f"{path.name}: Unicode mathematical minus found in TeX math")

    html_pages = sorted(PUBLICATION.glob("*.html"))
    html_text = "\n".join(path.read_text(errors="replace") for path in html_pages)
    if PUNCTUATION_ENTITY_RE.search(html_text):
        fail("generated HTML contains a named typographic punctuation entity")
    if SMART_ANCHOR_RE.search(html_text):
        fail("generated HTML contains smart punctuation in a public anchor id")
    for punctuation in ("“", "’", "–", "—"):
        if punctuation not in html_text:
            fail(f"generated HTML is missing reader-facing punctuation {punctuation!r}")

    require_file(README)
    readme = README.read_text(errors="replace")
    if "# Wave Motions in the Ocean: Myrl’s View" not in readme:
        fail(
            "README display metadata did not render the subtitle apostrophe typographically"
        )
    if PUNCTUATION_ENTITY_RE.search(readme):
        fail("README contains a named typographic punctuation entity")

    require_file(EPUB)
    with zipfile.ZipFile(EPUB) as archive:
        epub_text = "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in archive.namelist()
            if name.lower().endswith((".xhtml", ".html"))
        )
    if PUNCTUATION_ENTITY_RE.search(epub_text):
        fail("generated EPUB contains a named typographic punctuation entity")
    if SMART_ANCHOR_RE.search(epub_text):
        fail("generated EPUB contains smart punctuation in a public anchor id")
    for punctuation in ("“", "’", "–", "—"):
        if punctuation not in epub_text:
            fail(f"generated EPUB is missing reader-facing punctuation {punctuation!r}")

    print("Cross-format punctuation invariants OK")


def canonical_equation_labels() -> dict[int, tuple[str, ...]]:
    labels: dict[int, tuple[str, ...]] = {}
    for chapter_number in range(1, 7):
        path = SRC / f"chapter{chapter_number}.tex"
        text = strip_tex_comments(path.read_text())
        wrapper_count = len(NUMBERED_ENV_RE.findall(text))
        native = tuple(f"({m.group('tag')})" for m in NATIVE_TAG_RE.finditer(text))
        if native and wrapper_count:
            fail(f"{path.name}: mixes source tags with editorial numbering wrappers")
        if native:
            expected = tuple(
                f"({chapter_number}.{index})" for index in range(1, len(native) + 1)
            )
            if native != expected:
                fail(
                    f"{path.name}: native equation tags are not contiguous/in order: {native}"
                )
            labels[chapter_number] = native
        elif wrapper_count:
            labels[chapter_number] = tuple(
                f"({chapter_number}.{index})" for index in range(1, wrapper_count + 1)
            )
        else:
            fail(f"{path.name}: no selected numbered equations found")
    return labels


def require_labels(text: str, labels: tuple[str, ...], *, artifact: str) -> None:
    if artifact == "EPUB" or artifact.endswith(".html"):
        prefix = r'class=["\']upright["\'][^>]*>\s*'
        suffix = ""
    elif artifact.endswith(".pdf"):
        # pdftotext -layout preserves display-equation indentation, but the exact
        # column varies with trim width and equation length. Match an indented
        # equation line whose label is at the right edge instead of hard-coding
        # a minimum number of leading spaces. Prose references remain excluded.
        prefix = r"(?m)^[ \t]+[^\n]*?"
        suffix = r"[ \t]*$"
    else:
        prefix = ""
        suffix = ""
    positions: list[int] = []
    for label in labels:
        pattern = re.compile(
            prefix + re.escape(label) + suffix if prefix else re.escape(label)
        )
        matches = list(pattern.finditer(text))
        count = len(matches)
        if count != 1:
            fail(
                f"{artifact}: equation label {label} occurs {count} times; expected exactly once"
            )
        positions.append(matches[0].start())
    if positions != sorted(positions):
        fail(f"{artifact}: numbered equation labels are not in the expected order")


def github_math_patterns(expr: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    escaped = re.escape(expr)
    return (
        re.compile(rf"(?<!\\)\${escaped}(?<!\\)\$"),
        re.compile(rf"\$`{escaped}`\$"),
    )


def check_readme() -> None:
    require_file(README)
    text = README.read_text()
    paola_start = text.find("## Preface — Paola Malanotte-Rizzoli")
    editor_start = text.find("## Editor’s note")
    if paola_start < 0 or editor_start <= paola_start:
        fail("README Paola preface boundaries are missing")
    section = text[paola_start:editor_start]

    for expr in README_MATH_SENTINELS:
        if not any(pattern.search(section) for pattern in github_math_patterns(expr)):
            fail(
                f"README no longer preserves GitHub-renderable inline math for {expr!r}"
            )
    if "`\\ell`" in section and "$`\\ell`$" not in section:
        fail("README contains a code-formatted \\ell outside GitHub math delimiters")

    print("GitHub Markdown math preservation OK")


def html_page_index(path: Path) -> int | None:
    if path.name == "index.html":
        return None
    if path.name == "references.html":
        return 0
    match = re.fullmatch(r"chapter(\d+)\.html", path.name)
    if match is None or int(match.group(1)) not in CHAPTER_BY_NUMBER:
        fail(f"unexpected HTML publication page: {path.name}")
    return int(match.group(1))


def html_source_url(path: Path, sha: str) -> str:
    index = html_page_index(path)
    if index is None:
        source_path = "src/frontmatter-modern.tex"
    elif index == 0:
        source_path = "src/references.bib"
    else:
        source_path = f"src/chapter{index}.tex"
    revision = sha if sha != "unknown" else "main"
    return f"{REPOSITORY_URL}/blob/{revision}/{source_path}"


def _is_remote_reference(value: str) -> bool:
    value = html.unescape(value.strip())
    if value.startswith("//"):
        return True
    parsed = urllib.parse.urlsplit(value)
    return parsed.scheme.lower() in REMOTE_SCHEMES or bool(parsed.netloc)


def _attribute(tag: str, name: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1",
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(2) if match else None


def validate_offline_runtime(root: Path) -> None:
    root = root.resolve()
    pages = sorted(root.glob("*.html"))
    if not pages:
        raise ValueError("offline HTML check found no HTML pages")

    remote: list[str] = []
    for page in pages:
        text = page.read_text(errors="replace")
        for tag in re.findall(r"<[^>]+>", text, flags=re.DOTALL):
            for attr in ("src", "poster", "data"):
                value = _attribute(tag, attr)
                if value and _is_remote_reference(value):
                    remote.append(f"{page.name}: {attr}={value}")
            srcset = _attribute(tag, "srcset")
            if srcset:
                for candidate in srcset.split(","):
                    value = candidate.strip().split(maxsplit=1)[0]
                    if value and _is_remote_reference(value):
                        remote.append(f"{page.name}: srcset={value}")
            if tag.lower().startswith("<link"):
                href = _attribute(tag, "href")
                rel = (_attribute(tag, "rel") or "").lower().split()
                if (
                    href
                    and FETCHING_LINK_RELS.intersection(rel)
                    and _is_remote_reference(href)
                ):
                    remote.append(f"{page.name}: link href={href}")

    stylesheets = sorted(root.rglob("*.css"))
    for stylesheet in stylesheets:
        text = stylesheet.read_text(errors="replace")
        for match in re.finditer(
            r"url\(\s*([\"']?)(.*?)\1\s*\)", text, flags=re.IGNORECASE
        ):
            value = match.group(2).strip()
            if value and _is_remote_reference(value):
                remote.append(f"{stylesheet.relative_to(root)}: url({value})")
        for match in re.finditer(
            r"@import\s+(?:url\()?\s*([\"'])(.*?)\1",
            text,
            flags=re.IGNORECASE,
        ):
            value = match.group(2).strip()
            if value and _is_remote_reference(value):
                remote.append(f"{stylesheet.relative_to(root)}: @import {value}")

    if remote:
        details = "\n".join(f"  {item}" for item in remote[:40])
        raise ValueError(
            "HTML reader has remote runtime dependencies:\n"
            + details
            + (f"\n  ... and {len(remote) - 40} more" if len(remote) > 40 else "")
        )
    print(
        f"Offline HTML runtime OK: {len(pages)} page(s), "
        f"{len(stylesheets)} stylesheet(s)"
    )


def validate_mathml_alignment(
    text: str, *, require_aligned: bool = False
) -> tuple[int, int]:
    """Check generated ``aligned`` columns and trailing conditions."""
    ns = f"{{{MATHML_NS}}}"
    boundary_tables = 0
    normalized_tables = 0
    aligned_tables = 0
    for markup in MATHML_ELEMENT_RE.findall(text):
        try:
            root = ET.fromstring(markup)
        except ET.ParseError as exc:
            raise ValueError(f"generated MathML is not XML: {exc}") from exc
        annotation_text = " ".join(
            " ".join("".join(node.itertext()).split())
            for node in root.findall(f".//{ns}annotation")
        )
        aligned_semantics = r"\begin{aligned}" in annotation_text
        aligned_tables_in_math = (
            root.findall(f"./{ns}semantics/{ns}mtable") if aligned_semantics else []
        )
        for table in root.findall(f".//{ns}mtable"):
            rows = table.findall(f"{ns}mtr")
            if table in aligned_tables_in_math:
                width = max(
                    (len(row.findall(f"{ns}mtd")) for row in rows),
                    default=0,
                )
                expected = " ".join(
                    "right" if index % 2 == 0 else "left" for index in range(width)
                )
                if width and table.get("columnalign") != expected:
                    raise ValueError(
                        "generated MathML aligned table has incorrect column alignment: "
                        f"expected {expected!r}, got {table.get('columnalign')!r}"
                    )
                aligned_tables += 1
            if annotation_text and not aligned_semantics:
                continue
            boundary_rows = []
            for row in rows:
                cells = row.findall(f"{ns}mtd")
                for index, cell in enumerate(cells):
                    condition_text = [
                        " ".join("".join(node.itertext()).split())
                        for node in cell.iter(f"{ns}mtext")
                    ]
                    if any(
                        re.match(r"^(?:at|as)\b", value, re.IGNORECASE)
                        for value in condition_text
                    ):
                        boundary_rows.append((index, len(cells)))
            if not boundary_rows:
                continue
            boundary_tables += 1
            width = max((row_width for _, row_width in boundary_rows), default=0)
            if width > 2:
                raise ValueError(
                    "generated MathML trailing-condition alignment retains an "
                    f"unintended {width}-column table"
                )
            if width == 2:
                normalized_tables += 1
                if any(index != 1 for index, _ in boundary_rows):
                    raise ValueError(
                        "generated MathML boundary condition is not attached to "
                        "the aligned equation RHS cell"
                    )

    if boundary_tables == 0:
        raise ValueError(
            "generated HTML contains no representative MathML boundary alignment"
        )
    if normalized_tables == 0:
        raise ValueError(
            "generated HTML contains no normalized MathML boundary alignment"
        )
    if require_aligned and aligned_tables == 0:
        raise ValueError(
            "generated HTML contains no representative aligned MathML table"
        )
    return boundary_tables, normalized_tables


def validate_local_references(root: Path) -> None:
    root = root.resolve()
    pages = sorted(root.glob("*.html"))
    if not pages:
        fail("generated HTML pages are missing")
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
        for attr in ("src", "href", "data-vector-src", "data-original-src"):
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
        fail(f"{len(broken)} broken local HTML reference(s)")


FIGURE_BLOCK_RE = re.compile(
    r'<figure class="wave-figure(?: [^"]+)?"[^>]*>.*?</figure>',
    re.DOTALL,
)
FIGURE_IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
FIGURE_TOGGLE_RE = re.compile(
    r"<button\b[^>]*\bdata-figure-toggle\b[^>]*>(.*?)</button>",
    re.DOTALL | re.IGNORECASE,
)
FIGURE_CONTROL_RE = re.compile(
    r"<button\b[^>]*\bdata-figure-cycle\b[^>]*>(.*?)</button>",
    re.DOTALL | re.IGNORECASE,
)
FIGURE_LABEL_VALUE_RE = re.compile(
    r"<span\b[^>]*\bdata-figure-label\b[^>]*>(.*?)</span>",
    re.DOTALL | re.IGNORECASE,
)
READER_CONTEXT_RE = re.compile(
    r'<span class="reader-context"[^>]*>(?P<body>.*?)</span>\s*'
    r'<span class="reader-nav-slot">',
    re.DOTALL,
)


def check_html_reader_context(page: Path, text: str) -> None:
    """Validate the page-start link in the generated reader context."""
    matches = READER_CONTEXT_RE.findall(text)
    if len(matches) != 1:
        fail(f"{page.name}: reader context is missing or has changed structure")
    body = matches[0]
    if body.count('class="reader-context-chapter"') != 1:
        fail(f"{page.name}: reader context chapter label is missing or duplicated")
    if body.count('class="reader-context-title"') != 1:
        fail(f"{page.name}: reader context section slot is missing or duplicated")

    page_index = html_page_index(page)
    label = (
        f"Chapter {page_index}"
        if page_index is not None and page_index > 0
        else "Front matter"
        if page_index is None
        else "References"
    )
    expected = f'<a class="reader-context-chapter" href="#top">{label}</a>'
    if body.count(expected) != 1 or len(re.findall(r"<a\b", body)) != 1:
        fail(f"{page.name}: reader context label must link only to the page start")


def check_html_figures() -> None:
    """Validate HTML vector/source pairs and their progressive enhancement."""
    try:
        validate_maintained_figure_assets()
    except ValueError as exc:
        fail(str(exc))

    for page in EXPECTED_HTML_PAGES:
        text = page.read_text(errors="replace")
        expected = set(page_switchable_figure_stems(page, PUBLICATION))
        controls = FIGURE_CONTROL_RE.findall(text)
        if (
            len(controls) != 1
            or text.count("data-figure-cycle") != 1
            or text.count("data-figure-label") != 1
        ):
            fail(f"{page.name}: expected one global figure rendering preference")
        control_labels = FIGURE_LABEL_VALUE_RE.findall(controls[0])
        control_label = (
            re.sub(r"<[^>]+>", "", control_labels[0]).strip()
            if len(control_labels) == 1
            else ""
        )
        if control_label != "Original":
            fail(
                f"{page.name}: global figure rendering preference must start at Original"
            )
        if 'aria-label="Default figure rendering: Original"' not in text:
            fail(f"{page.name}: global figure preference has the wrong label")
        blocks = FIGURE_BLOCK_RE.findall(text)
        for block in blocks:
            images = FIGURE_IMAGE_RE.findall(block)
            if len(images) != 1 or block.count("<figcaption>") != 1:
                fail(f"{page.name}: figure must contain one image and one caption")
            image = images[0]
            if not re.search(r'\balt="[^"]*"', image, re.IGNORECASE):
                fail(f"{page.name}: figure image is missing alt text")
            switchable = "wave-figure-switchable" in block
            if not switchable:
                if "data-figure" in block or "figure-view-toggle" in block:
                    fail(f"{page.name}: unswitchable figure exposes a switch control")
                continue
            vector = re.search(r'\bdata-vector-src="([^"]+)"', image)
            original = re.search(r'\bdata-original-src="([^"]+)"', image)
            src = re.search(r'\bsrc="([^"]+)"', image)
            if not vector or not original or not src:
                fail(f"{page.name}: switchable figure is missing paired image URLs")
            if src.group(1) != original.group(1) or not original.group(1).endswith(
                ".png"
            ):
                fail(
                    f"{page.name}: switchable figure does not default to its original PNG"
                )
            stem = Path(vector.group(1)).stem
            if original.group(1) != f"assets/figures/{stem}.png":
                fail(f"{page.name}: switchable figure changes its asset stem")
            if stem not in expected:
                fail(f"{page.name}: switchable figure has no source provenance pair")
            if (
                not (PUBLICATION / vector.group(1)).is_file()
                or not (PUBLICATION / original.group(1)).is_file()
            ):
                fail(f"{page.name}: switchable figure asset is missing")
            toggles = FIGURE_TOGGLE_RE.findall(block)
            toggle_text = (
                re.sub(r"<[^>]+>", "", toggles[0]).strip() if len(toggles) == 1 else ""
            )
            if len(toggles) != 1 or toggle_text != "Switch to Vector":
                fail(f"{page.name}: switchable figure is missing its local action")
            if 'aria-label="Switch to reconstructed vector figure"' not in block:
                fail(
                    f"{page.name}: switchable figure has the wrong initial action label"
                )


def check_html() -> None:
    for page in EXPECTED_HTML_PAGES:
        require_file(page)
    check_html_figures()
    css = PUBLICATION / "assets" / "wave.css"
    require_file(css)
    css_text = css.read_text(errors="replace")
    template_text = (SRC / "layout" / "wave-html.html").read_text(errors="replace")
    script_text = (SRC / "layout" / "wave-html.js").read_text(errors="replace")
    html_opening = re.search(r"<html\b[^>]*>", template_text, flags=re.IGNORECASE)
    if html_opening is None or re.search(r"\bdata-theme=", html_opening.group(0)):
        fail("HTML template must leave the no-JS root theme unset")
    if re.search(r'class="book-contents-popover"[^>]*\bhidden\b', template_text):
        fail(
            "HTML Contents popover must remain declaratively usable without JavaScript"
        )
    template_modes = tuple(
        re.findall(r'data-text-size-action="([^"]+)"', template_text)
    )
    if template_modes != TEXT_SIZE_ACTIONS:
        fail(
            "HTML template text-size actions are not exactly "
            f"{TEXT_SIZE_ACTIONS!r}: {template_modes!r}"
        )
    mode_match = re.search(
        r"const textSizeActions = \[(?P<modes>.*?)\];", script_text, flags=re.DOTALL
    )
    if mode_match is None:
        fail("HTML reader JavaScript does not declare text-size actions")
    script_modes = tuple(re.findall(r'"([^"]+)"', mode_match.group("modes")))
    if script_modes != TEXT_SIZE_ACTIONS:
        fail(
            "HTML reader JavaScript text-size actions are not exactly "
            f"{TEXT_SIZE_ACTIONS!r}: {script_modes!r}"
        )
    if re.search(r'data-text-size="(?:small|default|large)"', css_text):
        fail("HTML stylesheet retains legacy named text-size states")
    if any(
        marker in css_text
        for marker in ("--wave-text-scale: .94", "--wave-text-scale: 1.12")
    ):
        fail("HTML stylesheet retains legacy text-size scales")
    if ":root.no-js .js-only" not in css_text:
        fail("HTML stylesheet does not hide JS-only controls for no-JS readers")
    if (
        ':root.js[data-initial-math="mathjax"]:not([data-math-ready]) #main-content'
        not in css_text
        or "visibility: hidden" not in css_text
    ):
        fail("HTML stylesheet does not gate first-paint MathJax content")
    selector = 'mjx-container[jax="CHTML"][display="true"]'
    if selector not in css_text or "overflow-x: auto" not in css_text:
        fail("HTML stylesheet is missing responsive display-math overflow handling")
    inline_math_rule = re.search(
        r"\.math\.inline\s*\{(?P<body>[^}]*)\}", css_text, flags=re.DOTALL
    )
    if inline_math_rule is None:
        fail("HTML stylesheet is missing the inline-math flow invariant")
    inline_math_css = inline_math_rule.group("body")
    if "display: inline" not in inline_math_css:
        fail("HTML inline mathematics must remain in normal inline flow")
    if "overflow: visible" not in inline_math_css or re.search(
        r"overflow(?:-x)?\s*:\s*(?:auto|scroll)", inline_math_css
    ):
        fail("HTML inline mathematics must not become an independent scroll container")

    combined = "\n".join(
        path.read_text(errors="replace") for path in EXPECTED_HTML_PAGES
    )
    for sentinel in (
        "David C. Chapman",
        "Paola Malanotte-Rizzoli",
        "CC BY-NC-SA 4.0",
        "Apel",
    ):
        if sentinel not in combined:
            fail(f"HTML sentinel missing: {sentinel}")
    if re.search(r"<mo\b[^>]*>ℓ</mo>", combined):
        fail("HTML native MathML represents ℓ as an operator instead of an identifier")
    if not re.search(r"<mi\b[^>]*>ℓ</mi>", combined):
        fail("HTML native MathML is missing identifier-form ℓ")
    if MATHJAX_PINNED not in combined:
        fail("pinned MathJax 3.2.2 combined component is missing from HTML")
    if "mathjax@3/es5/tex-mml-chtml.js" in combined:
        fail("unversioned MathJax URL remains in generated HTML")

    inline_count = len(re.findall(r'class="math inline"', combined))
    display_count = len(re.findall(r'class="math display"', combined))
    if inline_count == 0 or display_count == 0:
        fail(
            f"HTML lost inline or display math markup: inline={inline_count}, "
            f"display={display_count}"
        )
    if "assistiveMml: false" in combined or "enableAssistiveMml: false" in combined:
        fail("HTML explicitly disables MathJax assistive MathML")
    if 'data-math-renderer="mathml"' not in combined or "<math " not in combined:
        fail("native MathML alternates are missing from generated HTML")
    try:
        boundary_tables, normalized_tables = validate_mathml_alignment(
            combined, require_aligned=True
        )
    except ValueError as exc:
        fail(str(exc))
    if LOCAL_MATHJAX_URL not in combined:
        fail("local MathJax component is missing from generated HTML")
    mathjax_openings = re.findall(
        r'<span\b[^>]*data-math-renderer="mathjax"[^>]*>', combined
    )
    mathml_openings = re.findall(
        r'<span\b[^>]*data-math-renderer="mathml"[^>]*>', combined
    )
    if not all(re.search(r"\bhidden\b", opening) for opening in mathjax_openings):
        fail("HTML MathJax alternates must start hidden behind static MathML")
    if any(re.search(r"\bhidden\b", opening) for opening in mathml_openings):
        fail("HTML MathML alternates must remain visible for the static first paint")

    index = PUBLICATION / "index.html"
    index_text = index.read_text(errors="replace")
    for tex in (r"\ell", "x", "k", "y", "j,k,x,y,w"):
        if tex not in index_text:
            fail(f"HTML Paola-preface math sentinel is missing: {tex!r}")

    info = current_build()
    label = html.escape(info.label)
    build_url = html.escape(info.commit_url, quote=True)
    for page in EXPECTED_HTML_PAGES:
        text = page.read_text(errors="replace")
        page_index = html_page_index(page)
        check_html_reader_context(page, text)
        if not re.search(
            rf'<html[^>]+lang="{re.escape(LANGUAGE)}"', text, flags=re.IGNORECASE
        ):
            fail(f"HTML language metadata missing from {page.name}")
        if text.count("<head>") != 1 or text.count("</head>") != 1:
            fail(f"HTML head boundaries are not unique in {page.name}")
        if (
            len(re.findall(r"<body\b[^>]*>", text, flags=re.IGNORECASE)) != 1
            or len(re.findall(r"</body\s*>", text, flags=re.IGNORECASE)) != 1
        ):
            fail(f"HTML body boundaries are not unique in {page.name}")
        for required in (
            "<!DOCTYPE html>",
            '<meta charset="utf-8">',
            'name="viewport"',
            'rel="icon"',
            "🌊",
            '<main id="main-content">',
            'class="skip-link"',
            'class="reader-header page-shell"',
            'class="book-nav',
            'id="reader-settings"',
            "data-theme-cycle",
            "data-theme-label",
            "data-math-label",
            "data-figure-cycle",
            "data-figure-label",
            'data-text-size-action="decrease"',
            'data-text-size-action="reset"',
            'data-text-size-action="increase"',
            "data-reader-context",
            "data-book-toc-rail",
            "data-toc-scope",
            "data-toc-expand",
            'class="book-contents-rail"',
            'class="book-contents-popover"',
            'class="build-info"',
            ">Source</a>",
            "Build <a",
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
            html.escape(html_source_url(page, info.sha), quote=True),
        ):
            if required not in text:
                fail(f"HTML requirement {required!r} is missing from {page.name}")
        if text.count("data-theme-cycle") != 1:
            fail(f"HTML Appearance control count is not one in {page.name}")
        if text.count("data-theme-label") != 1 or text.count("data-math-label") != 1:
            fail(f"HTML reader setting labels are missing or duplicated in {page.name}")
        if any(
            marker in text
            for marker in (
                'id="appearance-settings"',
                "data-theme-option=",
                "toolbar-theme-value",
                "control-wide",
                "control-compact",
            )
        ):
            fail(f"obsolete reader setting markup remains in {page.name}")
        for action in TEXT_SIZE_ACTIONS:
            if text.count(f'data-text-size-action="{action}"') != 1:
                fail(
                    f"HTML text-size action {action!r} is not present exactly once in {page.name}"
                )
        for label in (
            "Decrease text size",
            "Reset text size to 100%",
            "Increase text size",
        ):
            if text.count(f'aria-label="{label}"') != 1:
                fail(
                    f"HTML text-size accessibility label {label!r} is missing from {page.name}"
                )
        if text.count("data-toc-scope") != 2 or text.count("data-toc-expand") != 2:
            fail(f"HTML Contents controls are duplicated or missing in {page.name}")
        if text.count('class="build-info"') != 1:
            fail(f"HTML build stamp count is not one in {page.name}")
        if '<a href="#top">Back to top</a>' not in text:
            fail(f"HTML back-to-top link is missing from {page.name}")
        repository_link = (
            f'<a href="{html.escape(REPOSITORY_URL, quote=True)}">Repository</a>'
        )
        if repository_link not in text or f"{REPOSITORY_URL}/tree/" in text:
            fail(
                f"HTML repository link must point to the repository root in {page.name}"
            )
        if "Build: <a" in text:
            fail(f"HTML build label has an unexpected colon in {page.name}")
        if text.count('property="og:image"') != 1:
            fail(f"HTML social preview image metadata count is not one in {page.name}")
        if 'class="book-context"' in text or "data-theme-select" in text:
            fail(f"obsolete HTML header controls remain in {page.name}")
        if page_index is not None and page_index > 0:
            chapter = CHAPTER_BY_NUMBER[page_index]
            if text.count("data-section-link=") != 2 * len(chapter.sections):
                fail(
                    f"{page.name}: active chapter contents count does not match source sections"
                )

    for chapter in CHAPTERS:
        text = (PUBLICATION / f"chapter{chapter.number}.html").read_text(
            errors="replace"
        )
        if f'id="chapter-{chapter.number}"' not in text:
            fail(f"chapter{chapter.number}.html: stable chapter anchor is missing")
        if 'class="chapter-title-block"' not in text:
            fail(f"chapter{chapter.number}.html: chapter title block is missing")
        for section in chapter.sections:
            if f'id="{section_slug(section)}"' not in text:
                fail(f"chapter{chapter.number}.html: stable section anchor is missing")

    first = CHAPTERS[0]
    last = CHAPTERS[-1]
    for anchor, _ in FRONTMATTER_SECTIONS:
        if f'id="{anchor}"' not in index_text:
            fail(f"HTML front matter anchor {anchor!r} is missing")
    if "wave-motions.pdf" not in index_text or "wave-motions.epub" not in index_text:
        fail("HTML download links are incomplete")
    if "wave-motions-facsimile.pdf" in index_text:
        fail("HTML front page must not link the facsimile PDF")
    if "Original online source" in index_text:
        fail("HTML front page must not link the original online source")
    if 'id="contents"' in index_text:
        fail("inline HTML Contents block must not be rendered")
    if f'href="chapter{first.number}.html"' not in index_text:
        fail(f"front matter must navigate forward to Chapter {first.number}")
    first_page = (PUBLICATION / f"chapter{first.number}.html").read_text(
        errors="replace"
    )
    if 'href="index.html"' not in first_page:
        fail(f"Chapter {first.number} must navigate back to front matter")
    references = (PUBLICATION / "references.html").read_text(errors="replace")
    if f'href="chapter{last.number}.html"' not in references:
        fail(f"References must navigate back to Chapter {last.number}")

    validate_local_references(PUBLICATION)
    try:
        validate_offline_runtime(PUBLICATION)
    except ValueError as exc:
        fail(str(exc))
    for chapter_number, labels in canonical_equation_labels().items():
        chapter = (PUBLICATION / f"chapter{chapter_number}.html").read_text(
            errors="replace"
        )
        require_labels(chapter, labels, artifact=f"chapter{chapter_number}.html")

    print(
        f"HTML reader/publication invariants OK: inline={inline_count}, "
        f"display={display_count}, MathML boundary tables={boundary_tables} "
        f"({normalized_tables} aligned tables normalized)"
    )


def check_epub_mathml() -> None:
    require_file(EPUB)
    ns = f"{{{MATHML_NS}}}"
    with zipfile.ZipFile(EPUB) as archive:
        opf_name, opf_root = package_document(archive)
        manifest = opf_root.find("{*}manifest")
        if manifest is None:
            fail("EPUB manifest is missing")
        package_dir = Path(opf_name).parent.as_posix()
        xhtml_items: dict[str, ET.Element] = {}
        for item in manifest.findall("{*}item"):
            if item.get("media-type") != "application/xhtml+xml" or not item.get(
                "href"
            ):
                continue
            href = urllib.parse.unquote(item.get("href") or "")
            member = str(Path(package_dir, href)).replace("\\", "/")
            xhtml_items[member] = item

        math_elements: list[ET.Element] = []
        math_docs: set[str] = set()
        for name, item in xhtml_items.items():
            try:
                root = ET.fromstring(archive.read(name))
            except (KeyError, ET.ParseError) as exc:
                fail(f"cannot parse EPUB XHTML {name}: {exc}")
            current = root.findall(f".//{ns}math")
            if current:
                math_docs.add(name)
                math_elements.extend(current)
                properties = set((item.get("properties") or "").split())
                if "mathml" not in properties:
                    fail(f"EPUB manifest omits mathml property for {name}")

        if len(math_elements) < 50:
            fail(f"EPUB contains only {len(math_elements)} MathML expressions")
        displays = {math.get("display") for math in math_elements}
        if not {"inline", "block"}.issubset(displays):
            fail(
                f"EPUB lacks inline or block MathML: {sorted(str(v) for v in displays)}"
            )

        required_structures = (
            "mi",
            "mn",
            "mo",
            "msub",
            "msup",
            "mfrac",
            "mover",
            "mtable",
        )
        counts: dict[str, int] = {}
        for tag in required_structures:
            count = sum(len(math.findall(f".//{ns}{tag}")) for math in math_elements)
            counts[tag] = count
            if count == 0:
                fail(f"EPUB MathML has no <{tag}> structure")

        mi_nodes = [
            node for math in math_elements for node in math.findall(f".//{ns}mi")
        ]
        mo_nodes = [
            node for math in math_elements for node in math.findall(f".//{ns}mo")
        ]
        mi_text = ["".join(node.itertext()).strip() for node in mi_nodes]
        mo_text = ["".join(node.itertext()).strip() for node in mo_nodes]
        for symbol in EPUB_VARIABLE_SENTINELS:
            if symbol not in mi_text:
                fail(f"EPUB variable {symbol!r} is not represented as <mi>")
            if symbol in mo_text:
                fail(
                    f"EPUB variable {symbol!r} is incorrectly represented as operator <mo>"
                )

        # texmath changed its MathML serialization of named functions. Older
        # versions used <mo>sin</mo>; newer versions use an <mi> function token
        # followed by U+2061 FUNCTION APPLICATION in <mo>. Accept either
        # serialization, but require every representative function to be
        # recognized as a function rather than an ordinary variable.
        def has_named_function(name: str) -> bool:
            if name in mo_text:
                return True
            for math in math_elements:
                for parent in math.iter():
                    children = list(parent)
                    for index, child in enumerate(children[:-1]):
                        if (
                            child.tag == f"{ns}mi"
                            and "".join(child.itertext()).strip() == name
                            and children[index + 1].tag == f"{ns}mo"
                            and "".join(children[index + 1].itertext()).strip()
                            == "\u2061"
                        ):
                            return True
            return False

        for function in EPUB_OPERATOR_SENTINELS:
            if not has_named_function(function):
                fail(
                    f"EPUB named function {function!r} is not represented "
                    "with a recognized MathML function serialization"
                )

        atmosphere_math = [
            math for math in math_elements if "atmosphere" in "".join(math.itertext())
        ]
        if not atmosphere_math:
            fail("EPUB lost the p_atmosphere mathematical expression")
        if not any(
            "atmosphere"
            in "".join(
                "".join(node.itertext()).strip()
                for node in math.findall(f".//{ns}mi")
                if node.get("mathvariant") == "normal"
            )
            for math in atmosphere_math
        ):
            fail("EPUB p_atmosphere subscript is not upright semantic math text")

        epub_markup = "\n".join(
            archive.read(name).decode("utf-8", errors="replace") for name in xhtml_items
        )
        all_labels = tuple(
            label for labels in canonical_equation_labels().values() for label in labels
        )
        require_labels(epub_markup, all_labels, artifact="EPUB")

        print(
            "EPUB MathML semantics OK: "
            f"expressions={len(math_elements)}, docs={len(math_docs)}, "
            + ", ".join(f"{tag}={counts[tag]}" for tag in required_structures)
        )


def epub_accessibility_metadata(opf_root: ET.Element) -> dict[str, list[str]]:
    metadata = opf_root.find("{*}metadata")
    if metadata is None:
        fail("EPUB package metadata is missing")
    actual: dict[str, list[str]] = {}
    for element in metadata.findall("{*}meta"):
        property_name = element.get("property")
        if property_name:
            actual.setdefault(property_name, []).append((element.text or "").strip())
    return actual


def validate_epub_document_languages(
    archive: zipfile.ZipFile, opf_name: str, opf_root: ET.Element
) -> None:
    for member in manifest_xhtml_members(opf_name, opf_root):
        root = ET.fromstring(archive.read(member))
        xml_lang = root.get(f"{{{XML_NS}}}lang")
        html_lang = root.get("lang")
        if xml_lang != LANGUAGE or (html_lang is not None and html_lang != LANGUAGE):
            fail(f"EPUB XHTML {member} does not declare {LANGUAGE}")


def validate_epub_bodymatter_landmark(
    archive: zipfile.ZipFile, opf_name: str, opf_root: ET.Element
) -> None:
    nav_member = navigation_member(opf_name, opf_root)
    expected = first_bodymatter_member(archive, opf_name, opf_root)
    assert nav_member is not None and expected is not None
    root = ET.fromstring(archive.read(nav_member))
    landmarks = [
        nav
        for nav in root.findall(".//{*}nav")
        if "landmarks" in (nav.get(EPUB_TYPE) or "").split()
    ]
    if len(landmarks) != 1:
        fail(f"expected one EPUB landmarks navigation element, found {len(landmarks)}")
    links = [
        link
        for link in landmarks[0].findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    if len(links) != 1:
        fail(f"expected one EPUB bodymatter landmark, found {len(links)}")
    target = urllib.parse.unquote(
        urllib.parse.urlsplit(links[0].get("href") or "").path
    )
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(nav_member), target))
    if resolved != expected:
        fail(
            f"EPUB bodymatter landmark resolves to {resolved!r}; expected {expected!r}"
        )


def epub_alternative_bucket(value: str | None) -> str:
    if value is None:
        return "missing"
    value = value.strip()
    if not value:
        return "empty"
    if value.casefold() in EPUB_GENERIC_ALT_TEXT:
        return "generic"
    return "meaningful"


def epub_image_alternative_inventory(
    archive: zipfile.ZipFile, opf_name: str, opf_root: ET.Element
) -> tuple[int, int, int, int, int, set[str]]:
    total = meaningful = generic = empty = missing = 0
    alternatives: set[str] = set()
    for member in manifest_xhtml_members(opf_name, opf_root):
        root = ET.fromstring(archive.read(member))
        for image in root.findall(".//{*}img"):
            total += 1
            value = image.get("alt")
            bucket = epub_alternative_bucket(value)
            if bucket == "meaningful":
                meaningful += 1
                alternatives.add((value or "").strip())
            elif bucket == "generic":
                generic += 1
            elif bucket == "empty":
                empty += 1
            else:
                missing += 1
        for svg in root.findall(".//{*}svg"):
            if not svg.findall(".//{*}image"):
                continue
            total += 1
            value = svg.get("aria-label")
            if not value:
                title = svg.find(f"{{{SVG_NS}}}title")
                value = (
                    " ".join("".join(title.itertext()).split())
                    if title is not None
                    else None
                )
            bucket = epub_alternative_bucket(value)
            if bucket == "meaningful":
                meaningful += 1
                alternatives.add((value or "").strip())
            elif bucket == "generic":
                generic += 1
            elif bucket == "empty":
                empty += 1
            else:
                missing += 1
    return total, meaningful, generic, empty, missing, alternatives


def check_epub_policy() -> None:
    """Validate the completed EPUB policy after the builder's final rewrite."""
    require_file(EPUB)
    validate_structure(EPUB)
    with zipfile.ZipFile(EPUB) as archive:
        opf_name, opf_root = package_document(archive)
        metadata = opf_root.find("{*}metadata")
        manifest = opf_root.find("{*}manifest")
        spine = opf_root.find("{*}spine")
        if metadata is None or manifest is None or spine is None:
            fail("EPUB package metadata/manifest/spine is incomplete")

        title = metadata.find(f"{{{DC_NS}}}title")
        if title is None or text_content(title) != TITLE:
            got = text_content(title) if title is not None else "<missing>"
            fail(f"EPUB metadata title is incorrect: {got!r}")
        creators = [
            text_content(item) for item in metadata.findall(f"{{{DC_NS}}}creator")
        ]
        if not all(author in creators for author in AUTHORS):
            fail(f"EPUB author metadata is incomplete: {creators!r}")
        contributors = [
            text_content(item) for item in metadata.findall(f"{{{DC_NS}}}contributor")
        ]
        if EDITOR not in contributors:
            fail(f"EPUB editor metadata is missing: {contributors!r}")

        if opf_root.get(f"{{{XML_NS}}}lang") != LANGUAGE:
            fail("EPUB package language is missing")
        languages = [
            (element.text or "").strip()
            for element in metadata.findall(f"{{{DC_NS}}}language")
        ]
        if languages != [LANGUAGE]:
            fail(f"EPUB publication language is incomplete: {languages!r}")
        validate_epub_document_languages(archive, opf_name, opf_root)
        validate_epub_bodymatter_landmark(archive, opf_name, opf_root)

        actual = epub_accessibility_metadata(opf_root)
        expected: dict[str, list[str]] = {}
        for property_name, value in ACCESSIBILITY_METADATA:
            expected.setdefault(property_name, []).append(value)
        for property_name, values in expected.items():
            if actual.get(property_name) != values:
                fail(
                    f"EPUB accessibility metadata {property_name!r} is "
                    f"{actual.get(property_name)!r}; expected {values!r}"
                )
        features = set(actual.get("schema:accessibilityFeature", []))
        if features & EPUB_FALSE_ACCESSIBILITY_FEATURES:
            fail("EPUB claims accessibility features that are not fully audited")
        for element in metadata.findall("{*}meta"):
            if element.get("property") == "dcterms:conformsTo" and (
                element.text or ""
            ).strip().startswith("EPUB Accessibility"):
                fail(
                    "EPUB must not claim accessibility conformance before the audit is complete"
                )

        manifest_items = list(manifest.findall("{*}item"))
        cover_items = [
            item
            for item in manifest_items
            if "cover-image" in (item.get("properties") or "").split()
        ]
        if len(cover_items) != 1:
            fail(f"expected one EPUB cover image, found {len(cover_items)}")
        cover_member = manifest_member(opf_name, cover_items[0])
        if cover_member not in archive.namelist():
            fail(f"EPUB cover image member is missing: {cover_member}")

        nav_member = navigation_member(opf_name, opf_root)
        assert nav_member is not None
        nav_root = ET.fromstring(archive.read(nav_member))
        nav_text = " ".join(text_content(a) for a in nav_root.findall(".//{*}a"))
        for sentinel in EPUB_NAV_SENTINELS:
            if sentinel not in nav_text:
                fail(f"EPUB navigation is missing: {sentinel}")
        if nav_text.strip() == "References":
            fail("EPUB navigation regressed to a References-only title")

        spine_ids = [item.get("idref") for item in spine.findall("{*}itemref")]
        by_id = {item.get("id"): item for item in manifest_items if item.get("id")}
        if len(spine_ids) < 8 or any(item_id not in by_id for item_id in spine_ids):
            fail(
                "EPUB spine is unexpectedly short or references missing manifest items"
            )

        xhtml_names = manifest_xhtml_members(opf_name, opf_root)
        xhtml = b"\n".join(archive.read(name) for name in xhtml_names)
        if b"David C. Chapman" not in xhtml or b"Paola Malanotte-Rizzoli" not in xhtml:
            fail("EPUB text sentinel is missing")
        if b"JP1847" not in xhtml:
            fail("EPUB cover credit is missing")
        if b"<table" not in xhtml:
            fail("EPUB contains no table markup")
        image_count = sum(
            1
            for item in manifest_items
            if (item.get("media-type") or "").startswith("image/")
        )
        if image_count < 5:
            fail(f"EPUB contains only {image_count} image asset(s)")

        total, meaningful, generic, empty, missing, alternatives = (
            epub_image_alternative_inventory(archive, opf_name, opf_root)
        )
        if total == 0:
            fail("EPUB contains no images to audit for alternative text")
        for required in (FRONTISPIECE_ALTERNATIVE, COVER_ALTERNATIVE):
            if required not in alternatives:
                fail("EPUB lost a known accessible image description: " + required)

        cover_basename = cover_image_basename(opf_root)
        assert cover_basename is not None
        cover_svg_seen = False
        cover_title_found = False
        for member in xhtml_names:
            root = ET.fromstring(archive.read(member))
            for svg in root.findall(".//{*}svg"):
                if not any(
                    ref_basename(svg_image_ref(image)) == cover_basename
                    for image in svg.findall(".//{*}image")
                ):
                    continue
                cover_svg_seen = True
                title = svg.find(f"{{{SVG_NS}}}title")
                if (
                    svg.get("aria-label") == COVER_ALTERNATIVE
                    and title is not None
                    and " ".join(title.itertext()).strip() == COVER_ALTERNATIVE
                ):
                    cover_title_found = True
        if cover_svg_seen and not cover_title_found:
            fail("EPUB cover SVG is missing its native accessible title")

        info = current_build()
        label = html.escape(info.label).encode()
        url = html.escape(info.commit_url, quote=True).encode()
        if (
            xhtml.count(b'class="build-info"') != 1
            or label not in xhtml
            or url not in xhtml
        ):
            fail("EPUB exact build identity is missing or duplicated")

    print("EPUB accessibility/finalization policy OK")
    print(
        "EPUB image-alternative baseline: "
        f"total={total}, meaningful={meaningful}, generic={generic}, "
        f"empty={empty}, missing={missing}"
    )
    if generic or missing:
        print(
            "Accessibility audit remains open: scientific figure alternatives are incomplete"
        )


@cache
def pdf_text(path: Path) -> str:
    if shutil.which("pdftotext") is None:
        fail("pdftotext is required for PDF text checks")
    with tempfile.TemporaryDirectory(prefix="wave-pdf-text-") as td:
        out = Path(td) / "text.txt"
        subprocess.run(
            ["pdftotext", "-layout", str(path), str(out)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return out.read_text(errors="replace")


def check_pdf_math() -> None:
    extracted: dict[Path, str] = {}
    for path in (MODERN_PDF, FACSIMILE_PDF):
        require_file(path)
        layout_text = pdf_text(path)
        text = " ".join(layout_text.split())
        extracted[path] = layout_text
        for sentinel in (
            "like him, I put",
            "wavenumber",
            "do not exist in the Italian alphabet",
        ):
            if sentinel not in text:
                fail(
                    f"{path.name}: Paola-preface PDF text sentinel is missing: {sentinel!r}"
                )

    modern_text = extracted[MODERN_PDF]
    all_labels = tuple(
        label for labels in canonical_equation_labels().values() for label in labels
    )
    require_labels(modern_text, all_labels, artifact=MODERN_PDF.name)

    modern_log = (
        Path(
            os.environ.get(
                "WAVE_CACHE_DIR",
                str(ROOT / ".cache" / "wave-motions"),
            )
        )
        / "latex"
        / "modern"
        / "main-modern.log"
    )
    if modern_log.is_file():
        log = modern_log.read_text(errors="replace")
        warnings = []
        if "Missing character:" in log:
            warnings.append("missing glyph warning")
        if "Package amsmath Warning:" in log:
            warnings.append("amsmath warning")
        if warnings:
            print(
                "PDF math log review warning: " + ", ".join(warnings),
                file=sys.stderr,
            )

    print("PDF math/text extraction smoke checks OK")


def run_epubcheck(require: bool) -> None:
    jar = os.environ.get("EPUBCHECK_JAR")
    command = shutil.which("epubcheck")
    if jar:
        require_file(Path(jar))
        cmd = ["java", "-jar", jar, str(EPUB)]
    elif command:
        cmd = [command, str(EPUB)]
    elif require:
        fail("EPUBCheck is required but EPUBCHECK_JAR/epubcheck is unavailable")
    else:
        print("EPUBCheck not installed; standards validation skipped")
        return

    proc = subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.returncode:
        fail(f"EPUBCheck failed with status {proc.returncode}")
    print("EPUBCheck conformance validation OK")


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        fail(f"missing required command: {command}")


@cache
def pdf_pages(path: Path) -> int:
    require_command("pdfinfo")
    proc = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, flags=re.MULTILINE)
    if not match:
        fail(f"pdfinfo did not report a page count for {path}")
    return int(match.group(1))


def facsimile_log_path() -> Path:
    return LATEX_CACHE / "facsimile" / "main-facsimile.log"


def parse_facsimile_log(
    text: str,
) -> tuple[list[tuple[int, int, float]], list[tuple[int, int]]]:
    """Parse machine-readable source-boundary and shipout diagnostics."""
    boundaries: list[tuple[int, int, float]] = []
    shipouts: list[tuple[int, int]] = []
    for line in text.splitlines():
        if match := FACSIMILE_BOUNDARY_RE.fullmatch(line.strip()):
            boundaries.append(
                (int(match.group(1)), int(match.group(2)), float(match.group(3)))
            )
        elif match := FACSIMILE_SHIPOUT_RE.fullmatch(line.strip()):
            shipouts.append((int(match.group(1)), int(match.group(2))))
    return boundaries, shipouts


def facsimile_layout_diagnostics(*, strict: bool) -> None:
    log_path = facsimile_log_path()
    require_file(log_path)
    text = log_path.read_text(errors="replace")

    boundaries, shipouts = parse_facsimile_log(text)

    problems: list[str] = []
    if len(boundaries) != FACSIMILE_BODY_BOUNDARIES:
        problems.append(
            f"logged {len(boundaries)} body source-page boundaries; "
            f"expected {FACSIMILE_BODY_BOUNDARIES}"
        )
    else:
        for expected, (index, page, _spare) in enumerate(boundaries, start=1):
            if index != expected or page != expected:
                problems.append(
                    "source-page boundary drift: "
                    f"boundary {index} closed printed page {page}; expected {expected}"
                )
                break

    fac_pages = pdf_pages(FACSIMILE_PDF)
    if len(shipouts) != fac_pages:
        problems.append(
            f"logged {len(shipouts)} facsimile shipouts but PDF contains {fac_pages} pages"
        )
    else:
        for physical, page in shipouts[FACSIMILE_FRONT_MATTER_PAGES:]:
            expected_page = physical - FACSIMILE_FRONT_MATTER_PAGES
            if page != expected_page:
                problems.append(
                    "physical/printed page drift: "
                    f"physical page {physical} shipped as printed page {page}; "
                    f"expected {expected_page}"
                )
                break

    if "Overfull \\vbox" in text:
        problems.append("facsimile LaTeX log contains an overfull vertical box")

    negative = [entry for entry in boundaries if entry[2] < 0.0]
    if negative:
        index, page, spare = min(negative, key=lambda entry: entry[2])
        problems.append(
            f"printed page {page} has negative natural vertical reserve "
            f"({spare:.2f} pt) at source boundary {index}"
        )

    if problems:
        message = "; ".join(problems)
        if strict:
            fail(f"facsimile layout validation failed: {message}")
        warning("Facsimile layout", message)

    if boundaries:
        index, page, spare = min(boundaries, key=lambda entry: entry[2])
        summary = (
            f"minimum facsimile body-page reserve: {spare:.2f} pt "
            f"(printed page {page}, boundary {index})"
        )
        if spare < FACSIMILE_HEADROOM_WARNING_PT:
            warning("Facsimile headroom", summary)
        else:
            print(summary)


def check_pdf_integrity() -> None:
    require_command("pdfinfo")
    for path in (FACSIMILE_PDF, MODERN_PDF):
        require_file(path)
        if shutil.which("qpdf"):
            subprocess.run(
                ["qpdf", "--check", str(path)], check=True, stdout=subprocess.DEVNULL
            )
        else:
            subprocess.run(
                ["pdfinfo", str(path)], check=True, stdout=subprocess.DEVNULL
            )

    fac_pages = pdf_pages(FACSIMILE_PDF)
    mod_pages = pdf_pages(MODERN_PDF)
    if fac_pages != FACSIMILE_EXPECTED_PAGES:
        warning(
            "Facsimile pagination",
            f"Facsimile page count is {fac_pages}; expected "
            f"{FACSIMILE_EXPECTED_PAGES}. Pagination remains a final "
            "publication requirement.",
        )
    if mod_pages <= 0:
        fail("modern PDF has no pages")
    print(f"PDF integrity OK: facsimile={fac_pages} pages, modern={mod_pages} pages")


def check_pdf_destinations() -> None:
    logs = (
        LATEX_CACHE / "facsimile" / "main-facsimile.log",
        LATEX_CACHE / "modern" / "main-modern.log",
    )
    for log_path in logs:
        require_file(log_path)
        if "destination with the same identifier" in log_path.read_text(
            errors="replace"
        ):
            fail(f"duplicate PDF destination reported in {log_path}")
    print("PDF destination checks OK")


def check_pdf_text() -> None:
    for text in (pdf_text(FACSIMILE_PDF), pdf_text(MODERN_PDF)):
        for sentinel in (
            "When I volunteered to teach the MIT/WHOI",
            "These notes have been collected and assembled",
        ):
            if sentinel not in text:
                fail(f"PDF text sentinel is missing: {sentinel}")
    print("PDF text sentinel checks OK")


def check_pdf_render() -> None:
    require_command("pdftoppm")
    for kind, path in (("facsimile", FACSIMILE_PDF), ("modern", MODERN_PDF)):
        pages = pdf_pages(path)
        middle = pages // 2
        destination = BUILD / kind / "render-check"
        shutil.rmtree(destination, ignore_errors=True)
        destination.mkdir(parents=True, exist_ok=True)
        for page in (1, middle, pages):
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page),
                    "-l",
                    str(page),
                    "-singlefile",
                    "-r",
                    "100",
                    "-png",
                    str(path),
                    str(destination / f"page-{page}"),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        if len(list(destination.glob("page-*.png"))) != 3:
            fail(
                f"PDF render smoke check produced the wrong number of pages for {kind}"
            )
    print("PDF render smoke checks OK")


def check_publish_root() -> None:
    expected = (
        PUBLICATION / "index.html",
        PUBLICATION / "wave-motions.pdf",
        PUBLICATION / "wave-motions-facsimile.pdf",
        PUBLICATION / "wave-motions.epub",
        PUBLICATION / "SHA256SUMS",
    )
    for path in expected:
        require_file(path)
    index = (PUBLICATION / "index.html").read_text(errors="replace")
    for name in ("wave-motions.pdf", "wave-motions.epub"):
        if name not in index:
            fail(f"HTML download link is missing: {name}")
    if "wave-motions-facsimile.pdf" in index:
        fail("HTML front page must not link the facsimile PDF")
    if (PUBLICATION / "html").exists():
        fail("legacy nested HTML output exists")
    print("Publish root and download checks OK")


def check_build_identity() -> None:
    require_command("pdfinfo")
    info = current_build()
    if info.short_sha == "unknown" or info.label == "unknown":
        fail("build identity is unknown")
    label = info.label
    index = (PUBLICATION / "index.html").read_text(errors="replace")
    if (
        'class="source-link"' not in index
        or info.commit_url not in index
        or label not in index
    ):
        fail("HTML build identity is missing")
    if label not in pdf_text(MODERN_PDF):
        fail("modern PDF build identity is missing")
    pdfinfo = subprocess.run(
        ["pdfinfo", str(FACSIMILE_PDF)],
        check=True,
        capture_output=True,
        text=True,
    )
    if label not in pdfinfo.stdout:
        fail("facsimile PDF build identity is missing")
    with zipfile.ZipFile(EPUB) as archive:
        payload = b"\n".join(
            archive.read(name)
            for name in archive.namelist()
            if name.lower().endswith((".xhtml", ".html", ".opf"))
        )
    if label.encode() not in payload:
        fail("EPUB exact build identity is missing")
    print(f"Build identity OK: {label}")


def check_checksums() -> None:
    try:
        names = publication_files(PUBLICATION)
        count = verify_manifest(PUBLICATION, names)
    except (FileNotFoundError, ValueError) as exc:
        fail(str(exc))
    print(f"Checksum manifest OK: {count} files")


def check_release_gate() -> None:
    tag = (
        os.environ.get("WAVE_BUILD_VERSION") or os.environ.get("GITHUB_REF_NAME") or ""
    )
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        fail(
            "release tag must be a stable semantic version such as v1.0.0; "
            f"got: {tag or '<empty>'}"
        )
    info = current_build()
    if (
        info.version != tag
        or info.short_sha == "unknown"
        or info.label != f"{tag} ({info.short_sha})"
    ):
        fail("release build identity does not match the stable release tag")
    fac_pages = pdf_pages(FACSIMILE_PDF)
    if fac_pages != FACSIMILE_EXPECTED_PAGES:
        fail(
            f"release blocked: facsimile page count is {fac_pages}; "
            f"expected exactly {FACSIMILE_EXPECTED_PAGES}"
        )
    facsimile_layout_diagnostics(strict=True)
    try:
        validate_offline_runtime(PUBLICATION)
    except ValueError as exc:
        fail(str(exc))
    check_checksums()
    print(f"Release gate OK: {info.label}, facsimile={fac_pages} pages")


def check_publication() -> None:
    check_pdf_artifacts()
    check_epub_policy()
    check_publish_root()
    check_build_identity()
    check_checksums()


def check_pdf_artifacts() -> None:
    check_pdf_integrity()
    facsimile_layout_diagnostics(strict=False)
    check_pdf_destinations()
    check_pdf_text()
    check_pdf_render()


def check_math(require_epubcheck: bool) -> None:
    check_figure_ledger()
    check_equation_ledger()
    check_canonical_source()
    check_punctuation()
    check_readme()
    check_html()
    check_epub_mathml()
    check_pdf_math()
    run_epubcheck(require_epubcheck)
    print("Cross-format math validation OK")


def check_epub(require_epubcheck: bool) -> None:
    check_epub_policy()
    check_epub_mathml()
    run_epubcheck(require_epubcheck)
    print("EPUB validation OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate publication artifacts")
    parser.add_argument(
        "mode",
        choices=("html", "epub", "pdf", "release", "all"),
        nargs="?",
        default="all",
        help="validation scope (default: all non-release checks)",
    )
    parser.add_argument(
        "--require-epubcheck",
        action="store_true",
        help="fail EPUB/math validation unless EPUBCheck is installed and passes",
    )
    args = parser.parse_args(argv)
    if args.mode == "html":
        check_html()
    if args.mode == "all":
        check_math(args.require_epubcheck)
    if args.mode == "epub":
        check_epub(args.require_epubcheck)
    if args.mode == "all":
        check_publication()
    if args.mode == "pdf":
        check_pdf_artifacts()
    if args.mode == "release":
        check_release_gate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
