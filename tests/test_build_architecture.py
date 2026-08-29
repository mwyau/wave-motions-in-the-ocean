from pathlib import Path

import pytest

import build_pdf


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
