# Repository instructions

## Core invariants

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- The facsimile PDF, modern PDF, and HTML edition share the same `chapter1.tex`--`chapter6.tex`, figures, corrections, and `references.bib`.
- Correct shared content once. Record every substantive deviation from the scan in `reconstruction/ERRATA.md`.
- Facsimile and modern editions differ only where explicitly intended: front matter, typography, spacing, navigation, and pagination/page-break behavior.
- Generated PDFs, HTML, comparison images, LaTeX auxiliaries, and other build products are not committed.
- Do not add source hashes, source manifests, verification TSVs, or generated build-status ledgers.

## Text and scientific audit

Work in small reviewable batches. Distinguish these checks:

1. **Text fidelity:** compare scan ↔ LaTeX for wording, punctuation, capitalization, symbols, subscripts/superscripts, references, footnotes, page order, and figure labels. Do not modernize prose merely because it sounds old.
2. **Equation transcription:** compare every mathematical symbol and sign directly with the scan.
3. **Scientific equation audit:** independently check dimensions, signs, factors (`2`, `pi`, `g`, `f`, `H`, etc.), definitions, coordinate conventions, derivation steps, boundary conditions, limiting cases, and consistency with surrounding prose. Verify standard results against the cited original paper, Hendershott/Myrl material where relevant, and another authoritative physical-oceanography source when practical.
4. **Scientific figure audit:** check axes, units, signs, propagation direction, orientation, node/antinode placement, dispersion relationships, phase arrows, boundary conditions, and agreement with nearby equations/prose.

Do not silently alter a scientifically questionable historical equation or figure. Record the suspected source error, evidence, and review status in `ERRATA.md`. Preserve the historical derivation style and logic rather than rewriting it as a modern textbook.

## Figure policy

- Use direct crops from the committed source PDF for untouched complex/historical art; do not commit an intermediate PNG.
- Use TikZ/vector source for simple analytic diagrams when scientific meaning can be preserved exactly.
- If a source figure genuinely requires deskewing, cleaning, manual repair, contrast correction, or another intentional raster edit, commit only the final edited raster. Extract at the PDF's native embedded resolution where possible; avoid screenshots and repeated lossy recompression.
- Each retained TikZ file carries a `wave-source` provenance comment used by `scripts/compare-figures.py` to regenerate comparisons on demand.
- Each intentionally edited raster carries equivalent `wave-source-*` PNG metadata so comparisons can be regenerated without keeping a duplicate source raster.
- Record figure status and decisions in `reconstruction/FIGURE_AUDIT.md`.

## Completion gate

Before considering work complete, run:

```bash
./scripts/build.sh all
```

For figure work, also run `python scripts/compare-figures.py <figure>` for affected figures. Update `PLAN.md`, `ERRATA.md`, and `FIGURE_AUDIT.md` as appropriate.
