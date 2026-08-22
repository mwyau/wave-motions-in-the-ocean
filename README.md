# Wave Motions in the Ocean: Myrl’s View

*Presented to* **Myrl C. Hendershott**

**David C. Chapman and Paola Malanotte-Rizzoli** — August 1989

Edited by **Albert M. W. Yau** — August 2026

<!-- README_BADGES_START -->
[![Read Online](https://img.shields.io/badge/Read-Online-0969da)](https://mwyau.github.io/wave-motions-in-the-ocean/)
[![Read PDF](https://img.shields.io/badge/Read-PDF-b31b1b)](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf)
[![Read EPUB](https://img.shields.io/badge/Read-EPUB-2da44e)](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.epub)
[![BY-NC-SA 4.0](https://img.shields.io/badge/-BY--NC--SA%204.0-ED592F?logo=creativecommons&logoColor=white&labelColor=333333)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Publish](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/mwyau/wave-motions-in-the-ocean/actions/workflows/publish.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22059881.svg)](https://doi.org/10.5281/zenodo.22059881)
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

- like him, I put $`\ell`$ ($`x`$ wavenumber) before $`k`$ ($`y`$ wavenumber)

As the letters $`j,k,x,y,w`$ do not exist in the Italian alphabet, $`k`$ coming before or after
$`\ell`$ was supremely unimportant to me. On the positive side, Myrl was absolutely the
best teacher I had in the various courses I took at Scripps. His lectures were always
interesting, imaginative and full of physical insight. Looking back, I realize that a
great deal of the important oceanographic concepts and ideas I learned over the years
go back to my long association with Myrl as teacher, advisor, colleague and, last but
not least, dear friend. I hope I absorbed from him some of the positive qualities too.

*Woods Hole — Paola Malanotte-Rizzoli, 1989*

## Editor’s note

I created this digital edition of *Wave Motions in the Ocean: Myrl’s View* as a
tribute to my dear advisor and mentor, Myrl C. Hendershott. Myrl’s guidance and
encouragement during my time working with him at Scripps and Coastal Environments
have had a lasting influence on me. I hope this edition, available in PDF, EPUB, and
online, will help future Physical Oceanography students for years to come.

The original notes have been passed from hand to hand, xeroxed many times, and eventually
preserved in scanned form on James Pringle’s website. This edition reconstructs the 1989
notes in modern LaTeX, with figures redrawn in vector format where possible.

Paola Malanotte-Rizzoli has authorized this digital edition for release under the
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
license (CC BY-NC-SA 4.0).

This edition is set in STIX Two for text and mathematics, with Source Sans 3 for headings
and other structural text. Both typefaces are used under the SIL Open Font License 1.1.

The front cover features Katsushika Hokusai’s *Under the Wave off Kanagawa
(The Great Wave)*, ca. 1830–32, and the back cover features Utagawa Hiroshige’s
*Naruto Whirlpool, Awa Province*, ca. 1853, both from The Metropolitan Museum
of Art’s Open Access collection. Both artworks are in the public domain; the images are
provided under CC0.

The reconstruction is a work in progress, with assistance from OpenAI’s GPT-5.6 Sol
and Luna.

*Stony Brook — Albert M. W. Yau, 2026*

<figure>
<img src="src/figures/frontmatter/salmon-hendershott-como-1980.jpg" width="420" />
<p>Rick Salmon (left) and Myrl Hendershott at Villa Carlotta, Lake Como,
during the International School of Physics “Enrico Fermi,” Course LXXX,
<em>Topics in Ocean Physics</em>, July 1980.</p>
</figure>

## Read and download

- [HTML](https://mwyau.github.io/wave-motions-in-the-ocean/)
- [PDF](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.pdf)
- [EPUB](https://mwyau.github.io/wave-motions-in-the-ocean/wave-motions.epub)

Contact: [albert@mwyau.com](mailto:albert@mwyau.com)

This work is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" width="16" height="16"> <img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" width="16" height="16">
