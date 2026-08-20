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

While figure/vector geometry is still changing, canonical CI may report facsimile page-count drift as a **warning** so otherwise-valid publication builds can complete. This does not relax the final publication requirement: before release, restore and verify the exact 184-page source-compatible structure. A stable release tag must fail rather than warn if the facsimile is not exactly 184 pages.

## README and HTML synchronization

`scripts/book_views.py` derives chapter titles, `\section{}` headings, Contents, Downloads, source links, and license presentation. `scripts/sync-views.py` applies that model.

README and `index.html` must have the same substantive front matter/publication navigation except:

- README uses absolute Pages URLs; HTML uses relative URLs.
- README alone has the Shields badge row.
- HTML has web navigation/theme controls.

Link `https://oxbow.sr.unh.edu/ChapmanRizzoli/Wave_Motions_in_the_Ocean.html` as **Original online source** in README and HTML only. It is web navigation/reference material, not part of the reconstructed book; do not add it to either PDF or the EPUB unless the owner requests it.

Shared Downloads are:

- `wave-motions.pdf` — PDF
- `wave-motions-facsimile.pdf` — Facsimile PDF
- `wave-motions.epub` — EPUB

README badges are **Read | Online**, **Read | PDF**, **Read | EPUB**, **License | CC BY-NC-SA 4.0**, and the native GitHub Actions **Build** status badge for `.github/workflows/publish.yml`. Keep the badge row after the complete title/dedication/authorship block. Do not add a facsimile badge unless explicitly requested.

Section anchors are public links; keep them stable.

## HTML

Preserve the responsive/mobile reader, Auto/Light/Dark theme selection, **GitHub Source** navigation, Contents navigation, wide-math/table overflow handling, and stable chapter/section navigation unless explicitly redesigned.

Do not dark-mode invert/filter the historical front-matter JPEG. Generated black-on-white scientific diagrams may be theme-adjusted for legibility.

The HTML edition is the browser reading/preview experience.

## EPUB

Build EPUB from the transformed canonical LaTeX prepared by the HTML pipeline, not by reparsing MathJax HTML. This preserves mathematical structure for MathML output and avoids a parallel content tree.

The EPUB metadata title must remain `Wave Motions in the Ocean: Myrl's View`, with David C. Chapman and Paola Malanotte-Rizzoli as authors and Albert M. W. Yau identified as digital editor/contributor. Validation must confirm package metadata and the presence of MathML.

EPUB TOC depth is Chapter → Section. Check metadata, shared cover, navigation, math, figures, tables, links, and reflow in representative readers as iteration proceeds.

Publish EPUB as a direct download. Browsers do not provide a consistent native EPUB reader, and the existing HTML edition already serves the web-reading use case. Do not add epub.js or another embedded EPUB reader unless explicitly requested.

## Figure and equation numbering

The modern PDF, HTML, and EPUB use chapter-based figure and equation numbers. The facsimile suppresses these added editorial numbers so its historical source-page presentation remains unchanged.

Number every scientific body figure, but number displayed equations selectively. An equation is important enough to number when it has a durable identity in the exposition: a governing equation/system, boundary or eigenvalue problem, dispersion or modal/root relation, conservation law, ray equation, or named physical definition/result such as phase speed, group velocity, sound speed, wave action, or energy flux. Keep transient algebra, intermediate substitutions/rearrangements, generic parameter-definition lists, and one-off evaluation steps unnumbered. A multi-line governing system normally receives one number unless its component equations have independent roles.

Do not add equation/figure cross-references or hyperlinks merely because numbers exist. Add those later, selectively, after numbering is stable across formats.

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
  SHA256SUMS
```

`build/` and `dist/` are generated and untracked.

Generated reader artifacts carry an exact source build identity. HTML and EPUB display the short commit identifier linked to that commit; the modern PDF places it on the copyright/edition-notice page; the facsimile keeps it non-visible in PDF metadata so historical page appearance is unchanged. The short commit identifier is **build provenance, not a Git tag**. Stable releases use semantic Git tags such as `v1.0.0`; an exact release-tag build displays both, for example `v1.0.0 (abc1234)`.

`SHA256SUMS` covers exactly the two PDFs and EPUB in the canonical `dist/` artifact. Release packaging requires that exact manifest before promotion, then emits a release manifest covering exactly the two direct PDFs, direct EPUB, and HTML-only ZIP. Duplicate, missing, unexpected, or mismatched checksum entries are fatal.

After any reconstruction `.tex` change, regenerate the README before committing:

```bash
python3 scripts/sync-views.py --readme
```

Include any resulting README update with the source change. A full local validation is `./scripts/build.sh all`. Canonical CI deliberately separates artifact generation from QA: `Build publication` uses `WAVE_SKIP_VALIDATION=1`, then runs the QA categories as explicit steps so development artifacts can still be produced when an audit check warns.

## Publish workflow

`.github/workflows/publish.yml` is the single publication workflow. It builds and validates the complete publication for relevant publication-input pushes to `main`, every pull request targeting `main`, stable semantic release tags such as `v1.0.0`, and manual runs. Tag pushes are release builds and must not depend on changed-path filtering.

For direct pushes to `main`, trigger on actual reader/build inputs: reconstruction TeX and BibTeX sources, `reconstruction/styles/**`, `reconstruction/figures/**`, immutable `source/**` scans, `scripts/**`, `.python-version`, `requirements.txt`, `tex-packages.txt`, `README.md`, and `.github/workflows/publish.yml`. Tracking-only records such as `reconstruction/ERRATA.md`, `reconstruction/FIGURES.md`, `reconstruction/PLAN.md`, and `reconstruction/RENDER_QA.md` do not by themselves require a full main-push publication build. Keep pull requests unfiltered so a future required Build check cannot remain indefinitely Pending merely because GitHub skipped the workflow. Source scans remain immutable; including `source/**` in the trigger is defensive so an accidental source-file change cannot bypass canonical CI.

`Publish` must be reproducible from the triggering commit and must not edit tracked source files, create commits, or push repository changes. Do not append chat/session migrations, one-time cleanup scripts, or other repository-mutating automation to it.

If your task genuinely requires GitHub Actions to modify tracked repository contents, create a separate purpose-specific workflow and any needed trigger file. Remove automation created by your task when that task is complete unless the owner asks to retain it. Treat unfamiliar temporary workflows and triggers as potentially active; do not remove another session's automation merely because it looks temporary.

During periods of frequent direct pushes, do **not** cancel the active publication build for the same ref. Use `cancel-in-progress: false` so one run can finish while GitHub coalesces pending work toward the newest commit instead of repeatedly terminating every build. The **Pages deployment** must also use `cancel-in-progress: false` so an active deployment is not interrupted.

An exact TinyTeX cache hit is a complete, pinned TeX environment for the matching TinyTeX version, runner OS, and `tex-packages.txt` hash. Skip `tlmgr update --self` and package installation on that exact hit. A cache miss or prefix restore must run dependency installation before building.

CI should surface build/validation categories as separate named steps where practical so findings are visible without reading a monolithic log. On ordinary `main`, pull-request, and manual builds, QA findings are **advisory**: README synchronization, EPUB accessibility/standards/math checks, PDF integrity/pagination/destination/text/render checks, publish-root checks, build-identity checks, and checksum verification may warn without failing the Build job. The build script may likewise retain a complete generated HTML set or nonempty EPUB when an embedded post-generation self-check reports an error during development CI. Missing/incomplete artifacts, dependency failures, LaTeX/Pandoc generation failures that do not produce the expected outputs, and checksum generation remain fatal. On stable `vX.Y.Z` tag builds, the same QA and embedded checks are strict, the facsimile must be exactly 184 pages, and the release gate is fatal.

Build once and promote that exact validated output. Pages and GitHub Releases must consume the `wave-motions-editions` artifact from the successful Build job rather than rebuilding the book. A release tag must be an exact stable `vX.Y.Z` semantic version and its commit must be reachable from `main`; reject malformed or off-main tags before expensive environment setup. The release gate additionally requires the exact semantic version/commit build identity and exactly 184 facsimile pages. The release publishes `wave-motions.pdf`, `wave-motions-facsimile.pdf`, and `wave-motions.epub` as direct assets plus `wave-motions-html.zip` and `SHA256SUMS`. Do not manufacture short-SHA Git tags.

Release publication is append-once. A draft release may be resumed only when it contains no unexpected assets; expected assets may be replaced while the release remains a draft. Once a release is published, automation must never replace or delete its assets. A rerun may succeed only after downloading the published assets and verifying the exact expected asset set and checksum manifest against the newly validated build; otherwise fail rather than mutate the published release. For stable public releases, enable GitHub's repository-level **release immutability** setting before the first release when available so GitHub itself locks the published tag and assets in addition to these workflow safeguards.

GitHub Pages is temporarily disabled while the repository remains private. Keep the existing Pages steps/deploy job dormant rather than removing them; when Pages is restored, remove only the temporary false guards so deployment promotes the same validated `dist/` output.

CI must verify `index.html` plus all three downloadable formats. Keep `tex-packages.txt` at repository root as the TeX dependency manifest.
