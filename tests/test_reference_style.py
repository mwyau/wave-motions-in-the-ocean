from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIBLIOGRAPHY = ROOT / "src" / "references.bib"
AMS_CSL = ROOT / "src" / "layout" / "wave-ams.csl"
AMS_BST = ROOT / "src" / "layout" / "wave-ams.bst"


def book_page_totals() -> tuple[str, ...]:
    entries = re.findall(r"(?ms)^@book\s*\{.*?^\}", BIBLIOGRAPHY.read_text())
    totals: list[str] = []
    for entry in entries:
        match = re.search(r"(?m)^\s*pages\s*=\s*\{(\d+)\}", entry)
        assert match is not None
        totals.append(match.group(1))
    assert totals
    return tuple(totals)


def test_ams_csl_renders_book_page_totals(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc is not installed")
    source = tmp_path / "references.md"
    source.write_text("---\nnocite: '@*'\n---\n")
    result = subprocess.run(
        [
            pandoc,
            str(source),
            "--citeproc",
            f"--bibliography={BIBLIOGRAPHY}",
            f"--csl={AMS_CSL}",
            "-t",
            "html5",
            "--wrap=none",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    rendered = " ".join(result.split())
    for total in book_page_totals():
        assert rendered.count(f"{total} pp.") == 1
    assert "McGraw-Hill Book Company, New York" not in rendered


def test_ams_bst_renders_book_page_totals_once(tmp_path: Path) -> None:
    bibtex = shutil.which("bibtex") or shutil.which("bibtex8")
    if bibtex is None:
        pytest.skip("BibTeX is not installed")
    aux = tmp_path / "references.aux"
    aux.write_text(
        "\\relax\n"
        "\\citation{*}\n"
        f"\\bibstyle{{{AMS_BST.with_suffix('')}}}\n"
        f"\\bibdata{{{BIBLIOGRAPHY.with_suffix('')}}}\n"
    )
    subprocess.run(
        [bibtex, aux.stem],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    bbl = (tmp_path / "references.bbl").read_text()
    assert bbl.startswith("\\begin{thebibliography}{99}\n")
    assert "\\\\begin{thebibliography}" not in bbl
    assert "\\\\bibitem" not in bbl
    rendered = " ".join(bbl.split())
    for total in book_page_totals():
        assert rendered.count(f"{total} pp.") == 1
    assert "McGraw-Hill Book Company, New York" not in rendered
