# Errata and editorial deviations

This file records reviewed differences between the historical 1989 source scans and the
shared reconstructed content. The scans remain the historical authority.

Each item has one status:

- **`accepted`** — a reviewed correction differs from the source.
- **`pending-review`** — a likely source problem has been identified, but the reconstruction
  remains unchanged pending a final editorial decision.
- **`reverted`** — an earlier reconstruction/audit finding was checked and restored to, or
  found already to match, the source.

Categories are `transcription`, `typographical`, `equation`, `figure`, `reference`, and
`editorial`. Audit coverage belongs in `PLAN.md`; figure-specific implementation and
provenance belong in `FIGURES.md`.

## Chapter 1

### Printed page 5 — direction dependence of vector advection

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 1, printed page 5
- **Original:** Cases (a)--(d) are said to have phase speed independent of wavelength,
  frequency, **or direction**.
- **Reconstruction:** Cases (a), (b), and (d) retain that statement. For case (c),
  $\sigma=\vec c_0\cdot\vec k$ is stated to give
  $c=\vec c_0\cdot\hat{\vec k}$, so $c$ depends on propagation direction but not on
  wavenumber magnitude.
- **Reason/evidence:** For case (c),
  $c=\sigma/|\vec k|=\vec c_0\cdot\hat{\vec k}$. It is therefore nondispersive with
  respect to $|\vec k|$ for a fixed direction, but it is anisotropic.

### Printed page 3 — complex-amplitude phase from a one-argument arctangent

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 1, printed page 3
- **Original:** The current reconstruction, believed to follow the historical text, defines
  the phase of a complex amplitude with $\tan^{-1}(\operatorname{Im}A/\operatorname{Re}A)$.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** A one-argument arctangent loses quadrant information and is undefined
  when $\operatorname{Re}A=0$. The phase is $\arg A$, equivalently an `atan2` convention.
  The scientific correction is clear; the remaining review is classification against the
  exact 1989 scan wording.

### Printed page 4 — scalar phase speed described as directed

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 1, printed page 4
- **Original:** The scalar phase speed $c=\sigma/|\vec k|$ is described as being
  directed along $\vec k$.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** A scalar speed has no direction. The normal phase-velocity vector is
  $\vec c_p=\sigma\vec k/|\vec k|^2$. Later successor notes explicitly distinguish
  the scalar phase speed from a vector velocity.

### Printed pages 11--12 — WKB scale separation of phase and amplitude

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 1, printed pages 11--12
- **Original:** The current reconstruction, believed to follow the source, describes both
  the amplitude and phase $\Theta$ as slowly varying and uses a fractional phase-change
  criterion.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** In WKB theory the phase varies on the wave scale; the slowly varying
  quantities are the amplitude and local wave parameters such as
  $\vec k=\nabla\Theta$ and $N=-\Theta_t$. The phase itself is also arbitrary up to an
  additive constant, so a criterion based on $\Delta\Theta/\Theta$ is not invariant.

## Chapter 2

### Printed page 19 — adiabatic entropy derivative

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 2, printed page 19
- **Original:** $\partial S/\partial t=0$
- **Reconstruction:** $DS/Dt=0$
- **Reason/evidence:** Adiabatic conservation applies to a moving parcel. The surrounding
  thermodynamic development also uses material derivatives.

### Printed page 19 — “infinitesmal”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 2, printed page 19
- **Original:** “infinitesmal”
- **Reconstruction:** “infinitesimal”
- **Reason/evidence:** Spelling correction only.

### Printed page 22 — tangential wavenumber projection in specular reflection

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 2, printed page 22
- **Original:** $|\vec k_i|\cos\theta_i=|\vec k_r|\cos\theta_r$
- **Reconstruction:** $|\vec k_i|\sin\theta_i=|\vec k_r|\sin\theta_r$
- **Reason/evidence:** The figure defines $\theta_i$ and $\theta_r$ from the boundary
  normal. The conserved component along the boundary is therefore
  $|\vec k|\sin\theta$, not $|\vec k|\cos\theta$. Together with
  $|\vec k_i|=|\vec k_r|$, this gives the stated $\theta_i=\theta_r$.

### Printed page 25 — waveguide cutoff indexing

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 2, printed page 25
- **Original:** The current reconstruction defines an integer $n_{\max}$ from
  $D\sigma/(\pi c_0)$ and then describes propagating/evanescent modes using
  $n<n_{\max}$ and $n>n_{\max}$.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** From
  $k_h^2=\sigma^2/c_0^2-n^2\pi^2/D^2$, propagation requires
  $n<D\sigma/(\pi c_0)$, evanescence requires the opposite strict inequality, and
  equality is the cutoff $k_h=0$. The integer shorthand mishandles exact equality and
  can omit the highest propagating integer mode.

### Printed pages 27--28 — low-impedance reflection called a solid boundary

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 2, printed pages 27--28
- **Original:** The low-transmitted-impedance limit gives pressure reflection
  $R\to-1$ and is described as consistent with a solid boundary.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** For acoustic pressure, a rigid/Neumann wall has reflection
  coefficient $R=+1$. The $R=-1$ limit is pressure-release/soft, as for water reflecting
  from a much lower-impedance air region. Likewise $T\to2$ is a pressure-amplitude
  coefficient and does not imply doubled transmitted energy.

## Chapter 3

### Printed page 54 — shorthand late-time envelope

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 3, printed page 54
- **Original:** $\eta(x,t\to\infty)=t$
- **Reconstruction:** The late-time envelope is described as $O(t)$ growth.
- **Reason/evidence:** The preceding fixed-$x$ asymptotic expression has an amplitude
  proportional to $t$. The source equality is dimensional shorthand, not a literal
  equality between surface displacement and time.

### Printed page 49 — finite-depth linear limit called deep water

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed page 49
- **Original:** The regime $\epsilon\ll1$, $\delta=1$ is described as the deep-water
  problem.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** With $\delta=D/L$, taking $\delta=O(1)$ is the linear
  finite-depth regime. The deep-water limit requires the depth to be asymptotically large
  compared with the wavelength, not merely $D/L=1$.

### Printed pages 51--52 — generic stationary-phase amplitude treated as real

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed pages 51--52
- **Original:** The generic stationary-phase expression uses $\bar\eta_0(k_0)$ as a
  real multiplicative amplitude.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** For arbitrary real initial data the Fourier transform
  $\bar\eta_0(k_0)$ is generally complex. The asymptotic physical elevation must retain
  the complex phase of that coefficient, e.g. through a real-part expression. The later
  delta-function example is unaffected because its transform is real and constant.

### Printed pages 57 and 59 — bottom kinematic and Leibniz signs

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed pages 57 and 59
- **Original:** For a bottom $z=-D(x,y,t)$ the stationary-bottom condition is written
  with the opposite sign, and the corresponding lower-limit term in the integrated
  energy manipulation carries the matching opposite sign.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** Material impermeability of $F=z+D(x,y,t)=0$ gives
  $w=-(D_t+uD_x+vD_y)$. The lower-limit Leibniz term must use the same geometry.
  The two sign errors cancel in the displayed integrated-energy result, so that final
  result survives even though the intermediate formulas do not.

### Printed page 57 — local gravitational-energy time derivative

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed page 57
- **Original:** The local energy derivation replaces $\rho g w$ by a time derivative of
  $\rho g z$ using $w=z_t$.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** $w=Dz/Dt$ is a material parcel derivative, not the Eulerian partial
  derivative of the coordinate $z$. The local derivation therefore mixes Eulerian and
  parcel derivatives. The later period-averaged results
  $\overline{KE}=\overline{PE}$ and $\overline{\vec F}=\overline E\,\vec c_g$
  remain correct.

### Printed page 59 — gravity retained after hydrostatic pressure subtraction

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed page 59
- **Original:** After writing total pressure as a hydrostatic basic pressure plus a
  perturbation, the perturbation vertical momentum equation retains another explicit
  $-g$ term.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** The background hydrostatic pressure gradient already balances
  gravity. Subtracting that basic state removes the constant gravitational acceleration
  from the perturbation vertical momentum equation.

### Printed page 60 — slowly varying current amplitude from energy conservation

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 3, printed page 60
- **Original:** Wave-amplitude evolution on a slowly varying current is described using
  ordinary wave-energy conservation.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** In a steady but spatially varying current, wave energy can exchange
  with the mean flow. The adiabatic invariant for conservative linear waves is generally
  wave action $E/\sigma'$, where $\sigma'$ is intrinsic frequency, consistent with the
  wave-action discussion introduced in Chapter 1.

## Chapter 4

### Printed page 69 — pressure symbol used instead of density perturbation

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 4, printed page 69
- **Original:** The historical scan writes
  $u_t=-g p\sin\theta/\rho_0$ in the nonrotating transverse-motion argument.
- **Reconstruction:** Currently follows the source; canonical correction pending.
- **Reason/evidence:** The force being projected along the parcel-motion direction is
  buoyancy, so the symbol must be the density perturbation:
  $u_t=-g\rho\sin\theta/\rho_0$. Combining this with
  $\rho_t+u\sin\theta\,\rho_{0z}=0$ then gives the immediately following
  $u_{tt}+N^2\sin^2\theta\,u=0$. Direct inspection confirms the error is present in
  the 1989 source scan.

### Printed pages 73--75 — zero-group-speed endpoints called energy propagation

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 4, printed pages 73--75
- **Original:** The exact $\sigma=N$ and $\sigma=f$ endpoints are described as
  vertical or horizontal “energy propagation.”
- **Reconstruction:** Currently follows the source; clarification pending.
- **Reason/evidence:** The same dispersion relation and displayed group-speed formula give
  $|\vec c_g|=0$ at those exact endpoints. The geometry is useful as the limiting
  cone/direction state approached by propagating waves, but there is no finite group
  propagation at the endpoint itself. Direct scan inspection confirms the wording is
  historical.

### Printed page 68 — earlier “approrimation” audit finding

- **Category:** `transcription`
- **Status:** `reverted`
- **Location:** Chapter 4, printed page 68
- **Original:** The source scan reads “f-plane approximation.”
- **Reconstruction:** “f-plane approximation.”
- **Reason/evidence:** Direct reinspection of the source scan shows that the earlier audit
  reading “f-plane approrimation” was erroneous. There is no current source/reconstruction
  deviation.

### Printed page 86 — pressure derivative transcription

- **Category:** `transcription`
- **Status:** `reverted`
- **Location:** Chapter 4, printed page 86
- **Original:** $\rho_0 w_{zt}=p_{xx}$
- **Reconstruction:** $\rho_0 w_{zt}=p_{xx}$
- **Reason/evidence:** A prior reconstruction had read the left side as $w_{xtt}$.
  Reinspection of the high-resolution scan restored the source form. Independently,
  differentiating $u_x+w_z=0$ in time and using
  $u_t=-p_x/\rho_0$ gives $\rho_0w_{zt}=p_{xx}$.

### Printed page 90 — reflected vertical-wavenumber ratio

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 4, printed page 90
- **Original:**
  $m_r=\pm m_i[(1+aR)/(1-aR)][(R+a)/(R-a)]$
- **Reconstruction:** $m_r=-m_i(1+aR)/(1-aR)$
- **Reason/evidence:** The surrounding derivation fixes
  $m_i=Rk_i$, $m_r=-Rk_r$, and
  $k_r/k_i=(1+aR)/(1-aR)$. These relations directly imply the reconstructed result;
  the extra source factor is incompatible with the characteristic directions.

### Printed page 90 — signed versus magnitude wavenumber ratio

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 4, printed page 90
- **Original:** $|\vec k_r|=|\vec k_i|(1+aR)/(1-aR)$.
- **Reconstruction:** Unchanged pending review.
- **Reason/evidence:** Equality of phase along the wall $z=ax$, together with
  $m_i=Rk_i$ and $m_r=-Rk_r$, gives the **signed** component relation
  $k_r/k_i=(1+aR)/(1-aR)$. For magnitudes the corresponding relation requires an
  absolute value,
  $|\vec k_r|/|\vec k_i|=|(1+aR)/(1-aR)|$. The printed magnitude equation becomes
  negative for $aR>1$ and therefore cannot hold literally across supercritical slopes.
  Check whether the surrounding argument intends an unstated restriction $aR<1$
  before changing the reconstruction.

## Chapter 5

### Printed page 98 — sign of the rotating effective potential

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 98
- **Original:** The historical source writes the total potential as
  $gr+\tfrac12\Omega^2r^2\cos^2\theta$.
- **Reconstruction:** Currently follows the source; canonical correction pending.
- **Reason/evidence:** Gravity contributes acceleration $-\nabla(gr)$ while centrifugal
  acceleration is $+\nabla[\tfrac12\Omega^2r^2\cos^2\theta]$. Therefore the
  effective potential whose negative gradient gives the total conservative acceleration is
  $gr-\tfrac12\Omega^2r^2\cos^2\theta$. The same page's laboratory free-surface
  paraboloid requires this minus sign. The nearby estimate
  $100\Omega^2a/(2g)$ also appears to contain an extra factor $1/2$ if it is intended
  to estimate the rotation-only pole-to-equator gravity difference, which is
  $\Omega^2a/g\simeq0.35\%$.

### Printed page 102 — “Bousinesq”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 102
- **Original:** “Bousinesq approximation”
- **Reconstruction:** “Boussinesq approximation”
- **Reason/evidence:** Spelling correction of the standard approximation name. Direct
  reinspection confirms the misspelling is present in the source scan.

### Printed page 110 — “free periods” followed by squared frequencies

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 110
- **Original:** “a sequence of free periods
  $\sigma_1^2,\sigma_2^2,\sigma_3^2,\ldots$”
- **Reconstruction:** “a sequence of squared free frequencies
  $\sigma_1^2,\sigma_2^2,\sigma_3^2,\ldots$”
- **Reason/evidence:** The text defines $\sigma$ as angular frequency and
  $T=2\pi/\sigma$ as period. The displayed eigenvalues are $\sigma_n^2$, so they are
  squared angular frequencies, not periods. “Squared free frequencies” also avoids the
  earlier imprecision of calling $\sigma_n^2$ simply “frequencies.”

### Printed page 110 — omitted Neumann zero mode

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 110
- **Original:** The Neumann Helmholtz problem is said to have squared free frequencies
  with a positive lowest member.
- **Reconstruction:** Unchanged pending canonical clarification.
- **Reason/evidence:** The Neumann Laplacian also admits the constant eigenfunction
  $\eta=\mathrm{constant}$ with $\sigma=0$. A positive lowest member follows only
  after imposing fixed volume, equivalently zero-mean surface displacement, to remove
  the constant offset. In the rectangular example, calling $(n,m)=(1,0)$ the gravest
  nonconstant mode also assumes the $x$ dimension is at least as long as the $y$
  dimension; in general the gravest nonconstant mode varies along the longer side.

### Printed page 111 — “Lamb (1832)”

- **Category:** `reference`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 111
- **Original:** “Lamb (1832)”
- **Reconstruction:** “Lamb (1932)”
- **Reason/evidence:** Horace Lamb lived from 1849 to 1934, so 1832 is impossible. The
  sixth edition of *Hydrodynamics* was published by Cambridge University Press in 1932,
  and later literature specifically cites Lamb (1932) for the long-wave step matching
  result discussed here. The bibliography's 1945 Dover volume is an unabridged reprint
  of that sixth edition, so retaining the reprint in the bibliography is compatible with
  correcting the historical in-text year to 1932.

### Printed page 113 — reversed depth and cross-step-wavenumber labels

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 113
- **Original:** In the reversed shallow-side-incidence problem the source carries over
  labels from the preceding deep-side-incidence case, including
  $\sin\alpha_I'=(D_2/D_1)^{1/2}$ and subsequent $k_1$ critical/evanescent labels.
- **Reconstruction:**
  $\sin\alpha_I'=(D_1/D_2)^{1/2}$,
  $\ell=\sigma/(gD_2)^{1/2}=K_T$, and $k_2^2<0$ beyond critical incidence.
- **Reason/evidence:** For incidence from the shallow side,
  $K_I=\sigma/(gD_1)^{1/2}$ and
  $K_T=\sigma/(gD_2)^{1/2}$. Snell’s law at
  $\alpha_T=90^\circ$ gives $K_I\sin\alpha_I'=K_T$, hence the reconstructed
  ratio. Since $D_1<D_2$, the source ratio would exceed one.

### Printed page 113 — reversed-incidence amplitude coefficients

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 113
- **Original:** On reversing the incidence direction, the text says that the reflected
  and transmitted amplitudes are “still given by the above formulas.”
- **Reconstruction:** Unchanged pending review.
- **Reason/evidence:** The preceding formulas are written for incidence from the deep
  $D_2$ side. Repeating the same elevation/transport matching for incidence from the
  shallow $D_1$ side gives
  $A_R/A_I=(D_1k_1-D_2k_2)/(D_1k_1+D_2k_2)$ and
  $A_T/A_I=2D_1k_1/(D_1k_1+D_2k_2)$. Thus the same **matching form** applies only
  after interchanging which region is incident and transmitted; the coefficients as
  previously written do not remain literally unchanged.

### Printed page 116 — “waves modes”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 116
- **Original:** “an infinite set of waves modes”
- **Reconstruction:** “an infinite set of wave modes”
- **Reason/evidence:** Grammatical/typesetting correction only; direct reinspection
  confirms the source wording.

### Printed page 117 — shelf-scattering amplitude denominator

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 117
- **Original:**
  $A=C\,i2D_2k_2/[iD_2k_2\cos(k_1L)-D_1k_1\sin(k_1L)]$
- **Reconstruction:**
  $A=C\,i2D_2k_2/[iD_2k_2\cos(k_1L)+D_1k_1\sin(k_1L)]$
- **Reason/evidence:** Eliminating $B$ from the two matching equations immediately
  preceding the formula gives the plus sign. Direct reinspection confirms the source
  prints the minus sign.

### Printed page 120 — reflection coefficient

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 120
- **Original:** The typeset fraction has numerator and denominator reversed.
- **Reconstruction:**
  $a_r/a_i=(\sigma k+i f\ell)/(\sigma k-i f\ell)$
- **Reason/evidence:** The corrected expression follows directly from the preceding wall
  boundary condition and has unit magnitude for real $\sigma,f,k,\ell$. A handwritten
  correction on the source page gives the same reconstructed expression.

### Printed page 120 — inertial-oscillation velocity sign

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 120
- **Original:** After $u_t-fv=0$ and $v_t+fu=0$, the source gives
  $u=\cos(ft)$ and $v=\sin(ft)$.
- **Reconstruction:** Currently follows the source; canonical correction pending.
- **Reason/evidence:** Substitution shows the printed pair does not satisfy the stated
  equations for $f>0$. With $u(0)=1$, $v(0)=0$, the solution is
  $u=\cos(ft)$, $v=-\sin(ft)$, corresponding to clockwise inertial rotation in the
  Northern Hemisphere under the chapter's sign convention.

### Printed page 122 — Kelvin-wave propagation direction

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 122
- **Original:** For the ocean on $x<0$, the source says the wave propagates in the
  “$+x$ direction.”
- **Reconstruction:** “$+y$ direction.”
- **Reason/evidence:** The propagating phase is $\exp(i\ell y)$; $x$ controls only the
  offshore exponential decay. For $x<0$, decay requires $\ell>0$, hence propagation
  in $+y$ for the stated positive-frequency convention.

### Printed page 126 — “simply be having”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 126
- **Original:** “one free mode is obtained simply be having ...”
- **Reconstruction:** “one free mode is obtained simply by having ...”
- **Reason/evidence:** Grammatical correction only.

### Printed page 129 — coordinate phase speeds described as components

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 129
- **Original:** After stating that phase speed has a westward component, the text writes
  $c_x=\sigma/k$ and $c_y=\sigma/\ell$ as though these were vector components.
- **Reconstruction:** Unchanged pending review.
- **Reason/evidence:** Chapter 1 already distinguishes $\sigma/k$ from the $x$ component
  of the phase-velocity vector: it is the speed at which a constant-phase plane
  intersects the $x$ axis. For a two-dimensional plane wave the phase-velocity vector is
  $\vec c_p=\sigma\vec k/|\vec k|^2$. The Rossby-wave conclusion remains valid because
  its true zonal component is
  $c_{px}=\sigma k/(k^2+\ell^2)=-\beta k^2/(k^2+\ell^2)^2\le0$.
  Consider clarifying the terminology while retaining $\sigma/k$ as the conventional
  zonal coordinate phase speed.

### Printed page 130 — “aditional”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 130
- **Original:** “aditional”
- **Reconstruction:** “additional”
- **Reason/evidence:** Spelling correction only.

### Printed page 131 — “plane wave sloution”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 131
- **Original:** “plane wave sloution”
- **Reconstruction:** “plane wave solution”
- **Reason/evidence:** Spelling correction only.

### Printed page 131 — implicit zonal-wave restriction

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 131
- **Original:** “Thus, in a westward propagating wave,” followed by
  $u=-i\ell\psi=0$.
- **Reconstruction:** “Thus, in a westward propagating wave with $\ell=0$,”
  followed by the same velocity relations.
- **Reason/evidence:** The equality $u=0$ requires $\ell=0$. The added qualifier clarifies
  the purely zonal example already used in the nearby discussion without
  changing the derivation.

### Printed page 131 — Rossby-wave group direction stated too generally

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 131
- **Original:** The text broadly states that a westward-going Rossby wave transmits
  energy eastward.
- **Reconstruction:** Unchanged pending canonical qualification.
- **Reason/evidence:** For the nondivergent Rossby dispersion relation,
  $c_{gx}=\beta(k^2-\ell^2)/(k^2+\ell^2)^2$, so the zonal group velocity can have
  either sign. The statement is appropriate for the purely or nearly zonal short-wave
  geometry being emphasized, but it is not universal for arbitrary $(k,\ell)$.

### Printed page 140 — “equations of motions”

- **Category:** `typographical`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 140
- **Original:** “The equations of motions become”
- **Reconstruction:** “The equations of motion become”
- **Reason/evidence:** Grammatical correction only.

### Printed page 141 — $f_0$ in the equatorial-validity sentence

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 141
- **Original:** After setting $f_0\to0$ and $f=\beta y$, the source says one cannot
  move to regions where “$f_0$ becomes large.”
- **Reconstruction:** “$f$ becomes large.”
- **Reason/evidence:** $f_0$ is a constant reference value and has just been set to zero.
  The retained Coriolis parameter $f=\beta y$ is what grows away from the equator.

### Printed page 142 — $m$ called a wavenumber

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 142
- **Original:** “For given wavenumbers $m$ and $k$ ...”
- **Reconstruction:** “For given mode number $m$ and wavenumber $k$ ...”
- **Reason/evidence:** $m=0,1,2,\ldots$ is the discrete Hermite mode index; $k$ is the
  zonal wavenumber.

### Printed page 142 — inconsistent constant-order high-wavenumber asymptotic

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 142
- **Original:** From
  $\omega^2-\lambda^2-\lambda/\omega=2m+1$, the text takes
  $|\lambda|,|\omega|\to\infty$, notes that $\lambda/\omega$ remains constant,
  and then writes $\omega^2=\lambda^2+2m+1$.
- **Reconstruction:** Unchanged pending direct scan confirmation and canonical edit.
- **Reason/evidence:** The step drops the $O(1)$ term $\lambda/\omega$ while retaining
  the $O(1)$ right side. The leading asymptote $\omega\sim\pm\lambda$ is correct.
  If constant-order accuracy is retained and $s=\omega/\lambda\to\pm1$, then
  $\omega^2-\lambda^2\sim2m+1+1/s$, giving approximately $2m+2$ on the
  eastward branch and $2m$ on the westward branch.

### Printed page 146 — local meridional phase with variable wavenumber

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed page 146
- **Original:** $v=v_0(y)\exp[-i\sigma t+ikx+i\ell(y)y]$ while treating $\ell(y)$ as
  the local meridional wavenumber.
- **Reconstruction:** Unchanged pending review.
- **Reason/evidence:** Ray theory defines local wavenumber as the gradient of phase. If
  $\Theta_y=\ell(y)$, the phase must contain
  $\int^y\ell(y')\,dy'$. Differentiating the printed phase instead gives
  $\Theta_y=\ell+y\ell_y$. The WKB/local-plane-wave ansatz should therefore use
  $\exp[i\int^y\ell(y')\,dy']$ when $\ell$ varies with latitude.

### Printed pages 146--147 — ray direction identified with wavevector direction

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 5, printed pages 146--147
- **Original:** The text defines the ray path by $dy/dx=\ell/k$ while retaining the
  local equatorial dispersion term $-\beta k/\sigma$.
- **Reconstruction:** Unchanged pending review.
- **Reason/evidence:** Earlier ray theory in Chapter 1 defines a ray as the wave-group
  path, so $dy/dx=c_{gy}/c_{gx}$. For the local dispersion function
  $F=\sigma^2/(gD)-k^2-\ell^2-\beta k/\sigma-\beta^2y^2/(gD)=0$,
  implicit differentiation gives
  $c_{gy}/c_{gx}=2\ell/(2k+\beta/\sigma)$, not $\ell/k$. The printed expression is
  recovered only if the $\beta k/\sigma$ contribution is neglected, but that term is
  retained in the same local dispersion relation. If the full local dispersion is kept,
  the subsequent ray angle and sinusoidal path require the same
  $k+\beta/(2\sigma)$ correction. The turning points still follow from $\ell=0$.

### Printed page 147 — turning coordinate written as $\theta_T$

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 5, printed page 147
- **Original:**
  $\pm\theta_T=\pm[(gD)^{1/2}k/\beta]\tan\theta_0$
- **Reconstruction:**
  $\pm y_T=\pm[(gD)^{1/2}k/\beta]\tan\theta_0$
- **Reason/evidence:** With $\beta$ defined per unit meridional distance, the
  right-hand side has dimensions of length. The immediately following inertial bound
  is also expressed in the distance coordinate $y$. A literal angular latitude would
  require an additional Earth-radius conversion.

### Chapter 5 section numbering in the contents

- **Category:** `transcription`
- **Status:** `reverted`
- **Location:** Historical table of contents; Kelvin waves entry
- **Original:** The historical source scan reads `5.8 Kelvin waves`.
- **Reconstruction:** `5.8 Kelvin waves`.
- **Reason/evidence:** Direct reinspection of the contents scan shows that the earlier
  audit reading `5.5 Kelvin waves` was erroneous. There is no source/reconstruction
  deviation.

## Chapter 6

### Printed page 159 — modal maximum differentiated at fixed cross-shelf wavenumber

- **Category:** `equation`
- **Status:** `pending-review`
- **Location:** Chapter 6, printed page 159
- **Original:** The maximum of each continental-shelf-wave dispersion branch is found by
  setting $\partial\sigma/\partial\ell=0$ in
  $\sigma=-2bf\ell/(\ell^2+k^2+b^2)$ while treating $k$ as fixed, giving
  $\ell=-(k^2+b^2)^{1/2}$.
- **Reconstruction:** Unchanged pending canonical correction; issue #9 independently
  identified the same source error from the figure-equation audit.
- **Reason/evidence:** Along a discrete shelf-wave mode, $k=k_n(\ell)$ is constrained by
  $\tan(kL)=k/(\ell-b)$, so the modal derivative must include $dk_n/d\ell$. The
  correct extremum condition is
  $k^2+b^2-\ell^2=2\ell k\,dk_n/d\ell$. For the normalized first branch
  $b=L=f=1$, the independently solved maximum is
  $\ell=-2.4232766722$, $k=2.5090927417$,
  $\sigma=0.3680605246$, not the fixed-$k$ condition.

### Printed pages 163--164 — condition on the short-wave coastal-trapped asymptote

- **Category:** `editorial`
- **Status:** `pending-review`
- **Location:** Chapter 6, printed pages 163--164
- **Original:** The short-wave limit is stated as
  $\lim_{\ell\to-\infty}\omega=S\max[D_x]$, followed on the next page by the
  statement that if $S\max[D_x]>1$ the free subinertial branches reach the inertial
  frequency $\omega=1$.
- **Reconstruction:** Unchanged pending a condition that explicitly reconciles the two
  statements.
- **Reason/evidence:** The Rhines/bottom-trapped large-$|\ell|$ asymptote is attained by
  the subinertial family only when $S\max[D_x]<1$. If the formal estimate exceeds
  unity, the physical subinertial branch reaches the inertial limit first and is cut off.
  The governing equations are not broken; the missing qualification is the issue.

### Printed page 160 — “discrete frequencies” versus discrete cross-shelf modes

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 6, printed page 160
- **Original:** “continental shelf waves occur at discrete frequencies whereas Rossby
  waves form a continuum”
- **Reconstruction:** “continental shelf waves have discrete cross-shelf modes whereas
  unbounded Rossby waves form a continuum”
- **Reason/evidence:** The cross-shelf boundary-value problem discretizes the modal
  index/eigenstructure, while the alongshore wavenumber $\ell$ remains continuous and
  each mode has a dispersion branch $\sigma_n(\ell)$. Frequency is not globally
  discrete.

### Printed page 167 — sign of the strong-stratification Kelvin-wave limit

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 6, printed page 167
- **Original:** $\omega=S\ell/(n\pi)$ with $n=1,2,\ldots$
- **Reconstruction:** $\omega=-S\ell/(n\pi)$ with $n=1,2,\ldots$
- **Reason/evidence:** The preceding convention is $\ell<0$. Applying the surface
  condition to
  $p=e^{\ell\xi/\omega}\cos[(\ell/\omega)(\eta+S)]$
  gives $\ell S/\omega=q\pi$. Positive-frequency branches with positive mode labels
  require $q=-n$, hence the reconstructed minus sign.

## References

### Printed page 172 — Bjerknes title spelling

- **Category:** `reference`
- **Status:** `accepted`
- **Location:** References, printed page 172
- **Original:** “Die Theorie der Aussertropischen Zyklonenbuildung.”
- **Reconstruction:** “Die Theorie der Aussertropischen Zyklonenbildung.”
- **Reason/evidence:** `Zyklonenbildung` is the correct German word and the form used
  by bibliographic records for the 1937 Bjerknes paper.
