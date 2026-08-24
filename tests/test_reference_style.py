from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIBLIOGRAPHY = ROOT / "src" / "references.bib"
AMS_CSL = ROOT / "src" / "layout" / "wave-ams.csl"
AMS_BST = ROOT / "src" / "layout" / "wave-ams.bst"
BOOK_EXPECTATIONS = {
    "pedlosky1979": (
        "Geophysical Fluid Dynamics",
        "Springer-Verlag",
        "624 pp.",
    )
}
JOURNAL_ABBREVIATIONS = {
    "bjerknes1937": ("Meteorologische Zeitschrift", "Meteorol. Z."),
    "gillschumann1974": (
        "Journal of Physical Oceanography",
        "J. Phys. Oceanogr.",
    ),
    "hendershottsperanza1971": ("Deep-Sea Research", "Deep-Sea Res."),
    "hough1897": (
        "Philosophical Transactions of the Royal Society of London A",
        "Philos. Trans. R. Soc. Lond. A",
    ),
    "hough1898": (
        "Philosophical Transactions of the Royal Society of London A",
        "Philos. Trans. R. Soc. Lond. A",
    ),
    "huthnance1975": ("Journal of Fluid Mechanics", "J. Fluid Mech."),
    "huthnance1978": (
        "Journal of Physical Oceanography",
        "J. Phys. Oceanogr.",
    ),
    "rhines1970": ("Geophysical Fluid Dynamics", "Geophys. Fluid Dyn."),
    "rossby1939": ("Journal of Marine Research", "J. Mar. Res."),
}
REQUIRE_REFERENCE_TOOLS = os.environ.get("WAVE_REQUIRE_REFERENCE_TOOLS") == "1"


def reference_command(*names: str) -> str:
    for name in names:
        command = shutil.which(name)
        if command is not None:
            return command
    message = f"required reference-style tool is unavailable: {', '.join(names)}"
    if REQUIRE_REFERENCE_TOOLS:
        pytest.fail(message)
    pytest.skip(message)


def book_page_totals() -> tuple[str, ...]:
    entries = re.findall(r"(?ms)^@book\s*\{.*?^\}", BIBLIOGRAPHY.read_text())
    totals: list[str] = []
    for entry in entries:
        match = re.search(r"(?m)^\s*pages\s*=\s*\{(\d+)\}", entry)
        assert match is not None
        totals.append(match.group(1))
    assert totals
    return tuple(totals)


def reference_block(rendered: str, key: str) -> str:
    patterns = (
        rf'id="ref-{re.escape(key)}"[^>]*>(.*?)(?=<div id="ref-|\Z)',
        rf"\\bibitem(?:\[[^]]*\])?\{{{re.escape(key)}\}}(.*?)(?=\s*\\bibitem|\Z)",
    )
    match = next(
        (
            match
            for pattern in patterns
            if (match := re.search(pattern, rendered, re.DOTALL))
        ),
        None,
    )
    assert match is not None, f"reference block not found for {key}"
    return match.group(1)


def assert_book_titles_are_not_abbreviated(rendered: str) -> None:
    for key, (title, publisher, pages) in BOOK_EXPECTATIONS.items():
        block = reference_block(rendered, key)
        assert title in block
        assert publisher in block
        assert pages in block
        assert "Geophys. Fluid Dyn." not in block


def assert_ams_journal_abbreviations(rendered: str) -> None:
    for key, (full, short) in JOURNAL_ABBREVIATIONS.items():
        block = reference_block(rendered, key)
        assert block.count(short) == 1
        assert full not in block


def assert_rhines_article_reference(rendered: str) -> None:
    block = reference_block(rendered, "rhines1970")
    assert re.search(r"Geophys\. Fluid Dyn\..*?\b1\b.*?273(?:--|–)302", block)


def test_ams_csl_renders_book_page_totals(tmp_path: Path) -> None:
    pandoc = reference_command("pandoc")
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
    assert_book_titles_are_not_abbreviated(rendered)
    assert_ams_journal_abbreviations(rendered)
    assert_rhines_article_reference(rendered)


def test_ams_bst_renders_book_page_totals_once(tmp_path: Path) -> None:
    bibtex = reference_command("bibtex", "bibtex8")
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
    assert_book_titles_are_not_abbreviated(rendered)
    assert_ams_journal_abbreviations(rendered)
    assert_rhines_article_reference(rendered)
