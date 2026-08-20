#!/usr/bin/env python3
"""Stamp generated HTML and EPUB outputs with the exact source revision."""
from __future__ import annotations

import argparse
import html
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from build_info import current_build

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EPUB = DIST / "wave-motions.epub"


def stamp_html() -> None:
    info = current_build()
    pages = sorted(DIST.glob("*.html"))
    if not pages:
        raise SystemExit("no HTML pages found to stamp")

    label = html.escape(info.label)
    url = html.escape(info.commit_url, quote=True)
    footer = (
        '<footer class="build-info">Digital edition build: '
        f'<a href="{url}"><code>{label}</code></a></footer>'
    )

    for path in pages:
        text = path.read_text(errors="replace")
        text = text.replace(">Repository</a>", ">GitHub Source</a>")
        if 'class="build-info"' not in text:
            text = text.replace("</body>", footer + "\n</body>", 1)
        path.write_text(text)

    index = DIST / "index.html"
    index_text = index.read_text(errors="replace")
    if "GitHub Source" not in index_text or info.short_sha not in index_text:
        raise SystemExit("HTML build stamp is missing from index.html")
    print(f"HTML build identity OK: {info.label}")


def _epub_rootfile(archive: zipfile.ZipFile) -> str:
    root = ET.fromstring(archive.read("META-INF/container.xml"))
    node = root.find(".//{*}rootfile")
    if node is None or not node.get("full-path"):
        raise SystemExit("EPUB container has no package rootfile")
    return node.get("full-path") or ""


def stamp_epub() -> None:
    info = current_build()
    if not EPUB.is_file():
        raise SystemExit("EPUB output is missing")

    with zipfile.ZipFile(EPUB, "r") as source:
        names = source.namelist()
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        entries = [(item, source.read(item.filename)) for item in source.infolist()]
        opf_name = _epub_rootfile(source)

    label = html.escape(info.label)
    url = html.escape(info.commit_url, quote=True)
    paragraph = (
        '<p class="build-info">Digital edition build: '
        f'<a href="{url}"><code>{label}</code></a></p>'
    ).encode()

    stamped_xhtml = False
    rewritten: list[tuple[zipfile.ZipInfo, bytes]] = []
    for item, data in entries:
        if (
            not stamped_xhtml
            and item.filename.lower().endswith((".xhtml", ".html"))
            and b"Albert M. W. Yau" in data
        ):
            marker = b"</section>" if b"</section>" in data else b"</body>"
            pos = data.rfind(marker)
            if pos >= 0:
                data = data[:pos] + paragraph + b"\n" + data[pos:]
                stamped_xhtml = True

        if item.filename == opf_name:
            try:
                root = ET.fromstring(data)
            except ET.ParseError as exc:
                raise SystemExit(f"invalid EPUB package document: {exc}") from exc
            metadata = root.find("{*}metadata")
            if metadata is None:
                raise SystemExit("EPUB package metadata is missing")
            dc = "http://purl.org/dc/elements/1.1/"
            existing = metadata.findall(f"{{{dc}}}source")
            for node in existing:
                metadata.remove(node)
            source_node = ET.SubElement(metadata, f"{{{dc}}}source")
            source_node.text = info.commit_url
            data = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        rewritten.append((item, data))

    if not stamped_xhtml:
        raise SystemExit("could not locate EPUB editor front matter for build stamp")

    with tempfile.NamedTemporaryFile(
        prefix="wave-motions-", suffix=".epub", dir=EPUB.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)

    try:
        with zipfile.ZipFile(tmp, "w") as target:
            for item, data in rewritten:
                compress_type = zipfile.ZIP_STORED if item.filename == "mimetype" else item.compress_type
                target.writestr(item, data, compress_type=compress_type)
        shutil.move(tmp, EPUB)
    finally:
        tmp.unlink(missing_ok=True)

    with zipfile.ZipFile(EPUB, "r") as archive:
        if archive.testzip() is not None:
            raise SystemExit("EPUB became corrupt while stamping build identity")
        if archive.namelist()[0] != "mimetype" or archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            raise SystemExit("EPUB mimetype entry is invalid after build stamping")
        xhtml = b"\n".join(
            archive.read(name)
            for name in archive.namelist()
            if name.lower().endswith((".xhtml", ".html"))
        )
        if info.short_sha.encode() not in xhtml:
            raise SystemExit("EPUB visible build identity is missing")
        opf = archive.read(_epub_rootfile(archive))
        if info.commit_url.encode() not in opf:
            raise SystemExit("EPUB source-revision metadata is missing")

    print(f"EPUB build identity OK: {info.label}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--epub", action="store_true")
    args = parser.parse_args()
    if not args.html and not args.epub:
        args.html = args.epub = True
    if args.html:
        stamp_html()
    if args.epub:
        stamp_epub()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
