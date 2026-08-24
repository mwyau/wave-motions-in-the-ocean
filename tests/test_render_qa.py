import html
import urllib.parse
import urllib.request
from pathlib import Path

import render_qa

BOUNDARY_SOURCE = r"""\begin{aligned}
p_t+w p_{0z}=p_t-gw\rho_0 & =0 &  & \text{at }z=0,  \\
w                         & =0 &  & \text{at }z=-D.
\end{aligned}"""


def math_pair(source: str, kind: str = "display") -> str:
    delimiters = (r"\(", r"\)") if kind == "inline" else (r"\[", r"\]")
    display = "inline" if kind == "inline" else "block"
    return (
        f'<span data-math-renderer="mathjax" hidden class="math {kind}">'
        f"{delimiters[0]}{source}{delimiters[1]}</span>"
        f'<span data-math-renderer="mathml" class="math {kind} mathml-alternate">'
        f'<math display="{display}" xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<semantics><mrow><mi>x</mi></mrow><annotation "
        f'encoding="application/x-tex">{html.escape(source)}</annotation>'
        "</semantics></math></span>"
    )


def write_publication(root: Path, *, include_boundary: bool = True) -> None:
    root.mkdir()
    for name in render_qa.EXPECTED_HTML:
        source = (
            BOUNDARY_SOURCE if name == "chapter5.html" and include_boundary else "x"
        )
        kind = "display" if name == "chapter5.html" else "inline"
        (root / name).write_text(
            "<!doctype html><html><head>"
            f'<title>{name}</title><meta name="viewport" content="width=device-width">'
            "</head><body>" + math_pair(source, kind) + "</body></html>"
        )

    assets = root / "assets"
    mathjax_fonts = assets / "mathjax" / "output" / "chtml" / "fonts" / "woff-v2"
    mathjax_fonts.mkdir(parents=True)
    (assets / "wave.css").write_text(
        "@media (max-width: 700px) {} @media (prefers-color-scheme: dark) {}"
    )
    (assets / "wave.js").write_text("")
    (assets / "mathjax" / "tex-chtml-full.js").write_text("")
    (assets / "fonts").mkdir()
    for name in (
        "SourceSerif4Variable-Roman.otf.woff2",
        "SourceSans3VF-Upright.otf.woff2",
    ):
        (assets / "fonts" / name).write_bytes(b"font")


def publication_tree(root: Path) -> tuple[str, ...]:
    return tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*")))


def test_math_specimen_uses_audit_page_and_virtual_arbitrary_root(
    tmp_path: Path,
) -> None:
    dist = tmp_path / "publication-archive"
    write_publication(dist)
    audit = tmp_path / "audit"
    report = render_qa.Report(str(dist), dist, audit)
    before = publication_tree(dist)

    page, labels = render_qa.mathml_comparison_specimen(dist, report)

    assert page == audit / "html" / "mathml-mathjax-comparison.html"
    assert "Chapter 5 boundary align" in labels
    assert publication_tree(dist) == before
    assert not (dist / "mathml-mathjax-comparison.html").exists()
    specimen = page.read_text()
    assert 'href="/assets/wave.css"' in specimen
    assert 'src="/assets/mathjax/tex-chtml-full.js"' in specimen
    assert '<main id="main-content">' in specimen
    assert 'data-text-size="default"' in specimen
    for text_size in render_qa.MATH_PARITY_TEXT_SIZES:
        assert f"'{text_size}'" in specimen
    assert "../../../release/" not in specimen

    (dist / "assets" / "wave.css").write_text("publication CSS")
    with render_qa.local_server(
        dist, qa_pages={render_qa.MATHML_COMPARISON_ROUTE: page}
    ) as base:
        with urllib.request.urlopen(
            f"{base}{render_qa.MATHML_COMPARISON_ROUTE}?text-size=large"
        ) as response:
            served_specimen = response.read().decode()
        with urllib.request.urlopen(f"{base}/assets/wave.css") as response:
            served_css = response.read().decode()

    assert served_specimen == specimen
    assert served_css == "publication CSS"


def test_math_parity_jobs_cover_widths_and_reader_text_sizes() -> None:
    jobs = render_qa.math_parity_jobs()

    assert len(jobs) == 9
    assert [job[0] for job in jobs] == [
        f"math-parity-{width}-{text_size}.png"
        for width, _height in render_qa.MATH_PARITY_VIEWPORTS
        for text_size in render_qa.MATH_PARITY_TEXT_SIZES
    ]
    assert {(job[2], job[3]) for job in jobs} == set(render_qa.MATH_PARITY_VIEWPORTS)
    assert {
        urllib.parse.parse_qs(urllib.parse.urlsplit(job[1]).query)["text-size"][0]
        for job in jobs
    } == set(render_qa.MATH_PARITY_TEXT_SIZES)


def test_math_specimen_requires_chapter5_boundary_alignment(tmp_path: Path) -> None:
    dist = tmp_path / "publication-copy"
    write_publication(dist, include_boundary=False)
    report = render_qa.Report(str(dist), dist, tmp_path / "audit")

    page, labels = render_qa.mathml_comparison_specimen(dist, report)

    assert page is not None
    assert "Chapter 5 boundary align" not in labels
    assert any(
        finding.level == "ERROR"
        and "required Chapter 5 trailing-boundary alignment" in finding.message
        for finding in report.findings
    )


def test_html_qa_leaves_publication_root_unchanged_on_success_and_failure(
    tmp_path: Path, monkeypatch
) -> None:
    dist = tmp_path / "staged-publication"
    write_publication(dist)
    before = publication_tree(dist)

    render_qa.html_qa(
        dist,
        render_qa.Report(str(dist), dist, tmp_path / "audit-success"),
        browser=None,
    )
    assert publication_tree(dist) == before

    def failed_screenshot(*args, **kwargs):
        args[2].parent.mkdir(parents=True, exist_ok=True)
        return False, "simulated browser failure"

    monkeypatch.setattr(render_qa, "browser_screenshot", failed_screenshot)
    monkeypatch.setattr(
        render_qa,
        "browser_dump_dom",
        lambda *args, **kwargs: (False, "simulated browser failure"),
    )
    failed_report = render_qa.Report(str(dist), dist, tmp_path / "audit-failure")
    render_qa.html_qa(dist, failed_report, browser="fake-browser")

    assert publication_tree(dist) == before
    assert not (dist / "mathml-mathjax-comparison.html").exists()
    assert any(finding.level == "WARNING" for finding in failed_report.findings)
