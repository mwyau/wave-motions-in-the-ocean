# Errata and editorial deviations

This file records substantive differences between the historical source scans and the shared reconstructed content. It is not an audit-coverage ledger.

For new items use this metadata explicitly:

- **Category:** `transcription`, `typographical`, `equation`, `figure`, `reference`, or `editorial`
- **Status:** `pending-review`, `accepted`, or `reverted`
- **Location:** source PDF/physical page and/or printed page/chapter
- **Original:** the historical form
- **Reconstruction:** the current form
- **Reason/evidence:** enough detail to review the decision independently

The legacy entries below predate this compact schema but contain their location, original/reconstructed forms, and reasoning. Unless an entry itself says the point is ambiguous or under review, it represents an **accepted** reconstruction correction. Future edits should add explicit category/status metadata rather than creating a second audit ledger.

This file records discrepancies in the 1989 source scans that matter to a faithful technical reconstruction. The scan remains the historical source; corrected forms are used in the reconstructed mathematics or prose only when the correction is independently verifiable.

## Chapter 1

### Printed page 5 - direction dependence of vector advection

The source states that for cases (a)--(d) in its example table, the phase speed

```math
c=\sigma/|\vec{k}|
```

is independent of wavelength, frequency **or direction**. That is correct for the one-dimensional examples (a) and (b) and the isotropic wave equation (d), but not for example (c), whose dispersion relation is

```math
\sigma=\vec c_0\cdot\vec k.
```

For (c),

```math
c=\frac{\sigma}{|\vec k|}
 =\vec c_0\cdot\hat{\vec k},
```

so the phase speed is independent of wavelength and frequency but depends on propagation direction relative to the background advection velocity $c_0$. It is still nondispersive with respect to wavenumber magnitude for a fixed propagation direction. The reconstruction qualifies the source sentence accordingly.

## Chapter 2

### Printed page 22 - tangential wavenumber projection in specular reflection

The source sketch labels $\theta_i$ and $\theta_r$ as the angles between the incident/reflected wavevectors and the dashed boundary **normal**. It then states that the projection of the incident wavenumber on the boundary equals the projection of the reflected wavenumber on the boundary, but typesets

```math
|\vec k_i|\cos\theta_i=|\vec k_r|\cos\theta_r.
```

For angles measured from the normal, the tangential (along-boundary) projection is instead

```math
|\vec k_i|\sin\theta_i=|\vec k_r|\sin\theta_r.
```

This is also the component that must match so the incident and reflected phases have the same dependence along the solid boundary. Together with

```math
|\vec k_i|=|\vec k_r|=\sigma/c_0,
```

it gives the source's stated result $\theta_r=\theta_i$. The reconstruction therefore uses $\sin$ and the redrawn figure constructs the boundary normal exactly perpendicular to the wall, with the two wavevectors exactly symmetric about that normal.

## Chapter 4

### Printed page 90 - reflected vertical-wavenumber ratio

The reflection geometry on pages 88--90 fixes the two wavevector directions by

```math
m_i=Rk_i,
\qquad
m_r=-Rk_r,
```

while conservation of the component along the sloping wall gives

```math
\frac{k_r}{k_i}=\frac{1+aR}{1-aR}.
```

These relations imply directly

```math
m_r=-m_i\frac{1+aR}{1-aR}.
```

The typeset source instead prints an additional factor,

```math
m_r=\pm m_i
\frac{1+aR}{1-aR}
\frac{R+a}{R-a}.
```

That extra factor is incompatible with the characteristic directions $m=\pm Rk$ stated on page 88 and with the wavevector sketch immediately preceding the formula. The reconstruction retains the historical source expression in the page note, but uses the relation implied by the source's own characteristic geometry as the corrected form.

## Chapter 5

### Printed page 110 - "free periods" followed by squared frequencies

The source says that the Neumann eigenproblem "results in a sequence of free periods" and then lists

```math
\sigma_1^2,\;\sigma_2^2,\;\sigma_3^2,\ldots
```

The surrounding derivation has consistently used $\sigma$ for angular frequency and $T=2\pi/\sigma$ for period. The listed quantities are therefore squared eigenfrequencies, not periods. The reconstruction changes only the noun, reading "a sequence of free frequencies" while preserving the displayed symbols and the rest of the source sentence.

### Printed page 113 - reversed depth and cross-step-wavenumber labels in the critical-angle argument

At the end of page 112 the source changes the problem from incidence from the deep side ($D_2$) to incidence from the shallow side ($D_1$), with $D_1 < D_2$. For this reversed problem the incident and transmitted total wavenumbers must therefore be

```math
K_I=\frac{\sigma}{(gD_1)^{1/2}},
\qquad
K_T=\frac{\sigma}{(gD_2)^{1/2}}.
```

At the critical angle, Snell's law gives

```math
K_I\sin\alpha_I'=K_T,
```

so the physically admissible result is

```math
\sin\alpha_I'=\left(\frac{D_1}{D_2}\right)^{1/2}<1.
```

The source page instead typesets $(D_2/D_1)^{1/2}$, apparently carrying the previous deep-side-incidence labels into the reversed problem. That expression is greater than one when $D_1<D_2$ and is incompatible with the same page's statement that a real critical incidence angle exists.

For the same reason, at criticality the consistent relation is

```math
\ell=\frac{\sigma}{(gD_2)^{1/2}}=K_T,
```

and beyond critical incidence it is the transmitted deep-water cross-step wavenumber $k_2$ that becomes imaginary:

```math
k_2^2=K_T^2-\ell^2<0.
```

The source page writes $k_1=0$ and then $k_1^2<0$; those labels are also inherited from the preceding incidence direction. The reconstruction uses the relabeled, internally consistent form and records the historical typesetting here.

### Printed page 116 - "waves modes"

The source sentence reads "an infinite set of waves modes". This is a straightforward grammatical/typesetting error; the reconstruction reads **"an infinite set of wave modes"**. No scientific meaning is changed.

### Printed page 117 - shelf-scattering amplitude denominator

The source first gives the matching equations

```math
A\cos k_1L=B+C,
```

and

```math
-D_1k_1A\sin k_1L=iD_2k_2(B-C).
```

Eliminating $B$ directly from those equations gives

```math
A=C\frac{i\,2D_2k_2}
        {iD_2k_2\cos k_1L+D_1k_1\sin k_1L}.
```

The subsequent typeset expression on the source page instead shows a minus sign before the $D_1 k_1\sin(k_1 L)$ term. The reconstructed equation uses the algebraically consistent plus sign and retains this note rather than silently changing the source.

### Printed page 120 - reflection coefficient

The typeset source prints the reflected/incident amplitude ratio with numerator and denominator reversed. A handwritten annotation on the source page says that it should instead be

```math
\frac{a_r}{a_i}=\frac{\sigma k+i f\ell}{\sigma k-i f\ell}.
```

This corrected form follows independently from the immediately preceding wall boundary condition

```math
-i\sigma(ika_i-ika_r)+f(i\ell a_i+i\ell a_r)=0.
```

It also has unit magnitude for real $\sigma$, $f$, $k$, and $\ell$, consistent with the text's statement that reflection changes phase but not amplitude magnitude.

### Printed page 122 - Kelvin-wave propagation direction

For a wall occupying $x=0$, the Kelvin solution has phase dependence $\exp(i\ell y)$. The source correctly states that for the ocean on $x>0$, decay requires $\ell<0$, so the wave propagates in the $-y$ direction. It then considers the ocean on $x<0$, for which decay requires $\ell>0$, but describes the propagation as the $+x$ direction. Because $\ell$ is the along-wall $y$ wavenumber and the preceding derivation contains no propagating $x$ phase, this should read **$+y$ direction**.

The reconstruction uses $+y$ and records the source wording here.

### Printed page 126 - "simply be having"

The source sentence reads "one free mode is obtained simply be having an integral number of Kelvin wavelengths around the circumference." The reconstruction changes **"be"** to **"by"**. This is a grammatical correction only.

### Printed page 130 - "aditional"

The source reads "the aditional north-south motion generated by the vorticity". The reconstruction reads "the additional north-south motion". This is a spelling correction only.

### Printed page 131 - "plane wave sloution"

The source reads "for a plane wave sloution". The reconstruction reads "for a plane wave solution". This is a spelling correction only.

### Printed page 131 - zonal-wave shorthand in the velocity example

The source first gives the general nondivergent plane-wave condition

```math
(ik\hat i+i\ell\hat j)\cdot\vec u=0,
```

then says "Thus, in a westward propagating wave" and writes

```math
v=ik\psi,
\qquad
u=-i\ell\psi=0.
```

The final equality $u=0$ requires $\ell=0$; it is therefore the purely zonal westward example, not an arbitrary westward Rossby wave. This is consistent with the earlier $\ell=0$ discussion on page 129, but the wording on page 131 does not repeat that restriction. The reconstruction preserves the source wording and formula and records the implicit assumption here rather than altering the derivation.

### Printed page 140 - "equations of motions"

The source reads "The equations of motions become". The intended grammatical form is **"The equations of motion become"**. This does not alter the equations.

### Printed page 141 - $f_0$ in the equatorial-validity sentence

After setting $f_0\to 0$ and adopting the equatorial approximation $f=\beta y$, the source says that the decay boundary condition is needed because "we cannot move to regions where $f_0$ becomes large." The constant reference value $f_0$ cannot grow with $y$; it is the retained Coriolis parameter $f=\beta y$ that grows away from the equator. The reconstruction therefore reads **$f$ becomes large**.

### Printed page 142 - $m$ called a wavenumber

The source says "For given wavenumbers $m$ and $k$, three frequencies are generally specified." Here $m$ is the discrete Hermite **mode number**, while $k$ is the zonal wavenumber. The reconstruction reads **"For given mode number $m$ and wavenumber $k$"**.

### Printed page 147 - turning coordinate written as $\theta_T$

The source calls the trapping locations $\pm\theta_T$ and writes

```math
\pm\theta_T
=\pm\frac{(gD)^{1/2}k}{\beta}\tan\theta_0.
```

With $\beta$ measured per unit meridional distance, the right-hand side has dimensions of length. The immediately following bound is also written in the distance coordinate $y$,

```math
-\sigma/\beta \le y \le \sigma/\beta.
```

The reconstructed equation therefore denotes the turning coordinate by **$y_T$**. If $\theta_T$ were intended literally as angular latitude, an additional conversion by the Earth's radius would be required. The original globe sketch is retained and still labels the conceptual trapping latitudes $\pm\theta_T$.

### Chapter 5 section numbering in the contents

The source contents list `5.5 Kelvin waves` after section `5.7 Sverdrup and Poincare waves`. The actual heading printed on page 121 is `5.8 Kelvin waves`, confirming that the table-of-contents entry is a numbering typo. The reconstruction follows the heading printed on the chapter page.

## Chapter 6

### Printed page 160 - "discrete frequencies" versus discrete cross-shelf modes

The source says that "continental shelf waves occur at discrete frequencies whereas Rossby waves form a continuum." In the derivation, however, the alongshore wavenumber $\ell$ remains continuous and each discrete cross-shelf eigenmode has a dispersion branch $\sigma_n(\ell)$. Thus the coast discretizes the **cross-shelf modal index/eigenstructure**, not frequency globally. The reconstruction reads "continental shelf waves have discrete cross-shelf modes whereas unbounded Rossby waves form a continuum."

### Printed page 167 - sign of the strong-stratification Kelvin-wave limit

The source states immediately before the dispersion relation that $\ell < 0$ in the adopted coastal orientation and the accompanying dispersion sketch shows positive frequency with mode labels $n=1,2,\ldots$. The surface condition applied to

```math
p=e^{\ell\xi/\omega}
  \cos\left[\frac{\ell}{\omega}(\eta+S)\right]
```

gives

```math
\frac{\ell S}{\omega}=q\pi
```

for an integer $q$. To label the positive-frequency branches with positive mode index $n=1,2,\ldots$ when $\ell<0$, take $q=-n$, giving

```math
\omega=-\frac{S\ell}{n\pi} > 0.
```

The source prints $\omega=S\ell/(n\pi)$ without the minus sign. That form can only be reconciled by allowing a negative integer mode label, contrary to the positive labels used in the figure. The reconstruction uses the positive-frequency form with the minus sign and records the source reading here.

## References

### Printed page 172 - Bjerknes title spelling

The source prints the German title as **"Die Theorie der Aussertropischen Zyklonenbuildung."** The correct German word, and the form used in the reconstruction, is **"Zyklonenbildung."** This is a bibliographic spelling correction only.

## Migrated audit notes still requiring explicit schema normalization

The former per-chapter audit documents contained a mixture of confirmed-no-change checks and deviations. Confirmed-no-change derivation checks were intentionally not copied here. The following source deviations were called out there and should remain visible during future review:

- **Chapter 2, printed p.19 — adiabatic entropy derivative.** Category: `equation`; status: `accepted`. Source prints $\partial S/\partial t=0$; reconstruction uses material conservation $DS/Dt=0$, consistent with the immediately following material-derivative equations.
- **Chapter 2, printed p.19 — “infinitesmal”.** Category: `typographical`; status: `accepted`. Reconstruction uses “infinitesimal”.
- **Chapter 3, printed p.54 — shorthand late-time envelope.** Category: `editorial`; status: `accepted`. The source shorthand $\eta(x,t\to\infty)=t$ is rendered as an $O(t)$ envelope statement; retain source wording/evidence if revisited.
- **Chapter 4, printed p.68 — “f-plane approrimation”.** Category: `typographical`; status: `accepted`. Reconstruction uses “f-plane approximation”.
- **Chapter 4, printed p.86 — pressure derivative transcription.** Category: `transcription`; status: `accepted`. High-resolution source read is $\rho_0 w_{zt}=p_{xx}$; an earlier reconstruction incorrectly had $w_{xtt}$.
- **Chapter 5, printed p.102 — “Bousinesq”.** Category: `typographical`; status: `accepted`. Reconstruction uses “Boussinesq”.

Continue normalizing older entries to the explicit metadata format when they are touched; do not create `verification.tsv` or separate chapter errata files.
