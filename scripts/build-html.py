#!/usr/bin/env python3
"""Build the chapter-split modern HTML edition from the canonical LaTeX sources.

Pandoc is used after a temporary, generated compatibility transform. Chapter
prose/equations are never duplicated or maintained as HTML. TikZ sources are
rendered to SVG; source-PDF crops are rendered to PNG under build/dist only.
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
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
SOURCE = ROOT / "source"
FIGURES = RECON / "figures"
BUILD = ROOT / "build" / "html-pandoc"
OUT = ROOT / "dist"
ASSETS = OUT / "assets"
FIG_ASSETS = ASSETS / "figures"

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
    r"\\includegraphics(?:\[[^]]*\])?\{figures/(?P<name>[^}]+\.(?:png|jpe?g))\}",
    re.I,
)
IF_PHOTO_RE = re.compile(
    r"\\IfFileExists\{figures/frontmatter/salmon-hendershott-como-1980\.jpeg\}\{%.*?\n\}\{%.*?\n\}\n",
    re.S,
)


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
    identity = f"{pdf_name}|{page}|{trim}|{angle:g}"
    digest = hashlib.sha1(identity.encode()).hexdigest()[:10]
    stem = Path(pdf_name).stem
    name = f"source-{stem}-p{page:03d}-{digest}.png"
    dest = FIG_ASSETS / name
    if dest.exists():
        return f"assets/figures/{name}"

    pdf = SOURCE / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    page_cache = BUILD / "source-pages" / f"{stem}-p{page:03d}.png"
    page_cache.parent.mkdir(parents=True, exist_ok=True)
    if not page_cache.exists():
        prefix = page_cache.with_suffix("")
        run([
            "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
            "-r", "170", "-png", str(pdf), str(prefix),
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
    td = BUILD / "tikz" / stem
    if td.exists():
        shutil.rmtree(td)
    td.mkdir(parents=True)
    tex = td / "figure.tex"
    tex.write_text(
        r"""\documentclass[border=5pt]{standalone}
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
"""
        + f"\\input{{{tikz.as_posix()}}}\n"
        + r"\endgroup\end{document}" + "\n"
    )
    run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "figure.tex"], cwd=td)
    tmp_svg = td / "figure.svg"
    run(["pdftocairo", "-svg", str(td / "figure.pdf"), str(tmp_svg)])
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
    print(f"Rendering {len(stems)} TikZ figures to SVG ({workers} workers)...")
    failures: list[tuple[str, BaseException]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(render_tikz_svg, stem): stem for stem in stems}
        for fut in as_completed(futs):
            stem = futs[fut]
            try:
                fut.result()
            except BaseException as exc:
                failures.append((stem, exc))
    if failures:
        for stem, exc in failures:
            print(f"TikZ render failed: {stem}: {exc}", file=sys.stderr)
        raise SystemExit(f"{len(failures)} TikZ figure render(s) failed")


def transform_tex(text: str) -> str:
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
        return rf"\includegraphics{{assets/figures/{m.group('stem')}.svg}}"

    text = VECTOR_RE.sub(vector_sub, text)
    text = TIKZ_INPUT_RE.sub(lambda m: rf"\includegraphics{{assets/figures/{m.group('stem')}.svg}}", text)

    def source_sub(m: re.Match[str]) -> str:
        rel = source_crop(m.group("pdf"), int(m.group("page")), m.group("trim"))
        return rf"\includegraphics{{{rel}}}"

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
    return text


def pandoc_page(source_tex: Path, output: Path, title: str) -> None:
    run([
        "pandoc", str(source_tex), "-f", "latex", "-t", "html5", "-s",
        "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        "--metadata", f"title={title}", "-o", str(output),
    ])


def inject_css_and_nav(page: Path, nav: str) -> None:
    text = page.read_text(errors="replace")
    if "assets/wave.css" not in text:
        text = text.replace("</head>", '<link rel="stylesheet" href="assets/wave.css" />\n</head>')
    text = text.replace("<body>", "<body>\n" + nav, 1)
    text = text.replace("</body>", nav + "\n</body>", 1)
    page.write_text(text)


def make_nav(index: int | None = None) -> str:
    links = ['<a href="index.html">Contents</a>']
    if index is not None and index > 1:
        links.append(f'<a href="chapter{index-1}.html">Previous chapter</a>')
    if index is not None and index < 6:
        links.append(f'<a href="chapter{index+1}.html">Next chapter</a>')
    if index == 6:
        links.append('<a href="references.html">References</a>')
    return '<nav class="book-nav" aria-label="Book navigation">' + " · ".join(links) + "</nav>"


def build_index(temp: Path) -> None:
    text = (RECON / "frontmatter-modern.tex").read_text()
    photo = RECON / "figures" / "frontmatter" / "salmon-hendershott-como-1980.jpeg"
    if photo.exists():
        photo_dest = ASSETS / photo.name
        shutil.copy2(photo, photo_dest)
        replacement = (
            r"\includegraphics{assets/salmon-hendershott-como-1980.jpeg}" + "\n\n"
            + "Rick Salmon (left) and Myrl Hendershott, Summer School on Lake Como, 1980, "
              "on solitons and predictability. Photograph by George.\n"
        )
        text = IF_PHOTO_RE.sub(lambda _: replacement, text)
    else:
        text = IF_PHOTO_RE.sub("", text)
    text = text.replace(r"\tableofcontents", "")
    src = temp / "frontmatter.tex"
    src.write_text(transform_tex(text))
    page = OUT / "index.html"
    pandoc_page(src, page, "Wave Motions in the Ocean: Myrl's View")
    downloads = []
    for filename, label in (
        ("wave-motions.pdf", "PDF"),
        ("wave-motions-facsimile.pdf", "Facsimile PDF"),
    ):
        if (OUT / filename).exists():
            downloads.append(f'<li><a href="{filename}">{label}</a></li>')
    download_html = (
        '<h2>Downloads</h2><ul>' + "".join(downloads) + '</ul>' if downloads else ""
    )
    toc = '<section class="book-toc"><h2>Contents</h2><ol>' + "".join(
        f'<li><a href="chapter{i}.html">Chapter {i}</a></li>' for i in range(1, 7)
    ) + '</ol><p><a href="references.html">References</a></p>' + download_html + '</section>'
    license_html = (
        '<p class="license">This work is licensed under '
        '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>'
        '<img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">'
        '<img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">'
        '<img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">'
        '<img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"></p>'
    )
    html_text = page.read_text(errors="replace")
    html_text = html_text.replace("</body>", toc + "\n" + license_html + "\n</body>")
    page.write_text(html_text)
    inject_css_and_nav(page, make_nav(None))


def build_references(temp: Path) -> None:
    md = temp / "references.md"
    md.write_text("---\ntitle: References\nnocite: |\n  @*\n---\n")
    page = OUT / "references.html"
    run([
        "pandoc", str(md), "-s", "-t", "html5", "--citeproc",
        f"--bibliography={RECON / 'references.bib'}", "-o", str(page),
    ])
    nav = '<nav class="book-nav" aria-label="Book navigation"><a href="index.html">Contents</a> · <a href="chapter6.html">Previous chapter</a></nav>'
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
.book-nav { margin: 0 0 2rem; padding: .75rem 0; border-bottom: 1px solid #bbb; }
.book-nav + header { margin-top: 1rem; }
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
        src.write_text(transform_tex((RECON / f"chapter{i}.tex").read_text()))
        page = OUT / f"chapter{i}.html"
        pandoc_page(src, page, f"Wave Motions in the Ocean — Chapter {i}")
        inject_css_and_nav(page, make_nav(i))
    build_references(temp)
    validate()
    print("HTML build OK: index + 6 chapters + references; generated from canonical LaTeX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
