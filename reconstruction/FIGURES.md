# Figure audit

This live ledger records figure provenance, scientific-review decisions, and remaining work. The committed PDFs in `../source/` are the visual authority.

Statuses used here:

- `source-pdf` — untouched complex historical art built directly from a source PDF crop;
- `edited-raster` — intentionally edited raster retained as the final book image;
- `vector-complete` — accepted TikZ/vector reconstruction;
- `vector-review-needed` — vector exists but needs scientific/visual re-review;
- `vector-candidate` — source art may be suitable for future vectorization.

For vectors, the `.tikz` file contains a machine-readable `wave-source` comment with source PDF, physical page, and crop. `scripts/compare-figures.py` regenerates temporary source/reconstruction/side-by-side files under `build/comparisons/`; those files are never committed. The governing question is whether the reconstruction preserves the scientific information of the original, not how many figures can be converted to vectors.

## Chapter 1

| Printed page | Source physical page | Figure | Reconstruction | Audit note |
|---:|---:|---|---|---|
| 4 | 14 | phase planes, wavevector and wavelength geometry | **vector-complete** | phase planes are constructed exactly normal to `k`; the displayed separation is `lambda=2 pi/|k|`, the `k/ell` component geometry is consistent with the same wavevector, and equation labels are offset from construction lines |
| 8 | 18 | slowly modulated wave packet | **vector-complete** | the carrier period is exactly the displayed `2 pi/k_0` marker; the envelope, center line, `Delta x`, and `Delta x >> k_0^{-1}` relationships reproduce the source without label/curve collisions |
| 8 | 18 | narrow-band spectrum | **vector-complete** | smooth spectral amplitude is centered at `k_0` and reproduces the source's narrow-band shape; the `A(k)` and `k_0` labels remain clear of axes and the curve |
| 10 | 20 | stationary-phase integrand | **vector-complete** | the schematic uses a stationary point at `k_0`, with slow phase variation near the stationary region and increasingly rapid oscillations away from it; the integrand label and `k_0` marker are separated from the curve |
| 12 | 22 | wave-crest counting along path `Gamma` | **vector-complete** | the two `A`-to-`B` boundary paths and the family of crest lines reproduce the source's Stokes/irrotational-wavenumber argument; endpoint, path and crest labels do not overlap the geometry |
| 15 | 25 | two initial wave groups with local envelope and wavenumber | **vector-complete** | carrier periods are exactly the displayed schematic `lambda_1` and `lambda_2`, wavelength markers use those same values, and the two `k(x,0)` plateaus are proportional to `2 pi/lambda`; the numerical display wavelengths are only normalization choices used to match the source proportions |
| 16 | 26 | two wave groups following intersecting rays | **vector-complete** | the same schematic carrier wavelengths as p.15 are preserved in time; each later packet center is computed from its straight ray so the group center lies exactly on that ray, and the source-style `k=k_1`, `k=k_2`, and failure annotation are offset from dashed lines |

## Chapter 2

| Printed page | Source physical page | Figure | Reconstruction | Audit note |
|---:|---:|---|---|---|
| 21 | 31 | incident/reflected acoustic wave at `z=0` | **vector-complete** | horizontal solid boundary, `x/z` axes, incident crest planes normal to the incident propagation direction, reflected direction, and source labels are reproduced; no unintended label/line crossings were found in the 300-dpi comparison |
| 22 | 32 | specular reflection from `z=alpha x` | **vector-complete** | the wall angle is display-only, while the boundary normal is constructed exactly perpendicular to the wall and the incident/reflected wavevectors are exactly symmetric about it, enforcing `theta_i=theta_r`; the source's tangential-projection `cos` typo is corrected to `sin` and documented in `ERRATA.md` |

## Chapter 4

| Printed page | Source physical page | Figure | Reconstruction | Audit note |
|---:|---:|---|---|---|
| 65 | 2 | stratified parcel displacement | **vector-complete** | monotonic background-density profile, equilibrium point and upward parcel displacement `xi` are reproduced; the source does not specify an analytic `rho_0(z)` curve, so profile curvature is explicitly schematic |
| 68 | 5 | internal-wave boundary-value problem | **vector-complete** | free-surface condition `(sigma^2-f^2)w_z+g nabla_H^2 w=0`, Boussinesq interior wave equation and flat-bottom `w=0` condition are typeset directly from the derivation; equations sit in clear water-column whitespace |
| 69 | 6 | constant-frequency internal-wave dispersion cone | **vector-complete** | cone follows `m^2=R^2(k^2+ell^2)`, so horizontal radius is `|m|/R` and `tan(theta)=1/R`; projected `k,ell,m` axes and source angle annotation are retained without duplicate labels |
| 78 | 15 | case A dispersion intersections | **vector-complete** | normalized exact curves `LHS=C/k` and `RHS=tanh(ak)` with positive `C` produce the two symmetric real `+/-k` roots; `C=a=1` is display-only and labels were moved off the curves after standalone render audit |
| 78 | 15 | case A1 absence of propagating roots | **vector-complete** | normalized exact curves `LHS=-C/k` and `RHS=tanh(ak)` have opposite sign for every real nonzero `k`, so no real propagating roots occur; labels are separated from both curves |

## Chapter 5

| Printed page | Source physical page | Figure | Reconstruction | Audit note |
|---:|---:|---|---|---|
| 108 | 13 | reflection from vertical wall | **vector-complete** | incident/reflected directions, wall, `x/y`, and wavevector label reproduced |
| 108 | 13 | rectangular basin | **vector-complete** | four walls and `x=0,a`, `y=0,b` geometry reproduced |
| 110 | 15 | depth step + incident/reflected/transmitted rays | **vector-complete** | `D_1/D_2`, `x=0`, ray directions, and angle labels reproduced |
| 113 | 18 | shallow-side incidence and critical-angle sequence | **source-pdf** | retained because the source figure and adjacent algebra contain a substantive label/depth erratum documented in `ERRATA.md` |
| 114 | 19 | classic step shelf | **vector-complete** | coast, shelf width `L`, `D_1`, `D_2`, shelf/deep-sea labels reproduced |
| 114 | 19 | trapped and deep-sea ray paths, cases A/B | **vector-complete** | reflecting shelf ray and incident/reflected deep-sea ray geometry reproduced |
| 115 | 20 | oscillatory shelf mode with evanescent deep-ocean tail | **vector-complete** | shelf field follows the source `A cos(k_1 x)` form and joins continuously to an exponential deep-ocean tail; depth labels were re-audited and moved clear of the curve |
| 116 | 21 | edge-wave dispersion diagram | **vector-complete** | first three symmetric branches are parameterized from `tan(k_1 L)=D_2 k_2/(D_1 k_1)`; the depth ratio only sets the source schematic's opening angle, while branch cutoffs/asymptotes come from the dispersion relation; limiting-line labels are offset so lines do not cross glyphs |
| 117 | 22 | forced shelf/deep-ocean cross-shelf structure | **vector-complete** | `A cos(k_1 x)` shelf structure is joined to a longer-wavelength deep-ocean oscillation consistent with `D_2>D_1`; depth labels are clear of the wave curves |
| 118 | 23 | coastal-seiche cross-shelf modes | **vector-complete** | gravest and first higher quarter-wave shelf profiles enforce the common shelf-break elevation node; the higher mode has one additional shelf zero and both deep-ocean tails radiate schematically; no label/line collision found in the retro-audit |
| 119 | 24 | no-rotation vs rotation particle-motion sketch | **vector-complete** | phase planes are normal to `k`; the no-rotation panel now uses local straight oscillation markers parallel to `k`, while the rotating panel uses clockwise ellipses consistent with `u/v=i\sigma/f`; source-style `k,c,c_g` labels are clear of lines |
| 123 | 28 | waveguide channel boundaries | **vector-complete** | external TikZ asset reproduces both channel walls and the `v=0`, `y=0,a` labels |
| 124 | 29 | Kelvin-wave amphidromic pattern | **edited-raster** | native embedded 300-ppi CCITT page strips extracted with `pdfimages`, cropped, and rotated 0.75° counterclockwise to correct measured scan skew; only the final lossless PNG is retained |
| 125 | 30 | channel closed at one end | **vector-complete** | external TikZ asset reproduces the three closed-channel boundaries and `u=0`, `v=0`, `x=0`, `y=0,a` labels |
| 126 | 31 | Kelvin wave turning the corner | **edited-raster** | native embedded 300-ppi CCITT page strips extracted with `pdfimages`, cropped, and rotated 1.25° counterclockwise to correct measured scan skew; only the final lossless PNG is retained |
| 129 | 34 | Rossby-wave constant-frequency circle and group-velocity geometry | **vector-complete** | circle is plotted from `(k+beta/(2 sigma))^2+ell^2=(beta/(2 sigma))^2`; normalized geometry preserves `W,C,O`, `gamma`, `delta=2 gamma`, wavevector/phase direction, and southeast group-velocity direction without label-line collisions |
| 130 | 35 | westward Rossby-wave propagation mechanism | **vector-complete** | three panels use `v(x,0)=sin(kx)`, `v_t=(beta/k) cos(kx)` from `(v_x)_t+beta v=0`, and a short-time `sin+epsilon cos` update; the resulting phase displacement is explicitly westward |
| 132 | 37 | divergent planetary-wave dispersion line | **vector-complete** | fixed frequency gives the vertical line `k=-sigma f^2/(gD beta)` with arbitrary `ell`; several wavevectors terminate on the same line as in the source |
| 132 | 37 | pressure-high convergence/divergence mechanism | **vector-complete** | concentric isobars, clockwise Northern Hemisphere geostrophic flow, `H`, `A/B`, and convergence/divergence annotations are retained; the transport contrast follows the source `1/f` argument |
| 134 | 39 | general planetary-wave constant-frequency circle | **vector-complete** | exact circle from `(k+beta/(2 sigma))^2+ell^2=(beta/(2 sigma))^2+(sigma^2-f^2)/(gD)`; the normalized display enforces `r<CO` for `sigma<f`, marks the long-wave fixed-`k` limit and short/long branches, and keeps all labels clear of curves |
| 135 | 40 | first-/second-class Rossby and gravity-wave dispersion surfaces | **vector-complete** | constant-frequency sections are generated from nondimensional Rossby and gravity-wave dispersion relations rather than freehand cones; `B=beta sqrt(gD)/f^2=0.4` is display-only, while the inertial and Rossby cutoffs follow the equations; equations and center labels are offset from the surfaces |
| 137 | 42 | angled-wall Rossby reflection geometry | **vector-complete** | wall and dashed normal are exactly perpendicular; incoming and outgoing group-velocity rays are specular about the normal line, while source-style `theta_i`, `theta_r`, `mu`, wavefronts and `k,c` labels are retained without text-line collisions |
| 138 | 43 | Rossby dispersion-circle reflection construction | **vector-complete** | `I` and `R` are the two constant-frequency roots with equal along-wall wavenumber projection, so chord `IR` is normal to the wall; `C'W'` is parallel to the wall and group velocities are radial normals to the constant-frequency circle; labels are offset from construction lines |
| 139 | 44 | western-boundary Rossby limiting reflection | **vector-complete** | for `ell=0`, the incident long-wave small-`|k|` root reflects onto the short-wave large-`|k|` root; group velocity reverses from westward to eastward and labels are separated from axes/arrows |
| 139 | 44 | eastern-boundary Rossby limiting reflection | **vector-complete** | for `ell=0`, the incident short-wave large-`|k|` root reflects onto the long-wave small-`|k|` root; group velocity reverses from eastward to westward with collision-free labels |
| 142 | 47 | first four equatorial Hermite modes | **vector-complete** | curves are plotted directly as `exp(-xi^2/2) H_m(xi)` for `m=0,1,2,3`; per-panel amplitude scaling is display-only, while parity, zeros and lobe geometry are exact |
| 145 | 50 | equatorial Kelvin-wave circulation closure | **vector-complete** | eastward equatorially trapped Kelvin-wave arrows and the source's western/eastern boundary return paths are reproduced with the equator and both north-south walls; all labels are separated from boundaries/arrows |
| 145 | 50 | equatorial trapped-wave dispersion diagram | **vector-complete** | `m=1,2,3` branches are generated directly from the exact cubic `omega^3-(lambda^2+2m+1)omega-lambda=0`; the Yanai branch uses `lambda=omega-1/omega`, the `m=-1` Kelvin branch uses `omega=lambda`, and source asymptotes are exact; tightly spaced Rossby mode numbers use leader callouts to avoid text/curve collisions |
| 147 | 52 | equatorial sinusoidal ray and turning coordinates | **vector-complete** | ray follows the derived `y=A sin(bx+const)` form with `A=y_T` so every extremum reaches the turning coordinates exactly; straight beta-plane chords at `+/-y_T` replace the source globe's schematic mismatch, and `y_T` follows the dimensional correction documented in `ERRATA.md` |

## Chapter 6

| Printed page | Source physical page | Figure | Reconstruction | Audit note |
|---:|---:|---|---|---|
| 156 | 9 | bottom-slope propagation, reflection and trapping sketches | **vector-complete** | three panels preserve the source distinction `omega<S` (oscillatory propagation along the bottom) versus `omega>S` (evanescence/reflection); the final panel traps the oscillatory segment between two evanescent regions; labels were moved into clear whitespace after standalone collision audit |
| 161 | 15 | complete coastal-wave dispersion spectrum | **source-pdf** | retained for now because it combines shelf-wave, Kelvin, Poincare-continuum and edge-wave branches in one information-dense schematic; a clean redraw would require a separate full-spectrum audit rather than generic curve tracing |
| 162 | 16 | coastal-trapped-wave coordinate/topography geometry | **vector-complete** | `x` offshore, `y` alongshore and `z` vertical axes, `z=-D(x)`, `x=0,L`, and flat deep-ocean level `z=-H` reproduced; curved bottom is explicitly schematic while monotonic offshore deepening is preserved |
| 164 | 18 | general coastal-trapped-wave dispersion family | **vector-complete** | arbitrary `D(x)` has no closed-form curve, so only derived constraints are enforced: all branches start at `omega=0` at `ell=0`, remain discretely ordered, and approach the common short-wave limit `S max[D_x]`; curvature is documented as schematic and labels do not cross curves |
| 164 | 18 | effect of increasing stratification on dispersion | **vector-complete** | weak/intermediate/strong `S` branches are schematic but enforce the source physics: increasing `S` raises the branch and a sufficiently strong branch reaches the inertial cutoff `omega=1`; `S<<1` and `S increases` labels were separated after standalone render audit |
| 165 | 19 | weak- versus strong-stratification scattering | **vector-complete** | weak-`S` panel includes incident, reflected and transmitted energy arrows, while strong-`S` panel omits the reflected branch; coastline geometry and deep-ocean contours reproduce the source layout and all `p_i,p_R,p_T` labels were moved clear of arrows/contours |

## Verification standard

For every vector redraw:

1. inspect the full source page at high resolution;
2. reproduce all scientific labels and boundary/wave orientation;
3. compile the TikZ independently before accepting the change;
4. inspect labels for unintended line/curve crossings at final scale;
5. compile and inspect the full reconstruction at the batch checkpoint;
6. compare affected reconstructed pages with their source pages;
7. record any intentional geometric simplification here.

For every direct source crop, the LaTeX uses the original committed PDF page directly through `\includegraphics[page=...,trim=...,clip]`; no raster re-encoding is introduced by the source file stored in Git.
