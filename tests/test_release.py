import zipfile
from pathlib import Path

import pytest
from release import (
    CHECKSUM_ASSETS,
    DEFAULT_FILES,
    _checked_names,
    _safe_name,
    package_release,
    validate_offline_runtime,
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


def test_offline_runtime_accepts_local_html_and_css(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(
        '<link rel="stylesheet" href="assets/site.css">'
        '<script src="assets/app.js"></script>'
    )
    (tmp_path / "assets/site.css").write_text(
        '@import "local.css"; .page { background: url("../paper.png"); }'
    )

    validate_offline_runtime(tmp_path)


@pytest.mark.parametrize(
    ("html", "css"),
    [
        ('<script src="https://cdn.example/app.js"></script>', ""),
        ("", '@import url("https://cdn.example/site.css");'),
    ],
)
def test_offline_runtime_rejects_remote_dependencies(
    tmp_path: Path, html: str, css: str
) -> None:
    (tmp_path / "index.html").write_text(html)
    (tmp_path / "site.css").write_text(css)

    with pytest.raises(ValueError, match="remote runtime dependencies"):
        validate_offline_runtime(tmp_path)


def test_package_release_excludes_qa_facsimile_and_requires_public_members(
    tmp_path: Path,
) -> None:
    dist = tmp_path / "dist"
    output = tmp_path / "release"
    (dist / "assets").mkdir(parents=True)
    for name in DEFAULT_FILES + ("wave-motions-facsimile.pdf",):
        (dist / name).write_bytes(name.encode())
    write_manifest(dist, DEFAULT_FILES)
    (dist / "index.html").write_text('<script src="assets/app.js"></script>')
    (dist / "assets/app.js").write_text("console.log('local');")

    package_release(dist, output)

    assert verify_manifest(output, CHECKSUM_ASSETS) == len(CHECKSUM_ASSETS)
    with zipfile.ZipFile(output / "wave-motions-html.zip") as archive:
        names = set(archive.namelist())
    assert "index.html" in names
    assert "wave-motions.pdf" in names
    assert "wave-motions.epub" in names
    assert "wave-motions-facsimile.pdf" not in names


def test_package_release_rejects_missing_index_member(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    (dist / "other.html").parent.mkdir(parents=True)
    for name in DEFAULT_FILES:
        (dist / name).write_bytes(name.encode())
    (dist / "other.html").write_text("<p>not the index</p>")
    write_manifest(dist, DEFAULT_FILES)

    with pytest.raises(ValueError, match="missing: index.html"):
        package_release(dist, tmp_path / "release")
