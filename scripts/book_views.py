#!/usr/bin/env python3
"""Shared publication metadata and navigation derived from the LaTeX sources."""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
SITE_URL = "https://mwyau.github.io/wave-motions-in-the-ocean"
ORIGINAL_SOURCE_URL = "https://oxbow.sr.unh.edu/ChapmanRizzoli/Wave_Motions_in_the_Ocean.html"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
DOWNLOADS = (
    ("wave-motions.pdf", "PDF"),
    ("wave-motions-facsimile.pdf", "Facsimile PDF"),
    ("wave-motions.epub", "EPUB"),
)
CC_ICONS = ("cc", "by", "nc", "sa")


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    sections: tuple[str, ...]


def _balanced_command_args(text: str, command: str) -> list[str]:
    marker = "\\" + command + "{"
    out: list[str] = []
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start < 0:
            break
        i = start + len(marker)
        depth = 1
        while i < len(text) and depth:
            if text[i] == "{" and (i == 0 or text[i - 1] != "\\"):
                depth += 1
            elif text[i] == "}" and (i == 0 or text[i - 1] != "\\"):
                depth -= 1
            i += 1
        if depth:
            raise ValueError(f"unbalanced \\{command} in source")
        out.append(text[start + len(marker) : i - 1])
        pos = i
    return out


def tex_plain(text: str) -> str:
    # Enough TeX normalization for headings/anchors; prose remains rendered by Pandoc.
    text = text.replace("---", "—").replace("--", "–")
    text = text.replace(r"\'e", "é").replace(r"\'E", "É")
    text = text.replace(r'\"a', "ä").replace(r'\"o', "ö").replace(r'\"u', "ü")
    text = text.replace(r"\ell", "ℓ").replace(r"\pi", "π").replace(r"\beta", "β")
    text = text.replace("$", "")
    for cmd in ("textit", "emph", "textbf", "mathrm", "rm", "mbox"):
        text = re.sub(rf"\\{cmd}\{{([^{{}}]*)\}}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?", "", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace(r"\&", "&").replace(r"\%", "%").replace(r"\_", "_")
    return " ".join(text.split()).strip()


def section_slug(title: str) -> str:
    plain = tex_plain(title)
    ascii_text = unicodedata.normalize("NFKD", plain).encode("ascii", "ignore").decode()
    ascii_text = ascii_text.replace("'", "").replace("’", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    if not slug:
        raise ValueError(f"cannot make section anchor from {title!r}")
    return slug


def book_structure() -> tuple[Chapter, ...]:
    chapters: list[Chapter] = []
    for number in range(1, 7):
        path = RECON / f"chapter{number}.tex"
        text = path.read_text()
        chapter_titles = _balanced_command_args(text, "chapter")
        if len(chapter_titles) != 1:
            raise ValueError(f"{path}: expected one \\chapter, found {len(chapter_titles)}")
        section_titles = tuple(_balanced_command_args(text, "section"))
        chapters.append(
            Chapter(
                number=number,
                title=tex_plain(chapter_titles[0]),
                sections=tuple(tex_plain(s) for s in section_titles),
            )
        )
    return tuple(chapters)


def html_contents(*, downloads: tuple[tuple[str, str], ...] = DOWNLOADS) -> str:
    items: list[str] = []
    for chapter in book_structure():
        sections = "".join(
            f'<li><a href="chapter{chapter.number}.html#{section_slug(section)}">'
            f"{html.escape(section)}</a></li>"
            for section in chapter.sections
        )
        nested = f"<ul>{sections}</ul>" if sections else ""
        items.append(
            f'<li><a href="chapter{chapter.number}.html">'
            f"{html.escape(chapter.title)}</a>{nested}</li>"
        )
    download_html = ""
    if downloads:
        links = "".join(
            f'<li><a href="{filename}">{html.escape(label)}</a></li>'
            for filename, label in downloads
        )
        download_html = f"<h2>Downloads</h2><ul>{links}</ul>"
    return (
        '<section class="book-toc" id="contents"><h2>Contents</h2><ol>'
        + "".join(items)
        + '</ol><p><a href="references.html">References</a> · '
        + f'<a href="{ORIGINAL_SOURCE_URL}">Original online source</a></p>'
        + download_html
        + "</section>"
    )


def markdown_contents() -> str:
    lines = ["## Contents", ""]
    for chapter in book_structure():
        chapter_url = f"{SITE_URL}/chapter{chapter.number}.html"
        lines.append(f"{chapter.number}. [{chapter.title}]({chapter_url})")
        for section in chapter.sections:
            lines.append(
                f"   - [{section}]({chapter_url}#{section_slug(section)})"
            )
    lines.extend(
        [
            "",
            f"[References]({SITE_URL}/references.html)",
            f"[Original online source]({ORIGINAL_SOURCE_URL})",
            "",
            "## Downloads",
            "",
        ]
    )
    for filename, label in DOWNLOADS:
        lines.append(f"- [{label}]({SITE_URL}/{filename})")
    return "\n".join(lines)


def html_license() -> str:
    icons = "".join(
        f'<img src="https://mirrors.creativecommons.org/presskit/icons/{name}.svg" '
        'alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">'
        for name in CC_ICONS
    )
    return (
        '<p class="license">This work is licensed under '
        f'<a href="{LICENSE_URL}">CC BY-NC-SA 4.0</a>{icons}</p>'
    )


def markdown_license() -> str:
    icons = " ".join(
        f'<img src="https://mirrors.creativecommons.org/presskit/icons/{name}.svg" '
        'alt="" width="16" height="16">'
        for name in CC_ICONS
    )
    return (
        f"This work is licensed under [CC BY-NC-SA 4.0]({LICENSE_URL}). {icons}"
    )
