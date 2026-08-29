#!/usr/bin/env python3
"""Build a structurally usable EPUB3 from the main flowing sources.

This builder prepares its own generated TeX and figures, then applies the
single final EPUB ZIP rewrite for metadata, accessibility, bodymatter,
language, and build identity before returning a completed artifact.
"""

from __future__ import annotations

import html
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image

from publication import (
    AUTHORS,
    EDITOR,
    LANGUAGE,
    PUBLICATION_TITLE,
    PUBLICATION_YEAR,
    SITE_URL,
    current_build,
    prepare_assets,
    prepare_flowing_sources,
    prepare_publication_images,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release"
BUILD = ROOT / "build" / "epub"
SRC = ROOT / "src"
CSS = SRC / "layout" / "wave-epub.css"
AMS_CSL = SRC / "layout" / "wave-ams.csl"
EPUB = OUT / "wave-motions.epub"
COVER_DIR = BUILD / "cover"
COVER_PDF = COVER_DIR / "cover.pdf"
COVER_PNG = COVER_DIR / "cover.png"
COVER_IMAGE = COVER_DIR / "cover.jpg"

OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
EPUB_TYPE = f"{{{EPUB_NS}}}type"
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
FRONTISPIECE_BASENAME = "salmon-hendershott-como-1980.jpg"
FRONTISPIECE_ALTERNATIVE = (
    "Rick Salmon (left) and Myrl Hendershott at Villa Carlotta, Lake Como, "
    "during the International School of Physics Enrico Fermi, Course LXXX, "
    "Topics in Ocean Physics, July 1980."
)
COVER_ALTERNATIVE = (
    f"Front cover of {PUBLICATION_TITLE}, featuring Katsushika "
    "Hokusai's Under the Wave off Kanagawa (The Great Wave)."
)
BUILD_STAMP_RE = re.compile(rb'<p class="build-info">.*?</p>\s*', re.DOTALL)


def run(
    cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def normalize_epub_math_tex(text: str) -> str:
    """Apply MathML compatibility changes to generated EPUB TeX."""
    return re.sub(r"\\ell(?![A-Za-z])", "{ℓ}", text)


def bibliography_entry_count() -> int:
    return len(re.findall(r"(?m)^@\w+\s*\{", (SRC / "references.bib").read_text()))


def epub_inputs() -> list[Path]:
    source_dir = BUILD / "source"
    paths = prepare_flowing_sources(source_dir, BUILD, include_epub_only=True)
    frontmatter = paths[0]
    credit_source = SRC / "cover-credit.tex"
    if not credit_source.is_file():
        raise SystemExit(f"missing cover credit source: {credit_source}")
    front_text = frontmatter.read_text()
    marker = r"\wavecovercredit"
    if marker not in front_text:
        raise SystemExit("EPUB front matter is missing the cover-credit marker")
    frontmatter.write_text(
        front_text.replace(marker, credit_source.read_text().strip(), 1)
    )

    for path in paths:
        path.write_text(normalize_epub_math_tex(path.read_text()))

    return paths


def render_cover() -> None:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    wrapper = COVER_DIR / "cover.tex"
    wrapper.write_text(
        r"""\documentclass[11pt,oneside]{report}
\usepackage{layout/wave-modern}
\begin{document}
\providecommand{\WavePublicationImagePath}[1]{../../publication-images/#1}
\input{cover-modern}
\WaveModernCover
\clearpage
\nopagecolor
\end{document}
"""
    )
    env = os.environ.copy()
    texinputs = str(SRC) + "//:"
    if env.get("TEXINPUTS"):
        texinputs += env["TEXINPUTS"]
    env["TEXINPUTS"] = texinputs
    run(
        [
            "lualatex",
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
    # Keep the existing 7 x 10 in, 200-dpi device-scale raster, but use a
    # high-quality JPEG so the cover does not dominate the reflowable EPUB.
    with Image.open(COVER_PNG) as image:
        image.convert("RGB").save(
            COVER_IMAGE,
            format="JPEG",
            quality=92,
            subsampling=0,
            optimize=True,
            progressive=False,
        )
    if not COVER_IMAGE.is_file() or COVER_IMAGE.stat().st_size == 0:
        raise SystemExit("EPUB cover JPEG conversion failed")


def write_metadata() -> Path:
    path = BUILD / "metadata.yaml"
    path.write_text(
        "---\n"
        f'title: "{PUBLICATION_TITLE}"\n'
        "author:\n"
        + "".join(f"  - {author}\n" for author in AUTHORS)
        + f'date: "{PUBLICATION_YEAR}"\n'
        f"lang: {LANGUAGE}\n"
        'rights: "CC BY-NC-SA 4.0"\n'
        f'identifier: "{SITE_URL}/"\n'
        f'contributor: "{EDITOR}"\n'
        "nocite: '@*'\n"
        'reference-section-title: "References"\n'
        "---\n"
    )
    return path


def build_epub(inputs: list[Path], metadata: Path) -> None:
    EPUB.parent.mkdir(parents=True, exist_ok=True)
    EPUB.unlink(missing_ok=True)
    resource_path = os.pathsep.join(
        (str(BUILD), str(BUILD / "source"), str(OUT), str(SRC))
    )
    run(
        [
            "pandoc",
            *(str(path) for path in inputs),
            "-f",
            "latex+smart",
            "-t",
            "epub3",
            "--toc",
            "--toc-depth=2",
            "--split-level=1",
            "--mathml",
            "--citeproc",
            "--csl",
            str(AMS_CSL),
            f"--bibliography={SRC / 'references.bib'}",
            "--metadata-file",
            str(metadata),
            "--metadata",
            f"title={PUBLICATION_TITLE}",
            "--css",
            str(CSS),
            "--epub-cover-image",
            str(COVER_IMAGE),
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
    ref_re = re.compile(rb'(?:href|src)=["\']([^"\']+)["\']', re.IGNORECASE)
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


def validate_structure(epub: Path = EPUB, *, require_legacy_cover: bool = True) -> None:
    """Keep the generated package usable before and after the final rewrite."""
    verify_integrity(epub)
    with zipfile.ZipFile(epub) as archive:
        names = set(archive.namelist())
        if "META-INF/container.xml" not in names:
            raise SystemExit("EPUB container.xml is missing")

        opf_name, opf_root = package_document(archive)
        if opf_name not in names:
            raise SystemExit(f"EPUB package document is missing: {opf_name}")
        metadata = opf_root.find("{*}metadata")
        manifest = opf_root.find("{*}manifest")
        spine = opf_root.find("{*}spine")
        if metadata is None or manifest is None or spine is None:
            raise SystemExit("EPUB package metadata/manifest/spine is incomplete")

        manifest_items = list(manifest.findall("{*}item"))
        by_id = {item.get("id"): item for item in manifest_items if item.get("id")}
        spine_ids = [item.get("idref") for item in spine.findall("{*}itemref")]
        if not spine_ids or any(item_id not in by_id for item_id in spine_ids):
            raise SystemExit("EPUB spine is empty or references missing manifest items")

        package_dir = posixpath.dirname(opf_name)
        for item in manifest_items:
            href = item.get("href")
            if href and manifest_member(opf_name, item) not in names:
                raise SystemExit(
                    f"EPUB manifest member is missing: "
                    f"{posixpath.normpath(posixpath.join(package_dir, urllib.parse.unquote(href)))}"
                )

        xhtml_names = manifest_xhtml_members(opf_name, opf_root)
        if not xhtml_names:
            raise SystemExit("EPUB XHTML manifest is empty")
        validate_internal_refs(archive, xhtml_names)

        reference_entries = 0
        for name in xhtml_names:
            root = ET.fromstring(archive.read(name))
            reference_entries += sum(
                1
                for element in root.iter()
                if "csl-entry" in (element.get("class") or "").split()
            )
        expected_references = bibliography_entry_count()
        if reference_entries != expected_references:
            raise SystemExit(
                "EPUB bibliography is incomplete: "
                f"found {reference_entries} entries; expected {expected_references}"
            )

        if require_legacy_cover:
            cover_item = cover_image_item(opf_root)
            assert cover_item is not None
            cover_id = cover_item.get("id")
            legacy_cover = [
                element
                for element in metadata.findall("{*}meta")
                if element.get("name") == "cover"
            ]
            if (
                len(legacy_cover) != 1
                or not cover_id
                or legacy_cover[0].get("content") != cover_id
            ):
                raise SystemExit(
                    "EPUB legacy cover metadata does not identify the EPUB3 cover image"
                )


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
        item.get("id"): item for item in manifest.findall("{*}item") if item.get("id")
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


def cover_image_item(
    opf_root: ET.Element, *, required: bool = True
) -> ET.Element | None:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    items = [
        item
        for item in manifest.findall("{*}item")
        if "cover-image" in (item.get("properties") or "").split()
    ]
    if len(items) != 1 or not items[0].get("href") or not items[0].get("id"):
        if required:
            raise SystemExit(f"expected one EPUB cover image, found {len(items)}")
        return None
    return items[0]


def cover_image_basename(opf_root: ET.Element, *, required: bool = True) -> str | None:
    item = cover_image_item(opf_root, required=required)
    if item is None:
        return None
    href = urllib.parse.unquote(item.get("href") or "")
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


def ensure_bodymatter_landmark(
    root: ET.Element, nav_member: str, bodymatter_member: str
) -> bool:
    landmarks = [
        nav
        for nav in root.findall(".//{*}nav")
        if "landmarks" in (nav.get(EPUB_TYPE) or "").split()
    ]
    if len(landmarks) != 1:
        raise SystemExit(
            f"expected one EPUB landmarks navigation element, found {len(landmarks)}"
        )
    landmark = landmarks[0]
    existing = [
        link
        for link in landmark.findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    expected_href = posixpath.relpath(
        bodymatter_member, posixpath.dirname(nav_member) or "."
    )
    if existing:
        if len(existing) != 1:
            raise SystemExit("EPUB landmarks contain multiple bodymatter entries")
        target = urllib.parse.unquote(
            urllib.parse.urlsplit(existing[0].get("href") or "").path
        )
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(nav_member), target)
        )
        if resolved != bodymatter_member:
            raise SystemExit(
                "EPUB bodymatter landmark points to the wrong content document"
            )
        return False
    ordered_list = landmark.find("./{*}ol")
    if ordered_list is None:
        raise SystemExit("EPUB landmarks navigation has no ordered list")
    item = ET.SubElement(ordered_list, f"{{{XHTML_NS}}}li")
    link = ET.SubElement(
        item, f"{{{XHTML_NS}}}a", {"href": expected_href, EPUB_TYPE: "bodymatter"}
    )
    link.text = "Start reading"
    return True


def set_known_accessibility(
    source: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> dict[str, bytes]:
    cover_basename = cover_image_basename(opf_root, required=False)
    nav_member = navigation_member(opf_name, opf_root, required=False)
    bodymatter_member = first_bodymatter_member(
        source, opf_name, opf_root, required=False
    )
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
            changed = (
                ensure_bodymatter_landmark(root, nav_member, bodymatter_member)
                or changed
            )
        if changed:
            rewritten[member] = ET.tostring(
                root, encoding="utf-8", xml_declaration=True
            )
    return rewritten


def _set_contributor_refinements(metadata: ET.Element) -> None:
    creators = metadata.findall(f"{{{DC_NS}}}creator")
    creators_by_name = {text_content(element): element for element in creators}
    missing_authors = [author for author in AUTHORS if author not in creators_by_name]
    if missing_authors:
        raise SystemExit(
            f"EPUB package metadata is missing authors: {missing_authors!r}"
        )

    contributor = next(
        (
            element
            for element in metadata.findall(f"{{{DC_NS}}}contributor")
            if text_content(element) == EDITOR
        ),
        None,
    )
    if contributor is None:
        raise SystemExit("EPUB package metadata is missing the editor")

    refined_elements = [*(creators_by_name[author] for author in AUTHORS), contributor]
    old_ids = {element.get("id") for element in refined_elements if element.get("id")}
    for meta in list(metadata.findall("{*}meta")):
        refines = (meta.get("refines") or "").removeprefix("#")
        if refines in old_ids and meta.get("property") in {"role", "display-seq"}:
            metadata.remove(meta)

    for sequence, author in enumerate(AUTHORS, start=1):
        creator = creators_by_name[author]
        creator_id = f"author-{sequence}"
        creator.set("id", creator_id)
        role = ET.SubElement(
            metadata,
            f"{{{OPF_NS}}}meta",
            {
                "refines": f"#{creator_id}",
                "property": "role",
                "scheme": "marc:relators",
            },
        )
        role.text = "aut"
        display_sequence = ET.SubElement(
            metadata,
            f"{{{OPF_NS}}}meta",
            {"refines": f"#{creator_id}", "property": "display-seq"},
        )
        display_sequence.text = str(sequence)

    contributor.set("id", "editor")
    editor_role = ET.SubElement(
        metadata,
        f"{{{OPF_NS}}}meta",
        {
            "refines": "#editor",
            "property": "role",
            "scheme": "marc:relators",
        },
    )
    editor_role.text = "edt"


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
    _set_contributor_refinements(metadata)

    cover_item = cover_image_item(opf_root)
    assert cover_item is not None
    cover_id = cover_item.get("id")
    assert cover_id is not None
    for element in list(metadata.findall("{*}meta")):
        if element.get("name") == "cover":
            metadata.remove(element)
    ET.SubElement(
        metadata,
        f"{{{OPF_NS}}}meta",
        {"name": "cover", "content": cover_id},
    )

    for element in list(metadata):
        if (
            element.tag.endswith("}meta")
            and element.get("property") in ACCESSIBILITY_PROPERTIES
        ):
            metadata.remove(element)
    for property_name, value in ACCESSIBILITY_METADATA:
        element = ET.SubElement(
            metadata, f"{{{OPF_NS}}}meta", {"property": property_name}
        )
        element.text = value
    for element in metadata.findall("{*}meta"):
        if element.get("property") == "dcterms:conformsTo" and (
            element.text or ""
        ).strip().startswith("EPUB Accessibility"):
            raise SystemExit(
                "EPUB declares accessibility conformance before the audit is complete"
            )
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
                compression = (
                    zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else info.compress_type
                )
                target.writestr(info, data, compress_type=compression)
        os.replace(temporary, epub)
    finally:
        temporary.unlink(missing_ok=True)
    verify_integrity(epub, original_names)


def finalize(epub: Path) -> None:
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
            raise SystemExit(
                "could not locate EPUB editor front matter for build stamp"
            )
    rewrite_epub(epub, replacements)
    validate_structure(epub)
    print(f"EPUB finalization OK: {epub.relative_to(ROOT)}")


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit(
            "build_epub.py does not accept options; use validate.py epub to validate"
        )
    for command in ("pandoc", "lualatex", "pdftoppm"):
        if shutil.which(command) is None:
            raise SystemExit(f"missing required command: {command}")
    if not CSS.is_file():
        raise SystemExit(f"missing EPUB stylesheet: {CSS}")
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    prepare_publication_images()
    prepare_assets(BUILD, BUILD)
    inputs = epub_inputs()
    render_cover()
    metadata = write_metadata()
    build_epub(inputs, metadata)
    validate_structure(require_legacy_cover=False)
    finalize(EPUB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
