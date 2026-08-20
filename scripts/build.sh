#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RECON="$ROOT/reconstruction"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
CACHE=${WAVE_CACHE_DIR:-"$ROOT/.cache/wave-motions"}
LATEX_CACHE="$CACHE/latex"
TARGET=${1:-all}

case "$TARGET" in
  pdf|html|epub|all) ;;
  *) echo "usage: $0 [pdf|html|epub|all]" >&2; exit 2 ;;
esac

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }
}
for cmd in latexmk pdflatex pdfinfo pdftotext pdftoppm python3; do need "$cmd"; done

# Some minimal TeX installations expose bibtex8 but not a `bibtex` executable.
# latexmk expects `bibtex`, so provide a temporary compatibility command.
TOOLBIN="$BUILD/toolbin"
mkdir -p "$TOOLBIN"
if command -v bibtex >/dev/null 2>&1; then
  :
elif command -v bibtex8 >/dev/null 2>&1; then
  ln -sf "$(command -v bibtex8)" "$TOOLBIN/bibtex"
  export PATH="$TOOLBIN:$PATH"
else
  echo "missing required BibTeX executable (bibtex or bibtex8)" >&2
  exit 1
fi

validate_pdf() {
  local pdf=$1
  test -s "$pdf"
  if command -v qpdf >/dev/null 2>&1; then
    qpdf --check "$pdf" >/dev/null
  else
    pdfinfo "$pdf" >/dev/null
  fi
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

rebuild_facsimile_clean() {
  echo "facsimile pagination mismatch; retrying from a clean latexmk cache" >&2
  rm -rf "$LATEX_CACHE/facsimile"
  mkdir -p "$LATEX_CACHE/facsimile"
  run_latexmk_cached main-facsimile.tex facsimile
  cp "$LATEX_CACHE/facsimile/main-facsimile.pdf" "$DIST/wave-motions-facsimile.pdf"
  validate_pdf "$DIST/wave-motions-facsimile.pdf"
}

build_pdf() {
  rm -rf "$BUILD/facsimile" "$BUILD/modern"
  mkdir -p "$BUILD/facsimile" "$BUILD/modern" "$LATEX_CACHE/facsimile" "$LATEX_CACHE/modern" "$DIST"
  rm -f "$DIST/wave-motions.pdf" "$DIST/wave-motions-facsimile.pdf" \
    "$DIST/wave-motions-1989-modern.pdf" "$DIST/wave-motions-1989-facsimile.pdf"

  run_latexmk_cached main-facsimile.tex facsimile
  run_latexmk_cached main-modern.tex modern

  cp "$LATEX_CACHE/facsimile/main-facsimile.pdf" "$DIST/wave-motions-facsimile.pdf"
  cp "$LATEX_CACHE/modern/main-modern.pdf" "$DIST/wave-motions.pdf"

  validate_pdf "$DIST/wave-motions-facsimile.pdf"
  validate_pdf "$DIST/wave-motions.pdf"

  local fac_pages mod_pages
  fac_pages=$(pdfinfo "$DIST/wave-motions-facsimile.pdf" | awk '/^Pages:/ {print $2}')
  if [[ "$fac_pages" != "184" ]]; then
    rebuild_facsimile_clean
    fac_pages=$(pdfinfo "$DIST/wave-motions-facsimile.pdf" | awk '/^Pages:/ {print $2}')
  fi
  mod_pages=$(pdfinfo "$DIST/wave-motions.pdf" | awk '/^Pages:/ {print $2}')
  test "$fac_pages" = "184" || { echo "facsimile page count is $fac_pages; expected 184 after clean rebuild" >&2; exit 1; }
  test "$mod_pages" -gt 0

  ! grep -q "destination with the same identifier" "$LATEX_CACHE/facsimile/main-facsimile.log"
  ! grep -q "destination with the same identifier" "$LATEX_CACHE/modern/main-modern.log"

  pdftotext -layout "$DIST/wave-motions-facsimile.pdf" "$BUILD/facsimile/text.txt"
  pdftotext -layout "$DIST/wave-motions.pdf" "$BUILD/modern/text.txt"
  for txt in "$BUILD/facsimile/text.txt" "$BUILD/modern/text.txt"; do
    grep -Fq "When I volunteered to teach the MIT/WHOI" "$txt"
    grep -Fq "These notes have been collected and assembled" "$txt"
  done

  for spec in "facsimile:$fac_pages:$DIST/wave-motions-facsimile.pdf" "modern:$mod_pages:$DIST/wave-motions.pdf"; do
    IFS=: read -r kind pages pdf <<< "$spec"
    local middle=$((pages / 2))
    mkdir -p "$BUILD/$kind/render-check"
    for p in 1 "$middle" "$pages"; do
      pdftoppm -f "$p" -l "$p" -singlefile -r 100 -png \
        "$pdf" "$BUILD/$kind/render-check/page-$p" >/dev/null 2>&1
    done
    test "$(find "$BUILD/$kind/render-check" -name 'page-*.png' | wc -l | tr -d ' ')" = "3"
  done

  printf 'PDF build OK: facsimile=%s pages, modern=%s pages\n' "$fac_pages" "$mod_pages"
}

prepare_html() {
  for cmd in pandoc pdftocairo; do need "$cmd"; done
  python3 "$ROOT/scripts/build-html.py"
}

build_epub() {
  need pandoc
  python3 "$ROOT/scripts/build-epub.py"
}

finish_html() {
  python3 "$ROOT/scripts/sync-views.py" --html
  python3 "$ROOT/scripts/enhance-html.py"
  python3 "$ROOT/scripts/sync-views.py" --check-readme
}

reset_generated() {
  rm -rf "$BUILD" "$DIST"
  mkdir -p "$BUILD" "$DIST"
  TOOLBIN="$BUILD/toolbin"
  mkdir -p "$TOOLBIN"
  if ! command -v bibtex >/dev/null 2>&1 && command -v bibtex8 >/dev/null 2>&1; then
    ln -sf "$(command -v bibtex8)" "$TOOLBIN/bibtex"
    export PATH="$TOOLBIN:$PATH"
  fi
}

case "$TARGET" in
  all)
    reset_generated
    build_pdf
    prepare_html
    build_epub
    finish_html
    ;;
  pdf)
    build_pdf
    ;;
  html)
    prepare_html
    finish_html
    ;;
  epub)
    prepare_html
    build_epub
    ;;
esac
