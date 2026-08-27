import re
from pathlib import Path

import pytest

from validate import (
    PUNCTUATION_ENTITY_RE,
    SMART_ANCHOR_RE,
    SMART_PUNCTUATION_RE,
    bare_named_functions,
    github_math_patterns,
    parse_facsimile_log,
    require_labels,
    strip_tex_comments,
    tex_math_regions,
    validate_mathml_alignment,
    validate_offline_runtime,
)


def test_strip_tex_comments_keeps_escaped_percent_signs() -> None:
    source = "keep % remove\nescaped \\% stays % remove too"

    assert strip_tex_comments(source) == "keep \nescaped \\% stays "


def test_tex_math_regions_extracts_only_math_delimiters() -> None:
    source = r"prose \[x+y\] \begin{waveequation}z=1\end{waveequation} and $q$"

    assert tex_math_regions(source) == ["x+y", "z=1", "q"]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (r"\[sin x + tan y\]", ("sin", "tan")),
        (r"\[\sin x + \operatorname{cos}(x) + \text{tanh}\]", ()),
        ("sin and cos in prose", ()),
    ],
)
def test_bare_named_function_detection_uses_math_only(
    source: str, expected: tuple[str, ...]
) -> None:
    assert bare_named_functions(source) == expected


def test_numbered_equation_labels_accept_one_ordered_occurrence() -> None:
    require_labels(
        "prefix (1.1) middle (1.2) suffix", ("(1.1)", "(1.2)"), artifact="sample"
    )


@pytest.mark.parametrize(
    "text",
    [
        "prefix (1.2) middle (1.1)",
        "prefix (1.1) middle (1.1) suffix (1.2)",
        "prefix (1.1) suffix",
    ],
)
def test_numbered_equation_labels_reject_order_duplicates_and_missing(
    text: str,
) -> None:
    with pytest.raises(SystemExit):
        require_labels(text, ("(1.1)", "(1.2)"), artifact="sample")


def test_github_math_patterns_recognize_inline_and_code_math() -> None:
    inline, code = github_math_patterns(r"\ell")

    assert inline.search(r"$\ell$")
    assert code.search(r"$`\ell`$")
    assert not inline.search(r"\$\ell$")


def test_punctuation_patterns_distinguish_reader_text_from_tex_syntax() -> None:
    assert SMART_PUNCTUATION_RE.search("reader — text")
    assert not SMART_PUNCTUATION_RE.search("source -- text")
    assert PUNCTUATION_ENTITY_RE.search("&mdash;")
    assert SMART_ANCHOR_RE.search('id="bad—anchor"')


def test_toolbar_labels_use_deterministic_spacing() -> None:
    template = (
        Path(__file__).resolve().parents[1] / "src" / "layout" / "wave-html.html"
    ).read_text()

    for label in ("Rendering:", "Figures:", "Text:", "Theme:"):
        assert f'<span class="reader-setting-label">{label}</span>' in template
    assert 'class="text-size-value" data-text-size-value' in template


def test_reader_context_keeps_chapter_link_static_and_section_updates_local() -> None:
    root = Path(__file__).resolve().parents[1]
    template = (root / "src" / "layout" / "wave-html.html").read_text()
    stylesheet = (root / "src" / "layout" / "wave-html.css").read_text()
    script = (root / "src" / "layout" / "wave-html.js").read_text()
    builder = (root / "scripts" / "build_html.py").read_text()

    assert (
        '<a class="reader-context-chapter" href="$reader_chapter_url$">$reader_chapter$</a>'
        in template
    )
    assert '<span class="reader-context-chapter">$reader_chapter$</span>' in template
    assert '"reader_chapter_url": f"chapter{chapter.number}.html"' in builder
    assert "readerContextTitle.textContent = title;" in script
    assert "readerContext.textContent" not in script
    chapter_link_rule = re.search(
        r"a\.reader-context-chapter,\s*"
        r"a\.reader-context-chapter:visited\s*\{(?P<body>.*?)\}",
        stylesheet,
        re.DOTALL,
    )
    assert chapter_link_rule is not None
    chapter_link_styles = chapter_link_rule.group("body")
    assert "font-weight: 500;" in chapter_link_styles
    assert "text-decoration: underline;" in chapter_link_styles
    assert "a.reader-context-chapter:focus-visible" in stylesheet


def test_figure_controls_are_conditional_and_progressive() -> None:
    root = Path(__file__).resolve().parents[1]
    template = (root / "src" / "layout" / "wave-html.html").read_text()
    stylesheet = (root / "src" / "layout" / "wave-html.css").read_text()
    script = (root / "src" / "layout" / "wave-html.js").read_text()
    builder = (root / "scripts" / "build_html.py").read_text()

    assert "$if(has_switchable_figures)$" in template
    assert 'data-figure-cycle aria-label="Figures currently showing vectors' in template
    assert '<span class="reader-setting-label">Figures:</span>' in template
    assert '<span class="control-compact" aria-hidden="true">Fig</span>' in template
    assert 'class="figure-view-toggle js-only"' in builder
    assert ":root.no-js .js-only" in stylesheet
    assert 'const figureModes = ["vector", "original"]' in script
    assert "data-vector-src" in script
    assert "originalSrc" in script
    assert "wave-figure-view" not in script
    assert 'localStorage.setItem("wave-figure' not in script


def test_figure_audit_uses_committed_visual_pairs_without_asset_review_state() -> None:
    root = Path(__file__).resolve().parents[1]
    figures = root / "src" / "FIGURES.md"
    text = figures.read_text()

    assert "Asset review" not in text
    assert "review-needed" not in text
    assert "same-stem source PNGs must not" not in (
        (root / "scripts" / "build_html.py").read_text()
        + (root / "scripts" / "validate.py").read_text()
    )

    assert "<img" not in text
    chapter_ledgers = sorted((figures.parent / "figures").glob("CHAPTER*.md"))
    assert len(chapter_ledgers) == 6
    for ledger in chapter_ledgers:
        image_paths = re.findall(r'<img\s+src="([^"]+)"', ledger.read_text())
        assert image_paths
        for image_path in image_paths:
            assert (ledger.parent / image_path).is_file(), image_path

    for tikz in sorted((figures.parent / "figures").glob("*.tikz")):
        assert (tikz.with_suffix(".svg")).is_file()
        assert (tikz.with_suffix(".png")).is_file()


def test_text_size_controls_are_numeric_actions() -> None:
    template = (
        Path(__file__).resolve().parents[1] / "src" / "layout" / "wave-html.html"
    ).read_text()

    assert 'data-text-size-action="decrease"' in template
    assert 'data-text-size-action="reset"' in template
    assert 'data-text-size-action="increase"' in template
    assert 'aria-label="Decrease text size"' in template
    assert 'aria-label="Reset text size to 100%"' in template
    assert 'aria-label="Increase text size"' in template
    assert "data-text-size-option" not in template
    assert 'data-text-size-action="decrease" aria-pressed' not in template


def test_reader_anchor_geometry_has_one_css_owned_gutter() -> None:
    stylesheet = (
        Path(__file__).resolve().parents[1] / "src" / "layout" / "wave-html.css"
    ).read_text()
    script = (
        Path(__file__).resolve().parents[1] / "src" / "layout" / "wave-html.js"
    ).read_text()

    assert "--wave-anchor-gutter: clamp(12px, .75rem, 24px);" in stylesheet
    assert (
        "var(--wave-measured-header-height, var(--wave-nav-fallback-height))"
        in stylesheet
    )
    assert "--wave-measured-header-height" in script
    assert "--wave-anchor-offset" not in stylesheet + script
    assert "width: min(6.75rem" not in stylesheet
    assert "Math.max(12" not in script


def test_facsimile_log_parser_reads_boundaries_and_shipouts() -> None:
    log = (
        "FACSIMILE_B n=1 p=1 s=12.50pt\n"
        "unrelated diagnostic\n"
        "FACSIMILE_P n=11 p=1\n"
        "FACSIMILE_B n=2 p=2 s=-0.25pt\n"
        "FACSIMILE_P n=12 p=2"
    )

    boundaries, shipouts = parse_facsimile_log(log)

    assert boundaries == [(1, 1, 12.5), (2, 2, -0.25)]
    assert shipouts == [(11, 1), (12, 2)]


def test_offline_runtime_accepts_local_html_and_css(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(
        '<link rel="stylesheet" href="assets/site.css">'
        '<script src="assets/app.js"></script>'
    )
    (tmp_path / "assets/site.css").write_text(
        '@import "local.css"; .page { background: url("../paper.png"); }'
    )

    validate_offline_runtime(tmp_path)


@pytest.mark.parametrize(
    ("html", "css"),
    [
        ('<script src="https://cdn.example/app.js"></script>', ""),
        ("", '@import url("https://cdn.example/site.css");'),
    ],
)
def test_offline_runtime_rejects_remote_dependencies(
    tmp_path: Path, html: str, css: str
) -> None:
    (tmp_path / "index.html").write_text(html)
    (tmp_path / "site.css").write_text(css)

    with pytest.raises(ValueError, match="remote runtime dependencies"):
        validate_offline_runtime(tmp_path)


def test_mathml_alignment_requires_normalized_boundary_columns() -> None:
    valid = (
        '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
        "<semantics><mtable>"
        "<mtr><mtd><mi>p</mi></mtd><mtd><mtext>at </mtext><mi>z</mi></mtd></mtr>"
        "</mtable></semantics></math>"
    )
    invalid = valid.replace(
        "<mtd><mtext>at </mtext><mi>z</mi></mtd>",
        "<mtd><mo>=</mo><mn>0</mn></mtd><mtd></mtd>"
        "<mtd><mtext>at </mtext><mi>z</mi></mtd>",
        1,
    )

    assert validate_mathml_alignment(valid) == (1, 1)
    with pytest.raises(ValueError, match="unintended 4-column table"):
        validate_mathml_alignment(invalid)


def test_mathml_alignment_requires_explicit_columns_for_aligned() -> None:
    invalid = (
        '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">'
        "<semantics><mtable>"
        "<mtr><mtd><mi>a</mi></mtd><mtd><mo>=</mo><mn>1</mn></mtd></mtr>"
        '</mtable><annotation encoding="application/x-tex">'
        r"\begin{aligned}a&amp;=1\end{aligned}"
        "</annotation></semantics></math>"
    )

    with pytest.raises(ValueError, match="incorrect column alignment"):
        validate_mathml_alignment(invalid)
