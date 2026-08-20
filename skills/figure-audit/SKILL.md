# Figure audit skill

Use this skill for figure extraction, direct source crops, TikZ/vector reconstruction, intentional raster editing, comparison, and scientific figure review.

## Source authority and decision order

The committed source PDFs are the visual authority. Choose the least destructive representation that preserves the scientific information:

1. **Untouched complex/historical art:** use a direct crop from the committed source PDF. Do not commit an intermediate raster.
2. **Simple analytic diagrams:** use TikZ/vector source only when geometry, labels, orientation, and scientific meaning can be preserved reliably.
3. **Genuinely damaged/skewed raster art:** extract at native embedded resolution where practical, make only controlled edits, and commit only the final edited raster.

Do **not** use generative image synthesis to reconstruct scientific figures. If source geometry or labeling is ambiguous, preserve the source or mark the issue for review rather than inventing information.

Avoid screenshots, repeated lossy recompression, and committed “before/after” copies. Temporary comparisons belong under `build/`.

## Provenance and ledger

Record figure state, provenance, reconstruction choice, review status, and equation-validation status in `reconstruction/FIGURES.md`.

Use the `Equation validation` column consistently:

- **Validated** — all materially equation-constrained content in the figure has been independently checked against the governing equation(s), analytically or numerically as appropriate. This records that the comparison was performed; a historical source mismatch may still be `Validated` when the mismatch is explicitly documented in `ERRATA.md`.
- **Partial** — some equation-constrained content has been independently checked, but another material part is intentionally schematic or still lacks a direct equation check.
- **Pending** — an equation check is materially applicable but has not yet been independently completed and recorded.
- **N/A** — there is no meaningful equation-defined quantity or relation to validate; visual, geometric, provenance, or source-fidelity checks still apply.

Do not infer `Validated` merely because a TikZ implementation contains a formula or because the redraw visually resembles the source. Record `Validated` only after an independent equation evaluation, calculation, or reference plot has been compared with the figure. When practical, state the equation or constrained quantities in the scientific-audit text so the evidence for the status is recoverable.

Retained TikZ figures should carry their `wave-source` provenance comment. Intentionally edited rasters should retain equivalent embedded source metadata when the existing tooling supports it.

A substantive discrepancy between source and reconstruction also belongs in `reconstruction/ERRATA.md`; do not use the figure ledger as a substitute for errata.

## Scientific figure audit

Check more than visual resemblance. Verify:

- axes, coordinates, units, signs, and orientation;
- wavevector, phase, group-velocity, propagation, and circulation directions;
- normals, reflection/refraction geometry, slopes, depths, coast/bottom orientation;
- nodes/antinodes, mode order, turning points, asymptotes, cutoffs, and dispersion branches;
- labels and mathematical annotations against nearby equations/prose;
- boundary and matching conditions represented by the drawing;
- any normalized/display-only geometry versus physically constrained geometry.

If a curve, surface, dispersion diagram, mode shape, or other plotted quantity is defined by an equation in the notes, independently evaluate or plot that equation whenever practical and compare the result with both the historical source and the vector reconstruction. Do not accept a freehand vector curve merely because it resembles the scan when the mathematical curve can be checked directly.

For simple analytic geometry, an independent symbolic or numerical check is sufficient when a plotted reference curve would add no information: for example, verify reflection angles from constructed vectors, boundary-condition values at the drawn boundary, or continuity/flux matching on both sides of an interface. Record which quantities were checked.

If a redraw is schematic, state which geometric properties are schematic and which are enforced by the equations. Use `Partial` rather than `Validated` if a material equation-defined part remains schematic without an independent equation check.

## Vector verification workflow

For each new or materially changed vector:

1. Inspect the full source page at high resolution.
2. Reproduce all scientifically meaningful geometry and labels.
3. Identify every governing equation or equation-derived constraint that materially controls the figure. If none applies, record `N/A` rather than manufacturing an equation test.
4. For equation-defined charts or curves, independently generate numerical/analytic reference values or a reference plot from the stated equation when practical, and verify branches, roots, extrema, slopes, asymptotes, cutoffs, intersections, and relative scale against the vector reconstruction.
5. For equation-constrained geometry, independently calculate the relevant angles, ratios, intersections, boundary values, continuity conditions, or vector directions rather than checking only by eye.
6. Compile the TikZ independently.
7. Inspect at final publication scale for label/line collisions and legibility.
8. Regenerate the source/reconstruction comparison:

```bash
python3 scripts/compare-figures.py <figure-name>
```

9. Inspect the affected full PDF/HTML/EPUB output as appropriate.
10. Record the result and the `Equation validation` state in `FIGURES.md`; record substantive corrections in `ERRATA.md`.

Use `python3 scripts/compare-figures.py --all` for a deliberate whole-ledger comparison pass, not routinely for every small edit.

## Raster editing

When an intentional raster edit is necessary:

- prefer the PDF's native embedded image over a rendered screenshot;
- preserve resolution and use lossless output where practical;
- perform only defensible operations such as crop, deskew, cleanup, or contrast correction;
- keep only the final edited book image in Git;
- record the source page/crop and edit in `FIGURES.md` and embedded metadata where supported;
- if the raster depicts an equation-defined chart or field, audit that scientific content against the governing equation separately from the raster-quality check and record its equation-validation state.

## Completion

After figure work, run the relevant comparison plus the publication build that contains the figure. For a coherent repository batch, finish with `./scripts/build.sh all`.

Before considering a figure audit complete, confirm that `FIGURES.md` has an explicit `Equation validation` value for every figure or direct source crop and that every `Validated`/`Partial` claim is supported by a recoverable calculation, equation reference, or reference plot rather than visual similarity alone.
