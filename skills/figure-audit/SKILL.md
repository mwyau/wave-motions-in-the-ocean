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

Record figure state, provenance, reconstruction choice, and review status in `reconstruction/FIGURES.md`.

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

If a redraw is schematic, state which geometric properties are schematic and which are enforced by the equations.

## Vector verification workflow

For each new or materially changed vector:

1. Inspect the full source page at high resolution.
2. Reproduce all scientifically meaningful geometry and labels.
3. For equation-defined charts or curves, independently generate numerical/analytic reference values or a reference plot from the stated equation when practical, and verify branches, roots, extrema, slopes, asymptotes, cutoffs, intersections, and relative scale against the vector reconstruction.
4. Compile the TikZ independently.
5. Inspect at final publication scale for label/line collisions and legibility.
6. Regenerate the source/reconstruction comparison:

```bash
python3 scripts/compare-figures.py <figure-name>
```

7. Inspect the affected full PDF/HTML/EPUB output as appropriate.
8. Record the result in `FIGURES.md`; record substantive corrections in `ERRATA.md`.

Use `python3 scripts/compare-figures.py --all` for a deliberate whole-ledger comparison pass, not routinely for every small edit.

## Raster editing

When an intentional raster edit is necessary:

- prefer the PDF's native embedded image over a rendered screenshot;
- preserve resolution and use lossless output where practical;
- perform only defensible operations such as crop, deskew, cleanup, or contrast correction;
- keep only the final edited book image in Git;
- record the source page/crop and edit in `FIGURES.md` and embedded metadata where supported.

## Completion

After figure work, run the relevant comparison plus the publication build that contains the figure. For a coherent repository batch, finish with `./scripts/build.sh all`.
