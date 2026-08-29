#!/usr/bin/env python3
"""Build the modern and facsimile PDF editions."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from publication import (
    DOI,
    ROOT,
    SRC,
    current_build,
    prepare_publication_images,
    write_build_info_tex,
)

BUILD = ROOT / "build"
PUBLICATION = ROOT / "release"
CACHE = Path(os.environ.get("WAVE_CACHE_DIR", str(ROOT / ".cache" / "wave-motions")))
LATEX_CACHE = CACHE / "latex"


def require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"missing required command: {command}")


def prepare_bibtex() -> None:
    """Provide the bibtex command name expected by latexmk when needed."""
    if shutil.which("bibtex") is not None:
        return
    bibtex8 = shutil.which("bibtex8")
    if bibtex8 is None:
        raise SystemExit("missing required BibTeX executable (bibtex or bibtex8)")
    toolbin = BUILD / "toolbin"
    toolbin.mkdir(parents=True, exist_ok=True)
    link = toolbin / "bibtex"
    link.unlink(missing_ok=True)
    link.symlink_to(bibtex8)
    os.environ["PATH"] = f"{toolbin}{os.pathsep}{os.environ.get('PATH', '')}"


def prepare_build_info() -> None:
    """Write the generated TeX identity and paged-edition artwork inputs."""
    build_info = BUILD / "build-info.tex"
    write_build_info_tex(build_info, current_build())
    with build_info.open("a", encoding="utf-8") as output:
        output.write(f"\\providecommand{{\\wavedoi}}{{{DOI}}}\n")
    prepare_publication_images(BUILD / "publication-images")


def _latexmk(main: str, output: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            "latexmk",
            "-lualatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={output}",
            main,
        ],
        cwd=SRC,
        check=False,
    )


def run_latexmk_cached(main: str, kind: str) -> None:
    """Run one PDF build, retrying once when cached latexmk state is stale."""
    output = LATEX_CACHE / kind
    base = Path(main).with_suffix("").name
    had_state = (output / f"{base}.fdb_latexmk").is_file()
    output.mkdir(parents=True, exist_ok=True)

    result = _latexmk(main, output)
    if result.returncode == 0:
        return
    if not had_state:
        raise SystemExit(result.returncode)

    print(f"cached latexmk state for {kind} failed; retrying clean", file=sys.stderr)
    shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    result = _latexmk(main, output)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _pdf_pages(path: Path) -> int:
    try:
        text = subprocess.check_output(["pdfinfo", str(path)], text=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"could not inspect generated PDF: {path}") from exc
    match = re.search(r"(?m)^Pages:\s+(\d+)\s*$", text)
    if match is None or int(match.group(1)) <= 0:
        raise SystemExit(f"generated PDF has no positive page count: {path}")
    return int(match.group(1))


def build_pdf() -> None:
    """Build and copy both PDF editions without applying publication policy."""
    for command in ("latexmk", "lualatex", "pdfinfo"):
        require(command)
    prepare_bibtex()
    shutil.rmtree(BUILD / "facsimile", ignore_errors=True)
    shutil.rmtree(BUILD / "modern", ignore_errors=True)
    (BUILD / "facsimile").mkdir(parents=True, exist_ok=True)
    (BUILD / "modern").mkdir(parents=True, exist_ok=True)
    (LATEX_CACHE / "facsimile").mkdir(parents=True, exist_ok=True)
    (LATEX_CACHE / "modern").mkdir(parents=True, exist_ok=True)
    PUBLICATION.mkdir(parents=True, exist_ok=True)

    prepare_build_info()
    run_latexmk_cached("main-facsimile.tex", "facsimile")
    run_latexmk_cached("main-modern.tex", "modern")

    outputs = (
        (
            LATEX_CACHE / "facsimile" / "main-facsimile.pdf",
            PUBLICATION / "wave-motions-facsimile.pdf",
        ),
        (LATEX_CACHE / "modern" / "main-modern.pdf", PUBLICATION / "wave-motions.pdf"),
    )
    for source, destination in outputs:
        if not source.is_file() or source.stat().st_size == 0:
            raise SystemExit(f"PDF builder did not produce {source}")
        shutil.copy2(source, destination)

    facsimile_pages = _pdf_pages(PUBLICATION / "wave-motions-facsimile.pdf")
    modern_pages = _pdf_pages(PUBLICATION / "wave-motions.pdf")
    print(
        f"PDF build complete: facsimile={facsimile_pages} pages, "
        f"modern={modern_pages} pages"
    )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        raise SystemExit("build_pdf.py does not accept options")
    build_pdf()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
