#!/usr/bin/env python3
"""Generate local visual/render QA artifacts for the published book outputs.

The script is intentionally a developer aid rather than a release gate. It can
inspect a built ``dist/`` directory or an artifact ZIP, render both PDFs into
contact sheets, perform static/optional-browser HTML checks, unpack and inspect
EPUB structure, and write a single Markdown report under ``audit/render-qa``.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "audit" / "render-qa"
EXPECTED_HTML = ["index.html", *(f"chapter{i}.html" for i in range(1, 7)), "references.html"]
FACSIMILE_EXPECTED_PAGES = 184


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
        raise SystemExit(f"QA input must be a dist directory or ZIP artifact: {source}")
    extracted = out / "input"
    shutil.rmtree(extracted, ignore_errors=True)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(source) as archive:
        archive.extractall(extracted)
    if (extracted / "dist").is_dir():
        return extracted / "dist"
    children = [p for p in extracted.iterdir() if p.is_dir()]
    if len(children) == 1 and all(
        (children[0] / name).exists() for name in ("wave-motions.pdf", "index.html")
    ):
        return children[0]
    if all((extracted / name).exists() for name in ("wave-motions.pdf", "index.html")):
        return extracted
    raise SystemExit("could not locate a dist-style publication root inside the ZIP")


def pdf_page_count(pdf: Path) -> int:
    proc = run(["pdfinfo", str(pdf)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, flags=re.M)
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
    for attr in ("src", "href"):
        for ref in re.findall(
            rf'{attr}=["\']([^"\']+)["\']', text, flags=re.I
        ):
            if ref.startswith(
                ("http:", "https:", "mailto:", "#", "javascript:", "data:")
            ):
                continue
            path = urllib.parse.unquote(ref.split("#", 1)[0].split("?", 1)[0])
            if path and not (page.parent / path).exists():
                broken.append(ref)
    return broken


def detect_browser(explicit: str | None) -> str | None:
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


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def local_server(root: Path):
    port = free_port()
    handler = lambda *args, **kwargs: QuietHandler(  # noqa: E731
        *args, directory=str(root), **kwargs
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


def html_qa(dist: Path, report: Report, browser: str | None) -> None:
    lines: list[str] = []
    missing = [name for name in EXPECTED_HTML if not (dist / name).is_file()]
    if missing:
        report.add("ERROR", "HTML", "missing pages: " + ", ".join(missing))
        return
    broken_all: list[str] = []
    titles: dict[str, str] = {}
    for name in EXPECTED_HTML:
        page = dist / name
        text = page.read_text(errors="replace")
        match = re.search(r"<title>(.*?)</title>", text, flags=re.S | re.I)
        titles[name] = (
            re.sub(r"\s+", " ", match.group(1)).strip() if match else "<missing>"
        )
        broken = html_local_refs(page)
        broken_all.extend(f"{name}: {ref}" for ref in broken)
        if 'name="viewport"' not in text and "name='viewport'" not in text:
            report.add("WARNING", "HTML", f"{name} has no viewport meta tag")
    if broken_all:
        report.add(
            "ERROR",
            "HTML",
            f"{len(broken_all)} broken local reference(s); first: {broken_all[0]}",
        )
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
        has_context = ".book-context" in css_text
        lines.append(
            f"- CSS includes book-context navigation: {'yes' if has_context else 'no'}"
        )
        if not has_context:
            report.add(
                "WARNING",
                "HTML",
                "book/chapter orientation context is missing; this artifact predates "
                "the current reader-navigation design",
            )
    else:
        report.add("ERROR", "HTML", "missing assets/wave.css")
    if not js.is_file():
        report.add("ERROR", "HTML", "missing assets/wave.js")

    mathjax_external: list[str] = []
    for name in EXPECTED_HTML:
        text = (dist / name).read_text(errors="replace")
        mathjax_external.extend(
            re.findall(r'https://[^"\']*mathjax[^"\']*', text, flags=re.I)
        )
    if mathjax_external:
        report.add(
            "INFO",
            "HTML",
            "HTML mathematics depends on an external MathJax runtime; offline ZIP "
            "reading will not typeset math unless MathJax is vendored.",
        )
        lines.append(
            f"- External MathJax reference detected: `{mathjax_external[0]}`"
        )

    if browser:
        lines.append(f"- Headless browser detected: `{browser}`")
        screenshots = report.out / "html" / "screenshots"
        with local_server(dist) as base:
            jobs = []
            for name in EXPECTED_HTML:
                jobs.append(
                    (f"desktop-{Path(name).stem}.png", name, 1440, 1000, False)
                )
                jobs.append(
                    (f"mobile-{Path(name).stem}.png", name, 390, 844, False)
                )
            jobs.append(("dark-chapter4.png", "chapter4.html", 390, 844, True))
            failures = 0
            completed = 0
            for output_name, page_name, width, height, dark in jobs:
                ok, detail = browser_screenshot(
                    browser,
                    f"{base}/{page_name}",
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
    else:
        report.add(
            "INFO",
            "HTML",
            "no Chrome/Chromium executable found; browser screenshot QA skipped",
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
        f"- `wave-motions.epub`; SHA-256 `{sha256(epub)[:16]}…`; unpacked to "
        f"`{dest.relative_to(report.out)}/`"
    ]
    try:
        with zipfile.ZipFile(epub) as archive:
            names = archive.namelist()
            if not names or names[0] != "mimetype":
                report.add("ERROR", "EPUB", "mimetype is not the first ZIP entry")
            elif archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
                report.add(
                    "ERROR", "EPUB", "mimetype entry is compressed; EPUB requires it stored"
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
        opf_rel = rootfile.attrib["full-path"] if rootfile is not None else "EPUB/content.opf"
    except Exception as exc:
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
            f"- Spine items: {len(spine)}; XHTML resources: {len(xhtml_paths)}; "
            f"MathML elements: {math_count}; inline image/SVG references: {media_ref_count}",
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
        "- small/default/large font sizes and light/dark/sepia themes where supported.",
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
        r"^Subject:\s+Digital edition build\s+(.+?)\s*$", proc.stdout, flags=re.M
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
        f"Findings: **{counts['ERROR']} errors**, **{counts['WARNING']} warnings**, "
        f"**{counts['INFO']} informational notes**.",
        "",
    ]
    if report.findings:
        lines.extend(["## Findings", ""])
        for finding in report.findings:
            lines.append(
                f"- **{finding.level} / {finding.area}:** {finding.message}"
            )
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
            "- Open HTML in a real desktop browser and a phone/narrow responsive viewport; exercise both top and bottom navigation, theme cycling, wide math/tables, and image scaling.",
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
        default="dist",
        help="built dist directory or publication artifact ZIP (default: dist)",
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
        help="skip optional headless HTML screenshots",
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


if __name__ == "__main__":
    raise SystemExit(main())
