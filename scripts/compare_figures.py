#!/usr/bin/env python3
"""Maintain and audit same-stem source/reconstruction figure assets.

Vector source info is stored in each retained .tikz file as:
    % wave-source: pdf=ChapmanRizzoli5.pdf; page=21; trim=...bp ...bp ...bp ...bp

Source-PDF-only placements are represented by ``\\sourceart`` in the chapter
source and do not have vector siblings to compare.

Normal updates write the maintained vector SVG and original-source PNG beside
the TikZ source. ``--comparison`` additionally writes a temporary side-by-side
PNG under ``audit/figures/comparisons/``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from publication import (
    FIGURES,
    figure_asset_paths,
    maintained_figure_asset_errors,
    maintained_tikz_stems,
    render_source_crop,
    render_tikz_png,
    render_tikz_source_png,
    render_tikz_svg,
    tikz_source_masks,
    tikz_source_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
OUTROOT = ROOT / "audit" / "figures" / "comparisons"


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
    if not tikz.exists():
        raise FileNotFoundError(f"No retained vector named {stem!r}")
    metadata = tikz_source_metadata(stem)
    if metadata is None:
        raise RuntimeError(f"Missing wave-source comment in {tikz}")
    pdf_name, page, trim = metadata

    OUTROOT.mkdir(parents=True, exist_ok=True)
    comparison = OUTROOT / f"{stem}.png"

    with tempfile.TemporaryDirectory(prefix="wave-figure-comparison-") as td:
        tmpdir = Path(td)
        original = tmpdir / "original.png"
        reconstruction = tmpdir / "reconstruction.png"
        masks = tikz_source_masks(stem)
        render_source_crop(pdf_name, page, trim, original, dpi, masks=masks)
        render_tikz_png(stem, reconstruction, dpi)
        side_by_side(original, reconstruction, comparison)

    return comparison


def update_assets(stem: str) -> tuple[str, ...]:
    """Regenerate stale maintained siblings for one vector figure."""
    tikz, svg, png = figure_asset_paths(stem)
    if not tikz.is_file():
        raise FileNotFoundError(f"No retained vector named {stem!r}")

    errors = maintained_figure_asset_errors(stem)
    if not errors:
        return ()

    with tempfile.TemporaryDirectory(prefix="wave-figure-update-") as temporary:
        temporary_root = Path(temporary)
        render_tikz_svg(
            stem,
            temporary_root,
            temporary_root,
            asset_prefix="figures",
            force=True,
        )
        temporary_svg = temporary_root / "figures" / f"{stem}.svg"
        shutil.copy2(temporary_svg, svg)

        if tikz_source_metadata(stem) is not None:
            render_tikz_source_png(
                stem,
                temporary_root,
                asset_prefix="figures",
            )
            temporary_png = temporary_root / "figures" / f"{stem}.png"
            shutil.copy2(temporary_png, png)

    remaining = maintained_figure_asset_errors(stem)
    if remaining:
        raise RuntimeError("; ".join(remaining))
    changed = [path.name for path in (svg, png) if path.exists()]
    return tuple(changed)


def check_assets(stem: str) -> None:
    errors = maintained_figure_asset_errors(stem, verify_content=True)
    if errors:
        raise RuntimeError("; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "figure", nargs="?", help="figure basename, e.g. ch05-p116-edge-wave-dispersion"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="synchronize maintained assets for every retained TikZ figure",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="render resolution for audit evidence (default: 180)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if maintained vector assets are stale; do not write them",
    )
    parser.add_argument(
        "--comparison",
        action="store_true",
        help="also write a temporary raster comparison under audit/",
    )
    args = parser.parse_args()

    if args.all:
        stems = list(maintained_tikz_stems())
    else:
        stems = [args.figure]
    if args.check and args.comparison:
        parser.error("--comparison cannot be combined with --check")

    failures: list[tuple[str, Exception]] = []
    for stem in stems:
        try:
            if args.check:
                check_assets(stem)
                print(f"{stem}: maintained assets are fresh")
            else:
                changed = update_assets(stem)
                if changed:
                    print(f"{stem}: updated {', '.join(changed)}")
                else:
                    print(f"{stem}: maintained assets are up to date")
                if args.comparison:
                    path = compare(stem, args.dpi)
                    print(f"{stem}: comparison {path.relative_to(ROOT)}")
        except Exception as exc:  # noqa: BLE001
            failures.append((stem, exc))
            print(f"{stem}: ERROR: {exc}", file=sys.stderr)
            if not args.all:
                break
    if failures:
        print(f"{len(failures)} figure asset operation(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
