#!/usr/bin/env python3
"""Generate local visual/render QA artifacts for the published book outputs.

The script is intentionally a developer aid rather than a release gate. It can
inspect a built ``release/`` publication root or an artifact ZIP, render both PDFs
into contact sheets, perform static/optional-browser HTML checks, unpack and inspect
EPUB structure, and write a single Markdown report under ``audit/render-qa``.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import http.server
import os
import re
import shutil
import socket
import subprocess
import threading
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "audit" / "render-qa"
EXPECTED_HTML = [
    "index.html",
    *(f"chapter{i}.html" for i in range(1, 7)),
    "references.html",
]
FACSIMILE_EXPECTED_PAGES = 184
MATHJAX_RENDERER_RE = re.compile(
    r'<span\b(?=[^>]*\bdata-math-renderer="mathjax")[^>]*>.*?</span>',
    re.DOTALL | re.IGNORECASE,
)
MATHML_RENDERER_RE = re.compile(
    r'<span\b(?=[^>]*\bdata-math-renderer="mathml")[^>]*>.*?</span>',
    re.DOTALL | re.IGNORECASE,
)
MATHML_ANNOTATION_RE = re.compile(
    r'<annotation\b[^>]*\bencoding="application/x-tex"[^>]*>(.*?)</annotation>',
    re.DOTALL | re.IGNORECASE,
)
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
MATH_PARITY_TEXT_SIZES = ("50%", "100%", "200%")
MATH_PARITY_VIEWPORTS = ((390, 844), (768, 1000), (1440, 1200))
MATHML_COMPARISON_ROUTE = "/__render-qa__/mathml-mathjax-comparison.html"
READER_REGRESSION_ROUTE = "/__render-qa__/reader-regressions.html"
READER_VISUAL_ROUTE = "/__render-qa__/reader-visual.html"
CHAPTER5_BOUNDARY_RE = re.compile(r"&&\\text\{(?:at|as)\}z=", re.IGNORECASE)


@dataclass
class Finding:
    level: str
    area: str
    message: str


@dataclass
class Report:
    source: str
    source_root: Path
    out: Path
    findings: list[Finding] = field(default_factory=list)
    sections: list[tuple[str, list[str]]] = field(default_factory=list)

    def add(self, level: str, area: str, message: str) -> None:
        self.findings.append(Finding(level, area, message))

    def section(self, title: str, lines: Iterable[str]) -> None:
        self.sections.append((title, list(lines)))


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


def need(cmd: str) -> str | None:
    return shutil.which(cmd)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_input(source: Path, out: Path) -> Path:
    if source.is_dir():
        return source.resolve()
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise SystemExit(
            f"QA input must be a publication directory or ZIP artifact: {source}"
        )
    extracted = out / "input"
    shutil.rmtree(extracted, ignore_errors=True)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(source) as archive:
        archive.extractall(extracted)
    children = [p for p in extracted.iterdir() if p.is_dir()]
    if len(children) == 1 and all(
        (children[0] / name).exists() for name in ("wave-motions.pdf", "index.html")
    ):
        return children[0]
    if all((extracted / name).exists() for name in ("wave-motions.pdf", "index.html")):
        return extracted
    raise SystemExit("could not locate a publication root inside the ZIP")


def pdf_page_count(pdf: Path) -> int:
    proc = run(["pdfinfo", str(pdf)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"pdfinfo did not report a page count for {pdf}")
    return int(match.group(1))


def render_pdf_pages(pdf: Path, dest: Path, dpi: int) -> list[Path]:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    prefix = dest / "page"
    run(
        [
            "pdftoppm",
            "-r",
            str(dpi),
            "-jpeg",
            "-jpegopt",
            "quality=84",
            str(pdf),
            str(prefix),
        ],
        timeout=300,
    )
    pages = sorted(dest.glob("page-*.jpg"))
    if not pages:
        raise RuntimeError(f"no page renders produced for {pdf}")
    return pages


def ink_coverage(path: Path) -> float:
    with Image.open(path) as image:
        gray = image.convert("L")
        gray.thumbnail((170, 220))
        hist = gray.histogram()
        ink = sum(hist[:245])
        return ink / max(1, sum(hist))


def make_contact_sheets(
    pages: list[Path],
    dest: Path,
    *,
    cols: int = 4,
    rows: int = 4,
    thumb_width: int = 230,
) -> list[Path]:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    per_sheet = cols * rows
    sheets: list[Path] = []
    for start in range(0, len(pages), per_sheet):
        batch = pages[start : start + per_sheet]
        thumbs: list[Image.Image] = []
        max_height = 0
        for offset, path in enumerate(batch):
            with Image.open(path) as source:
                image = source.convert("RGB")
            height = round(image.height * thumb_width / image.width)
            image = image.resize((thumb_width, height))
            canvas = Image.new("RGB", (thumb_width, height + 22), "white")
            canvas.paste(image, (0, 22))
            ImageDraw.Draw(canvas).text(
                (4, 4), f"PDF {start + offset + 1}", fill="black"
            )
            thumbs.append(canvas)
            max_height = max(max_height, canvas.height)
        sheet = Image.new(
            "RGB", (cols * thumb_width, rows * max_height), (225, 225, 225)
        )
        for i, thumb in enumerate(thumbs):
            sheet.paste(thumb, ((i % cols) * thumb_width, (i // cols) * max_height))
        path = dest / f"sheet-{start + 1:03d}-{start + len(batch):03d}.jpg"
        sheet.save(path, quality=88, optimize=True)
        sheets.append(path)
    return sheets


def pdf_qa(dist: Path, report: Report, dpi: int) -> None:
    if not need("pdfinfo") or not need("pdftoppm"):
        report.add("ERROR", "PDF", "pdfinfo/pdftoppm are required for render QA")
        return
    lines: list[str] = []
    for kind, filename in (
        ("modern", "wave-motions.pdf"),
        ("facsimile", "wave-motions-facsimile.pdf"),
    ):
        pdf = dist / filename
        if not pdf.is_file():
            report.add("ERROR", "PDF", f"missing {filename}")
            continue
        pages = pdf_page_count(pdf)
        lines.append(
            f"- **{kind.title()} PDF:** {pages} pages; `{filename}`; "
            f"SHA-256 `{sha256(pdf)[:16]}…`"
        )
        if kind == "facsimile" and pages != FACSIMILE_EXPECTED_PAGES:
            report.add(
                "WARNING",
                "PDF",
                f"facsimile is {pages} pages; expected {FACSIMILE_EXPECTED_PAGES}. "
                "This is release-blocking even though active-development CI treats it as a warning.",
            )
        renders = render_pdf_pages(pdf, report.out / "pdf" / kind / "pages", dpi)
        sheets = make_contact_sheets(
            renders, report.out / "pdf" / kind / "contact-sheets"
        )
        coverage = [ink_coverage(path) for path in renders]
        near_blank = [i + 1 for i, value in enumerate(coverage) if value < 0.0025]
        sparse = [i + 1 for i, value in enumerate(coverage) if 0.0025 <= value < 0.008]
        lines.append(
            f"  - Contact sheets: "
            f"`{(report.out / 'pdf' / kind / 'contact-sheets').relative_to(report.out)}/` "
            f"({len(sheets)} sheets at {dpi} dpi source renders)"
        )
        if near_blank:
            lines.append(
                f"  - Near-blank physical pages (<0.25% ink): "
                f"{', '.join(map(str, near_blank))}"
            )
        if sparse:
            lines.append(
                f"  - Sparse physical pages (0.25–0.8% ink): "
                f"{', '.join(map(str, sparse[:30]))}"
                f"{' …' if len(sparse) > 30 else ''}"
            )
        if len(renders) != pages:
            report.add(
                "ERROR",
                "PDF",
                f"{kind} rendered {len(renders)} pages but pdfinfo reports {pages}",
            )
    report.section("PDF render audit", lines)


def html_local_refs(page: Path) -> list[str]:
    text = page.read_text(errors="replace")
    broken: list[str] = []
    for attr in ("src", "href", "data-vector-src", "data-original-src"):
        for ref in re.findall(
            rf'{attr}=["\']([^"\']+)["\']', text, flags=re.IGNORECASE
        ):
            if ref.startswith(
                ("http:", "https:", "mailto:", "#", "javascript:", "data:")
            ):
                continue
            path = urllib.parse.unquote(ref.split("#", 1)[0].split("?", 1)[0])
            if path and not (page.parent / path).exists():
                broken.append(ref)
    return broken


FIGURE_BLOCK_RE = re.compile(
    r'<figure class="wave-figure(?: [^"]+)?"[^>]*>.*?</figure>',
    re.DOTALL,
)
FIGURE_IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
FIGURE_TOGGLE_RE = re.compile(
    r"<button\b[^>]*\bdata-figure-toggle\b[^>]*>(.*?)</button>",
    re.DOTALL | re.IGNORECASE,
)
FIGURE_CONTROL_RE = re.compile(
    r"<button\b[^>]*\bdata-figure-cycle\b[^>]*>(.*?)</button>",
    re.DOTALL | re.IGNORECASE,
)
FIGURE_LABEL_VALUE_RE = re.compile(
    r"<span\b[^>]*\bdata-figure-label\b[^>]*>(.*?)</span>",
    re.DOTALL | re.IGNORECASE,
)


def figure_html_qa(dist: Path, report: Report, lines: list[str]) -> None:
    """Check generated vector/source figure structure for render QA."""
    switchable = 0
    for name in EXPECTED_HTML:
        page = dist / name
        text = page.read_text(errors="replace")
        blocks = FIGURE_BLOCK_RE.findall(text)
        page_switchable = 0
        for block in blocks:
            images = FIGURE_IMAGE_RE.findall(block)
            if len(images) != 1 or block.count("<figcaption>") != 1:
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: figure must contain one image and one caption",
                )
                continue
            image = images[0]
            if not re.search(r'\balt="[^"]*"', image, re.IGNORECASE):
                report.add("ERROR", "HTML", f"{name}: figure image is missing alt text")
            if "wave-figure-switchable" not in block:
                if "data-figure" in block or "figure-view-toggle" in block:
                    report.add(
                        "ERROR",
                        "HTML",
                        f"{name}: unswitchable figure exposes a switch control",
                    )
                continue
            page_switchable += 1
            source = re.search(r'\bsrc="([^"]+)"', image)
            vector = re.search(r'\bdata-vector-src="([^"]+)"', block)
            original = re.search(r'\bdata-original-src="([^"]+)"', block)
            if not source or not vector or not original:
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: switchable figure is missing its single paired image",
                )
                continue
            if source.group(1) != original.group(1) or not original.group(1).endswith(
                ".png"
            ):
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: switchable figure does not default to its original PNG",
                )
            if Path(vector.group(1)).stem != Path(original.group(1)).stem:
                report.add(
                    "ERROR", "HTML", f"{name}: switchable figure changes its asset stem"
                )
            vector_path = dist / vector.group(1)
            original_path = dist / original.group(1)
            if not vector_path.is_file() or not original_path.is_file():
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: switchable figure asset is missing",
                )
            toggles = FIGURE_TOGGLE_RE.findall(block)
            toggle_text = (
                re.sub(r"<[^>]+>", "", toggles[0]).strip() if len(toggles) == 1 else ""
            )
            if len(toggles) != 1 or toggle_text != "Switch to Vector":
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: switchable figure initial local action is not Switch to Vector",
                )
            if 'aria-label="Switch to reconstructed vector figure"' not in block:
                report.add(
                    "ERROR",
                    "HTML",
                    f"{name}: switchable figure has the wrong initial action label",
                )
        controls = FIGURE_CONTROL_RE.findall(text)
        control_labels = (
            FIGURE_LABEL_VALUE_RE.findall(controls[0]) if len(controls) == 1 else []
        )
        control_label = (
            re.sub(r"<[^>]+>", "", control_labels[0]).strip()
            if len(control_labels) == 1
            else ""
        )
        if (
            len(controls) != 1
            or text.count("data-figure-cycle") != 1
            or text.count("data-figure-label") != 1
            or control_label != "Original"
            or 'aria-label="Default figure rendering: Original"' not in text
        ):
            report.add(
                "ERROR",
                "HTML",
                f"{name}: global figure rendering preference is missing or malformed",
            )
        switchable += page_switchable

    source_pngs = sorted(
        path
        for path in (dist / "assets" / "figures").glob("*.png")
        if (dist / "assets" / "figures" / f"{path.stem}.svg").is_file()
    )
    total_size = sum(path.stat().st_size for path in source_pngs)
    largest = max((path.stat().st_size for path in source_pngs), default=0)
    lines.append(
        f"- Switchable HTML figures: {switchable}; source-backed PNGs: "
        f"{len(source_pngs)}; total source-PNG size: {total_size:,} bytes; "
        f"largest: {largest:,} bytes"
    )


def detect_browser(explicit: str | None) -> str | None:
    explicit = explicit or os.environ.get("WAVE_CHROMIUM")
    if explicit:
        return explicit if Path(explicit).exists() else shutil.which(explicit)
    for command in (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
        "msedge",
    ):
        found = shutil.which(command)
        if found:
            return found
    return None


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class RenderQAHandler(QuietHandler):
    """Serve audit-only pages alongside the inspected publication root."""

    def __init__(
        self,
        *args,
        qa_pages: Mapping[str, Path] | None = None,
        **kwargs,
    ) -> None:
        self.qa_pages = dict(qa_pages or {})
        super().__init__(*args, **kwargs)

    def translate_path(self, path: str) -> str:
        route = urllib.parse.urlsplit(path).path
        audit_page = self.qa_pages.get(route)
        if audit_page is not None:
            return str(audit_page)
        return super().translate_path(path)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def local_server(root: Path, *, qa_pages: Mapping[str, Path] | None = None):
    port = free_port()
    handler = lambda *args, **kwargs: RenderQAHandler(
        *args,
        directory=str(root),
        qa_pages=qa_pages,
        **kwargs,
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def browser_screenshot(
    browser: str,
    url: str,
    dest: Path,
    width: int,
    height: int,
    *,
    force_dark: bool = False,
) -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--disable-component-update",
        "--hide-scrollbars",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=3500",
        f"--window-size={width},{height}",
        f"--screenshot={dest}",
    ]
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--no-sandbox")
    if force_dark:
        cmd.append("--force-dark-mode")
    cmd.append(url)
    try:
        proc = run(cmd, timeout=25, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    ok = proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 0
    return ok, proc.stdout[-2000:]


def browser_dump_dom(
    browser: str,
    url: str,
    width: int = 1440,
    height: int = 1000,
) -> tuple[bool, str]:
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--disable-component-update",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=3500",
        f"--window-size={width},{height}",
        "--dump-dom",
    ]
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--no-sandbox")
    cmd.append(url)
    try:
        proc = run(cmd, timeout=25, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    ok = proc.returncode == 0 and "<html" in proc.stdout.lower()
    return ok, proc.stdout


def first_section_case(page: Path) -> tuple[str, str] | None:
    text = page.read_text(errors="replace")
    links = re.findall(
        r'<a\b[^>]*\bdata-section-link=["\']([^"\']+)["\'][^>]*>',
        text,
        flags=re.IGNORECASE,
    )
    for section_id in links:
        match = re.search(
            rf'<h2\b[^>]*\bid=["\']{re.escape(section_id)}["\'][^>]*>(.*?)</h2>',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not match:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", match.group(1)))
        return section_id, " ".join(title.split())
    return None


def fragment_reader_context_ok(dom: str, section_id: str, title: str) -> bool:
    active = re.search(
        rf'<a\b(?=[^>]*\bdata-section-link=["\']{re.escape(section_id)}["\'])'
        rf'(?=[^>]*\baria-current=["\']location["\'])[^>]*>',
        dom,
        flags=re.IGNORECASE,
    )
    context = re.search(
        r'<[^>]*\bclass=["\'][^"\']*\breader-context-title\b[^"\']*["\'][^>]*>'
        r"(.*?)</[^>]+>",
        dom,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not active or not context:
        return False
    context_text = html.unescape(re.sub(r"<[^>]+>", "", context.group(1)))
    return " ".join(context_text.split()) == title


def math_parity_jobs(
    route: str = MATHML_COMPARISON_ROUTE,
) -> list[tuple[str, str, int, int, bool]]:
    return [
        (
            f"math-parity-{width}-{text_size.replace('%', '')}.png",
            f"{route}?{urllib.parse.urlencode({'text-size': text_size})}",
            width,
            height,
            False,
        )
        for width, height in MATH_PARITY_VIEWPORTS
        for text_size in MATH_PARITY_TEXT_SIZES
    ]


def mathml_table_width(markup: str) -> int:
    try:
        root = ET.fromstring(markup)
    except ET.ParseError:
        return 0
    table = root.find(f".//{{{MATHML_NS}}}mtable")
    if table is None:
        return 0
    return max(
        (
            len(row.findall(f"{{{MATHML_NS}}}mtd"))
            for row in table.findall(f"{{{MATHML_NS}}}mtr")
        ),
        default=0,
    )


def is_chapter5_boundary_alignment(pair: dict[str, object]) -> bool:
    source = re.sub(r"\s+", "", str(pair["source"]))
    return (
        pair["page"] == "chapter5.html"
        and pair["kind"] == "display"
        and r"\begin{aligned}" in source
        and len(CHAPTER5_BOUNDARY_RE.findall(source)) >= 2
    )


def mathml_comparison_specimen(
    dist: Path, report: Report
) -> tuple[Path | None, list[str]]:
    """Write a side-by-side page from actual paired book math fragments."""
    pairs: list[dict[str, object]] = []
    for name in EXPECTED_HTML:
        text = (dist / name).read_text(errors="replace")
        mathjax = list(MATHJAX_RENDERER_RE.finditer(text))
        mathml = list(MATHML_RENDERER_RE.finditer(text))
        if len(mathjax) != len(mathml):
            report.add(
                "ERROR",
                "HTML",
                f"{name}: MathJax/MathML pair count differs in render-QA specimen "
                f"({len(mathjax)} != {len(mathml)})",
            )
            continue
        for index, (mathjax_match, mathml_match) in enumerate(
            zip(mathjax, mathml, strict=True), start=1
        ):
            annotation = MATHML_ANNOTATION_RE.search(mathml_match.group(0))
            if annotation is None:
                continue
            class_match = re.search(
                r'class="math\s+(inline|display)', mathjax_match.group(0)
            )
            if class_match is None:
                continue
            tail = text[mathml_match.end() : mathml_match.end() + 500]
            pairs.append(
                {
                    "page": name,
                    "index": index,
                    "kind": class_match.group(1),
                    "source": html.unescape(annotation.group(1)),
                    "mathjax": re.sub(
                        r"\s+hidden(?=[\s>])", "", mathjax_match.group(0), count=1
                    ),
                    "mathml": mathml_match.group(0),
                    "width": mathml_table_width(mathml_match.group(0)),
                    "numbered": bool(
                        re.search(
                            r"<div class=\"flushright\">.*?\(\d+\.\d+\)",
                            tail,
                            re.DOTALL,
                        )
                    ),
                }
            )

    if not pairs:
        report.add(
            "ERROR", "HTML", "no paired mathematics available for render-QA specimen"
        )
        return None, []

    selected: list[tuple[str, dict[str, object]]] = []
    selected_ids: set[tuple[str, int]] = set()

    def choose(label: str, predicate) -> bool:
        for pair in pairs:
            identity = (str(pair["page"]), int(pair["index"]))
            if identity in selected_ids or not predicate(pair):
                continue
            selected.append((label, pair))
            selected_ids.add(identity)
            return True
        return False

    def choose_if_present(label: str, predicate, requirement: str) -> None:
        available = any(predicate(pair) for pair in pairs)
        if available and not choose(label, predicate):
            report.add("ERROR", "HTML", requirement)

    choose("Simple inline", lambda pair: pair["kind"] == "inline")
    chapter5_boundary = next(
        (pair for pair in pairs if is_chapter5_boundary_alignment(pair)), None
    )
    if chapter5_boundary is None:
        report.add(
            "ERROR",
            "HTML",
            "required Chapter 5 trailing-boundary alignment is missing from the "
            "MathML/MathJax render-QA specimen",
        )
    else:
        choose("Chapter 5 boundary align", is_chapter5_boundary_alignment)
        identity = (str(chapter5_boundary["page"]), int(chapter5_boundary["index"]))
        if identity not in selected_ids:
            report.add(
                "ERROR",
                "HTML",
                "required Chapter 5 trailing-boundary alignment could not be "
                "selected for the MathML/MathJax render-QA specimen",
            )
    choose(
        "Simple display",
        lambda pair: (
            pair["kind"] == "display"
            and not str(pair["source"]).lstrip().startswith(r"\begin")
            and pair["width"] == 0
        ),
    )
    choose(
        "Fraction",
        lambda pair: (
            pair["kind"] == "display"
            and (r"\frac" in str(pair["source"]) or "<mfrac" in str(pair["mathml"]))
        ),
    )
    root_pair = next(
        (
            pair
            for pair in pairs
            if pair["kind"] == "display"
            and (r"\sqrt" in str(pair["source"]) or "<msqrt" in str(pair["mathml"]))
        ),
        None,
    )
    if root_pair is not None:
        choose("Root", lambda pair, root_pair=root_pair: pair is root_pair)
    choose_if_present(
        "Ordinary align",
        lambda pair: (
            pair["kind"] == "display"
            and r"\begin{aligned}" in str(pair["source"])
            and r"&&" not in str(pair["source"])
            and pair["width"] == 2
        ),
        "ordinary multi-line aligned math could not be selected for the required "
        "MathML/MathJax render-QA specimen",
    )
    choose_if_present(
        "Multi-pair aligned",
        lambda pair: (
            pair["kind"] == "display"
            and r"\begin{aligned}" in str(pair["source"])
            and pair["width"] >= 4
        ),
        "multi-pair aligned math could not be selected for the required "
        "MathML/MathJax render-QA specimen",
    )
    choose_if_present(
        "Cases/array",
        lambda pair: (
            r"\begin{cases}" in str(pair["source"])
            or r"\begin{array}" in str(pair["source"])
        ),
        "cases/array math could not be selected for the MathML/MathJax "
        "render-QA specimen",
    )
    choose_if_present(
        "Numbered wavealign",
        lambda pair: (
            bool(pair["numbered"]) and r"\begin{aligned}" in str(pair["source"])
        ),
        "numbered aligned math could not be selected for the required "
        "MathML/MathJax render-QA specimen",
    )
    longest_display = max(
        (pair for pair in pairs if pair["kind"] == "display"),
        key=lambda pair: len(str(pair["source"])),
        default=None,
    )
    if longest_display is not None:
        choose(
            "Longest display",
            lambda pair, longest_display=longest_display: pair is longest_display,
        )

    if root_pair is None:
        report.add(
            "INFO",
            "HTML",
            "MathML/MathJax specimen: no square-root/root construct occurs in the book source",
        )

    comparison_rows = []
    for label, pair in selected:
        source = html.escape(str(pair["source"]))
        page = html.escape(str(pair["page"]))
        index = html.escape(str(pair["index"]))
        mathjax = str(pair["mathjax"])
        mathml = str(pair["mathml"])
        comparison_rows.append(
            '<section class="comparison-case">'
            f"<h2>{html.escape(label)}</h2>"
            f'<p class="case-meta">{page}, expression {index}</p>'
            '<div class="comparison-grid">'
            f'<div class="renderer-cell"><h3>MathJax</h3>{mathjax}</div>'
            f'<div class="renderer-cell"><h3>Native MathML</h3>{mathml}</div>'
            "</div>"
            f"<details><summary>TeX annotation</summary><code>{source}</code></details>"
            "</section>"
        )

    page = report.out / "html" / "mathml-mathjax-comparison.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "<!doctype html>\n"
        '<html lang="en-US"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<script>"
        "const textSizePercentages = new Set(['50%', '100%', '200%']);"
        "const requestedTextSize = new URLSearchParams(location.search).get('text-size');"
        "if (textSizePercentages.has(requestedTextSize)) {"
        "const numericTextSize = Number.parseInt(requestedTextSize, 10);"
        "document.documentElement.style.setProperty('--wave-text-scale', String(numericTextSize / 100));"
        "}"
        "</script>"
        "<title>MathJax and native MathML comparison</title>"
        '<link rel="stylesheet" href="/assets/wave.css">'
        "<style>"
        ".comparison-case{border-top:1px solid #999;padding:1rem 0 1.5rem;}"
        ".case-meta{color:#666;margin:.2rem 0 .8rem;}"
        ".comparison-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;}"
        ".renderer-cell{border:1px solid #bbb;padding:.8rem;min-width:0;overflow-x:auto;}"
        ".renderer-cell h3{font:600 1rem/1.2 sans-serif;margin:0 0 .8rem;}"
        ".renderer-cell .math.display{padding:1rem 0;}"
        ".renderer-cell code{white-space:pre-wrap;}"
        "@media(max-width:700px){.comparison-grid{grid-template-columns:1fr;}}"
        "</style>"
        '<script src="/assets/mathjax/tex-chtml-full.js"></script>'
        '</head><body><main id="main-content"><h1>MathJax and native MathML comparison</h1>'
        "<p>Each case is taken from the generated book HTML. MathJax is on the left; native MathML is on the right.</p>"
        + "".join(comparison_rows)
        + "</main></body></html>\n"
    )
    return page, [label for label, _ in selected]


def html_qa(dist: Path, report: Report, browser: str | None) -> None:
    lines: list[str] = []
    missing = [name for name in EXPECTED_HTML if not (dist / name).is_file()]
    if missing:
        report.add("ERROR", "HTML", "missing pages: " + ", ".join(missing))
        return
    broken_all: list[str] = []
    titles: dict[str, str] = {}
    external_runtime: list[str] = []
    for name in EXPECTED_HTML:
        page = dist / name
        text = page.read_text(errors="replace")
        match = re.search(
            r"<title>(.*?)</title>", text, flags=re.DOTALL | re.IGNORECASE
        )
        titles[name] = (
            re.sub(r"\s+", " ", match.group(1)).strip() if match else "<missing>"
        )
        broken = html_local_refs(page)
        broken_all.extend(f"{name}: {ref}" for ref in broken)
        if 'name="viewport"' not in text and "name='viewport'" not in text:
            report.add("WARNING", "HTML", f"{name} has no viewport meta tag")
        external_runtime.extend(
            re.findall(
                r'<(?:script|link)\b[^>]*(?:src|href)=["\'](https?://[^"\']+)["\'][^>]*>',
                text,
                flags=re.IGNORECASE,
            )
        )
    if broken_all:
        report.add(
            "ERROR",
            "HTML",
            f"{len(broken_all)} broken local reference(s); first: {broken_all[0]}",
        )
    figure_html_qa(dist, report, lines)
    lines.append("- Browser titles:")
    lines.extend(f"  - `{name}` → `{title}`" for name, title in titles.items())
    css = dist / "assets" / "wave.css"
    js = dist / "assets" / "wave.js"
    if css.is_file():
        css_text = css.read_text(errors="replace")
        lines.append(
            f"- CSS includes mobile breakpoint: "
            f"{'yes' if '@media (max-width: 700px)' in css_text else 'no'}"
        )
        lines.append(
            f"- CSS includes dark-theme rules: "
            f"{'yes' if 'prefers-color-scheme: dark' in css_text else 'no'}"
        )
        inline_math_rule = re.search(
            r"\.math\.inline\s*\{(?P<body>[^}]*)\}",
            css_text,
            flags=re.DOTALL,
        )
        inline_math_css = inline_math_rule.group("body") if inline_math_rule else ""
        if (
            inline_math_rule is None
            or "display: inline" not in inline_math_css
            or "overflow: visible" not in inline_math_css
            or re.search(r"overflow(?:-x)?\s*:\s*(?:auto|scroll)", inline_math_css)
        ):
            report.add(
                "ERROR",
                "HTML",
                "inline mathematics is missing its normal-flow overflow invariant",
            )
        else:
            lines.append("- Inline mathematics normal-flow overflow invariant: yes")
        if re.search(r"url\(\s*['\"]?https?://", css_text, flags=re.IGNORECASE):
            external_runtime.append("external CSS url()")
    else:
        report.add("ERROR", "HTML", "missing assets/wave.css")
    if not js.is_file():
        report.add("ERROR", "HTML", "missing assets/wave.js")

    required_runtime_assets = [
        dist / "assets" / "mathjax" / "tex-chtml-full.js",
        dist / "assets" / "mathjax" / "output" / "chtml" / "fonts" / "woff-v2",
        dist / "assets" / "fonts" / "SourceSerif4Variable-Roman.otf.woff2",
        dist / "assets" / "fonts" / "SourceSans3VF-Upright.otf.woff2",
    ]
    missing_runtime = [path for path in required_runtime_assets if not path.exists()]
    if missing_runtime:
        report.add(
            "ERROR",
            "HTML",
            "missing local runtime asset(s): "
            + ", ".join(str(path.relative_to(dist)) for path in missing_runtime),
        )
    else:
        lines.append("- Runtime MathJax and web-font assets are local: yes")
    if external_runtime:
        report.add(
            "ERROR",
            "HTML",
            "required script/style runtime references an external network resource: "
            f"{external_runtime[0]}",
        )
    else:
        lines.append("- Required script/style network dependencies: none detected")

    specimen_page, specimen_labels = mathml_comparison_specimen(dist, report)
    if specimen_page is not None:
        specimen_rel = specimen_page.relative_to(report.out)
        lines.append(
            "- MathJax/native MathML comparison specimen: "
            f"`{specimen_rel}` ({', '.join(specimen_labels)})"
        )
        lines.append(
            "- Math parity screenshot matrix: 390px, 768px, and 1440px at "
            "50%/100%/200% text size (9 jobs)"
        )

    if browser:
        lines.append(f"- Headless browser detected: `{browser}`")
        screenshots = report.out / "html" / "screenshots"
        qa_pages = (
            {MATHML_COMPARISON_ROUTE: specimen_page}
            if specimen_page is not None
            else {}
        )
        qa_pages[READER_REGRESSION_ROUTE] = reader_regression_specimen(report)
        jobs = []
        browser_reader_visual_jobs(report, qa_pages, jobs)
        fragment_case = first_section_case(dist / "chapter4.html")
        if fragment_case is not None:
            section_id, _section_title = fragment_case
            fragment_wrapper = report.out / "html" / "fragment-chapter4.html"
            fragment_wrapper.write_text(
                "<!doctype html><html><head>"
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                "<style>html,body,iframe{width:100%;height:100%;margin:0;border:0;display:block;overflow:hidden}</style>"
                "</head><body>"
                f'<iframe src="/chapter4.html#{urllib.parse.quote(section_id)}" title="Fragment QA"></iframe>'
                "</body></html>"
            )
            qa_pages["/__render-qa__/fragment-chapter4.html"] = fragment_wrapper
        with local_server(dist, qa_pages=qa_pages) as base:
            for name in EXPECTED_HTML:
                jobs.append((f"desktop-{Path(name).stem}.png", name, 1440, 1000, False))
                jobs.append((f"mobile-{Path(name).stem}.png", name, 390, 844, False))
            jobs.append(("toolbar-320-chapter2.png", "chapter2.html", 320, 844, False))
            jobs.append(("dark-chapter4.png", "chapter4.html", 390, 844, True))
            if fragment_case is not None:
                for width, height in (
                    (360, 844),
                    (390, 844),
                    (430, 900),
                    (768, 1000),
                    (1440, 1000),
                ):
                    jobs.append(
                        (
                            f"fragment-chapter4-{width}.png",
                            "__render-qa__/fragment-chapter4.html",
                            width,
                            height,
                            False,
                        )
                    )
                for width, height in ((360, 844), (390, 844), (430, 900)):
                    for mode in ("mathml", "mathjax"):
                        jobs.append(
                            (
                                f"renderer-{mode}-{width}.png",
                                f"chapter4.html?math={mode}",
                                width,
                                height,
                                False,
                            )
                        )
            if specimen_page is not None:
                jobs.extend(math_parity_jobs())
            failures = 0
            completed = 0
            for output_name, page_name, width, height, dark in jobs:
                ok, detail = browser_screenshot(
                    browser,
                    f"{base}/{page_name.lstrip('/')}",
                    screenshots / output_name,
                    width,
                    height,
                    force_dark=dark,
                )
                if not ok:
                    failures += 1
                    (screenshots / f"{output_name}.log.txt").write_text(detail)
                    if completed == 0:
                        break
                else:
                    completed += 1
            if failures:
                report.add(
                    "WARNING",
                    "HTML",
                    "headless screenshot generation failed after "
                    f"{completed} successful case(s); see logs and run the manual browser matrix",
                )
            else:
                lines.append(
                    f"- Browser screenshots: `{screenshots.relative_to(report.out)}/` "
                    f"({len(jobs)} cases)"
                )
                lines.append(
                    "- Reader visual screenshot matrix: 390px, 768px, and 1440px "
                    "at 50%/100%/200% in light mode plus 100% in dark mode"
                )

            if fragment_case is None:
                report.add(
                    "ERROR",
                    "HTML",
                    "could not identify a Chapter 4 section for fragment-navigation QA",
                )
            else:
                section_id, section_title = fragment_case
                ok, dom = browser_dump_dom(
                    browser,
                    f"{base}/chapter4.html#{urllib.parse.quote(section_id)}",
                )
                if not ok:
                    report.add(
                        "WARNING",
                        "HTML",
                        "headless DOM dump failed; direct-fragment reader-context regression check skipped",
                    )
                elif not fragment_reader_context_ok(dom, section_id, section_title):
                    report.add(
                        "ERROR",
                        "HTML",
                        "direct section permalink did not initialize both reader context and active Contents state",
                    )
                else:
                    lines.append(
                        f"- Direct-fragment reader context: PASS (`chapter4.html#{section_id}`)"
                    )
            browser_reader_regressions(browser, base, report, lines)
    else:
        report.add(
            "INFO",
            "HTML",
            "no Chrome/Chromium executable found; browser screenshot and fragment-regression QA skipped",
        )

    report.section("HTML render audit", lines)


def find_epubcheck() -> list[str] | None:
    command = shutil.which("epubcheck")
    if command:
        return [command]
    jar = os.environ.get("EPUBCHECK_JAR")
    if jar and Path(jar).is_file() and shutil.which("java"):
        return ["java", "-jar", jar]
    return None


def epub_qa(dist: Path, report: Report) -> None:
    epub = dist / "wave-motions.epub"
    if not epub.is_file():
        report.add("ERROR", "EPUB", "missing wave-motions.epub")
        return
    dest = report.out / "epub" / "unpacked"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    lines: list[str] = [
        (
            f"- `wave-motions.epub`; SHA-256 `{sha256(epub)[:16]}…`; unpacked to "
            f"`{dest.relative_to(report.out)}/`"
        )
    ]
    try:
        with zipfile.ZipFile(epub) as archive:
            names = archive.namelist()
            if not names or names[0] != "mimetype":
                report.add("ERROR", "EPUB", "mimetype is not the first ZIP entry")
            elif archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
                report.add(
                    "ERROR",
                    "EPUB",
                    "mimetype entry is compressed; EPUB requires it stored",
                )
            if archive.read("mimetype") != b"application/epub+zip":
                report.add("ERROR", "EPUB", "invalid mimetype payload")
            archive.extractall(dest)
    except (zipfile.BadZipFile, KeyError) as exc:
        report.add("ERROR", "EPUB", f"invalid EPUB ZIP: {exc}")
        return

    container = dest / "META-INF" / "container.xml"
    try:
        root = ET.parse(container).getroot()
        ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile = root.find(".//c:rootfile", ns)
        opf_rel = (
            rootfile.attrib["full-path"] if rootfile is not None else "EPUB/content.opf"
        )
    except (ET.ParseError, OSError, KeyError, AttributeError) as exc:
        report.add("ERROR", "EPUB", f"cannot parse container.xml: {exc}")
        return
    opf = dest / opf_rel
    try:
        opf_root = ET.parse(opf).getroot()
    except ET.ParseError as exc:
        report.add("ERROR", "EPUB", f"invalid OPF XML: {exc}")
        return
    ns = {
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    titles = [
        " ".join("".join(node.itertext()).split())
        for node in opf_root.findall(".//dc:title", ns)
    ]
    creators = [
        " ".join("".join(node.itertext()).split())
        for node in opf_root.findall(".//dc:creator", ns)
    ]
    contributors = [
        " ".join("".join(node.itertext()).split())
        for node in opf_root.findall(".//dc:contributor", ns)
    ]
    languages = [
        " ".join("".join(node.itertext()).split())
        for node in opf_root.findall(".//dc:language", ns)
    ]
    manifest = {
        node.attrib.get("id", ""): node.attrib
        for node in opf_root.findall(".//opf:manifest/opf:item", ns)
    }
    spine = [
        node.attrib.get("idref", "")
        for node in opf_root.findall(".//opf:spine/opf:itemref", ns)
    ]
    xhtml_paths = [
        opf.parent / item["href"]
        for item in manifest.values()
        if item.get("media-type") == "application/xhtml+xml"
    ]
    math_count = 0
    media_ref_count = 0
    for path in xhtml_paths:
        if not path.is_file():
            report.add(
                "ERROR", "EPUB", f"manifest XHTML missing: {path.relative_to(dest)}"
            )
            continue
        text = path.read_text(errors="replace")
        math_count += len(re.findall(r"<(?:m:)?math\b", text))
        media_ref_count += len(re.findall(r"<(?:img|svg)\b", text))
    lines.extend(
        [
            f"- Title: `{titles[0] if titles else '<missing>'}`",
            f"- Creators: {', '.join(creators) if creators else '<missing>'}",
            f"- Contributor(s): {', '.join(contributors) if contributors else '<none>'}",
            f"- Language: {', '.join(languages) if languages else '<missing>'}",
            (
                f"- Spine items: {len(spine)}; XHTML resources: {len(xhtml_paths)}; "
                f"MathML elements: {math_count}; inline image/SVG references: {media_ref_count}"
            ),
        ]
    )
    if not titles or "Wave Motions in the Ocean" not in titles[0]:
        report.add("ERROR", "EPUB", "book title missing or incorrect in OPF")
    if math_count == 0:
        report.add("ERROR", "EPUB", "no MathML elements found")

    checker = find_epubcheck()
    if checker:
        log = report.out / "epub" / "epubcheck.txt"
        proc = run([*checker, str(epub)], timeout=180, check=False)
        log.write_text(proc.stdout)
        lines.append(
            f"- EPUBCheck: {'PASS' if proc.returncode == 0 else 'FAIL'}; "
            f"log `{log.relative_to(report.out)}`"
        )
        if proc.returncode != 0:
            report.add(
                "ERROR", "EPUB", "EPUBCheck reported errors; see epub/epubcheck.txt"
            )
    else:
        report.add(
            "INFO",
            "EPUB",
            "EPUBCheck not found; install it or set EPUBCHECK_JAR to enable standards validation",
        )
        lines.append(
            "- EPUBCheck: skipped (install `epubcheck`, or set "
            "`EPUBCHECK_JAR=/path/to/epubcheck.jar`)"
        )

    reader_lines = [
        "Use at least two independent EPUB3 readers. Recommended minimum: **Thorium (Readium)** and **Calibre ebook-viewer**; add Apple Books/Kobo if those are release targets.",
        "For each reader record app/version and check:",
        "- cover and title/front matter; Contents navigation and chapter transitions;",
        "- inline variables in the Paola preface (ℓ, x, k, y, j/k/x/y/w), Greek symbols, named operators, vectors, subscripts/superscripts/fractions, and `p_atmosphere`;",
        "- representative aligned/display equations and chapter-based equation numbers;",
        "- long-equation behavior at narrow portrait width and at large font size;",
        "- SVG/raster figures, captions, tables, links, selection/search around math;",
        "- 50%/100%/200% font sizes and light/dark/sepia themes where supported.",
        "The unpacked XHTML/CSS above is for DOM diagnosis only; browser rendering is not an EPUB-reader acceptance test.",
    ]
    report.section("EPUB structural/render audit", lines)
    report.section("EPUB reader acceptance matrix", reader_lines)


def artifact_build_identity(dist: Path) -> str | None:
    pdf = dist / "wave-motions.pdf"
    if not pdf.is_file() or not need("pdfinfo"):
        return None
    proc = run(["pdfinfo", str(pdf)], check=False)
    match = re.search(
        r"^Subject:\s+Digital edition build\s+(.+?)\s*$",
        proc.stdout,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def checkout_identity() -> str | None:
    if not need("git"):
        return None
    try:
        proc = run(
            ["git", "-C", str(ROOT), "rev-parse", "--short=7", "HEAD"],
            timeout=10,
            check=False,
        )
    except OSError:
        return None
    value = proc.stdout.strip()
    return (
        value
        if proc.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{7,}", value)
        else None
    )


def build_identity_qa(dist: Path, report: Report) -> None:
    artifact = artifact_build_identity(dist)
    checkout = checkout_identity()
    lines = [f"- Artifact build identity: `{artifact or '<not detected>'}`"]
    if checkout:
        lines.append(f"- Current checkout: `{checkout}`")
    if (
        artifact
        and checkout
        and not artifact.startswith(checkout)
        and not checkout.startswith(artifact)
    ):
        report.add(
            "WARNING",
            "Build identity",
            f"artifact build {artifact} differs from current checkout {checkout}; "
            "visual findings may not describe the latest source",
        )
    report.section("Build identity", lines)


def artifact_inventory(dist: Path, report: Report) -> None:
    lines = []
    for path in sorted(
        p
        for p in dist.rglob("*")
        if p.is_file() and len(p.relative_to(dist).parts) <= 2
    ):
        rel = path.relative_to(dist)
        lines.append(f"- `{rel}` — {path.stat().st_size:,} bytes")
    report.section("Artifact inventory", lines)


def write_report(report: Report) -> Path:
    counts = {
        level: sum(1 for finding in report.findings if finding.level == level)
        for level in ("ERROR", "WARNING", "INFO")
    }
    lines = [
        "# Render QA report",
        "",
        f"Input: `{report.source}`",
        f"Resolved publication root: `{report.source_root}`",
        "",
        (
            f"Findings: **{counts['ERROR']} errors**, **{counts['WARNING']} warnings**, "
            f"**{counts['INFO']} informational notes**."
        ),
        "",
    ]
    if report.findings:
        lines.extend(["## Findings", ""])
        for finding in report.findings:
            lines.append(f"- **{finding.level} / {finding.area}:** {finding.message}")
        lines.append("")
    for title, section_lines in report.sections:
        lines.extend([f"## {title}", "", *section_lines, ""])
    lines.extend(
        [
            "## Manual final-pass checklist",
            "",
            "- Review every PDF contact sheet for unexpected blank pages, large whitespace changes, clipping, undersized figures, and abrupt pagination changes.",
            "- Inspect modern PDF pages 1–12 at full size (cover, half-title, frontispiece, title/edition notice, Contents, prefaces/editor note) plus every chapter opener and figure-dense page.",
            "- For facsimile, verify the exact 184-page physical structure before release and compare any suspicious blank/sparse pages to the source-page edition.",
            "- Open HTML in a real desktop browser and a phone/narrow viewport; test top/bottom navigation, Appearance theme/text-size choices, direct section permalinks, heading permalink/copy-link reveal and focus, scrolling active-section updates, back/forward fragment navigation, wide Contents rail, no-JS/native and scripted narrow Contents behavior, static MathML first paint, MathJax atomic swap/fallback, the non-persistent math URL override, per-figure vector/source switching, wide math/tables, image scaling, and the explicit 320px toolbar screenshot.",
            "- Complete the EPUB reader matrix above in real reading systems; structural/browser inspection alone is insufficient.",
            "",
        ]
    )
    path = report.out / "report.md"
    path.write_text("\n".join(lines))
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        default="release",
        help="publication directory or publication artifact ZIP (default: release)",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="QA output directory (default: audit/render-qa)",
    )
    parser.add_argument(
        "--pdf-dpi",
        type=int,
        default=72,
        help="DPI used for PDF contact-sheet source renders (default: 72)",
    )
    parser.add_argument(
        "--browser",
        help="Chrome/Chromium executable; auto-detected when omitted",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="skip optional headless HTML screenshots and browser regressions",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when QA records an ERROR",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    dist = prepare_input(source, out)
    report = Report(str(source), dist, out)
    artifact_inventory(dist, report)
    build_identity_qa(dist, report)
    pdf_qa(dist, report, args.pdf_dpi)
    browser = None if args.no_browser else detect_browser(args.browser)
    html_qa(dist, report, browser)
    epub_qa(dist, report)
    path = write_report(report)
    print(f"Render QA report: {path}")
    for finding in report.findings:
        print(f"{finding.level}: [{finding.area}] {finding.message}")
    errors = sum(1 for finding in report.findings if finding.level == "ERROR")
    return 1 if args.strict and errors else 0


def reader_regression_specimen(report: Report) -> Path:
    """Write an audit-only page that exercises the live HTML reader in Chromium."""
    page = report.out / "html" / "reader-regressions.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        """<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reader regression assertions</title>
  <style>
    html, body { width: 100%; min-height: 100%; margin: 0; }
    iframe { position: absolute; inset: 0; width: 100%; height: 100vh; border: 0; opacity: 0; }
    #reader-regression-results { position: relative; z-index: 1; white-space: pre-wrap; }
  </style>
</head>
<body>
  <iframe id="reader-regression-frame" title="Reader regression target"></iframe>
  <pre id="reader-regression-results"></pre>
  <script>
    (() => {
      const frame = document.querySelector("#reader-regression-frame");
      const output = document.querySelector("#reader-regression-results");
      const checks = [];
      const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
      const check = (condition, message) => {
        checks.push({ ok: Boolean(condition), message });
      };
      const finish = () => {
        const failed = checks.filter(({ ok }) => !ok);
        output.dataset.qaStatus = failed.length ? "fail" : "pass";
        output.textContent = JSON.stringify({
          status: output.dataset.qaStatus,
          checks,
        });
      };
      const storageEntries = (name) => {
        try {
          return [name, frame.contentWindow[name]];
        } catch (_) {
          return null;
        }
      };
      const loadReader = (url) => new Promise((resolve) => {
        frame.addEventListener("load", () => {
          setTimeout(() => resolve(frame.contentDocument), 300);
        }, { once: true });
        frame.src = url;
      });
      const run = async () => {
        let doc = frame.contentDocument;
        if (!doc) {
          check(false, "reader document is available");
          finish();
          return;
        }
        await wait(300);
        const figures = Array.from(doc.querySelectorAll("figure.wave-figure-switchable"));
        check(figures.length >= 2, "page has at least two switchable figures");
        const parts = figures.slice(0, 2).map((figure) => ({
          figure,
          image: figure.querySelector("img[data-vector-src]"),
          toggle: figure.querySelector("[data-figure-toggle]"),
        }));
        const complete = parts.length === 2 && parts.every(({ image, toggle }) => image && toggle);
        check(complete, "the first two figures have paired images and local actions");
        if (!complete) {
          finish();
          return;
        }
        const [first, second] = parts;
        const isOriginal = ({ image }) =>
          image.getAttribute("src") === image.dataset.originalSrc &&
          image.getAttribute("src").endsWith(".png");
        const isVector = ({ image }) =>
          image.getAttribute("src") === image.dataset.vectorSrc &&
          image.getAttribute("src").endsWith(".svg");
        check(isOriginal(first) && isOriginal(second), "first two figures initially use original PNGs");
        check(
          first.toggle.textContent.trim() === "Switch to Vector" &&
            second.toggle.textContent.trim() === "Switch to Vector",
          "first two figures initially say Switch to Vector",
        );
        first.toggle.click();
        await wait(50);
        check(isVector(first), "first figure switches to its vector SVG");
        check(
          first.toggle.textContent.trim() === "Switch to Original" &&
            first.toggle.getAttribute("aria-label") === "Switch to original source figure",
          "first action changes to Switch to Original with matching ARIA",
        );
        check(isOriginal(second), "second figure remains on its original PNG");
        check(second.toggle.textContent.trim() === "Switch to Vector", "second action remains Switch to Vector");
        first.toggle.click();
        await wait(50);
        check(isOriginal(first), "first figure switches back to its original PNG");
        check(first.toggle.textContent.trim() === "Switch to Vector", "first action restores Switch to Vector");

        const storageNames = ["localStorage", "sessionStorage"];
        const stores = storageNames.map(storageEntries).filter(Boolean);
        const figureStorageKeys = () => stores.flatMap(([name, store]) =>
          Object.keys(store)
            .filter((key) => /figure/i.test(key))
            .map((key) => name + ":" + key),
        );
        check(stores.length === storageNames.length, "reader storage is available for the persistence check");
        const figureControl = doc.querySelector("[data-figure-cycle]");
        const figureControlLabel = doc.querySelector("[data-figure-label]");
        check(Boolean(figureControl && figureControlLabel), "Settings exposes the global Figures control");
        if (figureControl && figureControlLabel) {
          check(figureControlLabel.textContent.trim() === "Original", "global figure preference initially says Original");
          check(
            figureControl.getAttribute("aria-label") === "Default figure rendering: Original" &&
              figureControl.title === "Default figure rendering: Original",
            "global figure preference has default-oriented accessibility text",
          );
        }
        check(figureStorageKeys().length === 0, "local figure switching writes no storage preference");

        figureControl?.click();
        await wait(50);
        check(isVector(first) && isVector(second), "global Vector preference updates all current figures");
        check(
          figureControlLabel?.textContent.trim() === "Vector" &&
            figureControl?.getAttribute("aria-label") === "Default figure rendering: Vector",
          "global figure preference changes to Vector",
        );
        check(
          frame.contentWindow.localStorage.getItem("wave-figure-view") === "vector",
          "global Vector preference is persisted",
        );
        check(
          !figureStorageKeys().some((key) => key.startsWith("sessionStorage:")),
          "figure preference is not written to session storage",
        );

        first.toggle.click();
        await wait(50);
        check(isOriginal(first) && isVector(second), "local override affects only its figure after a global change");
        check(figureControlLabel?.textContent.trim() === "Vector", "local override leaves the global preference unchanged");
        figureControl?.click();
        await wait(50);
        check(isOriginal(first) && isOriginal(second), "a global change resets temporary local overrides");
        check(
          frame.contentWindow.localStorage.getItem("wave-figure-view") === "original" &&
            figureControlLabel?.textContent.trim() === "Original",
          "global Original preference is persisted",
        );
        figureControl?.click();
        await wait(50);
        doc = await loadReader("/chapter1.html?math=mathjax");
        const reloadedFigures = Array.from(doc.querySelectorAll("figure.wave-figure-switchable")).slice(0, 2);
        const reloadedParts = reloadedFigures.map((figure) => ({
          image: figure.querySelector("img[data-vector-src]"),
          toggle: figure.querySelector("[data-figure-toggle]"),
        }));
        check(
          reloadedParts.length === 2 && reloadedParts.every(isVector),
          "persisted Vector preference applies on a new page load",
        );
        check(
          doc.querySelector("[data-figure-label]")?.textContent.trim() === "Vector" &&
            doc.querySelector("[data-figure-cycle]")?.getAttribute("aria-label") === "Default figure rendering: Vector",
          "new page Settings reflects the persisted Vector preference",
        );

        const heading = Array.from(doc.querySelectorAll("main h1[id], main h2[id]"))
          .sort((left, right) => right.textContent.length - left.textContent.length)[0];
        const headingActions = heading?.querySelector(":scope > .heading-actions");
        const headingPermalink = headingActions?.querySelector(":scope > .heading-permalink");
        const headingCopy = headingActions?.querySelector(":scope > .heading-copy-link");
        check(
          Boolean(heading && headingActions && headingPermalink && headingCopy),
          "headings expose separate permalink and copy-link actions",
        );
        if (heading && headingActions && headingPermalink && headingCopy) {
          const headingHeight = heading.getBoundingClientRect().height;
          const actionsRect = headingActions.getBoundingClientRect();
          const permalinkRect = headingPermalink.getBoundingClientRect();
          const copyRect = headingCopy.getBoundingClientRect();
          const copyStyle = getComputedStyle(headingCopy);
          check(
            copyStyle.position === "absolute" && copyStyle.display !== "none",
            "heading Copy link is absolutely positioned without display:none",
          );
          check(
            Math.abs(actionsRect.width - permalinkRect.width) <= 1,
            "heading action width is determined by the # permalink only",
          );
          check(
            copyRect.left >= permalinkRect.right - 1 &&
              Math.abs(
                (copyRect.top + copyRect.height / 2) -
                  (actionsRect.top + actionsRect.height / 2),
              ) <= 2,
            "heading Copy link is beside and vertically aligned with #",
          );
          headingCopy.focus();
          await wait(20);
          const revealedStyle = getComputedStyle(headingCopy);
          check(
            doc.activeElement === headingCopy &&
              revealedStyle.opacity !== "0" &&
              revealedStyle.pointerEvents !== "none",
            "heading Copy link reveals on keyboard focus",
          );
          check(
            Math.abs(heading.getBoundingClientRect().height - headingHeight) <= 1,
            "revealing heading Copy link does not change narrow heading wrapping",
          );
          headingCopy.blur();
        }

        const panel = doc.querySelector("#reader-settings");
        const settingsButton = doc.querySelector("[aria-controls=reader-settings]");
        const reset = doc.querySelector('[data-text-size-action="reset"]');
        const decrease = doc.querySelector('[data-text-size-action="decrease"]');
        const increase = doc.querySelector('[data-text-size-action="increase"]');
        const popoverOpen = () => {
          try {
            return panel?.matches(":popover-open") || false;
          } catch (_) {
            return false;
          }
        };
        const openSettings = async () => {
          if (!panel) return;
          if (!popoverOpen() && typeof panel.showPopover === "function") panel.showPopover();
          if (!popoverOpen()) settingsButton?.click();
          await wait(20);
        };
        const setTextSize = async (percent) => {
          reset?.click();
          const button = percent < 100 ? decrease : increase;
          const clicks = Math.abs(percent - 100) / 10;
          for (let index = 0; index < clicks; index += 1) button?.click();
          await openSettings();
          check(
            panel && panel.scrollWidth <= panel.clientWidth,
            "Settings has no horizontal overflow at " + percent + "% text size",
          );
        };
        check(Boolean(panel && settingsButton && reset && decrease && increase), "Settings exposes its expected controls");
        if (panel && settingsButton && reset && decrease && increase) {
          const rows = Array.from(panel.querySelectorAll(".reader-setting-row"));
          const rowLabels = rows.map((row) => row.querySelector(".reader-setting-label")?.textContent.trim());
          const rowControls = rows.map((row) => row.children[1]);
          check(
            rowLabels.join("|") === "Rendering:|Figures:|Text:|Theme:",
            "Settings has its four aligned rows",
          );
          check(
            rowControls.every(Boolean) &&
              Math.max(...rowControls.map((control) => control.getBoundingClientRect().width)) -
                Math.min(...rowControls.map((control) => control.getBoundingClientRect().width)) <= 1,
            "Settings controls have equal total widths",
          );
          check(
            rows.every((row) => {
              const label = row.querySelector(".reader-setting-label");
              const control = row.children[1];
              return label && control &&
                label.getBoundingClientRect().right <= control.getBoundingClientRect().left &&
                label.scrollWidth <= label.clientWidth;
            }),
            "Settings labels fit without wrapping or overlapping controls",
          );
          panel.style.maxHeight = "8rem";
          panel.style.overflow = "auto";
          await setTextSize(100);
          check(panel.scrollWidth <= panel.clientWidth, "Settings has no horizontal overflow at its default size");
          check(panel.scrollHeight > panel.clientHeight, "Settings overflow check includes a vertical scrollbar");
          await setTextSize(50);
          await setTextSize(200);
          reset.click();
        }
        if (panel && popoverOpen() && typeof panel.hidePopover === "function") panel.hidePopover();

        const mathjaxInline = doc.querySelector('span[data-math-renderer="mathjax"].math.inline');
        const mathmlInline = doc.querySelector('span[data-math-renderer="mathml"].math.inline');
        const mathjaxNode = mathjaxInline?.querySelector('mjx-container[jax="CHTML"]');
        const mathmlNode = mathmlInline?.querySelector("math");
        check(Boolean(mathjaxNode), "a representative inline MathJax node is rendered");
        check(Boolean(mathmlNode), "a representative native MathML node is present");
        for (const [label, node] of [
          ["inline math wrapper", mathjaxInline],
          ["MathJax inline node", mathjaxNode],
          ["native MathML wrapper", mathmlInline],
          ["native MathML node", mathmlNode],
        ]) {
          if (!node) continue;
          const style = getComputedStyle(node);
          check(
            style.overflowX !== "auto" && style.overflowX !== "scroll",
            label + " is not an independent horizontal scroll container",
          );
        }
        check(
          frame.contentWindow.localStorage.getItem("wave-figure-view") === "vector",
          "figure preference remains persisted after all checks",
        );
        finish();
      };
      frame.addEventListener("load", () => {
        run().catch((error) => {
          check(false, "reader regression script completed without an exception: " + error);
          finish();
        });
      }, { once: true });
      try {
        localStorage.removeItem("wave-figure-view");
        sessionStorage.removeItem("wave-figure-view");
      } catch (_) {}
      frame.src = "/chapter1.html?math=mathjax";
    })();
  </script>
</body>
</html>
"""
    )
    return page


def reader_visual_specimen(report: Report) -> Path:
    """Write an audit-only iframe page for the responsive reader screenshot matrix."""
    page = report.out / "html" / "reader-visual.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        """<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reader visual QA</title>
  <style>
    html, body, iframe { width: 100%; height: 100%; margin: 0; border: 0; display: block; }
    body { overflow: hidden; }
  </style>
</head>
<body>
  <iframe id="reader-visual-frame" title="Reader visual target"></iframe>
  <script>
    (() => {
      const params = new URLSearchParams(location.search);
      const page = params.get("page");
      const allowedPages = new Set([
        "chapter1.html",
        "chapter2.html",
        "chapter3.html",
        "chapter4.html",
        "chapter5.html",
        "chapter6.html",
      ]);
      const textSize = Number.parseInt(params.get("text-size"), 10);
      const theme = params.get("theme");
      const settingsOpen = params.get("settings") === "1";
      const frame = document.querySelector("#reader-visual-frame");
      frame.addEventListener("load", () => {
        const root = frame.contentDocument.documentElement;
        if ([50, 100, 200].includes(textSize)) {
          root.style.setProperty("--wave-text-scale", String(textSize / 100));
        }
        if (theme === "light" || theme === "dark") root.dataset.theme = theme;
        if (settingsOpen) {
          frame.contentDocument.querySelector("[aria-controls=reader-settings]")?.click();
        }
        document.documentElement.dataset.qaReady = "";
      }, { once: true });
      frame.src = "/" + (allowedPages.has(page) ? page : "chapter1.html");
    })();
  </script>
</body>
</html>
"""
    )
    return page


def browser_reader_visual_jobs(
    report: Report,
    qa_pages: dict[str, Path],
    jobs: list[tuple[str, str, int, int, bool]],
) -> None:
    visual_page = reader_visual_specimen(report)
    qa_pages[READER_VISUAL_ROUTE] = visual_page
    for width, height in ((390, 844), (768, 1000), (1440, 1200)):
        for text_size in MATH_PARITY_TEXT_SIZES:
            query = urllib.parse.urlencode(
                {
                    "page": "chapter1.html",
                    "text-size": text_size,
                    "theme": "light",
                }
            )
            jobs.append(
                (
                    f"reader-light-{width}-{text_size.replace('%', '')}.png",
                    f"{READER_VISUAL_ROUTE}?{query}",
                    width,
                    height,
                    False,
                )
            )
        query = urllib.parse.urlencode(
            {"page": "chapter1.html", "text-size": "100%", "theme": "dark"}
        )
        jobs.append(
            (
                f"reader-dark-{width}-100.png",
                f"{READER_VISUAL_ROUTE}?{query}",
                width,
                height,
                False,
            )
        )
    settings_query = urllib.parse.urlencode(
        {
            "page": "chapter1.html",
            "text-size": "100%",
            "theme": "light",
            "settings": "1",
        }
    )
    jobs.append(
        (
            "reader-settings-390.png",
            f"{READER_VISUAL_ROUTE}?{settings_query}",
            390,
            844,
            False,
        )
    )


def browser_reader_regressions(
    browser: str,
    base: str,
    report: Report,
    lines: list[str],
) -> None:
    ok, dom = browser_dump_dom(
        browser,
        f"{base}{READER_REGRESSION_ROUTE}",
        width=390,
        height=844,
    )
    if not ok:
        report.add(
            "WARNING",
            "HTML",
            "headless DOM dump failed; reader behavior regression assertions skipped",
        )
        return
    status = re.search(
        r'<pre id="reader-regression-results"[^>]*data-qa-status="([^"]+)"',
        dom,
        flags=re.IGNORECASE,
    )
    if status is None:
        report.add(
            "ERROR",
            "HTML",
            "reader behavior regression assertions did not report a result",
        )
        return
    if status.group(1) != "pass":
        result = re.search(
            r'<pre id="reader-regression-results"[^>]*>.*?</pre>',
            dom,
            flags=re.DOTALL | re.IGNORECASE,
        )
        detail = html.unescape(result.group(0)) if result else "no assertion details"
        report.add(
            "ERROR",
            "HTML",
            "reader behavior regression assertions failed: "
            + re.sub(r"\s+", " ", detail).strip()[:1600],
        )
        return
    lines.append(
        "- Chromium reader regression assertions: PASS "
        "(global and per-figure switching, figure persistence, Settings layout, "
        "heading permalink actions, narrow heading wrapping, overflow at "
        "50%/100%/200%, and inline MathJax/MathML overflow)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
