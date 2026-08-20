# Repository instructions

This file is the technical guide for working on the repository. Keep the public-facing `README.md` focused on the book's front matter and editor's note.

## Core invariants

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- The facsimile PDF, modern PDF, and HTML edition share the same `chapter1.tex`--`chapter6.tex`, figures, corrections, and `references.bib`.
- Correct shared content once. Record every substantive deviation from the scan in `reconstruction/ERRATA.md`.
- Facsimile and modern editions differ only where explicitly intended: front matter, typography, spacing, navigation, and pagination/page-break behavior.
- Generated PDFs, HTML, comparison images, LaTeX auxiliaries, and other build products are not committed.
- Do not add source hashes, source manifests, verification TSVs, or generated build-status ledgers.

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
    build.sh
    build-html.py
    compare-figures.py
```

Do not recreate compatibility entry points, duplicate chapter trees, figure registries, replacement manifests, or a separate maintained HTML prose tree.

The canonical PDF entry points are:

- `reconstruction/main-facsimile.tex`
- `reconstruction/main-modern.tex`

The HTML edition is generated from the same modern front matter, chapters, bibliography, TikZ sources, committed raster figures, and source-PDF crops.

## Editions

The repository produces three reader-facing editions from one canonical body:

- **Facsimile PDF:** reconstructed LaTeX with source-compatible page boundaries and typography tuned toward the 1989 notes. The accepted facsimile pagination is 184 pages.
- **Modern PDF:** the same body with modern typography, continuous pagination, generated table of contents, editor material, and more generous spacing. Its page count is not fixed.
- **Modern HTML:** chapter-split HTML generated from the same LaTeX for GitHub Pages. EPUB remains future work.

The modern front matter may include `reconstruction/figures/frontmatter/salmon-hendershott-como-1980.jpeg`. Do not recompress that historical photograph merely for the build.

## Local build requirements

The reproducible CI route uses TinyTeX plus the packages listed in `tex-packages.txt`.

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
```

A local full build also requires:

- `latexmk`, `pdflatex`, and BibTeX
- Pandoc
- Poppler tools: `pdfinfo`, `pdftoppm`, `pdftotext`, `pdftocairo`
- Python 3 with Pillow
- Ghostscript for additional PDF validation where available
- `qpdf` for structural PDF checks where available; CI installs it

On Debian/Ubuntu, install the system utilities with the distribution package manager. Do not work around a genuinely missing `.sty` file with `latexmk -f`; install the missing TeX package instead.

## Build interface

Use the single build interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh all
```

Build products belong under `dist/` only:

```text
dist/
├── wave-motions-1989-facsimile.pdf
├── wave-motions-1989-modern.pdf
└── html/
    ├── index.html
    ├── chapter1.html
    ├── ...
    ├── chapter6.html
    ├── references.html
    ├── wave-motions-1989-facsimile.pdf
    └── wave-motions-1989-modern.pdf
```

Temporary LaTeX, TikZ, source-crop, and comparison products belong under `build/` and remain ignored.

## HTML generation

`scripts/build-html.py` is a generated-view pipeline, not a second source tree.

It must:

- derive the Pages front page from `reconstruction/frontmatter-modern.tex`;
- generate one HTML page per canonical chapter plus references;
- render committed TikZ sources to SVG only as temporary/generated web assets;
- generate source-PDF crops only in build output;
- copy intentionally retained raster assets recursively while preserving subdirectories;
- include the historical front-matter photograph when present;
- place both built PDFs in the HTML root;
- put visible links to both PDFs on `index.html`;
- validate all local `src`/`href` references before success.

When using `re.sub`, use a callable replacement for generated LaTeX strings that contain backslashes. A plain replacement string such as `\includegraphics...` can be misinterpreted by Python's regular-expression replacement parser.

## GitHub Pages

`.github/workflows/pages.yml` is the only deployment workflow.

On pushes to `main` it must:

1. install the declared TeX/system dependencies;
2. run `./scripts/build.sh all`;
3. verify that `dist/html/index.html` exists;
4. verify that both PDFs are present in `dist/html/` and linked from `index.html`;
5. upload **`dist/html` itself** as the Pages artifact so its generated `index.html` is the site root;
6. deploy with GitHub Pages Actions.

The intended public URLs are:

```text
https://mwyau.github.io/wave-motions-in-the-ocean/
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions-1989-facsimile.pdf
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions-1989-modern.pdf
```

Do not deploy the repository root or render `README.md` as the Pages homepage.

## Figure policy

- Use direct crops from the committed source PDF for untouched complex/historical art; do not commit an intermediate PNG.
- Use TikZ/vector source for simple analytic diagrams when scientific meaning can be preserved exactly.
- If a source figure genuinely requires deskewing, cleaning, manual repair, contrast correction, or another intentional raster edit, commit only the final edited raster. Extract at the PDF's native embedded resolution where possible; avoid screenshots and repeated lossy recompression.
- Each retained TikZ file carries a `wave-source` provenance comment used by `scripts/compare-figures.py` to regenerate comparisons on demand.
- Each intentionally edited raster carries equivalent `wave-source-*` PNG metadata so comparisons can be regenerated without keeping a duplicate source raster.
- Record figure status and decisions in `reconstruction/FIGURE_AUDIT.md`.

To regenerate temporary source/reconstruction comparisons:

```bash
python scripts/compare-figures.py <figure-name>
python scripts/compare-figures.py --all
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
./scripts/build.sh all
```

For figure work, also run `python scripts/compare-figures.py <figure>` for affected figures.

Check at minimum:

- facsimile remains 184 pages unless an explicitly reviewed change requires otherwise;
- PDFs parse/render successfully;
- no unresolved LaTeX references remain;
- HTML index, six chapter pages, references, assets, and both downloadable PDFs exist;
- HTML local links are valid;
- Pages artifact root is `dist/html`;
- `PLAN.md`, `ERRATA.md`, and `FIGURE_AUDIT.md` are updated when the work changes their scope.
