#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python}
BUILD="$ROOT/build"
PUBLICATION="$ROOT/release"
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
  # latexmk requires a `bibtex` executable; minimal TinyTeX installs may
  # expose only bibtex8, so provide the expected command name for this build.
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
  "$PYTHON" "$ROOT/scripts/publication.py" build-info --tex "$BUILD/build-info.tex"

  # CITATION.cff is the single maintained DOI source.
  local doi
  doi=$(awk '
    /^[[:space:]]*doi:[[:space:]]*/ {
      count++
      value=$0
      sub(/^[[:space:]]*doi:[[:space:]]*/, "", value)
      gsub(/"/, "", value)
    }
    END {
      if (count != 1) exit 2
      print value
    }
  ' "$ROOT/CITATION.cff") || {
    echo "expected exactly one doi field in CITATION.cff" >&2
    exit 1
  }
  printf '\\providecommand{\\wavedoi}{%s}\n' "$doi" >> "$BUILD/build-info.tex"
}

run_latexmk_cached() {
  local main=$1 kind=$2
  local out="$LATEX_CACHE/$kind"
  local base=${main%.tex}
  local had_state=false
  [[ -f "$out/$base.fdb_latexmk" ]] && had_state=true
  mkdir -p "$out"

  if (cd "$ROOT/src" && latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir="$out" "$main"); then
    return
  fi

  if [[ "$had_state" == true ]]; then
    echo "cached latexmk state for $kind failed; retrying clean" >&2
    rm -rf "$out"
    mkdir -p "$out"
    (cd "$ROOT/src" && latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir="$out" "$main")
    return
  fi
  return 1
}

build_pdf() {
  for command in latexmk lualatex pdfinfo; do need "$command"; done
  prepare_bibtex
  rm -rf "$BUILD/facsimile" "$BUILD/modern"
  mkdir -p "$BUILD/facsimile" "$BUILD/modern" "$LATEX_CACHE/facsimile" "$LATEX_CACHE/modern" "$PUBLICATION"

  prepare_build_info
  # Both paged editions use the shared LuaLaTeX/STIX Two stack.
  run_latexmk_cached main-facsimile.tex facsimile
  run_latexmk_cached main-modern.tex modern
  cp "$LATEX_CACHE/facsimile/main-facsimile.pdf" "$PUBLICATION/wave-motions-facsimile.pdf"
  cp "$LATEX_CACHE/modern/main-modern.pdf" "$PUBLICATION/wave-motions.pdf"

  local fac_pages mod_pages
  fac_pages=$(pdfinfo "$PUBLICATION/wave-motions-facsimile.pdf" | awk '/^Pages:/ {print $2}')
  mod_pages=$(pdfinfo "$PUBLICATION/wave-motions.pdf" | awk '/^Pages:/ {print $2}')
  # Pagination drift is advisory during ordinary/build-only development runs;
  # validate.py owns publication policy and keeps stable releases strict.
  if [[ "$fac_pages" != 184 ]] && ! validation_enabled; then
    echo "warning: facsimile page count is $fac_pages; expected 184" >&2
  fi
  printf 'PDF build complete: facsimile=%s pages, modern=%s pages\n' "$fac_pages" "$mod_pages"
}

build_html() {
  "$PYTHON" "$ROOT/scripts/build_html.py"
}

build_epub() {
  "$PYTHON" "$ROOT/scripts/build_epub.py"
}

check_readme() {
  "$PYTHON" "$ROOT/scripts/sync_readme.py" --check
}

check_equations() {
  "$PYTHON" "$ROOT/scripts/publication.py" equations --check
}

finalize_publication() {
  "$PYTHON" "$ROOT/scripts/release.py" finalize --root "$PUBLICATION"
}

reset_generated() {
  rm -rf "$BUILD" "$PUBLICATION"
  mkdir -p "$BUILD" "$PUBLICATION"
}

finish_all() {
  finalize_publication
  if validation_enabled; then
    "$PYTHON" "$ROOT/scripts/validate.py" all
  else
    echo "Dedicated validation skipped (WAVE_SKIP_VALIDATION=1; builders retained structural checks)."
  fi
}

case "$TARGET" in
  all)
    check_equations
    reset_generated
    build_pdf
    build_epub
    build_html
    finish_all
    ;;
  pdf)
    check_equations
    build_pdf
    if validation_enabled; then
      "$PYTHON" "$ROOT/scripts/validate.py" pdf
    fi
    ;;
  html)
    check_equations
    build_html
    if validation_enabled; then
      "$PYTHON" "$ROOT/scripts/validate.py" html
      check_readme
    fi
    ;;
  epub)
    check_equations
    build_epub
    if validation_enabled; then
      "$PYTHON" "$ROOT/scripts/validate.py" epub
    fi
    ;;
esac
