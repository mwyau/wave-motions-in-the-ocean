#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BUILD="$ROOT/build"
DIST="$ROOT/dist"
CACHE=${WAVE_CACHE_DIR:-"$ROOT/.cache/wave-motions"}
LATEX_CACHE="$CACHE/latex"
MODE=${1:-all}

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }
}

pdf_pages() {
  pdfinfo "$1" | awk '/^Pages:/ {print $2}'
}

check_pdf_integrity() {
  need pdfinfo
  for pdf in "$DIST/wave-motions-facsimile.pdf" "$DIST/wave-motions.pdf"; do
    test -s "$pdf"
    if command -v qpdf >/dev/null 2>&1; then
      qpdf --check "$pdf" >/dev/null
    else
      pdfinfo "$pdf" >/dev/null
    fi
  done

  local fac_pages mod_pages
  fac_pages=$(pdf_pages "$DIST/wave-motions-facsimile.pdf")
  mod_pages=$(pdf_pages "$DIST/wave-motions.pdf")
  if [[ "$fac_pages" != "184" ]]; then
    if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
      echo "::warning title=Facsimile pagination::Facsimile page count is $fac_pages; expected 184. Pagination remains a final publication requirement."
    else
      echo "warning: facsimile page count is $fac_pages; expected 184; pagination remains a final publication requirement" >&2
    fi
  fi
  test "$mod_pages" -gt 0
  printf 'PDF integrity OK: facsimile=%s pages, modern=%s pages\n' "$fac_pages" "$mod_pages"
}

check_pdf_destinations() {
  test -s "$LATEX_CACHE/facsimile/main-facsimile.log"
  test -s "$LATEX_CACHE/modern/main-modern.log"
  ! grep -q "destination with the same identifier" "$LATEX_CACHE/facsimile/main-facsimile.log"
  ! grep -q "destination with the same identifier" "$LATEX_CACHE/modern/main-modern.log"
  echo "PDF destination checks OK"
}

check_pdf_text() {
  need pdftotext
  mkdir -p "$BUILD/facsimile" "$BUILD/modern"
  pdftotext -layout "$DIST/wave-motions-facsimile.pdf" "$BUILD/facsimile/text.txt"
  pdftotext -layout "$DIST/wave-motions.pdf" "$BUILD/modern/text.txt"
  for txt in "$BUILD/facsimile/text.txt" "$BUILD/modern/text.txt"; do
    grep -Fq "When I volunteered to teach the MIT/WHOI" "$txt"
    grep -Fq "These notes have been collected and assembled" "$txt"
  done
  echo "PDF text sentinel checks OK"
}

check_pdf_render() {
  need pdfinfo
  need pdftoppm
  local kind pages pdf middle
  for spec in \
    "facsimile:$(pdf_pages "$DIST/wave-motions-facsimile.pdf"):$DIST/wave-motions-facsimile.pdf" \
    "modern:$(pdf_pages "$DIST/wave-motions.pdf"):$DIST/wave-motions.pdf"; do
    IFS=: read -r kind pages pdf <<< "$spec"
    middle=$((pages / 2))
    rm -rf "$BUILD/$kind/render-check"
    mkdir -p "$BUILD/$kind/render-check"
    for p in 1 "$middle" "$pages"; do
      pdftoppm -f "$p" -l "$p" -singlefile -r 100 -png \
        "$pdf" "$BUILD/$kind/render-check/page-$p" >/dev/null 2>&1
    done
    test "$(find "$BUILD/$kind/render-check" -name 'page-*.png' | wc -l | tr -d ' ')" = "3"
  done
  echo "PDF render smoke checks OK"
}

check_publish_root() {
  test -s "$DIST/index.html"
  test -s "$DIST/wave-motions.pdf"
  test -s "$DIST/wave-motions-facsimile.pdf"
  test -s "$DIST/wave-motions.epub"
  test -s "$DIST/SHA256SUMS"
  grep -q 'wave-motions.pdf' "$DIST/index.html"
  grep -q 'wave-motions-facsimile.pdf' "$DIST/index.html"
  grep -q 'wave-motions.epub' "$DIST/index.html"
  test ! -e "$DIST/html"
  echo "Publish root and download checks OK"
}

check_build_identity() {
  need python3
  need pdfinfo
  need pdftotext
  local short label
  short=$(python3 "$ROOT/scripts/build_info.py" --short)
  label=$(python3 "$ROOT/scripts/build_info.py" --label)
  test "$short" != "unknown"

  grep -Fq "GitHub Source" "$DIST/index.html"
  grep -Fq "$short" "$DIST/index.html"

  mkdir -p "$BUILD/modern"
  pdftotext -layout "$DIST/wave-motions.pdf" "$BUILD/modern/build-identity.txt"
  grep -Fq "$short" "$BUILD/modern/build-identity.txt"

  pdfinfo "$DIST/wave-motions-facsimile.pdf" | grep -Fq "$short"

  python3 - "$DIST/wave-motions.epub" "$short" <<'PY'
import sys
import zipfile
from pathlib import Path

epub = Path(sys.argv[1])
short = sys.argv[2].encode()
with zipfile.ZipFile(epub) as archive:
    payload = b"\n".join(
        archive.read(name)
        for name in archive.namelist()
        if name.lower().endswith((".xhtml", ".html", ".opf"))
    )
if short not in payload:
    raise SystemExit("EPUB build identity is missing")
PY

  printf 'Build identity OK: %s\n' "$label"
}

check_checksums() {
  need python3
  python3 "$ROOT/scripts/checksums.py" --root "$DIST" --check
}

check_release_gate() {
  need python3
  need pdfinfo

  local tag version short label fac_pages
  tag=${WAVE_BUILD_VERSION:-${GITHUB_REF_NAME:-}}
  if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "release tag must be a stable semantic version such as v1.0.0; got: ${tag:-<empty>}" >&2
    exit 1
  fi

  version=$(python3 "$ROOT/scripts/build_info.py" --version)
  short=$(python3 "$ROOT/scripts/build_info.py" --short)
  label=$(python3 "$ROOT/scripts/build_info.py" --label)
  test "$version" = "$tag"
  test "$short" != "unknown"
  test "$label" = "$tag ($short)"
  [[ "$label" != *"+dirty"* ]]

  fac_pages=$(pdf_pages "$DIST/wave-motions-facsimile.pdf")
  if [[ "$fac_pages" != "184" ]]; then
    echo "release blocked: facsimile page count is $fac_pages; expected exactly 184" >&2
    exit 1
  fi

  check_checksums
  printf 'Release gate OK: %s, facsimile=%s pages\n' "$label" "$fac_pages"
}

case "$MODE" in
  pdf-integrity) check_pdf_integrity ;;
  pdf-destinations) check_pdf_destinations ;;
  pdf-text) check_pdf_text ;;
  pdf-render) check_pdf_render ;;
  publish-root) check_publish_root ;;
  build-identity) check_build_identity ;;
  checksums) check_checksums ;;
  release-gate) check_release_gate ;;
  pdf)
    check_pdf_integrity
    check_pdf_destinations
    check_pdf_text
    check_pdf_render
    ;;
  all)
    check_pdf_integrity
    check_pdf_destinations
    check_pdf_text
    check_pdf_render
    check_publish_root
    check_build_identity
    check_checksums
    ;;
  *)
    echo "usage: $0 [pdf-integrity|pdf-destinations|pdf-text|pdf-render|publish-root|build-identity|checksums|release-gate|pdf|all]" >&2
    exit 2
    ;;
esac
