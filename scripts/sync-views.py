#!/usr/bin/env python3
"""Keep README and HTML publication views synchronized with canonical LaTeX.

The LaTeX sources remain authoritative. README-only Shields badges are preserved
verbatim; front matter, contents, downloads, and license text are regenerated from
canonical sources. The HTML operation installs the same contents/download/license
model and stable section anchors into the already generated Pages files.
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from book_views import (
    DOWNLOADS,
    RECON,
    ROOT,
    book_structure,
    html_contents,
    html_license,
    markdown_contents,
    markdown_license,
    section_slug,
)

README = ROOT / "README.md"
OUT = ROOT / "dist"
FRONTMATTER = RECON / "frontmatter-modern.tex"
BADGES_START = "<!-- README_BADGES_START -->"
BADGES_END = "<!-- README_BADGES_END -->"
DEFAULT_BADGES = (
    "[![Read Online](https://img.shields.io/badge/Read-Online-0969da)]"
    "(https://mwyau.github.io/wave-motions-in-the-ocean/) "
    "[![Read PDF](https://img.shields.io/badge/Read-PDF-b31b1b)]"
    "(https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf) "
    "[![Read EPUB](https://img.shields.io/badge/Read-EPUB-85b916)]"
    "(https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.epub) "
    "[![CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-3c5c99)]"
    "(https://creativecommons.org/licenses/by-nc-sa/4.0/) "
    "[![Publish](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/"
    "publish.yml/badge.svg?branch=main)]"
    "(https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml)"
)
SIGNATURE_RE = re.compile(
    r"\\wavesignature\{(?P<name>[^{}]+)\}\{(?P<place>[^{}]+)\}\{(?P<year>[^{}]+)\}"
)
LOCAL_RASTER_RE = re.compile(
    r"\\includegraphics(?P<opts>\[[^]]*\])?\s*\{figures/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.I,
)


def require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"missing required command: {command}")


def preserve_badges(current: str) -> str:
    marked = re.search(
        re.escape(BADGES_START) + r"\n(?P<body>.*?)\n" + re.escape(BADGES_END),
        current,
        re.S,
    )
    if marked:
        return marked.group("body").strip()
    for line in current.splitlines():
        if "img.shields.io" in line:
            return line.strip()
    return DEFAULT_BADGES


def smart_title_case(title: str) -> str:
    small = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}
    words = title.lower().split()
    return " ".join(
        word.capitalize() if i == 0 or word not in small else word
        for i, word in enumerate(words)
    )


def title_metadata(text: str) -> tuple[str, str, str, str, str, str, str]:
    title_page = text.split(r"\clearpage", 1)[0]
    title_match = re.search(r"\\bfseries\s+([^\\{}]+?)\\par", title_page)
    subtitle_match = re.search(r"\\itshape\s+([^\\{}]+?)\\par", title_page)
    dedication_match = re.search(
        r"\\textit\{Presented to\}\s*\\textbf\{([^{}]+)\}", title_page
    )
    author_match = re.search(
        r"\\vfill\s*\{\\large\s+\\textbf\{(?P<authors>[^{}]+)\}\\par\}"
        r"\s*\\vspace\{[^}]+\}\s*\{\\normalsize\s+(?P<date>[^\\{}]+?)\\par\}",
        title_page,
        re.S,
    )
    editor_match = re.search(
        r"Digital edition by\s*\\textbf\{(?P<editor>[^{}]+)\}\\par\}"
        r"\s*\\vspace\{[^}]+\}\s*\{\\small\\sffamily\s+(?P<date>[^\\{}]+?)\\par\}",
        title_page,
        re.S,
    )
    if not all((title_match, subtitle_match, dedication_match, author_match, editor_match)):
        raise ValueError("could not parse modern title-page metadata")
    return (
        smart_title_case(title_match.group(1).strip()),
        subtitle_match.group(1).strip(),
        dedication_match.group(1).strip(),
        author_match.group("authors").strip(),
        author_match.group("date").strip(),
        editor_match.group("editor").strip(),
        editor_match.group("date").strip(),
    )


def frontmatter_markdown(text: str) -> str:
    require("pandoc")
    if r"\clearpage" not in text:
        raise ValueError("modern front matter has no title-page boundary")
    body = text.split(r"\clearpage", 1)[1]
    body = body.split(r"\tableofcontents", 1)[0]
    body = re.sub(r"\\wavepagenumbering\{[^}]+\}\s*", "", body)
    body = re.sub(r"\\addcontentsline\{toc\}\{chapter\}\{[^\n]*\}\s*", "", body)
    body = body.replace(r"\clearpage", "")

    def signature(m: re.Match[str]) -> str:
        return (
            "\\par\\medskip\n\\noindent\\textit{"
            + f"{m.group('place')} --- {m.group('name')}, {m.group('year')}"
            + "}\\par"
        )

    body = SIGNATURE_RE.sub(signature, body)
    body = LOCAL_RASTER_RE.sub(
        lambda m: rf"\includegraphics{m.group('opts') or ''}"
        rf"{{reconstruction/figures/{m.group('name')}}}",
        body,
    )
    with tempfile.TemporaryDirectory(prefix="wave-readme-") as td:
        src = Path(td) / "frontmatter.tex"
        src.write_text(body)
        proc = subprocess.run(
            ["pandoc", str(src), "-f", "latex", "-t", "gfm", "--wrap=preserve"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    rendered = proc.stdout.strip()
    # README already has a single H1 title; front-matter divisions are H2.
    rendered = re.sub(r"(?m)^# ", "## ", rendered)
    return rendered


def expected_readme(current: str) -> str:
    source = FRONTMATTER.read_text()
    title, subtitle, dedicatee, authors, original_date, editor, digital_date = title_metadata(source)
    badges = preserve_badges(current)
    header = (
        f"# {title}: {subtitle}\n\n"
        f"*Presented to* **{dedicatee}**\n\n"
        f"**{authors}** — {original_date}\n\n"
        f"Digital edition by **{editor}** — {digital_date}\n\n"
        f"{BADGES_START}\n{badges}\n{BADGES_END}"
    )
    return (
        header
        + "\n\n"
        + frontmatter_markdown(source)
        + "\n\n"
        + markdown_contents()
        + "\n\n"
        + markdown_license()
        + "\n"
    )


def write_readme(*, check: bool) -> None:
    current = README.read_text() if README.exists() else ""
    expected = expected_readme(current)
    if check:
        if current != expected:
            diff = "".join(
                difflib.unified_diff(
                    current.splitlines(keepends=True),
                    expected.splitlines(keepends=True),
                    fromfile="README.md",
                    tofile="README.md (generated)",
                )
            )
            sys.stderr.write(diff[:16000])
            raise SystemExit(
                "README.md is out of sync; run: python3 scripts/sync-views.py --readme"
            )
        print("README sync OK")
        return
    README.write_text(expected)
    print("README.md synchronized from canonical LaTeX")


def install_stable_section_ids() -> None:
    h2_re = re.compile(r"<h2(?P<attrs>[^>]*)>(?P<body>.*?)</h2>", re.S | re.I)
    for chapter in book_structure():
        page = OUT / f"chapter{chapter.number}.html"
        if not page.exists():
            raise SystemExit(f"missing generated HTML page: {page}")
        text = page.read_text(errors="replace")
        index = 0

        def repl(m: re.Match[str]) -> str:
            nonlocal index
            if index >= len(chapter.sections):
                return m.group(0)
            section = chapter.sections[index]
            index += 1
            attrs = re.sub(r'\s+id="[^"]*"', "", m.group("attrs"), flags=re.I)
            return f'<h2 id="{section_slug(section)}"{attrs}>{m.group("body")}</h2>'

        updated = h2_re.sub(repl, text)
        if index != len(chapter.sections):
            raise SystemExit(
                f"{page.name}: found {index} section headings, expected {len(chapter.sections)}"
            )
        page.write_text(updated)


def sync_html() -> None:
    install_stable_section_ids()
    index = OUT / "index.html"
    if not index.exists():
        raise SystemExit(f"missing generated HTML index: {index}")
    text = index.read_text(errors="replace")
    block_re = re.compile(
        r'<section class="book-toc">.*?</section>\s*<p class="license">.*?</p>',
        re.S | re.I,
    )
    available_downloads = tuple(item for item in DOWNLOADS if (OUT / item[0]).is_file())
    replacement = html_contents(downloads=available_downloads) + "\n" + html_license()
    text, count = block_re.subn(lambda _: replacement, text, count=1)
    if count != 1:
        raise SystemExit("could not locate generated Contents/Downloads/license block in index.html")
    index.write_text(text)
    print("HTML contents/downloads/license synchronized from canonical LaTeX")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--readme", action="store_true", help="rewrite README.md")
    group.add_argument("--check-readme", action="store_true", help="fail if README.md is stale")
    group.add_argument("--html", action="store_true", help="synchronize generated dist HTML")
    args = parser.parse_args()
    if args.readme:
        write_readme(check=False)
    elif args.check_readme:
        write_readme(check=True)
    else:
        sync_html()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
