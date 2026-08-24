#!/usr/bin/env python3
"""Keep the maintained README synchronized with the LaTeX publication source.

HTML generation owns its complete output. This command intentionally has no
HTML mutation mode; the README remains the only maintained view synchronized
outside the edition builders.
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

from publication import (
    CONTACT_EMAIL,
    DOWNLOADS,
    ROOT,
    SITE_URL,
    SRC,
    markdown_license,
    reader_punctuation,
)

README = ROOT / "README.md"
FRONTMATTER = SRC / "frontmatter-modern.tex"
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
    "[![Build](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/"
    "publish.yml/badge.svg?branch=main)]"
    "(https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml)"
)
SIGNATURE_RE = re.compile(
    r"\\wavesignature\{(?P<name>[^{}]+)\}\{(?P<place>[^{}]+)\}\{(?P<year>[^{}]+)\}"
)
LOCAL_RASTER_RE = re.compile(
    r"\\includegraphics(?P<opts>\[[^]]*\])?\s*\{(?P<directory>figures|images)/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.IGNORECASE,
)


def require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"missing required command: {command}")


def preserve_badges(current: str) -> str:
    marked = re.search(
        re.escape(BADGES_START) + r"\n(?P<body>.*?)\n" + re.escape(BADGES_END),
        current,
        re.DOTALL,
    )
    if marked:
        return marked.group("body").strip()
    return DEFAULT_BADGES


def smart_title_case(title: str) -> str:
    small = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "in",
        "of",
        "on",
        "or",
        "the",
        "to",
    }
    words = title.lower().split()
    return " ".join(
        word.capitalize() if index == 0 or word not in small else word
        for index, word in enumerate(words)
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
        re.DOTALL,
    )
    editor_match = re.search(
        r"Edited by\s*\\textbf\{(?P<editor>[^{}]+)\}\\par\}"
        r"\s*\\vspace\{[^}]+\}\s*\{\\small\\sffamily\s+(?P<date>[^\\{}]+?)\\par\}",
        title_page,
        re.DOTALL,
    )
    if not all(
        (title_match, subtitle_match, dedication_match, author_match, editor_match)
    ):
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
    body = re.sub(r"\\addcontentsline\{toc\}\{chapter\}\{[^\n]*\}\s*", "", body)
    body = body.replace(r"\clearpage", "")

    def signature(match: re.Match[str]) -> str:
        return (
            "\\par\\medskip\n\\noindent\\textit{"
            + f"{match.group('place')} --- {match.group('name')}, {match.group('year')}"
            + "}\\par"
        )

    body = SIGNATURE_RE.sub(signature, body)
    body = LOCAL_RASTER_RE.sub(
        lambda match: (
            rf"\includegraphics{match.group('opts') or ''}"
            rf"{{src/{match.group('directory')}/{match.group('name')}}}"
        ),
        body,
    )
    with tempfile.TemporaryDirectory(prefix="wave-readme-") as temporary:
        source = Path(temporary) / "frontmatter.tex"
        source.write_text(body)
        process = subprocess.run(
            [
                "pandoc",
                str(source),
                "-f",
                "latex+smart",
                "-t",
                "gfm",
                "--wrap=preserve",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    rendered = process.stdout.strip()
    rendered = re.sub(r"(?m)^# ", "## ", rendered)
    rendered = re.sub(
        r'<img src="src/images/salmon-hendershott-como-1980\.jpg"[^>]*>',
        '<img src="src/images/salmon-hendershott-como-1980.jpg" width="420" />',
        rendered,
    )
    return rendered


def read_download_markdown() -> str:
    lines = ["## Read and download", "", f"- [HTML]({SITE_URL}/)"]
    for filename, label in DOWNLOADS:
        if filename == "wave-motions-facsimile.pdf":
            continue
        lines.append(f"- [{label}]({SITE_URL}/{filename})")
    lines.extend(["", f"Contact: [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})"])
    return "\n".join(lines)


def expected_readme(current: str) -> str:
    source = FRONTMATTER.read_text()
    title, subtitle, dedicatee, authors, original_date, editor, digital_date = (
        title_metadata(source)
    )
    badges = preserve_badges(current)
    header = (
        f"# {reader_punctuation(title)}: {reader_punctuation(subtitle)}\n\n"
        f"*Presented to* **{reader_punctuation(dedicatee)}**\n\n"
        f"**{reader_punctuation(authors)}** — {reader_punctuation(original_date)}\n\n"
        f"Edited by **{reader_punctuation(editor)}** — {reader_punctuation(digital_date)}\n\n"
        f"{BADGES_START}\n{badges}\n{BADGES_END}"
    )
    return (
        header
        + "\n\n"
        + frontmatter_markdown(source)
        + "\n\n"
        + read_download_markdown()
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
                "README.md is out of sync; run: uv run --frozen python scripts/sync_readme.py"
            )
        print("README sync OK")
        return
    README.write_text(expected)
    print("README.md synchronized from LaTeX sources")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if README.md is stale"
    )
    args = parser.parse_args()
    write_readme(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
