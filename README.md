# Wave Motions in the Ocean: Myrl's View

This repository reconstructs the 1989 lecture notes **Wave Motions in the Ocean: Myrl's View**, by David C. Chapman and Paola Malanotte-Rizzoli. Chapman and Malanotte-Rizzoli explain in the original prefaces that the notes grew from wave courses they took from Myrl C. Hendershott at Scripps and were assembled as a tribute to him.

The original five scanned PDFs were distributed by James Pringle at `https://oxbow.sr.unh.edu/ChapmanRizzoli/Wave_Motions_in_the_Ocean.html`. They are committed unchanged under `source/` and remain the historical authority for the reconstruction.

Paola Malanotte-Rizzoli has authorized editing, modernization, and release of the notes. The reconstructed work is licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**; see `LICENSE`.

## Editions

The repository has one canonical body (`chapter1.tex`--`chapter6.tex`) and one bibliography (`references.bib`). It produces:

- **Facsimile edition** — reconstructed LaTeX with source-compatible page boundaries and typography tuned toward the 1989 notes.
- **Modern edition** — the same content with modern typography, continuous pagination, generated table of contents, editor material, and more comfortable spacing.
- **Modern HTML edition** — generated from the same LaTeX source for GitHub Pages. EPUB is a later goal.

The two PDF entry points are `reconstruction/main-facsimile.tex` and `reconstruction/main-modern.tex`.

## Build locally

Requirements include a working TeX installation with `latexmk` and BibTeX, Pandoc, Poppler (`pdfinfo`, `pdftoppm`, `pdftotext`, `pdftocairo`), Python 3 with Pillow, and preferably `qpdf`. HTML is generated from temporary compatibility transforms of the same canonical LaTeX; no HTML prose is maintained separately.

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh all
```

Outputs are written only under `dist/`:

```text
dist/
├── wave-motions-1989-facsimile.pdf
├── wave-motions-1989-modern.pdf
└── html/
    ├── index.html
    ├── chapter1.html
    ├── ...
    └── references.html
```

Use `python scripts/compare-figures.py <figure-name>` or `--all` to regenerate temporary source/reconstruction comparisons under `build/comparisons/`.

## Reconstruction policy

Source scans are not rewritten to sound modern. Text fidelity, equation transcription, scientific correctness, and figure meaning are audited separately. Clear corrections and editorial changes are recorded in `reconstruction/ERRATA.md`; figure provenance and reconstruction decisions are recorded in `reconstruction/FIGURE_AUDIT.md`; ongoing audit coverage and future work are tracked in `reconstruction/PLAN.md`.

Generated PDFs and Pages output are not committed. Pull-request/manual CI exposes build artifacts; `main` deploys the current HTML edition and both PDFs to GitHub Pages. Versioned release assets can be added later after the reconstruction is stable.
