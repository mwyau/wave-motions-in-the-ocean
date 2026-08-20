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
  grep -q 'wave-motions.pdf' "$DIST/index.html"
  grep -q 'wave-motions-facsimile.pdf' "$DIST/index.html"
  grep -q 'wave-motions.epub' "$DIST/index.html"
  test ! -e "$DIST/html"
  echo "Publish root and download checks OK"
}

case "$MODE" in
  pdf-integrity) check_pdf_integrity ;;
  pdf-destinations) check_pdf_destinations ;;
  pdf-text) check_pdf_text ;;
  pdf-render) check_pdf_render ;;
  publish-root) check_publish_root ;;
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
    ;;
  *)
    echo "usage: $0 [pdf-integrity|pdf-destinations|pdf-text|pdf-render|publish-root|pdf|all]" >&2
    exit 2
    ;;
esac
