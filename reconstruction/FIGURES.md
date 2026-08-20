# Figure audit

This file tracks figures used in the reconstructed book. The PDFs in `../source/` are the visual and scientific reference. A figure is not accepted merely because it looks cleaner: direction, magnitude relationships, wavelength, nodes, tangencies, boundary contact, coordinate orientation, and consistency with the nearby equations must also survive review.

Statuses:

- `source-pdf` — untouched crop from a source PDF;
- `edited-raster` — edited raster retained as the final book image;
- `vector-complete` — TikZ/vector reconstruction rechecked against source and nearby physics;
- `vector-review-needed` — vector exists but an identified issue still needs resolution;
- `vector-candidate` — a source crop may be worth redrawing later.

Equation-validation states are tracked independently of representation status:

- **Validated** — materially equation-constrained content has been independently checked against the governing equation(s), analytically or numerically as appropriate. A historical source mismatch may still be `Validated` when the mismatch itself has been checked and documented in `ERRATA.md`.
- **Partial** — some equation-constrained content has been independently checked, but another material part remains schematic or lacks a direct equation check.
- **Pending** — equation validation materially applies but has not yet been independently completed and recorded.
- **N/A** — no meaningful equation-defined quantity or relation controls the figure; visual, geometric, source-fidelity, and provenance checks still apply.

The initial 2026-08-20 backfill is conservative: `Validated` is used only where the existing audit record supports an independent equation/constraint check, not merely because a vector was generated from a formula. Current snapshot across the 105 tracked body/front-matter assets and direct source placements: **35 Validated, 6 Partial, 51 Pending, 13 N/A**.

Every `.tikz` file carries a `wave-source` comment naming the source PDF, physical page, and crop. `scripts/compare-figures.py` regenerates temporary side-by-side comparisons under `build/comparisons/`; comparison outputs are never committed.

## Committed figure assets — image-by-image audit

### Chapter 1

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch01-p004-phase-speed.tikz` | 4 | **vector-complete** | **Pending** | Phase planes are normal to `k`; component geometry and displayed wavelength are mutually consistent. |
| `ch01-p008-spectrum.tikz` | 8 | **vector-complete** | **N/A** | Narrow-band spectrum is centered at `k_0`; labels do not obscure the curve. |
| `ch01-p008-wave-packet.tikz` | 8 | **vector-complete** | **Pending** | Carrier wavelength matches the marked `2 pi/k_0`; envelope and scale annotations are consistent. |
| `ch01-p010-stationary-phase.tikz` | 10 | **vector-complete** | **Pending** | Stationary region is at `k_0`; oscillations become progressively faster away from it. |
| `ch01-p012-wave-crest-path.tikz` | 12 | **vector-complete** | **Pending** | Crest family and the two A-to-B paths preserve the circulation/wavenumber argument. |
| `ch01-p015-initial-wave-groups.tikz` | 15 | **vector-complete** | **Pending** | Display wavelengths and local `k` plateaus use the same normalization. |
| `ch01-p016-ray-crossing.tikz` | 16 | **vector-complete** | **Pending** | Packet centers lie on their rays and preserve the p.15 carrier wavelengths. |

Chapter 1 has no direct source-PDF crop placements in the book body.

### Chapter 2

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch02-p021-solid-boundary-reflection.tikz` | 21 | **vector-complete** | **Pending** | Boundary, incident crest orientation, and reflected propagation are source-faithful. |
| `ch02-p022-specular-reflection.tikz` | 22 | **vector-complete** | **Pending** | Boundary normal is exactly perpendicular to the wall and incident/reflected `k` are exact mirrors, enforcing equal angles. |
| `ch02-p023-waveguide-boundary-problem.tikz` | 23 | **vector-complete** | **Validated** | The channel walls are at `z=0,-D` with `p_z=0`; independently substituting `P=cos(n pi z/D)` gives zero normal derivative at both walls for integer `n` and satisfies the separated acoustic field equation. Wall thickness is schematic. |
| `ch02-p024-waveguide-dispersion.tikz` | 24 | **vector-complete** | **Validated** | Branches are generated from normalized `S_n=sqrt(K^2+n^2)`. Independent evaluation confirms the `n=0` linear branch, `n=1,2` cutoffs at `S=1,2`, branch ordering, and common large-`K` slope. |
| `ch02-p026-interface-scattering.tikz` | 26 | **vector-complete** | **Validated** | Incident/reflected rays are exact mirrors about the interface normal. For the declared illustrative ratio `c_2/c_1=1.25`, the transmitted angle is independently calculated from Snell’s law; ray lengths remain schematic. |
| `ch02-p028-total-internal-reflection.tikz` | 28 | **vector-complete** | **Validated** | With the declared illustrative `c_1/c_2=0.75`, independent calculation gives `theta_Ic=48.590 deg`; the subcritical transmitted ray satisfies Snell’s law, the critical ray is tangent to the interface, and the supercritical panel has no propagating transmitted ray. |
| `ch02-p032-forced-source-jump.tikz` | 32 | **vector-complete** | **Validated** | Independently integrating the delta-forced one-dimensional wave equation across `x=0` gives `p_x^R-p_x^L=-q_t`; each side obeys the homogeneous acoustic wave equation. |
| `ch02-p036-sound-ray-turning.tikz` | 36 | **vector-complete** | **Validated** | For `c(z)` increasing upward, `k` remains fixed while `m` decreases. The ray is generated from `dz/dx=m/k=sqrt(sigma^2/(c^2 k^2)-1)` and independently checked to approach a horizontal tangent as `m` tends to zero; normalized display values are schematic. |

### Chapter 3

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch03-p039-surface-boundaries.tikz` | 39 | **vector-complete** | **Validated** | Free surface `z=eta` near `z=0` and rigid bottom `z=-D` are preserved; the adjacent kinematic/dynamic conditions and bottom no-normal-flow condition were checked against the reconstructed derivation. Surface waviness is schematic. |
| `ch03-p042-surface-wave-dispersion.tikz` | 42 | **vector-complete** | **Validated** | The curve is generated from normalized `S=sqrt(K tanh K)`. Independent limiting checks recover `S~K` for `K<<1` and `S~sqrt(K)` for `K>>1`, with positive monotone branch and correct asymptotic ordering. |
| `ch03-p044-two-fluid-interface.tikz` | 44 | **vector-complete** | **Validated** | Two semi-infinite potential-flow regions meet at `z=eta` near `z=0`; `nabla^2 phi_1=nabla^2 phi_2=0` and the common interface geometry match the independently checked decay and matching construction. Interface waviness is schematic. |
| `ch03-p052-delta-snapshot.tikz` | 52 | **vector-complete** | **Validated** | Snapshot is generated directly from `eta proportional to t x^(-3/2) cos(g t^2/(4x)+pi/4)` at fixed `t`; independent differentiation of the phase confirms local wavelength grows with `x`, while the explicit envelope decays as `x^(-3/2)`. |
| `ch03-p052-delta-wavestaff.tikz` | 52 | **vector-complete** | **Validated** | Fixed-position record is generated from the same asymptotic solution: amplitude envelope grows linearly in `t` and instantaneous frequency grows in magnitude with `t`, so oscillations tighten while the envelope expands. |

### Chapter 4

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch04-p065-parcel-displacement.tikz` | 65 | **vector-complete** | **N/A** | Background-density profile, equilibrium location, and upward displacement `xi` are preserved; curvature is schematic. |
| `ch04-p068-boundary-value-problem.tikz` | 68 | **vector-complete** | **Pending** | Free-surface, interior, and bottom boundary conditions follow the adjacent derivation. |
| `ch04-p069-dispersion-cone.tikz` | 69 | **vector-complete** | **Pending** | Cone satisfies `m^2=R^2(k^2+ell^2)` and the projected axes/angle are consistent. |
| `ch04-p069-nonrotating-transverse.tikz` | 69 | **vector-complete** | **Pending** | Replaces a crop that also contained the following displayed equation. The redraw keeps `u` perpendicular to `k`, the source angle, and `w=u sin(theta)` without duplicated surrounding text. |
| `ch04-p070-rotating-transverse.tikz` | 70 | **vector-complete** | **Pending** | Replaces a crop that extended into the following algebra. `f` is decomposed into components parallel/perpendicular to `k`; `u` remains transverse and the source `k-hat-prime` direction is retained. |
| `ch04-p072-phase-energy-theta.tikz` | 72 | **vector-complete** | **Validated** | Upper `f>N` / `f<N` pair: phase direction and energy direction are perpendicular; the energy arrow reverses side exactly as in the source. The phase/group-direction limits were independently checked from the chapter relations during the 2026-08-20 redraw. |
| `ch04-p072-phase-energy-phi.tikz` | 72 | **vector-complete** | **Validated** | Lower `f>N` / `f<N` pair: `c_g` is the energy direction and phase propagation is perpendicular; replacing the crop prevents the first prose line below the source drawing from entering the figure. The direction relation was independently checked during the redraw. |
| `ch04-p073-rotation-only-limits.tikz` | 73 | **vector-complete** | **Validated** | Rotation-only endpoint sketch is reconstructed from the stated limits (`phi=0` Taylor-column limit and `phi=90 deg` inertial limit), excluding the duplicated equation above and prose below. Both endpoint limits were independently checked from the chapter equations. |
| `ch04-p074-stratification-only-limits.tikz` | 74 | **vector-complete** | **Validated** | Stratification-only endpoint sketch preserves the buoyancy-oscillation and steady limits without surrounding source prose. Both endpoint limits were independently checked from the chapter equations. |
| `ch04-p075-rotation-stratification-limits.tikz` | 75 | **vector-complete** | **Validated** | Combined rotation/stratification endpoint sketch preserves the buoyancy and inertial limits and their wavenumber orientations. The limiting values were independently checked from the chapter equations. |
| `ch04-p076-waveguide-boundary-problem.tikz` | 76 | **vector-complete** | **Pending** | Replaces an over-tall crop. The free-surface condition, interior field equation, flat-bottom `w=0`, and `z=0,-D` boundaries are isolated vector content with no section text and no clipped lower annotation. |
| `ch04-p078-case-a-intersections.tikz` | 78 | **vector-complete** | **Pending** | Curves use the stated normalized equations and yield the two symmetric real roots. A fresh independent reference-curve/root check is still required under the explicit equation-audit standard. |
| `ch04-p078-case-a1-no-intersections.tikz` | 78 | **vector-complete** | **Pending** | Curves have opposite sign for every nonzero real `k`, so no propagating real root is implied. A fresh independent reference-curve/sign check is still required under the explicit equation-audit standard. |

### Chapter 5

Chapter 5 was re-audited first on 2026-08-20. Four previously accepted drawings required scientific geometry corrections; those corrections are now encoded in the vector construction rather than left to visual approximation.

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch05-p108-wall-reflection.tikz` | 108 | **vector-complete** | **Validated** | Re-audited 2026-08-20: reflected endpoint is the exact mirror of the incident endpoint about the wall normal, so `alpha_R=alpha_I` and displayed ray magnitudes are equal. The mirror/equal-angle constraint was independently checked. Enlarged from the earlier undersized redraw. |
| `ch05-p108-rectangular-basin.tikz` | 108 | **vector-complete** | **N/A** | Four walls and `x=0,a`, `y=0,b` geometry reproduce the source. |
| `ch05-p110-depth-step-rays.tikz` | 110 | **vector-complete** | **Partial** | Re-audited 2026-08-20: reflected ray is an exact mirror of the incident ray and that equal-angle constraint was checked; transmitted ray remains schematic rather than a quantitative Snell-law construction, though it bends toward the normal for the stated depth ordering. Figure scale increased. |
| `ch05-p114-step-shelf.tikz` | 114 | **vector-complete** | **N/A** | Coast, shelf width `L`, and `D_1/D_2` step geometry reproduce the source. |
| `ch05-p114-ray-paths.tikz` | 114 | **vector-complete** | **Partial** | Re-audited 2026-08-20: coast and shelf-edge bounces are built from checked mirrored ray segments; source arrow traversal is preserved; refraction at `x=L` remains schematic rather than a quantitative Snell construction. |
| `ch05-p115-edge-wave-profile.tikz` | 115 | **vector-complete** | **Validated** | Re-audited 2026-08-20: shelf cosine and offshore exponential were independently evaluated and satisfy both `eta` continuity and `D eta_x` continuity at `x=L`; display-only parameters are identified in comments and are not presented as source data. Figure enlarged. |
| `ch05-p116-edge-wave-dispersion.tikz` | 116 | **vector-complete** | **Validated** | First three branches are generated from the stated matching relation; branch cutoffs/asymptotes were checked against the dispersion relation in the Chapter 5 audit. |
| `ch05-p117-forced-shelf-profile.tikz` | 117 | **vector-complete** | **Partial** | Preserves `A cos(k_1 x)` on the shelf and a longer-wavelength deep-ocean oscillation; the shelf dependence is equation-constrained, but the deep-ocean portion remains a qualitative forced-profile sketch rather than a fully equation-matched free mode. |
| `ch05-p118-coastal-seiche-modes.tikz` | 118 | **vector-complete** | **Validated** | Both modes have the common shelf-break elevation node; the higher mode adds one shelf zero as required, checked against the modal conditions in the Chapter 5 audit. |
| `ch05-p119-particle-motion.tikz` | 119 | **vector-complete** | **Validated** | Phase planes are normal to `k`; no-rotation displacement is parallel to `k`, while rotating trajectories are clockwise ellipses checked against `u/v=i sigma/f`. |
| `ch05-p123-waveguide-channel.tikz` | 123 | **vector-complete** | **N/A** | Two channel walls and `v=0`, `y=0,a` labels reproduce the source geometry. |
| `ch05-p124-amphidromic-pattern.png` | 124 | **edited-raster** | **Pending** | Native 300-ppi CCITT source art is cropped to the figure band and deskewed losslessly; no surrounding page prose is intended in the retained raster. Its field pattern has not yet been independently checked against the superposed Kelvin-wave solution and amphidromic geometry. A future vector version must use that solution rather than tracing the scan. |
| `ch05-p125-closed-channel.tikz` | 125 | **vector-complete** | **N/A** | Three closed-channel boundaries and `u=0`, `v=0`, `x=0`, `y=0,a` labels are preserved. |
| `ch05-p126-kelvin-turning-corner.png` | 126 | **edited-raster** | **Pending** | Native 300-ppi CCITT source art is cropped to the figure band and deskewed losslessly; no surrounding page prose is intended in the retained raster. The near-corner field has not yet been independently checked against the Kelvin-plus-Poincare boundary-value solution; any vectorization must start from that solution rather than a freehand trace. |
| `ch05-p129-rossby-cg.tikz` | 129 | **vector-complete** | **Validated** | Constant-frequency circle and group-velocity normal direction were checked against the stated Rossby relation. |
| `ch05-p130-westward-propagation.tikz` | 130 | **vector-complete** | **Validated** | Panels were checked against the stated sinusoidal field and time tendency, producing westward phase displacement. |
| `ch05-p132-divergent-dispersion.tikz` | 132 | **vector-complete** | **Validated** | Fixed-frequency solutions were checked against the stated dispersion relation and lie on the constant-`k` line with arbitrary `ell`. |
| `ch05-p132-pressure-high.tikz` | 132 | **vector-complete** | **Pending** | Clockwise Northern Hemisphere geostrophic flow and convergence/divergence annotations preserve the source argument, but a fresh explicit equation audit of the displayed tendency/flow relation has not yet been recorded. |
| `ch05-p134-general-dispersion.tikz` | 134 | **vector-complete** | **Validated** | Constant-frequency circle and long-/short-wave branches were checked against the nearby equation. |
| `ch05-p135-rossby-gravity-surfaces.tikz` | 135 | **vector-complete** | **Validated** | Surfaces and inertial/Rossby cutoffs were checked against the model relations rather than accepted from freehand cone placement. |
| `ch05-p137-angled-wall-reflection.tikz` | 137 | **vector-complete** | **Validated** | Wall/normal perpendicularity and incident/reflected group-velocity mirror geometry were checked against the reflection constraint. |
| `ch05-p138-dispersion-circle-reflection.tikz` | 138 | **vector-complete** | **Validated** | Incident/reflected roots and radial group velocities were checked against the constant-frequency circle and equal along-wall wavenumber projection. |
| `ch05-p139-west-boundary.tikz` | 139 | **vector-complete** | **Validated** | Long-wave incident and short-wave reflected roots, including the group-velocity reversal, were checked against the dispersion geometry. |
| `ch05-p139-east-boundary.tikz` | 139 | **vector-complete** | **Validated** | Short-wave incident and long-wave reflected roots, including the group-velocity reversal, were checked against the dispersion geometry. |
| `ch05-p142-hermite-modes.tikz` | 142 | **vector-complete** | **Validated** | Curves were checked as `exp(-xi^2/2) H_m(xi)` for `m=0..3`; parity, zeros, and lobes are exact. |
| `ch05-p145-kelvin-circulation.tikz` | 145 | **vector-complete** | **N/A** | Eastward equatorial Kelvin-wave path and boundary return circulation preserve the source closure; this is a directional schematic rather than an equation-defined plotted quantity. |
| `ch05-p145-equatorial-dispersion.tikz` | 145 | **vector-complete** | **Validated** | `m=1,2,3` gravity/Rossby branches, Yanai branch, and Kelvin branch were checked against the stated dispersion relations. |
| `ch05-p147-equatorial-ray.tikz` | 147 | **vector-complete** | **Validated** | Sinusoidal ray and its extrema were checked against the equation-defined turning latitudes. |

### Chapter 6

| Asset | Printed page | Status | Equation validation | Scientific audit |
|---|---:|---|---|---|
| `ch06-p156-bottom-slope-trapping.tikz` | 156 | **vector-complete** | **Pending** | Preserves `omega<S` propagation and `omega>S` evanescence/reflection, including the trapped segment. A fresh independent check against the governing slope-wave criterion is still required under the explicit equation-audit standard. |
| `ch06-p162-coastal-geometry.tikz` | 162 | **vector-complete** | **N/A** | Re-audited 2026-08-20: `z=-H` is now attached to the actual flat deep-ocean bottom; the lower shaded closure is distinguished from the physical bottom. Figure slightly enlarged. |
| `ch06-p164-ctw-dispersion-family.tikz` | 164 | **vector-complete** | **Partial** | Schematic branches obey checked derived origin, ordering, and common short-wave asymptote constraints, but the full branch shapes are intentionally schematic rather than independently replotted solutions. |
| `ch06-p164-stratification-effect.tikz` | 164 | **vector-complete** | **Partial** | Increasing stratification raises the schematic branch toward the inertial cutoff as stated; the qualitative trend is checked, but the branch is not a full equation-generated solution. |
| `ch06-p165-scattering-by-stratification.tikz` | 165 | **vector-complete** | **Partial** | Weak-stratification panel has incident/reflected/transmitted branches and strong-stratification panel omits the reflected branch as required by the derived regime change; branch shapes remain schematic. |

### Front matter

| Asset | Use | Status | Equation validation | Audit |
|---|---|---|---|---|
| `frontmatter/great-wave-met-dp130155.jpg` | modern cover | **edited-raster / provenance-complete** | **N/A** | Met object identification and public-domain status are recorded; artwork should remain raster rather than be vector-traced. |
| `frontmatter/salmon-hendershott-como-1980.jpeg` | modern front matter | **source photo / provenance-review-needed** | **N/A** | Course LXXX / Topics in Ocean Physics / July 1980 is supported. Do not assert a more specific Lake Como villa or photographer surname without photo-specific evidence. A photograph is not a vectorization candidate. |

## Direct source-PDF crop placements — complete inventory

These 37 placements are real figures even though no separate image file is committed. They are rendered directly from the source PDFs. Retaining a source crop is a positive scientific decision when vectorization would add interpretation risk; it is not an incomplete reconstruction by itself.

The 2026-08-20 source-art pass also treats crop isolation as part of acceptance: surrounding prose/equations must not be embedded in a figure, and no scientific label or line may be cut by the trim. Eight Chapter 4 crops (printed pp. 69--76) failed or were unnecessarily fragile under that criterion and were replaced by isolated vectors. The remaining direct crops below are classified explicitly as vector candidates or deliberate source-art retentions.

Chapter 5 p.97 is a particularly important example: the sphere drawing was reviewed as a vector candidate and retained as source art because the local `u/v/z` tangencies, latitude/longitude circles, point `P`, rotation axis, and projected angle geometry are exactly the sort of subtle relationships that a cleaner redraw can accidentally change.

| Chapter | Printed page | Source PDF | Physical page | Equation validation | Status / vectorization disposition |
|---|---:|---|---:|---|---|
| 2 | 34 | `ChapmanRizzoli0_2.pdf` | 44 | **N/A** | **source-pdf** — retain the source-specific sound-speed profile; generic smoothing would invent profile detail. |
| 2 | 35 | `ChapmanRizzoli0_2.pdf` | 45 | **N/A** | **source-pdf** — retain the source-specific sound-speed profile; generic smoothing would invent profile detail. The p.35 crop was already tightened specifically to exclude duplicated prose. |
| 3 | 55 | `ChapmanRizzoli3.pdf` | 20 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 3 | 56 | `ChapmanRizzoli3.pdf` | 21 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 3 | 56 | `ChapmanRizzoli3.pdf` | 21 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 3 | 61 | `ChapmanRizzoli3.pdf` | 26 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 3 | 62 | `ChapmanRizzoli3.pdf` | 27 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 3 | 63 | `ChapmanRizzoli3.pdf` | 28 | **Pending** | **vector-candidate** — analytic surface-wave geometry or equation-defined schematic; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 4 | 77 | `ChapmanRizzoli4.pdf` | 14 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 79 | `ChapmanRizzoli4.pdf` | 16 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 80 | `ChapmanRizzoli4.pdf` | 17 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 81 | `ChapmanRizzoli4.pdf` | 18 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 81 | `ChapmanRizzoli4.pdf` | 18 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 83 | `ChapmanRizzoli4.pdf` | 20 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 84 | `ChapmanRizzoli4.pdf` | 21 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 85 | `ChapmanRizzoli4.pdf` | 22 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 88 | `ChapmanRizzoli4.pdf` | 25 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 89 | `ChapmanRizzoli4.pdf` | 26 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 89 | `ChapmanRizzoli4.pdf` | 26 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 90 | `ChapmanRizzoli4.pdf` | 27 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 90 | `ChapmanRizzoli4.pdf` | 27 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 91 | `ChapmanRizzoli4.pdf` | 28 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 92 | `ChapmanRizzoli4.pdf` | 29 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 93 | `ChapmanRizzoli4.pdf` | 30 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 4 | 94 | `ChapmanRizzoli4.pdf` | 31 | **Pending** | **vector-candidate** — analytic internal-wave diagram/dispersion sketch; suitable for equation- or geometry-driven TikZ; source crop remains authoritative until replacement is compared. |
| 5 | 97 | `ChapmanRizzoli5.pdf` | 2 | **N/A** | **vector-candidate (high-risk)** — feasible only with exact spherical projection/tangency construction for longitude/latitude circles and local `u/v/z`; keep source art until then. Its acceptance is primarily geometric rather than an equation-defined plot audit. |
| 5 | 113 | `ChapmanRizzoli5.pdf` | 18 | **Validated** | **source-pdf** — retain the historical labels because this figure participates in the documented source erratum; the disagreement with the nearby equations has been checked and is intentionally preserved as historical evidence. |
| 5 | 113 | `ChapmanRizzoli5.pdf` | 18 | **Validated** | **source-pdf** — same disposition; the source/equation mismatch is documented rather than silently corrected in the historical art. |
| 6 | 151 | `ChapmanRizzoli6.pdf` | 4 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 152 | `ChapmanRizzoli6.pdf` | 5 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 154 | `ChapmanRizzoli6.pdf` | 7 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 157 | `ChapmanRizzoli6.pdf` | 10 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 159 | `ChapmanRizzoli6.pdf` | 12 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 159 | `ChapmanRizzoli6.pdf` | 12 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 161 | `ChapmanRizzoli6.pdf` | 15 | **Pending** | **source-pdf** — retain the information-dense full coastal-wave spectrum until every branch/cutoff is independently checked and reconstructed equation-by-equation. |
| 6 | 167 | `ChapmanRizzoli6.pdf` | 21 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |
| 6 | 168 | `ChapmanRizzoli6.pdf` | 22 | **Pending** | **vector-candidate** — analytic topographic/coastal-wave geometry or dispersion sketch; suitable for a constrained redraw; source crop remains authoritative until replacement is compared. |

## Sizing and acceptance rules

1. Size is part of the audit. A scientifically correct redraw should also occupy roughly the same useful page area as the source without clipping or forcing surrounding text into poor layout.
2. Prefer changing vector drawing scale/extent at the vector source so PDF and generated SVG/HTML inherit the same improvement. Avoid PDF-only sizing hacks.
3. A source crop may keep its historical aspect ratio and whitespace when that whitespace carries geometry or annotations; otherwise trim should be tightened in the chapter inclusion rather than resampling the image.
4. Arrowheads must be checked for propagation/group-velocity direction, not only placement. Equal-magnitude vectors must be constructed from equal geometry rather than estimated visually.
5. Wave crests/wavelength markers must be generated from the same wavelength parameter when a quantitative relation is implied.
6. On spherical/curvilinear figures, verify whether vectors/curves actually touch or are tangent to the intended latitude/longitude/meridian construction. Do not infer contact from a low-resolution scan.
7. For free-mode joins, enforce the stated matching conditions (for example both field and flux/transport continuity), not only positional continuity.
8. `vector-complete` does not waive later typography/page-fill review after global style changes. If a style change alters final figure scale or clipping, re-open the relevant records.
9. Representation status and equation-validation status are independent. A `vector-complete` figure may remain `Pending` for equation validation, and a retained historical `source-pdf` may be `Validated` even when it intentionally preserves a documented source error.

## Batch verification checklist

For every changed vector:

1. inspect the full source page at high resolution;
2. read the nearby equations/prose and list the geometric constraints;
3. identify which equation-defined quantities materially control the figure, if any;
4. encode those constraints in coordinates/equations where practical;
5. for equation-defined charts or curves, independently evaluate or plot the stated equation when practical and compare it to the vector reconstruction;
6. for equation-constrained geometry, independently calculate the relevant angles, ratios, intersections, boundary values, continuity conditions, or vector directions rather than checking only by eye;
7. compile the TikZ independently;
8. inspect arrowheads, labels, tangencies, crossings, wavelength, amplitude ratios, and final scale;
9. compile both PDF editions and generated HTML/EPUB at the batch checkpoint;
10. compare affected pages/assets with the source;
11. record intentional schematic simplifications and the explicit `Equation validation` state here.

Direct source crops use the committed PDF page through `\includegraphics[page=...,trim=...,clip]`; no permanent raster intermediary is committed.
