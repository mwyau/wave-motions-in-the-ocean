# Repository instructions

This file is the technical guide for working on the repository. Keep `README.md` reader-facing: it is the Markdown publication view of the modern front matter plus shared contents/download/license material, with README-only Shields badges.

## Core invariants

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- The facsimile PDF, modern PDF, HTML edition, and README publication view are derived from the canonical reconstruction sources. Do not maintain duplicate prose or chapter/section metadata by hand.
- `reconstruction/frontmatter-modern.tex` is the canonical modern front matter for the modern PDF, HTML index, and README. `reconstruction/frontmatter-facsimile.tex` remains source-faithful for the facsimile edition.
- `reconstruction/chapter1.tex` through `chapter6.tex` are the canonical chapter bodies and heading structure for all editions.
- Correct shared content once. Record every substantive deviation from the scan in `reconstruction/ERRATA.md`.
- Facsimile and modern editions differ only where explicitly intended: front matter, typography, spacing, navigation, and pagination/page-break behavior.
- Generated PDFs, HTML, comparison images, LaTeX auxiliaries, and other build products are not committed.
- Do not add source hashes, source manifests, verification TSVs, or generated build-status ledgers.

## Published-view synchronization

README and Pages must stay synchronized from canonical LaTeX rather than being sources for one another.

- `scripts/book_views.py` extracts chapter titles and `\section{}` headings from the canonical chapter files and defines the shared Contents, Downloads, and CC-license presentation data.
- `scripts/sync-views.py --readme` regenerates the README front matter, chapter/section Contents, both PDF download links, and CC statement from canonical sources.
- The block between `README_BADGES_START` and `README_BADGES_END` is intentionally README-only and is preserved verbatim by the generator.
- `scripts/sync-views.py --html` installs the same chapter/section Contents, Downloads, and CC statement into generated `dist/index.html` and assigns stable section anchors to chapter HTML pages.
- `scripts/sync-views.py --check-readme` must pass in a successful HTML/full build. If it fails, regenerate the README and review the diff rather than editing duplicated content separately.
- Both README and HTML must list both `wave-motions.pdf` and `wave-motions-facsimile.pdf` under Downloads. The HTML index does not contain the README Shields badges.

When canonical front matter or chapter headings change, run:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

Review the README diff because Pandoc performs the LaTeX-to-GitHub-Markdown rendering of the front matter.

## Repository layout and entry points

The maintained source layout is intentionally small:

```text
source/
    ChapmanRizzoli0_2.pdf
    ChapmanRizzoli3.pdf
    ChapmanRizzoli4.pdf
    ChapmanRizzoli5.pdf
    ChapmanRizzoli6.pdf

reconstruction/
    main-facsimile.tex
    main-modern.tex
    frontmatter-facsimile.tex
    frontmatter-modern.tex
    chapter1.tex ... chapter6.tex
    references.bib
    styles/
    figures/
    ERRATA.md
    FIGURE_AUDIT.md
    PLAN.md

scripts/
    book_views.py
    sync-views.py
    build.sh
    build-html.py
    enhance-html.py
    compare-figures.py
```

Do not recreate compatibility entry points, duplicate chapter trees, figure registries, replacement manifests, or a separately maintained HTML/Markdown prose tree.

The canonical PDF entry points are:

- `reconstruction/main-facsimile.tex`
- `reconstruction/main-modern.tex`

The HTML edition is generated from the same modern front matter, chapters, bibliography, TikZ sources, committed raster figures, and source-PDF crops.

## Editions

The repository produces three reader-facing editions from one canonical body:

- **Facsimile PDF:** reconstructed LaTeX with source-compatible page boundaries and typography tuned toward the 1989 notes. Accepted pagination is 184 pages.
- **Modern PDF:** the same body with modern typography, continuous pagination, generated table of contents, editor material, and more generous spacing. Its page count is not fixed.
- **Modern HTML:** chapter-split HTML generated from the same LaTeX for GitHub Pages. EPUB remains future work.

`README.md` is not a fourth independent edition; it is a synchronized repository-facing Markdown view of the modern front matter and publication navigation.

The modern front matter may include `reconstruction/figures/frontmatter/salmon-hendershott-como-1980.jpeg`. Do not recompress that historical photograph merely for the build.

## Local build requirements

The reproducible CI route uses TinyTeX plus packages listed in `tex-packages.txt`.

With TinyTeX/TeX Live managed by `tlmgr`:

```bash
mapfile -t PACKAGES < <(grep -Ev '^\s*(#|$)' tex-packages.txt)
tlmgr install "${PACKAGES[@]}"
```

The modern edition currently requires, among other packages, `newtx` and Source Sans. If a local build reports a missing font package, verify the TeX installation directly:

```bash
kpsewhich newtxtext.sty
kpsewhich newtxmath.sty
kpsewhich sourcesanspro.sty
kpsewhich titlesec.sty
```

A local full build also requires:

- `latexmk`, `pdflatex`, and BibTeX
- Pandoc
- Poppler tools: `pdfinfo`, `pdftoppm`, `pdftotext`, `pdftocairo`
- Python 3 with Pillow
- Ghostscript where available
- `qpdf` where available; CI installs it

Do not work around a genuinely missing `.sty` with `latexmk -f`; install the missing TeX package.

## Build interface and outputs

Use the single build interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh all
```

`build/` is temporary/intermediate output. `dist/` is the complete publish root:

```text
dist/
├── index.html
├── chapter1.html
├── ...
├── chapter6.html
├── references.html
├── assets/
├── wave-motions.pdf
└── wave-motions-facsimile.pdf
```

Do not restore the old nested `dist/html/` layout or old `wave-motions-1989-*.pdf` public filenames.

## HTML generation

`scripts/build-html.py` is a generated-view pipeline, not a second source tree.

It must:

- derive the Pages front page from `reconstruction/frontmatter-modern.tex`;
- generate one HTML page per canonical chapter plus references;
- render committed TikZ sources to SVG only as generated web assets;
- generate source-PDF crops only in build output;
- copy intentionally retained raster assets recursively while preserving subdirectories;
- include the historical front-matter photograph when present;
- place both built PDFs at the publish root;
- validate local `src`/`href` references before success.

After base HTML generation, `scripts/sync-views.py --html` applies shared Contents/Downloads/license data and stable section anchors; `scripts/enhance-html.py` applies responsive navigation, source links, and light/dark/auto theming.

When using `re.sub`, use a callable replacement for generated LaTeX strings containing backslashes. A plain replacement string such as `\includegraphics...` can be misinterpreted by Python's regular-expression replacement parser.

## GitHub Pages

`.github/workflows/pages.yml` is the only deployment workflow. On pushes to `main` it must build all editions, verify `dist/index.html` and both public PDFs, upload `dist/` as the Pages artifact, and deploy it.

Intended public URLs:

```text
https://mwyau.github.io/wave-motions-in-the-ocean/
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions-facsimile.pdf
```

Do not deploy the repository root or render `README.md` as the Pages homepage.

## Figure policy

- Use direct crops from committed source PDFs for untouched complex/historical art; do not commit an intermediate PNG.
- Use TikZ/vector source for simple analytic diagrams when scientific meaning can be preserved exactly.
- If source art genuinely requires deskewing, cleaning, manual repair, contrast correction, or another intentional raster edit, commit only the final edited raster. Extract at the PDF's native embedded resolution where possible; avoid screenshots and repeated lossy recompression.
- Each retained TikZ file carries a `wave-source` provenance comment used by `scripts/compare-figures.py` to regenerate comparisons on demand.
- Each intentionally edited raster carries equivalent `wave-source-*` PNG metadata so comparisons can be regenerated without keeping a duplicate source raster.
- Record figure status and decisions in `reconstruction/FIGURE_AUDIT.md`.

To regenerate temporary source/reconstruction comparisons:

```bash
python3 scripts/compare-figures.py <figure-name>
python3 scripts/compare-figures.py --all
```

Comparisons belong under `build/comparisons/`; do not commit them.

## Text and scientific audit

Work in small reviewable batches. Distinguish these checks:

1. **Text fidelity:** compare scan ↔ LaTeX for wording, punctuation, capitalization, symbols, subscripts/superscripts, references, footnotes, page order, and figure labels. Do not modernize prose merely because it sounds old.
2. **Equation transcription:** compare every mathematical symbol and sign directly with the scan.
3. **Scientific equation audit:** independently check dimensions, signs, factors (`2`, `pi`, `g`, `f`, `H`, etc.), definitions, coordinate conventions, derivation steps, boundary conditions, limiting cases, and consistency with surrounding prose. Verify standard results against the cited original paper, Hendershott/Myrl material where relevant, and another authoritative physical-oceanography source when practical.
4. **Scientific figure audit:** check axes, units, signs, propagation direction, orientation, node/antinode placement, dispersion relationships, phase arrows, boundary conditions, and agreement with nearby equations/prose.

Do not silently alter a scientifically questionable historical equation or figure. Record the suspected source error, evidence, and review status in `ERRATA.md`. Preserve the historical derivation style and logic rather than rewriting it as a modern textbook.

## Tracking and editorial records

- `reconstruction/ERRATA.md`: actual deviations, corrections, suspected source errors, and review status.
- `reconstruction/FIGURE_AUDIT.md`: figure provenance, vectorization/edit decisions, and scientific figure review.
- `reconstruction/PLAN.md`: audit coverage, current status, and future work.

Do not create a separate `verification.tsv` or duplicate these responsibilities in generated manifests.

## Completion gate

Before considering repository work complete, run:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For figure work, also run `python3 scripts/compare-figures.py <figure>` for affected figures.

Check at minimum:

- facsimile remains 184 pages unless an explicitly reviewed change requires otherwise;
- PDFs parse/render successfully;
- no unresolved LaTeX references remain;
- `dist/index.html`, six chapter pages, references, assets, and both downloadable PDFs exist;
- README sync check passes;
- HTML Contents include canonical chapter names and section links with working anchors;
- README and HTML list the same Contents, Downloads, and CC-license statement, aside from README-only badges and URL relativity;
- Pages artifact root is `dist/`;
- `PLAN.md`, `ERRATA.md`, and `FIGURE_AUDIT.md` are updated when work changes their scope.
