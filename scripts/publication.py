#!/usr/bin/env python3
"""Shared publication model, transformations, assets, and build identity.

The modern HTML and EPUB editions consume the same generated-only LaTeX
transformation, figure preparation, reader metadata, and build identity.
This is an importable support module; its small ``build-info`` command only
exposes the shared identity writer needed by the PDF build. Nothing written
here is a maintained source of book text: inputs always come from
``reconstruction/``.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
SOURCE = ROOT / "source"
DIST = ROOT / "dist"
FIGURES = RECON / "figures"
CACHE = Path(os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions")))
SOURCE_PAGE_CACHE = CACHE / "source-pages"
TIKZ_CACHE = CACHE / "tikz"
SOURCE_RENDER_DPI = 170
TIKZ_CACHE_VERSION = "v2"
FIGURE_ASSET_PREFIX = "assets/figures"
BOOK_TITLE = "Wave Motions in the Ocean"
PUBLICATION_TITLE = f"{BOOK_TITLE}: Myrl's View"
AUTHORS = ("David C. Chapman", "Paola Malanotte-Rizzoli")
EDITOR = "Albert M. W. Yau (digital editor)"
LANGUAGE = "en-US"
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
SITE_URL = "https://mwyau.github.io/wave-motions-in-the-ocean"
ORIGINAL_SOURCE_URL = "https://oxbow.sr.unh.edu/ChapmanRizzoli/Wave_Motions_in_the_Ocean.html"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
REPOSITORY_URL = "https://github.com/mwyau/wave-motions-in-the-ocean"
DOWNLOADS = (
    ("wave-motions.pdf", "PDF"),
    ("wave-motions-facsimile.pdf", "Facsimile PDF"),
    ("wave-motions.epub", "EPUB"),
)
CC_ICONS = ("cc", "by", "nc", "sa")

TIKZ_RENDER_TEMPLATE = r"""\documentclass{article}
\usepackage{fontspec}
\usepackage{amsmath,mathtools}
\usepackage[math-style=TeX,bold-style=TeX]{unicode-math}
\setmainfont{STIX Two Text}[Ligatures=TeX]
\setsansfont{Source Sans 3}[Ligatures=TeX,Scale=0.94]
\setmathfont{STIX Two Math}
\usepackage{graphicx,xcolor,tikz}
\usetikzlibrary{calc,decorations.pathreplacing}
\begin{document}
\newbox\wavefigurebox
\setbox\wavefigurebox=\hbox{%
\begingroup
\let\par\relax
\let\smallskip\relax
\def\center{}
\def\endcenter{}
\input{__WAVE_TIKZ_PATH__}%
\endgroup}
\pagewidth=\dimexpr\wd\wavefigurebox+10pt\relax
\pageheight=\dimexpr\ht\wavefigurebox+\dp\wavefigurebox+10pt\relax
\pdfvariable horigin 0pt
\pdfvariable vorigin 0pt
\shipout\vbox to \pageheight{%
  \offinterlineskip
  \vskip5pt
  \hbox to \pagewidth{\hskip5pt\box\wavefigurebox\hss}%
  \vss}
\end{document}
"""

SOURCEART_RE = re.compile(
    r"\\sourceart(?:\[(?P<width>[^]]+)\])?"
    r"\{(?P<pdf>[^}]+)\}\{(?P<page>\d+)\}\{(?P<trim>[^}]+)\}"
)
VECTOR_RE = re.compile(r"\\wavevectorart(?:\[(?P<width>[^]]+)\])?\{(?P<stem>[^}]+)\}")
TIKZ_INPUT_RE = re.compile(r"\\input\{figures/(?P<stem>[^}]+)\.tikz\}")
SIGNATURE_RE = re.compile(
    r"\\wavesignature\{(?P<name>[^{}]+)\}\{(?P<place>[^{}]+)\}\{(?P<year>[^{}]+)\}"
)
DIRECT_PDF_RE = re.compile(
    r"\\includegraphics\[(?P<opts>[^]]*page=(?P<page>\d+)[^]]*trim=(?P<trim>[^,\]]+)[^]]*)\]"
    r"\s*\{(?P<path>\.\./source/(?P<pdf>[^}]+))\}",
    re.S,
)
LOCAL_RASTER_RE = re.compile(
    r"\\includegraphics(?:\[[^]]*\])?\s*\{figures/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.I,
)
PDF_ONLY_RE = re.compile(
    r"\\begin\{wavepdfonly\}.*?\\end\{wavepdfonly\}",
    re.S,
)
WAVE_NUMBERED_RE = re.compile(
    r"\\begin\{(?P<env>waveequation|wavealign)\}(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    re.S,
)
NATIVE_TAGGED_EQUATION_RE = re.compile(
    r"\\begin\{equation\}(?P<body>.*?)\\tag\{(?P<tag>\d+\.\d+)\}(?P<tail>.*?)"
    r"\\end\{equation\}",
    re.S,
)
FIGURE_MARK_RE = re.compile(r"\\wavefiguremark")


def run(cmd: list[str], *, cwd: Path | None = None, quiet: bool = True) -> None:
    kwargs = {"cwd": cwd, "check": True}
    if quiet:
        kwargs.update(stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as exc:
        if quiet and exc.stderr:
            sys.stderr.write(exc.stderr[-12000:])
        raise


@lru_cache(maxsize=None)
def file_sha256(path_text: str) -> str:
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_size_points(pdf: Path, page: int) -> tuple[float, float]:
    text = subprocess.check_output(
        ["pdfinfo", "-f", str(page), "-l", str(page), "-box", str(pdf)],
        text=True,
    )
    match = re.search(rf"Page\s+{page} size:\s+([0-9.]+) x ([0-9.]+) pts", text)
    if not match:
        raise RuntimeError(f"could not determine page size for {pdf.name} page {page}")
    return float(match.group(1)), float(match.group(2))


def parse_trim(text: str) -> tuple[float, float, float, float]:
    values = re.findall(r"(-?[0-9.]+)\s*bp", text)
    if len(values) != 4:
        raise ValueError(f"expected four bp trim values, got {text!r}")
    return tuple(map(float, values))


def _asset_path(assets_root: Path, asset_prefix: str, name: str) -> Path:
    return assets_root / Path(asset_prefix) / name


def _render_pdf_page(pdf: Path, page: int, dpi: int, prefix: Path, *, quiet: bool = True) -> Path:
    run(
        [
            "pdftoppm",
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            "-r",
            str(dpi),
            "-png",
            str(pdf),
            str(prefix),
        ],
        quiet=quiet,
    )
    return prefix.with_suffix(".png")


def _crop_source_image(
    pdf: Path,
    page: int,
    trim: str,
    image_path: Path,
    destination: Path,
    *,
    angle: float = 0.0,
    optimize: bool = False,
) -> None:
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    page_width, page_height = page_size_points(pdf, page)
    left, bottom, right, top = parse_trim(trim)
    x0 = round(left / page_width * image.width)
    x1 = round(image.width - right / page_width * image.width)
    y0 = round(top / page_height * image.height)
    y1 = round(image.height - bottom / page_height * image.height)
    if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
        raise ValueError(f"invalid crop for {pdf.name} page {page}: {trim}")
    image = image.crop((x0, y0, x1, y1))
    if angle:
        image = image.rotate(angle, expand=True, fillcolor="white")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=optimize)


def source_crop(
    pdf_name: str,
    page: int,
    trim: str,
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
    angle: float = 0.0,
    dpi: int = SOURCE_RENDER_DPI,
) -> str:
    """Render and crop a source-PDF page into a publication asset directory."""
    pdf = SOURCE / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)

    pdf_digest = file_sha256(str(pdf.resolve()))
    identity = f"{pdf_name}|{pdf_digest}|{page}|{trim}|{angle:g}|dpi={dpi}"
    digest = hashlib.sha1(identity.encode()).hexdigest()[:10]
    name = f"source-{Path(pdf_name).stem}-p{page:03d}-{digest}.png"
    destination = _asset_path(assets_root, asset_prefix, name)
    if destination.exists():
        return f"{asset_prefix}/{name}"

    page_cache = SOURCE_PAGE_CACHE / (
        f"{Path(pdf_name).stem}-{pdf_digest[:12]}-p{page:03d}-r{dpi}.png"
    )
    page_cache.parent.mkdir(parents=True, exist_ok=True)
    if not page_cache.exists():
        _render_pdf_page(pdf, page, dpi, page_cache.with_suffix(""))

    _crop_source_image(
        pdf,
        page,
        trim,
        page_cache,
        destination,
        angle=angle,
        optimize=True,
    )
    return f"{asset_prefix}/{name}"


def render_source_crop(
    pdf_name: str,
    page: int,
    trim: str,
    destination: Path,
    dpi: int,
    *,
    angle: float = 0.0,
) -> None:
    """Render one source crop for figure-audit comparisons."""
    pdf = SOURCE / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    with tempfile.TemporaryDirectory(prefix="wave-source-") as temporary:
        prefix = Path(temporary) / "page"
        image_path = _render_pdf_page(pdf, page, dpi, prefix, quiet=False)
        _crop_source_image(pdf, page, trim, image_path, destination, angle=angle)


def _tikz_digest(stem: str) -> str:
    tikz = FIGURES / f"{stem}.tikz"
    return hashlib.sha256(
        TIKZ_CACHE_VERSION.encode()
        + b"\0"
        + TIKZ_RENDER_TEMPLATE.encode()
        + b"\0"
        + (ROOT / "tex-packages.txt").read_bytes()
        + b"\0"
        + tikz.read_bytes()
    ).hexdigest()[:16]


def _compile_tikz_pdf(stem: str, workdir: Path, *, quiet: bool = True) -> Path:
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.exists():
        raise FileNotFoundError(tikz)
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    tex = workdir / "figure.tex"
    tex.write_text(TIKZ_RENDER_TEMPLATE.replace("__WAVE_TIKZ_PATH__", tikz.as_posix()))
    run(
        [
            "latexmk",
            "-lualatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "figure.tex",
        ],
        cwd=workdir,
        quiet=quiet,
    )
    return workdir / "figure.pdf"


def render_tikz_svg(
    stem: str,
    assets_root: Path,
    work_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> None:
    destination = _asset_path(assets_root, asset_prefix, f"{stem}.svg")
    if destination.exists():
        return
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.exists():
        raise FileNotFoundError(tikz)

    cached_svg = TIKZ_CACHE / f"{stem}-{_tikz_digest(stem)}.svg"
    if cached_svg.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached_svg, destination)
        return

    workdir = work_root / "tikz" / stem
    pdf = _compile_tikz_pdf(stem, workdir)
    svg = workdir / "figure.svg"
    run(["pdftocairo", "-svg", str(pdf), str(svg)])
    cached_svg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(svg, cached_svg)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(svg, destination)


def render_tikz_png(stem: str, destination: Path, dpi: int) -> None:
    """Render one retained TikZ figure for figure-audit comparisons."""
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.exists():
        raise FileNotFoundError(tikz)
    with tempfile.TemporaryDirectory(prefix="wave-vector-") as temporary:
        workdir = Path(temporary) / "compile"
        pdf = _compile_tikz_pdf(stem, workdir, quiet=False)
        prefix = workdir / "render"
        run(
            [
                "pdftoppm",
                "-singlefile",
                "-r",
                str(dpi),
                "-png",
                str(pdf),
                str(prefix),
            ],
            quiet=False,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prefix.with_suffix(".png"), destination)


def referenced_tikz() -> list[str]:
    stems: set[str] = set()
    for path in [RECON / f"chapter{i}.tex" for i in range(1, 7)]:
        text = path.read_text()
        stems.update(match.group("stem") for match in VECTOR_RE.finditer(text))
        stems.update(match.group("stem") for match in TIKZ_INPUT_RE.finditer(text))
    return sorted(stems)


def prepare_vector_assets(assets_root: Path, work_root: Path) -> None:
    stems = referenced_tikz()
    workers = max(1, min(4, os.cpu_count() or 2))
    print(f"Rendering {len(stems)} TikZ figures to SVG ({workers} workers; cache enabled)...")
    failures: list[tuple[str, Exception]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(render_tikz_svg, stem, assets_root, work_root): stem
            for stem in stems
        }
        for future in as_completed(futures):
            stem = futures[future]
            try:
                future.result()
            except Exception as exc:
                failures.append((stem, exc))
    if failures:
        for stem, exc in failures:
            print(f"TikZ render failed: {stem}: {exc}", file=sys.stderr)
        raise SystemExit(f"{len(failures)} TikZ figure render(s) failed")


def copy_raster_assets(assets_root: Path, *, asset_prefix: str = FIGURE_ASSET_PREFIX) -> None:
    for raster in FIGURES.rglob("*"):
        if not raster.is_file() or raster.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        destination = _asset_path(assets_root, asset_prefix, str(raster.relative_to(FIGURES)))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raster, destination)


def prepare_assets(assets_root: Path, work_root: Path) -> None:
    """Prepare all figures used by the flowing editions under one asset root."""
    prepare_vector_assets(assets_root, work_root)
    copy_raster_assets(assets_root)


def transform_tex(
    text: str,
    chapter_number: int | None,
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> str:
    """Apply generated-only flowing-publication transformations."""
    text = PDF_ONLY_RE.sub("", text)
    text = text.replace(r"\begin{wavewebonly}", "").replace(r"\end{wavewebonly}", "")
    text = text.replace(r"\nopagecolor", "")
    text = text.replace(r"\sourcepagebreak", "")
    text = re.sub(r"\\sourcesetpage\{[^}]+\}", "", text)

    def signature_sub(match: re.Match[str]) -> str:
        return (
            "\\begin{flushright}\n"
            f"\\textit{{{match.group('name')}}}\\\\\n"
            f"{match.group('place')}, {match.group('year')}\n"
            "\\end{flushright}"
        )

    text = SIGNATURE_RE.sub(signature_sub, text)

    def vector_sub(match: re.Match[str]) -> str:
        return rf"\includegraphics{{{asset_prefix}/{match.group('stem')}.svg}}" + "\n\\wavefiguremark"

    text = VECTOR_RE.sub(vector_sub, text)
    text = TIKZ_INPUT_RE.sub(
        lambda match: rf"\includegraphics{{{asset_prefix}/{match.group('stem')}.svg}}",
        text,
    )

    def source_sub(match: re.Match[str]) -> str:
        relative = source_crop(
            match.group("pdf"),
            int(match.group("page")),
            match.group("trim"),
            assets_root,
            asset_prefix=asset_prefix,
        )
        return rf"\includegraphics{{{relative}}}" + "\n\\wavefiguremark"

    text = SOURCEART_RE.sub(source_sub, text)

    def direct_sub(match: re.Match[str]) -> str:
        options = match.group("opts")
        angle_match = re.search(r"angle\s*=\s*(-?[0-9.]+)", options)
        angle = float(angle_match.group(1)) if angle_match else 0.0
        relative = source_crop(
            match.group("pdf"),
            int(match.group("page")),
            match.group("trim"),
            assets_root,
            asset_prefix=asset_prefix,
            angle=angle,
        )
        return rf"\includegraphics{{{relative}}}"

    text = DIRECT_PDF_RE.sub(direct_sub, text)
    text = LOCAL_RASTER_RE.sub(
        lambda match: rf"\includegraphics{{{asset_prefix}/{match.group('name')}}}",
        text,
    )

    if chapter_number is None:
        text = WAVE_NUMBERED_RE.sub(lambda match: rf"\[{match.group('body')}\]", text)
        return FIGURE_MARK_RE.sub("", text)

    native_labels: list[str] = []

    def native_equation_sub(match: re.Match[str]) -> str:
        tag = match.group("tag")
        if not tag.startswith(f"{chapter_number}."):
            raise SystemExit(
                f"chapter {chapter_number}: native equation tag {tag} has wrong chapter"
            )
        native_labels.append(f"({tag})")
        body = (match.group("body") + match.group("tail")).strip()
        return (
            "\\[\n"
            + body
            + "\n\\]\n"
            "\\begin{flushright}\n\\textup{("
            + tag
            + ")}\n\\end{flushright}"
        )

    text = NATIVE_TAGGED_EQUATION_RE.sub(native_equation_sub, text)

    equation_number = 0

    def numbered_equation_sub(match: re.Match[str]) -> str:
        nonlocal equation_number
        equation_number += 1
        body = match.group("body").strip()
        if match.group("env") == "wavealign":
            body = r"\begin{aligned}" + body + r"\end{aligned}"
        label = f"({chapter_number}.{equation_number})"
        return (
            "\\[\n"
            + body
            + "\n\\]\n"
            "\\begin{flushright}\n\\textup{"
            + label
            + "}\n\\end{flushright}"
        )

    text = WAVE_NUMBERED_RE.sub(numbered_equation_sub, text)
    if native_labels and equation_number:
        raise SystemExit(
            f"chapter {chapter_number}: mixed native and editorial equation numbering is unsupported"
        )

    figure_number = 0

    def figure_mark_sub(_: re.Match[str]) -> str:
        nonlocal figure_number
        figure_number += 1
        return (
            "\\begin{center}\n"
            f"\\textsf{{Figure {chapter_number}.{figure_number}}}\n"
            "\\end{center}"
        )

    text = FIGURE_MARK_RE.sub(figure_mark_sub, text)
    expected_figures = {1: 7, 2: 10, 3: 12, 4: 30, 5: 31, 6: 14}
    if figure_number != expected_figures[chapter_number]:
        raise SystemExit(
            f"chapter {chapter_number}: expected canonical figure count, got {figure_number}"
        )
    return text


def prepare_flowing_sources(output_dir: Path, assets_root: Path) -> list[Path]:
    """Write transformed front matter and chapters for a flowing edition."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_root.mkdir(parents=True, exist_ok=True)
    frontmatter = (RECON / "frontmatter-modern.tex").read_text()
    frontmatter = frontmatter.replace(r"\tableofcontents", "")
    frontmatter_path = output_dir / "frontmatter.tex"
    frontmatter_path.write_text(transform_tex(frontmatter, None, assets_root))

    paths = [frontmatter_path]
    for chapter_number in range(1, 7):
        path = output_dir / f"chapter{chapter_number}.tex"
        path.write_text(
            transform_tex(
                (RECON / f"chapter{chapter_number}.tex").read_text(),
                chapter_number,
                assets_root,
            )
        )
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Shared book model and reader-view helpers


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


def reader_punctuation(text: str) -> str:
    """Render TeX/text punctuation for generated reader-facing display strings."""
    text = text.replace("``", "“").replace("''", "”")
    text = text.replace("`", "‘").replace("'", "’")
    return text


def tex_plain(text: str) -> str:
    """Normalize TeX enough for headings, anchors, and reader metadata."""
    text = text.replace("---", "—").replace("--", "–")
    text = text.replace(r"\'e", "é").replace(r"\'E", "É")
    text = text.replace(r'\"a', "ä").replace(r'\"o', "ö").replace(r'\"u', "ü")
    text = text.replace(r"\ell", "ℓ").replace(r"\pi", "π").replace(r"\beta", "β")
    text = text.replace("$", "")
    for cmd in ("textit", "emph", "textbf", "mathrm", "mbox"):
        text = re.sub(rf"\\{cmd}\{{([^{{}}]*)\}}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?", "", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace(r"\&", "&").replace(r"\%", "%").replace(r"\_", "_")
    return reader_punctuation(" ".join(text.split()).strip())


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
                sections=tuple(tex_plain(section) for section in section_titles),
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
            lines.append(f"   - [{section}]({chapter_url}#{section_slug(section)})")
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
    return f"This work is licensed under [CC BY-NC-SA 4.0]({LICENSE_URL}). {icons}"


# ---------------------------------------------------------------------------
# Build identity, kept here because it is shared by every publication format.


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "#": r"\#",
        "&": r"\&",
        "_": r"\_",
        "$": r"\$",
    }
    return "".join(replacements.get(char, char) for char in value)


@dataclass(frozen=True)
class BuildInfo:
    sha: str
    short_sha: str
    version: str | None

    @property
    def revision_label(self) -> str:
        return self.short_sha

    @property
    def label(self) -> str:
        return f"{self.version} ({self.revision_label})" if self.version else self.revision_label

    @property
    def commit_url(self) -> str:
        if self.sha == "unknown":
            return REPOSITORY_URL
        return f"{REPOSITORY_URL}/commit/{self.sha}"


def current_build() -> BuildInfo:
    explicit_sha = os.environ.get("WAVE_BUILD_SHA") or os.environ.get("GITHUB_SHA")
    sha = (explicit_sha or _git("rev-parse", "HEAD") or "unknown").strip()
    short_sha = sha[:7] if re.fullmatch(r"[0-9a-fA-F]{7,40}", sha) else "unknown"
    version = os.environ.get("WAVE_BUILD_VERSION")
    if not version and os.environ.get("GITHUB_REF_TYPE") == "tag":
        version = os.environ.get("GITHUB_REF_NAME")
    if not version:
        version = _git("describe", "--tags", "--exact-match", "--match", "v[0-9]*")
    return BuildInfo(sha=sha, short_sha=short_sha, version=version.strip() if version else None)


def write_build_info_tex(path: Path, info: BuildInfo | None = None) -> None:
    info = info or current_build()
    path.parent.mkdir(parents=True, exist_ok=True)
    version = info.version or ""
    path.write_text(
        "% Generated by scripts/publication.py; do not commit.\n"
        f"\\providecommand{{\\wavebuildsha}}{{{_tex_escape(info.sha)}}}\n"
        f"\\providecommand{{\\wavebuildshort}}{{{_tex_escape(info.short_sha)}}}\n"
        f"\\providecommand{{\\wavebuildversion}}{{{_tex_escape(version)}}}\n"
        f"\\providecommand{{\\wavebuildlabel}}{{{_tex_escape(info.label)}}}\n"
        f"\\providecommand{{\\wavebuildurl}}{{{_tex_escape(info.commit_url)}}}\n"
    )


def _build_info_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publication.py build-info")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sha", action="store_true")
    group.add_argument("--short", action="store_true")
    group.add_argument("--label", action="store_true")
    group.add_argument("--version", action="store_true")
    group.add_argument("--url", action="store_true")
    group.add_argument("--tex", type=Path)
    args = parser.parse_args(argv)
    info = current_build()
    if args.tex:
        write_build_info_tex(args.tex, info)
    elif args.sha:
        print(info.sha)
    elif args.short:
        print(info.short_sha)
    elif args.label:
        print(info.label)
    elif args.version:
        print(info.version or "")
    elif args.url:
        print(info.commit_url)
    else:
        print(info.label)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shared publication support utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-info", help="print or write the current build identity")
    args, remainder = parser.parse_known_args(argv)
    if args.command == "build-info":
        return _build_info_cli(remainder)
    raise SystemExit(f"unsupported publication command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
