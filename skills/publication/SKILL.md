# Publication skill

Use this skill for modern/facsimile presentation, front matter, README/HTML synchronization, EPUB, builds, and GitHub Pages/CI.

## Canonical publication sources

- Shared modern PDF/EPUB cover: `reconstruction/cover-modern.tex`
- Modern front matter: `reconstruction/frontmatter-modern.tex`
- PDF-only modern book preliminaries: `reconstruction/frontmatter-modern-book.tex`
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

The Met image is committed as `reconstruction/figures/frontmatter/great-wave-met-dp130155.jpg`. Preserve it as the source image; do not color-correct, crop away the original composition, or replace it with AI-generated art.

The paged modern PDF uses conventional book preliminaries after the exterior cover:

1. half-title,
2. Lake Como frontispiece,
3. full title page,
4. copyright / edition-notice verso,
5. Contents,
6. Preface — David C. Chapman,
7. Preface — Paola Malanotte-Rizzoli,
8. Editor's note,
9. Chapter 1.

`frontmatter-modern-book.tex` owns that PDF-only sequence. The half-title, frontispiece, title, and edition-notice leaves are counted as Roman preliminary pages but suppress their folios; Contents is the first visibly numbered preliminary page and begins at **v**. Chapter 1 resets to Arabic page `1`.

On modern page iii, keep the digital-editor credit at the bottom of the title page. Use the same serif family as the author line, but smaller/lower prominence so Albert M. W. Yau does not read as a third author. Keep the credit concise: `Digital edition by Albert M. W. Yau, August 2026.`

The edition-notice verso lists the original authors and presentation date, digital editor and date, the authorized CC BY-NC-SA 4.0 release, the original source scan, and the concise Hokusai cover credit. Do not assert that the digital editor owns copyright in the original lecture notes. Keep this page bibliographic/legal rather than repeating the GPT assistance statement there.

Use plain publication wording in reader-facing text. Prefer `Digital edition by` to `Digital edition prepared by` and `original source scan` to `historical source scan`. Avoid inflated words such as `provenance` when a simpler phrase is equally precise.

The generated web/README title block may continue to state original/digital dates and the digital editor even though those details are deliberately absent from the front cover. In `frontmatter-modern.tex`, `wavepdfonly` selects the paged book preliminaries and `wavewebonly` retains the web/README title metadata. Do not let the two branches diverge in authorship/title facts.

The Editor's note keeps `\wavesignature{Albert M. W. Yau}{Stony Brook}{2026}`, while its contents entry is simply `Editor's note`. Keep the CC BY-NC-SA 4.0 statement and the brief GPT-5.6 Sol reconstruction-assistance sentence in the Editor's note.

The concise Hokusai cover credit belongs on the PDF edition-notice verso. The EPUB builder expands the same credit marker in its flowing front matter because the EPUB includes the shared Hokusai cover. README and HTML may omit the cover credit because they do not display that cover.

The historical Lake Como photograph is the modern PDF **frontispiece**, unnumbered, with the established caption identifying Rick Salmon (left) and Myrl Hendershott at Villa Carlotta during the International School of Physics “Enrico Fermi,” Course LXXX, *Topics in Ocean Physics*, July 1980. In flowing README/HTML/EPUB output, retain the same photograph with the Editor's note rather than forcing print page geometry into a reflowable format. Preserve the committed JPEG as the source image; do not add unsupported photographer attribution such as “Photograph by George,” perform speculative color correction, generatively reconstruct faces/details, or replace it with an AI-generated image.

Modern contents use Chapter → Section only (`tocdepth=1`).

## Facsimile PDF

The facsimile is a source-page edition, not merely the modern text with old-style fonts. Preserve the **184 physical-page** structure and the historical printed page numbers.

`styles/wave-facsimile.sty` intentionally uses a larger 12 pt body font and stretchable leading. The minimum baseline is compact enough for dense historical pages, while sparse pages may stretch substantially so the reconstructed text occupies the page vertically like the scans instead of collecting at the top. Keep `\flushbottom` and source-page `\pagebreak[4]` behavior together; replacing those breaks with `\newpage` or `\clearpage` defeats the vertical justification by inserting bottom fill.

Historical fragment-level `\setcounter{page}{...}` resets are also source-page boundaries when encountered after material has begun. The facsimile style enforces that boundary before resetting the printed page number so separately reconstructed fragments cannot merge two original pages.

When changing facsimile typography, validate the components as well as the full build: front matter = 10 pages, Chapters 1–6 = 17 + 20 + 26 + 32 + 53 + 23 = 171 pages, references = 3 pages, total = 184. Do not accept overfull vertical boxes as a way to preserve the count.

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

README badges are **Read | Online**, **Read | PDF**, **Read | EPUB**, **License | CC BY-NC-SA 4.0**, and the native GitHub Actions **Publish** status badge for `.github/workflows/publish.yml`. Keep the badge row after the complete title/dedication/authorship block. Do not add a facsimile badge unless explicitly requested.

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

## Publish workflow

`.github/workflows/publish.yml` is the single canonical publication workflow. It builds and validates the complete publication for pushes to `main`, pull requests targeting `main`, and manual runs. Deployment to GitHub Pages occurs only for `main`; PRs and manual runs from other branches build and validate without deploying.

The canonical `Publish` workflow must be reproducible from the triggering commit and must not edit tracked source files, create commits, or push repository changes. Do not append chat/session migrations, one-time cleanup scripts, or other repository-mutating automation to it. If a task genuinely requires GitHub Actions to modify tracked repository contents, create a separate purpose-specific workflow and remove it after the task unless the owner explicitly wants it retained.

Keep `cancel-in-progress: false` for production publishing so an active deployment is not interrupted by a newer push. CI must verify `index.html` plus all three downloadable formats. Keep `tex-packages.txt` at repository root as the TeX dependency manifest.
