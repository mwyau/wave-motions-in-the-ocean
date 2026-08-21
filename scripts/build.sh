#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
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

is_release_build() {
  [[ "${GITHUB_REF:-}" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]] ||
    [[ "${WAVE_BUILD_VERSION:-}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

validation_enabled() {
  [[ "$SKIP_VALIDATION" != "1" ]] || is_release_build
}

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
  python3 "$ROOT/scripts/publication.py" build-info --tex "$BUILD/build-info.tex"
}

run_latexmk_cached() {
  local main=$1 kind=$2
  local out="$LATEX_CACHE/$kind"
  local base=${main%.tex}
  local had_state=false
  [[ -f "$out/$base.fdb_latexmk" ]] && had_state=true
  mkdir -p "$out"

  if (cd "$ROOT/reconstruction" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out" "$main"); then
    return
  fi

  if [[ "$had_state" == true ]]; then
    echo "cached latexmk state for $kind failed; retrying clean" >&2
    rm -rf "$out"
    mkdir -p "$out"
    (cd "$ROOT/reconstruction" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out" "$main")
    return
  fi
  return 1
}

check_facsimile_layout() {
  local log="$LATEX_CACHE/facsimile/main-facsimile.log"
  [[ -s "$log" ]] || { echo "missing facsimile LaTeX log: $log" >&2; exit 1; }
  if grep -Fq 'Overfull \vbox' "$log"; then
    echo "facsimile layout error: overfull vertical box detected" >&2
    grep -F 'Overfull \vbox' "$log" >&2
    exit 1
  fi
}

build_pdf() {
  for command in latexmk pdflatex pdfinfo; do need "$command"; done
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
  if [[ "$fac_pages" != 184 ]]; then
    echo "facsimile pagination error: got $fac_pages pages; expected exactly 184" >&2
    exit 1
  fi
  check_facsimile_layout
  printf 'PDF build complete: facsimile=%s pages, modern=%s pages\n' "$fac_pages" "$mod_pages"
}

build_html() {
  need python3
  python3 "$ROOT/scripts/build_html.py"
}

build_epub() {
  need python3
  python3 "$ROOT/scripts/build_epub.py"
}

check_readme() {
  python3 "$ROOT/scripts/sync_readme.py" --check
}

write_checksums() {
  python3 "$ROOT/scripts/release.py" checksums --root "$DIST" --write
}

reset_generated() {
  rm -rf "$BUILD" "$DIST"
  mkdir -p "$BUILD" "$DIST"
}

finish_all() {
  write_checksums
  if validation_enabled; then
    check_readme
    python3 "$ROOT/scripts/validate.py" all
  else
    echo "Dedicated validation skipped (WAVE_SKIP_VALIDATION=1; builders retained structural checks)."
  fi
}

case "$TARGET" in
  all)
    reset_generated
    build_pdf
    build_epub
    build_html
    finish_all
    ;;
  pdf)
    reset_generated
    build_pdf
    if validation_enabled; then
      python3 "$ROOT/scripts/validate.py" pdf
    fi
    ;;
  html)
    reset_generated
    build_html
    if validation_enabled; then
      check_readme
    fi
    ;;
  epub)
    reset_generated
    build_epub
    if validation_enabled; then
      python3 "$ROOT/scripts/validate.py" epub
    fi
    ;;
esac
