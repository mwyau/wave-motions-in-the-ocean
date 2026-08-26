#!/usr/bin/env python3
"""Shared publication model, transformations, assets, and build identity.

The modern HTML and EPUB editions consume the same generated-only LaTeX
transformation, figure preparation, reader metadata, and build identity.
This is an importable support module; its small ``build-info`` command only
exposes the shared identity writer needed by the PDF build. Nothing written
here is a maintained source of book text: inputs always come from
``src/``.
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
import tarfile
import tempfile
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REFERENCES = ROOT / "references"
SOURCE_DIR = REFERENCES / "chapman-rizzoli-1989"
FIGURES = SRC / "figures"
IMAGE_DIRS = (FIGURES, SRC / "images")
CACHE = Path(os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions")))
SOURCE_PAGE_CACHE = CACHE / "source-pages"
TIKZ_CACHE = CACHE / "tikz"
SOURCE_RENDER_DPI = 170
SOURCE_CROP_VERSION = "v1"
TIKZ_CACHE_VERSION = "v3"
FIGURE_ASSET_PREFIX = "assets/figures"
BOOK_TITLE = "Wave Motions in the Ocean"
PUBLICATION_TITLE = f"{BOOK_TITLE}: Myrl's View"
AUTHORS = ("David C. Chapman", "Paola Malanotte-Rizzoli")
EDITOR = "Albert M. W. Yau"
CONTACT_EMAIL = "albert@mwyau.com"
LANGUAGE = "en-US"
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
SITE_URL = "https://mwyau.github.io/wave-motions-in-the-ocean"
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
    r"(?:\[(?P<mask>[^]]+)\])?"
)
VECTOR_RE = re.compile(r"\\wavevectorart(?:\[(?P<width>[^]]+)\])?\{(?P<stem>[^}]+)\}")
TIKZ_INPUT_RE = re.compile(r"\\input\{figures/(?P<stem>[^}]+)\.tikz\}")
TIKZ_SOURCE_RE = re.compile(
    r"^% wave-source:\s*pdf=(?P<pdf>[^;]+);\s*page=(?P<page>\d+);\s*"
    r"trim=(?P<trim>[^\n]+)$",
    re.MULTILINE,
)
TIKZ_MASK_RE = re.compile(
    r"^% wave-source-mask:\s*pdf=(?P<pdf>[^;]+);\s*page=(?P<page>\d+);\s*"
    r"rect=(?P<rect>[^;]+);\s*origin=lower-left(?:;[^\n]*)?$",
    re.MULTILINE,
)
SVG_DIGEST_RE = re.compile(
    r"<!--\s*wave-generated-sha256:\s*(?P<digest>[0-9a-f]{16,64})\s*-->"
)
SIGNATURE_RE = re.compile(
    r"\\wavesignature\{(?P<name>[^{}]+)\}\{(?P<place>[^{}]+)\}\{(?P<year>[^{}]+)\}"
)
DIRECT_PDF_RE = re.compile(
    r"\\includegraphics\[(?P<opts>[^]]*page=(?P<page>\d+)[^]]*trim=(?P<trim>[^,\]]+)[^]]*)\]"
    r"\s*\{(?P<path>\.\./references/chapman-rizzoli-1989/(?P<pdf>[^}]+))\}",
    re.DOTALL,
)
LOCAL_RASTER_RE = re.compile(
    r"\\includegraphics(?:\[[^]]*\])?\s*\{(?:figures|images)/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.IGNORECASE,
)
PDF_ONLY_RE = re.compile(
    r"\\begin\{wavepdfonly\}.*?\\end\{wavepdfonly\}",
    re.DOTALL,
)
WAVE_NUMBERED_RE = re.compile(
    r"\\begin\{(?P<env>waveequation|wavealign)\}(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    re.DOTALL,
)
NATIVE_TAGGED_EQUATION_RE = re.compile(
    r"\\begin\{equation\}(?P<body>.*?)\\tag\{(?P<tag>\d+\.\d+)\}(?P<tail>.*?)"
    r"\\end\{equation\}",
    re.DOTALL,
)
FIGURE_MARK_RE = re.compile(r"\\wavefiguremark")
EQUATION_DISPLAY_ENVS = frozenset(
    {
        "align",
        "align*",
        "equation",
        "equation*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "wavealign",
        "waveequation",
    }
)
EQUATION_PAGE_RE = re.compile(
    r"^%\s*Source printed page (?P<printed>\d+) / "
    r"(?:source )?physical page (?P<physical>\d+)\s*$"
)
EQUATION_BEGIN_RE = re.compile(r"^\s*\\begin\{(?P<environment>[^}]+)\}\s*$")
EQUATION_STEM_RE = re.compile(r"ch\d{2}-p\d{3}-e\d{2,}")

FIGURE_LEDGER_CHAPTERS = tuple(range(1, 7))
FIGURE_REPRESENTATIONS = frozenset({"vector", "source-pdf"})
FIGURE_LEDGER_VERSION = 2
FIGURE_ENTRY_RE = re.compile(
    r"^#### Figure (?P<chapter>[1-6])\.(?P<number>\d+) — (?P<title>.+)$",
    re.MULTILINE,
)
FIGURE_PAGE_RE = re.compile(r"^- \*\*Printed page:\*\* (?P<page>\d+)$", re.MULTILINE)
FIGURE_ASSET_RE = re.compile(r"^- \*\*Asset:\*\* `(?P<asset>[^`]+)`$", re.MULTILINE)
FIGURE_REPRESENTATION_RE = re.compile(
    r"^- \*\*Representation:\*\* (?P<representation>[^\s]+)$", re.MULTILINE
)

EQUATION_SOURCE_PDFS = {
    1: "ChapmanRizzoli0_2.pdf",
    2: "ChapmanRizzoli0_2.pdf",
    3: "ChapmanRizzoli3.pdf",
    4: "ChapmanRizzoli4.pdf",
    5: "ChapmanRizzoli5.pdf",
    6: "ChapmanRizzoli6.pdf",
}
EQUATION_ASSET_KINDS = ("source", "mathjax", "mathml")
EQUATION_LEDGER_VERSION = 2
EQUATION_SOURCE_DPI = 300
EQUATION_ASSET_VERSION = "v2"
EQUATION_RENDER_CONFIG = {
    "source": ("source-pdf", "v2", "pdf-raster;dpi=300;recorded-page-crop"),
    "mathjax": (
        "chromium-mathjax",
        "3.2.2",
        "chtml;scale=2;viewport=content;background=white",
    ),
    "mathml": (
        "chromium-native-mathml",
        "3.7",
        "pandoc-3.7;scale=2;viewport=content;background=white",
    ),
}
EQUATION_SOURCE_CROP_RE = re.compile(
    r"^(?P<x>\d+),(?P<y>\d+),(?P<width>\d+),(?P<height>\d+)@"
    r"(?P<dpi>\d+)dpi$"
)
EQUATION_CHAPTER_HEADING_RE = re.compile(
    r"^### Chapter (?P<chapter>[1-6])\s*$", re.MULTILINE
)
MANIFEST_ENTRY_RE = re.compile(r"^(?P<digest>[0-9a-f]{64})  (?P<entry>\S+)$")


def run(cmd: list[str], *, cwd: Path | None = None, quiet: bool = True) -> None:
    stdout = subprocess.DEVNULL if quiet else None
    stderr = subprocess.PIPE if quiet else None
    try:
        subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=stdout,
            stderr=stderr,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if quiet and exc.stderr:
            sys.stderr.write(exc.stderr[-12000:])
        raise


@cache
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


def parse_mask(text: str) -> tuple[float, float, float, float]:
    number = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
    bp_match = re.fullmatch(
        rf"\s*({number})\s*bp\s+({number})\s*bp\s+"
        rf"({number})\s*bp\s+({number})\s*bp\s*",
        text,
    )
    slash_match = re.fullmatch(
        rf"\s*({number})\s*/\s*({number})\s*/\s*"
        rf"({number})\s*/\s*({number})\s*",
        text,
    )
    match = bp_match or slash_match
    if match is None:
        raise ValueError(
            f"expected four PDF mask coordinates in bp or slash form, got {text!r}"
        )
    return tuple(map(float, match.groups()))


def _validate_mask_boxes(
    masks: tuple[tuple[float, float, float, float], ...],
    page_width: float,
    page_height: float,
    trim: str,
) -> None:
    left, bottom, right, top = parse_trim(trim)
    crop = (left, bottom, page_width - right, page_height - top)
    if not (
        0 <= crop[0] < crop[2] <= page_width and 0 <= crop[1] < crop[3] <= page_height
    ):
        raise ValueError(f"invalid crop for source page: {trim}")
    for mask in masks:
        x0, y0, x1, y1 = mask
        if not (0 <= x0 < x1 <= page_width and 0 <= y0 < y1 <= page_height):
            raise ValueError(
                f"mask must be a non-reversed rectangle inside the source page: {mask}"
            )
        if not (
            max(x0, crop[0]) < min(x1, crop[2]) and max(y0, crop[1]) < min(y1, crop[3])
        ):
            raise ValueError(f"mask does not intersect the final crop: {mask}")


def _mask_box_pixels(
    mask: tuple[float, float, float, float],
    page_width: float,
    page_height: float,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    x0_pt, y0_pt, x1_pt, y1_pt = mask
    return (
        round(x0_pt / page_width * image_width),
        round(image_height - y1_pt / page_height * image_height),
        round(x1_pt / page_width * image_width),
        round(image_height - y0_pt / page_height * image_height),
    )


def _asset_path(assets_root: Path, asset_prefix: str, name: str) -> Path:
    return assets_root / Path(asset_prefix) / name


def figure_asset_paths(stem: str) -> tuple[Path, Path, Path]:
    """Return the maintained TikZ, SVG, and source-PNG paths for a stem."""
    path = Path(stem)
    if path.name != stem or path.suffix:
        raise ValueError(f"figure stem must be a plain basename, got {stem!r}")
    return (
        FIGURES / f"{stem}.tikz",
        FIGURES / f"{stem}.svg",
        FIGURES / f"{stem}.png",
    )


def maintained_tikz_stems() -> tuple[str, ...]:
    """Return all maintained vector figure stems in stable order."""
    return tuple(sorted(path.stem for path in FIGURES.glob("*.tikz")))


def _format_bp(value: float) -> str:
    return f"{value:g}bp"


def _format_source_masks(
    masks: tuple[tuple[float, float, float, float], ...],
) -> str:
    if not masks:
        return "none"
    return "; ".join(" ".join(_format_bp(value) for value in mask) for mask in masks)


def _source_png_metadata(
    pdf_name: str,
    page: int,
    trim: str,
    masks: tuple[tuple[float, float, float, float], ...],
    pdf_digest: str,
    dpi: int,
    angle: float,
) -> dict[str, str]:
    return {
        "wave-source-pdf": pdf_name,
        "wave-source-pdf-sha256": pdf_digest,
        "wave-source-page": str(page),
        "wave-source-trim": trim,
        "wave-source-masks": _format_source_masks(masks),
        "wave-source-dpi": str(dpi),
        "wave-source-angle": f"{angle:g}",
        "wave-source-renderer": SOURCE_CROP_VERSION,
    }


def _render_pdf_page(
    pdf: Path, page: int, dpi: int, prefix: Path, *, quiet: bool = True
) -> Path:
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
    masks: tuple[tuple[float, float, float, float], ...] = (),
    metadata: dict[str, str] | None = None,
) -> None:
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    page_width, page_height = page_size_points(pdf, page)
    left, bottom, right, top = parse_trim(trim)
    if masks:
        _validate_mask_boxes(masks, page_width, page_height, trim)
        draw = ImageDraw.Draw(image)
        for mask in masks:
            draw.rectangle(
                _mask_box_pixels(
                    mask,
                    page_width,
                    page_height,
                    image.width,
                    image.height,
                ),
                fill="white",
            )
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
    save_kwargs: dict[str, object] = {"optimize": optimize}
    if metadata:
        pnginfo = PngInfo()
        for key, value in metadata.items():
            pnginfo.add_text(key, value)
        save_kwargs["pnginfo"] = pnginfo
    image.save(destination, **save_kwargs)


def source_crop(
    pdf_name: str,
    page: int,
    trim: str,
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
    angle: float = 0.0,
    dpi: int = SOURCE_RENDER_DPI,
    asset_name: str | None = None,
    mask: str | None = None,
    masks: tuple[tuple[float, float, float, float], ...] = (),
) -> str:
    """Render and crop a source-PDF page into a publication asset directory."""
    if Path(pdf_name).name != pdf_name:
        raise ValueError(f"source PDF must be a filename, got {pdf_name!r}")
    pdf = SOURCE_DIR / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)

    pdf_digest = file_sha256(str(pdf.resolve()))
    parsed_masks = masks
    if mask is not None:
        parsed_masks = (parse_mask(mask),)
    if parsed_masks:
        _validate_mask_boxes(
            parsed_masks,
            *page_size_points(pdf, page),
            trim,
        )
    identity = f"{pdf_name}|{pdf_digest}|{page}|{trim}|{angle:g}|dpi={dpi}|masks={parsed_masks}"
    digest = hashlib.sha1(identity.encode()).hexdigest()[:10]
    if asset_name is None:
        name = f"source-{Path(pdf_name).stem}-p{page:03d}-{digest}.png"
    else:
        if (
            Path(asset_name).name != asset_name
            or Path(asset_name).suffix.lower() != ".png"
        ):
            raise ValueError(
                f"publication asset name must be a PNG filename, got {asset_name!r}"
            )
        name = asset_name
    destination = _asset_path(assets_root, asset_prefix, name)
    if destination.exists() and asset_name is None:
        return f"{asset_prefix}/{name}"

    page_cache = SOURCE_PAGE_CACHE / (
        f"{Path(pdf_name).stem}-{pdf_digest[:12]}-p{page:03d}-r{dpi}.png"
    )
    page_cache.parent.mkdir(parents=True, exist_ok=True)
    if not page_cache.exists():
        _render_pdf_page(pdf, page, dpi, page_cache.with_suffix(""))

    crop_kwargs = {
        "angle": angle,
        "optimize": True,
        "metadata": _source_png_metadata(
            pdf_name,
            page,
            trim,
            parsed_masks,
            pdf_digest,
            dpi,
            angle,
        ),
    }
    if parsed_masks:
        crop_kwargs["masks"] = parsed_masks
    _crop_source_image(pdf, page, trim, page_cache, destination, **crop_kwargs)
    return f"{asset_prefix}/{name}"


def tikz_source_metadata(stem: str) -> tuple[str, int, str] | None:
    """Return source-PDF metadata embedded in a retained TikZ figure."""
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.is_file():
        raise FileNotFoundError(tikz)
    text = tikz.read_text()
    markers = re.findall(r"^% wave-source:", text, re.MULTILINE)
    matches = list(TIKZ_SOURCE_RE.finditer(text))
    if not matches:
        if markers:
            raise ValueError(f"malformed wave-source comment in {tikz}")
        return None
    if len(markers) != 1 or len(matches) != 1:
        raise ValueError(f"expected one wave-source comment in {tikz}")
    match = matches[0]
    pdf_name = match.group("pdf").strip()
    if Path(pdf_name).name != pdf_name or Path(pdf_name).suffix.lower() != ".pdf":
        raise ValueError(f"invalid wave-source PDF in {tikz}: {pdf_name!r}")
    trim = match.group("trim").strip()
    parse_trim(trim)
    return pdf_name, int(match.group("page")), trim


def tikz_source_masks(stem: str) -> tuple[tuple[float, float, float, float], ...]:
    """Return absolute source-page masks recorded beside a TikZ crop."""
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.is_file():
        raise FileNotFoundError(tikz)
    text = tikz.read_text()
    source = TIKZ_SOURCE_RE.search(text)
    if source is None:
        return ()
    pdf_name = source.group("pdf").strip()
    page = int(source.group("page"))
    return tuple(
        parse_mask(match.group("rect"))
        for match in TIKZ_MASK_RE.finditer(text)
        if match.group("pdf").strip() == pdf_name and int(match.group("page")) == page
    )


def expected_source_png_metadata(stem: str) -> dict[str, str] | None:
    """Return the metadata a maintained source PNG must contain."""
    metadata = tikz_source_metadata(stem)
    if metadata is None:
        return None
    pdf_name, page, trim = metadata
    pdf = SOURCE_DIR / pdf_name
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    return _source_png_metadata(
        pdf_name,
        page,
        trim,
        tikz_source_masks(stem),
        file_sha256(str(pdf.resolve())),
        SOURCE_RENDER_DPI,
        0.0,
    )


def render_source_crop(
    pdf_name: str,
    page: int,
    trim: str,
    destination: Path,
    dpi: int,
    *,
    angle: float = 0.0,
    masks: tuple[tuple[float, float, float, float], ...] = (),
) -> None:
    """Render one source crop for figure-audit comparisons."""
    pdf = SOURCE_DIR / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    with tempfile.TemporaryDirectory(prefix="wave-source-") as temporary:
        prefix = Path(temporary) / "page"
        image_path = _render_pdf_page(pdf, page, dpi, prefix, quiet=False)
        crop_kwargs = {"angle": angle}
        if masks:
            crop_kwargs["masks"] = masks
        _crop_source_image(pdf, page, trim, image_path, destination, **crop_kwargs)


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


def svg_generation_digest(path: Path) -> str | None:
    """Return the generated-input digest recorded in an SVG, if unambiguous."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    matches = SVG_DIGEST_RE.findall(text)
    return matches[0] if len(matches) == 1 else None


def _write_svg_digest(path: Path, digest: str) -> None:
    text = path.read_text()
    text = SVG_DIGEST_RE.sub("", text)
    marker = f"<!-- wave-generated-sha256: {digest} -->\n"
    declaration = re.match(r"\s*<\?xml[^>]*\?>\s*", text)
    if declaration:
        position = declaration.end()
        text = text[:position] + marker + text[position:]
    else:
        text = marker + text
    path.write_text(text)


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
    force: bool = False,
) -> None:
    destination = _asset_path(assets_root, asset_prefix, f"{stem}.svg")
    digest = _tikz_digest(stem)
    if not force and svg_generation_digest(destination) == digest:
        return
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.exists():
        raise FileNotFoundError(tikz)

    cached_svg = TIKZ_CACHE / f"{stem}-{_tikz_digest(stem)}.svg"
    if not cached_svg.exists():
        workdir = work_root / "tikz" / stem
        pdf = _compile_tikz_pdf(stem, workdir)
        svg = workdir / "figure.svg"
        run(["pdftocairo", "-svg", str(pdf), str(svg)])
        cached_svg.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg, cached_svg)
    if svg_generation_digest(cached_svg) != digest:
        _write_svg_digest(cached_svg, digest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cached_svg, destination)


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


def render_tikz_source_png(
    stem: str,
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> str | None:
    """Render the original source crop for one retained TikZ figure."""
    metadata = tikz_source_metadata(stem)
    if metadata is None:
        return None
    pdf_name, page, trim = metadata
    return source_crop(
        pdf_name,
        page,
        trim,
        assets_root,
        asset_prefix=asset_prefix,
        asset_name=f"{stem}.png",
        masks=tikz_source_masks(stem),
    )


def _png_text_metadata(path: Path) -> dict[str, str]:
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError(f"{path} is not a PNG")
            return {key: str(value) for key, value in image.info.items()}
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read PNG metadata from {path}: {exc}") from exc


def maintained_figure_asset_errors(
    stem: str,
    *,
    verify_content: bool = False,
) -> list[str]:
    """Return freshness errors for one maintained TikZ figure asset set."""
    tikz, svg, png = figure_asset_paths(stem)
    errors: list[str] = []
    if not tikz.is_file():
        return [f"{tikz} is missing"]

    try:
        source_metadata = tikz_source_metadata(stem)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        source_metadata = None

    if not svg.is_file() or svg.stat().st_size == 0:
        errors.append(f"{svg} is missing or empty")
    else:
        try:
            svg_text = svg.read_text(errors="replace")
        except OSError as exc:
            errors.append(f"cannot read {svg}: {exc}")
        else:
            if "<svg" not in svg_text:
                errors.append(f"{svg} is not an SVG document")
            digest = svg_generation_digest(svg)
            expected_digest = _tikz_digest(stem)
            if digest != expected_digest:
                errors.append(
                    f"{svg} has digest {digest or '<missing>'}; "
                    f"expected {expected_digest}"
                )

    if source_metadata is None:
        return errors

    if not png.is_file() or png.stat().st_size == 0:
        errors.append(f"{png} is missing or empty")
        return errors

    try:
        actual_metadata = _png_text_metadata(png)
        expected_metadata = expected_source_png_metadata(stem)
        assert expected_metadata is not None
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        return errors

    for key, expected in expected_metadata.items():
        actual = actual_metadata.get(key)
        if actual != expected:
            errors.append(f"{png} metadata {key} is {actual!r}; expected {expected!r}")

    if verify_content and not errors:
        with tempfile.TemporaryDirectory(prefix="wave-figure-check-") as temporary:
            temporary_root = Path(temporary)
            temporary_svg = temporary_root / FIGURE_ASSET_PREFIX / f"{stem}.svg"
            render_tikz_svg(
                stem,
                temporary_root,
                temporary_root,
                force=True,
            )
            if temporary_svg.read_bytes() != svg.read_bytes():
                errors.append(f"{svg} content differs from a fresh rendering")

            render_tikz_source_png(stem, temporary_root)
            temporary_png = temporary_root / FIGURE_ASSET_PREFIX / f"{stem}.png"
            if temporary_png.read_bytes() != png.read_bytes():
                errors.append(f"{png} content differs from a fresh source crop")

    return errors


def validate_maintained_figure_assets(
    stems: Iterable[str] | None = None,
    *,
    verify_content: bool = False,
) -> None:
    """Validate all maintained TikZ siblings without modifying source files."""
    selected = tuple(stems) if stems is not None else maintained_tikz_stems()
    errors = [
        error
        for stem in selected
        for error in maintained_figure_asset_errors(
            stem,
            verify_content=verify_content,
        )
    ]
    if errors:
        raise ValueError(
            "maintained figure asset validation failed:\n- " + "\n- ".join(errors)
        )


@dataclass(frozen=True)
class FigureLedgerEntry:
    chapter: int
    number: int
    title: str
    printed_page: int
    asset: str
    representation: str
    block: str
    image_paths: tuple[str, ...]

    @property
    def order_key(self) -> tuple[int, int, str]:
        return self.printed_page, self.number, self.asset


def _semantic_digest(parts: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def figure_entry_id(entry: FigureLedgerEntry) -> str:
    """Return the stable manifest identity for one figure placement."""
    return Path(entry.asset).stem


def _figure_source_metadata(path: Path) -> tuple[str, ...]:
    if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        return ()
    try:
        metadata = _png_text_metadata(path)
    except OSError, ValueError:
        return ()
    return tuple(
        f"{key}={metadata[key]}"
        for key in sorted(metadata)
        if key.startswith("wave-source-")
    )


def figure_entry_digest(entry: FigureLedgerEntry, figure_dir: Path) -> str:
    """Hash source and placement inputs, excluding mutable review text."""
    asset_path = figure_dir / entry.asset
    parts = [
        f"ledger-version={FIGURE_LEDGER_VERSION}",
        f"chapter={entry.chapter}",
        f"figure-number={entry.number}",
        f"title={entry.title}",
        f"printed-page={entry.printed_page}",
        f"asset={entry.asset}",
        f"representation={entry.representation}",
        "image-paths=" + "|".join(entry.image_paths),
    ]
    parts.extend(
        line.strip()
        for line in entry.block.splitlines()
        if line.startswith("- **Original source:**")
    )
    chapter_source = figure_dir.parent / f"chapter{entry.chapter}.tex"
    if chapter_source.is_file():
        stem = Path(entry.asset).stem
        for line in chapter_source.read_text().splitlines():
            if ("\\wavevectorart" in line and f"{{{stem}}}" in line) or (
                "\\input{figures/" in line and f"{stem}.tikz" in line
            ):
                parts.append(f"chapter-placement={line.strip()}")
    if asset_path.is_file():
        parts.append(
            f"asset-sha256={hashlib.sha256(asset_path.read_bytes()).hexdigest()}"
        )
        parts.extend(_figure_source_metadata(asset_path))
    else:
        parts.append("asset-sha256=<missing>")
    return _semantic_digest(parts)


def figure_ledger_manifest_paths(root: Path | None = None) -> tuple[Path, ...]:
    root = root or SRC
    return tuple(
        root / "figures" / f"CHAPTER{chapter}.sha256"
        for chapter in FIGURE_LEDGER_CHAPTERS
    )


def _manifest_text(
    entries: Iterable[tuple[str, str]],
    *,
    kind: str,
    version: int,
) -> str:
    return (
        "\n".join(
            (
                f"# Generated by scripts/publication.py; {kind}-ledger-version={version}",
                *(f"{digest}  {entry_id}" for digest, entry_id in entries),
            )
        )
        + "\n"
    )


def _read_manifest(path: Path) -> tuple[dict[str, str], list[str]]:
    if not path.is_file():
        return {}, [f"missing audit manifest: {path}"]
    entries: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        match = MANIFEST_ENTRY_RE.fullmatch(line)
        if match is None:
            errors.append(f"{path}:{line_number}: invalid manifest entry")
            continue
        entry_id = match.group("entry")
        if entry_id in entries:
            errors.append(f"{path}:{line_number}: duplicate manifest entry {entry_id}")
        entries[entry_id] = match.group("digest")
    return entries, errors


def _manifest_change_lines(
    current: dict[str, str],
    expected: dict[str, str],
) -> tuple[list[str], list[str], list[str]]:
    return (
        sorted(set(expected) - set(current)),
        sorted(set(current) - set(expected)),
        sorted(
            entry_id
            for entry_id in set(current) & set(expected)
            if current[entry_id] != expected[entry_id]
        ),
    )


def _manifest_diagnostic(
    *,
    kind: str,
    chapter: int,
    added: list[str],
    removed: list[str],
    changed: list[str],
    command: str,
) -> str:
    def describe(label: str, entries: list[str]) -> str:
        if len(entries) <= 12:
            return label + ", ".join(entries)
        return f"{label}{len(entries)} entries"

    details = []
    if changed:
        details.append(describe("changed: ", changed))
    if added:
        details.append(describe("added: ", added))
    if removed:
        details.append(describe("removed: ", removed))
    detail = "; ".join(details) or "manifest format or structure changed"
    noun = "Figure" if kind == "figure" else "Equation"
    return (
        f"{noun} audit changed in Chapter {chapter} ({detail}).\nRegenerate: {command}"
    )


def figure_ledger_chapter_paths(root: Path | None = None) -> tuple[Path, ...]:
    root = root or SRC
    return tuple(
        root / "figures" / f"CHAPTER{chapter}.md" for chapter in FIGURE_LEDGER_CHAPTERS
    )


def _stray_chapter_heading_errors(path: Path, expected_chapter: int) -> list[str]:
    headings = EQUATION_CHAPTER_HEADING_RE.findall(path.read_text())
    return [
        f"{path} contains stray heading for Chapter {chapter}; "
        f"expected only Chapter {expected_chapter}"
        for chapter in headings
    ]


def normalize_figure_chapter_text(text: str) -> str:
    """Remove accidental next-chapter headings from a figure chapter ledger."""
    return EQUATION_CHAPTER_HEADING_RE.sub("", text).rstrip("\n") + "\n"


def figure_ledger_manifest_text(chapter: int, root: Path | None = None) -> str:
    root = root or SRC
    chapter_path = root / "figures" / f"CHAPTER{chapter}.md"
    entries = _figure_entries_from_text(chapter_path.read_text(), chapter=chapter)
    return _manifest_text(
        (
            (figure_entry_digest(entry, chapter_path.parent), figure_entry_id(entry))
            for entry in entries
        ),
        kind="figure",
        version=FIGURE_LEDGER_VERSION,
    )


def _figure_manifest_errors(chapter: int, root: Path) -> list[str]:
    chapter_path = root / "figures" / f"CHAPTER{chapter}.md"
    manifest_path = root / "figures" / f"CHAPTER{chapter}.sha256"
    if not chapter_path.is_file():
        return [f"missing figure chapter ledger: {chapter_path}"]
    try:
        entries = _figure_entries_from_text(chapter_path.read_text(), chapter=chapter)
        expected = {
            figure_entry_id(entry): figure_entry_digest(entry, chapter_path.parent)
            for entry in entries
        }
        expected_text = _manifest_text(
            ((digest, entry_id) for entry_id, digest in expected.items()),
            kind="figure",
            version=FIGURE_LEDGER_VERSION,
        )
    except (OSError, ValueError) as exc:
        return [str(exc)]
    current, errors = _read_manifest(manifest_path)
    added, removed, changed = _manifest_change_lines(current, expected)
    if (
        added
        or removed
        or changed
        or (manifest_path.is_file() and manifest_path.read_text() != expected_text)
    ):
        errors.append(
            _manifest_diagnostic(
                kind="figure",
                chapter=chapter,
                added=added,
                removed=removed,
                changed=changed,
                command=(
                    "uv run --frozen python scripts/publication.py figures "
                    f"--chapter {chapter}"
                ),
            )
        )
    return errors


def _figure_entries_from_text(
    text: str,
    *,
    chapter: int | None = None,
) -> tuple[FigureLedgerEntry, ...]:
    matches = list(FIGURE_ENTRY_RE.finditer(text))
    entries: list[FigureLedgerEntry] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end].rstrip("\n")

        page_match = FIGURE_PAGE_RE.search(block)
        asset_match = FIGURE_ASSET_RE.search(block)
        representation_match = FIGURE_REPRESENTATION_RE.search(block)
        title_page_match = re.search(r"printed page (\d+)", match.group("title"))
        missing = [
            label
            for label, found in (
                ("Printed page", page_match or title_page_match),
                ("Asset", asset_match),
                ("Representation", representation_match),
            )
            if found is None
        ]
        if missing:
            raise ValueError(
                f"Figure {match.group('chapter')}.{match.group('number')} is missing "
                + ", ".join(missing)
            )
        entry = FigureLedgerEntry(
            chapter=int(match.group("chapter")),
            number=int(match.group("number")),
            title=match.group("title"),
            printed_page=int(
                page_match.group("page") if page_match else title_page_match.group(1)
            ),
            asset=asset_match.group("asset"),
            representation=representation_match.group("representation"),
            block=block,
            image_paths=tuple(re.findall(r'<img\s+src="([^"]+)"', block)),
        )
        if chapter is not None and entry.chapter != chapter:
            raise ValueError(
                f"{chapter} ledger contains Figure {entry.chapter}.{entry.number}"
            )
        entries.append(entry)
    return tuple(entries)


def _figure_ledger_counts(
    entries_by_chapter: dict[int, tuple[FigureLedgerEntry, ...]],
) -> tuple[int, dict[str, int]]:
    all_entries = [
        entry for entries in entries_by_chapter.values() for entry in entries
    ]
    representations = {
        representation: sum(
            entry.representation == representation for entry in all_entries
        )
        for representation in sorted(FIGURE_REPRESENTATIONS)
    }
    return len(all_entries), representations


def figure_ledger_text(
    chapter_dir: Path | None = None,
) -> tuple[str, int]:
    """Return the concise generated figure-audit landing page."""
    chapter_dir = chapter_dir or SRC / "figures"
    entries_by_chapter = {
        chapter: (
            _figure_entries_from_text(
                (chapter_dir / f"CHAPTER{chapter}.md").read_text(), chapter=chapter
            )
            if (chapter_dir / f"CHAPTER{chapter}.md").is_file()
            else ()
        )
        for chapter in FIGURE_LEDGER_CHAPTERS
    }
    total, representations = _figure_ledger_counts(entries_by_chapter)
    lines = [
        "# Figure audit",
        "",
        "<!-- Generated from src/figures/CHAPTER1.md through src/figures/CHAPTER6.md. -->",
        "",
        (
            "This audit covers scientific and technical figures in Chapters 1–6. "
            "Cover art, photographs, and other editorial images are outside it."
        ),
        "",
        (
            "The chapter ledgers show each placement in printed-page and visual order. "
            "The committed 1989 PDFs are the reference for source fidelity and scientific "
            "review."
        ),
        "",
        "## Summary",
        "",
        f"The six chapter ledgers contain **{total} scientific figure placements**.",
        "",
        "| Chapter | Placements | vector | source-pdf |",
        "| --- | ---: | ---: | ---: |",
    ]
    for chapter in FIGURE_LEDGER_CHAPTERS:
        entries = entries_by_chapter[chapter]
        lines.append(
            f"| Chapter {chapter} | {len(entries)} | "
            f"{sum(entry.representation == 'vector' for entry in entries)} | "
            f"{sum(entry.representation == 'source-pdf' for entry in entries)} |"
        )
    lines.extend(
        [
            (
                f"| **Total** | **{total}** | **{representations['vector']}** | "
                f"**{representations['source-pdf']}** |"
            ),
            "",
            "## Chapters",
            "",
        ]
    )
    for chapter in FIGURE_LEDGER_CHAPTERS:
        lines.append(
            f"- [Chapter {chapter}](figures/CHAPTER{chapter}.md) — "
            f"{len(entries_by_chapter[chapter])} placements"
        )
    lines.extend(
        [
            "",
            "## Review states",
            "",
            "Representation describes the maintained scientific asset:",
            "",
            "- `vector` — a maintained TikZ/vector reconstruction.",
            "- `source-pdf` — a direct crop kept from the source PDF when redrawing would add interpretation risk.",
            "",
            "Equation check describes the scientific review of equation-defined content:",
            "",
            "- `ai-checked` — an AI model checked the material equation-constrained content. This is not human validation.",
            "- `partial` — some material equation-constrained content was checked; another part remains schematic or unchecked.",
            "- `pending` — a material equation check remains to be done.",
            "- `n/a` — no meaningful equation-defined quantity or relation controls the figure; visual and source checks still apply.",
            "",
            "Source discrepancies and approval state belong in `ERRATA.md`; a scientific check does not approve a substantive source change.",
        ]
    )
    return "\n".join(lines).rstrip("\n") + "\n", total


def figure_ledger_errors(
    root: Path | None = None,
    chapters: Iterable[int] | None = None,
) -> list[str]:
    """Return structural, semantic-manifest, and landing-page errors."""
    root = root or SRC
    selected = tuple(chapters) if chapters is not None else FIGURE_LEDGER_CHAPTERS
    invalid = sorted(set(selected) - set(FIGURE_LEDGER_CHAPTERS))
    if invalid:
        return [f"invalid figure audit chapter(s): {', '.join(map(str, invalid))}"]
    chapter_dir = root / "figures"
    expected_paths = figure_ledger_chapter_paths(root)
    errors: list[str] = []
    for chapter in selected:
        path = expected_paths[chapter - 1]
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing figure chapter ledger: {path}")
    if chapters is None:
        expected_set = set(expected_paths)
        for path in sorted(chapter_dir.glob("*.md")):
            if path not in expected_set:
                errors.append(f"unexpected figure chapter ledger: {path}")

    entries_by_chapter: dict[int, tuple[FigureLedgerEntry, ...]] = {}
    for chapter, path in zip(FIGURE_LEDGER_CHAPTERS, expected_paths, strict=True):
        if not path.is_file():
            entries_by_chapter[chapter] = ()
            continue
        try:
            entries = _figure_entries_from_text(path.read_text(), chapter=chapter)
        except (OSError, ValueError) as exc:
            if chapter in selected:
                errors.append(str(exc))
            entries_by_chapter[chapter] = ()
            continue
        entries_by_chapter[chapter] = entries
        if chapter in selected:
            errors.extend(_stray_chapter_heading_errors(path, chapter))
            normalized = normalize_figure_chapter_text(path.read_text())
            if path.read_bytes() != normalized.encode("utf-8"):
                errors.append(
                    f"figure chapter ledger is not normalized: {path}\n"
                    "Regenerate: uv run --frozen python scripts/publication.py figures "
                    f"--chapter {chapter}"
                )
            if [entry.order_key for entry in entries] != sorted(
                entry.order_key for entry in entries
            ):
                errors.append(f"{path} entries are not ordered by page, figure, asset")
            for entry in entries:
                if entry.representation not in FIGURE_REPRESENTATIONS:
                    errors.append(
                        f"{path}: Figure {entry.chapter}.{entry.number} uses unsupported "
                        f"representation {entry.representation!r}"
                    )
                if "images/" in entry.block or "source-photo" in entry.block:
                    errors.append(
                        f"{path}: Figure {entry.chapter}.{entry.number} contains an "
                        "editorial image reference"
                    )
                for image_path in entry.image_paths:
                    asset_path = (path.parent / image_path).resolve()
                    if not asset_path.is_file():
                        errors.append(
                            f"{path}: missing figure review asset {image_path}"
                        )
            errors.extend(_figure_manifest_errors(chapter, root))

    landing = root / "FIGURES.md"
    if not landing.is_file() or landing.stat().st_size == 0:
        errors.append(f"missing figure audit landing page: {landing}")
    else:
        landing_text = landing.read_text()
        if FIGURE_ENTRY_RE.search(landing_text):
            errors.append(f"{landing} still contains detailed figure entries")
        if "Front matter and artwork" in landing_text:
            errors.append(f"{landing} contains editorial artwork inventory")
        try:
            expected, _ = figure_ledger_text(chapter_dir)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot regenerate {landing}: {exc}")
        else:
            if landing.read_bytes() != expected.encode("utf-8"):
                command = "uv run --frozen python scripts/publication.py figures"
                if chapters is not None and len(selected) == 1:
                    command += f" --chapter {selected[0]}"
                errors.append(
                    f"figure audit landing page is stale: {landing}\nRegenerate: {command}"
                )
    return errors


def figure_ledger_matches(path: Path | None = None) -> bool:
    landing = path or SRC / "FIGURES.md"
    if not landing.is_file():
        return False
    expected, _ = figure_ledger_text(landing.parent / "figures")
    return landing.read_bytes() == expected.encode("utf-8")


def write_figure_ledger(path: Path | None = None) -> int:
    """Write all figure chapter manifests and the generated landing page."""
    landing = path or SRC / "FIGURES.md"
    return write_figure_chapter_ledgers(landing.parent)


def write_figure_chapter_ledgers(
    root: Path | None = None,
    chapters: Iterable[int] | None = None,
) -> int:
    """Normalize selected figure ledgers and write only their manifests."""
    root = root or SRC
    selected = tuple(chapters) if chapters is not None else FIGURE_LEDGER_CHAPTERS
    figure_dir = root / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for chapter in selected:
        chapter_path = figure_dir / f"CHAPTER{chapter}.md"
        if not chapter_path.is_file():
            raise FileNotFoundError(chapter_path)
        normalized = normalize_figure_chapter_text(chapter_path.read_text())
        if chapter_path.read_bytes() != normalized.encode("utf-8"):
            chapter_path.write_bytes(normalized.encode("utf-8"))
        entries = _figure_entries_from_text(normalized, chapter=chapter)
        expected = _manifest_text(
            (
                (figure_entry_digest(entry, figure_dir), figure_entry_id(entry))
                for entry in entries
            ),
            kind="figure",
            version=FIGURE_LEDGER_VERSION,
        )
        manifest = figure_dir / f"CHAPTER{chapter}.sha256"
        if not manifest.is_file() or manifest.read_bytes() != expected.encode("utf-8"):
            manifest.write_bytes(expected.encode("utf-8"))
        count += len(entries)
    landing = root / "FIGURES.md"
    text, _ = figure_ledger_text(figure_dir)
    if not landing.is_file() or landing.read_bytes() != text.encode("utf-8"):
        landing.write_bytes(text.encode("utf-8"))
    return count


def referenced_tikz() -> list[str]:
    return referenced_tikz_in_texts(
        (SRC / f"chapter{i}.tex").read_text() for i in range(1, 7)
    )


def referenced_tikz_in_texts(texts: Iterable[str]) -> list[str]:
    stems: set[str] = set()
    for text in texts:
        stems.update(match.group("stem") for match in VECTOR_RE.finditer(text))
        stems.update(match.group("stem") for match in TIKZ_INPUT_RE.finditer(text))
    return sorted(stems)


def prepare_original_assets(
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> None:
    """Copy maintained same-stem source PNGs for HTML-used TikZ figures."""
    stems = [
        stem for stem in referenced_tikz() if tikz_source_metadata(stem) is not None
    ]
    if not stems:
        return
    validate_maintained_figure_assets(stems)
    print(f"Copying {len(stems)} maintained original TikZ source PNGs...")
    for stem in stems:
        source = FIGURES / f"{stem}.png"
        destination = _asset_path(assets_root, asset_prefix, source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def switchable_figure_stems(
    assets_root: Path,
    stems: list[str] | tuple[str, ...] | None = None,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> tuple[str, ...]:
    """Return stems with both SVG and PNG assets in one publication directory."""
    candidates = stems if stems is not None else referenced_tikz()
    figure_dir = assets_root / Path(asset_prefix)
    return tuple(
        sorted(
            stem
            for stem in set(candidates)
            if (figure_dir / f"{stem}.svg").is_file()
            and (figure_dir / f"{stem}.png").is_file()
        )
    )


def page_switchable_figure_stems(
    page: Path,
    assets_root: Path,
    *,
    asset_prefix: str = FIGURE_ASSET_PREFIX,
) -> tuple[str, ...]:
    """Return switchable figure stems referenced by one flowing HTML page."""
    match = re.fullmatch(r"chapter(?P<number>\d+)\.html", page.name)
    if match is None:
        return ()
    chapter = SRC / f"chapter{int(match.group('number'))}.tex"
    if not chapter.is_file():
        raise FileNotFoundError(chapter)
    stems = referenced_tikz_in_texts((chapter.read_text(),))
    return switchable_figure_stems(assets_root, stems, asset_prefix=asset_prefix)


def prepare_vector_assets(assets_root: Path, work_root: Path) -> None:
    stems = referenced_tikz()
    del work_root
    validate_maintained_figure_assets()
    print(f"Copying {len(stems)} maintained TikZ SVGs...")
    for stem in stems:
        source = FIGURES / f"{stem}.svg"
        destination = _asset_path(assets_root, FIGURE_ASSET_PREFIX, source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def copy_raster_assets(
    assets_root: Path, *, asset_prefix: str = FIGURE_ASSET_PREFIX
) -> None:
    for raster_dir in IMAGE_DIRS:
        for raster in raster_dir.rglob("*"):
            if not raster.is_file() or raster.suffix.lower() not in {
                ".png",
                ".jpg",
                ".jpeg",
            }:
                continue
            destination = _asset_path(
                assets_root, asset_prefix, str(raster.relative_to(raster_dir))
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(raster, destination)


def copy_cc_assets(assets_root: Path) -> None:
    destination = assets_root / "assets" / "cc"
    destination.mkdir(parents=True, exist_ok=True)
    for name in CC_ICONS:
        source = SRC / "assets" / "cc" / f"{name}.svg"
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, destination / source.name)


def prepare_assets(
    assets_root: Path, work_root: Path, *, include_originals: bool = False
) -> None:
    """Prepare shared assets used by the flowing editions under one asset root."""
    prepare_vector_assets(assets_root, work_root)
    if include_originals:
        prepare_original_assets(assets_root)
    copy_raster_assets(assets_root)
    copy_cc_assets(assets_root)


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
        return (
            rf"\includegraphics{{{asset_prefix}/{match.group('stem')}.svg}}"
            + "\n\\wavefiguremark"
        )

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
            mask=match.group("mask"),
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
            "\\[\n" + body + "\n\\]\n"
            "\\begin{flushright}\n\\textup{(" + tag + ")}\n\\end{flushright}"
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
            "\\[\n" + body + "\n\\]\n"
            "\\begin{flushright}\n\\textup{" + label + "}\n\\end{flushright}"
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
            f"chapter {chapter_number}: expected figure count, got {figure_number}"
        )
    return text


def prepare_flowing_sources(output_dir: Path, assets_root: Path) -> list[Path]:
    """Write transformed front matter and chapters for a flowing edition."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_root.mkdir(parents=True, exist_ok=True)
    frontmatter = (SRC / "frontmatter-modern.tex").read_text()
    frontmatter = frontmatter.replace(r"\tableofcontents", "")
    frontmatter_path = output_dir / "frontmatter.tex"
    frontmatter_path.write_text(transform_tex(frontmatter, None, assets_root))

    paths = [frontmatter_path]
    for chapter_number in range(1, 7):
        path = output_dir / f"chapter{chapter_number}.tex"
        path.write_text(
            transform_tex(
                (SRC / f"chapter{chapter_number}.tex").read_text(),
                chapter_number,
                assets_root,
            )
        )
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Equation ledger generation


@dataclass(frozen=True)
class EquationDisplay:
    chapter: int
    printed_page: int
    physical_page: int
    display_ordinal: int
    display_type: str
    line: int
    source: str

    @property
    def stem(self) -> str:
        return (
            f"ch{self.chapter:02d}-p{self.printed_page:03d}-e{self.display_ordinal:02d}"
        )


def extract_equation_displays(
    chapter_number: int,
    path: Path | None = None,
) -> tuple[EquationDisplay, ...]:
    """Extract complete display blocks from one maintained chapter source."""
    source_path = path or SRC / f"chapter{chapter_number}.tex"
    lines = source_path.read_text().splitlines()
    printed_page: int | None = None
    physical_page: int | None = None
    display_ordinal = 0
    displays: list[EquationDisplay] = []
    index = 0

    while index < len(lines):
        page_match = EQUATION_PAGE_RE.fullmatch(lines[index])
        if page_match:
            printed_page = int(page_match.group("printed"))
            physical_page = int(page_match.group("physical"))
            display_ordinal = 0
            index += 1
            continue

        line = lines[index]
        is_bracket = line.strip() == r"\["
        begin_match = EQUATION_BEGIN_RE.fullmatch(line)
        environment = (
            begin_match.group("environment")
            if begin_match and begin_match.group("environment") in EQUATION_DISPLAY_ENVS
            else None
        )
        if not is_bracket and environment is None:
            index += 1
            continue
        if printed_page is None or physical_page is None:
            raise ValueError(
                f"{source_path}:{index + 1}: display appears before a source-page comment"
            )

        start = index
        end_token = r"\]" if is_bracket else rf"\end{{{environment}}}"
        index += 1
        while index < len(lines) and lines[index].strip() != end_token:
            index += 1
        if index >= len(lines):
            raise ValueError(f"unclosed display in {source_path}:{start + 1}")

        source = "\n".join(lines[start : index + 1])
        display_ordinal += 1
        displays.append(
            EquationDisplay(
                chapter=chapter_number,
                printed_page=printed_page,
                physical_page=physical_page,
                display_ordinal=display_ordinal,
                display_type="bracket" if is_bracket else environment,
                line=start + 1,
                source=source,
            )
        )
        index += 1

    if displays:
        pages = [display.printed_page for display in displays]
        if pages != sorted(pages):
            raise ValueError(f"{source_path}: printed pages are not in source order")
    return tuple(displays)


def collect_equation_displays(
    source_dir: Path | None = None,
) -> tuple[EquationDisplay, ...]:
    """Return all chapter displays in stable chapter/page/display order."""
    source_dir = source_dir or SRC
    displays: list[EquationDisplay] = []
    for chapter_number in range(1, 7):
        displays.extend(
            extract_equation_displays(
                chapter_number,
                source_dir / f"chapter{chapter_number}.tex",
            )
        )

    displays.sort(
        key=lambda display: (
            display.chapter,
            display.printed_page,
            display.display_ordinal,
        )
    )
    identities = [
        (display.chapter, display.printed_page, display.display_ordinal)
        for display in displays
    ]
    if len(identities) != len(set(identities)):
        raise ValueError("equation display identities are not unique")
    return tuple(displays)


def equation_entry_digest(display: EquationDisplay) -> str:
    """Hash the semantic source represented by one displayed equation."""
    return _semantic_digest(
        (
            f"ledger-version={EQUATION_LEDGER_VERSION}",
            f"stem={display.stem}",
            f"chapter={display.chapter}",
            f"printed-page={display.printed_page}",
            f"physical-page={display.physical_page}",
            f"display-ordinal={display.display_ordinal}",
            f"display-type={display.display_type}",
            display.source,
        )
    )


def equation_ledger_manifest_paths(root: Path | None = None) -> tuple[Path, ...]:
    root = root or SRC
    return tuple(
        root / "equations" / f"CHAPTER{chapter}.sha256"
        for chapter in FIGURE_LEDGER_CHAPTERS
    )


def equation_ledger_manifest_text(
    chapter: int,
    source_dir: Path | None = None,
) -> str:
    source_dir = source_dir or SRC
    displays = extract_equation_displays(chapter, source_dir / f"chapter{chapter}.tex")
    return _manifest_text(
        ((equation_entry_digest(display), display.stem) for display in displays),
        kind="equation",
        version=EQUATION_LEDGER_VERSION,
    )


def _equation_manifest_errors(
    chapter: int,
    root: Path,
    source_dir: Path | None = None,
) -> list[str]:
    source_dir = source_dir or SRC
    try:
        displays = extract_equation_displays(
            chapter, source_dir / f"chapter{chapter}.tex"
        )
        expected = {
            display.stem: equation_entry_digest(display) for display in displays
        }
        expected_text = _manifest_text(
            ((digest, entry_id) for entry_id, digest in expected.items()),
            kind="equation",
            version=EQUATION_LEDGER_VERSION,
        )
    except (OSError, ValueError) as exc:
        return [str(exc)]
    manifest_path = root / "equations" / f"CHAPTER{chapter}.sha256"
    current, errors = _read_manifest(manifest_path)
    added, removed, changed = _manifest_change_lines(current, expected)
    if (
        added
        or removed
        or changed
        or (manifest_path.is_file() and manifest_path.read_text() != expected_text)
    ):
        errors.append(
            _manifest_diagnostic(
                kind="equation",
                chapter=chapter,
                added=added,
                removed=removed,
                changed=changed,
                command=(
                    "uv run --frozen python scripts/publication.py equations "
                    f"--chapter {chapter}"
                ),
            )
        )
    return errors


def _equation_body(display: EquationDisplay) -> str:
    lines = display.source.splitlines()
    if len(lines) < 2:
        raise ValueError(f"display source is incomplete for {display.stem}")
    return "\n".join(lines[1:-1])


def equation_markdown_math(display: EquationDisplay) -> str:
    """Convert repository display wrappers to semantically matched GitHub math."""
    body = _equation_body(display)
    if display.display_type == "bracket":
        return f"$$\n{body}\n$$"
    if display.display_type in {"waveequation", "equation", "equation*"}:
        return f"$$\n{body}\n$$"
    if display.display_type in {"wavealign", "align", "align*"}:
        return f"$$\n\\begin{{aligned}}\n{body}\n\\end{{aligned}}\n$$"
    if display.display_type in {"gather", "gather*"}:
        return f"$$\n\\begin{{gathered}}\n{body}\n\\end{{gathered}}\n$$"
    if display.display_type in {"multline", "multline*"}:
        # MathJax's AMS package supports multline and preserves its deliberately
        # asymmetric first/intermediate/last-line layout.  Do not turn it into
        # aligned: that would add alignment points and change the real Chapter 5
        # display's rendering semantics.
        return f"$$\n\\begin{{{display.display_type}}}\n{body}\n\\end{{{display.display_type}}}\n$$"
    raise ValueError(f"unsupported equation display type: {display.display_type}")


def equation_asset_paths(stem: str) -> tuple[Path, Path, Path]:
    """Return the three maintained PNG paths derived from one equation stem."""
    if EQUATION_STEM_RE.fullmatch(stem) is None:
        raise ValueError(f"invalid equation stem: {stem!r}")
    directory = SRC / "equations"
    return (
        directory / f"{stem}-source.png",
        directory / f"{stem}-mathjax.png",
        directory / f"{stem}-mathml.png",
    )


def _equation_source_pdf(display: EquationDisplay) -> tuple[str, Path]:
    name = EQUATION_SOURCE_PDFS[display.chapter]
    return name, SOURCE_DIR / name


def _equation_source_digest(display: EquationDisplay) -> str:
    return hashlib.sha256(display.source.encode("utf-8")).hexdigest()


def _equation_rendered_tex_digest(display: EquationDisplay) -> str:
    return hashlib.sha256(equation_markdown_math(display).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EquationSourceCrop:
    trim: str
    pixels: tuple[int, int, int, int]
    dpi: int = EQUATION_SOURCE_DPI


def _image_pixel_digest(image: Image.Image) -> str:
    rgba = image.convert("RGBA")
    identity = f"{rgba.width}x{rgba.height}\0".encode("ascii")
    return hashlib.sha256(identity + rgba.tobytes()).hexdigest()


def _png_pixel_digest(path: Path) -> str:
    with Image.open(path) as image:
        return _image_pixel_digest(image)


def _equation_source_page_path(display: EquationDisplay, dpi: int) -> Path:
    pdf_name, pdf = _equation_source_pdf(display)
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    pdf_digest = file_sha256(str(pdf.resolve()))
    page_cache = SOURCE_PAGE_CACHE / (
        f"equation-{Path(pdf_name).stem}-{pdf_digest[:12]}-"
        f"p{display.physical_page:03d}-r{dpi}.png"
    )
    page_cache.parent.mkdir(parents=True, exist_ok=True)
    if not page_cache.is_file():
        _render_pdf_page(pdf, display.physical_page, dpi, page_cache.with_suffix(""))
    return page_cache


def _format_equation_source_trim(
    pixels: tuple[int, int, int, int],
    page_size: tuple[int, int],
    dpi: int,
) -> str:
    x, y, width, height = pixels
    page_width, page_height = page_size
    left = x / dpi * 72
    top = y / dpi * 72
    right = (page_width - x - width) / dpi * 72
    bottom = (page_height - y - height) / dpi * 72
    return " ".join(f"{value:g}bp" for value in (left, bottom, right, top))


def _parse_equation_source_crop(value: str) -> EquationSourceCrop:
    match = EQUATION_SOURCE_CROP_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            f"expected equation source crop as x,y,width,height@300dpi, got {value!r}"
        )
    pixels = tuple(int(match.group(name)) for name in ("x", "y", "width", "height"))
    dpi = int(match.group("dpi"))
    if pixels[2] <= 0 or pixels[3] <= 0 or dpi <= 0:
        raise ValueError(f"invalid equation source crop: {value!r}")
    return EquationSourceCrop(trim="", pixels=pixels, dpi=dpi)


def _locate_equation_source_crop(
    display: EquationDisplay,
    source_path: Path,
) -> EquationSourceCrop:
    """Recover crop geometry without using the existing pixels as output."""
    page_path = _equation_source_page_path(display, EQUATION_SOURCE_DPI)
    with Image.open(page_path) as page_image, Image.open(source_path) as template_image:
        page = page_image.convert("RGB")
        template = template_image.convert("RGB")
    if template.width > page.width or template.height > page.height:
        raise ValueError(f"{source_path}: crop is larger than its source page")

    page_bytes = page.tobytes()
    template_bytes = template.tobytes()
    page_stride = page.width * 3
    template_stride = template.width * 3
    row_scores = []
    for row in range(template.height):
        start = row * template_stride
        row_scores.append(
            (
                sum(
                    template_bytes[start + offset] < 200
                    for offset in range(0, template_stride, 3)
                ),
                row,
            )
        )
    matches: set[tuple[int, int]] = set()
    for _score, template_row in sorted(row_scores, reverse=True)[:12]:
        start = template_row * template_stride
        needle = template_bytes[start : start + template_stride]
        search_from = 0
        while True:
            offset = page_bytes.find(needle, search_from)
            if offset < 0:
                break
            search_from = offset + 3
            if offset % 3:
                continue
            page_row = offset // page_stride
            row_offset = offset % page_stride
            if row_offset % 3:
                continue
            x = row_offset // 3
            page_row -= template_row
            if page_row < 0 or x + template.width > page.width:
                continue
            if page_row + template.height > page.height:
                continue
            candidate = page.crop(
                (x, page_row, x + template.width, page_row + template.height)
            )
            if ImageChops.difference(candidate, template).getbbox() is None:
                matches.add((x, page_row))
    if len(matches) != 1:
        raise ValueError(
            f"{source_path}: could not locate its source crop uniquely on "
            f"physical page {display.physical_page} ({len(matches)} exact matches); "
            "record wave-source-crop-pixels explicitly"
        )
    x, y = matches.pop()
    pixels = (x, y, template.width, template.height)
    return EquationSourceCrop(
        trim=_format_equation_source_trim(
            pixels,
            (page.width, page.height),
            EQUATION_SOURCE_DPI,
        ),
        pixels=pixels,
    )


def _recorded_equation_source_crop(
    display: EquationDisplay,
    source_path: Path,
) -> EquationSourceCrop:
    if not source_path.is_file() or source_path.stat().st_size == 0:
        raise ValueError(
            f"{source_path}: a recorded source crop is needed before equation "
            "assets can be regenerated"
        )
    metadata = _png_text_metadata(source_path)
    expected_pdf, _pdf = _equation_source_pdf(display)
    if metadata.get("wave-source-pdf") != expected_pdf:
        raise ValueError(
            f"{source_path}: source PDF metadata does not match {expected_pdf!r}"
        )
    if metadata.get("wave-source-page") != str(display.physical_page):
        raise ValueError(
            f"{source_path}: source page metadata does not match "
            f"{display.physical_page}"
        )
    crop_pixels = metadata.get("wave-source-crop-pixels")
    crop = _parse_equation_source_crop(crop_pixels) if crop_pixels else None
    if crop is not None:
        if crop.dpi != EQUATION_SOURCE_DPI:
            raise ValueError(
                f"{source_path}: source crop uses {crop.dpi} DPI; "
                f"expected {EQUATION_SOURCE_DPI}"
            )
        trim = metadata.get("wave-source-crop", "")
        if not trim:
            page_path = _equation_source_page_path(display, crop.dpi)
            with Image.open(page_path) as page:
                trim = _format_equation_source_trim(crop.pixels, page.size, crop.dpi)
        return EquationSourceCrop(trim=trim, pixels=crop.pixels, dpi=crop.dpi)
    return _locate_equation_source_crop(display, source_path)


def _equation_asset_input_metadata(
    display: EquationDisplay,
    kind: str,
    source_crop: EquationSourceCrop | None = None,
) -> dict[str, str]:
    if kind not in EQUATION_ASSET_KINDS:
        raise ValueError(f"unsupported equation asset kind: {kind!r}")
    renderer, renderer_version, renderer_config = EQUATION_RENDER_CONFIG[kind]
    metadata = {
        "wave-equation-asset-version": EQUATION_ASSET_VERSION,
        "wave-equation-asset-kind": kind,
        "wave-equation-stem": display.stem,
        "wave-equation-source-sha256": _equation_source_digest(display),
        "wave-equation-rendered-tex-sha256": _equation_rendered_tex_digest(display),
        "wave-equation-renderer": renderer,
        "wave-equation-renderer-version": renderer_version,
        "wave-equation-renderer-config": renderer_config,
    }
    if kind == "source":
        pdf_name, pdf = _equation_source_pdf(display)
        metadata.update(
            {
                "wave-source-pdf": pdf_name,
                "wave-source-pdf-sha256": (
                    file_sha256(str(pdf.resolve())) if pdf.is_file() else "<missing>"
                ),
                "wave-source-page": str(display.physical_page),
            }
        )
        if source_crop is not None:
            metadata.update(
                {
                    "wave-source-crop": source_crop.trim,
                    "wave-source-crop-dpi": str(source_crop.dpi),
                    "wave-source-crop-pixels": (
                        ",".join(str(value) for value in source_crop.pixels)
                        + f"@{source_crop.dpi}dpi"
                    ),
                }
            )
    return metadata


def _equation_asset_metadata(
    display: EquationDisplay,
    kind: str,
    path: Path | None = None,
    source_crop: EquationSourceCrop | None = None,
) -> dict[str, str]:
    del path
    return _equation_asset_input_metadata(display, kind, source_crop)


def expected_equation_asset_metadata(
    display: EquationDisplay,
    kind: str,
    path: Path | None = None,
) -> dict[str, str]:
    """Return stable input metadata expected in one equation review PNG."""
    return _equation_asset_metadata(display, kind, path)


def _recorded_source_crop_errors(
    display: EquationDisplay,
    path: Path,
    metadata: dict[str, str],
    pixel_digest: str,
    *,
    validate_source_page: bool = True,
) -> list[str]:
    errors: list[str] = []
    try:
        crop = _parse_equation_source_crop(metadata.get("wave-source-crop-pixels", ""))
    except ValueError as exc:
        return [f"{path}: {exc}"]
    if metadata.get("wave-source-crop-dpi") != str(crop.dpi):
        errors.append(f"{path}: source crop DPI does not match its pixel record")
    if crop.dpi != EQUATION_SOURCE_DPI:
        errors.append(
            f"{path}: source crop DPI is {crop.dpi}; expected {EQUATION_SOURCE_DPI}"
        )
    if not metadata.get("wave-source-crop"):
        errors.append(f"{path}: source crop trim is missing")
    with Image.open(path) as image:
        if image.size != crop.pixels[2:]:
            errors.append(f"{path}: dimensions do not match its recorded crop")
    if metadata.get("wave-source-crop-sha256") != pixel_digest:
        errors.append(f"{path}: source-crop pixel digest does not match its pixels")
    if validate_source_page:
        try:
            page_path = _equation_source_page_path(display, crop.dpi)
            with Image.open(page_path) as page:
                x, y, width, height = crop.pixels
                if x < 0 or y < 0 or x + width > page.width or y + height > page.height:
                    errors.append(
                        f"{path}: recorded source crop is outside its PDF page"
                    )
                expected_trim = _format_equation_source_trim(
                    crop.pixels, page.size, crop.dpi
                )
                if metadata.get("wave-source-crop") != expected_trim:
                    errors.append(
                        f"{path}: source crop trim does not match its pixel record"
                    )
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{path}: cannot validate source-page crop: {exc}")
    return errors


def _equation_asset_errors_for_display(
    display: EquationDisplay,
    equation_dir: Path,
    *,
    validate_source_page: bool = True,
    source_pdf_errors: set[Path] | None = None,
) -> list[str]:
    """Return the detailed asset errors for one equation."""
    errors: list[str] = []
    source_pdf_errors = source_pdf_errors if source_pdf_errors is not None else set()
    paths = tuple(
        equation_dir / path.name for path in equation_asset_paths(display.stem)
    )
    for kind, path in zip(EQUATION_ASSET_KINDS, paths, strict=True):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty equation asset: {path}")
            continue
        try:
            actual = _png_text_metadata(path)
            expected = _equation_asset_metadata(display, kind)
            pixel_digest = _png_pixel_digest(path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        for key, value in expected.items():
            if actual.get(key) != value:
                errors.append(
                    f"{path} metadata {key} is {actual.get(key)!r}; expected {value!r}"
                )
        if actual.get("wave-equation-pixel-sha256") != pixel_digest:
            errors.append(f"{path} pixel digest does not match its metadata")
        if kind == "source":
            source_pdf = SOURCE_DIR / EQUATION_SOURCE_PDFS[display.chapter]
            if not source_pdf.is_file() and source_pdf not in source_pdf_errors:
                source_pdf_errors.add(source_pdf)
                errors.append(f"missing equation source PDF: {source_pdf}")
            errors.extend(
                _recorded_source_crop_errors(
                    display,
                    path,
                    actual,
                    pixel_digest,
                    validate_source_page=validate_source_page,
                )
            )
    return errors


def equation_asset_errors_for_display(
    display: EquationDisplay,
    equation_dir: Path | None = None,
    *,
    validate_source_page: bool = True,
) -> list[str]:
    """Return detailed validation errors for one equation's three PNGs."""
    return _equation_asset_errors_for_display(
        display,
        equation_dir or SRC / "equations",
        validate_source_page=validate_source_page,
    )


def stale_equation_displays(
    displays: Iterable[EquationDisplay],
    equation_dir: Path | None = None,
) -> tuple[EquationDisplay, ...]:
    """Return equations for which any of the three review PNGs is stale."""
    equation_dir = equation_dir or SRC / "equations"
    return tuple(
        display
        for display in displays
        if equation_asset_errors_for_display(
            display,
            equation_dir,
            validate_source_page=False,
        )
    )


def equation_asset_errors(
    displays: Iterable[EquationDisplay] | None = None,
    equation_dir: Path | None = None,
) -> list[str]:
    """Return missing, stale, or malformed equation review PNG errors."""
    selected_all = displays is None
    displays = tuple(displays if displays is not None else collect_equation_displays())
    equation_dir = equation_dir or SRC / "equations"
    errors: list[str] = []
    expected_names = {
        path.name for display in displays for path in equation_asset_paths(display.stem)
    }
    if selected_all:
        for path in sorted(equation_dir.glob("*.png")):
            if path.name not in expected_names:
                errors.append(f"unexpected equation asset: {path}")
    source_pdf_errors: set[Path] = set()
    for display in displays:
        errors.extend(
            _equation_asset_errors_for_display(
                display,
                equation_dir,
                source_pdf_errors=source_pdf_errors,
            )
        )
    return errors


EQUATION_ASSET_SCHEMA_METADATA_KEYS = frozenset(
    {
        "wave-equation-asset-version",
        "wave-equation-asset-kind",
        "wave-equation-renderer",
        "wave-equation-renderer-version",
        "wave-equation-renderer-config",
    }
)


def summarize_equation_asset_errors(errors: Iterable[str]) -> list[str]:
    """Collapse repeated renderer/schema failures for concise full checks."""
    summarized: list[str] = []
    positions: dict[tuple[str, str, str], int] = {}
    counts: dict[tuple[str, str, str], int] = {}
    metadata_re = re.compile(
        r" metadata (?P<key>[^ ]+) is (?P<actual>.*); expected (?P<expected>.*)$"
    )
    for error in errors:
        match = metadata_re.search(error)
        if (
            match is None
            or match.group("key") not in EQUATION_ASSET_SCHEMA_METADATA_KEYS
        ):
            summarized.append(error)
            continue
        key = (
            match.group("key"),
            match.group("actual"),
            match.group("expected"),
        )
        if key not in positions:
            positions[key] = len(summarized)
            counts[key] = 1
            summarized.append(error)
        else:
            counts[key] += 1
    for key, position in positions.items():
        if counts[key] > 1:
            summarized[position] += f" ({counts[key]} matching assets)"
    return summarized


def _equation_asset_input_stale_ids(
    displays: Iterable[EquationDisplay],
    equation_dir: Path | None = None,
) -> set[str]:
    """Cheaply identify equation assets whose recorded inputs no longer match."""
    equation_dir = equation_dir or SRC / "equations"
    stale: set[str] = set()
    for display in displays:
        for kind, path in zip(
            EQUATION_ASSET_KINDS,
            (equation_dir / item.name for item in equation_asset_paths(display.stem)),
            strict=True,
        ):
            if not path.is_file() or path.stat().st_size == 0:
                stale.add(display.stem)
                continue
            try:
                actual = _png_text_metadata(path)
                expected = _equation_asset_metadata(display, kind)
            except OSError, ValueError:
                stale.add(display.stem)
                continue
            if any(actual.get(key) != value for key, value in expected.items()):
                stale.add(display.stem)
    return stale


def _save_generated_equation_png(
    path: Path,
    image: Image.Image,
    metadata: dict[str, str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = image.convert("RGB")
    digest = _image_pixel_digest(image)
    full_metadata = dict(metadata)
    full_metadata["wave-equation-pixel-sha256"] = digest
    if full_metadata.get("wave-equation-asset-kind") == "source":
        full_metadata["wave-source-crop-sha256"] = digest
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        pnginfo = PngInfo()
        for key, value in full_metadata.items():
            pnginfo.add_text(key, value)
        image.save(temporary, format="PNG", optimize=True, pnginfo=pnginfo)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _chromium_executable() -> str:
    explicit = os.environ.get("WAVE_CHROMIUM")
    if explicit:
        found = explicit if Path(explicit).is_file() else shutil.which(explicit)
        if found:
            return found
        raise RuntimeError(f"WAVE_CHROMIUM does not point to an executable: {explicit}")
    for command in (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
        "msedge",
    ):
        found = shutil.which(command)
        if found:
            return found
    raise RuntimeError(
        "equation asset regeneration needs Chromium; install it or set WAVE_CHROMIUM"
    )


def _mathjax_script(render_root: Path) -> Path:
    explicit = os.environ.get("WAVE_MATHJAX")
    candidates = [Path(explicit)] if explicit else []
    bundled = ROOT / "release" / "assets" / "mathjax" / "tex-chtml-full.js"
    if bundled.is_file():
        candidates.append(bundled)
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size:
            return candidate.resolve()
    archive = ROOT / "build" / "html-vendor" / "mathjax-3.2.2.tar.gz"
    if archive.is_file() and archive.stat().st_size:
        extracted = render_root / "mathjax"
        extracted.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as source:
            source.extractall(extracted, filter="data")
        matches = sorted(extracted.glob("*/es5/tex-chtml-full.js"))
        if matches:
            return matches[0].resolve()
    raise RuntimeError(
        "equation asset regeneration needs the pinned MathJax 3.2.2 runtime; "
        "build the HTML edition first, provide build/html-vendor, or set WAVE_MATHJAX"
    )


def _native_mathml_fragments(
    displays: tuple[EquationDisplay, ...], workdir: Path
) -> tuple[str, ...]:
    if shutil.which("pandoc") is None:
        raise RuntimeError(
            "equation asset regeneration needs Pandoc for the native MathML path"
        )
    source = workdir / "equations.tex"
    output = workdir / "equations.html"
    source.write_text(
        "\n\n".join(equation_markdown_math(display) for display in displays) + "\n"
    )
    run(
        [
            "pandoc",
            str(source),
            "-f",
            "latex+smart",
            "-t",
            "html5",
            "--mathml",
            "-s",
            "-o",
            str(output),
        ],
        quiet=False,
    )
    text = output.read_text(errors="replace")
    fragments = tuple(re.findall(r"<math\b.*?</math>", text, re.DOTALL | re.IGNORECASE))
    if len(fragments) != len(displays):
        raise RuntimeError(
            "Pandoc native MathML output count does not match the extracted equation "
            f"count ({len(fragments)} != {len(displays)})"
        )
    return fragments


EQUATION_BROWSER_ROW_HEIGHT = 480
EQUATION_BROWSER_ROWS_PER_BATCH = 16
EQUATION_BROWSER_WIDTH = 2400
EQUATION_BROWSER_HEIGHT = 8400


def _equation_browser_html(
    entries: tuple[tuple[str, str], ...], kind: str, mathjax_script: Path | None
) -> str:
    rows = []
    for stem, markup in entries:
        content = html.escape(markup, quote=False) if kind == "mathjax" else markup
        rows.append(f'<div class="wave-equation" data-stem="{stem}">{content}</div>')
    script = ""
    if kind == "mathjax":
        assert mathjax_script is not None
        script = (
            "<script>window.MathJax={tex:{packages:{'[+]':['ams']}},"
            "options:{enableMenu:false}};</script>"
            f'<script src="{html.escape(mathjax_script.as_uri(), quote=True)}"></script>'
            "<script>MathJax.startup.promise.then(function(){"
            "document.documentElement.dataset.waveReady='true';});</script>"
        )
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        "html,body{margin:0;padding:0;background:#fff;}"
        ".wave-equation{box-sizing:border-box;width:2300px;height:480px;"
        "display:flex;align-items:center;justify-content:center;overflow:hidden;"
        "padding:24px;background:#fff;color:#000;font-size:1rem;}"
        ".wave-equation mjx-container{margin:0!important;}"
        "</style></head><body>" + "".join(rows) + script + "</body></html>"
    )


def _browser_screenshot(browser: str, page: Path, destination: Path) -> None:
    command = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--disable-component-update",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        "--force-device-scale-factor=2",
        f"--window-size={EQUATION_BROWSER_WIDTH},{EQUATION_BROWSER_HEIGHT}",
        f"--screenshot={destination}",
    ]
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
        command.append("--no-sandbox")
    run(command + [page.as_uri()], quiet=False)


def _trim_equation_browser_row(screenshot: Path, row: int) -> Image.Image:
    with Image.open(screenshot) as source:
        image = source.convert("RGB")
    scale = image.width / EQUATION_BROWSER_WIDTH
    y0 = round(row * EQUATION_BROWSER_ROW_HEIGHT * scale)
    y1 = min(image.height, round((row + 1) * EQUATION_BROWSER_ROW_HEIGHT * scale))
    cell = image.crop((0, y0, image.width, y1))
    diff = ImageChops.difference(cell, Image.new("RGB", cell.size, "white"))
    bbox = diff.getbbox()
    if bbox is None:
        raise RuntimeError(f"browser produced an empty equation row {row + 1}")
    margin = round(12 * scale)
    return cell.crop(
        (
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(cell.width, bbox[2] + margin),
            min(cell.height, bbox[3] + margin),
        )
    )


def _render_equation_browser_assets(
    displays: tuple[EquationDisplay, ...],
    destinations: dict[tuple[str, str], Path],
    workdir: Path,
) -> None:
    browser = _chromium_executable()
    mathjax_script = _mathjax_script(workdir)
    mathml_fragments = _native_mathml_fragments(displays, workdir)
    entries_by_kind = {
        "mathjax": tuple(
            (display.stem, equation_markdown_math(display)) for display in displays
        ),
        "mathml": tuple(
            (display.stem, fragment)
            for display, fragment in zip(displays, mathml_fragments, strict=True)
        ),
    }
    for kind, entries in entries_by_kind.items():
        for batch_start in range(0, len(entries), EQUATION_BROWSER_ROWS_PER_BATCH):
            batch = entries[batch_start : batch_start + EQUATION_BROWSER_ROWS_PER_BATCH]
            page = workdir / f"{kind}-{batch_start:04d}.html"
            screenshot = workdir / f"{kind}-{batch_start:04d}.png"
            page.write_text(_equation_browser_html(batch, kind, mathjax_script))
            _browser_screenshot(browser, page, screenshot)
            for offset, (stem, _markup) in enumerate(batch):
                image = _trim_equation_browser_row(screenshot, offset)
                display = displays[batch_start + offset]
                _save_generated_equation_png(
                    destinations[(stem, kind)],
                    image,
                    _equation_asset_metadata(display, kind),
                )


def _render_equation_source_assets(
    displays: tuple[EquationDisplay, ...],
    destinations: dict[tuple[str, str], Path],
    equation_dir: Path,
) -> None:
    page_images: dict[tuple[str, int], Image.Image] = {}
    try:
        for display in displays:
            source_path = equation_dir / f"{display.stem}-source.png"
            crop = _recorded_equation_source_crop(display, source_path)
            page_key = (EQUATION_SOURCE_PDFS[display.chapter], display.physical_page)
            if page_key not in page_images:
                page_path = _equation_source_page_path(display, crop.dpi)
                with Image.open(page_path) as page:
                    page_images[page_key] = page.convert("RGB")
            page = page_images[page_key]
            x, y, width, height = crop.pixels
            if x < 0 or y < 0 or x + width > page.width or y + height > page.height:
                raise RuntimeError(
                    f"{source_path}: recorded crop is outside source page"
                )
            image = page.crop((x, y, x + width, y + height))
            _save_generated_equation_png(
                destinations[(display.stem, "source")],
                image,
                _equation_asset_metadata(display, "source", source_crop=crop),
            )
    finally:
        for image in page_images.values():
            image.close()


def regenerate_equation_assets(
    displays: Iterable[EquationDisplay] | None = None,
    equation_dir: Path | None = None,
) -> int:
    """Regenerate source, MathJax, and native-MathML review PNG pixels."""
    displays = tuple(displays if displays is not None else collect_equation_displays())
    equation_dir = equation_dir or SRC / "equations"
    equation_dir.mkdir(parents=True, exist_ok=True)
    if not displays:
        return 0
    with tempfile.TemporaryDirectory(prefix="wave-equation-assets-") as temporary:
        workdir = Path(temporary)
        destinations = {
            (display.stem, kind): workdir / f"{display.stem}-{kind}.png"
            for display in displays
            for kind in EQUATION_ASSET_KINDS
        }
        _render_equation_source_assets(displays, destinations, equation_dir)
        _render_equation_browser_assets(displays, destinations, workdir)
        for display in displays:
            for kind in EQUATION_ASSET_KINDS:
                source = destinations[(display.stem, kind)]
                if not source.is_file() or source.stat().st_size == 0:
                    raise RuntimeError(f"equation renderer did not produce {source}")
                target = equation_dir / f"{display.stem}-{kind}.png"
                temporary_target = equation_dir / f".{target.name}.tmp"
                try:
                    shutil.copyfile(source, temporary_target)
                    temporary_target.replace(target)
                finally:
                    temporary_target.unlink(missing_ok=True)
    return len(displays) * len(EQUATION_ASSET_KINDS)


def refresh_equation_assets(
    displays: Iterable[EquationDisplay] | None = None,
    equation_dir: Path | None = None,
) -> int:
    """Regenerate equation review assets using the current v2 renderers."""
    return regenerate_equation_assets(displays, equation_dir)


EQUATION_LEDGER_HEADER = (
    "<!-- Generated from src/chapter1.tex through src/chapter6.tex.\n"
    "     Do not edit equation entries by hand. -->"
)


def _equation_entry_text(display: EquationDisplay) -> list[str]:
    assets = tuple(
        f"[![{label}](../equations/{display.stem}-{kind}.png)]"
        f"(../equations/{display.stem}-{kind}.png)"
        for label, kind in (
            ("Source PDF", "source"),
            ("MathJax", "mathjax"),
            ("MathML", "mathml"),
        )
    )
    return [
        f"### p. {display.printed_page} · display {display.display_ordinal} · {display.stem}",
        "",
        (
            f"Source: [chapter{display.chapter}.tex](../chapter{display.chapter}.tex):{display.line} "
            f"· display type: `{display.display_type}`"
        ),
        "",
        "#### Markdown math",
        "",
        equation_markdown_math(display),
        "",
        "<details>",
        "<summary>LaTeX source</summary>",
        "",
        "```tex",
        display.source,
        "```",
        "",
        "</details>",
        "",
        "| Source PDF | MathJax | MathML |",
        "| --- | --- | --- |",
        f"| {assets[0]} | {assets[1]} | {assets[2]} |",
        "",
    ]


def equation_ledger_texts(
    source_dir: Path | None = None,
) -> tuple[str, dict[int, str], int]:
    """Return deterministic root and per-chapter equation ledger text."""
    displays = collect_equation_displays(source_dir)
    by_chapter = {
        chapter: tuple(display for display in displays if display.chapter == chapter)
        for chapter in range(1, 7)
    }
    root_lines = [
        "# Equation audit",
        "",
        "<!-- Generated from src/chapter1.tex through src/chapter6.tex. -->",
        "",
        (
            "This audit covers the display equations in the six maintained chapter TeX "
            "files. The chapter ledgers are the detailed review surface; the mathematical "
            "source of truth remains the chapter TeX."
        ),
        "",
        (
            "Each chapter entry pairs the exact extracted display with its source-page "
            "crop, MathJax rendering, and native MathML rendering."
        ),
        "",
        f"The six chapters contain **{len(displays)} display equations**.",
        "",
        "## Summary",
        "",
        "| Chapter | Displays |",
        "| --- | ---: |",
    ]
    for chapter in range(1, 7):
        root_lines.append(f"| Chapter {chapter} | {len(by_chapter[chapter])} |")
    root_lines.extend(
        [
            "",
            "## Chapters",
            "",
            *(
                f"- [Chapter {chapter}](equations/CHAPTER{chapter}.md) — "
                f"{len(by_chapter[chapter])} displays"
                for chapter in range(1, 7)
            ),
            "",
            "## Review states",
            "",
            "Each entry includes three independent review renderings:",
            "",
            "- `source` — a crop of the corresponding source-PDF page.",
            "- `mathjax` — the rendered Markdown equation.",
            "- `mathml` — native MathML rendered by the configured browser.",
            "",
            "The images support source and rendering review; they do not imply human approval.",
        ]
    )
    chapter_texts: dict[int, str] = {}
    for chapter in range(1, 7):
        lines = [
            f"# Equation audit — Chapter {chapter}",
            "",
            EQUATION_LEDGER_HEADER,
            "",
            "[Back to the equation audit](../EQUATIONS.md)",
            "",
            "Entries follow printed-page order and display order within each page.",
            (
                "The Markdown math and raw LaTeX source are produced from the same "
                "extracted display."
            ),
            "",
        ]
        for display in by_chapter[chapter]:
            lines.extend(_equation_entry_text(display))
        chapter_texts[chapter] = "\n".join(lines).rstrip("\n") + "\n"
    return "\n".join(root_lines).rstrip("\n") + "\n", chapter_texts, len(displays)


def equation_ledger_text(
    source_dir: Path | None = None,
) -> tuple[str, int]:
    """Return the generated root equation ledger and extracted count."""
    root, _chapters, count = equation_ledger_texts(source_dir)
    return root, count


def equation_chapter_ledger_text(
    chapter: int,
    source_dir: Path | None = None,
) -> str:
    _root, chapters, _count = equation_ledger_texts(source_dir)
    return chapters[chapter]


def equation_ledger_errors(
    root: Path | None = None,
    source_dir: Path | None = None,
    chapters: Iterable[int] | None = None,
) -> list[str]:
    """Return stale, missing, or unexpected generated equation ledger files."""
    root = root or SRC / "EQUATIONS.md"
    source_dir = source_dir or SRC
    selected = tuple(chapters) if chapters is not None else FIGURE_LEDGER_CHAPTERS
    invalid = sorted(set(selected) - set(FIGURE_LEDGER_CHAPTERS))
    if invalid:
        return [f"invalid equation audit chapter(s): {', '.join(map(str, invalid))}"]
    output_root = root.parent
    expected_root, expected_chapters, _ = equation_ledger_texts(source_dir)
    errors: list[str] = []
    if not root.is_file() or root.read_bytes() != expected_root.encode("utf-8"):
        command = "uv run --frozen python scripts/publication.py equations"
        if chapters is not None and len(selected) == 1:
            command += f" --chapter {selected[0]}"
        errors.append(
            f"equation audit landing page is stale or missing: {root}\n"
            f"Regenerate: {command}"
        )
    equation_dir = output_root / "equations"
    expected_names = {f"CHAPTER{chapter}.md" for chapter in range(1, 7)}
    actual_names = {path.name for path in equation_dir.glob("*.md")}
    for chapter in selected:
        expected = expected_chapters[chapter]
        path = equation_dir / f"CHAPTER{chapter}.md"
        if path.is_file():
            errors.extend(_stray_chapter_heading_errors(path, chapter))
        if not path.is_file() or path.read_bytes() != expected.encode("utf-8"):
            errors.append(
                f"Equation audit changed in Chapter {chapter} "
                "(stale ledger text; see the per-entry manifest diagnostic).\n"
                "Regenerate: uv run --frozen python scripts/publication.py equations "
                f"--chapter {chapter}"
            )
        errors.extend(_equation_manifest_errors(chapter, output_root, source_dir))
    if chapters is None:
        for name in sorted(actual_names - expected_names):
            errors.append(f"unexpected equation chapter ledger: {equation_dir / name}")
    return errors


def equation_ledger_matches(path: Path | None = None) -> bool:
    return not equation_ledger_errors(path)


def write_equation_ledger(
    path: Path | None = None,
    chapters: Iterable[int] | None = None,
    source_dir: Path | None = None,
) -> int:
    """Regenerate selected equation ledgers, manifests, and the root summary."""
    output = path or SRC / "EQUATIONS.md"
    source_dir = source_dir or SRC
    selected = tuple(chapters) if chapters is not None else FIGURE_LEDGER_CHAPTERS
    root, chapter_texts, count = equation_ledger_texts(source_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.is_file() or output.read_bytes() != root.encode("utf-8"):
        output.write_bytes(root.encode("utf-8"))
    equation_dir = output.parent / "equations"
    equation_dir.mkdir(parents=True, exist_ok=True)
    for chapter in selected:
        text = chapter_texts[chapter]
        chapter_path = equation_dir / f"CHAPTER{chapter}.md"
        if not chapter_path.is_file() or chapter_path.read_bytes() != text.encode(
            "utf-8"
        ):
            chapter_path.write_bytes(text.encode("utf-8"))
        manifest = equation_dir / f"CHAPTER{chapter}.sha256"
        manifest_text = equation_ledger_manifest_text(chapter, source_dir)
        if not manifest.is_file() or manifest.read_bytes() != manifest_text.encode(
            "utf-8"
        ):
            manifest.write_bytes(manifest_text.encode("utf-8"))
    return count


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
    text = text.replace(r"\"a", "ä").replace(r"\"o", "ö").replace(r"\"u", "ü")
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
        path = SRC / f"chapter{number}.tex"
        text = path.read_text()
        chapter_titles = _balanced_command_args(text, "chapter")
        if len(chapter_titles) != 1:
            raise ValueError(
                f"{path}: expected one \\chapter, found {len(chapter_titles)}"
            )
        section_titles = tuple(_balanced_command_args(text, "section"))
        chapters.append(
            Chapter(
                number=number,
                title=tex_plain(chapter_titles[0]),
                sections=tuple(tex_plain(section) for section in section_titles),
            )
        )
    return tuple(chapters)


def html_license() -> str:
    icons = "".join(
        f'<img src="assets/cc/{name}.svg" alt="" '
        'style="max-width: 1em;max-height:1em;margin-left: .2em;">'
        for name in CC_ICONS
    )
    return (
        '<p class="license">This work is licensed under '
        f'<a href="{LICENSE_URL}">CC BY-NC-SA 4.0</a>. {icons}</p>'
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
        return (
            subprocess.check_output(
                ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            ).strip()
            or None
        )
    except OSError, subprocess.CalledProcessError:
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
        return (
            f"{self.version} ({self.revision_label})"
            if self.version
            else self.revision_label
        )

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
    return BuildInfo(
        sha=sha, short_sha=short_sha, version=version.strip() if version else None
    )


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


def _equations_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publication.py equations")
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the selected chapter ledgers and manifests without writing",
    )
    parser.add_argument(
        "--assets",
        action="store_true",
        help="regenerate or check the selected equation review PNGs",
    )
    parser.add_argument("--chapter", type=int, choices=FIGURE_LEDGER_CHAPTERS)
    args = parser.parse_args(argv)
    output = SRC / "EQUATIONS.md"
    chapters = (args.chapter,) if args.chapter is not None else None
    selected_displays = tuple(
        display
        for display in collect_equation_displays()
        if chapters is None or display.chapter in chapters
    )
    scope = f"Chapter {args.chapter}" if args.chapter is not None else "all chapters"
    errors: list[str] = []
    if args.check:
        errors.extend(equation_ledger_errors(output, chapters=chapters))
    else:
        count = write_equation_ledger(output, chapters=chapters)
        if not args.assets:
            print(f"generated equation ledgers for {scope}: {output} ({count} entries)")

    if args.assets:
        if args.check:
            asset_displays = None if args.chapter is None else selected_displays
            errors.extend(equation_asset_errors(asset_displays))
        else:
            stale = stale_equation_displays(selected_displays)
            if stale:
                regenerate_equation_assets(stale)
                stale_chapters = tuple(sorted({display.chapter for display in stale}))
                chapter_label = (
                    f"Chapter {stale_chapters[0]}"
                    if len(stale_chapters) == 1
                    else "Chapters " + ", ".join(map(str, stale_chapters))
                )
                equation_word = "equation" if len(stale) == 1 else "equations"
                print(
                    f"Regenerated {len(stale)} {equation_word} "
                    f"({len(stale) * len(EQUATION_ASSET_KINDS)} review assets) "
                    f"in {chapter_label}."
                )
            else:
                print(f"Equation review assets are current for {scope}.")
    if errors:
        print(
            "equation audit validation failed:\n- "
            + "\n- ".join(summarize_equation_asset_errors(errors)),
            file=sys.stderr,
        )
        return 1
    if args.check:
        scope = (
            f"Chapter {args.chapter}" if args.chapter is not None else "all chapters"
        )
        print(f"equation audit is current for {scope}: {output}")
        if args.assets:
            print(f"Equation review assets are current for {scope}.")
    return 0


def _figures_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publication.py figures")
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the selected chapter ledger and manifest without writing",
    )
    parser.add_argument("--chapter", type=int, choices=FIGURE_LEDGER_CHAPTERS)
    args = parser.parse_args(argv)
    output = SRC / "FIGURES.md"
    chapters = (args.chapter,) if args.chapter is not None else None
    if args.check:
        errors = figure_ledger_errors(chapters=chapters)
        if errors:
            print(
                "figure ledger validation failed:\n- " + "\n- ".join(errors),
                file=sys.stderr,
            )
            return 1
        scope = (
            f"Chapter {args.chapter}" if args.chapter is not None else "all chapters"
        )
        print(f"figure audit is current for {scope}: {output}")
        return 0
    count = write_figure_chapter_ledgers(SRC, chapters)
    scope = f"Chapter {args.chapter}" if args.chapter is not None else "all chapters"
    print(f"generated figure audit for {scope}: {output} ({count} placements)")
    return 0


def _audit_candidate_chapters(paths: Iterable[str]) -> tuple[bool, tuple[int, ...]]:
    """Map changed hook paths to chapters, conservatively when uncertain."""
    chapters: set[int] = set()
    all_chapters = False
    for raw_path in paths:
        path = raw_path.replace("\\", "/").lstrip("./")
        if not path:
            continue
        if path in {
            "scripts/publication.py",
            "scripts/compare_figures.py",
            ".pre-commit-config.yaml",
        } or path.startswith("skills/"):
            all_chapters = True
            continue
        chapter_match = re.search(r"(?:^|/)chapter([1-6])\.tex$", path)
        if chapter_match:
            chapters.add(int(chapter_match.group(1)))
            continue
        if path.endswith(("src/FIGURES.md", "src/EQUATIONS.md")):
            all_chapters = True
            continue
        if "/figures/" in f"/{path}/" or "/equations/" in f"/{path}/":
            match = re.search(r"CHAPTER([1-6])(?:\.|/)|ch0([1-6])[-.]", path)
            if match:
                chapters.add(int(match.group(1) or match.group(2)))
            else:
                all_chapters = True
            continue
        if path.startswith("references/"):
            all_chapters = True
    if all_chapters or not chapters:
        return True, FIGURE_LEDGER_CHAPTERS
    return False, tuple(sorted(chapters))


def _equation_manifest_change_ids(
    chapters: Iterable[int],
) -> dict[int, tuple[str, ...]]:
    changes: dict[int, tuple[str, ...]] = {}
    for chapter in chapters:
        displays = extract_equation_displays(chapter, SRC / f"chapter{chapter}.tex")
        expected = {
            display.stem: equation_entry_digest(display) for display in displays
        }
        current, _errors = _read_manifest(
            SRC / "equations" / f"CHAPTER{chapter}.sha256"
        )
        added, _removed, changed = _manifest_change_lines(current, expected)
        changes[chapter] = tuple(sorted(set(added) | set(changed)))
    return changes


def _changed_equation_asset_stems(paths: Iterable[str]) -> tuple[str, ...]:
    pattern = re.compile(
        r"(ch[0-9]{2}-p[0-9]{3}-e[0-9]{2,})-(?:source|mathjax|mathml)\.png$"
    )
    return tuple(
        sorted(
            {
                match.group(1)
                for raw_path in paths
                if (match := pattern.search(raw_path.replace("\\", "/")))
            }
        )
    )


def _audit_check_only(
    selected: tuple[int, ...] | None,
    *,
    full_assets: bool = False,
) -> list[str]:
    errors = figure_ledger_errors(chapters=selected)
    errors.extend(equation_ledger_errors(chapters=selected))
    if full_assets:
        errors.extend(equation_asset_errors())
    return errors


def _audit_update_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publication.py audit-update")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    all_chapters, candidate = _audit_candidate_chapters(args.paths)
    if args.all:
        all_chapters = True
        candidate = FIGURE_LEDGER_CHAPTERS
    selected = None if all_chapters else candidate
    check_only = args.check or os.environ.get("WAVE_AUDIT_CHECK_ONLY") == "1"
    if check_only:
        errors = _audit_check_only(selected, full_assets=args.all)
        if errors:
            print(
                "audit freshness check failed:\n- "
                + "\n- ".join(summarize_equation_asset_errors(errors)),
                file=sys.stderr,
            )
            return 1
        return 0

    chapters = FIGURE_LEDGER_CHAPTERS if selected is None else selected
    equation_changes = _equation_manifest_change_ids(chapters)
    write_figure_chapter_ledgers(SRC, chapters)
    write_equation_ledger(SRC / "EQUATIONS.md", chapters=chapters)

    displays = collect_equation_displays()
    stale_asset_chapters: set[int] = set()
    if selected is None:
        stale = {display.stem for display in stale_equation_displays(displays)}
        stale_asset_chapters.update(
            display.chapter for display in displays if display.stem in stale
        )
    else:
        for chapter, ids in equation_changes.items():
            candidates = tuple(
                display
                for display in displays
                if display.chapter == chapter and display.stem in ids
            )
            stale = _equation_asset_input_stale_ids(candidates)
            if stale:
                stale_asset_chapters.add(chapter)

    changed_stems = set(_changed_equation_asset_stems(args.paths))
    if changed_stems:
        direct = tuple(display for display in displays if display.stem in changed_stems)
        for display in direct:
            if equation_asset_errors_for_display(
                display,
                SRC / "equations",
                validate_source_page=False,
            ):
                stale_asset_chapters.add(display.chapter)

    if stale_asset_chapters:
        chapters_text = ", ".join(map(str, sorted(stale_asset_chapters)))
        chapter_word = "Chapter" if len(stale_asset_chapters) == 1 else "Chapters"
        print(
            f"Equation review assets are stale in {chapter_word} {chapters_text}.\n\n"
            "Regenerate:\n"
            + "\n".join(
                "  uv run --frozen python scripts/publication.py equations "
                f"--chapter {chapter} --assets"
                for chapter in sorted(stale_asset_chapters)
            ),
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shared publication support utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "build-info", help="print or write the current build identity"
    )
    subparsers.add_parser(
        "equations", help="regenerate or check the equation review ledger"
    )
    subparsers.add_parser(
        "figures", help="generate or check the figure audit landing page"
    )
    subparsers.add_parser(
        "audit-check", help="check affected figure/equation ledgers without writing"
    )
    subparsers.add_parser(
        "audit-update",
        help="refresh affected figure/equation ledgers without rendering PNGs",
    )
    args, remainder = parser.parse_known_args(argv)
    if args.command == "build-info":
        return _build_info_cli(remainder)
    if args.command == "equations":
        return _equations_cli(remainder)
    if args.command == "figures":
        return _figures_cli(remainder)
    if args.command == "audit-check":
        return _audit_update_cli(["--check", *remainder])
    if args.command == "audit-update":
        return _audit_update_cli(remainder)
    raise SystemExit(f"unsupported publication command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
