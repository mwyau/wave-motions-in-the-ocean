# Reconstruction plan

The first full transcription is present. Ongoing work is audit, scientific verification, typography refinement, figure review, and publication-format improvement—not a second parallel content tree.

## Current baseline

- [x] Five historical source PDFs committed under `source/`.
- [x] Historical title page, both prefaces, and original contents transcribed.
- [x] Chapters 1--6 present as one canonical file per chapter.
- [x] Printed pp. 1--174 represented in the logical reconstruction.
- [x] One shared BibTeX database for both editions and HTML.
- [x] Vector replacement registry removed; chapters now name TikZ/direct-source art explicitly.
- [x] Source-capture/vector-preview PNG audit copies removed; comparisons regenerate on demand.
- [ ] Lake Como photograph: add `figures/frontmatter/salmon-hendershott-como-1980.jpeg` when supplied, then verify PDF and HTML placement.

## Text/equation audit coverage

A first transcription pass exists for the whole work. The old per-chapter audit files were consolidated during repository cleanup; their substantive deviations remain or should be migrated into `ERRATA.md` as review proceeds.

- [x] Front matter: direct source read completed; compiled visual tuning still continues.
- [x] Chapter 1 (pp. 1--17): first fidelity pass present.
- [x] Chapter 2 (pp. 18--37): verbatim restoration and targeted scientific checks completed; independent final pass still required.
- [x] Chapter 3 (pp. 38--63): verbatim restoration and targeted checks completed; independent final pass still required.
- [x] Chapter 4 (pp. 64--95): verbatim restoration and targeted checks completed; independent final pass still required.
- [x] Chapter 5 (pp. 96--148): verbatim restoration present; numerous source errata already documented.
- [x] Chapter 6 + references (pp. 149--174): transcription present; targeted source errata documented.
- [ ] Continue scan-to-LaTeX lexical/symbol audit chapter by chapter in small batches.
- [ ] Continue independent scientific equation audit: dimensions, signs, factors, conventions, boundary conditions, limiting cases, and cited-source checks.
- [ ] Record uncertain scientific issues as `pending-review`; do not silently rewrite them.

## Figure audit/vector work

- [x] Existing simple analytic diagrams retained as TikZ with source provenance embedded in each `.tikz` file.
- [x] Untouched complex historical figures are built directly from the committed source PDFs.
- [x] `scripts/compare-figures.py` regenerates source/vector or source/edited-raster comparisons without committed intermediates.
- [ ] Re-review existing vectors for scientific meaning, not just visual resemblance.
- [ ] Continue vectorization only where it preserves all scientific content; leave dense/source-specific art as direct PDF crops.
- [x] Current deskewed pp. 124/126 figures retain only final lossless PNGs extracted from native embedded source images; provenance/edit metadata is recorded in the PNGs and `FIGURE_AUDIT.md`.
- [ ] For any future edited raster, keep only the final book image and log native-image provenance/edit details in `FIGURE_AUDIT.md`.

## Typography and semantic structure

- [ ] Continue empirical facsimile typography comparison on representative dense, sparse, equation-heavy, figure-heavy, chapter-opening, and bibliography pages while preserving the accepted 184-page logical edition.
- [ ] Continue modern typography/accessibility refinements without changing shared content.
- [ ] Introduce semantic figure numbering/labels (`Figure 5.1`, etc.) in a later focused pass.
- [ ] Introduce stable chapter-based equation numbering/labels in a later focused pass.

## HTML / publication

- [x] Initial chapter-split HTML build from the modern LaTeX source.
- [ ] Continue MathJax/Pandoc compatibility and mobile styling improvements as needed.
- [ ] EPUB after HTML is stable.
- [ ] GitHub Release automation only after reconstruction/versioning is stable; do not add tag automation yet.
