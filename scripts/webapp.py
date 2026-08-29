#!/usr/bin/env python3
"""Generate deterministic web-app resources for the HTML edition."""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import re
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from publication import BOOK_TITLE, LANGUAGE, ROOT, SRC, BuildInfo, current_build

ICON_SOURCE = SRC / "images" / "great-wave-met-dp130155.jpg"
ICON_CROP = (0.06, 0.00, 0.92, 0.86)
ICON_PROFILE: dict[str, float | int] = {
    "contrast": 1.06,
    "saturation": 1.06,
    "sharpness": 1.12,
    "unsharp_percent": 85,
    "unsharp_radius": 0.9,
    "unsharp_threshold": 3,
}
ICON_OUTPUTS = (
    ("icon-512.png", 512),
    ("icon-192.png", 192),
    ("apple-touch-icon.png", 180),
)
ICON_OUTPUT_DIR = ROOT / "release" / "assets" / "icons"
ICON_PREVIEW_PATH = ROOT / "build" / "icon-preview.html"
ICON_PREVIEW_SIZES = (180, 96, 64, 48, 32)
ICON_ASSET_PREFIX = "assets/icons"
APPLE_TOUCH_ICON_PATH = f"{ICON_ASSET_PREFIX}/apple-touch-icon.png"
WEB_MANIFEST_FILENAME = "app.webmanifest"
SERVICE_WORKER_FILENAME = "service-worker.js"
SERVICE_WORKER_TEMPLATE = SRC / "layout" / "wave-service-worker.js"
WEB_APP_NAME = BOOK_TITLE
WEB_APP_SHORT_NAME = "Wave Motions"
WEB_APP_RELATIVE_URL = "./"
MANIFEST_ICON_OUTPUTS = (
    ("icon-192.png", 192),
    ("icon-512.png", 512),
)
ARTWORK_ASSET_PATHS = (
    "assets/figures/great-wave-met-dp130155.jpg",
    "assets/figures/naruto-whirlpool-met-jp1198.jpg",
)
OFFLINE_OPTIONAL_ARTWORK_ASSETS = frozenset(ARTWORK_ASSET_PATHS)
FIGURE_ASSET_PREFIX = "assets/figures/"
RUNTIME_FIGURE_EXTENSIONS = frozenset({".png", ".svg"})
OFFLINE_CORE_READER_ASSETS = frozenset(
    {"assets/figures/salmon-hendershott-como-1980.jpg"}
)


def icon_crop_pixels(source_size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Return the exact pixel crop selected for the application icons."""
    source_width, source_height = source_size
    left = round(ICON_CROP[0] * source_width)
    top = round(ICON_CROP[1] * source_height)
    right = round(ICON_CROP[2] * source_width)
    bottom = round(ICON_CROP[3] * source_height)
    crop = (left, top, right, bottom)
    if not (0 <= left < right <= source_width and 0 <= top < bottom <= source_height):
        raise ValueError(f"invalid application icon crop for source size {source_size}")
    return crop


def _render_application_icon(master: Image.Image, size: int) -> Image.Image:
    """Render one RGB icon in the pinned crop, fit, and enhancement order."""
    if size <= 0:
        raise ValueError(f"application icon size must be positive, got {size}")

    cropped = master.crop(icon_crop_pixels(master.size))
    image = ImageOps.fit(
        cropped,
        (size, size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    image = ImageEnhance.Contrast(image).enhance(float(ICON_PROFILE["contrast"]))
    image = ImageEnhance.Color(image).enhance(float(ICON_PROFILE["saturation"]))
    image = ImageEnhance.Sharpness(image).enhance(float(ICON_PROFILE["sharpness"]))
    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=float(ICON_PROFILE["unsharp_radius"]),
            percent=int(ICON_PROFILE["unsharp_percent"]),
            threshold=int(ICON_PROFILE["unsharp_threshold"]),
        )
    )
    return image.convert("RGB")


def _save_application_icon(image: Image.Image, destination: Path | io.BytesIO) -> None:
    """Write a plain, metadata-free RGB PNG with pinned encoder settings."""
    if isinstance(destination, Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(
        destination,
        format="PNG",
        optimize=True,
        compress_level=9,
    )


def application_icon_paths(
    output_dir: Path = ICON_OUTPUT_DIR,
) -> tuple[Path, ...]:
    """Return canonical application-icon paths below an output directory."""
    output_dir = Path(output_dir)
    return tuple(output_dir / name for name, _size in ICON_OUTPUTS)


def generate_application_icons(
    output_dir: Path = ICON_OUTPUT_DIR,
    source_path: Path = ICON_SOURCE,
    *,
    announce: bool = True,
) -> tuple[Path, ...]:
    """Generate all canonical application icons from the maintained artwork."""
    output_dir = Path(output_dir)
    source_path = Path(source_path)
    with Image.open(source_path) as source:
        master = source.convert("RGB")
    crop = icon_crop_pixels(master.size)
    if announce:
        print(
            f"Application icon source {source_path}: "
            f"{master.width}x{master.height}; crop={crop} "
            f"({crop[2] - crop[0]}x{crop[3] - crop[1]})"
        )

    paths: list[Path] = []
    for name, size in ICON_OUTPUTS:
        destination = output_dir / name
        _save_application_icon(_render_application_icon(master, size), destination)
        paths.append(destination)
        if announce:
            print(f"Application icon {name}: {size}x{size} pixels")
    return tuple(paths)


def application_icon_errors(output_dir: Path = ICON_OUTPUT_DIR) -> list[str]:
    """Return structural errors for generated application icons."""
    output_dir = Path(output_dir)
    errors: list[str] = []
    expected_names = {name for name, _size in ICON_OUTPUTS}
    if output_dir.is_dir():
        actual_names = {path.name for path in output_dir.iterdir() if path.is_file()}
        unexpected_names = sorted(actual_names - expected_names)
        if unexpected_names:
            errors.append(
                f"{output_dir} contains unsupported application icon outputs: "
                + ", ".join(unexpected_names)
            )
    for path, (_name, size) in zip(
        application_icon_paths(output_dir), ICON_OUTPUTS, strict=True
    ):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"{path} is missing or empty")
            continue
        try:
            with Image.open(path) as image:
                if image.format != "PNG":
                    errors.append(f"{path} is {image.format or 'not'} a PNG")
                image.load()
                if image.size != (size, size):
                    errors.append(
                        f"{path} is {image.width}x{image.height}; "
                        f"expected {size}x{size}"
                    )
                if image.mode != "RGB":
                    errors.append(f"{path} uses {image.mode} mode; expected RGB")
                if image.info:
                    errors.append(
                        f"{path} contains unexpected PNG metadata: "
                        + ", ".join(sorted(image.info))
                    )
        except (OSError, ValueError) as exc:
            errors.append(f"cannot read application icon {path}: {exc}")
    return errors


def application_icon_check_errors(output_dir: Path = ICON_OUTPUT_DIR) -> list[str]:
    """Return structural or decoded-pixel freshness errors for the icon set."""
    output_dir = Path(output_dir)
    errors = application_icon_errors(output_dir)
    if errors:
        return errors

    with tempfile.TemporaryDirectory(prefix="wave-application-icons-") as temporary:
        expected_paths = generate_application_icons(
            Path(temporary),
            announce=False,
        )
        for actual_path, expected_path in zip(
            application_icon_paths(output_dir), expected_paths, strict=True
        ):
            with (
                Image.open(actual_path) as actual,
                Image.open(expected_path) as expected,
            ):
                if actual.size != expected.size or actual.mode != expected.mode:
                    errors.append(
                        f"{actual_path} dimensions or mode differ from fresh output"
                    )
                elif actual.tobytes() != expected.tobytes():
                    errors.append(f"{actual_path} pixels differ from fresh output")
    return errors


def validate_application_icons(output_dir: Path = ICON_OUTPUT_DIR) -> None:
    """Raise when a generated icon set is missing or structurally invalid."""
    errors = application_icon_errors(output_dir)
    if errors:
        raise ValueError(
            "application icon validation failed:\n- " + "\n- ".join(errors)
        )


def _application_icon_data_uri(image: Image.Image) -> str:
    payload = io.BytesIO()
    _save_application_icon(image, payload)
    return "data:image/png;base64," + base64.b64encode(payload.getvalue()).decode(
        "ascii"
    )


def write_application_icon_preview(
    output_path: Path = ICON_PREVIEW_PATH,
    source_path: Path = ICON_SOURCE,
) -> Path:
    """Write a self-contained preview of the pinned icon at launcher sizes."""
    output_path = Path(output_path)
    source_path = Path(source_path)
    with Image.open(source_path) as source:
        master = source.convert("RGB")

    preview_images = {
        size: _application_icon_data_uri(_render_application_icon(master, size))
        for size in ICON_PREVIEW_SIZES
    }
    profile = ", ".join(f"{key}={value}" for key, value in ICON_PROFILE.items())
    try:
        source_label = str(source_path.relative_to(ROOT))
    except ValueError:
        source_label = str(source_path)
    source_label = html.escape(source_label)
    crop_label = html.escape(str(ICON_CROP))
    profile_label = html.escape(profile)
    variants = (
        ("square", "Square"),
        ("rounded", "Rounded square"),
        ("circle", "Circle"),
        ("squircle", "Squircle"),
        ("safe", "Maskable safe-zone overlay"),
    )

    sections: list[str] = []
    for size in ICON_PREVIEW_SIZES:
        samples = []
        for variant, label in variants:
            samples.append(
                f'''<figure class="sample">
  <div class="icon-frame icon-frame--{variant}" style="--size: {size}px">
    <img src="{preview_images[size]}" alt="{label} preview at {size} pixels">
  </div>
  <figcaption>{label}</figcaption>
</figure>'''
            )
        sections.append(
            f'<section class="size-group"><h2>{size} × {size}</h2>'
            f'<div class="samples">{"".join(samples)}</div></section>'
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wave Motions application icon preview</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 72rem; padding: 0 1rem; }}
    h1 {{ margin-bottom: .4rem; }}
    .details {{ line-height: 1.5; }}
    .size-group {{ border-top: 1px solid #8888; margin-top: 2rem; padding-top: 1rem; }}
    .samples {{ align-items: end; display: flex; flex-wrap: wrap; gap: 1.5rem; }}
    .sample {{ margin: 0; text-align: center; }}
    .icon-frame {{
      aspect-ratio: 1;
      max-width: 100%;
      position: relative;
      width: var(--size);
    }}
    .icon-frame img {{ display: block; height: 100%; width: 100%; }}
    .icon-frame--rounded img {{ border-radius: 20%; }}
    .icon-frame--circle img {{ border-radius: 50%; }}
    .icon-frame--squircle img {{ border-radius: 28%; }}
    .icon-frame--safe::after {{
      border: 2px dashed #fff;
      border-radius: 50%;
      box-sizing: border-box;
      box-shadow: 0 0 0 1px #000;
      content: "";
      inset: 10%;
      pointer-events: none;
      position: absolute;
    }}
    figcaption {{ font-size: .85rem; margin-top: .45rem; max-width: 12rem; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Final application icon preview</h1>
  <p class="details">Source: <code>{source_label}</code><br>
  Crop: <code>{crop_label}</code><br>
  Profile: <code>crisp_vivid</code> ({profile_label})<br>
  Every preview uses the same composition. The dashed circle is the intended
  maskable safe zone: radius 40% of the icon side, with a 10% inset.</p>
  {"".join(sections)}
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


def prepare_application_icons(assets_root: Path) -> tuple[Path, ...]:
    """Generate application icons below a publication root's assets folder."""
    output_dir = Path(assets_root) / "assets" / "icons"
    paths = generate_application_icons(output_dir)
    validate_application_icons(output_dir)
    return paths


def reader_palette() -> tuple[str, str]:
    """Return the normal reader background and heading colors from its CSS."""
    stylesheet = SRC / "layout" / "wave-html.css"
    text = stylesheet.read_text()

    def color(variable: str) -> str:
        match = re.search(
            rf"(?m)^\s*{re.escape(variable)}\s*:\s*(#[0-9A-Fa-f]{{6}})\s*;",
            text,
        )
        if match is None:
            raise ValueError(f"reader color {variable} is missing from {stylesheet}")
        return match.group(1)

    return color("--wave-bg"), color("--wave-heading")


def web_app_manifest() -> dict[str, object]:
    """Return the deterministic manifest for the single HTML edition."""
    background_color, theme_color = reader_palette()
    return {
        "id": WEB_APP_RELATIVE_URL,
        "name": WEB_APP_NAME,
        "short_name": WEB_APP_SHORT_NAME,
        "start_url": WEB_APP_RELATIVE_URL,
        "scope": WEB_APP_RELATIVE_URL,
        "display": "standalone",
        "icons": [
            {
                "src": f"{ICON_ASSET_PREFIX}/{name}",
                "sizes": f"{size}x{size}",
                "type": "image/png",
                "purpose": "any maskable",
            }
            for name, size in MANIFEST_ICON_OUTPUTS
        ],
        "lang": LANGUAGE,
        "theme_color": theme_color,
        "background_color": background_color,
    }


def web_app_manifest_text() -> str:
    """Serialize the web-app manifest with stable formatting."""
    return json.dumps(web_app_manifest(), ensure_ascii=False, indent=2) + "\n"


def write_web_app_manifest(root: Path) -> Path:
    """Write the manifest at the root of one generated HTML publication."""
    path = Path(root) / WEB_MANIFEST_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(web_app_manifest_text(), encoding="utf-8")
    return path


def _reader_resource_candidates(root: Path) -> tuple[str, ...]:
    """Return local reader files, excluding downloads and bookkeeping files."""
    root = Path(root).resolve()
    candidates = list(root.glob("*.html"))
    candidates.append(root / WEB_MANIFEST_FILENAME)
    assets = root / "assets"
    if assets.is_dir():
        candidates.extend(assets.rglob("*"))

    excluded_names = {
        SERVICE_WORKER_FILENAME,
        "SHA256SUMS",
        "wave-motions-html.zip",
    }
    excluded_suffixes = {".epub", ".pdf", ".zip"}
    resources: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded_names or path.suffix.lower() in excluded_suffixes:
            continue
        resources.append(relative)
    return tuple(sorted(set(resources)))


def all_reader_resources(root: Path) -> tuple[str, ...]:
    """Return the broad local resource set used for precache savings reporting."""
    return _reader_resource_candidates(root)


def is_runtime_figure_asset(relative: str) -> bool:
    """Return whether a publication-relative path is a runtime-cached figure."""
    return (
        relative.startswith(FIGURE_ASSET_PREFIX)
        and Path(relative).suffix.lower() in RUNTIME_FIGURE_EXTENSIONS
    )


def offline_reader_resources(root: Path) -> tuple[str, ...]:
    """Return the sorted shell and text-reading files needed offline.

    The complete HTML reader, local runtime assets, and the small front-matter
    photograph are precached. Scientific PNG/SVG figures and large optional
    artwork are fetched and cached only after a successful runtime request.
    Download artifacts remain outside the offline policy.
    """
    return tuple(
        relative
        for relative in _reader_resource_candidates(root)
        if relative not in OFFLINE_OPTIONAL_ARTWORK_ASSETS
        and (
            not relative.startswith(FIGURE_ASSET_PREFIX)
            or relative in OFFLINE_CORE_READER_ASSETS
        )
    )


def offline_reader_resource_stats(
    root: Path, resources: Iterable[str] | None = None
) -> tuple[int, tuple[tuple[str, int], ...]]:
    """Return total bytes and descending file sizes for an offline resource set."""
    root = Path(root)
    selected = (
        tuple(resources) if resources is not None else offline_reader_resources(root)
    )
    sizes = tuple(
        sorted(
            ((name, (root / name).stat().st_size) for name in selected),
            key=lambda item: (-item[1], item[0]),
        )
    )
    return sum(size for _name, size in sizes), sizes


def service_worker_text(root: Path, info: BuildInfo | None = None) -> str:
    """Render the maintained service-worker source for one publication root."""
    info = info or current_build()
    replacements = {
        "__WAVE_CACHE_NAME__": json.dumps(f"wave-motions-{info.short_sha}"),
        "__WAVE_PRECACHE_URLS__": json.dumps(
            list(offline_reader_resources(root)), ensure_ascii=False, indent=2
        ),
    }
    text = SERVICE_WORKER_TEMPLATE.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        if text.count(marker) != 1:
            raise ValueError(
                f"service-worker template must contain exactly one {marker} marker"
            )
        text = text.replace(marker, value)
    if "__WAVE_" in text:
        raise ValueError("service-worker template contains an unknown generated marker")
    return text


def write_service_worker(root: Path, info: BuildInfo | None = None) -> Path:
    """Write the generated service worker at the HTML publication root."""
    path = Path(root) / SERVICE_WORKER_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(service_worker_text(root, info), encoding="utf-8")
    return path


def _icons_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="webapp.py icons")
    parser.add_argument("--output", type=Path, default=ICON_OUTPUT_DIR)
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--check",
        action="store_true",
        help="compare generated icons with fresh decoded pixels without writing",
    )
    action.add_argument(
        "--preview",
        nargs="?",
        const=ICON_PREVIEW_PATH,
        type=Path,
        metavar="PATH",
        help="write a self-contained pinned-design preview (default: build/icon-preview.html)",
    )
    args = parser.parse_args(argv)
    if args.preview is not None:
        path = write_application_icon_preview(args.preview)
        print(f"Application icon preview written: {path}")
        return 0
    if args.check:
        errors = application_icon_check_errors(args.output)
        if errors:
            print(
                "application icon check failed:\n- " + "\n- ".join(errors),
                file=sys.stderr,
            )
            return 1
        print(f"Application icons are current: {args.output}")
        return 0
    generate_application_icons(args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Web-app generation utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("icons", help="generate, check, or preview application icons")
    args, remainder = parser.parse_known_args(argv)
    if args.command == "icons":
        return _icons_cli(remainder)
    raise SystemExit(f"unsupported web-app command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
