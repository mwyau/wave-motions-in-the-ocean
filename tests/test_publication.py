from pathlib import Path

import pytest

import publication
from publication import (
    BuildInfo,
    _balanced_command_args,
    parse_trim,
    reader_punctuation,
    section_slug,
    source_crop,
    tex_plain,
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
