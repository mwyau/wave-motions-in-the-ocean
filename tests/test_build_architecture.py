from pathlib import Path

import pytest

import build_pdf

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {
    ".cache",
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "audit",
    "build",
    "release",
}


def test_pdf_builder_main_exposes_a_direct_no_argument_entry_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(build_pdf, "build_pdf", lambda: calls.append("pdf"))

    assert build_pdf.main([]) == 0
    assert calls == ["pdf"]


def test_pdf_builder_rejects_builder_options() -> None:
    with pytest.raises(SystemExit, match="does not accept options"):
        build_pdf.main(["--check"])


def test_pdf_builder_checks_the_pdfinfo_page_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = tmp_path / "edition.pdf"
    pdf.write_bytes(b"pdf")
    calls: list[list[str]] = []

    def fake_check_output(command: list[str], *, text: bool) -> str:
        assert text is True
        calls.append(command)
        return "Creator: test\nPages: 184\n"

    monkeypatch.setattr(build_pdf.subprocess, "check_output", fake_check_output)

    assert build_pdf._pdf_pages(pdf) == 184
    assert calls == [["pdfinfo", str(pdf)]]


def test_generated_text_is_not_rewritten_when_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "build-info.tex"
    path.write_text("generated\n")
    before = path.stat().st_mtime_ns

    build_pdf.write_if_changed(path, "generated\n")

    assert path.stat().st_mtime_ns == before


def test_removed_build_controls_are_absent_from_repository_text() -> None:
    removed_builder_name = "build" + ".sh"
    removed_validation_flag = "WAVE_SKIP_" + "VALIDATION"
    matches: list[Path] = []

    assert not (ROOT / "scripts" / removed_builder_name).exists()
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(
            directory in IGNORED_DIRECTORIES for directory in path.parts
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if removed_builder_name in text or removed_validation_flag in text:
            matches.append(path)

    assert matches == []
