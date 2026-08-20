# Wave Motions in the Ocean: Myrl's View

*Presented to* **Myrl C. Hendershott**

**David C. Chapman and Paola Malanotte-Rizzoli** — August 1989

Digital edition by **Albert M. W. Yau** — August 2026

<!-- README_BADGES_START -->
[![Read Online](https://img.shields.io/badge/Read-Online-0969da)](https://mwyau.github.io/wave-motions-in-the-ocean/) [![Read PDF](https://img.shields.io/badge/Read-PDF-b31b1b)](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf) [![Read EPUB](https://img.shields.io/badge/Read-EPUB-85b916)](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.epub) [![CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-3c5c99)](https://creativecommons.org/licenses/by-nc-sa/4.0/) [![Publish](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml)
<!-- README_BADGES_END -->

## Preface — David C. Chapman

When I volunteered to teach the MIT/WHOI Joint Program core course on
“Wave Motions in the Ocean and Atmosphere” in Spring 1989, I naturally turned for
guidance to the notes I had acquired from a similar course taken while a student at
Scripps Institution of Oceanography. In an attempt to broaden the scope of the course,
I borrowed a set of notes from Paola Malanotte-Rizzoli who taught the MIT/WHOI
core course from 1983-1985. It didn’t take long to recognize that Paola’s notes were
nearly identical to mine because she had also based hers on the waves course she had
taken at Scripps. In both cases, the Scripps course was taught by our former advisor
Myrl Hendershott, which means that at least two generations of Physical
Oceanography students have learned the “Hendershott view” of waves. Considering
the seemingly timeless nature of the concepts presented in Myrl’s course as well as the
profound influence Myrl has had on Paola and myself through both his teaching and
his advising, we decided to compile these notes into a form which could be distributed
to students and, at the same time, serve as a tribute to Myrl. Thus, with the exception
of some minor modifications, additions and deletions that Paola and I have made, the
notes contained herein are those developed by Myrl for his course. We hope that these
notes will be as clear and as useful to future readers as they have been to us.

*Woods Hole — David C. Chapman, 1989*

## Preface — Paola Malanotte-Rizzoli

These notes have been collected and assembled in different ways over the years
by two people successively, Paola Malanotte-Rizzoli and Dave Chapman. The present
and chronologically latest version has been put together by Dave and constitutes the
bulk of the waves course he taught in Spring 1989. When I taught the course during
the years 1983-85, the chapter on acoustic waves was absent. I had instead a section on
the Garrett and Munk spectrum and a chapter on nonlinear wave interactions. These
differences reflect the different years in which Dave and I took the waves course at
Scripps Institution of Oceanography from our former advisor Professor Myrl C.
Hendershott and the modifications that Myrl had made in his course in successive
years. Thus the inspirational source or, rather, the actual bulk of these notes is the
waves course taught by Myrl at Scripps.

Myrl Hendershott has been at W.H.O.I. this summer as Principal Lecturer of
the GFD Summer School on Ocean Circulation. This opportunity, plus Dave
Chapman’s diligence and patience in typing the notes on his word processor together
with formulas and equations (the latter were handwritten in my own set of notes), has
motivated us to produce this report as an homage to Myrl. Without him, we would
both have had a much harder and more time-consuming role in putting together a
decent course on waves. More importantly, Myrl is in many ways responsible for
whatever success we have had in the field of Oceanography.

I must add here a personal note. Hearing Myrl again as a teacher this summer
after so many years, I have realized how much he has influenced my way of thinking
and teaching. On the not-so-positive side (I will not say negative):

- like him, I “scribble” a lot on the blackboard.

- like him, I erase with my left hand what I have just written with my right hand.

- like him, I put $\ell$ ($x$ wavenumber) before $k$ ($y$ wavenumber)

As the letters $j,k,x,y,w$ do not exist in the Italian alphabet, $k$ coming before or after
$\ell$ was supremely unimportant to me. On the positive side, Myrl was absolutely the
best teacher I had in the various courses I took at Scripps. His lectures were always
interesting, imaginative and full of physical insight. Looking back, I realize that a
great deal of the important oceanographic concepts and ideas I learned over the years
go back to my long association with Myrl as teacher, advisor, colleague and, last but
not least, dear friend. I hope I absorbed from him some of the positive qualities too.

*Woods Hole — Paola Malanotte-Rizzoli, 1989*

## Editor’s note

These lecture notes have been preserved on James Pringle’s website and have
recently been reconstructed in LaTeX. This digital edition has been
authorized by Paola Malanotte-Rizzoli for release under the Creative Commons
Attribution–NonCommercial–ShareAlike 4.0 International license
(CC BY-NC-SA 4.0).

The reconstruction is still a work in progress.

*Stony Brook — Albert M. W. Yau, 2026*

<figure>
<img src="reconstruction/figures/frontmatter/salmon-hendershott-como-1980.jpeg" />
<p>Rick Salmon (left) and Myrl Hendershott at Villa Carlotta, Lake Como,
during the International School of Physics “Enrico Fermi,” Course LXXX,
<em>Topics in Ocean Physics</em>, July 1980.</p>
</figure>

## Contents

1. [Basic concepts](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html)
   - [Plane waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html#plane-waves)
   - [The dispersion relation](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html#the-dispersion-relation)
   - [Linear superposition of plane waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html#linear-superposition-of-plane-waves)
   - [The method of stationary phase: Group velocity](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html#the-method-of-stationary-phase-group-velocity)
   - [Waves in slowly varying media: Ray theory](https://mwyau.github.io/wave-motions-in-the-ocean/chapter1.html#waves-in-slowly-varying-media-ray-theory)
2. [Acoustic waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html)
   - [Basic physics](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#basic-physics)
   - [Plane waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#plane-waves)
   - [Reflection at a solid boundary](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#reflection-at-a-solid-boundary)
   - [Plane waves in a channel](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#plane-waves-in-a-channel)
   - [Scattering at a discontinuity](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#scattering-at-a-discontinuity)
   - [Generation of plane waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#generation-of-plane-waves)
   - [Slowly varying medium](https://mwyau.github.io/wave-motions-in-the-ocean/chapter2.html#slowly-varying-medium)
3. [Surface gravity waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html)
   - [Homogeneous medium](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#homogeneous-medium)
   - [Linear solutions](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#linear-solutions)
   - [Internal waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#internal-waves)
   - [Qualitative retreatment of surface waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#qualitative-retreatment-of-surface-waves)
   - [Careful retreatment of surface waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#careful-retreatment-of-surface-waves)
   - [An initial value problem](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#an-initial-value-problem)
   - [Ship waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#ship-waves)
   - [A wave energy equation](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#a-wave-energy-equation)
   - [Slowly varying medium](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#slowly-varying-medium)
   - [Waves riding on a current](https://mwyau.github.io/wave-motions-in-the-ocean/chapter3.html#waves-riding-on-a-current)
4. [Internal gravity waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html)
   - [The internal wave equation](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#the-internal-wave-equation)
   - [Unbounded, rotating, stratified fluid](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#unbounded-rotating-stratified-fluid)
   - [Waveguide modes](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#waveguide-modes)
   - [Generation at a horizontal boundary](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#generation-at-a-horizontal-boundary)
   - [Reflection from a solid boundary](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#reflection-from-a-solid-boundary)
   - [Variable buoyancy frequency](https://mwyau.github.io/wave-motions-in-the-ocean/chapter4.html#variable-buoyancy-frequency)
5. [Shallow water dynamics](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html)
   - [Laplace's tidal equations](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#laplaces-tidal-equations)
   - [Shallow water equations with rotation](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#shallow-water-equations-with-rotation)
   - [Reflection at a solid wall](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#reflection-at-a-solid-wall)
   - [Seiches in a box](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#seiches-in-a-box)
   - [Propagation over a step](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#propagation-over-a-step)
   - [Edge waves and coastal seiches](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#edge-waves-and-coastal-seiches)
   - [Sverdrup and Poincaré waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#sverdrup-and-poincare-waves)
   - [Kelvin waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#kelvin-waves)
   - [Waveguide modes](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#waveguide-modes)
   - [Kelvin wave reflection](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#kelvin-wave-reflection)
   - [Rossby and planetary waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#rossby-and-planetary-waves)
   - [Rossby wave reflection](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#rossby-wave-reflection)
   - [Western boundary current formation](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#western-boundary-current-formation)
   - [Equatorial waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter5.html#equatorial-waves)
6. [Topographic effects](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html)
   - [Topographic Rossby waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html#topographic-rossby-waves)
   - [Bottom-trapped waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html#bottom-trapped-waves)
   - [Continental shelf waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html#continental-shelf-waves)
   - [Coastal-trapped waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html#coastal-trapped-waves)
   - [Wind-forced, long waves](https://mwyau.github.io/wave-motions-in-the-ocean/chapter6.html#wind-forced-long-waves)

[References](https://mwyau.github.io/wave-motions-in-the-ocean/references.html)

## Downloads

- [PDF](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf)
- [Facsimile PDF](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions-facsimile.pdf)
- [EPUB](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.epub)

This work is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" width="16" height="16">
