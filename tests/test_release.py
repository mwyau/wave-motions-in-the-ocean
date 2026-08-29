import zipfile
from pathlib import Path

import pytest

from release import (
    DEFAULT_FILES,
    HTML_ARCHIVE,
    HTML_ARCHIVE_EXCLUDED,
    MANIFEST,
    _checked_names,
    _safe_name,
    archive_publication,
    finalize_publication,
    html_archive_files,
    publication_files,
    sha256,
    verify_manifest,
    write_manifest,
)


def test_safe_relative_names_are_accepted() -> None:
    assert _safe_name("assets/index.html") == "assets/index.html"


@pytest.mark.parametrize("name", ["../index.html", "/tmp/index.html", "", "SHA256SUMS"])
def test_unsafe_checksum_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="unsafe checksum path"):
        _safe_name(name)


def test_duplicate_checksum_targets_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate paths"):
        _checked_names(["wave-motions.pdf", "wave-motions.pdf"])


def test_checksum_manifest_round_trip(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha")
    (tmp_path / "b.txt").write_text("beta")

    manifest = write_manifest(tmp_path, ["a.txt", "b.txt"])

    assert manifest.name == "SHA256SUMS"
    assert verify_manifest(tmp_path, ["a.txt", "b.txt"]) == 2


def test_checksum_mismatch_is_detected(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("before")
    write_manifest(tmp_path, ["a.txt"])
    target.write_text("after")

    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_manifest(tmp_path)


def test_checksum_expected_names_report_missing_and_unexpected(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    write_manifest(tmp_path, ["a.txt"])
    with pytest.raises(ValueError, match="missing: b.txt"):
        verify_manifest(tmp_path, ["a.txt", "b.txt"])

    write_manifest(tmp_path, ["a.txt", "b.txt"])
    with pytest.raises(ValueError, match="unexpected: b.txt"):
        verify_manifest(tmp_path, ["a.txt"])


def test_malformed_checksum_line_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "SHA256SUMS").write_text("not-a-digest  a.txt\n")

    with pytest.raises(ValueError, match="invalid checksum line"):
        verify_manifest(tmp_path)


def make_publication_root(tmp_path: Path) -> Path:
    root = tmp_path / "release"
    (root / "assets" / "licenses").mkdir(parents=True)
    for name in DEFAULT_FILES + ("wave-motions-facsimile.pdf",):
        (root / name).write_bytes(name.encode())
    (root / "index.html").write_text('<script src="assets/app.js"></script>')
    (root / "assets/app.js").write_text("console.log('local');")
    (root / "assets/figure.png").write_bytes(b"png")
    (root / "assets/licenses/MathJax.txt").write_text("Apache-2.0")
    return root


def test_finalize_publication_does_not_create_html_archive(tmp_path: Path) -> None:
    root = make_publication_root(tmp_path)

    finalize_publication(root)

    assert (root / "wave-motions-facsimile.pdf").is_file()
    names = publication_files(root)
    assert "assets/figure.png" in names
    assert verify_manifest(root, names) == len(names)
    assert not (root / HTML_ARCHIVE).exists()


def test_html_archive_file_set_excludes_separate_publication_formats(
    tmp_path: Path,
) -> None:
    root = make_publication_root(tmp_path)

    names = html_archive_files(root)

    assert "index.html" in names
    assert "assets/figure.png" in names
    assert "assets/licenses/MathJax.txt" in names
    assert HTML_ARCHIVE_EXCLUDED.isdisjoint(names)


def test_archive_publication_contains_only_html_reader_tree(tmp_path: Path) -> None:
    root = make_publication_root(tmp_path)
    finalize_publication(root)
    output = tmp_path / HTML_ARCHIVE

    archive_publication(root, output)

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        manifest = archive.read(MANIFEST).decode()
    assert "index.html" in names
    assert "assets/app.js" in names
    assert "assets/figure.png" in names
    assert "assets/licenses/MathJax.txt" in names
    assert MANIFEST in names
    assert HTML_ARCHIVE not in names
    assert HTML_ARCHIVE_EXCLUDED.isdisjoint(names)

    expected = html_archive_files(root)
    expected_manifest = "".join(f"{sha256(root / name)}  {name}\n" for name in expected)
    assert manifest == expected_manifest


def test_finalize_publication_rejects_missing_index_member(tmp_path: Path) -> None:
    root = tmp_path / "release"
    root.mkdir()
    for name in DEFAULT_FILES + ("wave-motions-facsimile.pdf",):
        (root / name).write_bytes(name.encode())

    with pytest.raises(FileNotFoundError, match="index.html"):
        finalize_publication(root)
