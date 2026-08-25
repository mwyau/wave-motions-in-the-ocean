# Figure audit skill

Use this skill for figure extraction, direct source crops, TikZ/vector reconstruction, intentional raster editing, comparison, and scientific figure review.

## Source authority and correction boundary

The committed 1989 PDFs under `references/chapman-rizzoli-1989/` control visual source checks. A figure audit may identify a scientific or geometric problem, but that finding does not authorize silently correcting the source figure.

Use the same check order for figures: check the 1989 PDF first, independently check the science or math when needed, then use the 2008 MIT OpenCourseWare notes and other references to help understand a possible error. A similar figure in the 2008 notes does not by itself show that the 1989 reconstruction is wrong or authorize a redraw. Agreement between sources is not an independent scientific check.

Choose the least destructive faithful representation:

1. **Untouched complex/source art:** use a direct crop from the committed source PDF. Do not commit an intermediate raster.
2. **Simple analytic or geometric diagrams:** use TikZ/vector source only when the visible geometry, labels, orientation, and scientific meaning can be reproduced reliably.
3. **Genuinely damaged/skewed raster art:** extract at native embedded resolution where practical, make only controlled edits, and commit only the final edited raster.

Do **not** use generative image synthesis to reconstruct scientific figures. Do not invent missing geometry or labels.

A scientifically “better” redraw is not automatically a faithful reconstruction. If the source figure, nearby equation, and physical interpretation disagree, preserve the source representation and record a `pending-human-approval` erratum. Only a `human-approved` erratum authorizes a substantive corrected redraw, and an agent may create that status only when the owner directly approves it in the current chat.

## Source-visible content in vectors

A TikZ/vector figure has two distinct correctness dimensions: source fidelity and scientific audit. The scientific audit can identify problems, but it cannot override source fidelity.

Source-visible scientific content includes labels, variables, vector marks, plus/minus signs, numerator/denominator expressions, limits such as `ell=infinity`, arrow and ray directions, orientation, branch and root placement, boundary relationships, and relative geometry when it carries scientific meaning. These must match the 1989 figure unless the specific erratum is approved.

An equation-generated reconstruction may calculate geometry independently, but `equation → source → reconstruction` is a check pipeline, not automatic authorization to replace the source. If the governing equation and source figure disagree:

1. confirm the source figure literally;
2. independently verify the equation or science;
3. record a pending erratum;
4. keep the vector faithful to the source;
5. do not render the scientifically corrected version as the maintained reconstruction.

Temporary corrected or reference plots belong only under the ignored `audit/` workspace. The maintained artifact is a source-faithful vector; a scientifically corrected hypothetical vector is audit evidence only unless the owner approves it.

Autonomous textual corrections inside a reconstructed figure follow the same minor-correction rule as the source-audit skill: small, unambiguous spelling, grammar, transcription, or punctuation fixes are allowed when they cannot plausibly affect scientific, mathematical, bibliographic, or substantive editorial meaning. If uncertain, preserve the source and ask for human review.

Avoid screenshots, repeated lossy recompression, and committed before/after copies. Temporary source renders, comparison images, numerical/reference plots, and scratch audit evidence belong under the ignored `audit/` workspace, preferably in a task-specific subdirectory such as `audit/figures/`.

## Figure ledger

Record figure state, source info, representation choice, and equation/scientific
checks in `src/FIGURES.md`. For a vector reconstruction, the committed
same-stem PNG and SVG are the visual review surface.

Keep entries ordered by chapter, then printed page, then asset name.

Track the literal representation:

- **Representation:** `vector`, `source-pdf`, `edited-raster`, or another literal representation such as `source-photo` when needed.

Use `Equation check` consistently:

- `ai-checked` — all materially equation-constrained content has been checked by an AI model against the governing equation(s), analytically or numerically as appropriate. This is not human validation or peer review.
- `partial` — some equation-constrained content has been checked, but another material part is schematic or still lacks a direct check.
- `pending` — an equation check materially applies but has not yet been completed and recorded.
- `n/a` — no meaningful equation-defined quantity or relation applies; visual, geometric, source, and source-fidelity checks still do.

`ai-checked` means the scientific comparison was performed by an AI model. It does **not** mean an erratum is approved, and it does not permit the vector to depart from an unapproved source error. A source mismatch may therefore be `ai-checked` while the rendered reconstruction still preserves the source and `ERRATA.md` records the discrepancy as pending human approval.

Do not infer `ai-checked` merely because a TikZ file contains a formula or visually resembles the scan. Record it only after an equation evaluation, calculation, or reference plot has been compared with the figure.

An existing equation-check state records a prior audit; it is not proof to inherit blindly. If a figure is materially changed, or if its scientific correctness matters to the current task, independently recheck the affected constraints rather than relying on the existing ledger value.

TikZ figures should carry their `wave-source` source comment. Source-PDF-only
placements should use `\sourceart` in the chapter source; intentionally edited
rasters should keep equivalent embedded source metadata when tooling supports it.

For every TikZ figure with source-PDF provenance, maintain these files together:

```text
src/figures/<stem>.tikz  # authored vector source
src/figures/<stem>.svg   # generated vector review/publication asset
src/figures/<stem>.png   # generated original-source crop
```

Run `uv run --frozen python scripts/compare_figures.py <stem>` after changing
TikZ or crop metadata. Do not edit the generated SVG or PNG by hand. Their
source of truth is the TikZ, its provenance metadata, and the committed source
PDF. Generated previews never imply human acceptance.

`ERRATA.md` owns any substantive source discrepancy, proposed correction, evidence, and approval state. `FIGURES.md` owns the figure asset, representation choice, and scientific/equation checks. Cross-reference the erratum concisely instead of copying the full correction into both files.

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

**governing equation → 1989 source figure → reconstructed figure**.

Do not freehand an equation-defined curve merely to resemble the scan. Conversely, do not replace a source curve with a mathematically corrected one without human approval when the two disagree.

For simple analytic geometry, an independent symbolic or numerical check is sufficient when a plotted reference curve adds no information. Record which quantities were checked.

If a redraw is schematic, state which properties are schematic and which are equation-constrained. Use `partial` rather than `ai-checked` if a material equation-defined part remains unchecked.

## Mandatory pre-edit gate for material vector changes

Before materially changing a vector:

1. identify its printed page;
2. search `ERRATA.md` for that page, figure, or equation;
3. check whether an applicable entry is `pending-human-approval`;
4. if so, read its `Source` field before editing;
5. ensure the maintained vector continues to reproduce `Source`, not `Proposed correction`.

A trivial line-position tweak need not use this gate, but it is mandatory when changing labels, equations, scientific notation, arrows or directions, roots or branches, or scientific geometry. Never use the `Proposed correction` field as drawing instructions while the status is pending.

## Vector verification workflow

For every source-backed placement—retained TikZ, source-art or direct-PDF crop,
and maintained raster—review the full source page at 300–400 DPI and
probe each edge in both directions by at least 6 bp. Use the smallest practical
`left bottom right top` rectangle that contains the complete figure with a
small safe margin and no unrelated prose. If no rectangle can separate
overlapping source ink, record a narrow mask in absolute PDF page coordinates
(origin at lower left) beside the source marker and retain the unmasked page
render as audit evidence.

For each new or materially changed vector:

1. Inspect the full source page at high resolution.
2. Inspect surrounding equations and prose.
3. List the scientifically meaningful constraints shown by the figure.
4. Independently check applicable equations/geometry.
5. Build a faithful TikZ/vector representation without silently repairing source errors.
6. Compile the TikZ independently.
7. Inspect at final publication scale for labels, arrows, line contact, clipping, scale, and whitespace.
8. Regenerate the maintained review assets:

```bash
uv run --frozen python scripts/compare_figures.py <figure-name>
```

Use `--comparison` only when a temporary raster side-by-side image under
`audit/` is useful. Open `src/FIGURES.md` to review the committed Original and
Vector pair directly.

09. Inspect the affected full PDF/HTML/EPUB output as appropriate.
10. Update `FIGURES.md`; record any substantive source problem in `ERRATA.md` as `pending-human-approval` unless the owner directly approved the correction in the current chat.

Use `uv run --frozen python scripts/compare_figures.py --all` only for a deliberate whole-ledger pass. Keep generated comparisons under `audit/figures/comparisons/`; do not use `build/` for persistent audit evidence.

## Raster editing

When an intentional raster edit is necessary:

- prefer the PDF's native embedded image over a rendered screenshot;
- preserve resolution and use lossless output where practical;
- perform only defensible crop, deskew, cleanup, or contrast operations that do not change scientific content;
- keep only the final edited book image in Git;
- record the source page/crop and edit in `FIGURES.md` and embedded metadata where supported;
- audit equation-defined scientific content separately from raster quality.

## Mandatory post-edit source-fidelity gate

For every materially changed scientific vector, compare the rendered vector's scientific labels, notation, and geometry directly with the source crop again before considering the work complete. Ask whether the edit made the figure scientifically “better” by departing from the source. If yes, stop, restore source fidelity, and record or propose the correction in `ERRATA.md` instead.

Run this check even when equations were independently verified, tests pass, the vector looks cleaner, or an existing erratum already proposes the same correction. No materially changed vector may be considered complete while it contains a proposed correction from a `pending-human-approval` erratum.

## Completion

After figure work, run the relevant comparison plus the publication build containing the figure. For a coherent batch, finish with `./scripts/build.sh all`.

Before considering a figure audit complete, confirm that every figure/direct
source crop has an explicit representation and equation-check state, every
vector source-PDF pair has fresh committed SVG/PNG siblings, and every
`ai-checked`/`partial` claim has recoverable calculation/equation evidence. AI
checking is never a substitute for the separate human-approval requirement for
substantive source corrections.
