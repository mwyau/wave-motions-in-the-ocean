#!/usr/bin/env python3
"""Build the reflowable EPUB edition from transformed canonical LaTeX."""
from __future__ import annotations

import html
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
BUILD = ROOT / "build" / "epub"
HTML_SOURCE = ROOT / "build" / "html-pandoc" / "source"
RECON = ROOT / "reconstruction"
CSS = RECON / "styles" / "wave-epub.css"
EPUB = OUT / "wave-motions.epub"
COVER_DIR = BUILD / "cover"
COVER_PDF = COVER_DIR / "cover.pdf"
COVER_PNG = COVER_DIR / "cover.png"

TITLE = "Wave Motions in the Ocean: Myrl's View"
AUTHORS = ("David C. Chapman", "Paola Malanotte-Rizzoli")


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def canonical_inputs() -> list[Path]:
    paths = [HTML_SOURCE / "frontmatter.tex"] + [
        HTML_SOURCE / f"chapter{i}.tex" for i in range(1, 7)
    ]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit(
            "missing transformed canonical EPUB input(s): " + ", ".join(missing)
        )
    return paths


def render_cover() -> None:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    wrapper = COVER_DIR / "cover.tex"
    wrapper.write_text(
        r"""\documentclass[11pt,oneside]{report}
\usepackage{styles/wave-modern}
\begin{document}
\input{cover-modern}
\WaveModernCover
\clearpage
\nopagecolor
\end{document}
"""
    )
    env = os.environ.copy()
    texinputs = str(RECON) + "//:"
    if env.get("TEXINPUTS"):
        texinputs += env["TEXINPUTS"]
    env["TEXINPUTS"] = texinputs
    run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-jobname=cover",
            str(wrapper),
        ],
        cwd=COVER_DIR,
        env=env,
    )
    if not COVER_PDF.is_file() or COVER_PDF.stat().st_size == 0:
        raise SystemExit("shared PDF/EPUB cover rendering failed")
    run(
        [
            "pdftoppm",
            "-f", "1",
            "-l", "1",
            "-singlefile",
            "-r", "200",
            "-png",
            str(COVER_PDF),
            str(COVER_PNG.with_suffix("")),
        ]
    )
    if not COVER_PNG.is_file() or COVER_PNG.stat().st_size == 0:
        raise SystemExit("EPUB cover rasterization failed")


def write_metadata() -> Path:
    path = BUILD / "metadata.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"title: \"{TITLE}\"\n"
        "author:\n"
        + "".join(f"  - {author}\n" for author in AUTHORS)
        + "date: \"1989\"\n"
        "lang: en-US\n"
        "rights: \"CC BY-NC-SA 4.0\"\n"
        "identifier: \"https://mwyau.github.io/wave-motions-in-the-ocean/\"\n"
        "contributor: \"Albert M. W. Yau (digital editor)\"\n"
        "---\n"
    )
    return path


def build_epub(inputs: list[Path], metadata: Path) -> None:
    EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB.unlink(missing_ok=True)
    resource_path = os.pathsep.join((str(OUT), str(HTML_SOURCE), str(RECON)))
    run(
        [
            "pandoc",
            *(str(path) for path in inputs),
            "-f", "latex",
            "-t", "epub3",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            "--mathml",
            "--citeproc",
            f"--bibliography={RECON / 'references.bib'}",
            "--metadata", "nocite=@*",
            "--metadata-file", str(metadata),
            "--metadata", f"title={TITLE}",
            "--css", str(CSS),
            "--epub-cover-image", str(COVER_PNG),
            "--resource-path", resource_path,
            "-o", str(EPUB),
        ]
    )


def validate_epub() -> None:
    if not EPUB.is_file() or EPUB.stat().st_size == 0:
        raise SystemExit("EPUB output is missing or empty")
    with zipfile.ZipFile(EPUB) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        if archive.read("mimetype") != b"application/epub+zip":
            raise SystemExit("invalid EPUB mimetype")
        if "META-INF/container.xml" not in names:
            raise SystemExit("EPUB container.xml is missing")
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"corrupt EPUB member: {bad}")

        opf_names = [name for name in names if name.lower().endswith(".opf")]
        if len(opf_names) != 1:
            raise SystemExit(f"expected one EPUB package document, found {len(opf_names)}")
        opf = archive.read(opf_names[0]).decode("utf-8", errors="replace")
        if TITLE not in html.unescape(opf):
            raise SystemExit("EPUB metadata title is missing or incorrect")
        if not all(author in opf for author in AUTHORS):
            raise SystemExit("EPUB author metadata is incomplete")

        xhtml = b"\n".join(
            archive.read(name)
            for name in names
            if name.lower().endswith((".xhtml", ".html"))
        )
        if b"<math" not in xhtml:
            raise SystemExit("EPUB contains no MathML; mathematical rendering regressed")
        if b"David C. Chapman" not in xhtml or b"Paola Malanotte-Rizzoli" not in xhtml:
            raise SystemExit("EPUB text sentinel is missing")

    print(f"EPUB build OK: {EPUB.relative_to(ROOT)} ({EPUB.stat().st_size} bytes)")


def main() -> int:
    for command in ("pandoc", "pdflatex", "pdftoppm"):
        if shutil.which(command) is None:
            raise SystemExit(f"missing required command: {command}")
    if not CSS.is_file():
        raise SystemExit(f"missing EPUB stylesheet: {CSS}")
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    inputs = canonical_inputs()
    render_cover()
    metadata = write_metadata()
    build_epub(inputs, metadata)
    validate_epub()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
