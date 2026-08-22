#!/usr/bin/env python3
"""Build a structurally usable EPUB3 from canonical flowing sources.

This builder prepares its own generated TeX and figures, then applies the
single final EPUB ZIP rewrite for metadata, accessibility, bodymatter,
language, and build identity before returning a completed artifact.
"""
from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from publication import current_build, prepare_assets, prepare_flowing_sources

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
BUILD = ROOT / "build" / "epub"
RECON = ROOT / "reconstruction"
CSS = RECON / "styles" / "wave-epub.css"
EPUB = OUT / "wave-motions.epub"
COVER_DIR = BUILD / "cover"
COVER_PDF = COVER_DIR / "cover.pdf"
COVER_PNG = COVER_DIR / "cover.png"

TITLE = "Wave Motions in the Ocean: Myrl's View"
AUTHORS = ("David C. Chapman", "Paola Malanotte-Rizzoli")
EDITOR = "Albert M. W. Yau (digital editor)"
NAV_SENTINELS = (
    "Basic concepts",
    "Acoustic waves",
    "Surface gravity waves",
    "Internal gravity waves",
    "Shallow water dynamics",
    "Topographic effects",
    "References",
)

OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
EPUB_TYPE = f"{{{EPUB_NS}}}type"
LANGUAGE = "en-US"
ACCESSIBILITY_SUMMARY = (
    "Mathematics is encoded as MathML and the EPUB includes linked table-of-contents navigation. "
    "Scientific figures do not yet have complete alternative text or extended descriptions, so visual access is required for full use."
)
ACCESSIBILITY_METADATA: tuple[tuple[str, str], ...] = (
    ("schema:accessMode", "textual"),
    ("schema:accessMode", "visual"),
    ("schema:accessModeSufficient", "textual,visual"),
    ("schema:accessibilityFeature", "MathML"),
    ("schema:accessibilityFeature", "tableOfContents"),
    ("schema:accessibilityHazard", "none"),
    ("schema:accessibilitySummary", ACCESSIBILITY_SUMMARY),
)
ACCESSIBILITY_PROPERTIES = {name for name, _ in ACCESSIBILITY_METADATA}
GENERIC_ALT_TEXT = {"image", "figure"}
FRONTISPIECE_BASENAME = "salmon-hendershott-como-1980.jpg"
FRONTISPIECE_ALTERNATIVE = (
    "Rick Salmon (left) and Myrl Hendershott at Villa Carlotta, Lake Como, "
    "during the International School of Physics Enrico Fermi, Course LXXX, "
    "Topics in Ocean Physics, July 1980."
)
COVER_ALTERNATIVE = (
    "Cover of Wave Motions in the Ocean: Myrl's View, featuring Katsushika "
    "Hokusai's Under the Wave off Kanagawa (The Great Wave)."
)
BUILD_STAMP_RE = re.compile(br'<p class="build-info">.*?</p>\s*', re.S)


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def normalize_epub_math_tex(text: str) -> str:
    """Apply EPUB-only compatibility changes to generated TeX."""
    return re.sub(r"\\ell(?![A-Za-z])", "{ℓ}", text)


def epub_inputs() -> list[Path]:
    source_dir = BUILD / "source"
    paths = prepare_flowing_sources(source_dir, BUILD)
    frontmatter = paths[0]
    credit_source = RECON / "cover-credit.tex"
    if not credit_source.is_file():
        raise SystemExit(f"missing cover credit source: {credit_source}")
    front_text = frontmatter.read_text()
    marker = r"\wavecovercredit"
    if marker not in front_text:
        raise SystemExit("EPUB front matter is missing the cover-credit marker")
    frontmatter.write_text(front_text.replace(marker, credit_source.read_text().strip(), 1))

    for chapter in paths[1:]:
        chapter.write_text(normalize_epub_math_tex(chapter.read_text()))

    references = source_dir / "references.tex"
    references.write_text("\\chapter{References}\n")
    return [*paths, references]


def render_cover() -> None:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    wrapper = COVER_DIR / "cover.tex"
    wrapper.write_text(
        r"""\documentclass[11pt,oneside]{report}
\usepackage{styles/wave-modern}
\begin{document}
\input{cover-modern}
\WaveModernCover
\clearpage
\nopagecolor
\end{document}
"""
    )
    env = os.environ.copy()
    texinputs = str(RECON) + "//:"
    if env.get("TEXINPUTS"):
        texinputs += env["TEXINPUTS"]
    env["TEXINPUTS"] = texinputs
    run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-jobname=cover",
            str(wrapper),
        ],
        cwd=COVER_DIR,
        env=env,
    )
    if not COVER_PDF.is_file() or COVER_PDF.stat().st_size == 0:
        raise SystemExit("shared PDF/EPUB cover rendering failed")
    run(
        [
            "pdftoppm",
            "-f",
            "1",
            "-l",
            "1",
            "-singlefile",
            "-r",
            "200",
            "-png",
            str(COVER_PDF),
            str(COVER_PNG.with_suffix("")),
        ]
    )
    if not COVER_PNG.is_file() or COVER_PNG.stat().st_size == 0:
        raise SystemExit("EPUB cover rasterization failed")


def write_metadata() -> Path:
    path = BUILD / "metadata.yaml"
    path.write_text(
        "---\n"
        f'title: "{TITLE}"\n'
        "author:\n"
        + "".join(f"  - {author}\n" for author in AUTHORS)
        + 'date: "1989"\n'
        'lang: en-US\n'
        'rights: "CC BY-NC-SA 4.0"\n'
        'identifier: "https://mwyau.github.io/wave-motions-in-the-ocean/"\n'
        f'contributor: "{EDITOR}"\n'
        "---\n"
    )
    return path


def build_epub(inputs: list[Path], metadata: Path) -> None:
    EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB.unlink(missing_ok=True)
    resource_path = os.pathsep.join((str(BUILD), str(BUILD / "source"), str(OUT), str(RECON)))
    run(
        [
            "pandoc",
            *(str(path) for path in inputs),
            "-f",
            "latex",
            "-t",
            "epub3",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            "--mathml",
            "--citeproc",
            f"--bibliography={RECON / 'references.bib'}",
            "--metadata",
            "nocite=@*",
            "--metadata-file",
            str(metadata),
            "--metadata",
            f"title={TITLE}",
            "--css",
            str(CSS),
            "--epub-cover-image",
            str(COVER_PNG),
            "--resource-path",
            resource_path,
            "-o",
            str(EPUB),
        ]
    )


def text_content(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def resolved_member(base: str, ref: str) -> str | None:
    parsed = urllib.parse.urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        return None
    if not parsed.path:
        return base if parsed.fragment else None
    path = urllib.parse.unquote(parsed.path)
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), path))


def xhtml_ids(archive: zipfile.ZipFile, name: str) -> set[str]:
    try:
        root = ET.fromstring(archive.read(name))
    except ET.ParseError as exc:
        raise SystemExit(f"invalid EPUB XHTML in {name}: {exc}") from exc
    return {value for element in root.iter() if (value := element.get("id"))}


def validate_internal_refs(archive: zipfile.ZipFile, xhtml_names: list[str]) -> None:
    names = set(archive.namelist())
    xhtml_name_set = set(xhtml_names)
    ids_by_name = {name: xhtml_ids(archive, name) for name in xhtml_names}
    broken: list[tuple[str, str]] = []
    ref_re = re.compile(rb'(?:href|src)=["\']([^"\']+)["\']', re.I)
    for name in xhtml_names:
        for raw_ref in ref_re.findall(archive.read(name)):
            ref = html.unescape(raw_ref.decode("utf-8", errors="replace"))
            parsed = urllib.parse.urlsplit(ref)
            member = resolved_member(name, ref)
            if member is None:
                continue
            if member not in names:
                broken.append((name, ref))
                continue
            if parsed.fragment and member in xhtml_name_set:
                fragment = urllib.parse.unquote(parsed.fragment)
                if fragment not in ids_by_name[member]:
                    broken.append((name, ref))
    if broken:
        for name, ref in broken[:20]:
            print(f"broken EPUB reference: {name}: {ref}")
        raise SystemExit(f"EPUB contains {len(broken)} broken internal reference(s)")


def package_document(archive: zipfile.ZipFile) -> tuple[str, ET.Element]:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = container.find(".//{*}rootfile")
        if rootfile is None or not rootfile.get("full-path"):
            raise ValueError("container has no package rootfile")
        name = rootfile.get("full-path")
        assert name is not None
        return name, ET.fromstring(archive.read(name))
    except (KeyError, ET.ParseError, ValueError) as exc:
        raise SystemExit(f"EPUB package structure is invalid: {exc}") from exc


def validate_epub() -> None:
    if not EPUB.is_file() or EPUB.stat().st_size == 0:
        raise SystemExit("EPUB output is missing or empty")
    with zipfile.ZipFile(EPUB) as archive:
        names = archive.namelist()
        name_set = set(names)
        if not names or names[0] != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        if archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            raise SystemExit("EPUB mimetype entry is compressed")
        if archive.read("mimetype") != b"application/epub+zip":
            raise SystemExit("invalid EPUB mimetype")
        if "META-INF/container.xml" not in name_set:
            raise SystemExit("EPUB container.xml is missing")
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"corrupt EPUB member: {bad}")

        opf_name, opf_root = package_document(archive)
        if opf_name not in name_set:
            raise SystemExit(f"EPUB package document is missing: {opf_name}")
        metadata = opf_root.find("{*}metadata")
        manifest = opf_root.find("{*}manifest")
        spine = opf_root.find("{*}spine")
        if metadata is None or manifest is None or spine is None:
            raise SystemExit("EPUB package metadata/manifest/spine is incomplete")

        title = metadata.find("{http://purl.org/dc/elements/1.1/}title")
        if title is None or text_content(title) != TITLE:
            got = text_content(title) if title is not None else "<missing>"
            raise SystemExit(f"EPUB metadata title is incorrect: {got!r}")
        creators = [
            text_content(item)
            for item in metadata.findall("{http://purl.org/dc/elements/1.1/}creator")
        ]
        if not all(author in creators for author in AUTHORS):
            raise SystemExit(f"EPUB author metadata is incomplete: {creators!r}")

        manifest_items = list(manifest.findall("{*}item"))
        contributors = [
            text_content(item)
            for item in metadata.findall("{http://purl.org/dc/elements/1.1/}contributor")
        ]
        if EDITOR not in contributors:
            raise SystemExit(f"EPUB editor metadata is missing: {contributors!r}")
        by_id = {item.get("id"): item for item in manifest_items if item.get("id")}
        package_dir = posixpath.dirname(opf_name)

        cover_items = [
            item
            for item in manifest_items
            if "cover-image" in (item.get("properties") or "").split()
        ]
        if len(cover_items) != 1:
            raise SystemExit(f"expected one EPUB cover image, found {len(cover_items)}")
        cover_member = posixpath.normpath(
            posixpath.join(package_dir, urllib.parse.unquote(cover_items[0].get("href") or ""))
        )
        if cover_member not in name_set:
            raise SystemExit(f"EPUB cover image member is missing: {cover_member}")

        nav_items = [
            item for item in manifest_items if "nav" in (item.get("properties") or "").split()
        ]
        if len(nav_items) != 1 or not nav_items[0].get("href"):
            raise SystemExit("EPUB navigation document is missing or ambiguous")
        nav_name = posixpath.normpath(
            posixpath.join(package_dir, urllib.parse.unquote(nav_items[0].get("href") or ""))
        )
        if nav_name not in name_set:
            raise SystemExit(f"EPUB navigation member is missing: {nav_name}")
        nav_root = ET.fromstring(archive.read(nav_name))
        nav_text = " ".join(text_content(a) for a in nav_root.findall(".//{*}a"))
        for sentinel in NAV_SENTINELS:
            if sentinel not in nav_text:
                raise SystemExit(f"EPUB navigation is missing: {sentinel}")
        if nav_text.strip() == "References":
            raise SystemExit("EPUB navigation regressed to a References-only title")

        spine_ids = [item.get("idref") for item in spine.findall("{*}itemref")]
        if len(spine_ids) < 8 or any(item_id not in by_id for item_id in spine_ids):
            raise SystemExit("EPUB spine is unexpectedly short or references missing manifest items")

        xhtml_items = {
            posixpath.normpath(
                posixpath.join(package_dir, urllib.parse.unquote(item.get("href") or ""))
            ): item
            for item in manifest_items
            if item.get("media-type") == "application/xhtml+xml" and item.get("href")
        }
        xhtml_names = list(xhtml_items)
        if not xhtml_names or any(name not in name_set for name in xhtml_names):
            raise SystemExit("EPUB XHTML manifest is incomplete")
        validate_internal_refs(archive, xhtml_names)

        xhtml = b"\n".join(archive.read(name) for name in xhtml_names)
        if b"David C. Chapman" not in xhtml or b"Paola Malanotte-Rizzoli" not in xhtml:
            raise SystemExit("EPUB text sentinel is missing")
        if b"JP1847" not in xhtml:
            raise SystemExit("EPUB cover credit is missing")
        if b"<table" not in xhtml:
            raise SystemExit("EPUB contains no table markup")
        image_count = sum(
            1 for item in manifest_items if (item.get("media-type") or "").startswith("image/")
        )
        if image_count < 5:
            raise SystemExit(f"EPUB contains only {image_count} image asset(s)")
    print(f"EPUB build OK: {EPUB.relative_to(ROOT)} ({EPUB.stat().st_size} bytes)")


def manifest_member(opf_name: str, item: ET.Element) -> str:
    href = urllib.parse.unquote(item.get("href") or "")
    return posixpath.normpath(posixpath.join(posixpath.dirname(opf_name), href))


def manifest_xhtml_members(opf_name: str, opf_root: ET.Element) -> list[str]:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    return [
        manifest_member(opf_name, item)
        for item in manifest.findall("{*}item")
        if item.get("media-type") == "application/xhtml+xml" and item.get("href")
    ]


def navigation_member(
    opf_name: str,
    opf_root: ET.Element,
    *,
    required: bool = True,
) -> str | None:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    items = [
        item
        for item in manifest.findall("{*}item")
        if "nav" in (item.get("properties") or "").split()
    ]
    if len(items) != 1 or not items[0].get("href"):
        if required:
            raise SystemExit("EPUB navigation document is missing or ambiguous")
        return None
    return manifest_member(opf_name, items[0])


def first_bodymatter_member(
    source: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
    *,
    required: bool = True,
) -> str | None:
    manifest = opf_root.find("{*}manifest")
    spine = opf_root.find("{*}spine")
    if manifest is None or spine is None:
        if required:
            raise SystemExit("EPUB manifest/spine is incomplete")
        return None
    by_id = {
        item.get("id"): item
        for item in manifest.findall("{*}item")
        if item.get("id")
    }
    for itemref in spine.findall("{*}itemref"):
        item = by_id.get(itemref.get("idref"))
        if item is None or item.get("media-type") != "application/xhtml+xml":
            continue
        member = manifest_member(opf_name, item)
        try:
            root = ET.fromstring(source.read(member))
        except (KeyError, ET.ParseError) as exc:
            raise SystemExit(f"cannot parse EPUB XHTML {member}: {exc}") from exc
        body = root.find(".//{*}body")
        if body is not None and "bodymatter" in (body.get(EPUB_TYPE) or "").split():
            return member
    if required:
        raise SystemExit("EPUB spine has no bodymatter content document")
    return None


def cover_image_basename(opf_root: ET.Element, *, required: bool = True) -> str | None:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    items = [
        item
        for item in manifest.findall("{*}item")
        if "cover-image" in (item.get("properties") or "").split()
    ]
    if len(items) != 1 or not items[0].get("href"):
        if required:
            raise SystemExit(f"expected one EPUB cover image, found {len(items)}")
        return None
    href = urllib.parse.unquote(items[0].get("href") or "")
    return posixpath.basename(urllib.parse.urlsplit(href).path)


def ref_basename(ref: str | None) -> str:
    if not ref:
        return ""
    parsed = urllib.parse.urlsplit(ref)
    return posixpath.basename(urllib.parse.unquote(parsed.path))


def svg_image_ref(image: ET.Element) -> str | None:
    return image.get(f"{{{XLINK_NS}}}href") or image.get("href")


def set_svg_accessible_name(svg: ET.Element, text: str) -> None:
    svg.set("role", "img")
    svg.set("aria-label", text)
    title = svg.find(f"{{{SVG_NS}}}title")
    if title is None:
        title = ET.Element(f"{{{SVG_NS}}}title")
        svg.insert(0, title)
    title.text = text


def ensure_bodymatter_landmark(root: ET.Element, nav_member: str, bodymatter_member: str) -> bool:
    landmarks = [
        nav
        for nav in root.findall(".//{*}nav")
        if "landmarks" in (nav.get(EPUB_TYPE) or "").split()
    ]
    if len(landmarks) != 1:
        raise SystemExit(f"expected one EPUB landmarks navigation element, found {len(landmarks)}")
    landmark = landmarks[0]
    existing = [
        link
        for link in landmark.findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    expected_href = posixpath.relpath(bodymatter_member, posixpath.dirname(nav_member) or ".")
    if existing:
        if len(existing) != 1:
            raise SystemExit("EPUB landmarks contain multiple bodymatter entries")
        target = urllib.parse.unquote(urllib.parse.urlsplit(existing[0].get("href") or "").path)
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(nav_member), target))
        if resolved != bodymatter_member:
            raise SystemExit("EPUB bodymatter landmark points to the wrong content document")
        return False
    ordered_list = landmark.find("./{*}ol")
    if ordered_list is None:
        raise SystemExit("EPUB landmarks navigation has no ordered list")
    item = ET.SubElement(ordered_list, f"{{{XHTML_NS}}}li")
    link = ET.SubElement(item, f"{{{XHTML_NS}}}a", {"href": expected_href, EPUB_TYPE: "bodymatter"})
    link.text = "Start reading"
    return True


def set_known_accessibility(
    source: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> dict[str, bytes]:
    cover_basename = cover_image_basename(opf_root, required=False)
    nav_member = navigation_member(opf_name, opf_root, required=False)
    bodymatter_member = first_bodymatter_member(source, opf_name, opf_root, required=False)
    rewritten: dict[str, bytes] = {}
    ET.register_namespace("", XHTML_NS)
    ET.register_namespace("epub", EPUB_NS)
    ET.register_namespace("svg", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)

    for member in manifest_xhtml_members(opf_name, opf_root):
        try:
            root = ET.fromstring(source.read(member))
        except (KeyError, ET.ParseError) as exc:
            raise SystemExit(f"cannot parse EPUB XHTML {member}: {exc}") from exc
        changed = False
        frontispiece_document = "Villa Carlotta" in text_content(root)
        frontispiece_assigned = False
        for image in root.findall(".//{*}img"):
            basename = ref_basename(image.get("src"))
            if basename == FRONTISPIECE_BASENAME or (
                frontispiece_document and not frontispiece_assigned
            ):
                image.set("alt", FRONTISPIECE_ALTERNATIVE)
                frontispiece_assigned = True
                changed = True
            if cover_basename and basename == cover_basename:
                image.set("alt", COVER_ALTERNATIVE)
                changed = True
        if cover_basename:
            for svg in root.findall(".//{*}svg"):
                if not any(
                    ref_basename(svg_image_ref(image)) == cover_basename
                    for image in svg.findall(".//{*}image")
                ):
                    continue
                set_svg_accessible_name(svg, COVER_ALTERNATIVE)
                changed = True
        if member == nav_member and bodymatter_member:
            changed = ensure_bodymatter_landmark(root, nav_member, bodymatter_member) or changed
        if changed:
            rewritten[member] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return rewritten


def accessibility_metadata(opf_root: ET.Element) -> dict[str, list[str]]:
    metadata = opf_root.find("{*}metadata")
    if metadata is None:
        raise SystemExit("EPUB package metadata is missing")
    actual: dict[str, list[str]] = {}
    for element in metadata.findall("{*}meta"):
        property_name = element.get("property")
        if property_name:
            actual.setdefault(property_name, []).append((element.text or "").strip())
    return actual


def update_package_metadata(opf_root: ET.Element) -> bytes:
    metadata = opf_root.find("{*}metadata")
    if metadata is None:
        raise SystemExit("EPUB package metadata is missing")
    opf_root.set(f"{{{XML_NS}}}lang", LANGUAGE)
    languages = metadata.findall(f"{{{DC_NS}}}language")
    if languages:
        languages[0].text = LANGUAGE
        for extra in languages[1:]:
            metadata.remove(extra)
    else:
        ET.SubElement(metadata, f"{{{DC_NS}}}language").text = LANGUAGE
    for element in list(metadata):
        if element.tag.endswith("}meta") and element.get("property") in ACCESSIBILITY_PROPERTIES:
            metadata.remove(element)
    for property_name, value in ACCESSIBILITY_METADATA:
        element = ET.SubElement(metadata, f"{{{OPF_NS}}}meta", {"property": property_name})
        element.text = value
    for element in metadata.findall("{*}meta"):
        if (
            element.get("property") == "dcterms:conformsTo"
            and (element.text or "").strip().startswith("EPUB Accessibility")
        ):
            raise SystemExit("EPUB declares accessibility conformance before the audit is complete")
    ET.register_namespace("", OPF_NS)
    ET.register_namespace("dc", DC_NS)
    return ET.tostring(opf_root, encoding="utf-8", xml_declaration=True)


def build_stamp(data: bytes) -> tuple[bytes, bool]:
    info = current_build()
    label = html.escape(info.label)
    url = html.escape(info.commit_url, quote=True)
    paragraph = (
        '<p class="build-info">Digital edition build: '
        f'<a href="{url}"><code>{label}</code></a></p>'
    ).encode()
    data = BUILD_STAMP_RE.sub(b"", data)
    if b"Albert M. W. Yau" not in data:
        return data, False
    marker = b"</section>" if b"</section>" in data else b"</body>"
    position = data.rfind(marker)
    if position < 0:
        raise SystemExit("could not locate EPUB editor front matter for build stamp")
    return data[:position] + paragraph + b"\n" + data[position:], True


def verify_integrity(epub: Path, expected_names: tuple[str, ...] | None = None) -> None:
    if not epub.is_file() or epub.stat().st_size == 0:
        raise SystemExit(f"EPUB output is missing or empty: {epub}")
    try:
        with zipfile.ZipFile(epub) as archive:
            names = archive.namelist()
            if not names or names[0] != "mimetype":
                raise SystemExit("EPUB mimetype entry is not first")
            if archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
                raise SystemExit("EPUB mimetype entry is compressed")
            if archive.read("mimetype") != b"application/epub+zip":
                raise SystemExit("invalid EPUB mimetype")
            if archive.testzip() is not None:
                raise SystemExit("EPUB contains a corrupt member")
            if expected_names is not None and tuple(names) != expected_names:
                raise SystemExit("EPUB finalization did not preserve package members")
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"EPUB is not a valid ZIP archive: {exc}") from exc


def rewrite_epub(epub: Path, replacements: dict[str, bytes]) -> None:
    """Rewrite an EPUB atomically while preserving every package member."""
    with zipfile.ZipFile(epub, "r") as source:
        infos = source.infolist()
        if not infos or infos[0].filename != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        original_names = tuple(info.filename for info in infos)
        entries = [
            (info, replacements.get(info.filename, source.read(info.filename)))
            for info in infos
        ]

    with tempfile.NamedTemporaryFile(
        prefix="wave-motions-", suffix=".epub", dir=epub.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w") as target:
            for info, data in entries:
                compression = zipfile.ZIP_STORED if info.filename == "mimetype" else info.compress_type
                target.writestr(info, data, compress_type=compression)
        os.replace(temporary, epub)
    finally:
        temporary.unlink(missing_ok=True)
    verify_integrity(epub, original_names)


def finalize(epub: Path) -> None:
    verify_integrity(epub)
    with zipfile.ZipFile(epub, "r") as source:
        opf_name, opf_root = package_document(source)
        replacements = set_known_accessibility(source, opf_name, opf_root)
        replacements[opf_name] = update_package_metadata(opf_root)
        stamped = False
        for member in manifest_xhtml_members(opf_name, opf_root):
            data = replacements.get(member, source.read(member))
            data = BUILD_STAMP_RE.sub(b"", data)
            if stamped:
                found = False
            else:
                data, found = build_stamp(data)
            replacements[member] = data
            stamped = stamped or found
        if not stamped:
            raise SystemExit("could not locate EPUB editor front matter for build stamp")
    rewrite_epub(epub, replacements)
    validate_finalized(epub)
    print(f"EPUB finalization OK: {epub.relative_to(ROOT)}")


def alternative_bucket(value: str | None) -> str:
    if value is None:
        return "missing"
    value = value.strip()
    if not value:
        return "empty"
    if value.casefold() in GENERIC_ALT_TEXT:
        return "generic"
    return "meaningful"


def image_alternative_inventory(
    archive: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> tuple[int, int, int, int, int, set[str]]:
    total = meaningful = generic = empty = missing = 0
    alternatives: set[str] = set()
    for member in manifest_xhtml_members(opf_name, opf_root):
        try:
            root = ET.fromstring(archive.read(member))
        except (KeyError, ET.ParseError) as exc:
            raise SystemExit(f"cannot parse EPUB XHTML {member}: {exc}") from exc
        for image in root.findall(".//{*}img"):
            total += 1
            value = image.get("alt")
            bucket = alternative_bucket(value)
            if bucket == "meaningful":
                meaningful += 1
                alternatives.add((value or "").strip())
            elif bucket == "generic":
                generic += 1
            elif bucket == "empty":
                empty += 1
            else:
                missing += 1
        for svg in root.findall(".//{*}svg"):
            if not svg.findall(".//{*}image"):
                continue
            total += 1
            value = svg.get("aria-label")
            if not value:
                title = svg.find(f"{{{SVG_NS}}}title")
                value = " ".join("".join(title.itertext()).split()) if title is not None else None
            bucket = alternative_bucket(value)
            if bucket == "meaningful":
                meaningful += 1
                alternatives.add((value or "").strip())
            elif bucket == "generic":
                generic += 1
            elif bucket == "empty":
                empty += 1
            else:
                missing += 1
    return total, meaningful, generic, empty, missing, alternatives


def validate_document_languages(archive: zipfile.ZipFile, opf_name: str, opf_root: ET.Element) -> None:
    for member in manifest_xhtml_members(opf_name, opf_root):
        root = ET.fromstring(archive.read(member))
        xml_lang = root.get(f"{{{XML_NS}}}lang")
        html_lang = root.get("lang")
        if xml_lang != LANGUAGE or (html_lang is not None and html_lang != LANGUAGE):
            raise SystemExit(f"EPUB XHTML {member} does not declare {LANGUAGE}")


def validate_bodymatter_landmark(archive: zipfile.ZipFile, opf_name: str, opf_root: ET.Element) -> None:
    nav_member = navigation_member(opf_name, opf_root)
    expected = first_bodymatter_member(archive, opf_name, opf_root)
    assert nav_member is not None and expected is not None
    root = ET.fromstring(archive.read(nav_member))
    landmarks = [
        nav
        for nav in root.findall(".//{*}nav")
        if "landmarks" in (nav.get(EPUB_TYPE) or "").split()
    ]
    if len(landmarks) != 1:
        raise SystemExit(f"expected one EPUB landmarks navigation element, found {len(landmarks)}")
    links = [
        link
        for link in landmarks[0].findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    if len(links) != 1:
        raise SystemExit(f"expected one EPUB bodymatter landmark, found {len(links)}")
    target = urllib.parse.unquote(urllib.parse.urlsplit(links[0].get("href") or "").path)
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(nav_member), target))
    if resolved != expected:
        raise SystemExit(f"EPUB bodymatter landmark resolves to {resolved!r}; expected {expected!r}")


def validate_finalized(epub: Path) -> None:
    verify_integrity(epub)
    with zipfile.ZipFile(epub, "r") as archive:
        opf_name, opf_root = package_document(archive)
        metadata = opf_root.find("{*}metadata")
        if metadata is None or opf_root.get(f"{{{XML_NS}}}lang") != LANGUAGE:
            raise SystemExit("EPUB package language is missing")
        languages = [(element.text or "").strip() for element in metadata.findall(f"{{{DC_NS}}}language")]
        if languages != [LANGUAGE]:
            raise SystemExit(f"EPUB publication language is incomplete: {languages!r}")
        validate_document_languages(archive, opf_name, opf_root)
        validate_bodymatter_landmark(archive, opf_name, opf_root)

        actual = accessibility_metadata(opf_root)
        expected: dict[str, list[str]] = {}
        for property_name, value in ACCESSIBILITY_METADATA:
            expected.setdefault(property_name, []).append(value)
        for property_name, values in expected.items():
            if actual.get(property_name) != values:
                raise SystemExit(f"EPUB accessibility metadata {property_name!r} is {actual.get(property_name)!r}; expected {values!r}")
        false_claims = {"alternativeText", "longDescription", "taggedPDF"}
        features = set(actual.get("schema:accessibilityFeature", []))
        if features & false_claims:
            raise SystemExit("EPUB claims accessibility features that are not fully audited")
        for element in metadata.findall("{*}meta"):
            if element.get("property") == "dcterms:conformsTo" and (element.text or "").strip().startswith("EPUB Accessibility"):
                raise SystemExit("EPUB must not claim accessibility conformance before the audit is complete")

        total, meaningful, generic, empty, missing, alternatives = image_alternative_inventory(archive, opf_name, opf_root)
        if total == 0:
            raise SystemExit("EPUB contains no images to audit for alternative text")
        for required in (FRONTISPIECE_ALTERNATIVE, COVER_ALTERNATIVE):
            if required not in alternatives:
                raise SystemExit("EPUB lost a known accessible image description: " + required)

        cover_basename = cover_image_basename(opf_root)
        assert cover_basename is not None
        cover_svg_seen = False
        cover_title_found = False
        for member in manifest_xhtml_members(opf_name, opf_root):
            root = ET.fromstring(archive.read(member))
            for svg in root.findall(".//{*}svg"):
                if not any(ref_basename(svg_image_ref(image)) == cover_basename for image in svg.findall(".//{*}image")):
                    continue
                cover_svg_seen = True
                title = svg.find(f"{{{SVG_NS}}}title")
                if svg.get("aria-label") == COVER_ALTERNATIVE and title is not None and " ".join(title.itertext()).strip() == COVER_ALTERNATIVE:
                    cover_title_found = True
        if cover_svg_seen and not cover_title_found:
            raise SystemExit("EPUB cover SVG is missing its native accessible title")

        info = current_build()
        label = html.escape(info.label).encode()
        url = html.escape(info.commit_url, quote=True).encode()
        xhtml = b"\n".join(archive.read(member) for member in manifest_xhtml_members(opf_name, opf_root))
        if xhtml.count(b'class="build-info"') != 1 or label not in xhtml or url not in xhtml:
            raise SystemExit("EPUB exact build identity is missing or duplicated")
    print("EPUB accessibility/finalization policy OK")
    print(f"EPUB image-alternative baseline: total={total}, meaningful={meaningful}, generic={generic}, empty={empty}, missing={missing}")
    if generic or missing:
        print("Accessibility audit remains open: scientific figure alternatives are incomplete")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify the reflowable EPUB edition")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the completed EPUB without rebuilding or rewriting it",
    )
    args = parser.parse_args()
    if args.check:
        validate_finalized(EPUB)
        return 0

    for command in ("pandoc", "pdflatex", "pdftoppm"):
        if shutil.which(command) is None:
            raise SystemExit(f"missing required command: {command}")
    if not CSS.is_file():
        raise SystemExit(f"missing EPUB stylesheet: {CSS}")
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    prepare_assets(BUILD, BUILD)
    inputs = epub_inputs()
    render_cover()
    metadata = write_metadata()
    build_epub(inputs, metadata)
    validate_epub()
    finalize(EPUB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
