from pathlib import Path

import pytest
from PIL import Image, ImageChops
from PIL.PngImagePlugin import PngInfo

import build_html
import publication
from publication import (
    BuildInfo,
    _balanced_command_args,
    _crop_source_image,
    _mask_box_pixels,
    _validate_mask_boxes,
    collect_equation_displays,
    equation_asset_paths,
    equation_ledger_text,
    equation_markdown_math,
    expected_source_png_metadata,
    figure_asset_paths,
    maintained_figure_asset_errors,
    parse_mask,
    parse_trim,
    prepare_assets,
    prepare_original_assets,
    prepare_vector_assets,
    reader_punctuation,
    section_slug,
    source_crop,
    switchable_figure_stems,
    tex_plain,
    tikz_source_masks,
    tikz_source_metadata,
    transform_tex,
    validate_maintained_figure_assets,
)


def _write_equation_test_sources(root: Path) -> Path:
    source = root / "src"
    source.mkdir()
    (source / "chapter1.tex").write_text(
        r"""% Source printed page 2 / physical page 1
\begin{waveequation}
	x = 1
\end{waveequation}
\begin{wavealign}
	a &= b \\
	c &= d
\end{wavealign}
% Source printed page 3 / source physical page 2
\[
	y = 2
\]
"""
    )
    (source / "chapter2.tex").write_text(
        r"""% Source printed page 4 / physical page 1
\begin{equation*}
	z = 3
\end{equation*}
"""
    )
    for chapter in range(3, 7):
        (source / f"chapter{chapter}.tex").write_text(
            f"% Source printed page {chapter + 2} / physical page 1\n"
        )
    return source


def test_equation_extraction_order_wrappers_and_exact_source(tmp_path: Path) -> None:
    source = _write_equation_test_sources(tmp_path)
    displays = collect_equation_displays(source)

    assert [display.stem for display in displays] == [
        "ch01-p002-e01",
        "ch01-p002-e02",
        "ch01-p003-e01",
        "ch02-p004-e01",
    ]
    assert displays[0].source == "\\begin{waveequation}\n\tx = 1\n\\end{waveequation}"
    assert displays[0].line == 2
    assert equation_markdown_math(displays[0]) == "$$\n\tx = 1\n$$"
    assert equation_markdown_math(displays[1]) == (
        "$$\n\\begin{aligned}\n\ta &= b \\\\\n\tc &= d\n\\end{aligned}\n$$"
    )
    assert equation_markdown_math(displays[2]) == "$$\n\ty = 2\n$$"


def test_equation_asset_paths_are_derived_from_the_stem() -> None:
    paths = equation_asset_paths("ch01-p002-e01")
    assert [path.name for path in paths] == [
        "ch01-p002-e01-source.png",
        "ch01-p002-e01-mathjax.png",
        "ch01-p002-e01-mathml.png",
    ]
    with pytest.raises(ValueError):
        equation_asset_paths("not-an-equation")


def test_equation_ledger_is_stable_and_contains_no_machine_data(tmp_path: Path) -> None:
    source = _write_equation_test_sources(tmp_path)
    first, count = equation_ledger_text(source)
    second, second_count = equation_ledger_text(source)

    assert count == second_count == 4
    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert "<!-- Generated from src/chapter1.tex through src/chapter6.tex." in first
    assert "```tex\n\\begin{waveequation}\n\tx = 1\n\\end{waveequation}\n```" in first
    assert "equations/ch01-p002-e01-source.png" in first
    assert all(
        forbidden not in first
        for forbidden in ("2026-", "/home/", "tmp/", "Chromium", "git SHA")
    )


def test_equation_cli_check_passes_and_fails_after_source_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_equation_test_sources(tmp_path)
    monkeypatch.setattr(publication, "SRC", source)
    publication.write_equation_ledger()

    assert publication._equations_cli(["--check"]) == 0
    assert "current" in capsys.readouterr().out

    chapter = source / "chapter1.tex"
    chapter.write_text(chapter.read_text().replace("x = 1", "x = 9"))
    assert publication._equations_cli(["--check"]) == 1
    assert "stale" in capsys.readouterr().err


def test_parse_trim_accepts_four_bp_values() -> None:
    assert parse_trim("1bp 2.5bp -3bp 4.25bp") == (1.0, 2.5, -3.0, 4.25)


def test_parse_trim_rejects_malformed_values() -> None:
    for trim in ("1bp 2bp 3bp", "1bp 2bp 3bp 4px", "1bp 2bp 3bp 4bp 5bp"):
        with pytest.raises(ValueError, match="expected four bp trim values"):
            parse_trim(trim)


def test_parse_mask_accepts_bp_and_sourceart_slash_forms() -> None:
    assert parse_mask("1bp 2.5bp -3bp 4.25bp") == (1.0, 2.5, -3.0, 4.25)
    assert parse_mask("1/2.5/-3/4.25") == (1.0, 2.5, -3.0, 4.25)


def test_parse_mask_rejects_wrong_count_and_units() -> None:
    for mask in ("1bp 2bp 3bp", "1px 2px 3px 4px", "1/2/3/4/5"):
        with pytest.raises(ValueError, match="expected four PDF mask coordinates"):
            parse_mask(mask)


def test_figure_asset_paths_use_the_same_stem() -> None:
    tikz, svg, png = figure_asset_paths("ch01-p004-phase-speed")

    assert tikz.name == "ch01-p004-phase-speed.tikz"
    assert svg.name == "ch01-p004-phase-speed.svg"
    assert png.name == "ch01-p004-phase-speed.png"
    with pytest.raises(ValueError):
        figure_asset_paths("nested/figure")


def _write_valid_figure_assets(
    figures: Path,
    source_dir: Path,
    *,
    trim: str = "1bp 2bp 3bp 4bp",
    masks: str = "",
) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    tikz = figures / "sample.tikz"
    tikz.write_text(
        f"% wave-source: pdf=scan.pdf; page=3; trim={trim}\n"
        + (masks + "\n" if masks else "")
    )
    publication.file_sha256.cache_clear()
    expected = expected_source_png_metadata("sample")
    assert expected is not None
    (figures / "sample.svg").write_text(
        f"<svg><!-- wave-generated-sha256: "
        f"{publication._tikz_digest('sample')} --></svg>"
    )
    image = Image.new("RGB", (2, 2), "white")
    info = PngInfo()
    for key, value in expected.items():
        info.add_text(key, value)
    image.save(figures / "sample.png", pnginfo=info)


def test_source_png_metadata_records_source_identity_and_render_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "scan.pdf"
    source.write_bytes(b"scan")
    figures = tmp_path / "figures"
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "FIGURES", figures)
    _write_valid_figure_assets(figures, source_dir)

    metadata = expected_source_png_metadata("sample")
    assert metadata is not None
    with Image.open(figures / "sample.png") as image:
        assert image.info == metadata


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("trim", "wave-source-trim"),
        ("masks", "wave-source-masks"),
        ("dpi", "wave-source-dpi"),
    ],
)
def test_source_png_is_stale_when_crop_inputs_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
    expected: str,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "scan.pdf").write_bytes(b"scan")
    figures = tmp_path / "figures"
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "FIGURES", figures)
    _write_valid_figure_assets(figures, source_dir)

    tikz = figures / "sample.tikz"
    text = tikz.read_text()
    if change == "trim":
        text = text.replace("1bp 2bp 3bp 4bp", "2bp 2bp 3bp 4bp")
    elif change == "masks":
        text += (
            "% wave-source-mask: pdf=scan.pdf; page=3; "
            "rect=10bp 10bp 20bp 20bp; origin=lower-left\n"
        )
    else:
        monkeypatch.setattr(publication, "SOURCE_RENDER_DPI", 171)
    tikz.write_text(text)
    publication.file_sha256.cache_clear()

    errors = maintained_figure_asset_errors("sample")

    assert any(expected in error for error in errors)


def test_source_png_is_stale_when_source_pdf_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "scan.pdf"
    source.write_bytes(b"scan-a")
    figures = tmp_path / "figures"
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "FIGURES", figures)
    _write_valid_figure_assets(figures, source_dir)

    source.write_bytes(b"scan-b")
    publication.file_sha256.cache_clear()

    errors = maintained_figure_asset_errors("sample")

    assert any("wave-source-pdf-sha256" in error for error in errors)


def test_svg_is_stale_when_tikz_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "scan.pdf").write_bytes(b"scan")
    figures = tmp_path / "figures"
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "FIGURES", figures)
    _write_valid_figure_assets(figures, source_dir)
    (figures / "sample.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3; trim=1bp 2bp 3bp 4bp\n% changed\n"
    )

    errors = maintained_figure_asset_errors("sample")

    assert any("sample.svg has digest" in error for error in errors)


def test_source_only_asset_does_not_require_vector_siblings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.new("RGB", (2, 2), "white").save(figures / "source-only.png")
    monkeypatch.setattr(publication, "FIGURES", figures)

    validate_maintained_figure_assets()


def test_tikz_source_masks_accepts_multiple_matching_masks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publication, "FIGURES", tmp_path)
    (tmp_path / "multiple.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3; trim=1bp 2bp 3bp 4bp\n"
        "% wave-source-mask: pdf=scan.pdf; page=3; "
        "rect=10bp 20bp 30bp 40bp; origin=lower-left\n"
        "% wave-source-mask: pdf=scan.pdf; page=3; "
        "rect=40bp 50bp 60bp 70bp; origin=lower-left\n"
        "% wave-source-mask: pdf=other.pdf; page=3; "
        "rect=1bp 2bp 3bp 4bp; origin=lower-left\n"
    )

    assert tikz_source_masks("multiple") == (
        (10.0, 20.0, 30.0, 40.0),
        (40.0, 50.0, 60.0, 70.0),
    )


@pytest.mark.parametrize(
    "mask",
    [
        (40.0, 20.0, 20.0, 30.0),
        (-1.0, 20.0, 30.0, 40.0),
        (0.0, 80.0, 5.0, 90.0),
    ],
)
def test_validate_mask_boxes_rejects_reversed_outside_and_disjoint_masks(
    mask: tuple[float, float, float, float],
) -> None:
    with pytest.raises(ValueError):
        _validate_mask_boxes((mask,), 100.0, 100.0, "10bp 10bp 10bp 10bp")


def test_mask_page_coordinates_convert_from_lower_left() -> None:
    assert _mask_box_pixels((10.0, 20.0, 30.0, 40.0), 100.0, 200.0, 1000, 2000) == (
        100,
        1600,
        300,
        1800,
    )


def test_masks_apply_before_crop_and_keep_absolute_page_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publication, "page_size_points", lambda *_: (100.0, 100.0))
    source = tmp_path / "page.png"
    Image.new("RGB", (100, 100), "white").save(source)
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.putpixel((50, 50), (0, 0, 0))
        image.putpixel((80, 20), (0, 0, 0))
        image.putpixel((80, 50), (0, 0, 0))
        image.save(source)

    masks = ((40.0, 40.0, 60.0, 60.0), (70.0, 70.0, 90.0, 90.0))
    full = tmp_path / "full.png"
    shifted = tmp_path / "shifted.png"
    _crop_source_image(
        tmp_path / "scan.pdf",
        3,
        "0bp 0bp 0bp 0bp",
        source,
        full,
        masks=masks,
    )
    _crop_source_image(
        tmp_path / "scan.pdf",
        3,
        "10bp 0bp 0bp 0bp",
        source,
        shifted,
        masks=masks,
    )

    with Image.open(full) as image:
        assert image.getpixel((50, 50)) == (255, 255, 255)
        assert image.getpixel((80, 20)) == (255, 255, 255)
        assert image.getpixel((80, 50)) == (0, 0, 0)
    with Image.open(shifted) as image:
        assert image.getpixel((40, 50)) == (255, 255, 255)
        assert image.getpixel((70, 20)) == (255, 255, 255)
        assert image.getpixel((70, 50)) == (0, 0, 0)


def test_no_mask_crop_remains_the_normal_pixel_crop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publication, "page_size_points", lambda *_: (100.0, 100.0))
    source = tmp_path / "page.png"
    original = Image.new("RGB", (100, 100), "white")
    original.putpixel((50, 50), (0, 0, 0))
    original.save(source)
    destination = tmp_path / "crop.png"

    _crop_source_image(
        tmp_path / "scan.pdf",
        3,
        "10bp 20bp 30bp 40bp",
        source,
        destination,
    )

    expected = original.crop((10, 40, 70, 80))
    with Image.open(destination) as actual:
        assert ImageChops.difference(actual, expected).getbbox() is None


def test_source_crop_identity_changes_with_source_and_render_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "scan.pdf"
    source.write_bytes(b"source-a")
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "SOURCE_PAGE_CACHE", tmp_path / "cache")

    def render(
        _pdf: Path,
        _page: int,
        _dpi: int,
        prefix: Path,
        *,
        quiet: bool = True,
    ) -> Path:
        rendered = prefix.with_suffix(".png")
        rendered.parent.mkdir(parents=True, exist_ok=True)
        rendered.write_bytes(b"rendered")
        return rendered

    def crop(
        _pdf: Path,
        _page: int,
        _trim: str,
        _image_path: Path,
        destination: Path,
        *,
        angle: float,
        optimize: bool,
        metadata: dict[str, str],
    ) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            f"{angle}:{optimize}:{metadata['wave-source-dpi']}".encode()
        )

    monkeypatch.setattr(publication, "_render_pdf_page", render)
    monkeypatch.setattr(publication, "_crop_source_image", crop)
    publication.file_sha256.cache_clear()

    assets = tmp_path / "assets"
    base = source_crop("scan.pdf", 3, "1bp 2bp 3bp 4bp", assets)
    assert source_crop("scan.pdf", 3, "1bp 2bp 3bp 4bp", assets) == base
    assert source_crop("scan.pdf", 3, "2bp 2bp 3bp 4bp", assets) != base
    assert source_crop("scan.pdf", 3, "1bp 2bp 3bp 4bp", assets, dpi=171) != base
    assert source_crop("scan.pdf", 3, "1bp 2bp 3bp 4bp", assets, angle=1) != base

    paired = source_crop(
        "scan.pdf",
        3,
        "1bp 2bp 3bp 4bp",
        assets,
        asset_name="figure.png",
    )
    assert paired == "assets/figures/figure.png"
    assert (assets / "assets" / "figures" / "figure.png").is_file()

    source.write_bytes(b"source-b")
    publication.file_sha256.cache_clear()
    assert source_crop("scan.pdf", 3, "1bp 2bp 3bp 4bp", assets) != base


def test_transform_tex_removes_pdf_only_content_and_source_markers(
    tmp_path: Path,
) -> None:
    source = r"""
\begin{wavepdfonly}pdf-only text\end{wavepdfonly}
\begin{wavewebonly}web text\end{wavewebonly}
\nopagecolor\sourcepagebreak\sourcesetpage{11}
\begin{waveequation}x = 1\end{waveequation}
\wavefiguremark
"""
    transformed = transform_tex(source, None, tmp_path)

    assert "pdf-only text" not in transformed
    assert "web text" in transformed
    assert "sourcepagebreak" not in transformed
    assert "sourcesetpage" not in transformed
    assert r"\nopagecolor" not in transformed
    assert r"\[x = 1\]" in transformed
    assert r"\wavefiguremark" not in transformed


def test_transform_tex_numbers_editorial_equations_and_alignments(
    tmp_path: Path,
) -> None:
    marks = "\n".join([r"\wavefiguremark"] * 10)
    source = (
        r"\begin{waveequation}a=b\end{waveequation}"
        r"\begin{wavealign}a&=b\end{wavealign}" + "\n" + marks
    )
    transformed = transform_tex(source, 2, tmp_path)

    assert r"\textup{(2.1)}" in transformed
    assert r"\textup{(2.2)}" in transformed
    assert r"\begin{aligned}a&=b\end{aligned}" in transformed
    assert transformed.count("Figure 2.") == 10


def test_transform_tex_preserves_native_equation_numbering(tmp_path: Path) -> None:
    marks = "\n".join([r"\wavefiguremark"] * 10)
    source = r"\begin{equation}x=1\tag{2.1}\end{equation}" + "\n" + marks
    transformed = transform_tex(source, 2, tmp_path)

    assert r"\textup{(2.1)}" in transformed
    assert r"\tag{2.1}" not in transformed


def test_transform_tex_rejects_wrong_native_equation_chapter(tmp_path: Path) -> None:
    source = r"\begin{equation}x=1\tag{1.1}\end{equation}"
    with pytest.raises(SystemExit, match="wrong chapter"):
        transform_tex(source, 2, tmp_path)


def test_transform_tex_rejects_mixed_equation_numbering(tmp_path: Path) -> None:
    marks = "\n".join([r"\wavefiguremark"] * 10)
    source = (
        r"\begin{equation}x=1\tag{2.1}\end{equation}"
        r"\begin{waveequation}y=2\end{waveequation}" + "\n" + marks
    )
    with pytest.raises(SystemExit, match="mixed native"):
        transform_tex(source, 2, tmp_path)


def test_transform_tex_rewrites_vector_source_and_local_figure_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        publication,
        "source_crop",
        lambda *args, **kwargs: "assets/figures/source.png",
    )
    marks = "\n".join([r"\wavefiguremark"] * 5)
    source = (
        r"\wavevectorart{vector}"
        r"\input{figures/inline.tikz}"
        r"\includegraphics{images/photo.png}"
        r"\sourceart{scan.pdf}{2}{1bp 2bp 3bp 4bp}" + "\n" + marks
    )
    transformed = transform_tex(source, 1, tmp_path)

    assert r"\includegraphics{assets/figures/vector.svg}" in transformed
    assert r"\includegraphics{assets/figures/inline.svg}" in transformed
    assert r"\includegraphics{assets/figures/photo.png}" in transformed
    assert r"\includegraphics{assets/figures/source.png}" in transformed
    assert transformed.count("Figure 1.") == 7


def test_tikz_source_metadata_accepts_valid_and_rejects_malformed_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publication, "FIGURES", tmp_path)
    (tmp_path / "valid.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3; trim=1bp 2bp 3bp 4bp\n"
    )
    (tmp_path / "missing.tikz").write_text("% a vector without a source crop\n")
    (tmp_path / "malformed.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3; trim=1bp 2bp 3bp\n"
    )
    (tmp_path / "malformed-marker.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3\n"
    )

    assert tikz_source_metadata("valid") == ("scan.pdf", 3, "1bp 2bp 3bp 4bp")
    assert tikz_source_metadata("missing") is None
    with pytest.raises(ValueError, match="expected four bp trim values"):
        tikz_source_metadata("malformed")
    with pytest.raises(ValueError, match="malformed wave-source comment"):
        tikz_source_metadata("malformed-marker")


def test_prepare_original_assets_copies_only_source_backed_tikz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "scan.pdf").write_bytes(b"scan")
    figures = tmp_path / "figures"
    figures.mkdir()
    (figures / "vector.tikz").write_text(
        "% wave-source: pdf=scan.pdf; page=3; trim=1bp 2bp 3bp 4bp\n"
    )
    (figures / "digital.tikz").write_text("% digital-only\n")
    monkeypatch.setattr(publication, "FIGURES", figures)
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    (figures / "vector.svg").write_text(
        f"<svg><!-- wave-generated-sha256: "
        f"{publication._tikz_digest('vector')} --></svg>"
    )
    expected = expected_source_png_metadata("vector")
    assert expected is not None
    image = Image.new("RGB", (2, 2), "white")
    info = PngInfo()
    for key, value in expected.items():
        info.add_text(key, value)
    image.save(figures / "vector.png", pnginfo=info)

    monkeypatch.setattr(publication, "referenced_tikz", lambda: ["vector", "digital"])
    publication.file_sha256.cache_clear()

    prepare_original_assets(tmp_path / "assets")

    assert (tmp_path / "assets" / "assets" / "figures" / "vector.png").is_file()
    assert not (tmp_path / "assets" / "assets" / "figures" / "digital.png").exists()


def test_publication_asset_preparation_copies_maintained_vector_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "scan.pdf").write_bytes(b"scan")
    figures = tmp_path / "figures"
    monkeypatch.setattr(publication, "FIGURES", figures)
    monkeypatch.setattr(publication, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(publication, "referenced_tikz", lambda: ["sample"])
    _write_valid_figure_assets(figures, source_dir)

    output = tmp_path / "release"
    prepare_vector_assets(output, tmp_path / "work")
    prepare_original_assets(output)

    assert (output / "assets" / "figures" / "sample.svg").is_file()
    assert (output / "assets" / "figures" / "sample.png").is_file()


def test_prepare_assets_only_generates_originals_when_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []
    monkeypatch.setattr(publication, "prepare_vector_assets", lambda *_: None)
    monkeypatch.setattr(publication, "copy_raster_assets", lambda *_: None)
    monkeypatch.setattr(publication, "copy_cc_assets", lambda *_: None)
    monkeypatch.setattr(
        publication,
        "prepare_original_assets",
        lambda assets_root: calls.append(assets_root),
    )

    prepare_assets(tmp_path, tmp_path)
    prepare_assets(tmp_path, tmp_path, include_originals=True)

    assert calls == [tmp_path]


def test_switchable_stems_require_same_directory_svg_and_png(tmp_path: Path) -> None:
    figure_dir = tmp_path / "assets" / "figures"
    figure_dir.mkdir(parents=True)
    (figure_dir / "paired.svg").write_text("svg")
    (figure_dir / "paired.png").write_bytes(b"png")
    (figure_dir / "svg-only.svg").write_text("svg")
    (figure_dir / "png-only.png").write_bytes(b"png")

    assert switchable_figure_stems(tmp_path, ["paired", "svg-only", "png-only"]) == (
        "paired",
    )


def test_install_figure_markup_adds_one_switchable_image_and_local_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = tmp_path / "chapter1.html"
    page.write_text(
        '<div class="center"><p><img src="assets/figures/paired.svg" '
        'alt="existing alternative" /></p><div class="center"><p>'
        '<span class="sans-serif">Figure 1.1</span></p></div></div>'
    )
    monkeypatch.setattr(
        build_html, "page_switchable_figure_stems", lambda *_: ("paired",)
    )

    build_html.install_figure_markup(page, tmp_path)
    output = page.read_text()

    assert output.count('<figure class="wave-figure wave-figure-switchable"') == 1
    assert output.count("<img") == 1
    assert 'src="assets/figures/paired.svg"' in output
    assert 'data-vector-src="assets/figures/paired.svg"' in output
    assert 'data-original-src="assets/figures/paired.png"' in output
    assert 'aria-label="Show original source figure"' in output
    assert ">Original</button>" in output


def test_install_figure_markup_leaves_source_art_without_switch_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    page = tmp_path / "chapter1.html"
    page.write_text(
        '<p><img src="assets/figures/source-art.png" alt="source art" /></p>'
        '<div class="center"><p><span class="sans-serif">Figure 1.1</span>'
        "</p></div>"
    )
    monkeypatch.setattr(build_html, "page_switchable_figure_stems", lambda *_: ())

    build_html.install_figure_markup(page, tmp_path)
    output = page.read_text()

    assert '<figure class="wave-figure">' in output
    assert "figure-view-toggle" not in output
    assert 'src="assets/figures/source-art.png"' in output


def test_balanced_command_args_handles_nested_braces() -> None:
    assert _balanced_command_args(r"\section{A {nested} title}", "section") == [
        "A {nested} title"
    ]


def test_balanced_command_args_rejects_unbalanced_braces() -> None:
    with pytest.raises(ValueError, match="unbalanced"):
        _balanced_command_args(r"\section{unfinished", "section")


def test_reader_text_normalization_and_section_slugs() -> None:
    assert reader_punctuation("``Wave'' motion") == "“Wave” motion"
    assert tex_plain(r"Surface---gravity \ell waves") == "Surface—gravity ℓ waves"
    assert section_slug(r"Surface \& gravity waves") == "surface-gravity-waves"


def test_build_info_exposes_stable_labels_and_commit_urls() -> None:
    info = BuildInfo("a" * 40, "abcdef0", "v1.2.3")
    assert info.label == "v1.2.3 (abcdef0)"
    assert info.commit_url.endswith("/commit/" + "a" * 40)
