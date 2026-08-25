# Figure audit — Chapter 6

[Back to the figure audit landing page](../FIGURES.md)

This chapter ledger contains scientific and technical figure placements only.
Entries follow printed page, figure order on the page, and component asset.

#### Figure 6.1 — sloping channel

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p151-sloping-channel.png" alt="Original source figure for Figure 6.1 — sloping channel" width="390"></td>
  <td><img src="../figures/ch06-p151-sloping-channel.svg" alt="Vector reconstruction for Figure 6.1 — sloping channel" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p151-sloping-channel.tikz`
- **Printed page:** 151
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The channel is constructed with sidewalls `y=0,L`, rigid lid `z=0`, and the planar bottom `z=-H+alpha y`; perspective depth is schematic but every boundary contact follows the stated geometry.

#### Figure 6.2 — bottom trapped mode

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p152-bottom-trapped-mode.png" alt="Original source figure for Figure 6.2 — bottom trapped mode" width="390"></td>
  <td><img src="../figures/ch06-p152-bottom-trapped-mode.svg" alt="Vector reconstruction for Figure 6.2 — bottom trapped mode" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p152-bottom-trapped-mode.tikz`
- **Printed page:** 152
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The vertical structure is generated from normalized `cosh(mu z)` with `mu^2=S^2(n^2 pi^2+k^2)`. Evaluation confirms amplitude increases monotonically toward the bottom and trapping strengthens with increasing `mu`.

#### Figure 6.3 — effective slope

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p154-effective-slope.png" alt="Original source figure for Figure 6.3 — effective slope" width="390"></td>
  <td><img src="../figures/ch06-p154-effective-slope.svg" alt="Vector reconstruction for Figure 6.3 — effective slope" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p154-effective-slope.tikz`
- **Printed page:** 154
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The scaled bottom is `z prime=R alpha x`, with `theta=atan(R alpha)` and `R alpha=S/sqrt(1-omega^2)`; tangent `k` and normal decay `m` are perpendicular.

#### Figure 6.4 — bottom slope trapping

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p156-bottom-slope-trapping.png" alt="Original source figure for Figure 6.4 — bottom slope trapping" width="390"></td>
  <td><img src="../figures/ch06-p156-bottom-slope-trapping.svg" alt="Vector reconstruction for Figure 6.4 — bottom slope trapping" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p156-bottom-slope-trapping.tikz`
- **Printed page:** 156
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** From the checked dispersion relation, for `omega<1` the sign of `k^2` is the sign of `S^2-omega^2`: propagation requires `omega<S`, while `omega>S` is evanescent. The reflection/trapping panels encode those regimes.

#### Figure 6.5 — continental shelf

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p157-continental-shelf.png" alt="Original source figure for Figure 6.5 — continental shelf" width="390"></td>
  <td><img src="../figures/ch06-p157-continental-shelf.svg" alt="Vector reconstruction for Figure 6.5 — continental shelf" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p157-continental-shelf.tikz`
- **Printed page:** 157
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The shelf profile is generated from `D=D_0 exp(2bx)` for `0<x<L` and matched to constant depth offshore; coast, shelf edge, and alongshore/offshore axes obey the chapter definition.

#### Figure 6.6 — shelf root condition

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p159-shelf-root-condition.png" alt="Original source figure for Figure 6.6 — shelf root condition" width="390"></td>
  <td><img src="../figures/ch06-p159-shelf-root-condition.svg" alt="Vector reconstruction for Figure 6.6 — shelf root condition" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p159-shelf-root-condition.tikz`
- **Printed page:** 159
- **Representation:** vector
- **Equation check:** ai-checked
- **Scientific check:** The root plot is generated from `tan(kL)=k/(ell-b)`. For normalized `(ell-b)L=-1.5`, roots are `2.1746260`, `5.0036453`, and `8.0384628`, approaching half-integer-`pi` asymptotes.

#### Figure 6.7 — source PDF crop, printed page 159

<table>
<tr><th>Original source</th></tr>
<tr>
  <td><img src="../figures/ch06-p159-modal-dispersion-source.png" alt="Original source figure for Figure 6.7" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p159-modal-dispersion-source.png`
- **Original source:** [ChapmanRizzoli6.pdf](../../references/chapman-rizzoli-1989/ChapmanRizzoli6.pdf), physical page 12
- **Representation:** source-pdf
- **Equation check:** ai-checked
- **Scientific check:** Keep the source modal dispersion diagram. Along each matched mode `tan(kL)=k/(ell-b)`, `k=k_n(ell)`; independently solved maxima preserve one maximum per branch and decreasing peak frequency with mode number. See `ERRATA.md`, printed p.159, for the source extremum issue.

#### Figure 6.8 — source PDF crop, printed page 161

<table>
<tr><th>Original source</th></tr>
<tr>
  <td><img src="../figures/ch06-p161-coastal-spectrum-source.png" alt="Original source figure for Figure 6.8" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p161-coastal-spectrum-source.png`
- **Original source:** [ChapmanRizzoli6.pdf](../../references/chapman-rizzoli-1989/ChapmanRizzoli6.pdf), physical page 15
- **Representation:** source-pdf
- **Equation check:** partial
- **Scientific check:** Keep the information-dense full coastal spectrum. The family content (one Kelvin wave, discrete shelf/edge families, Poincaré continuum, no Yanai analogue) is checked, but every detailed branch/cutoff for general `D(x)` is not independently reconstructible from the notes.

#### Figure 6.9 — coastal geometry

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p162-coastal-geometry.png" alt="Original source figure for Figure 6.9 — coastal geometry" width="390"></td>
  <td><img src="../figures/ch06-p162-coastal-geometry.svg" alt="Vector reconstruction for Figure 6.9 — coastal geometry" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p162-coastal-geometry.tikz`
- **Printed page:** 162
- **Representation:** vector
- **Equation check:** n/a
- **Scientific check:** `z=-H` is attached to the flat deep-ocean bottom; the lower shaded closure is distinguished from the physical bottom.

#### Figure 6.10 — ctw dispersion family

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p164-ctw-dispersion-family.png" alt="Original source figure for Figure 6.10 — ctw dispersion family" width="390"></td>
  <td><img src="../figures/ch06-p164-ctw-dispersion-family.svg" alt="Vector reconstruction for Figure 6.10 — ctw dispersion family" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p164-ctw-dispersion-family.tikz`
- **Printed page:** 164
- **Representation:** vector
- **Equation check:** partial
- **Scientific check:** Schematic branches obey checked origin, ordering, and common short-wave asymptote constraints, but the full branch shapes are intentionally schematic rather than independently replotted solutions.

#### Figure 6.11 — stratification effect

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p164-stratification-effect.png" alt="Original source figure for Figure 6.11 — stratification effect" width="390"></td>
  <td><img src="../figures/ch06-p164-stratification-effect.svg" alt="Vector reconstruction for Figure 6.11 — stratification effect" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p164-stratification-effect.tikz`
- **Printed page:** 164
- **Representation:** vector
- **Equation check:** partial
- **Scientific check:** Increasing stratification and the finite `omega=1` cutoff are constrained; the strong-`S` branch terminates on the cutoff. Detailed curvature remains schematic for unspecified `D(x)`.

#### Figure 6.12 — scattering by stratification

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p165-scattering-by-stratification.png" alt="Original source figure for Figure 6.12 — scattering by stratification" width="390"></td>
  <td><img src="../figures/ch06-p165-scattering-by-stratification.svg" alt="Vector reconstruction for Figure 6.12 — scattering by stratification" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p165-scattering-by-stratification.tikz`
- **Printed page:** 165
- **Representation:** vector
- **Equation check:** partial
- **Scientific check:** Weak-stratification panel has incident/reflected/transmitted branches and strong-stratification panel omits the reflected branch as required by the derived regime change; branch shapes remain schematic.

#### Figure 6.13 — mode transition

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p167-mode-transition.png" alt="Original source figure for Figure 6.13 — mode transition" width="390"></td>
  <td><img src="../figures/ch06-p167-mode-transition.svg" alt="Vector reconstruction for Figure 6.13 — mode transition" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p167-mode-transition.tikz`
- **Printed page:** 167
- **Representation:** vector
- **Equation check:** partial
- **Scientific check:** The source family layout is preserved with `ell<0` to the left, inertial line `sigma=f`, and strong-stratification Kelvin limit `omega=-S ell/(n pi)`. Intermediate coastal-trapped/shelf-wave branch shapes are schematic because no unique `D(x)` is specified. See `ERRATA.md`, printed p.167.

#### Figure 6.14 — wind forced shelf

<table>
<tr><th>Original</th><th>Vector</th></tr>
<tr>
  <td><img src="../figures/ch06-p168-wind-forced-shelf.png" alt="Original source figure for Figure 6.14 — wind forced shelf" width="390"></td>
  <td><img src="../figures/ch06-p168-wind-forced-shelf.svg" alt="Vector reconstruction for Figure 6.14 — wind forced shelf" width="390"></td>
</tr>
</table>

- **Asset:** `ch06-p168-wind-forced-shelf.tikz`
- **Printed page:** 168
- **Representation:** vector
- **Equation check:** n/a
- **Scientific check:** Coast, offshore `x`, alongshore `y`, shelf edge `x=L`, `D(x)`, and alongshelf wind-stress direction are isolated as vector geometry. The bathymetric curve is schematic and no equation-defined plotted quantity is asserted.
