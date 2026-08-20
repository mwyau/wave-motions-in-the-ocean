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

        opf_bytes = ET.tostring(
            opf_root,
            encoding="utf-8",
            xml_declaration=True,
        )
        entries = [
            (
                info,
                opf_bytes if info.filename == opf_name else source.read(info.filename),
            )
            for info in infos
        ]

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


def image_alternative_inventory(
    archive: zipfile.ZipFile,
    opf_name: str,
    opf_root: ET.Element,
) -> tuple[int, int, int, int, int]:
    manifest = opf_root.find("{*}manifest")
    if manifest is None:
        raise SystemExit("EPUB manifest is missing")
    package_dir = posixpath.dirname(opf_name)
    total = meaningful = generic = empty = missing = 0
    for item in manifest.findall("{*}item"):
        if item.get("media-type") != "application/xhtml+xml" or not item.get("href"):
            continue
        href = urllib.parse.unquote(item.get("href") or "")
        member = posixpath.normpath(posixpath.join(package_dir, href))
        try:
            root = ET.fromstring(archive.read(member))
        except (KeyError, ET.ParseError) as exc:
            raise SystemExit(f"cannot parse EPUB XHTML {member}: {exc}") from exc
        for image in root.findall(".//{*}img"):
            total += 1
            alt = image.get("alt")
            if alt is None:
                missing += 1
            elif not alt.strip():
                empty += 1
            elif alt.strip().casefold() in GENERIC_ALT_TEXT:
                generic += 1
            else:
                meaningful += 1
    return total, meaningful, generic, empty, missing


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
        actual: dict[str, list[str]] = {}
        for element in metadata.findall("{*}meta"):
            property_name = element.get("property")
            if property_name:
                actual.setdefault(property_name, []).append(
                    (element.text or "").strip()
                )

        expected: dict[str, list[str]] = {}
        for property_name, value in ACCESSIBILITY_METADATA:
            expected.setdefault(property_name, []).append(value)
        for property_name, values in expected.items():
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

        total, meaningful, generic, empty, missing = image_alternative_inventory(
            archive, opf_name, opf_root
        )
        if total == 0:
            raise SystemExit("EPUB contains no images to audit for alternative text")

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
    if not args.check:
        apply_metadata(epub)
    validate_metadata(epub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
