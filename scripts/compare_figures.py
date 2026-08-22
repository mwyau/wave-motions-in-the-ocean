#!/usr/bin/env python3
"""Regenerate source-vs-reconstruction figure comparisons on demand.

Vector provenance is stored in each retained .tikz file as:
    % wave-source: pdf=ChapmanRizzoli5.pdf; page=21; trim=...bp ...bp ...bp ...bp

Edited-raster provenance is embedded as PNG text metadata (wave-source-*).
Outputs are temporary side-by-side images written directly under
audit/figures/comparisons/<figure>.png.
No overlay or difference image is produced.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from publication import render_source_crop, render_tikz_png

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
FIGURES = RECON / "figures"
OUTROOT = ROOT / "audit" / "figures" / "comparisons"
META_RE = re.compile(
    r"^% wave-source:\s*pdf=(?P<pdf>[^;]+);\s*page=(?P<page>\d+);\s*"
    r"trim=(?P<trim>[^\n]+)$",
    re.MULTILINE,
)


def side_by_side(left_path: Path, right_path: Path, out_path: Path) -> None:
    left = Image.open(left_path).convert("RGB")
    right = Image.open(right_path).convert("RGB")
    target_h = max(left.height, right.height)

    def fit_height(img: Image.Image) -> Image.Image:
        if img.height == target_h:
            return img
        scale = target_h / img.height
        return img.resize(
            (max(1, round(img.width * scale)), target_h), Image.Resampling.LANCZOS
        )

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
                raise RuntimeError(
                    f"Missing embedded wave-source metadata in {raster}"
                ) from exc
        kind = "edited-raster"
    else:
        raise FileNotFoundError(f"No retained vector or edited raster named {stem!r}")

    OUTROOT.mkdir(parents=True, exist_ok=True)
    comparison = OUTROOT / f"{stem}.png"

    with tempfile.TemporaryDirectory(prefix="wave-figure-comparison-") as td:
        tmpdir = Path(td)
        original = tmpdir / "original.png"
        reconstruction = tmpdir / "reconstruction.png"
        render_source_crop(pdf_name, page, trim, original, dpi)
        if kind == "vector":
            render_tikz_png(stem, reconstruction, dpi)
        else:
            with Image.open(raster) as img:
                img.convert("RGB").save(reconstruction)
        side_by_side(original, reconstruction, comparison)

    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "figure", nargs="?", help="figure basename, e.g. ch05-p116-edge-wave-dispersion"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="regenerate comparisons for every retained TikZ figure",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="render resolution for audit evidence (default: 180)",
    )
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
        except Exception as exc:  # noqa: BLE001
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
