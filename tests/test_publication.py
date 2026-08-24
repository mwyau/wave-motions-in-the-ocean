from pathlib import Path

import pytest

import build_html
import publication
from publication import (
    BuildInfo,
    _balanced_command_args,
    parse_trim,
    prepare_assets,
    prepare_original_assets,
    reader_punctuation,
    section_slug,
    source_crop,
    switchable_figure_stems,
    tex_plain,
    tikz_source_metadata,
    transform_tex,
)


def test_parse_trim_accepts_four_bp_values() -> None:
    assert parse_trim("1bp 2.5bp -3bp 4.25bp") == (1.0, 2.5, -3.0, 4.25)


def test_parse_trim_rejects_malformed_values() -> None:
    for trim in ("1bp 2bp 3bp", "1bp 2bp 3bp 4px", "1bp 2bp 3bp 4bp 5bp"):
        with pytest.raises(ValueError, match="expected four bp trim values"):
            parse_trim(trim)


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
    ) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(f"{angle}:{optimize}".encode())

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


def test_prepare_original_assets_skips_figures_without_source_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publication, "referenced_tikz", lambda: ["vector", "digital"])
    metadata = {"vector": ("scan.pdf", 3, "1bp 2bp 3bp 4bp"), "digital": None}
    monkeypatch.setattr(
        publication,
        "tikz_source_metadata",
        lambda stem: metadata[stem],
    )
    calls: list[tuple[str, Path, str]] = []
    monkeypatch.setattr(
        publication,
        "render_tikz_source_png",
        lambda stem, assets_root, *, asset_prefix: (
            calls.append((stem, assets_root, asset_prefix))
            or "assets/figures/vector.png"
        ),
    )

    prepare_original_assets(tmp_path)

    assert calls == [("vector", tmp_path, "assets/figures")]


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
