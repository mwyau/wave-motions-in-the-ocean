# Figure audit

<!-- Generated from src/figures/CHAPTER1.md through src/figures/CHAPTER6.md. -->

FIGURES.md tracks scientific and technical figures in Chapters 1–6; cover art, photographs, and other editorial images are outside this audit.

The chapter files contain the detailed placement entries. They are ordered by printed page, figure order on that page, and component asset.

The committed 1989 PDFs are the visual and scientific reference. A figure is not accepted merely because it looks cleaner: direction, magnitude relationships, wavelength, nodes, tangencies, boundary contact, coordinate orientation, and consistency with nearby equations must also survive review.

Representation describes the maintained scientific asset:

- `vector` — a maintained TikZ/vector reconstruction with its source-PDF review crop when provenance is recorded.
- `source-pdf` — a direct crop retained from the immutable source PDF because redrawing would add interpretation risk.

Equation checks remain separate:

- `ai-checked` — all materially equation-constrained content has been checked by an AI model against the governing equation(s), analytically or numerically as appropriate. This is not human validation or peer review.
- `partial` — some equation-constrained content has been checked, but another material part remains schematic or lacks a direct check.
- `pending` — equation checking materially applies but has not yet been completed and recorded.
- `n/a` — no meaningful equation-defined quantity or relation controls the figure; visual, geometric, source, and source-fidelity checks still apply.

An existing equation-check state records a prior audit; it is not proof to inherit blindly after a material figure change. A source mismatch may still be `ai-checked` when the mismatch itself has been checked and is recorded in `ERRATA.md`. `ERRATA.md` owns source discrepancies and approval state; the chapter ledgers cross-reference errata rather than duplicating proposed corrections.

This is an asset/placement ledger, not a count of distinct figures in the book: one numbered figure can use more than one underlying asset or source crop. Keep those components separate.

Every `.tikz` file carries a `wave-source` comment naming the source PDF, physical page, and crop. Run `uv run --frozen python scripts/compare_figures.py <stem>` after changing TikZ or crop metadata; it updates the checked-in `.svg` and `.png` siblings. Use `--comparison` only when a temporary raster side-by-side image under `audit/` is useful. Generated previews are not independently edited and never imply human acceptance.

Review the committed source crop and vector rendering together. Check axes, coordinates, signs, orientation, propagation and group-velocity directions, boundary contact, labels, and any equation-defined curves or modes. The 1989 source PDFs remain the source-fidelity authority; a scientific finding does not authorize a substantive source correction.

For source-backed TikZ figures, run `uv run --frozen python scripts/compare_figures.py <stem>` after changing the drawing or provenance metadata. The publication checks validate the recorded SVG/PNG freshness metadata; they do not imply scientific or human acceptance.

## Summary

The six chapter ledgers contain **104 scientific figure placements**.

| Chapter | Placements | vector | source-pdf |
| --- | ---: | ---: | ---: |
| Chapter 1 | 7 | 7 | 0 |
| Chapter 2 | 10 | 10 | 0 |
| Chapter 3 | 12 | 11 | 1 |
| Chapter 4 | 30 | 28 | 2 |
| Chapter 5 | 31 | 26 | 5 |
| Chapter 6 | 14 | 12 | 2 |
| **Total** | **104** | **94** | **10** |

## Chapters

- [Chapter 1](figures/CHAPTER1.md) — 7 placements
- [Chapter 2](figures/CHAPTER2.md) — 10 placements
- [Chapter 3](figures/CHAPTER3.md) — 12 placements
- [Chapter 4](figures/CHAPTER4.md) — 30 placements
- [Chapter 5](figures/CHAPTER5.md) — 31 placements
- [Chapter 6](figures/CHAPTER6.md) — 14 placements

## Audit conventions

Keep entries ordered by actual visual appearance. If one printed figure uses several component assets, keep those components together in their visual order. Preserve source discrepancies and approval state in `ERRATA.md`; this ledger records the figure asset and its scientific and equation checks.

For any proposed substantive departure from the source, record a `pending-human-approval` erratum. Do not infer or assign human approval from a build, test, or scientific judgment.

## Sizing and acceptance rules

1. Size is part of the audit. A scientifically correct redraw should also occupy roughly the same useful page area as the source without clipping or forcing surrounding text into poor layout.
2. Prefer changing vector drawing scale/extent at the vector source so PDF and generated SVG/HTML inherit the same improvement. Avoid PDF-only sizing hacks.
3. A source crop may keep its source aspect ratio and whitespace when that whitespace carries geometry or annotations; otherwise trim should be tightened in the chapter inclusion rather than resampling the image.
4. Arrowheads must be checked for propagation/group-velocity direction, not only placement. Equal-magnitude vectors must be constructed from equal geometry rather than estimated visually.
5. Wave crests/wavelength markers must be generated from the same wavelength parameter when a quantitative relation is implied.
6. On spherical/curvilinear figures, verify whether vectors/curves actually touch or are tangent to the intended latitude/longitude/meridian construction. Do not infer contact from a low-resolution scan.
7. For free-mode joins, enforce the stated matching conditions (for example both field and flux/transport continuity), not only positional continuity.
8. The committed Original/Vector pair is the visual review surface; freshness checks do not imply scientific or human acceptance.
9. Representation and equation check are independent. A vector may remain pending for equation checking, and a kept source-PDF figure may be `ai-checked` even when it intentionally preserves a documented source error.

## Batch verification checklist

For every changed vector:

01. Inspect the full source page at high resolution.
02. Read the nearby equations/prose and list the geometric constraints.
03. Identify which equation-defined quantities materially control the figure, if any.
04. Encode those constraints in coordinates/equations where practical.
05. For equation-defined charts or curves, independently evaluate or plot the stated equation when practical and compare it to the vector reconstruction.
06. For equation-constrained geometry, independently calculate the relevant angles, ratios, intersections, boundary values, continuity conditions, or vector directions rather than checking only by eye.
07. Compile the TikZ independently.
08. Inspect arrowheads, labels, tangencies, crossings, wavelength, amplitude ratios, and final scale.
09. Update the same-stem SVG/PNG pair and open the affected chapter entry.
10. Compile both PDF editions and generated HTML/EPUB at the batch checkpoint.
11. Compare affected pages/assets with the source.
12. Record intentional schematic simplifications and the explicit `Equation check` state in the chapter ledger.

Direct source crops use the committed PDF page through `\includegraphics[page=...,trim=...,clip]`; no permanent raster intermediary is committed unless the source-only asset is intentionally retained.
