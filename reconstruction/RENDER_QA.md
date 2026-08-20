# Render QA

Use the publication build for correctness checks, then run a separate visual QA pass on the exact generated artifact:

```bash
./scripts/build.sh all
python3 scripts/render-qa.py dist
```

The QA tool also accepts a downloaded publication artifact ZIP:

```bash
python3 scripts/render-qa.py path/to/artifact.zip
```

Output is written under `build/render-qa/` and is intentionally untracked. The report includes artifact/build identity, PDF page counts and full-book contact sheets, static HTML checks plus optional Chrome/Chromium desktop/mobile screenshots, an unpacked EPUB and EPUB metadata/MathML summary, optional EPUBCheck output, and the manual EPUB reader acceptance matrix.

Useful options:

```bash
python3 scripts/render-qa.py dist --pdf-dpi 90
python3 scripts/render-qa.py dist --no-browser
python3 scripts/render-qa.py dist --browser /path/to/chromium
EPUBCHECK_JAR=/path/to/epubcheck.jar python3 scripts/render-qa.py dist
```

`--strict` makes structural QA errors return nonzero, but visual warnings remain review items rather than CI gates. The script is a developer/release-review aid, not a substitute for the existing publication validators.

## PDF review

Review every generated contact sheet, then inspect suspicious pages at full size. For the modern edition, always inspect the cover and preliminary pages, every chapter opener, figure-dense pages, equation-heavy pages, and references. For the facsimile, exact source-page structure is part of correctness: a stable release must contain exactly **184 physical pages**.

## HTML review

The automated pass checks local references, viewport/theme/mobile CSS, book/chapter orientation, external MathJax dependence, and—when Chrome or Chromium is available—captures representative desktop and phone screenshots. A real-browser pass should still exercise both navigation bars, Auto/Light/Dark cycling, narrow viewports, wide equations/tables, and figure scaling.

The HTML reader currently loads MathJax from jsDelivr. A packaged HTML ZIP is therefore network-dependent for mathematical typesetting unless MathJax is later vendored; render QA reports this explicitly.

## EPUB review

The automated pass validates ZIP/package basics, metadata, spine/XHTML presence, MathML presence, media references, and runs EPUBCheck when `epubcheck` is installed or `EPUBCHECK_JAR` is set. It also unpacks the EPUB for DOM/CSS diagnosis.

Browser inspection of unpacked XHTML is **not** EPUB acceptance. Before release, inspect the actual EPUB in at least two independent EPUB3 reading systems—preferably Thorium/Readium and Calibre ebook-viewer—and record reader versions. Check cover/front matter, TOC navigation, representative inline and display math, chapter-based equation numbers, long-equation reflow at narrow widths and large font sizes, figures/captions/tables/links, selection/search around math, and reader themes where supported.
