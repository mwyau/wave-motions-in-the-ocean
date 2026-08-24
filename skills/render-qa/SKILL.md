# Render QA skill

Use this skill for post-build visual and structural review of generated PDF, HTML, and EPUB artifacts. Publication construction and release rules remain in `skills/publication/SKILL.md`; source-content discrepancies remain governed by `skills/source-audit/SKILL.md`.

## Run the QA pass

Build first, then inspect the exact generated artifact:

```bash
./scripts/build.sh all
python3 scripts/render_qa.py dist
```

A downloaded publication artifact ZIP may be inspected instead:

```bash
python3 scripts/render_qa.py path/to/artifact.zip
```

Output goes under `audit/render-qa/` and is intentionally ignored. The report includes artifact/build identity, PDF page counts and contact sheets, static HTML checks plus optional Chrome/Chromium desktop/mobile screenshots and browser regressions, an unpacked EPUB and metadata/MathML summary, optional EPUBCheck output, and the manual EPUB reader acceptance matrix. This audit material survives publication builds; `build/` remains disposable build intermediates.

Useful options:

```bash
python3 scripts/render_qa.py dist --pdf-dpi 90
python3 scripts/render_qa.py dist --no-browser
python3 scripts/render_qa.py dist --browser /path/to/chromium
EPUBCHECK_JAR=/path/to/epubcheck.jar python3 scripts/render_qa.py dist
```

`--strict` makes structural QA errors return nonzero. Visual warnings remain review items rather than CI gates. Render QA supplements, rather than replaces, the publication validators.

A QA finding does not authorize changing source or scientific content. Route any apparent source or content error through `skills/source-audit/SKILL.md`.

## PDF review

Review every generated contact sheet, then inspect suspicious pages at full size.

For the modern edition, always inspect:

- cover and preliminary pages;
- every chapter opener;
- figure-dense pages;
- equation-heavy pages;
- references.

For the facsimile, source-page structure is part of correctness. A stable release must contain exactly **184 physical pages**.

## HTML review

The automated pass checks local references, viewport/theme/mobile CSS, book/chapter orientation, local runtime assets, and—when Chrome or Chromium is available—captures representative desktop/mobile screenshots and exercises direct-fragment reader-context behavior.

The finished HTML reader is expected to be self-contained at runtime. MathJax JavaScript/fonts and the Source Serif/Source Sans web fonts must resolve from local `assets/`; required third-party network dependencies are a defect.

A real-browser pass should exercise:

- top and bottom navigation;
- Auto/Light/Dark cycling;
- direct section permalinks, including correct current-section context and active Contents state immediately after load;
- scrolling between sections and active-section/context updates;
- browser back/forward and fragment navigation;
- the wide-layout Contents rail and narrow-layout Contents popover/fallback;
- the hidden `?dev=1` MathJax/MathML comparison mode on representative inline and display math;
- narrow viewports, wide equations/tables, and figure scaling.

The direct-fragment check belongs at the browser-integration layer rather than in a separate DOM unit-test framework: the regression depends on fragment navigation, executed page JavaScript, and browser layout/timing. Do not add jsdom/Playwright solely for this reader check unless the project later adopts a broader browser-test suite.

## EPUB review

The automated pass checks ZIP/package structure, metadata, spine/XHTML presence, MathML, media references, and runs EPUBCheck when `epubcheck` is installed or `EPUBCHECK_JAR` is set. It also unpacks the EPUB for DOM/CSS diagnosis.

Browser inspection of unpacked XHTML is **not** EPUB acceptance. Before release, inspect the actual EPUB in at least two independent EPUB3 reading systems, preferably Thorium/Readium and Calibre ebook-viewer, and record reader versions.

Check:

- cover and front matter;
- TOC navigation;
- representative inline and display math;
- chapter-based equation numbers;
- long-equation reflow at narrow widths and large font sizes;
- figures, captions, tables, and links;
- selection/search around math;
- reader themes where supported.

## Completion

Treat structural failures as defects to resolve before release. Review visual warnings manually and fix only confirmed presentation or generation defects. Do not alter source content merely to make a render check pass.
