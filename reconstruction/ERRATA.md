# Errata and editorial deviations

The historical PDFs under `source/` are authoritative for the reconstruction. The canonical
chapter text follows the source unless a deviation is either an unambiguous minor typo or an
explicitly human-approved substantive erratum.

Agents may identify and analyze possible errors, but **agents can never approve an erratum**.
Scientific or mathematical correctness by itself is not approval. Until the human owner approves
a substantive change, the source reading remains in the canonical reconstruction.

Statuses used here:

- **`pending-human-approval`** — a substantive source issue or proposed correction. The
  canonical reconstruction follows the historical source until the human owner explicitly approves
  the deviation.
- **`minor-typo-correction`** — a small, unambiguous spelling/grammar/transcription typo with no
  plausible scientific, mathematical, bibliographic, or editorial change in meaning. These may be
  corrected without separate errata approval.
- **`human-approved`** — reserved for an explicitly documented human-approved substantive
  deviation. Agents must never assign this status autonomously.

False-positive audit findings that were already shown to match the source are omitted rather than
retained as errata history. Audit coverage belongs in `PLAN.md`; figure provenance and equation
validation belong in `FIGURES.md`.

## Chapter 1

### Printed page 5 — direction dependence of vector advection
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 1, printed page 5
- **Source:** Cases (a)--(d) are said to have phase speed independent of wavelength, frequency, **or direction**.
- **Proposed correction:** Qualify case (c), since for $\sigma=\vec c_0\cdot\vec k$, $c=\vec c_0\cdot\hat{\vec k}$ depends on propagation direction.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The proposed correction is mathematically defensible, but it is substantive.

### Printed page 3 — complex-amplitude phase from a one-argument arctangent
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 1, printed page 3
- **Source:** $\tan^{-1}(\operatorname{Im}A/\operatorname{Re}A)$.
- **Proposed correction:** Use $\arg A$ or an equivalent `atan2` convention.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** A one-argument arctangent loses quadrant information; the source scan nevertheless prints this form.

### Printed page 4 — scalar phase speed described as directed
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 1, printed page 4
- **Source:** After defining scalar $c=\sigma/|\vec k|=\lambda/T$, the source says, “It is directed along $\vec k$.”
- **Proposed correction:** Distinguish scalar speed from the phase-velocity vector.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Direction belongs to a velocity vector, but changing the prose is editorially substantive.

### Printed pages 11--12 — WKB scale separation of phase and amplitude
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 1, printed pages 11--12
- **Source:** Both amplitude $a$ and phase $\Theta$ are described as slowly varying, with $\Delta\Theta/\Theta\ll1$.
- **Proposed correction:** State that amplitude and local phase gradients vary slowly while phase itself varies on the wave scale.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The proposed WKB formulation is more standard, but the historical wording is unambiguous and must be preserved absent approval.

## Chapter 2

### Printed page 19 — adiabatic entropy derivative
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 2, printed page 19
- **Source:** $\partial S/\partial t=0$.
- **Proposed correction:** $DS/Dt=0$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Material conservation is physically preferable, but the change is substantive.

### Printed page 19 — “infinitesmal”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 2, printed page 19
- **Source:** “infinitesmal”
- **Reconstruction:** “infinitesimal”
- **Reason/evidence:** Unambiguous spelling correction only.

### Printed page 22 — tangential wavenumber projection in specular reflection
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 2, printed page 22
- **Source:** $|\vec k_i|\cos\theta_i=|\vec k_r|\cos\theta_r$.
- **Proposed correction:** Use $\sin\theta$ if the angles are measured from the boundary normal.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The geometric argument supports the proposal, but the source expression is clear.

### Printed page 25 — waveguide cutoff indexing
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 2, printed page 25
- **Source:** Integer $n_{\max}$ is used with $n<n_{\max}$ and $n>n_{\max}$ to separate propagating and evanescent modes.
- **Proposed correction:** State the exact condition $n<D\sigma/(\pi c_0)$, equality as cutoff, and $n>D\sigma/(\pi c_0)$ as evanescence.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The integer shorthand mishandles exact equality and can omit the highest propagating integer mode.

### Printed pages 27--28 — low-impedance reflection called a solid boundary
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 2, printed pages 27--28
- **Source:** The $R\to-1$ low-transmitted-impedance pressure-reflection limit is described as consistent with a solid boundary.
- **Proposed correction:** Describe $R=-1$ as pressure-release/soft rather than rigid/solid, and clarify that $T\to2$ is a pressure-amplitude coefficient.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Rigid pressure reflection has $R=+1$ under the stated convention.

## Chapter 3

### Printed page 54 — shorthand late-time envelope
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed page 54
- **Source:** $\eta(x,t\to\infty)=t$.
- **Proposed correction:** Describe the asymptotic envelope as $O(t)$ growth.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The source equality is dimensional shorthand, but changing it alters the historical text.

### Printed page 49 — finite-depth linear limit called deep water
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed page 49
- **Source:** The regime $\epsilon\ll1$, $\delta=1$ is described as deep water.
- **Proposed correction:** Call this the linear finite-depth regime.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** With $\delta=D/L$, $\delta=O(1)$ is not the asymptotic deep-water limit.

### Printed pages 51--52 — generic stationary-phase amplitude treated as real
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed pages 51--52
- **Source:** The generic stationary-phase expression treats $\bar\eta_0(k_0)$ as a real multiplicative amplitude.
- **Proposed correction:** Retain its complex phase, e.g. through a real-part expression.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** For arbitrary real initial data the Fourier transform is generally complex.

### Printed pages 57 and 59 — bottom kinematic and Leibniz signs
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed pages 57 and 59
- **Source:** The bottom kinematic condition and matching lower-limit term use the opposite sign from $w=-(D_t+uD_x+vD_y)$.
- **Proposed correction:** Reverse both intermediate signs consistently.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The two apparent sign errors cancel in the displayed integrated-energy result.

### Printed page 57 — local gravitational-energy time derivative
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed page 57
- **Source:** The derivation replaces $\rho g w$ by a time derivative of $\rho g z$ using $w=z_t$.
- **Proposed correction:** Distinguish material and Eulerian derivatives.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** $w=Dz/Dt$ is a parcel derivative; the later period-averaged results remain correct.

### Printed page 59 — gravity retained after hydrostatic pressure subtraction
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed page 59
- **Source:** The perturbation vertical momentum equation retains an explicit $-g$ after hydrostatic pressure is split off.
- **Proposed correction:** Remove the duplicated gravitational term.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The hydrostatic background pressure gradient already balances gravity.

### Printed page 60 — slowly varying current amplitude from energy conservation
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 3, printed page 60
- **Source:** Wave-amplitude evolution on a slowly varying current is described using ordinary wave-energy conservation.
- **Proposed correction:** Use wave-action conservation $E/\sigma'$ where appropriate.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Wave energy can exchange with the mean flow in a spatially varying current.

## Chapter 4

### Printed page 69 — pressure symbol used instead of density perturbation
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 4, printed page 69
- **Source:** $u_t=-g p\sin\theta/\rho_0$.
- **Proposed correction:** $u_t=-g\rho\sin\theta/\rho_0$.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Only the density-perturbation form combines with the following density equation to produce $u_{tt}+N^2\sin^2\theta\,u=0$; the source scan clearly prints $p$.

### Printed pages 73--75 — zero-group-speed endpoints called energy propagation
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 4, printed pages 73--75
- **Source:** Exact $\sigma=N$ and $\sigma=f$ endpoints are described as directions of “energy propagation.”
- **Proposed correction:** Describe them as limiting direction/cone cases because $|\vec c_g|=0$ at the exact endpoints.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The source's own group-speed expression gives zero at those endpoints.

### Printed page 90 — reflected vertical-wavenumber ratio
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 4, printed page 90
- **Source:** $m_r=\pm m_i[(1+aR)/(1-aR)][(R+a)/(R-a)]$.
- **Proposed correction:** $m_r=-m_i(1+aR)/(1-aR)$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The surrounding relations imply the proposed result, but the source expression is unambiguous.

### Printed page 90 — signed versus magnitude wavenumber ratio
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 4, printed page 90
- **Source:** $|\vec k_r|=|\vec k_i|(1+aR)/(1-aR)$.
- **Proposed correction:** Use a signed component relation or an absolute value for magnitude if supercritical slopes are included.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The printed magnitude factor becomes negative for $aR>1$.

## Chapter 5

### Printed page 98 — sign of the rotating effective potential
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 98
- **Source:** $gr+\tfrac12\Omega^2r^2\cos^2\theta$.
- **Proposed correction:** $gr-\tfrac12\Omega^2r^2\cos^2\theta$ for the effective potential whose negative gradient gives gravity plus centrifugal acceleration.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The sign implied by the laboratory free-surface paraboloid differs from the printed potential.

### Printed page 102 — “Bousinesq”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 102
- **Source:** “Bousinesq approximation”
- **Reconstruction:** “Boussinesq approximation”
- **Reason/evidence:** Unambiguous spelling correction only.

### Printed page 110 — “free periods” followed by squared frequencies
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 110
- **Source:** “a sequence of free periods $\sigma_1^2,\sigma_2^2,\sigma_3^2,\ldots$”.
- **Proposed correction:** “a sequence of squared free frequencies”.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** $\sigma$ is angular frequency and the displayed eigenvalues are $\sigma_n^2$.

### Printed page 110 — omitted Neumann zero mode
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 110
- **Source:** The Neumann Helmholtz problem is described as having a positive lowest squared free frequency.
- **Proposed correction:** Note the constant $\sigma=0$ mode unless fixed volume/zero mean is imposed.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** The Neumann Laplacian admits a constant eigenfunction.

### Printed page 111 — “Lamb (1832)”
- **Category:** `reference`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 111
- **Source:** “Lamb (1832)”
- **Proposed correction:** “Lamb (1932)”
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Horace Lamb lived 1849–1934 and the sixth edition of *Hydrodynamics* is 1932, but changing a historical citation year is substantive bibliographic editing.

### Printed page 113 — reversed depth and cross-step-wavenumber labels
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 113
- **Source:** The reversed shallow-side-incidence case carries over $\sin\alpha_I'=(D_2/D_1)^{1/2}$ and subsequent $k_1$ labels.
- **Proposed correction:** $\sin\alpha_I'=(D_1/D_2)^{1/2}$, $\ell=\sigma/(gD_2)^{1/2}=K_T$, and $k_2^2<0$ beyond critical incidence.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Snell's law for shallow-side incidence gives the proposed depth ratio.

### Printed page 113 — reversed-incidence amplitude coefficients
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 113
- **Source:** On reversing incidence, the text says reflected and transmitted amplitudes are “still given by the above formulas.”
- **Proposed correction:** State that the matching form is retained only after interchanging incident/transmitted region labels.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Direct rematching gives $A_R/A_I=(D_1k_1-D_2k_2)/(D_1k_1+D_2k_2)$ and $A_T/A_I=2D_1k_1/(D_1k_1+D_2k_2)$.

### Printed page 116 — “waves modes”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 116
- **Source:** “an infinite set of waves modes”
- **Reconstruction:** “an infinite set of wave modes”
- **Reason/evidence:** Unambiguous grammatical correction only.

### Printed page 117 — shelf-scattering amplitude denominator
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 117
- **Source:** $A=C\,i2D_2k_2/[iD_2k_2\cos(k_1L)-D_1k_1\sin(k_1L)]$.
- **Proposed correction:** Replace the minus sign in the denominator by plus.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Eliminating $B$ from the preceding matching equations gives the proposed plus sign.

### Printed page 120 — reflection coefficient
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 120
- **Source:** The typeset fraction is the inverse of $(\sigma k+i f\ell)/(\sigma k-i f\ell)$.
- **Proposed correction:** $a_r/a_i=(\sigma k+i f\ell)/(\sigma k-i f\ell)$.
- **Canonical reconstruction:** Restored to the typeset historical source pending human approval.
- **Reason/evidence:** The proposed form follows from the wall boundary condition and agrees with a handwritten correction, but the handwritten mark is not human approval for this digital edition.

### Printed page 120 — inertial-oscillation velocity sign
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 120
- **Source:** After $u_t-fv=0$ and $v_t+fu=0$, the source gives $u=\cos(ft)$ and $v=\sin(ft)$.
- **Proposed correction:** $v=-\sin(ft)$ for the stated equations and initial condition.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Direct substitution supports the proposed sign.

### Printed page 122 — Kelvin-wave propagation direction
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 122
- **Source:** For the ocean on $x<0$, the source says the wave propagates in the “$+x$ direction.”
- **Proposed correction:** “$+y$ direction.”
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The propagating phase is $\exp(i\ell y)$; $x$ controls offshore decay.

### Printed page 126 — “simply be having”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 126
- **Source:** “one free mode is obtained simply be having ...”
- **Reconstruction:** “one free mode is obtained simply by having ...”
- **Reason/evidence:** Unambiguous grammatical correction only.

### Printed page 129 — coordinate phase speeds described as components
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 129
- **Source:** $c_x=\sigma/k$ and $c_y=\sigma/\ell$ are described as though they were vector components.
- **Proposed correction:** Clarify that these are coordinate-axis phase-plane intersection speeds; vector phase velocity is $\sigma\vec k/|\vec k|^2$.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Chapter 1 already distinguishes the scalar coordinate speed from the true vector component.

### Printed page 130 — “aditional”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 130
- **Source:** “aditional”
- **Reconstruction:** “additional”
- **Reason/evidence:** Unambiguous spelling correction only.

### Printed page 131 — “plane wave sloution”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 131
- **Source:** “plane wave sloution”
- **Reconstruction:** “plane wave solution”
- **Reason/evidence:** Unambiguous spelling correction only.

### Printed page 131 — implicit zonal-wave restriction
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 131
- **Source:** “Thus, in a westward propagating wave,” followed by $u=-i\ell\psi=0$.
- **Proposed correction:** Add the qualifier $\ell=0$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** $u=0$ requires $\ell=0$.

### Printed page 131 — Rossby-wave group direction stated too generally
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 131
- **Source:** The text broadly states that a westward-going Rossby wave transmits energy eastward.
- **Proposed correction:** Restrict the statement to the relevant nearly/purely zonal short-wave geometry.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** $c_{gx}=\beta(k^2-\ell^2)/(k^2+\ell^2)^2$ can have either sign.

### Printed page 140 — “equations of motions”
- **Category:** `typographical`
- **Status:** `minor-typo-correction`
- **Location:** Chapter 5, printed page 140
- **Source:** “The equations of motions become”
- **Reconstruction:** “The equations of motion become”
- **Reason/evidence:** Unambiguous grammatical correction only.

### Printed page 141 — $f_0$ in the equatorial-validity sentence
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 141
- **Source:** After $f_0\to0$ and $f=\beta y$, the source says one cannot move to regions where “$f_0$ becomes large.”
- **Proposed correction:** Replace that occurrence by $f$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** $f_0$ is a constant reference value; $f=\beta y$ grows away from the equator.

### Printed page 142 — $m$ called a wavenumber
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 142
- **Source:** “For given wavenumbers $m$ and $k$ ...”
- **Proposed correction:** “For given mode number $m$ and wavenumber $k$ ...”
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** $m=0,1,2,\ldots$ is the discrete Hermite mode index.

### Printed page 142 — inconsistent constant-order high-wavenumber asymptotic
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 142
- **Source:** From $\omega^2-\lambda^2-\lambda/\omega=2m+1$, the source drops $\lambda/\omega$ but retains other $O(1)$ terms.
- **Proposed correction:** Retain consistent constant-order terms or state only the leading $\omega\sim\pm\lambda$ asymptote.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** If $s=\omega/\lambda\to\pm1$, then $\omega^2-\lambda^2\sim2m+1+1/s$.

### Printed page 146 — local meridional phase with variable wavenumber
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 146
- **Source:** $v=v_0(y)\exp[-i\sigma t+ikx+i\ell(y)y]$ while treating $\ell(y)$ as local meridional wavenumber.
- **Proposed correction:** Use $\exp[i\int^y\ell(y')\,dy']$.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Differentiating $\ell(y)y$ gives $\ell+y\ell_y$, not the assumed local wavenumber $\ell$.

### Printed pages 146--147 — ray direction identified with wavevector direction
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed pages 146--147
- **Source:** The ray path is defined by $dy/dx=\ell/k$ while retaining the $-\beta k/\sigma$ term in the local dispersion relation.
- **Proposed correction:** Use the group-velocity ray slope $2\ell/(2k+\beta/\sigma)$ and propagate that change consistently through the ray construction.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** Rays follow group velocity under the chapter's earlier ray-theory definition.

### Printed page 147 — turning coordinate written as $\theta_T$
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 5, printed page 147
- **Source:** $\pm\theta_T=\pm[(gD)^{1/2}k/\beta]\tan\theta_0$.
- **Proposed correction:** Write the turning coordinate as $y_T$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** With $\beta$ defined per unit meridional distance, the right side has dimensions of length.

## Chapter 6

### Printed page 159 — modal maximum differentiated at fixed cross-shelf wavenumber
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 6, printed page 159
- **Source:** The branch maximum is found from $\partial\sigma/\partial\ell=0$ treating $k$ as fixed, giving $\ell=-(k^2+b^2)^{1/2}$.
- **Proposed correction:** Differentiate along the matched modal branch $k=k_n(\ell)$, giving $k^2+b^2-\ell^2=2\ell k\,dk_n/d\ell$.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** The boundary condition $\tan(kL)=k/(\ell-b)$ constrains $k$ along each discrete branch.

### Printed pages 163--164 — condition on the short-wave coastal-trapped asymptote
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 6, printed pages 163--164
- **Source:** $\lim_{\ell\to-\infty}\omega=S\max[D_x]$, followed by the statement that if $S\max[D_x]>1$ the free subinertial branches reach $\omega=1$.
- **Proposed correction:** Qualify the asymptote to distinguish the $S\max[D_x]<1$ case from inertial cutoff.
- **Canonical reconstruction:** Follows the historical source pending human approval.
- **Reason/evidence:** If the formal estimate exceeds unity, the subinertial branch reaches the inertial limit first.

### Printed page 160 — “discrete frequencies” versus discrete cross-shelf modes
- **Category:** `editorial`
- **Status:** `pending-human-approval`
- **Location:** Chapter 6, printed page 160
- **Source:** “continental shelf waves occur at discrete frequencies whereas Rossby waves form a continuum”.
- **Proposed correction:** “continental shelf waves have discrete cross-shelf modes whereas unbounded Rossby waves form a continuum”.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Alongshore wavenumber remains continuous and each mode has a dispersion branch $\sigma_n(\ell)$.

### Printed page 167 — sign of the strong-stratification Kelvin-wave limit
- **Category:** `equation`
- **Status:** `pending-human-approval`
- **Location:** Chapter 6, printed page 167
- **Source:** $\omega=S\ell/(n\pi)$ with $n=1,2,\ldots$.
- **Proposed correction:** $\omega=-S\ell/(n\pi)$ under the preceding $\ell<0$ positive-frequency convention.
- **Canonical reconstruction:** Restored to the historical source pending human approval.
- **Reason/evidence:** Applying the displayed surface condition gives the proposed sign for positive mode labels, but the source form is unambiguous.

## References

### Printed page 172 — Bjerknes title spelling
- **Category:** `reference`
- **Status:** `minor-typo-correction`
- **Location:** References, printed page 172
- **Source:** “Die Theorie der Aussertropischen Zyklonenbuildung.”
- **Reconstruction:** “Die Theorie der Aussertropischen Zyklonenbildung.”
- **Reason/evidence:** Unambiguous spelling correction of `Zyklonenbildung`; no scientific or bibliographic identity changes.
