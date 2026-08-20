# Repository instructions

This is the technical guide for work on the repository. Keep it focused on durable invariants and review requirements, not transient implementation details.

## Canonical sources and editorial authority

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- `reconstruction/frontmatter-modern.tex` is the canonical modern front matter for the modern PDF, HTML index, and README publication view.
- `reconstruction/frontmatter-facsimile.tex` remains source-faithful for the facsimile edition.
- `reconstruction/chapter1.tex` through `chapter6.tex` are the canonical chapter bodies and heading structure for every edition.
- `reconstruction/references.bib` is the canonical bibliography. Use BibTeX/citations rather than duplicating bibliography entries manually, and verify new or changed metadata against a primary publisher or equivalent authoritative source.
- Correct shared content once. Record every substantive correction or suspected source error in `reconstruction/ERRATA.md`.
- Do not maintain duplicate prose, equations, chapter names, section names, figure registries, or a separate HTML/Markdown source tree.
- The authorized license is CC BY-NC-SA 4.0. Do not weaken or change licensing without explicit instruction.

## Editions

The repository publishes three editions from one canonical body:

- **Facsimile PDF:** source-compatible page boundaries and typography tuned toward the 1989 notes. Accepted pagination is 184 pages.
- **Modern PDF:** the same corrected body with modern typography, continuous pagination, modern front matter, and generated contents.
- **Modern HTML:** chapter-split Pages edition generated from the same LaTeX sources.

`README.md` is not an independent edition. It is a synchronized Markdown publication view of the modern front matter and publication navigation.

Facsimile and modern editions may differ only where intentionally required by presentation: front matter, typography, spacing, navigation, and pagination/page-break behavior. Scientific/textual content and errata remain shared.

## Modern front matter

Preserve the modern title hierarchy unless explicitly asked to redesign it:

1. `WAVE MOTIONS IN THE OCEAN` is the dominant title.
2. `Myrl's View` is a substantial italic subtitle, visibly larger than ordinary front-matter text but subordinate to the main title.
3. `Presented to` **Myrl C. Hendershott** forms a separate dedication block.
4. **David C. Chapman and Paola Malanotte-Rizzoli** form the original-author block; `August 1989` is on its own line in regular weight rather than being emphasized.
5. `Digital edition by` **Albert M. W. Yau** is a smaller, clearly separated credit near the bottom; `August 2026` is on its own line in regular weight.

Keep the original authorship and digital-editor credit visually distinct so the modern editor is not presented as a third author. Modern attribution blocks use the shared `\wavesignature` presentation. The Editor's note keeps the editor signature in the body, but its TOC entry is simply `Editor's note` without the editor's name. Do not normalize the facsimile front matter to the modern style.

The modern PDF title page has no visible page number. After it, front matter uses lower-case Roman numbering beginning at `i`; Chapter 1 resets to Arabic page `1`. The modern PDF contents stop at chapters and sections (`tocdepth=1`).

Keep the CC BY-NC-SA 4.0 statement in the Editor's note. Do not put a CC badge, logo, or raw license URL on the title page; the repository/HTML views may use badges or icons as appropriate.

The historical photograph `reconstruction/figures/frontmatter/salmon-hendershott-como-1980.jpeg` is part of the modern front matter. Keep it unnumbered and preserve the established provenance/caption identifying Rick Salmon and Myrl Hendershott at Villa Carlotta, Lake Como, during the International School of Physics “Enrico Fermi,” Course LXXX, *Topics in Ocean Physics*, July 1980. Do not reintroduce unsupported wording such as “Photograph by George” unless independently established. Do not recompress the photograph merely for the build.

## README, HTML, and contents synchronization

README and Pages are generated views of the canonical LaTeX; neither is the source of the other.

- `scripts/book_views.py` extracts canonical chapter titles and `\section{}` headings and defines shared Contents, Downloads, and license presentation data.
- `scripts/sync-views.py --readme` regenerates the README publication content while preserving the README-only badge block.
- `scripts/sync-views.py --html` applies the same Contents, Downloads, and license data to generated HTML and supplies stable section anchors.
- `scripts/sync-views.py --check-readme` must pass in a successful HTML/full build.
- README and `index.html` must have the same publication content apart from URL relativity, HTML presentation controls, and README-only badges.
- Both README and HTML list **PDF** and **Facsimile PDF** under Downloads.

### Contents depth

Published contents stop at **Chapter → Section**.

- Include `\chapter{}` and `\section{}` headings.
- Exclude `\subsection{}` and deeper levels from README, HTML index, and modern PDF contents.
- Keep the modern PDF TOC depth at `tocdepth=1` for the `report` class.
- Do not impose this modern TOC policy on the source-faithful facsimile unless explicitly requested.

### README badge contract

The README-only badge row is intentionally not copied into `index.html`:

- **Read | Online**
- **Read | PDF**
- **License | CC BY-NC-SA 4.0**
- **Build | status**

Do not add a facsimile badge; the facsimile remains available in the synchronized Downloads section. The Build badge should represent the actual `build` check, not the overall Pages deployment result, because a superseded/cancelled deployment is not a build failure.

## Build and outputs

Use the single build interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh all
```

`build/` is temporary/intermediate output. `dist/` is the complete publish root and contains `index.html`, six chapter pages, `references.html`, assets, `wave-motions.pdf`, and `wave-motions-facsimile.pdf`.

Generated PDFs, HTML, comparison images, LaTeX auxiliaries, and other build products are not committed. Do not restore the old nested `dist/html/` layout or old `wave-motions-1989-*.pdf` public names.

A full local build requires the declared TeX packages plus Pandoc, Python/Pillow, and Poppler tools. Install genuinely missing TeX packages rather than forcing `latexmk` through missing dependencies.

## HTML presentation

The HTML edition must remain a generated view of the canonical sources. Preserve these reader-facing behaviors unless explicitly redesigned:

- responsive/mobile layout;
- Auto / Light / Dark theme selection;
- source navigation back to the GitHub repository;
- stable chapter/section anchors used by README links;
- horizontally scrollable wide equations/tables on small screens;
- theme-aware generated diagrams.

Do not apply dark-mode inversion/filtering to the historical front-matter JPEG. Generated black-on-white scientific figures may be theme-adjusted when needed for legibility.

## GitHub Pages and CI

`.github/workflows/pages.yml` is the production deployment workflow. It must build all editions, verify the publish root and both PDFs, upload `dist/`, and deploy Pages.

Keep Pages deployment concurrency configured so an in-progress production deployment is not cancelled by a newer push (`cancel-in-progress: false`). A newer run may supersede queued deployment work, but that must not be interpreted as a failed build.

Public URLs are:

```text
https://mwyau.github.io/wave-motions-in-the-ocean/
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf
https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions-facsimile.pdf
```

Do not deploy the repository root or render `README.md` as the Pages homepage.

## Figure policy

- Use direct crops from committed source PDFs for untouched complex/historical art; do not commit an intermediate source raster.
- Use TikZ/vector source for simple analytic diagrams when scientific meaning can be preserved exactly.
- If a figure genuinely requires deskewing, cleaning, repair, contrast correction, or another intentional raster edit, commit only the final edited raster. Prefer native embedded resolution and avoid screenshots or repeated lossy recompression.
- Keep figure provenance sufficient to regenerate source/reconstruction comparisons with `scripts/compare-figures.py`.
- Record vectorization/edit decisions and scientific review status in `reconstruction/FIGURE_AUDIT.md`.
- Do not keep duplicate “before/after” raster stages merely for tracking.

## Text, equation, and scientific audit

Reconstruction is not complete merely because the files build. Continue auditing in small reviewable batches.

1. **Text fidelity:** compare scan ↔ LaTeX for wording, punctuation, capitalization, symbols, references, footnotes, page order, and figure labels. Do not modernize historical prose casually.
2. **Equation transcription:** compare every mathematical symbol, sign, factor, subscript, and superscript directly with the scan.
3. **Scientific equation audit:** independently check dimensions, signs, factors, definitions, coordinate conventions, derivation steps, boundary conditions, limiting cases, and consistency with surrounding prose.
4. **Scientific figure audit:** check axes, units, signs, propagation direction, orientation, node/antinode placement, dispersion relationships, phase arrows, boundary conditions, and agreement with nearby equations/prose.

For scientific verification, consult the cited original paper where applicable, Hendershott/Myrl material when relevant, and another authoritative physical-oceanography source when practical. Do not silently “fix” a scientifically questionable historical equation or figure: document the suspected source error, evidence, and review status in `ERRATA.md` first.

Preserve the historical derivation style and physical reasoning rather than rewriting the notes as a modern textbook.

## Tracking files

- `reconstruction/ERRATA.md`: actual corrections, suspected source errors, evidence, and review status.
- `reconstruction/FIGURE_AUDIT.md`: figure provenance, conversion decisions, and scientific figure review.
- `reconstruction/PLAN.md`: audit coverage, current status, and remaining work.

Do not create a separate verification TSV, source manifest, hash ledger, generated status ledger, or other duplicate tracking system.

## Completion gate

Before considering repository work complete:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For affected figures, also run the relevant `scripts/compare-figures.py` checks.

Verify at minimum:

- facsimile pagination remains 184 pages unless an explicitly reviewed change requires otherwise;
- PDFs parse/render successfully and LaTeX references resolve;
- modern title page is unnumbered, front matter uses Roman numerals, and Chapter 1 starts at Arabic page 1;
- `dist/` contains the complete HTML site and both PDFs;
- README synchronization passes;
- README and HTML share chapter/section Contents, both Downloads, and the CC statement;
- section anchors work;
- modern contents contain chapters and sections only;
- Pages artifact root is `dist/`;
- `PLAN.md`, `ERRATA.md`, and `FIGURE_AUDIT.md` are updated when the work changes their scope.
