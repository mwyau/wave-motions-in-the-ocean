from pathlib import Path

p = Path('reconstruction/chapter1.tex')
s = p.read_text()
repls = [
(''' +\\tan^{-1}\\frac{\\Im A}{\\Re A}\\right)\n\\]\nwhere $\\Im$ refers to the imaginary part of the expression.''', ''' +\\arg A\\right)\n\\]\nwhere $\\arg A$ denotes the complex argument of $A$.'''),
('''The speed at which phase planes move along $\\vec{k}$ is the \\emph{phase speed}\n\\begin{waveequation}\n c=\\sigma/|\\vec{k}|=\\lambda/T.\n\\end{waveequation}\nIt is directed along $\\vec{k}$.''', '''The speed at which phase planes move normal to themselves is the \\emph{phase speed}\n\\begin{waveequation}\n c=\\sigma/|\\vec{k}|=\\lambda/T.\n\\end{waveequation}\nFor the stated $\\sigma>0$ convention the associated normal phase-velocity vector is\n$\\vec c_p=c\\,\\hat{\\vec k}=\\sigma\\vec k/|\\vec k|^2$.'''),
('''in which the amplitude $a$ and the phase $\\Theta$ are slowly varying functions of\n$\\vec{x}$ and $t$; i.e., they vary with the large space and time scales of the medium or\nof the wave groups''', '''in which the amplitude $a$ and the local wave parameters vary slowly, while the phase\n$\\Theta$ itself varies on the wave scale. More precisely, $a$ and the derivatives of\n$\\Theta$ change with the large space and time scales of the medium or of the wave groups'''),
('''partial derivatives are carried out keeping the other coordinate constant. Thus,\n$\\Delta a/a\\ll1$ and $\\Delta\\Theta/\\Theta\\ll1$ over $|\\vec{k}|^{-1}$ and $N^{-1}$.''', '''partial derivatives are carried out keeping the other coordinate constant. The WKB\nassumption is that $a$, $\\vec{k}$, and $N$ change only by small fractions over local\ndistances and times of order $|\\vec{k}|^{-1}$ and $|N|^{-1}$; $\\Theta$ itself need not\nvary slowly.'''),
]
for old,new in repls:
    if s.count(old) != 1:
        raise SystemExit(f'chapter1 matcher count {s.count(old)} for {old[:40]!r}')
    s=s.replace(old,new)
p.write_text(s)

e = Path('reconstruction/ERRATA.md')
t = e.read_text()
def section(title, body):
    global t
    marker='### '+title+'\n'
    i=t.index(marker)
    j=t.find('\n### ', i+len(marker))
    if j < 0: j=t.find('\n## ', i+len(marker))
    if j < 0: raise SystemExit(title)
    t=t[:i]+body.rstrip()+'\n'+t[j:]
section('Printed page 3 — complex-amplitude phase from a one-argument arctangent', r'''### Printed page 3 — complex-amplitude phase from a one-argument arctangent

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 1, printed page 3
- **Original:** The historical source writes the phase of a complex amplitude as
  $\tan^{-1}(\operatorname{Im}A/\operatorname{Re}A)$.
- **Reconstruction:** The phase is written as $\arg A$.
- **Reason/evidence:** A one-argument arctangent loses quadrant information and is undefined
  when $\operatorname{Re}A=0$. The complex argument preserves the quadrant and is defined
  with the usual branch convention. Direct inspection of physical page 13 confirms the
  one-argument arctangent is present in the 1989 source.''')
section('Printed page 4 — scalar phase speed described as directed', r'''### Printed page 4 — scalar phase speed described as directed

- **Category:** `editorial`
- **Status:** `accepted`
- **Location:** Chapter 1, printed page 4
- **Original:** After defining the scalar phase speed $c=\sigma/|\vec k|=\lambda/T$,
  the historical source says, “It is directed along $\vec k$.”
- **Reconstruction:** The text identifies $c$ as the normal phase speed and, for the
  stated $\sigma>0$ convention, gives the associated phase-velocity vector
  $\vec c_p=c\hat{\vec k}=\sigma\vec k/|\vec k|^2$.
- **Reason/evidence:** A scalar speed has no direction; direction belongs to the velocity
  vector. This distinction also preserves the following discussion that $\sigma/k$ is
  the speed at which a phase plane intersects the $x$ axis, not a vector component.
  Direct inspection of physical page 14 confirms the historical wording.''')
section('Printed pages 11--12 — WKB scale separation of phase and amplitude', r'''### Printed pages 11--12 — WKB scale separation of phase and amplitude

- **Category:** `equation`
- **Status:** `accepted`
- **Location:** Chapter 1, printed pages 11--12
- **Original:** The historical source says both the amplitude $a$ and phase $\Theta$ are
  slowly varying and states $\Delta\Theta/\Theta\ll1$ over a local wave scale.
- **Reconstruction:** The amplitude and local wave parameters are stated to vary slowly,
  while the phase itself varies on the wave scale. The small-variation condition is
  applied to $a$, $\vec k=\nabla\Theta$, and $N=-\Theta_t$, not to
  $\Delta\Theta/\Theta$.
- **Reason/evidence:** WKB scale separation requires the envelope and local phase gradients
  to vary on the medium scale while the phase accumulates on the wavelength/time scale.
  Moreover, $\Theta$ is arbitrary up to an additive constant, so a fractional criterion
  $\Delta\Theta/\Theta$ is not invariant. Direct inspection of physical pages 21--22
  confirms the historical wording and criterion.''')
e.write_text(t)
