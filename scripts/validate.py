#!/usr/bin/env python3
"""Publication validation with math, artifact, release, and all modes."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from publication import current_build
from release import DEFAULT_FILES, verify_manifest

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "reconstruction"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
README = ROOT / "README.md"
EPUB = DIST / "wave-motions.epub"
MODERN_PDF = DIST / "wave-motions.pdf"
FACSIMILE_PDF = DIST / "wave-motions-facsimile.pdf"
LATEX_CACHE = Path(
    os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions"))
) / "latex"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
MATHJAX_PINNED = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"

# Paola's preface is a compact cross-format sentinel because it intentionally
# distinguishes ordinary prose from mathematical variable glyphs.
PAOLA_SOURCE_SENTINELS = (
    r"put $\ell$ ($x$ wavenumber) before $k$ ($y$ wavenumber)",
    r"letters $j,k,x,y,w$ do not exist",
    r"$k$ coming before or after",
    r"$\ell$ was supremely unimportant",
)
README_MATH_SENTINELS = (r"\ell", "x", "k", "y", "j,k,x,y,w")
EPUB_VARIABLE_SENTINELS = ("σ", "ρ", "ℓ", "k", "m", "x", "y", "t")
EPUB_OPERATOR_SENTINELS = ("sin", "cos", "tanh")
NAMED_FUNCTIONS = ("sin", "cos", "tan", "sinh", "cosh", "tanh", "exp", "log", "ln")
NUMBERED_ENV_RE = re.compile(r"\\begin\{(?:waveequation|wavealign)\}")
NATIVE_TAG_RE = re.compile(r"\\tag\{(?P<tag>\d+\.\d+)\}")
MATH_ENV_RE = re.compile(
    r"\\begin\{(?P<env>waveequation|wavealign|align\*?|equation\*?|gather\*?|multline\*?)\}"
    r"(?P<body>.*?)\\end\{(?P=env)\}",
    re.S,
)
MATH_TEXT_COMMAND_RE = re.compile(
    r"\\(?:text|textrm|textsf|texttt|textit|textbf|mathrm|operatorname)\{[^{}]*\}"
)


def fail(message: str) -> None:
    raise SystemExit(message)


def require_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"missing required generated artifact: {path}")


def strip_tex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        # Ignore unescaped percent signs; sufficient for source-lint purposes.
        m = re.search(r"(?<!\\)%", line)
        lines.append(line[: m.start()] if m else line)
    return "\n".join(lines)


def tex_math_regions(text: str) -> list[str]:
    """Return TeX regions that are actually interpreted as mathematics."""
    regions = [m.group(1) for m in re.finditer(r"\\\[(.*?)\\\]", text, re.S)]
    regions.extend(m.group("body") for m in MATH_ENV_RE.finditer(text))
    regions.extend(
        m.group(1)
        for m in re.finditer(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", text, re.S)
    )
    return regions


def check_canonical_source() -> None:
    frontmatter = (RECON / "frontmatter-modern.tex").read_text()
    for sentinel in PAOLA_SOURCE_SENTINELS:
        if sentinel not in frontmatter:
            fail(f"canonical Paola preface math sentinel changed or lost: {sentinel}")

    for chapter in sorted(RECON.glob("chapter[1-6].tex")):
        text = strip_tex_comments(chapter.read_text())
        occurrences = re.findall(r"\\rm(?:\s|\{|$)", text)
        if occurrences:
            fail(
                f"{chapter.name}: found {len(occurrences)} legacy \\rm declaration(s); "
                "replace with semantic math commands"
            )

        math_text = "\n".join(
            MATH_TEXT_COMMAND_RE.sub("", region) for region in tex_math_regions(text)
        )
        for function in NAMED_FUNCTIONS:
            bare = re.search(rf"(?<![\\A-Za-z]){function}(?![A-Za-z])", math_text)
            if bare:
                fail(
                    f"{chapter.name}: named math function {function!r} appears without a TeX operator command"
                )

    print("Canonical TeX math audit OK")


def canonical_equation_labels() -> dict[int, tuple[str, ...]]:
    labels: dict[int, tuple[str, ...]] = {}
    for chapter_number in range(1, 7):
        path = RECON / f"chapter{chapter_number}.tex"
        text = strip_tex_comments(path.read_text())
        wrapper_count = len(NUMBERED_ENV_RE.findall(text))
        native = tuple(f"({m.group('tag')})" for m in NATIVE_TAG_RE.finditer(text))
        if native and wrapper_count:
            fail(f"{path.name}: mixes historical native tags with editorial numbering wrappers")
        if native:
            expected = tuple(f"({chapter_number}.{index})" for index in range(1, len(native) + 1))
            if native != expected:
                fail(f"{path.name}: native equation tags are not contiguous/in order: {native}")
            labels[chapter_number] = native
        elif wrapper_count:
            labels[chapter_number] = tuple(
                f"({chapter_number}.{index})" for index in range(1, wrapper_count + 1)
            )
        else:
            fail(f"{path.name}: no selected numbered equations found")
    return labels


def require_labels(text: str, labels: tuple[str, ...], *, artifact: str) -> None:
    if artifact == "EPUB" or artifact.endswith(".html"):
        marker = r'class=["\']upright["\'][^>]*>\s*'
    elif artifact.endswith(".pdf"):
        # PDF text extraction keeps equation labels on the right edge of the
        # displayed equation line, while prose references remain left-aligned.
        marker = r"(?m)^[ \t]{20,}.*?"
    else:
        marker = ""
    positions: list[int] = []
    for label in labels:
        pattern = re.compile(marker + re.escape(label) if marker else re.escape(label))
        matches = list(pattern.finditer(text))
        count = len(matches)
        if count != 1:
            fail(
                f"{artifact}: equation label {label} occurs {count} times; expected exactly once"
            )
        positions.append(matches[0].start())
    if positions != sorted(positions):
        fail(f"{artifact}: numbered equation labels are not in canonical order")


def github_math_patterns(expr: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    escaped = re.escape(expr)
    return (
        re.compile(rf"(?<!\\)\${escaped}(?<!\\)\$"),
        re.compile(rf"\$`{escaped}`\$"),
    )


def check_readme() -> None:
    require_file(README)
    text = README.read_text()
    paola_start = text.find("## Preface — Paola Malanotte-Rizzoli")
    editor_start = text.find("## Editor’s note")
    if paola_start < 0 or editor_start <= paola_start:
        fail("README Paola preface boundaries are missing")
    section = text[paola_start:editor_start]

    for expr in README_MATH_SENTINELS:
        if not any(pattern.search(section) for pattern in github_math_patterns(expr)):
            fail(f"README no longer preserves GitHub-renderable inline math for {expr!r}")
    if "`\\ell`" in section and "$`\\ell`$" not in section:
        fail("README contains a code-formatted \\ell outside GitHub math delimiters")

    print("GitHub Markdown math preservation OK")


def check_html() -> None:
    pages = sorted(DIST.glob("*.html"))
    if not pages:
        fail("generated HTML pages are missing")
    css = DIST / "assets" / "wave.css"
    require_file(css)
    css_text = css.read_text(errors="replace")
    selector = 'mjx-container[jax="CHTML"][display="true"]'
    if selector not in css_text or "overflow-x: auto" not in css_text:
        fail("HTML stylesheet is missing responsive display-math overflow handling")

    joined = "\n".join(page.read_text(errors="replace") for page in pages)
    if MATHJAX_PINNED not in joined:
        fail("pinned MathJax 3.2.2 combined component is missing from HTML")
    if "mathjax@3/es5/tex-mml-chtml.js" in joined:
        fail("unversioned MathJax URL remains in generated HTML")

    inline_count = len(re.findall(r'class="math inline"', joined))
    display_count = len(re.findall(r'class="math display"', joined))
    if inline_count == 0 or display_count == 0:
        fail(
            f"HTML lost inline or display math markup: inline={inline_count}, display={display_count}"
        )
    if "assistiveMml: false" in joined or "enableAssistiveMml: false" in joined:
        fail("HTML explicitly disables MathJax assistive MathML")

    index = (DIST / "index.html").read_text(errors="replace")
    for tex in (r"\ell", "x", "k", "y", "j,k,x,y,w"):
        if tex not in index:
            fail(f"HTML Paola-preface math sentinel is missing: {tex!r}")

    for chapter_number, labels in canonical_equation_labels().items():
        chapter = (DIST / f"chapter{chapter_number}.html").read_text(errors="replace")
        require_labels(chapter, labels, artifact=f"chapter{chapter_number}.html")

    print(
        f"HTML MathJax markup/accessibility invariants OK: "
        f"inline={inline_count}, display={display_count}"
    )


def package_document(archive: zipfile.ZipFile) -> tuple[str, ET.Element]:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
    except (KeyError, ET.ParseError) as exc:
        fail(f"cannot read EPUB package container: {exc}")
    rootfile = container.find(".//{*}rootfile")
    if rootfile is None or not rootfile.get("full-path"):
        fail("EPUB container has no package rootfile")
    name = rootfile.get("full-path")
    assert name is not None
    try:
        return name, ET.fromstring(archive.read(name))
    except (KeyError, ET.ParseError) as exc:
        fail(f"cannot read EPUB package document {name}: {exc}")


def check_epub_mathml() -> None:
    require_file(EPUB)
    ns = f"{{{MATHML_NS}}}"
    with zipfile.ZipFile(EPUB) as archive:
        opf_name, opf_root = package_document(archive)
        manifest = opf_root.find("{*}manifest")
        if manifest is None:
            fail("EPUB manifest is missing")
        package_dir = Path(opf_name).parent.as_posix()
        xhtml_items: dict[str, ET.Element] = {}
        for item in manifest.findall("{*}item"):
            if item.get("media-type") != "application/xhtml+xml" or not item.get("href"):
                continue
            href = urllib.parse.unquote(item.get("href") or "")
            member = str(Path(package_dir, href)).replace("\\", "/")
            xhtml_items[member] = item

        math_elements: list[ET.Element] = []
        math_docs: set[str] = set()
        for name, item in xhtml_items.items():
            try:
                root = ET.fromstring(archive.read(name))
            except (KeyError, ET.ParseError) as exc:
                fail(f"cannot parse EPUB XHTML {name}: {exc}")
            current = root.findall(f".//{ns}math")
            if current:
                math_docs.add(name)
                math_elements.extend(current)
                properties = set((item.get("properties") or "").split())
                if "mathml" not in properties:
                    fail(f"EPUB manifest omits mathml property for {name}")

        if len(math_elements) < 50:
            fail(f"EPUB contains only {len(math_elements)} MathML expressions")
        displays = {math.get("display") for math in math_elements}
        if not {"inline", "block"}.issubset(displays):
            fail(f"EPUB lacks inline or block MathML: {sorted(str(v) for v in displays)}")

        required_structures = (
            "mi",
            "mn",
            "mo",
            "msub",
            "msup",
            "mfrac",
            "mover",
            "mtable",
        )
        counts: dict[str, int] = {}
        for tag in required_structures:
            count = sum(len(math.findall(f".//{ns}{tag}")) for math in math_elements)
            counts[tag] = count
            if count == 0:
                fail(f"EPUB MathML has no <{tag}> structure")

        mi_nodes = [
            node for math in math_elements for node in math.findall(f".//{ns}mi")
        ]
        mo_nodes = [
            node for math in math_elements for node in math.findall(f".//{ns}mo")
        ]
        mi_text = ["".join(node.itertext()).strip() for node in mi_nodes]
        mo_text = ["".join(node.itertext()).strip() for node in mo_nodes]
        for symbol in EPUB_VARIABLE_SENTINELS:
            if symbol not in mi_text:
                fail(f"EPUB variable {symbol!r} is not represented as <mi>")
            if symbol in mo_text:
                fail(f"EPUB variable {symbol!r} is incorrectly represented as operator <mo>")

        # texmath changed its MathML serialization of named functions. Older
        # versions used <mo>sin</mo>; newer versions use an <mi> function token
        # followed by U+2061 FUNCTION APPLICATION in <mo>. Accept either
        # serialization, but require every representative function to be
        # recognized as a function rather than an ordinary variable.
        def has_named_function(name: str) -> bool:
            if name in mo_text:
                return True
            for math in math_elements:
                for parent in math.iter():
                    children = list(parent)
                    for index, child in enumerate(children[:-1]):
                        if (
                            child.tag == f"{ns}mi"
                            and "".join(child.itertext()).strip() == name
                            and children[index + 1].tag == f"{ns}mo"
                            and "".join(children[index + 1].itertext()).strip() == "\u2061"
                        ):
                            return True
            return False

        for function in EPUB_OPERATOR_SENTINELS:
            if not has_named_function(function):
                fail(
                    f"EPUB named function {function!r} is not represented "
                    "with a recognized MathML function serialization"
                )

        atmosphere_math = [
            math
            for math in math_elements
            if "atmosphere" in "".join(math.itertext())
        ]
        if not atmosphere_math:
            fail("EPUB lost the p_atmosphere mathematical expression")
        if not any(
            "atmosphere"
            in "".join(
                "".join(node.itertext()).strip()
                for node in math.findall(f".//{ns}mi")
                if node.get("mathvariant") == "normal"
            )
            for math in atmosphere_math
        ):
            fail("EPUB p_atmosphere subscript is not upright semantic math text")

        epub_markup = "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in xhtml_items
        )
        all_labels = tuple(
            label
            for labels in canonical_equation_labels().values()
            for label in labels
        )
        require_labels(epub_markup, all_labels, artifact="EPUB")

        print(
            "EPUB MathML semantics OK: "
            f"expressions={len(math_elements)}, docs={len(math_docs)}, "
            + ", ".join(f"{tag}={counts[tag]}" for tag in required_structures)
        )


def pdf_text(path: Path) -> str:
    if shutil.which("pdftotext") is None:
        fail("pdftotext is required for PDF math smoke checks")
    with tempfile.TemporaryDirectory(prefix="wave-math-pdf-") as td:
        out = Path(td) / "text.txt"
        subprocess.run(
            ["pdftotext", "-layout", str(path), str(out)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return out.read_text(errors="replace")


def check_pdf_math() -> None:
    extracted: dict[Path, str] = {}
    for path in (MODERN_PDF, FACSIMILE_PDF):
        require_file(path)
        layout_text = pdf_text(path)
        text = " ".join(layout_text.split())
        extracted[path] = layout_text
        for sentinel in (
            "like him, I put",
            "wavenumber",
            "do not exist in the Italian alphabet",
        ):
            if sentinel not in text:
                fail(
                    f"{path.name}: Paola-preface PDF text sentinel is missing: {sentinel!r}"
                )

    modern_text = extracted[MODERN_PDF]
    all_labels = tuple(
        label
        for labels in canonical_equation_labels().values()
        for label in labels
    )
    require_labels(modern_text, all_labels, artifact=MODERN_PDF.name)

    modern_log = (
        Path(
            os.environ.get(
                "WAVE_CACHE_DIR",
                str(ROOT / ".cache" / "wave-motions"),
            )
        )
        / "latex"
        / "modern"
        / "main-modern.log"
    )
    if modern_log.is_file():
        log = modern_log.read_text(errors="replace")
        warnings = []
        if "Missing character:" in log:
            warnings.append("missing glyph warning")
        if "Package amsmath Warning:" in log:
            warnings.append("amsmath warning")
        if warnings:
            print(
                "PDF math log review warning: " + ", ".join(warnings),
                file=sys.stderr,
            )

    print("PDF math/text extraction smoke checks OK")


def run_epubcheck(require: bool) -> None:
    jar = os.environ.get("EPUBCHECK_JAR")
    command = shutil.which("epubcheck")
    if jar:
        require_file(Path(jar))
        cmd = ["java", "-jar", jar, str(EPUB)]
    elif command:
        cmd = [command, str(EPUB)]
    elif require:
        fail("EPUBCheck is required but EPUBCHECK_JAR/epubcheck is unavailable")
    else:
        print("EPUBCheck not installed; standards validation skipped")
        return

    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.returncode:
        fail(f"EPUBCheck failed with status {proc.returncode}")
    print("EPUBCheck conformance validation OK")


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        fail(f"missing required command: {command}")


def pdf_pages(path: Path) -> int:
    require_command("pdfinfo")
    proc = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, flags=re.M)
    if not match:
        fail(f"pdfinfo did not report a page count for {path}")
    return int(match.group(1))


def check_pdf_integrity() -> None:
    require_command("pdfinfo")
    for path in (FACSIMILE_PDF, MODERN_PDF):
        require_file(path)
        if shutil.which("qpdf"):
            subprocess.run(
                ["qpdf", "--check", str(path)], check=True, stdout=subprocess.DEVNULL
            )
        else:
            subprocess.run(["pdfinfo", str(path)], check=True, stdout=subprocess.DEVNULL)

    fac_pages = pdf_pages(FACSIMILE_PDF)
    mod_pages = pdf_pages(MODERN_PDF)
    if fac_pages != 184:
        message = (
            f"Facsimile page count is {fac_pages}; expected 184. "
            "Pagination remains a final publication requirement."
        )
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning title=Facsimile pagination::{message}")
        else:
            print(f"warning: {message}", file=sys.stderr)
    if mod_pages <= 0:
        fail("modern PDF has no pages")
    print(f"PDF integrity OK: facsimile={fac_pages} pages, modern={mod_pages} pages")


def check_pdf_destinations() -> None:
    logs = (
        LATEX_CACHE / "facsimile" / "main-facsimile.log",
        LATEX_CACHE / "modern" / "main-modern.log",
    )
    for log_path in logs:
        require_file(log_path)
        if "destination with the same identifier" in log_path.read_text(errors="replace"):
            fail(f"duplicate PDF destination reported in {log_path}")
    print("PDF destination checks OK")


def _write_pdf_text(path: Path, destination: Path) -> str:
    require_command("pdftotext")
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftotext", "-layout", str(path), str(destination)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return destination.read_text(errors="replace")


def check_pdf_text() -> None:
    facsimile_text = _write_pdf_text(FACSIMILE_PDF, BUILD / "facsimile" / "text.txt")
    modern_text = _write_pdf_text(MODERN_PDF, BUILD / "modern" / "text.txt")
    for text in (facsimile_text, modern_text):
        for sentinel in (
            "When I volunteered to teach the MIT/WHOI",
            "These notes have been collected and assembled",
        ):
            if sentinel not in text:
                fail(f"PDF text sentinel is missing: {sentinel}")
    print("PDF text sentinel checks OK")


def check_pdf_render() -> None:
    require_command("pdftoppm")
    for kind, path in (("facsimile", FACSIMILE_PDF), ("modern", MODERN_PDF)):
        pages = pdf_pages(path)
        middle = pages // 2
        destination = BUILD / kind / "render-check"
        shutil.rmtree(destination, ignore_errors=True)
        destination.mkdir(parents=True, exist_ok=True)
        for page in (1, middle, pages):
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page),
                    "-l",
                    str(page),
                    "-singlefile",
                    "-r",
                    "100",
                    "-png",
                    str(path),
                    str(destination / f"page-{page}"),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        if len(list(destination.glob("page-*.png"))) != 3:
            fail(f"PDF render smoke check produced the wrong number of pages for {kind}")
    print("PDF render smoke checks OK")


def check_publish_root() -> None:
    expected = (
        DIST / "index.html",
        DIST / "wave-motions.pdf",
        DIST / "wave-motions-facsimile.pdf",
        DIST / "wave-motions.epub",
        DIST / "SHA256SUMS",
    )
    for path in expected:
        require_file(path)
    index = (DIST / "index.html").read_text(errors="replace")
    for name in ("wave-motions.pdf", "wave-motions-facsimile.pdf", "wave-motions.epub"):
        if name not in index:
            fail(f"HTML download link is missing: {name}")
    if (DIST / "html").exists():
        fail("legacy nested dist/html output exists")
    print("Publish root and download checks OK")


def check_build_identity() -> None:
    require_command("pdfinfo")
    info = current_build()
    if info.short_sha == "unknown" or info.label == "unknown":
        fail("build identity is unknown")
    label = info.label
    index = (DIST / "index.html").read_text(errors="replace")
    if "GitHub Source" not in index or label not in index:
        fail("HTML build identity is missing")
    modern_text = _write_pdf_text(MODERN_PDF, BUILD / "modern" / "build-identity.txt")
    if label not in modern_text:
        fail("modern PDF build identity is missing")
    pdfinfo = subprocess.run(
        ["pdfinfo", str(FACSIMILE_PDF)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if label not in pdfinfo.stdout:
        fail("facsimile PDF build identity is missing")
    with zipfile.ZipFile(EPUB) as archive:
        payload = b"\n".join(
            archive.read(name)
            for name in archive.namelist()
            if name.lower().endswith((".xhtml", ".html", ".opf"))
        )
    if label.encode() not in payload:
        fail("EPUB exact build identity is missing")
    print(f"Build identity OK: {label}")


def check_checksums() -> None:
    try:
        count = verify_manifest(DIST, DEFAULT_FILES)
    except (FileNotFoundError, ValueError) as exc:
        fail(str(exc))
    print(f"Checksum manifest OK: {count} files")


def check_release_gate() -> None:
    tag = os.environ.get("WAVE_BUILD_VERSION") or os.environ.get("GITHUB_REF_NAME") or ""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        fail(
            "release tag must be a stable semantic version such as v1.0.0; "
            f"got: {tag or '<empty>'}"
        )
    info = current_build()
    if (
        info.version != tag
        or info.short_sha == "unknown"
        or info.label != f"{tag} ({info.short_sha})"
    ):
        fail("release build identity does not match the stable release tag")
    fac_pages = pdf_pages(FACSIMILE_PDF)
    if fac_pages != 184:
        fail(f"release blocked: facsimile page count is {fac_pages}; expected exactly 184")
    check_checksums()
    print(f"Release gate OK: {info.label}, facsimile={fac_pages} pages")


def check_publication() -> None:
    check_pdf_artifacts()
    check_publish_root()
    check_build_identity()
    check_checksums()


def check_pdf_artifacts() -> None:
    check_pdf_integrity()
    check_pdf_destinations()
    check_pdf_text()
    check_pdf_render()


def check_math(require_epubcheck: bool) -> None:
    check_canonical_source()
    check_readme()
    check_html()
    check_epub_mathml()
    check_pdf_math()
    run_epubcheck(require_epubcheck)
    print("Cross-format math validation OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate publication artifacts")
    parser.add_argument(
        "mode",
        choices=("math", "pdf", "publication", "release", "all"),
        nargs="?",
        default="all",
        help="validation scope (default: all non-release checks)",
    )
    parser.add_argument(
        "--require-epubcheck",
        action="store_true",
        help="fail math validation unless EPUBCheck is installed and passes",
    )
    args = parser.parse_args(argv)
    if args.mode in {"math", "all"}:
        check_math(args.require_epubcheck)
    if args.mode in {"publication", "all"}:
        check_publication()
    if args.mode == "pdf":
        check_pdf_artifacts()
    if args.mode == "release":
        check_release_gate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
