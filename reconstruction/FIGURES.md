# Figure audit

This file tracks figures used in the reconstructed book. The PDFs in `../source/` are the visual and scientific reference. A figure is not accepted merely because it looks cleaner: direction, magnitude relationships, wavelength, nodes, tangencies, boundary contact, coordinate orientation, and consistency with the nearby equations must also survive review.

Statuses:

- `source-pdf` — untouched crop from a source PDF;
- `edited-raster` — edited raster retained as the final book image;
- `vector-complete` — TikZ/vector reconstruction rechecked against source and nearby physics;
- `vector-review-needed` — vector exists but an identified issue still needs resolution;
- `vector-candidate` — a source crop may be worth redrawing later.

Every `.tikz` file carries a `wave-source` comment naming the source PDF, physical page, and crop. `scripts/compare-figures.py` regenerates temporary side-by-side comparisons under `build/comparisons/`; comparison outputs are never committed.

## Committed figure assets — image-by-image audit

### Chapter 1

| Asset | Printed page | Status | Scientific audit |
|---|---:|---|---|
| `ch01-p004-phase-speed.tikz` | 4 | **vector-complete** | Phase planes are normal to `k`; component geometry and displayed wavelength are mutually consistent. |
| `ch01-p008-spectrum.tikz` | 8 | **vector-complete** | Narrow-band spectrum is centered at `k_0`; labels do not obscure the curve. |
| `ch01-p008-wave-packet.tikz` | 8 | **vector-complete** | Carrier wavelength matches the marked `2 pi/k_0`; envelope and scale annotations are consistent. |
| `ch01-p010-stationary-phase.tikz` | 10 | **vector-complete** | Stationary region is at `k_0`; oscillations become progressively faster away from it. |
| `ch01-p012-wave-crest-path.tikz` | 12 | **vector-complete** | Crest family and the two A-to-B paths preserve the circulation/wavenumber argument. |
| `ch01-p015-initial-wave-groups.tikz` | 15 | **vector-complete** | Display wavelengths and local `k` plateaus use the same normalization. |
| `ch01-p016-ray-crossing.tikz` | 16 | **vector-complete** | Packet centers lie on their rays and preserve the p.15 carrier wavelengths. |

Chapter 1 has no direct source-PDF crop placements in the book body.

### Chapter 2

| Asset | Printed page | Status | Scientific audit |
|---|---:|---|---|
| `ch02-p021-solid-boundary-reflection.tikz` | 21 | **vector-complete** | Boundary, incident crest orientation, and reflected propagation are source-faithful. |
| `ch02-p022-specular-reflection.tikz` | 22 | **vector-complete** | Boundary normal is exactly perpendicular to the wall and incident/reflected `k` are exact mirrors, enforcing equal angles. |

### Chapter 3

There are no committed replacement/vector assets. All retained Chapter 3 figures are direct source-PDF crops; see the placement inventory below.

### Chapter 4

| Asset | Printed page | Status | Scientific audit |
|---|---:|---|---|
| `ch04-p065-parcel-displacement.tikz` | 65 | **vector-complete** | Background-density profile, equilibrium location, and upward displacement `xi` are preserved; curvature is schematic. |
| `ch04-p068-boundary-value-problem.tikz` | 68 | **vector-complete** | Free-surface, interior, and bottom boundary conditions follow the adjacent derivation. |
| `ch04-p069-dispersion-cone.tikz` | 69 | **vector-complete** | Cone satisfies `m^2=R^2(k^2+ell^2)` and the projected axes/angle are consistent. |
| `ch04-p078-case-a-intersections.tikz` | 78 | **vector-complete** | Curves use the stated normalized equations and yield the two symmetric real roots. |
| `ch04-p078-case-a1-no-intersections.tikz` | 78 | **vector-complete** | Curves have opposite sign for every nonzero real `k`, so no propagating real root is implied. |

### Chapter 5

Chapter 5 was re-audited first on 2026-08-20. Four previously accepted drawings required scientific geometry corrections; those corrections are now encoded in the vector construction rather than left to visual approximation.

| Asset | Printed page | Status | Scientific audit |
|---|---:|---|---|
| `ch05-p108-wall-reflection.tikz` | 108 | **vector-complete** | Re-audited 2026-08-20: reflected endpoint is the exact mirror of the incident endpoint about the wall normal, so `alpha_R=alpha_I` and displayed ray magnitudes are equal. Enlarged from the earlier undersized redraw. |
| `ch05-p108-rectangular-basin.tikz` | 108 | **vector-complete** | Four walls and `x=0,a`, `y=0,b` geometry reproduce the source. |
| `ch05-p110-depth-step-rays.tikz` | 110 | **vector-complete** | Re-audited 2026-08-20: reflected ray is an exact mirror of the incident ray; transmitted ray remains schematic but bends toward the normal for the stated depth ordering. Figure scale increased. |
| `ch05-p114-step-shelf.tikz` | 114 | **vector-complete** | Coast, shelf width `L`, and `D_1/D_2` step geometry reproduce the source. |
| `ch05-p114-ray-paths.tikz` | 114 | **vector-complete** | Re-audited 2026-08-20: coast and shelf-edge bounces are built from mirrored ray segments; source arrow traversal is preserved; refraction at `x=L` is schematic rather than a quantitative Snell construction. |
| `ch05-p115-edge-wave-profile.tikz` | 115 | **vector-complete** | Re-audited 2026-08-20: shelf cosine and offshore exponential now satisfy both `eta` continuity and `D eta_x` continuity at `x=L`; display-only parameters are identified in comments and are not presented as source data. Figure enlarged. |
| `ch05-p116-edge-wave-dispersion.tikz` | 116 | **vector-complete** | First three branches are generated from the stated matching relation; branch cutoffs/asymptotes come from the dispersion relation. |
| `ch05-p117-forced-shelf-profile.tikz` | 117 | **vector-complete** | Preserves `A cos(k_1 x)` on the shelf and a longer-wavelength deep-ocean oscillation; it is a qualitative forced-profile sketch, not a generic derivative-matched free mode. |
| `ch05-p118-coastal-seiche-modes.tikz` | 118 | **vector-complete** | Both modes have the common shelf-break elevation node; the higher mode adds one shelf zero as required. |
| `ch05-p119-particle-motion.tikz` | 119 | **vector-complete** | Phase planes are normal to `k`; no-rotation displacement is parallel to `k`, while rotating trajectories are clockwise ellipses consistent with `u/v=i sigma/f`. |
| `ch05-p123-waveguide-channel.tikz` | 123 | **vector-complete** | Two channel walls and `v=0`, `y=0,a` labels reproduce the source geometry. |
| `ch05-p124-amphidromic-pattern.png` | 124 | **edited-raster** | Native embedded 300-ppi CCITT page strips were extracted and deskewed; only the final lossless PNG is retained. Pixel-level source comparison remains an appropriate future provenance check, not a reason to redraw the field. |
| `ch05-p125-closed-channel.tikz` | 125 | **vector-complete** | Three closed-channel boundaries and `u=0`, `v=0`, `x=0`, `y=0,a` labels are preserved. |
| `ch05-p126-kelvin-turning-corner.png` | 126 | **edited-raster** | Native embedded 300-ppi CCITT page strips were extracted and deskewed; only the final lossless PNG is retained. |
| `ch05-p129-rossby-cg.tikz` | 129 | **vector-complete** | Constant-frequency circle follows the stated Rossby relation; group-velocity direction is normal to the circle. |
| `ch05-p130-westward-propagation.tikz` | 130 | **vector-complete** | Panels use the stated sinusoidal field and time tendency, producing westward phase displacement. |
| `ch05-p132-divergent-dispersion.tikz` | 132 | **vector-complete** | Fixed-frequency solutions lie on the stated constant-`k` line with arbitrary `ell`. |
| `ch05-p132-pressure-high.tikz` | 132 | **vector-complete** | Clockwise Northern Hemisphere geostrophic flow and convergence/divergence annotations preserve the source argument. |
| `ch05-p134-general-dispersion.tikz` | 134 | **vector-complete** | Exact constant-frequency circle and long-/short-wave branches follow the nearby equation. |
| `ch05-p135-rossby-gravity-surfaces.tikz` | 135 | **vector-complete** | Surfaces are equation-generated; inertial/Rossby cutoffs follow the model rather than freehand cone placement. |
| `ch05-p137-angled-wall-reflection.tikz` | 137 | **vector-complete** | Wall and normal are perpendicular; incident/reflected group-velocity rays are mirror constructions. |
| `ch05-p138-dispersion-circle-reflection.tikz` | 138 | **vector-complete** | Incident/reflected roots preserve equal along-wall wavenumber projection; group velocities are radial normals to the frequency circle. |
| `ch05-p139-west-boundary.tikz` | 139 | **vector-complete** | Long-wave incident root maps to short-wave reflected root with the stated group-velocity reversal. |
| `ch05-p139-east-boundary.tikz` | 139 | **vector-complete** | Short-wave incident root maps to long-wave reflected root with the stated reversal. |
| `ch05-p142-hermite-modes.tikz` | 142 | **vector-complete** | Curves are generated as `exp(-xi^2/2) H_m(xi)` for `m=0..3`; parity, zeros, and lobes are exact. |
| `ch05-p145-kelvin-circulation.tikz` | 145 | **vector-complete** | Eastward equatorial Kelvin-wave path and boundary return circulation preserve the source closure. |
| `ch05-p145-equatorial-dispersion.tikz` | 145 | **vector-complete** | `m=1,2,3` gravity/Rossby branches, Yanai branch, and Kelvin branch are generated from the stated relations. |
| `ch05-p147-equatorial-ray.tikz` | 147 | **vector-complete** | Sinusoidal ray is equation-generated and its extrema coincide with the turning latitudes. |

### Chapter 6

| Asset | Printed page | Status | Scientific audit |
|---|---:|---|---|
| `ch06-p156-bottom-slope-trapping.tikz` | 156 | **vector-complete** | Preserves `omega<S` propagation and `omega>S` evanescence/reflection, including the trapped segment. |
| `ch06-p162-coastal-geometry.tikz` | 162 | **vector-complete** | Re-audited 2026-08-20: `z=-H` is now attached to the actual flat deep-ocean bottom; the lower shaded closure is distinguished from the physical bottom. Figure slightly enlarged. |
| `ch06-p164-ctw-dispersion-family.tikz` | 164 | **vector-complete** | Schematic branches obey the derived origin, ordering, and common short-wave asymptote constraints. |
| `ch06-p164-stratification-effect.tikz` | 164 | **vector-complete** | Increasing stratification raises the schematic branch toward the inertial cutoff as stated. |
| `ch06-p165-scattering-by-stratification.tikz` | 165 | **vector-complete** | Weak-stratification panel has incident/reflected/transmitted branches; strong-stratification panel omits the reflected branch. |

### Front matter

| Asset | Use | Status | Audit |
|---|---|---|---|
| `frontmatter/great-wave-met-dp130155.jpg` | modern cover | **edited-raster / provenance-complete** | Met object identification and public-domain status are recorded; artwork should remain raster rather than be vector-traced. |
| `frontmatter/salmon-hendershott-como-1980.jpeg` | modern front matter | **source photo / provenance-review-needed** | Course LXXX / Topics in Ocean Physics / July 1980 is supported. Do not assert a more specific Lake Como villa or photographer surname without photo-specific evidence. A photograph is not a vectorization candidate. |

## Direct source-PDF crop placements — complete inventory

These 56 placements are real figures even though no separate image file is committed. They are rendered directly from the source PDFs. Retaining a source crop is a positive scientific decision when vectorization would add interpretation risk; it is not an incomplete reconstruction by itself.

Chapter 5 p.97 is a particularly important example: the sphere drawing was reviewed as a vector candidate and retained as source art because the local `u/v/z` tangencies, latitude/longitude circles, point `P`, rotation axis, and projected angle geometry are exactly the sort of subtle relationships that a cleaner redraw can accidentally change.

| Chapter | Printed page | Source PDF | Physical page | Status / vectorization disposition |
|---|---:|---|---:|---|
| 2 | 23 | `ChapmanRizzoli0_2.pdf` | 33 | **source-pdf** — retained after review; no scientific need for redraw. |
| 2 | 24 | `ChapmanRizzoli0_2.pdf` | 34 | **source-pdf** — retained after review. |
| 2 | 26 | `ChapmanRizzoli0_2.pdf` | 36 | **source-pdf** — retained after review. |
| 2 | 28 | `ChapmanRizzoli0_2.pdf` | 38 | **source-pdf** — retained after review. |
| 2 | 32 | `ChapmanRizzoli0_2.pdf` | 42 | **source-pdf** — retained after review. |
| 2 | 34 | `ChapmanRizzoli0_2.pdf` | 44 | **source-pdf** — retained after review. |
| 2 | 35 | `ChapmanRizzoli0_2.pdf` | 45 | **source-pdf** — retained after review. |
| 2 | 36 | `ChapmanRizzoli0_2.pdf` | 46 | **source-pdf** — retained after review. |
| 3 | 39 | `ChapmanRizzoli3.pdf` | 3 | **source-pdf** — retained after review. |
| 3 | 42 | `ChapmanRizzoli3.pdf` | 7 | **source-pdf** — retained after review. |
| 3 | 44 | `ChapmanRizzoli3.pdf` | 9 | **source-pdf** — retained after review. |
| 3 | 52 | `ChapmanRizzoli3.pdf` | 17 | **source-pdf 1/2** — retained after review. |
| 3 | 52 | `ChapmanRizzoli3.pdf` | 17 | **source-pdf 2/2** — retained after review. |
| 3 | 55 | `ChapmanRizzoli3.pdf` | 20 | **source-pdf** — retained after review. |
| 3 | 56 | `ChapmanRizzoli3.pdf` | 21 | **source-pdf 1/2** — retained after review. |
| 3 | 56 | `ChapmanRizzoli3.pdf` | 21 | **source-pdf 2/2** — retained after review. |
| 3 | 61 | `ChapmanRizzoli3.pdf` | 26 | **source-pdf** — retained after review. |
| 3 | 62 | `ChapmanRizzoli3.pdf` | 27 | **source-pdf** — retained after review. |
| 3 | 63 | `ChapmanRizzoli3.pdf` | 28 | **source-pdf** — retained after review. |
| 4 | 69 | `ChapmanRizzoli4.pdf` | 6 | **source-pdf** — retained after review. |
| 4 | 70 | `ChapmanRizzoli4.pdf` | 7 | **source-pdf** — retained after review. |
| 4 | 72 | `ChapmanRizzoli4.pdf` | 9 | **source-pdf 1/2** — retained after review. |
| 4 | 72 | `ChapmanRizzoli4.pdf` | 9 | **source-pdf 2/2** — retained after review. |
| 4 | 73 | `ChapmanRizzoli4.pdf` | 10 | **source-pdf** — retained after review. |
| 4 | 74 | `ChapmanRizzoli4.pdf` | 11 | **source-pdf** — retained after review. |
| 4 | 75 | `ChapmanRizzoli4.pdf` | 12 | **source-pdf** — retained after review. |
| 4 | 76 | `ChapmanRizzoli4.pdf` | 13 | **source-pdf** — retained after review. |
| 4 | 77 | `ChapmanRizzoli4.pdf` | 14 | **source-pdf** — retained after review. |
| 4 | 79 | `ChapmanRizzoli4.pdf` | 16 | **source-pdf** — retained after review. |
| 4 | 80 | `ChapmanRizzoli4.pdf` | 17 | **source-pdf** — retained after review. |
| 4 | 81 | `ChapmanRizzoli4.pdf` | 18 | **source-pdf 1/2** — retained after review. |
| 4 | 81 | `ChapmanRizzoli4.pdf` | 18 | **source-pdf 2/2** — retained after review. |
| 4 | 83 | `ChapmanRizzoli4.pdf` | 20 | **source-pdf** — retained after review. |
| 4 | 84 | `ChapmanRizzoli4.pdf` | 21 | **source-pdf** — retained after review. |
| 4 | 85 | `ChapmanRizzoli4.pdf` | 22 | **source-pdf** — retained after review. |
| 4 | 88 | `ChapmanRizzoli4.pdf` | 25 | **source-pdf** — retained after review. |
| 4 | 89 | `ChapmanRizzoli4.pdf` | 26 | **source-pdf 1/2** — retained after review. |
| 4 | 89 | `ChapmanRizzoli4.pdf` | 26 | **source-pdf 2/2** — retained after review. |
| 4 | 90 | `ChapmanRizzoli4.pdf` | 27 | **source-pdf 1/2** — retained after review. |
| 4 | 90 | `ChapmanRizzoli4.pdf` | 27 | **source-pdf 2/2** — retained after review. |
| 4 | 91 | `ChapmanRizzoli4.pdf` | 28 | **source-pdf** — retained after review. |
| 4 | 92 | `ChapmanRizzoli4.pdf` | 29 | **source-pdf** — retained after review. |
| 4 | 93 | `ChapmanRizzoli4.pdf` | 30 | **source-pdf** — retained after review. |
| 4 | 94 | `ChapmanRizzoli4.pdf` | 31 | **source-pdf** — retained after review. |
| 5 | 97 | `ChapmanRizzoli5.pdf` | 2 | **source-pdf** — vectorization reviewed and deferred because the sphere/tangent/longitude-latitude geometry is scientifically dense. |
| 5 | 113 | `ChapmanRizzoli5.pdf` | 18 | **source-pdf 1/2** — historical labels retained beside corrected text; do not silently redraw the erratum away. |
| 5 | 113 | `ChapmanRizzoli5.pdf` | 18 | **source-pdf 2/2** — same disposition. |
| 6 | 151 | `ChapmanRizzoli6.pdf` | 4 | **source-pdf** — retained after review. |
| 6 | 152 | `ChapmanRizzoli6.pdf` | 5 | **source-pdf** — retained after review. |
| 6 | 154 | `ChapmanRizzoli6.pdf` | 7 | **source-pdf** — retained after review. |
| 6 | 157 | `ChapmanRizzoli6.pdf` | 10 | **source-pdf** — retained after review. |
| 6 | 159 | `ChapmanRizzoli6.pdf` | 12 | **source-pdf 1/2** — retained after review. |
| 6 | 159 | `ChapmanRizzoli6.pdf` | 12 | **source-pdf 2/2** — retained after review. |
| 6 | 161 | `ChapmanRizzoli6.pdf` | 15 | **source-pdf** — retained because the full coastal-wave spectrum combines several physical branches; vectorization would require a dedicated equation-by-equation spectrum reconstruction. |
| 6 | 167 | `ChapmanRizzoli6.pdf` | 21 | **source-pdf** — retained after review. |
| 6 | 168 | `ChapmanRizzoli6.pdf` | 22 | **source-pdf** — retained after review. |

## Sizing and acceptance rules

1. Size is part of the audit. A scientifically correct redraw should also occupy roughly the same useful page area as the source without clipping or forcing surrounding text into poor layout.
2. Prefer changing vector drawing scale/extent at the vector source so PDF and generated SVG/HTML inherit the same improvement. Avoid PDF-only sizing hacks.
3. A source crop may keep its historical aspect ratio and whitespace when that whitespace carries geometry or annotations; otherwise trim should be tightened in the chapter inclusion rather than resampling the image.
4. Arrowheads must be checked for propagation/group-velocity direction, not only placement. Equal-magnitude vectors must be constructed from equal geometry rather than estimated visually.
5. Wave crests/wavelength markers must be generated from the same wavelength parameter when a quantitative relation is implied.
6. On spherical/curvilinear figures, verify whether vectors/curves actually touch or are tangent to the intended latitude/longitude/meridian construction. Do not infer contact from a low-resolution scan.
7. For free-mode joins, enforce the stated matching conditions (for example both field and flux/transport continuity), not only positional continuity.
8. `vector-complete` does not waive later typography/page-fill review after global style changes. If a style change alters final figure scale or clipping, re-open the relevant records.

## Batch verification checklist

For every changed vector:

1. inspect the full source page at high resolution;
2. read the nearby equations/prose and list the geometric constraints;
3. encode those constraints in coordinates/equations where practical;
4. compile the TikZ independently;
5. inspect arrowheads, labels, tangencies, crossings, wavelength, amplitude ratios, and final scale;
6. compile both PDF editions and generated HTML/EPUB at the batch checkpoint;
7. compare affected pages/assets with the source;
8. record intentional schematic simplifications here.

Direct source crops use the committed PDF page through `\includegraphics[page=...,trim=...,clip]`; no permanent raster intermediary is committed.
