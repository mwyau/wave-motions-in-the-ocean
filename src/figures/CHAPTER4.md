# Figure audit — Chapter 4

[Back to the figure audit landing page](../FIGURES.md)

This chapter ledger contains scientific and technical figure placements only.
Entries follow printed page, figure order on the page, and component asset.

#### Figure 4.1 — parcel displacement

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p065-parcel-displacement.png" alt="Original source figure for Figure 4.1 — parcel displacement" width="390"></td>
  <td><img src="../figures/ch04-p065-parcel-displacement.svg" alt="Vector reconstruction for Figure 4.1 — parcel displacement" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p065-parcel-displacement.tikz`
- **Printed page:** 65
- **Representation:** vector
- **Equation check:** n/a
- **Scientific check:** The reconstruction preserves the source parcel, monotonic density profile, and upward displacement `xi`; the crop uses the audited `545bp` lower trim and does not add an analytic density law.

#### Figure 4.2 — boundary value problem

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p068-boundary-value-problem.png" alt="Original source figure for Figure 4.2 — boundary value problem" width="390"></td>
  <td><img src="../figures/ch04-p068-boundary-value-problem.svg" alt="Vector reconstruction for Figure 4.2 — boundary value problem" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p068-boundary-value-problem.tikz`
- **Printed page:** 68
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The checked free-surface condition `(sigma^2-f^2) w_z+g nabla_H^2 w=0`, interior internal-wave equation, and bottom `w=0` condition are attached to the correct `z=0,-D` boundaries.

#### Figure 4.3 — dispersion cone

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p069-dispersion-cone.png" alt="Original source figure for Figure 4.3 — dispersion cone" width="390"></td>
  <td><img src="../figures/ch04-p069-dispersion-cone.svg" alt="Vector reconstruction for Figure 4.3 — dispersion cone" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p069-dispersion-cone.tikz`
- **Printed page:** 69
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The cone satisfies `m^2=R^2(k^2+ell^2)`; the displayed opening angle is generated from the same cone geometry rather than hard-coded.

#### Figure 4.4 — nonrotating transverse

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p069-nonrotating-transverse.png" alt="Original source figure for Figure 4.4 — nonrotating transverse" width="390"></td>
  <td><img src="../figures/ch04-p069-nonrotating-transverse.svg" alt="Vector reconstruction for Figure 4.4 — nonrotating transverse" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p069-nonrotating-transverse.tikz`
- **Printed page:** 69
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves the transverse `u`/`k` construction, `w=u sin(theta)`, and the source's displayed `u_t=-g p sin(theta)/rho_0` relation. The nearby derivation indicates the density-perturbation form would be expected; see `ERRATA.md`, printed p.69. The reconstruction preserves the source pending human review.

#### Figure 4.5 — rotating transverse

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p070-rotating-transverse.png" alt="Original source figure for Figure 4.5 — rotating transverse" width="390"></td>
  <td><img src="../figures/ch04-p070-rotating-transverse.svg" alt="Vector reconstruction for Figure 4.5 — rotating transverse" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p070-rotating-transverse.tikz`
- **Printed page:** 70
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves the transverse velocity, the `f_parallel`/`f_perp` decomposition, and both displayed rotating-transverse equations.

#### Figure 4.6 — phase energy theta

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p072-phase-energy-theta.png" alt="Original source figure for Figure 4.6 — phase energy theta" width="390"></td>
  <td><img src="../figures/ch04-p072-phase-energy-theta.svg" alt="Vector reconstruction for Figure 4.6 — phase energy theta" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p072-phase-energy-theta.tikz`
- **Printed page:** 72
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Upper `f>N` / `f<N` pair: phase direction and energy direction are perpendicular; the energy arrow reverses side as in the source. Direction limits were independently checked.

#### Figure 4.7 — phase energy phi

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p072-phase-energy-phi.png" alt="Original source figure for Figure 4.7 — phase energy phi" width="390"></td>
  <td><img src="../figures/ch04-p072-phase-energy-phi.svg" alt="Vector reconstruction for Figure 4.7 — phase energy phi" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p072-phase-energy-phi.tikz`
- **Printed page:** 72
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Lower `f>N` / `f<N` pair: `c_g` is the energy direction and phase propagation is perpendicular; the redraw excludes surrounding source prose. Direction relations were independently checked.

#### Figure 4.8 — rotation only limits

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p073-rotation-only-limits.png" alt="Original source figure for Figure 4.8 — rotation only limits" width="390"></td>
  <td><img src="../figures/ch04-p073-rotation-only-limits.svg" alt="Vector reconstruction for Figure 4.8 — rotation only limits" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p073-rotation-only-limits.tikz`
- **Printed page:** 73
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Rotation-only endpoint sketch is reconstructed from the stated limits (`phi=0` Taylor-column limit and `phi=90 deg` inertial limit), excluding surrounding prose. Both endpoint limits were checked from the chapter equations.

#### Figure 4.9 — stratification only limits

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p074-stratification-only-limits.png" alt="Original source figure for Figure 4.9 — stratification only limits" width="390"></td>
  <td><img src="../figures/ch04-p074-stratification-only-limits.svg" alt="Vector reconstruction for Figure 4.9 — stratification only limits" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p074-stratification-only-limits.tikz`
- **Printed page:** 74
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Stratification-only endpoint sketch preserves the buoyancy-oscillation and steady limits without surrounding source prose. Both endpoint limits were checked from the chapter equations.

#### Figure 4.10 — rotation stratification limits

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p075-rotation-stratification-limits.png" alt="Original source figure for Figure 4.10 — rotation stratification limits" width="390"></td>
  <td><img src="../figures/ch04-p075-rotation-stratification-limits.svg" alt="Vector reconstruction for Figure 4.10 — rotation stratification limits" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p075-rotation-stratification-limits.tikz`
- **Printed page:** 75
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Combined rotation/stratification endpoint sketch preserves the buoyancy and inertial limits and their wavenumber orientations. The limiting values were checked from the chapter equations.

#### Figure 4.11 — waveguide boundary problem

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p076-waveguide-boundary-problem.png" alt="Original source figure for Figure 4.11 — waveguide boundary problem" width="390"></td>
  <td><img src="../figures/ch04-p076-waveguide-boundary-problem.svg" alt="Vector reconstruction for Figure 4.11 — waveguide boundary problem" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p076-waveguide-boundary-problem.tikz`
- **Printed page:** 76
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Substitution confirms the internal-wave field equation and the same free-surface/bottom conditions as p.68, with labels attached to the `z=0,-D` boundaries.

#### Figure 4.12 — frequency regimes

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p077-frequency-regimes.png" alt="Original source figure for Figure 4.12 — frequency regimes" width="390"></td>
  <td><img src="../figures/ch04-p077-frequency-regimes.svg" alt="Vector reconstruction for Figure 4.12 — frequency regimes" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p077-frequency-regimes.tikz`
- **Printed page:** 77
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves both `N^2>f^2` and `N^2<f^2` sign rows, the `f`/`N` ordering, and the A, A1, B, and B1 labels used by the following case analysis.

#### Figure 4.13 — case a intersections

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p078-case-a-intersections.png" alt="Original source figure for Figure 4.13 — case a intersections" width="390"></td>
  <td><img src="../figures/ch04-p078-case-a-intersections.svg" alt="Vector reconstruction for Figure 4.13 — case a intersections" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p078-case-a-intersections.tikz`
- **Printed page:** 78
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Root solving of normalized `1/k=tanh(k)` gives `k=+/-1.1996786403`; the vector contains those two symmetric propagating intersections.

#### Figure 4.14 — case a1 no intersections

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p078-case-a1-no-intersections.png" alt="Original source figure for Figure 4.14 — case a1 no intersections" width="390"></td>
  <td><img src="../figures/ch04-p078-case-a1-no-intersections.svg" alt="Vector reconstruction for Figure 4.14 — case a1 no intersections" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p078-case-a1-no-intersections.tikz`
- **Printed page:** 78
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** For normalized `-1/k=tanh(k)`, the two sides have opposite sign for every nonzero real `k`; a sign/root check confirms no real propagating intersection.

#### Figure 4.15 — case b intersections

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p079-case-b-intersections.png" alt="Original source figure for Figure 4.15 — case b intersections" width="390"></td>
  <td><img src="../figures/ch04-p079-case-b-intersections.svg" alt="Vector reconstruction for Figure 4.15 — case b intersections" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p079-case-b-intersections.tikz`
- **Printed page:** 79
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Roots of `tan(t)+C/t=0` were independently checked for both signs of `C`; the vector retains the complete B/B1 panels, tangent asymptotes, LHS/RHS curves, and root markers.

#### Figure 4.16 — waveguide dispersion

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p080-waveguide-dispersion.png" alt="Original source figure for Figure 4.16 — waveguide dispersion" width="390"></td>
  <td><img src="../figures/ch04-p080-waveguide-dispersion.svg" alt="Vector reconstruction for Figure 4.16 — waveguide dispersion" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p080-waveguide-dispersion.tikz`
- **Printed page:** 80
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Surface and internal branches are generated from the stated approximate dispersion relations. Limiting checks give `sigma->f` as `k->0`, `sigma->N` as `k->infinity`, and vanishing group velocity at both internal-branch limits.

#### Figure 4.17 — mode structure

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p081-mode-structure.png" alt="Original source figure for Figure 4.17 — mode structure" width="390"></td>
  <td><img src="../figures/ch04-p081-mode-structure.svg" alt="Vector reconstruction for Figure 4.17 — mode structure" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p081-mode-structure.tikz`
- **Printed page:** 81
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The checked `n=1` factors `w/w_0=sin(pi(z+D)/D)` and `u/(Rw_0)=-cos(pi(z+D)/D)` set the paired profiles, boundary values, and `z=0,-D` labels.

#### Figure 4.18 — particle cells

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p081-particle-cells.png" alt="Original source figure for Figure 4.18 — particle cells" width="390"></td>
  <td><img src="../figures/ch04-p081-particle-cells.svg" alt="Vector reconstruction for Figure 4.18 — particle cells" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p081-particle-cells.tikz`
- **Printed page:** 81
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Velocity cells use the same `n=1` solution and are analytically divergence-free. Surface convergence/divergence locations and alternating circulation follow from the checked `u,w` phase relation.

#### Figure 4.19 — evanescent case a

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p083-evanescent-case-a.png" alt="Original source figure for Figure 4.19 — evanescent case a" width="390"></td>
  <td><img src="../figures/ch04-p083-evanescent-case-a.svg" alt="Vector reconstruction for Figure 4.19 — evanescent case a" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p083-evanescent-case-a.tikz`
- **Printed page:** 83
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Roots of `C/t=-tan(t)` were independently checked for both case signs; the vector retains both A/A1 panels, asymptotes, LHS/RHS curves, and all symmetric root markers.

#### Figure 4.20 — evanescent case b

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p084-evanescent-case-b.png" alt="Original source figure for Figure 4.20 — evanescent case b" width="390"></td>
  <td><img src="../figures/ch04-p084-evanescent-case-b.svg" alt="Vector reconstruction for Figure 4.20 — evanescent case b" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p084-evanescent-case-b.tikz`
- **Printed page:** 84
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** Solving `C/t=-tanh(t)` gives no real root for the positive case and the checked symmetric pair `t=+/-0.94761` for the negative case; both B/B1 panels retain that distinction.

#### Figure 4.21 — topographic generation

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p085-topographic-generation.png" alt="Original source figure for Figure 4.21 — topographic generation" width="390"></td>
  <td><img src="../figures/ch04-p085-topographic-generation.svg" alt="Vector reconstruction for Figure 4.21 — topographic generation" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p085-topographic-generation.tikz`
- **Printed page:** 85
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves the stippled `h=h_0 sin(kx)` topography, mean flow `U`, and local `x,z` axes; the nearby forcing and radiation equations constrain the schematic.

#### Figure 4.22 — characteristics

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p088-characteristics.png" alt="Original source figure for Figure 4.22 — characteristics" width="390"></td>
  <td><img src="../figures/ch04-p088-characteristics.svg" alt="Vector reconstruction for Figure 4.22 — characteristics" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p088-characteristics.tikz`
- **Printed page:** 88
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves the two characteristic slopes `dz/dx=+/-1/R`, their parallel phase lines, phase arrows, and the sign labels for `x-Rz=0` and `x+Rz=0`.

#### Figure 4.23 — slope reflection

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p089-slope-reflection.png" alt="Original source figure for Figure 4.23 — slope reflection" width="390"></td>
  <td><img src="../figures/ch04-p089-slope-reflection.svg" alt="Vector reconstruction for Figure 4.23 — slope reflection" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p089-slope-reflection.tikz`
- **Printed page:** 89
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vector preserves the two characteristic lines, incident/reflected energy directions, and paired wavevector directions used to show non-specular reflection.

#### Figure 4.24 — wavenumber projection

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p089-wavenumber-projection.png" alt="Original source figure for Figure 4.24 — wavenumber projection" width="390"></td>
  <td><img src="../figures/ch04-p089-wavenumber-projection.svg" alt="Vector reconstruction for Figure 4.24 — wavenumber projection" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p089-wavenumber-projection.tikz`
- **Printed page:** 89
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** With `k_i=(1,R)` and `q=(1+aR)/(1-aR)`, the vector preserves the sloping wall, characteristic directions, incident/reflected wavevectors, and equal-projection angle construction.

#### Figure 4.25 — wavenumber triangle

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p090-wavenumber-triangle.png" alt="Original source figure for Figure 4.25 — wavenumber triangle" width="390"></td>
  <td><img src="../figures/ch04-p090-wavenumber-triangle.svg" alt="Vector reconstruction for Figure 4.25 — wavenumber triangle" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p090-wavenumber-triangle.tikz`
- **Printed page:** 90
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The revised subcritical construction uses common `R=1.25`, `a=0.32`; directions are `+/-atan(R)` and arrow lengths use `q=(1+aR)/(1-aR)=2.333333`. It makes no supercritical magnitude claim. See `ERRATA.md`, printed p.90.

#### Figure 4.26 — velocity reflection

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p090-velocity-reflection.png" alt="Original source figure for Figure 4.26 — velocity reflection" width="390"></td>
  <td><img src="../figures/ch04-p090-velocity-reflection.svg" alt="Vector reconstruction for Figure 4.26 — velocity reflection" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p090-velocity-reflection.tikz`
- **Printed page:** 90
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The source-traced construction preserves `v_i`, `v_r`, the `x+Rz=0` and `x-Rz=0` characteristic lines, the sloping wall, the normal, angle marks, labels, and arrow directions. It does not replace the pending source convention with a derived formula; see `ERRATA.md`, printed p.90.

#### Figure 4.27 — source PDF crop, printed page 91

<table>
<tr><th>Original source</th></tr>
<tr>
  <td><img src="../figures/ch04-p091-slope-reflection-source.png" alt="Original source figure for Figure 4.27" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p091-slope-reflection-source.png`
- **Original source:** [ChapmanRizzoli4.pdf](../../references/chapman-rizzoli-1989/ChapmanRizzoli4.pdf), physical page 28
- **Representation:** source-pdf
- **Equation check:** partial
- **Scientific check:** Keep the multi-slope reflection sketch because the signed-versus-magnitude convention remains ambiguous for the full displayed regime. See `ERRATA.md`, printed p.90.

#### Figure 4.28 — density profiles

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p092-density-profiles.png" alt="Original source figure for Figure 4.28 — density profiles" width="390"></td>
  <td><img src="../figures/ch04-p092-density-profiles.svg" alt="Vector reconstruction for Figure 4.28 — density profiles" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p092-density-profiles.tikz`
- **Printed page:** 92
- **Original source:** [ChapmanRizzoli4.pdf](../../references/chapman-rizzoli-1989/ChapmanRizzoli4.pdf), physical page 29
- **Representation:** vector
- **Equation check:** n/a
- **Scientific check:** The source-traced empirical curves preserve the printed typical density and `N(z)` profiles, depth ticks, and the 10-minute, 20–30-minute, and 2–3-hour labels without inventing an analytic fit.

#### Figure 4.29 — turning profile

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p093-turning-profile.png" alt="Original source figure for Figure 4.29 — turning profile" width="390"></td>
  <td><img src="../figures/ch04-p093-turning-profile.svg" alt="Vector reconstruction for Figure 4.29 — turning profile" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p093-turning-profile.tikz`
- **Printed page:** 93
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The source-traced asymmetric curve preserves the two crossings, dashed turning-level guides, exponential outer regions, oscillating interior, signs, and source labels; it does not impose a symmetric parabola.

#### Figure 4.30 — eigenvalue spectrum

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch04-p094-eigenvalue-spectrum.png" alt="Original source figure for Figure 4.30 — eigenvalue spectrum" width="390"></td>
  <td><img src="../figures/ch04-p094-eigenvalue-spectrum.svg" alt="Vector reconstruction for Figure 4.30 — eigenvalue spectrum" width="390"></td>
</tr>
</table>

- **Asset:** `ch04-p094-eigenvalue-spectrum.tikz`
- **Printed page:** 94
- **Representation:** vector
- **Equation check:** partial
- **Scientific check:** The source-traced panels preserve the sign-changing `R^2(z)` profile, turning-level guides, outer evanescent wiggles, broad evanescent mode, and multi-lobed travelling mode; the curves remain schematic rather than analytic fits.
