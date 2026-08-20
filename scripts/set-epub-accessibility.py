#!/usr/bin/env python3
"""Apply and verify conservative accessibility discovery metadata for EPUB."""
from __future__ import annotations

import argparse
import posixpath
import shutil
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / "dist" / "wave-motions.epub"
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
ACCESSIBILITY_PROPERTIES = {
    property_name for property_name, _ in ACCESSIBILITY_METADATA
}
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


def package_document(archive: zipfile.ZipFile) -> tuple[str, ET.Element]:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
    except (KeyError, ET.ParseError) as exc:
        raise SystemExit(f"cannot read EPUB package container: {exc}") from exc
    rootfile = container.find(".//{*}rootfile")
    if rootfile is None or not rootfile.get("full-path"):
        raise SystemExit("EPUB container has no package rootfile")
    name = rootfile.get("full-path")
    assert name is not None
    try:
        return name, ET.fromstring(archive.read(name))
    except (KeyError, ET.ParseError) as exc:
        raise SystemExit(f"cannot read EPUB package document {name}: {exc}") from exc


def manifest_xhtml_members(
    opf_name: str,
    opf_root: ET.Element,
) -> list[str]:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    package_dir = posixpath.dirname(opf_name)
    members: list[str] = []
    for item in manifest.findall("{*}item"):
        if item.get("media-type") != "application/xhtml+xml" or not item.get("href"):
            continue
        href = urllib.parse.unquote(item.get("href") or "")
        members.append(posixpath.normpath(posixpath.join(package_dir, href)))
    return members


def manifest_member(opf_name: str, item: ET.Element) -> str:
    href = urllib.parse.unquote(item.get("href") or "")
    return posixpath.normpath(posixpath.join(posixpath.dirname(opf_name), href))


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
        if (
            item is None
            or item.get("media-type") != "application/xhtml+xml"
            or not item.get("href")
        ):
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


def cover_image_basename(
    opf_root: ET.Element,
    *,
    required: bool = True,
) -> str | None:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    cover_items = [
        item
        for item in manifest.findall("{*}item")
        if "cover-image" in (item.get("properties") or "").split()
    ]
    if len(cover_items) != 1 or not cover_items[0].get("href"):
        if required:
            raise SystemExit(
                f"expected one EPUB cover image, found {len(cover_items)}"
            )
        return None
    href = urllib.parse.unquote(cover_items[0].get("href") or "")
    return posixpath.basename(urllib.parse.urlsplit(href).path)


def ref_basename(ref: str | None) -> str:
    if not ref:
        return ""
    parsed = urllib.parse.urlsplit(ref)
    return posixpath.basename(urllib.parse.unquote(parsed.path))


def svg_image_ref(image: ET.Element) -> str | None:
    return image.get(f"{{{XLINK_NS}}}href") or image.get("href")


def set_svg_accessible_name(svg: ET.Element, text: str) -> None:
    """Give an SVG both ARIA and native SVG accessible-name mechanisms."""
    svg.set("role", "img")
    svg.set("aria-label", text)
    title = svg.find(f"{{{SVG_NS}}}title")
    if title is None:
        title = ET.Element(f"{{{SVG_NS}}}title")
        svg.insert(0, title)
    title.text = text


def ensure_bodymatter_landmark(
    root: ET.Element,
    nav_member: str,
    bodymatter_member: str,
    *,
    required: bool = True,
) -> bool:
    landmarks = [
        nav
        for nav in root.findall(".//{*}nav")
        if "landmarks" in (nav.get(EPUB_TYPE) or "").split()
    ]
    if len(landmarks) != 1:
        if required:
            raise SystemExit(
                f"expected one EPUB landmarks navigation element, found {len(landmarks)}"
            )
        return False
    landmark = landmarks[0]
    existing = [
        link
        for link in landmark.findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    expected_href = posixpath.relpath(
        bodymatter_member,
        posixpath.dirname(nav_member) or ".",
    )
    if existing:
        if len(existing) != 1:
            if required:
                raise SystemExit("EPUB landmarks contain multiple bodymatter entries")
            return False
        target = urllib.parse.unquote(
            urllib.parse.urlsplit(existing[0].get("href") or "").path
        )
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(nav_member), target)
        )
        if resolved != bodymatter_member:
            if required:
                raise SystemExit(
                    "EPUB bodymatter landmark points to the wrong content document"
                )
            return False
        return False

    ordered_list = landmark.find("./{*}ol")
    if ordered_list is None:
        if required:
            raise SystemExit("EPUB landmarks navigation has no ordered list")
        return False
    item = ET.SubElement(ordered_list, f"{{{XHTML_NS}}}li")
    link = ET.SubElement(
        item,
        f"{{{XHTML_NS}}}a",
        {"href": expected_href, EPUB_TYPE: "bodymatter"},
    )
    link.text = "Start reading"
    return True


def set_known_accessibility(
    source: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> dict[str, bytes]:
    """Best-effort additions whose meaning is already authoritative in the book."""
    cover_basename = cover_image_basename(opf_root, required=False)
    nav_member = navigation_member(opf_name, opf_root, required=False)
    bodymatter_member = first_bodymatter_member(
        source,
        opf_name,
        opf_root,
        required=False,
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
        for image in root.findall(".//{*}img"):
            basename = ref_basename(image.get("src"))
            if basename == FRONTISPIECE_BASENAME:
                image.set("alt", FRONTISPIECE_ALTERNATIVE)
                changed = True
            if cover_basename and basename == cover_basename:
                image.set("alt", COVER_ALTERNATIVE)
                changed = True

        # Pandoc commonly wraps the EPUB cover raster in an inline SVG. Name
        # the outer SVG through both ARIA and its native <title>; EPUB reading
        # systems vary in which accessibility mapping they expose.
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
            changed = ensure_bodymatter_landmark(
                root,
                nav_member,
                bodymatter_member,
                required=False,
            ) or changed

        if changed:
            rewritten[member] = ET.tostring(
                root,
                encoding="utf-8",
                xml_declaration=True,
            )

    return rewritten


def apply_metadata(epub: Path) -> None:
    if not epub.is_file() or epub.stat().st_size == 0:
        raise SystemExit(f"EPUB output is missing or empty: {epub}")

    ET.register_namespace("", OPF_NS)
    ET.register_namespace("dc", DC_NS)

    with zipfile.ZipFile(epub, "r") as source:
        infos = source.infolist()
        if not infos or infos[0].filename != "mimetype":
            raise SystemExit("EPUB mimetype entry is not first")
        if source.read("mimetype") != b"application/epub+zip":
            raise SystemExit("invalid EPUB mimetype")
        opf_name, opf_root = package_document(source)
        metadata = opf_root.find("{*}metadata")
        if metadata is None:
            raise SystemExit("EPUB package metadata is missing")

        # The package document contains human-readable metadata of its own, so
        # identify that text's default language independently of dc:language.
        opf_root.set(f"{{{XML_NS}}}lang", LANGUAGE)

        # Replace these fields rather than trusting Pandoc defaults. Older
        # Pandoc versions ignore the accessibility YAML keys, while newer ones
        # can provide defaults that would overstate the current figure support.
        for element in list(metadata):
            if (
                element.tag.endswith("}meta")
                and element.get("property") in ACCESSIBILITY_PROPERTIES
            ):
                metadata.remove(element)

        for property_name, value in ACCESSIBILITY_METADATA:
            element = ET.SubElement(
                metadata,
                f"{{{OPF_NS}}}meta",
                {"property": property_name},
            )
            element.text = value

        for element in metadata.findall("{*}meta"):
            if (
                element.get("property") == "dcterms:conformsTo"
                and (element.text or "").strip().startswith("EPUB Accessibility")
            ):
                raise SystemExit(
                    "EPUB declares accessibility conformance before the publication has been fully audited"
                )

        # Serialize the OPF before registering XHTML as the default namespace.
        opf_bytes = ET.tostring(
            opf_root,
            encoding="utf-8",
            xml_declaration=True,
        )
        rewritten_xhtml = set_known_accessibility(
            source,
            opf_name,
            opf_root,
        )
        entries: list[tuple[zipfile.ZipInfo, bytes]] = []
        for info in infos:
            if info.filename == opf_name:
                data = opf_bytes
            elif info.filename in rewritten_xhtml:
                data = rewritten_xhtml[info.filename]
            else:
                data = source.read(info.filename)
            entries.append((info, data))

    with tempfile.NamedTemporaryFile(
        prefix="wave-motions-a11y-",
        suffix=".epub",
        dir=epub.parent,
        delete=False,
    ) as handle:
        tmp = Path(handle.name)

    try:
        with zipfile.ZipFile(tmp, "w") as target:
            for info, data in entries:
                compress_type = (
                    zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else info.compress_type
                )
                target.writestr(info, data, compress_type=compress_type)
        shutil.move(tmp, epub)
    finally:
        tmp.unlink(missing_ok=True)


def accessibility_metadata(opf_root: ET.Element) -> dict[str, list[str]]:
    metadata = opf_root.find("{*}metadata")
    if metadata is None:
        raise SystemExit("EPUB package metadata is missing")
    actual: dict[str, list[str]] = {}
    for element in metadata.findall("{*}meta"):
        property_name = element.get("property")
        if property_name:
            actual.setdefault(property_name, []).append(
                (element.text or "").strip()
            )
    return actual


def validate_rewrite_integrity(epub: Path) -> None:
    """Fail the generation path only for corrupt output or failed OPF rewriting."""
    if not epub.is_file() or epub.stat().st_size == 0:
        raise SystemExit(f"EPUB output is missing or empty: {epub}")
    try:
        archive = zipfile.ZipFile(epub, "r")
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"EPUB became invalid after accessibility rewrite: {exc}") from exc
    with archive:
        if archive.testzip() is not None:
            raise SystemExit(
                "EPUB became corrupt while adding accessibility metadata"
            )
        if (
            not archive.namelist()
            or archive.namelist()[0] != "mimetype"
            or archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED
            or archive.read("mimetype") != b"application/epub+zip"
        ):
            raise SystemExit(
                "EPUB mimetype entry is invalid after accessibility metadata update"
            )
        _, opf_root = package_document(archive)
        if opf_root.get(f"{{{XML_NS}}}lang") != LANGUAGE:
            raise SystemExit(
                f"EPUB package text language rewrite did not preserve {LANGUAGE}"
            )
        actual = accessibility_metadata(opf_root)
        expected: dict[str, list[str]] = {}
        for property_name, value in ACCESSIBILITY_METADATA:
            expected.setdefault(property_name, []).append(value)
        for property_name, values in expected.items():
            if actual.get(property_name) != values:
                raise SystemExit(
                    f"EPUB accessibility metadata rewrite failed for {property_name!r}: "
                    f"{actual.get(property_name)!r}"
                )
    print("EPUB accessibility rewrite integrity OK")


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

        # Count each inline SVG that embeds a raster as one visual item. This
        # catches Pandoc's cover wrapper, which the old <img>-only inventory
        # silently omitted.
        for svg in root.findall(".//{*}svg"):
            if not svg.findall(".//{*}image"):
                continue
            total += 1
            value = svg.get("aria-label")
            if not value:
                title = svg.find(f"{{{SVG_NS}}}title")
                value = (
                    " ".join("".join(title.itertext()).split())
                    if title is not None
                    else None
                )
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


def validate_document_languages(
    archive: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> None:
    for member in manifest_xhtml_members(opf_name, opf_root):
        root = ET.fromstring(archive.read(member))
        xml_lang = root.get(f"{{{XML_NS}}}lang")
        html_lang = root.get("lang")
        if xml_lang != LANGUAGE:
            raise SystemExit(
                f"EPUB XHTML {member} has xml:lang={xml_lang!r}; expected {LANGUAGE!r}"
            )
        if html_lang is not None and html_lang != LANGUAGE:
            raise SystemExit(
                f"EPUB XHTML {member} has lang={html_lang!r}; expected {LANGUAGE!r}"
            )


def validate_bodymatter_landmark(
    archive: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> None:
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
        raise SystemExit(
            f"expected one EPUB landmarks navigation element, found {len(landmarks)}"
        )
    links = [
        link
        for link in landmarks[0].findall(".//{*}a")
        if "bodymatter" in (link.get(EPUB_TYPE) or "").split()
    ]
    if len(links) != 1:
        raise SystemExit(
            f"expected one EPUB bodymatter landmark, found {len(links)}"
        )
    target = urllib.parse.unquote(
        urllib.parse.urlsplit(links[0].get("href") or "").path
    )
    resolved = posixpath.normpath(
        posixpath.join(posixpath.dirname(nav_member), target)
    )
    if resolved != expected:
        raise SystemExit(
            f"EPUB bodymatter landmark resolves to {resolved!r}; expected {expected!r}"
        )


def validate_metadata(epub: Path) -> None:
    with zipfile.ZipFile(epub, "r") as archive:
        if archive.testzip() is not None:
            raise SystemExit(
                "EPUB became corrupt while adding accessibility metadata"
            )
        if (
            archive.namelist()[0] != "mimetype"
            or archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED
        ):
            raise SystemExit(
                "EPUB mimetype entry is invalid after accessibility metadata update"
            )

        opf_name, opf_root = package_document(archive)
        metadata = opf_root.find("{*}metadata")
        if metadata is None:
            raise SystemExit("EPUB package metadata is missing")
        if opf_root.get(f"{{{XML_NS}}}lang") != LANGUAGE:
            raise SystemExit(
                f"EPUB package text language is not declared as {LANGUAGE}"
            )
        dc_languages = [
            (element.text or "").strip()
            for element in metadata.findall(f"{{{DC_NS}}}language")
        ]
        if LANGUAGE not in dc_languages:
            raise SystemExit(
                f"EPUB publication language is incomplete: {dc_languages!r}"
            )
        validate_document_languages(archive, opf_name, opf_root)
        validate_bodymatter_landmark(archive, opf_name, opf_root)

        actual = accessibility_metadata(opf_root)
        expected_metadata: dict[str, list[str]] = {}
        for property_name, value in ACCESSIBILITY_METADATA:
            expected_metadata.setdefault(property_name, []).append(value)
        for property_name, values in expected_metadata.items():
            if actual.get(property_name) != values:
                raise SystemExit(
                    f"EPUB accessibility metadata {property_name!r} is "
                    f"{actual.get(property_name)!r}; expected {values!r}"
                )

        false_claims = {
            "alternativeText",
            "longDescription",
            "taggedPDF",
        }
        features = set(actual.get("schema:accessibilityFeature", []))
        if features & false_claims:
            raise SystemExit(
                "EPUB accessibility metadata claims features that are not yet fully audited: "
                + ", ".join(sorted(features & false_claims))
            )
        for element in metadata.findall("{*}meta"):
            if (
                element.get("property") == "dcterms:conformsTo"
                and (element.text or "").strip().startswith("EPUB Accessibility")
            ):
                raise SystemExit(
                    "EPUB must not claim accessibility conformance before the audit is complete"
                )

        (
            total,
            meaningful,
            generic,
            empty,
            missing,
            alternatives,
        ) = image_alternative_inventory(archive, opf_name, opf_root)
        if total == 0:
            raise SystemExit("EPUB contains no images to audit for alternative text")
        for required in (FRONTISPIECE_ALTERNATIVE, COVER_ALTERNATIVE):
            if required not in alternatives:
                raise SystemExit(
                    "EPUB lost a known accessible image description: "
                    + required
                )

        # If Pandoc uses an inline SVG cover, validate its native <title> as
        # well as its ARIA name. Other Pandoc versions may emit a normal <img>,
        # whose required alt text is already checked above.
        cover_basename = cover_image_basename(opf_root)
        assert cover_basename is not None
        cover_svg_seen = False
        cover_title_found = False
        for member in manifest_xhtml_members(opf_name, opf_root):
            root = ET.fromstring(archive.read(member))
            for svg in root.findall(".//{*}svg"):
                if not any(
                    ref_basename(svg_image_ref(image)) == cover_basename
                    for image in svg.findall(".//{*}image")
                ):
                    continue
                cover_svg_seen = True
                if svg.get("aria-label") != COVER_ALTERNATIVE:
                    continue
                title = svg.find(f"{{{SVG_NS}}}title")
                if (
                    title is not None
                    and " ".join(title.itertext()).strip() == COVER_ALTERNATIVE
                ):
                    cover_title_found = True
        if cover_svg_seen and not cover_title_found:
            raise SystemExit("EPUB cover SVG is missing its native accessible title")

    print("EPUB accessibility discovery metadata OK")
    print(
        "EPUB image-alternative baseline: "
        f"total={total}, meaningful={meaningful}, generic={generic}, "
        f"empty={empty}, missing={missing}"
    )
    if generic or missing:
        print(
            "Accessibility audit remains open: scientific figure alternatives are incomplete",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("epub", nargs="?", type=Path, default=EPUB)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated EPUB without modifying it",
    )
    args = parser.parse_args()
    epub = args.epub.resolve()
    if args.check:
        validate_metadata(epub)
    else:
        apply_metadata(epub)
        validate_rewrite_integrity(epub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
