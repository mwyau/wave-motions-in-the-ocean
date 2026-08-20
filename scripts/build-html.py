#!/usr/bin/env python3
"""Build the chapter-split modern HTML edition from the LaTeX sources.

Pandoc is used after a temporary, generated compatibility transform. Chapter
prose/equations are never duplicated or maintained as HTML. TikZ sources are
rendered to SVG; source-PDF crops are rendered to PNG under build/dist only.
Expensive source-page and TikZ renders are content-addressed under .cache/.
"""
from __future__ import annotations

import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

from PIL import Image

from book_views import DOWNLOADS, html_contents, html_license

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
SOURCE = ROOT / "source"
FIGURES = RECON / "figures"
BUILD = ROOT / "build" / "html-pandoc"
CACHE = Path(os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions")))
SOURCE_PAGE_CACHE = CACHE / "source-pages"
TIKZ_CACHE = CACHE / "tikz"
OUT = ROOT / "dist"
ASSETS = OUT / "assets"
FIG_ASSETS = ASSETS / "figures"
SOURCE_RENDER_DPI = 170
TIKZ_CACHE_VERSION = "v1"
TIKZ_STANDALONE_TEMPLATE = r"""\documentclass[border=5pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,bm,mathtools}
\usepackage{graphicx,xcolor,tikz}
\usetikzlibrary{calc,decorations.pathreplacing}
\begin{document}
\begingroup
\let\par\relax
\let\smallskip\relax
\def\center{}
\def\endcenter{}
\input{%s}
\endgroup\end{document}
"""

SOURCEART_RE = re.compile(
    r"\\sourceart(?:\[(?P<width>[^]]+)\])?"
    r"\{(?P<pdf>[^}]+)\}\{(?P<page>\d+)\}\{(?P<trim>[^}]+)\}"
)
VECTOR_RE = re.compile(r"\\wavevectorart(?:\[(?P<width>[^]]+)\])?\{(?P<stem>[^}]+)\}")
TIKZ_INPUT_RE = re.compile(r"\\input\{figures/(?P<stem>[^}]+)\.tikz\}")
SIGNATURE_RE = re.compile(
    r"\\wavesignature\{(?P<name>[^{}]+)\}\{(?P<place>[^{}]+)\}\{(?P<year>[^{}]+)\}"
)
# Direct source-PDF inclusions retained where a one-off wrapper would be needless.
DIRECT_PDF_RE = re.compile(
    r"\\includegraphics\[(?P<opts>[^]]*page=(?P<page>\d+)[^]]*trim=(?P<trim>[^,\]]+)[^]]*)\]"
    r"\s*\{(?P<path>\.\./source/(?P<pdf>[^}]+))\}",
    re.S,
)
LOCAL_RASTER_RE = re.compile(
    r"\\includegraphics(?:\[[^]]*\])?\s*\{figures/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.I,
)
PDF_ONLY_RE = re.compile(
    r"\\begin\{wavepdfonly\}.*?\\end\{wavepdfonly\}",
    re.S,
)
WAVE_NUMBERED_RE = re.compile(
    r"\\begin\{(?P<env>waveequation|wavealign)\}(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    re.S,
)
NATIVE_TAGGED_EQUATION_RE = re.compile(
    r"\\begin\{equation\}(?P<body>.*?)\\tag\{(?P<tag>\d+\.\d+)\}(?P<tail>.*?)"
    r"\\end\{equation\}",
    re.S,
)
FIGURE_MARK_RE = re.compile(r"\\wavefiguremark")


def run(cmd: list[str], *, cwd: Path | None = None, quiet: bool = True) -> None:
    kwargs = {"cwd": cwd, "check": True}
    if quiet:
        kwargs.update(stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as exc:
        if quiet and exc.stderr:
            sys.stderr.write(exc.stderr[-12000:])
        raise


def require(cmd: str) -> None:
    if shutil.which(cmd) is None:
        raise SystemExit(f"missing required command: {cmd}")


@lru_cache(maxsize=None)
def file_sha256(path_text: str) -> str:
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_size_points(pdf: Path, page: int) -> tuple[float, float]:
    text = subprocess.check_output(
        ["pdfinfo", "-f", str(page), "-l", str(page), "-box", str(pdf)], text=True
    )
    m = re.search(rf"Page\s+{page} size:\s+([0-9.]+) x ([0-9.]+) pts", text)
    if not m:
        raise RuntimeError(f"could not determine page size for {pdf.name} page {page}")
    return float(m.group(1)), float(m.group(2))


def parse_trim(text: str) -> tuple[float, float, float, float]:
    vals = re.findall(r"(-?[0-9.]+)\s*bp", text)
    if len(vals) != 4:
        raise ValueError(f"expected four bp trim values, got {text!r}")
    return tuple(map(float, vals))


def source_crop(pdf_name: str, page: int, trim: str, *, angle: float = 0.0) -> str:
    pdf = SOURCE / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    pdf_digest = file_sha256(str(pdf.resolve()))
    identity = f"{pdf_name}|{pdf_digest}|{page}|{trim}|{angle:g}|dpi={SOURCE_RENDER_DPI}"
    digest = hashlib.sha1(identity.encode()).hexdigest()[:10]
    stem = Path(pdf_name).stem
    name = f"source-{stem}-p{page:03d}-{digest}.png"
    dest = FIG_ASSETS / name
    if dest.exists():
        return f"assets/figures/{name}"

    page_cache = (
        SOURCE_PAGE_CACHE
        / f"{stem}-{pdf_digest[:12]}-p{page:03d}-r{SOURCE_RENDER_DPI}.png"
    )
    page_cache.parent.mkdir(parents=True, exist_ok=True)
    if not page_cache.exists():
        prefix = page_cache.with_suffix("")
        run([
            "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
            "-r", str(SOURCE_RENDER_DPI), "-png", str(pdf), str(prefix),
        ])
    img = Image.open(page_cache).convert("RGB")
    pw, ph = page_size_points(pdf, page)
    left, bottom, right, top = parse_trim(trim)
    x0 = round(left / pw * img.width)
    x1 = round(img.width - right / pw * img.width)
    y0 = round(top / ph * img.height)
    y1 = round(img.height - bottom / ph * img.height)
    if not (0 <= x0 < x1 <= img.width and 0 <= y0 < y1 <= img.height):
        raise ValueError(f"invalid crop for {pdf_name} page {page}: {trim}")
    img = img.crop((x0, y0, x1, y1))
    if angle:
        img = img.rotate(angle, expand=True, fillcolor="white")
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, optimize=True)
    return f"assets/figures/{name}"


def render_tikz_svg(stem: str) -> None:
    dest = FIG_ASSETS / f"{stem}.svg"
    if dest.exists():
        return
    tikz = FIGURES / f"{stem}.tikz"
    if not tikz.exists():
        raise FileNotFoundError(tikz)

    digest = hashlib.sha256(
        TIKZ_CACHE_VERSION.encode()
        + b"\0"
        + TIKZ_STANDALONE_TEMPLATE.encode()
        + b"\0"
        + (ROOT / "tex-packages.txt").read_bytes()
        + b"\0"
        + tikz.read_bytes()
    ).hexdigest()[:16]
    cached_svg = TIKZ_CACHE / f"{stem}-{digest}.svg"
    if cached_svg.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached_svg, dest)
        return

    td = BUILD / "tikz" / stem
    if td.exists():
        shutil.rmtree(td)
    td.mkdir(parents=True)
    tex = td / "figure.tex"
    tex.write_text(TIKZ_STANDALONE_TEMPLATE % tikz.as_posix())
    run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "figure.tex"], cwd=td)
    tmp_svg = td / "figure.svg"
    run(["pdftocairo", "-svg", str(td / "figure.pdf"), str(tmp_svg)])
    cached_svg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmp_svg, cached_svg)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmp_svg, dest)


def referenced_tikz() -> list[str]:
    stems: set[str] = set()
    for path in [RECON / f"chapter{i}.tex" for i in range(1, 7)]:
        text = path.read_text()
        stems.update(m.group("stem") for m in VECTOR_RE.finditer(text))
        stems.update(m.group("stem") for m in TIKZ_INPUT_RE.finditer(text))
    return sorted(stems)


def prepare_vector_assets() -> None:
    stems = referenced_tikz()
    workers = max(1, min(4, (os.cpu_count() or 2)))
    print(f"Rendering {len(stems)} TikZ figures to SVG ({workers} workers; cache enabled)...")
    failures: list[tuple[str, Exception]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(render_tikz_svg, stem): stem for stem in stems}
        for fut in as_completed(futs):
            stem = futs[fut]
            try:
                fut.result()
            except Exception as exc:
                failures.append((stem, exc))
    if failures:
        for stem, exc in failures:
            print(f"TikZ render failed: {stem}: {exc}", file=sys.stderr)
        raise SystemExit(f"{len(failures)} TikZ figure render(s) failed")


def transform_tex(text: str, chapter_number: int | None = None) -> str:
    # Keep the PDF cover out of flowing outputs while preserving the web title
    # block used by HTML/README and the EPUB interior title page.
    text = PDF_ONLY_RE.sub("", text)
    text = text.replace(r"\begin{wavewebonly}", "").replace(r"\end{wavewebonly}", "")
    text = text.replace(r"\nopagecolor", "")

    # Source-compatible pagination has no meaning in flowing HTML.
    text = text.replace(r"\sourcepagebreak", "")
    text = re.sub(r"\\setcounter\{page\}\{[^}]+\}", "", text)

    def signature_sub(m: re.Match[str]) -> str:
        return (
            "\\begin{flushright}\n"
            f"\\textit{{{m.group('name')}}}\\\\\n"
            f"{m.group('place')}, {m.group('year')}\n"
            "\\end{flushright}"
        )

    text = SIGNATURE_RE.sub(signature_sub, text)

    def vector_sub(m: re.Match[str]) -> str:
        return rf"\includegraphics{{assets/figures/{m.group('stem')}.svg}}" + "\n\\wavefiguremark"

    text = VECTOR_RE.sub(vector_sub, text)
    text = TIKZ_INPUT_RE.sub(lambda m: rf"\includegraphics{{assets/figures/{m.group('stem')}.svg}}", text)

    def source_sub(m: re.Match[str]) -> str:
        rel = source_crop(m.group("pdf"), int(m.group("page")), m.group("trim"))
        return rf"\includegraphics{{{rel}}}" + "\n\\wavefiguremark"

    text = SOURCEART_RE.sub(source_sub, text)

    def direct_sub(m: re.Match[str]) -> str:
        opts = m.group("opts")
        am = re.search(r"angle\s*=\s*(-?[0-9.]+)", opts)
        angle = float(am.group(1)) if am else 0.0
        rel = source_crop(m.group("pdf"), int(m.group("page")), m.group("trim"), angle=angle)
        return rf"\includegraphics{{{rel}}}"

    text = DIRECT_PDF_RE.sub(direct_sub, text)
    text = LOCAL_RASTER_RE.sub(
        lambda m: rf"\includegraphics{{assets/figures/{m.group('name')}}}", text
    )

    if chapter_number is None:
        # Front matter has no numbered body figures/equations.
        text = WAVE_NUMBERED_RE.sub(lambda m: rf"\[{m.group('body')}\]", text)
        return FIGURE_MARK_RE.sub("", text)

    native_labels: list[str] = []
    def native_equation_sub(m: re.Match[str]) -> str:
        tag = m.group("tag")
        if not tag.startswith(f"{chapter_number}."):
            raise SystemExit(f"chapter {chapter_number}: native equation tag {tag} has wrong chapter")
        native_labels.append(f"({tag})")
        body = (m.group("body") + m.group("tail")).strip()
        return (
            "\\[\n" + body + "\n\\]\n"
            "\\begin{flushright}\n\\textup{(" + tag + ")}\n\\end{flushright}"
        )

    text = NATIVE_TAGGED_EQUATION_RE.sub(native_equation_sub, text)

    equation_number = 0
    def numbered_equation_sub(m: re.Match[str]) -> str:
        nonlocal equation_number
        equation_number += 1
        body = m.group("body").strip()
        if m.group("env") == "wavealign":
            body = r"\begin{aligned}" + body + r"\end{aligned}"
        label = f"({chapter_number}.{equation_number})"
        return (
            "\\[\n" + body + "\n\\]\n"
            "\\begin{flushright}\n\\textup{" + label + "}\n\\end{flushright}"
        )

    text = WAVE_NUMBERED_RE.sub(numbered_equation_sub, text)
    if native_labels and equation_number:
        raise SystemExit(f"chapter {chapter_number}: mixed native and editorial equation numbering is unsupported")

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
    if figure_number != {1:7, 2:10, 3:12, 4:30, 5:31, 6:14}[chapter_number]:
        raise SystemExit(
            f"chapter {chapter_number}: expected canonical figure count, got {figure_number}"
        )
    return text


def pandoc_page(source_tex: Path, output: Path, title: str) -> None:
    run([
        "pandoc", str(source_tex), "-f", "latex", "-t", "html5", "-s",
        "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js",
        "--metadata", f"title={title}", "--metadata", "lang=en-US", "-o", str(output),
    ])


def inject_css_and_nav(page: Path, nav: str) -> None:
    text = page.read_text(errors="replace")
    if "assets/wave.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="assets/wave.css" />\n</head>')
    top = (
        '<a class="skip-link" href="#main-content">Skip to content</a>\n'
        + nav
        + '\n<main id="main-content">'
    )
    bottom = "</main>\n" + nav
    text = text.replace("<body>", "<body>\n" + top, 1)
    text = text.replace("</body>", bottom + "\n</body>", 1)
    page.write_text(text)


def make_nav(index: int | None = None) -> str:
    links = ['<a href="index.html#contents">Contents</a>']
    if index is not None and index > 1:
        links.append(f'<a href="chapter{index-1}.html">Previous chapter</a>')
    if index is not None and index < 6:
        links.append(f'<a href="chapter{index+1}.html">Next chapter</a>')
    if index == 6:
        links.append('<a href="references.html">References</a>')
    return '<nav class="book-nav" aria-label="Book navigation">' + " · ".join(links) + "</nav>"


def build_index(temp: Path) -> None:
    text = (RECON / "frontmatter-modern.tex").read_text()
    text = text.replace(r"\tableofcontents", "")
    src = temp / "frontmatter.tex"
    src.write_text(transform_tex(text))
    page = OUT / "index.html"
    pandoc_page(src, page, "Wave Motions in the Ocean: Myrl's View")
    available_downloads = tuple(item for item in DOWNLOADS if (OUT / item[0]).is_file())
    toc = html_contents(downloads=available_downloads)
    license_html = html_license()
    html_text = page.read_text(errors="replace")
    html_text = html_text.replace("</body>", toc + "\n" + license_html + "\n</body>")
    page.write_text(html_text)
    inject_css_and_nav(page, make_nav(None))


def build_references(temp: Path) -> None:
    md = temp / "references.md"
    md.write_text("---\ntitle: References\nlang: en-US\nnocite: |\n  @*\n---\n")
    page = OUT / "references.html"
    run([
        "pandoc", str(md), "-s", "-t", "html5", "--citeproc",
        f"--bibliography={RECON / 'references.bib'}", "-o", str(page),
    ])
    nav = '<nav class="book-nav" aria-label="Book navigation"><a href="index.html#contents">Contents</a> · <a href="chapter6.html">Previous chapter</a></nav>'
    inject_css_and_nav(page, nav)


def validate() -> None:
    required = [OUT / "index.html", OUT / "references.html"] + [OUT / f"chapter{i}.html" for i in range(1, 7)]
    missing = [p.name for p in required if not p.is_file() or p.stat().st_size == 0]
    if missing:
        raise SystemExit("missing HTML outputs: " + ", ".join(missing))
    combined = "\n".join(p.read_text(errors="replace") for p in required)
    for sentinel in ("David C. Chapman", "Paola Malanotte-Rizzoli", "CC BY-NC-SA 4.0", "Apel"):
        if sentinel not in combined:
            raise SystemExit(f"HTML sentinel missing: {sentinel}")
    broken: list[tuple[str, str]] = []
    for page in required:
        text = page.read_text(errors="replace")
        if not re.search(r'<html[^>]+lang="en-US"', text, flags=re.I):
            raise SystemExit(f"HTML language metadata missing from {page.name}")
        if '<main id="main-content">' not in text or 'class="skip-link"' not in text:
            raise SystemExit(f"HTML main/skip navigation missing from {page.name}")
        for attr in ("src", "href"):
            for ref in re.findall(rf'{attr}=["\']([^"\']+)["\']', text, flags=re.I):
                if ref.startswith(("http:", "https:", "mailto:", "#", "javascript:", "data:")):
                    continue
                target = ref.split("#", 1)[0].split("?", 1)[0]
                if target and not (page.parent / target).exists():
                    broken.append((page.name, ref))
    if broken:
        for page, ref in broken[:40]:
            print(f"broken local reference: {page}: {ref}", file=sys.stderr)
        raise SystemExit(f"{len(broken)} broken local HTML reference(s)")


def main() -> int:
    for cmd in ("pandoc", "latexmk", "pdflatex", "pdftocairo", "pdftoppm", "pdfinfo"):
        require(cmd)
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(ASSETS, ignore_errors=True)
    shutil.rmtree(OUT / "html", ignore_errors=True)  # legacy nested site layout
    OUT.mkdir(parents=True, exist_ok=True)
    for page in [OUT / "index.html", OUT / "references.html"] + [
        OUT / f"chapter{i}.html" for i in range(1, 7)
    ]:
        page.unlink(missing_ok=True)
    BUILD.mkdir(parents=True)
    FIG_ASSETS.mkdir(parents=True)
    SOURCE_PAGE_CACHE.mkdir(parents=True, exist_ok=True)
    TIKZ_CACHE.mkdir(parents=True, exist_ok=True)
    prepare_vector_assets()
    # Intentionally edited raster figures and front-matter photos are committed once.
    for raster in FIGURES.rglob("*"):
        if not raster.is_file() or raster.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        dest = FIG_ASSETS / raster.relative_to(FIGURES)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raster, dest)

    css = ASSETS / "wave.css"
    css.write_text(
        """html { color-scheme: light; }
body { max-width: 72rem; margin: 0 auto; padding: 1.5rem 2rem 4rem; line-height: 1.58; font-family: Georgia, 'Times New Roman', serif; }
h1,h2,h3,nav { font-family: system-ui, sans-serif; }
main { min-width: 0; }
div.center { text-align: center; }
div.flushright { text-align: right; margin-top: -0.85em; }
.skip-link { position: absolute; left: -10000px; top: auto; width: 1px; height: 1px; overflow: hidden; }
.skip-link:focus { left: 1rem; top: 1rem; width: auto; height: auto; z-index: 1000; padding: .5rem .75rem; background: white; color: black; border: 2px solid currentColor; }
.book-nav { margin: 0 0 2rem; padding: .75rem 0; border-bottom: 1px solid #bbb; }
.book-nav + main > header { margin-top: 1rem; }
.book-toc { margin: 3rem 0; padding-top: 1rem; border-top: 1px solid #bbb; }
.flushright { text-align: right; margin: 1.5rem 0; }
img, svg { display: block; max-width: min(100%, 58rem); height: auto; margin: 1.1rem auto; }
.math.display { overflow-x: auto; overflow-y: hidden; padding: .2rem 0; }
.references { font-size: .96rem; }
.license img { display: inline; width: 1em; height: 1em; margin: 0 0 0 .2em; vertical-align: -.12em; }
a { overflow-wrap: anywhere; }
@media (max-width: 700px) { body { padding: 1rem 1rem 3rem; } .book-nav { font-size: .92rem; } }
"""
    )

    temp = BUILD / "source"
    temp.mkdir()
    build_index(temp)
    for i in range(1, 7):
        src = temp / f"chapter{i}.tex"
        src.write_text(transform_tex((RECON / f"chapter{i}.tex").read_text(), chapter_number=i))
        page = OUT / f"chapter{i}.html"
        pandoc_page(src, page, f"Wave Motions in the Ocean — Chapter {i}")
        inject_css_and_nav(page, make_nav(i))
    build_references(temp)
    validate()
    print("HTML build OK: index + 6 chapters + references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
