#!/usr/bin/env python3
"""Regenerate source-vs-reconstruction figure comparisons on demand.

Vector provenance is stored in each retained .tikz file as:
    % wave-source: pdf=ChapmanRizzoli5.pdf; page=21; trim=...bp ...bp ...bp ...bp

Edited-raster provenance is embedded as PNG text metadata (wave-source-*).
Outputs are temporary and always written under build/comparisons/<figure>/.
No overlay or difference image is produced.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
FIGURES = RECON / "figures"
SOURCE = ROOT / "source"
OUTROOT = ROOT / "build" / "comparisons"
META_RE = re.compile(
    r"^% wave-source:\s*pdf=(?P<pdf>[^;]+);\s*page=(?P<page>\d+);\s*"
    r"trim=(?P<trim>[^\n]+)$",
    re.MULTILINE,
)


def load_publication_renderer() -> ModuleType:
    """Load the HTML builder so comparison renders use its exact figure geometry."""
    path = ROOT / "scripts" / "build-html.py"
    spec = importlib.util.spec_from_file_location("wave_build_html", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load publication renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PUBLICATION_RENDERER = load_publication_renderer()


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def render_original(pdf_name: str, page: int, trim: str, out_png: Path, dpi: int) -> None:
    pdf = SOURCE / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    with tempfile.TemporaryDirectory(prefix="wave-source-") as td:
        tdpath = Path(td)
        prefix = tdpath / "page"
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
            ]
        )
        img = Image.open(prefix.with_suffix(".png")).convert("RGB")
        pw, ph = PUBLICATION_RENDERER.page_size_points(pdf, page)
        left, bottom, right, top = PUBLICATION_RENDERER.parse_trim(trim)
        x0 = round(left / pw * img.width)
        x1 = round(img.width - right / pw * img.width)
        y0 = round(top / ph * img.height)
        y1 = round(img.height - bottom / ph * img.height)
        if not (0 <= x0 < x1 <= img.width and 0 <= y0 < y1 <= img.height):
            raise ValueError(f"Invalid crop for {pdf_name} page {page}: {trim}")
        img.crop((x0, y0, x1, y1)).save(out_png)


def render_tikz(stem: str, out_png: Path, dpi: int) -> None:
    tikz = FIGURES / f"{stem}.tikz"
    with tempfile.TemporaryDirectory(prefix="wave-vector-") as td:
        tdpath = Path(td)
        tex = tdpath / "figure.tex"
        tex.write_text(PUBLICATION_RENDERER.TIKZ_STANDALONE_TEMPLATE % tikz.as_posix())
        run(
            [
                "latexmk",
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "figure.tex",
            ],
            cwd=tdpath,
        )
        prefix = tdpath / "render"
        run(
            [
                "pdftoppm",
                "-singlefile",
                "-r",
                str(dpi),
                "-png",
                str(tdpath / "figure.pdf"),
                str(prefix),
            ]
        )
        shutil.copy2(prefix.with_suffix(".png"), out_png)


def side_by_side(left_path: Path, right_path: Path, out_path: Path) -> None:
    left = Image.open(left_path).convert("RGB")
    right = Image.open(right_path).convert("RGB")
    target_h = max(left.height, right.height)

    def fit_height(img: Image.Image) -> Image.Image:
        if img.height == target_h:
            return img
        scale = target_h / img.height
        return img.resize((max(1, round(img.width * scale)), target_h), Image.Resampling.LANCZOS)

    left = fit_height(left)
    right = fit_height(right)
    gap = 40
    margin = 24
    header = 46
    canvas = Image.new(
        "RGB",
        (left.width + right.width + gap + 2 * margin, target_h + header + 2 * margin),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 12), "Original source", fill="black")
    draw.text((margin + left.width + gap, 12), "Reconstruction", fill="black")
    y = header + margin
    canvas.paste(left, (margin, y))
    canvas.paste(right, (margin + left.width + gap, y))
    canvas.save(out_path)


def compare(stem: str, dpi: int) -> Path:
    tikz = FIGURES / f"{stem}.tikz"
    raster = FIGURES / f"{stem}.png"
    pdf_name: str
    page: int
    trim: str
    kind: str

    if tikz.exists():
        text = tikz.read_text()
        m = META_RE.search(text)
        if not m:
            raise RuntimeError(f"Missing wave-source provenance comment in {tikz}")
        pdf_name = m.group("pdf").strip()
        page = int(m.group("page"))
        trim = m.group("trim").strip()
        kind = "vector"
    elif raster.exists():
        with Image.open(raster) as img:
            info = img.info
            try:
                pdf_name = str(info["wave-source-pdf"])
                page = int(info["wave-source-page"])
                trim = str(info["wave-source-trim"])
            except KeyError as exc:
                raise RuntimeError(f"Missing embedded wave-source metadata in {raster}") from exc
        kind = "edited-raster"
    else:
        raise FileNotFoundError(f"No retained vector or edited raster named {stem!r}")

    outdir = OUTROOT / stem
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    original = outdir / "original.png"
    reconstruction = outdir / "reconstruction.png"
    comparison = outdir / "comparison.png"
    render_original(pdf_name, page, trim, original, dpi)
    if kind == "vector":
        render_tikz(stem, reconstruction, dpi)
    else:
        with Image.open(raster) as img:
            img.convert("RGB").save(reconstruction)
    side_by_side(original, reconstruction, comparison)
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "figure", nargs="?", help="figure basename, e.g. ch05-p116-edge-wave-dispersion"
    )
    group.add_argument(
        "--all", action="store_true", help="regenerate comparisons for every retained TikZ figure"
    )
    parser.add_argument("--dpi", type=int, default=180, help="render resolution (default: 180)")
    args = parser.parse_args()

    if args.all:
        stems = {p.stem for p in FIGURES.glob("*.tikz")}
        for p in FIGURES.glob("*.png"):
            try:
                with Image.open(p) as img:
                    if "wave-source-pdf" in img.info:
                        stems.add(p.stem)
            except OSError:
                pass
        stems = sorted(stems)
    else:
        stems = [args.figure]
    failures: list[tuple[str, Exception]] = []
    for stem in stems:
        try:
            path = compare(stem, args.dpi)
            print(f"{stem}: {path.relative_to(ROOT)}")
        except Exception as exc:  # report all failures in --all mode
            failures.append((stem, exc))
            print(f"{stem}: ERROR: {exc}", file=sys.stderr)
            if not args.all:
                break
    if failures:
        print(f"{len(failures)} comparison(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
