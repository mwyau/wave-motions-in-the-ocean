# Figure audit skill

Use this skill for figure extraction, direct source crops, TikZ/vector reconstruction, intentional raster editing, comparison, and scientific figure review.

## Source authority and correction boundary

The committed source PDFs are the historical visual authority. A figure audit may identify a scientific or geometric problem, but that finding does not authorize silently correcting the historical figure.

Choose the least destructive faithful representation:

1. **Untouched complex/historical art:** use a direct crop from the committed source PDF. Do not commit an intermediate raster.
1. **Simple analytic or geometric diagrams:** use TikZ/vector source only when the visible geometry, labels, orientation, and scientific meaning can be reproduced reliably.
1. **Genuinely damaged/skewed raster art:** extract at native embedded resolution where practical, make only controlled edits, and commit only the final edited raster.

Do **not** use generative image synthesis to reconstruct scientific figures. Do not invent missing geometry or labels.

A scientifically “better” redraw is not automatically a faithful reconstruction. If the source figure, nearby equation, and physical interpretation disagree, preserve the historical source representation and record a `pending-human-approval` erratum. Only an explicitly `human-approved` erratum authorizes a substantive corrected redraw.

Autonomous textual corrections inside a reconstructed figure follow the same minor-correction rule as the source-audit skill: small, unambiguous spelling, grammar, transcription, or punctuation fixes are allowed when they cannot plausibly affect scientific, mathematical, bibliographic, or substantive editorial meaning. If uncertain, preserve the source and ask for human review.

Avoid screenshots, repeated lossy recompression, and committed before/after copies. Temporary source renders, comparison images, numerical/reference plots, and scratch audit evidence belong under the ignored `audit/` workspace, preferably in a task-specific subdirectory such as `audit/figures/`.

## Provenance and ledger

Record figure state, provenance, representation choice, review status, and equation-validation status in `reconstruction/FIGURES.md`.

Use `Equation validation` consistently:

- **Validated** — all materially equation-constrained content has been independently checked against the governing equation(s), analytically or numerically as appropriate.
- **Partial** — some equation-constrained content has been independently checked, but another material part is schematic or still lacks a direct check.
- **Pending** — an equation check materially applies but has not yet been independently completed and recorded.
- **N/A** — no meaningful equation-defined quantity or relation applies; visual, geometric, provenance, and source-fidelity checks still do.

`Validated` means the scientific comparison was performed. It does **not** mean an erratum is approved, and it does not permit the vector to depart from an unapproved historical source error. A historical mismatch may therefore be scientifically `Validated` while the rendered reconstruction still preserves the source and `ERRATA.md` records the discrepancy as pending human approval.

Do not infer `Validated` merely because a TikZ file contains a formula or visually resembles the scan. Record it only after an independent equation evaluation, calculation, or reference plot has been compared with the figure.

Retained TikZ figures should carry their `wave-source` provenance comment. Intentionally edited rasters should retain equivalent embedded source metadata when tooling supports it.

A substantive discrepancy between source and reconstruction also belongs in `reconstruction/ERRATA.md`; the figure ledger is not an approval mechanism or substitute errata ledger.

## Scientific figure audit

Check more than visual resemblance. Verify as applicable:

- axes, coordinates, units, signs, and orientation;
- wavevector, phase, group-velocity, propagation, and circulation directions;
- normals, reflection/refraction geometry, slopes, depths, coast/bottom orientation;
- nodes/antinodes, mode order, turning points, asymptotes, cutoffs, roots, extrema, and dispersion branches;
- labels and mathematical annotations against nearby equations/prose;
- boundary and matching conditions represented by the drawing;
- normalized/display-only geometry versus physically constrained geometry.

If a curve, surface, dispersion diagram, mode shape, ray path, or other plotted quantity is defined by an equation, independently evaluate or plot that equation whenever practical and compare:

**governing equation → historical source figure → reconstructed figure**.

Do not freehand an equation-defined curve merely to resemble the scan. Conversely, do not replace a historical source curve with a mathematically corrected one without human approval when the two disagree.

For simple analytic geometry, an independent symbolic or numerical check is sufficient when a plotted reference curve adds no information. Record which quantities were checked.

If a redraw is schematic, state which properties are schematic and which are equation-constrained. Use `Partial` rather than `Validated` if a material equation-defined part remains unchecked.

## Vector verification workflow

For each new or materially changed vector:

1. Inspect the full source page at high resolution.
1. Inspect surrounding equations and prose.
1. List the scientifically meaningful constraints shown by the figure.
1. Independently check applicable equations/geometry.
1. Build a faithful TikZ/vector representation without silently repairing source errors.
1. Compile the TikZ independently.
1. Inspect at final publication scale for labels, arrows, line contact, clipping, scale, and whitespace.
1. Regenerate the comparison:

```bash
python3 scripts/compare_figures.py <figure-name>
```

9. Inspect the affected full PDF/HTML/EPUB output as appropriate.
1. Update `FIGURES.md`; record any substantive source problem in `ERRATA.md` as `pending-human-approval` unless explicit human approval already exists.

Use `python3 scripts/compare_figures.py --all` only for a deliberate whole-ledger pass. Keep generated comparisons under `audit/figures/comparisons/`; do not use `build/` for persistent audit evidence.

## Raster editing

When an intentional raster edit is necessary:

- prefer the PDF's native embedded image over a rendered screenshot;
- preserve resolution and use lossless output where practical;
- perform only defensible crop, deskew, cleanup, or contrast operations that do not change scientific content;
- keep only the final edited book image in Git;
- record the source page/crop and edit in `FIGURES.md` and embedded metadata where supported;
- audit equation-defined scientific content separately from raster quality.

## Completion

After figure work, run the relevant comparison plus the publication build containing the figure. For a coherent batch, finish with `./scripts/build.sh all`.

Before considering a figure audit complete, confirm that every figure/direct source crop has an explicit equation-validation state and that every `Validated`/`Partial` claim has recoverable calculation/equation evidence. Scientific validation is never a substitute for the separate human-approval requirement for substantive source corrections.
