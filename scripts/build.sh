#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RECON="$ROOT/reconstruction"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
CACHE=${WAVE_CACHE_DIR:-"$ROOT/.cache/wave-motions"}
LATEX_CACHE="$CACHE/latex"
TARGET=${1:-all}
SKIP_VALIDATION=${WAVE_SKIP_VALIDATION:-0}

case "$TARGET" in
  pdf|html|epub|all) ;;
  *) echo "usage: $0 [pdf|html|epub|all]" >&2; exit 2 ;;
esac

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }
}
need python3

prepare_bibtex() {
  # Some minimal TeX installations expose bibtex8 but not a `bibtex` executable.
  # latexmk expects `bibtex`, so provide a temporary compatibility command only
  # for PDF builds that can actually invoke the bibliography tool.
  if command -v bibtex >/dev/null 2>&1; then
    return
  fi
  if command -v bibtex8 >/dev/null 2>&1; then
    local toolbin="$BUILD/toolbin"
    mkdir -p "$toolbin"
    ln -sf "$(command -v bibtex8)" "$toolbin/bibtex"
    export PATH="$toolbin:$PATH"
    return
  fi
  echo "missing required BibTeX executable (bibtex or bibtex8)" >&2
  exit 1
}

prepare_build_info() {
  python3 "$ROOT/scripts/build_info.py" --tex "$BUILD/build-info.tex"
}

run_latexmk_cached() {
  local main=$1 kind=$2
  local out="$LATEX_CACHE/$kind"
  local base=${main%.tex}
  local had_state=false
  [[ -f "$out/$base.fdb_latexmk" ]] && had_state=true
  mkdir -p "$out"

  if (cd "$RECON" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out" "$main"); then
    return
  fi

  if [[ "$had_state" == true ]]; then
    echo "cached latexmk state for $kind failed; retrying clean" >&2
    rm -rf "$out"
    mkdir -p "$out"
    (cd "$RECON" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out" "$main")
    return
  fi

  return 1
}

build_pdf() {
  for cmd in latexmk pdflatex pdfinfo; do need "$cmd"; done
  prepare_bibtex

  rm -rf "$BUILD/facsimile" "$BUILD/modern"
  mkdir -p "$BUILD/facsimile" "$BUILD/modern" "$LATEX_CACHE/facsimile" "$LATEX_CACHE/modern" "$DIST"
  rm -f "$DIST/wave-motions.pdf" "$DIST/wave-motions-facsimile.pdf" \
    "$DIST/wave-motions-1989-modern.pdf" "$DIST/wave-motions-1989-facsimile.pdf"

  prepare_build_info
  run_latexmk_cached main-facsimile.tex facsimile
  run_latexmk_cached main-modern.tex modern

  cp "$LATEX_CACHE/facsimile/main-facsimile.pdf" "$DIST/wave-motions-facsimile.pdf"
  cp "$LATEX_CACHE/modern/main-modern.pdf" "$DIST/wave-motions.pdf"

  local fac_pages mod_pages
  fac_pages=$(pdfinfo "$DIST/wave-motions-facsimile.pdf" | awk '/^Pages:/ {print $2}')
  mod_pages=$(pdfinfo "$DIST/wave-motions.pdf" | awk '/^Pages:/ {print $2}')
  printf 'PDF build complete: facsimile=%s pages, modern=%s pages\n' "$fac_pages" "$mod_pages"

  if [[ "$SKIP_VALIDATION" != "1" ]]; then
    bash "$ROOT/scripts/validate-publication.sh" pdf
  fi
}

prepare_html() {
  for cmd in pandoc pdftocairo; do need "$cmd"; done
  python3 "$ROOT/scripts/build-html.py"
}

build_epub() {
  need pandoc
  python3 "$ROOT/scripts/build-epub.py"
  python3 "$ROOT/scripts/set-epub-accessibility.py"
}

finish_html() {
  python3 "$ROOT/scripts/sync-views.py" --html
  python3 "$ROOT/scripts/enhance-html.py"
}

check_readme_sync() {
  python3 "$ROOT/scripts/sync-views.py" --check-readme
}

stamp_html() {
  python3 "$ROOT/scripts/stamp-build-info.py" --html
}

stamp_epub() {
  python3 "$ROOT/scripts/stamp-build-info.py" --epub
}

check_epub_accessibility() {
  python3 "$ROOT/scripts/set-epub-accessibility.py" --check
}

write_checksums() {
  python3 "$ROOT/scripts/checksums.py" --root "$DIST" --write
}

clean_html_outputs() {
  rm -rf "$DIST/assets"
  rm -f "$DIST/index.html" "$DIST/references.html" "$DIST"/chapter*.html
}

reset_generated() {
  rm -rf "$BUILD" "$DIST"
  mkdir -p "$BUILD" "$DIST"
}

case "$TARGET" in
  all)
    reset_generated
    build_pdf
    prepare_html
    build_epub
    finish_html
    stamp_html
    stamp_epub
    write_checksums
    if [[ "$SKIP_VALIDATION" != "1" ]]; then
      check_readme_sync
      check_epub_accessibility
      bash "$ROOT/scripts/validate-publication.sh" publish-root
      bash "$ROOT/scripts/validate-publication.sh" build-identity
      bash "$ROOT/scripts/validate-publication.sh" checksums
    fi
    ;;
  pdf)
    reset_generated
    build_pdf
    ;;
  html)
    reset_generated
    prepare_html
    finish_html
    stamp_html
    if [[ "$SKIP_VALIDATION" != "1" ]]; then
      check_readme_sync
    fi
    ;;
  epub)
    reset_generated
    prepare_html
    build_epub
    stamp_epub
    if [[ "$SKIP_VALIDATION" != "1" ]]; then
      check_epub_accessibility
    fi
    clean_html_outputs
    ;;
esac
