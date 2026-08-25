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
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw
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


def _equation_body(display: EquationDisplay) -> str:
    lines = display.source.splitlines()
    if len(lines) < 2:
        raise ValueError(f"display source is incomplete for {display.stem}")
    return "\n".join(lines[1:-1])


def equation_markdown_math(display: EquationDisplay) -> str:
    """Convert only repository display wrappers to GitHub Markdown math."""
    body = _equation_body(display)
    if display.display_type == "bracket":
        return f"$$\n{body}\n$$"
    if display.display_type in {"waveequation", "equation", "equation*"}:
        return f"$$\n{body}\n$$"
    if display.display_type in {
        "wavealign",
        "align",
        "align*",
        "gather",
        "gather*",
        "multline",
        "multline*",
    }:
        return f"$$\n\\begin{{aligned}}\n{body}\n\\end{{aligned}}\n$$"
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


def equation_asset_errors(
    displays: Iterable[EquationDisplay] | None = None,
) -> list[str]:
    """Return missing/empty PNG errors for the equation identities."""
    displays = displays if displays is not None else collect_equation_displays()
    errors: list[str] = []
    for display in displays:
        for path in equation_asset_paths(display.stem):
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing or empty equation asset: {path}")
    return errors


EQUATION_LEDGER_HEADER = (
    "<!-- Generated from src/chapter1.tex through src/chapter6.tex.\n"
    "     Do not edit equation entries by hand. -->"
)


def equation_ledger_text(
    source_dir: Path | None = None,
) -> tuple[str, int]:
    """Return deterministic ledger bytes as text and the extracted count."""
    displays = collect_equation_displays(source_dir)
    lines = [
        "# Equation ledger",
        "",
        EQUATION_LEDGER_HEADER,
        "",
        "This file is generated review material for the display equations in the six maintained chapter TeX files.",
        "Entries follow chapter order, printed-page order, and display order within each page.",
        "The Markdown equation and the LaTeX source block are produced from the same extracted display.",
        "",
    ]
    current_chapter: int | None = None
    for display in displays:
        if display.chapter != current_chapter:
            current_chapter = display.chapter
            lines.extend([f"## Chapter {current_chapter}", ""])
        asset_headers = ("Source PDF", "MathJax", "MathML")
        asset_cells = (
            (
                f"[![Source PDF](equations/{display.stem}-source.png)]"
                f"(equations/{display.stem}-source.png)"
            ),
            (
                f"[![MathJax](equations/{display.stem}-mathjax.png)]"
                f"(equations/{display.stem}-mathjax.png)"
            ),
            (
                f"[![MathML](equations/{display.stem}-mathml.png)]"
                f"(equations/{display.stem}-mathml.png)"
            ),
        )
        asset_widths = tuple(
            max(len(header), len(cell))
            for header, cell in zip(asset_headers, asset_cells, strict=True)
        )
        asset_table = (
            "| "
            + " | ".join(
                cell.ljust(width)
                for cell, width in zip(asset_headers, asset_widths, strict=True)
            )
            + " |",
            "| " + " | ".join("-" * width for width in asset_widths) + " |",
            "| "
            + " | ".join(
                cell.ljust(width)
                for cell, width in zip(asset_cells, asset_widths, strict=True)
            )
            + " |",
        )
        lines.extend(
            [
                f"### p. {display.printed_page} · display {display.display_ordinal} · {display.stem}",
                "",
                f"Source: `src/chapter{display.chapter}.tex:{display.line}` · display type: `{display.display_type}`",
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
                *asset_table,
                "",
            ]
        )
    return "\n".join(lines).rstrip("\n") + "\n", len(displays)


def equation_ledger_matches(path: Path | None = None) -> bool:
    """Compare a checked-in ledger with a fresh in-memory regeneration."""
    output = path or SRC / "EQUATIONS.md"
    expected, _ = equation_ledger_text()
    return output.is_file() and output.read_bytes() == expected.encode("utf-8")


def write_equation_ledger(path: Path | None = None) -> int:
    """Regenerate the maintained equation ledger and return its display count."""
    output = path or SRC / "EQUATIONS.md"
    text, count = equation_ledger_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.encode("utf-8"))
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
        help="regenerate in a temporary location and compare byte-for-byte",
    )
    args = parser.parse_args(argv)
    output = SRC / "EQUATIONS.md"
    if args.check:
        with tempfile.TemporaryDirectory(prefix="wave-equations-check-") as temporary:
            fresh = Path(temporary) / "EQUATIONS.md"
            count = write_equation_ledger(fresh)
            if not output.is_file() or output.read_bytes() != fresh.read_bytes():
                print(
                    f"equation ledger is stale: {output}; "
                    "run 'uv run --frozen python scripts/publication.py equations' "
                    f"to regenerate {count} entries",
                    file=sys.stderr,
                )
                return 1
        print(f"equation ledger is current: {output}")
        return 0

    count = write_equation_ledger(output)
    print(f"generated equation ledger: {output} ({count} entries)")
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
    args, remainder = parser.parse_known_args(argv)
    if args.command == "build-info":
        return _build_info_cli(remainder)
    if args.command == "equations":
        return _equations_cli(remainder)
    raise SystemExit(f"unsupported publication command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
