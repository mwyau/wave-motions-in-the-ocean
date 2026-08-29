"""Build the modern and facsimile PDF editions."""

from __future__ import annotations

import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
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
    temporary_info: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=BUILD, prefix=".build-info-", suffix=".tex", delete=False
        ) as handle:
            temporary_info = Path(handle.name)
        write_build_info_tex(temporary_info, current_build())
        text = temporary_info.read_text(encoding="utf-8")
        text += f"\\providecommand{{\\wavedoi}}{{{DOI}}}\n"
        write_if_changed(build_info, text)
    finally:
        if temporary_info is not None:
            temporary_info.unlink(missing_ok=True)

    publication_images = BUILD / "publication-images"
    with tempfile.TemporaryDirectory(
        dir=BUILD, prefix="publication-images-"
    ) as temporary:
        generated = prepare_publication_images(Path(temporary))
        for source in generated:
            destination = publication_images / source.name
            copy_if_changed(source, destination)


def write_if_changed(path: Path, text: str) -> None:
    """Write deterministic generated text only when its contents changed."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_if_changed(source: Path, destination: Path) -> None:
    """Copy a deterministic generated asset only when its bytes changed."""
    if destination.is_file() and filecmp.cmp(source, destination, shallow=False):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


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
        raise SystemExit(f"latexmk failed for {kind} (exit {result.returncode})")

    print(f"cached latexmk state for {kind} failed; retrying clean", file=sys.stderr)
    shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    result = _latexmk(main, output)
    if result.returncode != 0:
        raise SystemExit(f"latexmk failed for {kind} (exit {result.returncode})")


def run_latexmk_parallel() -> None:
    """Build the independent edition variants concurrently in separate caches."""
    jobs = {
        "facsimile": "main-facsimile.tex",
        "modern": "main-modern.tex",
    }
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="latexmk") as pool:
        futures = {
            kind: pool.submit(run_latexmk_cached, main, kind)
            for kind, main in jobs.items()
        }
        for kind in jobs:
            futures[kind].result()


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
    run_latexmk_parallel()

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
