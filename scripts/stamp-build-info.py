#!/usr/bin/env python3
"""Stamp generated HTML and EPUB outputs with the exact source revision."""
from __future__ import annotations

import argparse
import html
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from build_info import current_build

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EPUB = DIST / "wave-motions.epub"
HTML_STAMP_RE = re.compile(r'<footer class="build-info">.*?</footer>\s*', re.S)
EPUB_STAMP_RE = re.compile(br'<p class="build-info">.*?</p>\s*', re.S)


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
        text = HTML_STAMP_RE.sub("", text)
        if "</body>" not in text:
            raise SystemExit(f"HTML body end is missing from {path.name}")
        text = text.replace("</body>", footer + "\n</body>", 1)
        if text.count('class="build-info"') != 1:
            raise SystemExit(f"HTML build stamp count is not one in {path.name}")
        if label not in text or url not in text:
            raise SystemExit(f"HTML exact build stamp is missing from {path.name}")
        path.write_text(text)

    index = DIST / "index.html"
    index_text = index.read_text(errors="replace")
    if "GitHub Source" not in index_text or label not in index_text:
        raise SystemExit("HTML build stamp is missing from index.html")
    print(f"HTML build identity OK: {info.label}")


def stamp_epub() -> None:
    info = current_build()
    if not EPUB.is_file():
        raise SystemExit("EPUB output is missing")

    with zipfile.ZipFile(EPUB, "r") as source:
        names = source.namelist()
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        entries = [(item, source.read(item.filename)) for item in source.infolist()]

    label = html.escape(info.label)
    url = html.escape(info.commit_url, quote=True)
    paragraph = (
        '<p class="build-info">Digital edition build: '
        f'<a href="{url}"><code>{label}</code></a></p>'
    ).encode()

    stamped_xhtml = False
    rewritten: list[tuple[zipfile.ZipInfo, bytes]] = []
    for item, data in entries:
        if item.filename.lower().endswith((".xhtml", ".html")):
            data = EPUB_STAMP_RE.sub(b"", data)
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
        if xhtml.count(b'class="build-info"') != 1:
            raise SystemExit("EPUB build stamp count is not one")
        if label.encode() not in xhtml or info.commit_url.encode() not in xhtml:
            raise SystemExit("EPUB exact build identity is missing")

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
