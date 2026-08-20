# Publication skill

Use this skill for modern/facsimile presentation, front matter, README/HTML synchronization, EPUB, build outputs, and GitHub Pages/CI.

## Canonical publication sources

- Shared modern PDF/EPUB cover: `reconstruction/cover-modern.tex`
- Modern front matter: `reconstruction/frontmatter-modern.tex`
- Facsimile front matter: `reconstruction/frontmatter-facsimile.tex`
- Shared body: `reconstruction/chapter1.tex` … `chapter6.tex`
- Bibliography: `reconstruction/references.bib`

README, HTML, and EPUB are generated publication views; none is a separate prose source.

## Modern cover and front matter

The modern PDF and EPUB use the **same cover design**. The cover is generated from `cover-modern.tex`; EPUB rasterizes that exact TeX cover rather than maintaining a second cover source.

Cover invariants:

1. `WAVE MOTIONS IN THE OCEAN` is dominant, very large, dark ocean blue.
2. `Myrl's View` is an italic subtitle at roughly half the title's visual size.
3. The full rectangular Met image of Hokusai's *Under the Wave off Kanagawa* is reproduced without color correction and with only a thin frame.
4. `Presented to Myrl C. Hendershott` appears **below the image and above the authors**.
5. **David C. Chapman and Paola Malanotte-Rizzoli** appear prominently on two lines.
6. Do not put years, the digital editor's name, license marks, museum credit, or badges on the front cover.

The cover text/frame color `#213E5E` is derived from the dark blue in the supplied Met image; the cover paper is warm ivory `#FBF7EC`.

The Met image is committed as `reconstruction/figures/frontmatter/great-wave-met-dp130155.jpg`. Preserve it as the source image; do not color-correct, crop away the original composition, or replace it with AI-generated art. Keep the full scholarly attribution in the Editor's note.

The generated web/README title block may continue to state original/digital dates and the digital editor even though those details are deliberately absent from the front cover. In `frontmatter-modern.tex`, `wavepdfonly` contains the modern cover and `wavewebonly` retains the web/README title metadata. Do not let the two branches diverge in authorship/title facts.

The Editor's note keeps `\wavesignature{Albert M. W. Yau}{Stony Brook}{2026}`, while its contents entry is simply `Editor's note`.

The modern cover page is unnumbered. Front matter then uses lower-case Roman numerals starting at `i`; Chapter 1 resets to Arabic `1`. Modern contents use Chapter → Section only (`tocdepth=1`).

Keep the CC BY-NC-SA 4.0 statement in the Editor's note. The cover-image attribution belongs on the Editor's-note page, not on the front cover.

The historical Lake Como photograph remains unnumbered and uses the established caption identifying Rick Salmon (left) and Myrl Hendershott at Villa Carlotta during the International School of Physics “Enrico Fermi,” Course LXXX, *Topics in Ocean Physics*, July 1980. Do not add unsupported photographer attribution or apply speculative color correction.

## README and HTML synchronization

`scripts/book_views.py` derives chapter titles, `\section{}` headings, Contents, Downloads, and license presentation. `scripts/sync-views.py` applies that model.

README and `index.html` must have the same substantive front matter/publication navigation except:

- README uses absolute Pages URLs; HTML uses relative URLs.
- README alone has the Shields badge row.
- HTML has web navigation/theme controls.

Shared Downloads are:

- `wave-motions.pdf` — PDF
- `wave-motions-facsimile.pdf` — Facsimile PDF
- `wave-motions.epub` — EPUB

README badges are **Read | Online**, **Read | PDF**, **Read | EPUB**, **License | CC BY-NC-SA 4.0**, and **Build | status**. Keep the badge row after the complete title/dedication/authorship block. Do not add a facsimile badge unless explicitly requested.

Section anchors are public links; keep them stable.

## HTML

Preserve the responsive/mobile reader, Auto/Light/Dark theme selection, Source navigation, wide-math/table overflow handling, and stable chapter/section navigation unless explicitly redesigned.

Do not dark-mode invert/filter the historical front-matter JPEG. Generated black-on-white scientific diagrams may be theme-adjusted for legibility.

The HTML edition is the browser reading/preview experience.

## EPUB

Build EPUB from the transformed canonical LaTeX prepared by the HTML pipeline, not by reparsing MathJax HTML. This preserves mathematical structure for MathML output and avoids a parallel content tree.

The EPUB metadata title must remain `Wave Motions in the Ocean: Myrl's View`, with David C. Chapman and Paola Malanotte-Rizzoli as authors and Albert M. W. Yau identified as digital editor/contributor. Validation must confirm package metadata and the presence of MathML.

EPUB TOC depth is Chapter → Section. Check metadata, shared cover, navigation, math, figures, tables, links, and reflow in representative readers as iteration proceeds.

Publish EPUB as a direct download. Browsers do not provide a consistent native EPUB reader, and the existing HTML edition already serves the web-reading use case. Do not add epub.js or another embedded EPUB reader unless explicitly requested.

## Build interface and outputs

Use:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh epub
./scripts/build.sh all
```

The flat `dist/` publish root contains:

```text
dist/
  index.html
  chapter1.html ... chapter6.html
  references.html
  assets/
  wave-motions.pdf
  wave-motions-facsimile.pdf
  wave-motions.epub
```

`build/` and `dist/` are generated and untracked.

Before committing a canonical front-matter or heading change, regenerate the README:

```bash
python3 scripts/sync-views.py --readme
```

A full validation is `./scripts/build.sh all`.

## Pages and CI

`.github/workflows/pages.yml` builds the full publication and deploys `dist/` as the Pages root. Keep `cancel-in-progress: false` for the production Pages concurrency group. A superseded deployment is not equivalent to a build failure; the README Build badge tracks the build check.

CI must verify `index.html` plus all three downloadable formats. Keep `tex-packages.txt` at repository root as the TeX dependency manifest.
