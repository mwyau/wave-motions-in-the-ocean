# Publication skill

Use this skill for modern/facsimile presentation, front matter, README/HTML synchronization, EPUB, build outputs, and GitHub Pages/CI.

## Canonical publication sources

- Modern front matter: `reconstruction/frontmatter-modern.tex`
- Facsimile front matter: `reconstruction/frontmatter-facsimile.tex`
- Shared body: `reconstruction/chapter1.tex` … `chapter6.tex`
- Bibliography: `reconstruction/references.bib`

README, HTML, and EPUB are generated publication views; none is a separate prose source.

## Modern front matter

Preserve this hierarchy unless explicitly redesigned:

1. `WAVE MOTIONS IN THE OCEAN` is dominant.
2. `Myrl's View` is a substantial italic subtitle.
3. `Presented to` **Myrl C. Hendershott** is a distinct dedication block.
4. **David C. Chapman and Paola Malanotte-Rizzoli** are the original authors; `August 1989` is a separate regular-weight line.
5. `Digital edition by` **Albert M. W. Yau** is smaller and clearly separated; `August 2026` is a separate regular-weight line.

Do not make the digital editor look like a third author. The Editor's note keeps `\wavesignature{Albert M. W. Yau}{Stony Brook}{2026}`, while its contents entry is simply `Editor's note`.

The modern title page is unnumbered. Front matter then uses lower-case Roman numerals starting at `i`; Chapter 1 resets to Arabic `1`. Modern contents use Chapter → Section only (`tocdepth=1`).

Keep the CC BY-NC-SA 4.0 statement in the Editor's note. Do not add a CC badge/logo/raw URL to the PDF or EPUB cover merely for branding.

The historical Lake Como photograph remains unnumbered and uses the established caption identifying Rick Salmon (left) and Myrl Hendershott at Villa Carlotta during the International School of Physics “Enrico Fermi,” Course LXXX, *Topics in Ocean Physics*, July 1980. Do not add unsupported photographer attribution.

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

README badges are **Read | Online**, **Read | PDF**, **Read | EPUB**, **License | CC BY-NC-SA 4.0**, and **Build | status**. Keep the badge row after the complete title/dedication/authorship block so it does not interrupt the book attribution hierarchy. Do not add a facsimile badge unless explicitly requested.

Section anchors are public links; keep them stable.

## HTML

Preserve the responsive/mobile reader, Auto/Light/Dark theme selection, Source navigation, wide-math/table overflow handling, and stable chapter/section navigation unless explicitly redesigned.

Do not dark-mode invert/filter the historical front-matter JPEG. Generated black-on-white scientific diagrams may be theme-adjusted for legibility.

The HTML edition is the browser reading/preview experience.

## EPUB

The EPUB is reflowable and generated from the same canonical material, using the transformed HTML/assets pipeline rather than a parallel content tree.

Use the dedicated EPUB cover source `reconstruction/figures/frontmatter/epub-cover.svg`. It should match the modern edition's restrained visual language while being legible as an e-reader thumbnail; do not use a screenshot of the PDF title page. Rasterize the committed SVG during the build for broad reader compatibility.

Keep original authors prominent and the digital-editor role secondary. Do not put CC logos/badges on the cover.

EPUB TOC depth is Chapter → Section. Check metadata, cover, navigation, math, figures, tables, links, and reflow in representative readers as iteration proceeds.

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
