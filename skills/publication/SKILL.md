# Publication skill

Use this skill for modern/facsimile presentation, front matter, README/HTML synchronization, EPUB, builds, CI, Pages, and releases.

## Content boundary

Publication work controls presentation and generated editions. It must not silently rewrite source or scientific content.

- Shared body text comes from `src/chapter1.tex` … `chapter6.tex` and remains governed by `skills/source-audit/SKILL.md`.
- The committed 1989 PDFs under `references/chapman-rizzoli-1989/` control source-fidelity checks.
- Do not alter prose, equations, figure labels, references, or scientific meaning merely to improve style, satisfy a validator, make a derivation more correct, or simplify a build.
- A substantive source correction requires explicit human approval under the source-audit rules. Publication tooling/build success never constitutes approval.

### Cross-format punctuation

Canonical `.tex` uses TeX punctuation conventions; Markdown, HTML, and EPUB should render the equivalent reader-facing UTF-8 smart punctuation. Generated formats are views, never independent punctuation sources. Conversion tooling owns format-specific punctuation rendering: use the explicit `latex+smart` Pandoc reader where LaTeX is converted to a reader format, and keep identifiers, URLs, slugs, and mathematical source syntax out of smart-punctuation normalization.

## Canonical publication sources

- Shared modern PDF/EPUB cover: `src/cover-modern.tex`
- Modern front matter: `src/frontmatter-modern.tex`
- PDF-only modern book preliminaries: `src/frontmatter-modern-book.tex`
- PDF-only modern closing page: `src/back-modern.tex`
- Facsimile front matter: `src/frontmatter-facsimile.tex`
- Shared body: `src/chapter1.tex` … `chapter6.tex`
- Bibliography: `src/references.bib`

README, HTML, and EPUB are generated/synchronized publication views, not separate prose sources.

## Modern cover and front matter

The modern PDF and EPUB use the same cover generated from `cover-modern.tex`; EPUB rasterizes that TeX cover rather than maintaining another cover source.

Preserve these cover invariants unless explicitly redesigned by the owner:

1. `WAVE MOTIONS IN THE OCEAN` is the dominant dark-ocean-blue title.
2. `Myrl's View` is the prominent italic subtitle.
3. The full rectangular Met image of Hokusai's *Under the Wave off Kanagawa* is reproduced without speculative color correction or generative reconstruction.
4. `Presented to Myrl C. Hendershott` appears below the image and above the authors.
5. David C. Chapman and Paola Malanotte-Rizzoli are the authors, shown on separate lines without an intervening `and` and at a visibly larger size than the presentation line.
6. A small centered `Editor: Albert M. W. Yau.` appears near the bottom edge.
7. Years, license marks, museum credit, and badges do not belong on the front cover.

The committed Hokusai source image is `src/images/great-wave-met-dp130155.jpg`. Preserve its composition.

The paged modern PDF ends with a closing artwork page defined in `src/back-modern.tex`. Preserve these closing-page invariants unless explicitly redesigned by the owner:

1. Use Utagawa Hiroshige's *Naruto Whirlpool, Awa Province*, The Met JP1198.
2. The committed artwork is a lightly deskewed crop to the print's black border; do not generatively reconstruct or recolor it.
3. Use the same left/right margins and restrained dark-ocean-blue frame treatment as the front cover.
4. Keep the closing page otherwise uncaptioned, with only small `DOI: Pending` text at bottom right until a DOI is assigned.
5. Keep the museum/public-domain credit in the interior edition notice rather than on the artwork page.

The paged modern PDF preliminaries are:

1. half-title,
2. Lake Como frontispiece,
3. full title page,
4. copyright / edition-notice verso,
5. Contents,
6. Preface — David C. Chapman,
7. Preface — Paola Malanotte-Rizzoli,
8. Editor's note,
9. Chapter 1.

`frontmatter-modern-book.tex` owns that PDF-only sequence. Preliminary leaves count in Roman pagination; Contents begins visibly at v; Chapter 1 resets to Arabic page 1.

Keep the editor credit subordinate to the authors on interior title/front-matter pages: `Edited by Albert M. W. Yau, August 2026.` Do not assert ownership of the original lecture-note copyright.

The Lake Como photograph remains the modern PDF frontispiece with its established Villa Carlotta caption. Preserve the committed JPEG; do not invent photographer attribution, generatively reconstruct details, or apply speculative restoration.

Modern contents use Chapter → Section only (`tocdepth=1`).

## Facsimile PDF

The facsimile is a QA edition, not a reader-facing publication. Build and validate it to compare source-page layout and catch reconstruction drift. Keep it unlinked from README and HTML. It is included in the final `release/` publication root and is therefore publicly accessible on GitHub Pages. Stable tagged releases archive that complete publication root in `wave-motions-html.zip`, so the facsimile is included inside the ZIP, but it is not published as a standalone GitHub Release asset.

Preserve the 184-physical-page structure and original printed page numbers.

Expected component counts are:

- front matter: 10 pages
- Chapters 1–6: 17 + 20 + 26 + 32 + 53 + 23 = 171 pages
- references: 3 pages
- total: 184 pages

Keep `\flushbottom`, source-page `\pagebreak[4]` behavior, and source-page page-counter boundaries consistent with the existing style. Do not accept overfull vertical boxes as a way to force the count. Keep facsimile layout policy centralized in `wave-facsimile.sty`; do not add page-specific scaling, crop, spacing, or `\enlargethispage` exceptions to repair pagination.

The facsimile build logs machine-readable source-boundary headroom and physical/printed-page identity. Development validation should warn when pagination drifts, a vertical box overflows, source-page identity drifts, or the minimum natural body-page reserve falls below 10 pt, so regressions are visible before a page splits. Stable release validation remains strict: exactly 184 physical pages, correct source-page identity, no overfull vertical boxes, and no negative source-boundary reserve.

## README and HTML synchronization

`scripts/publication.py` derives shared titles, section headings, reader links, license presentation, flowing sources, figure assets, and build identity. `scripts/webapp.py` owns the HTML web-app manifest, icons, offline resource set, and service-worker generation from `src/layout/wave-service-worker.js`. `scripts/build_html.py` consumes those models while generating the final HTML edition; `scripts/sync_readme.py` owns README synchronization/checking only.

README and HTML must remain substantively synchronized, with format-specific differences such as absolute/relative URLs, README badges, and HTML reader controls.

Reader-facing downloads are:

- `wave-motions.pdf`
- `wave-motions.epub`

Do not link the original online source from README or HTML. Keep that URL with the source-reference material under `references/chapman-rizzoli-1989/README.md`, where it does not compete with the current edition.

Keep public section anchors stable.

## HTML

Preserve the responsive reader, System/Light/Dark themes, GitHub Source navigation, Contents navigation, wide-math/table overflow behavior, and stable chapter/section navigation unless explicitly redesigned.

The current reader also preserves these navigation behaviors: the sticky context reflects the current chapter/section; direct section permalinks initialize that context and the matching Contents entry immediately; scrolling updates the active section; wide layouts expose the Contents rail when space permits, while narrower layouts use the Contents popover/fallback; browser fragment/back-forward navigation must remain correct. The visible Rendering control switches between MathJax and native MathML and should remain available unless deliberately replaced.

`build_html.py` owns the public HTML discovery metadata. It derives one clean canonical URL, description, social URL, and structured-data record per page from the shared publication model and page inventory, and writes the same canonical page set to `release/sitemap.xml`. Chapter descriptions are curated strings in the same canonical metadata as the maintained chapter and section headings; Contents and navigation keep the complete section inventory. Google Scholar Highwire metadata belongs only on the complete-book landing page; chapter pages must not present themselves as separate scholarly works.

Reader preferences are URL state: non-default Figures, zoom, theme, and math values appear in that order in shareable reader URLs and propagate across reader-page links. Clean URLs use publication defaults, no browser preference storage is used, and query variants retain the parameter-free canonical metadata, receive `noindex,follow`, and stay out of the sitemap.

The finished HTML reader keeps required runtime assets local: pinned MathJax, MathJax fonts, Source Serif, and Source Sans are under local `assets/`. The two large decorative cover/back-cover artwork images use stable Wave Motions Pages URLs and are optional to reading; a clean build may fetch the pinned vendor archives into the build cache, but the generated HTML and tagged release ZIP must not require third-party network resources to render text or mathematics.

The HTML build also emits one root `app.webmanifest` and one root `service-worker.js`. The manifest consumes the deterministic Stage-1 icons, and the worker precaches the complete text-reading content and required local reader assets with a build-identity cache; scientific PNG/SVG figures are cached only after a successful same-origin request, while PDF, EPUB, archive downloads, and the two large decorative artwork images stay outside the offline set. Reading and local-file behavior must remain functional without service-worker support.

Do not dark-mode invert/filter the front-matter photograph. Generated black-on-white scientific diagrams may be theme-adjusted for legibility without changing their content.

## EPUB

Build EPUB from transformed main LaTeX, not by reparsing MathJax HTML. Preserve mathematical structure as MathML.

Metadata must keep the title `Wave Motions in the Ocean: Myrl's View`, David C. Chapman and Paola Malanotte-Rizzoli as authors, and Albert M. W. Yau as editor/contributor.

EPUB TOC depth is Chapter → Section. Validate metadata, cover, navigation, MathML, figures, tables, links, accessibility metadata, and reflow. Do not change source mathematics merely to satisfy a MathML validator; fix the transformation/validator unless the source itself was mistranscribed.

Publish EPUB as a direct download; the HTML edition is the web-reading experience.

## Figure and equation numbering

Modern PDF, HTML, and EPUB use chapter-based figure/equation numbering. The facsimile suppresses added editorial numbers.

Number every scientific body figure. Number displayed equations selectively when they have durable identity in the exposition: governing systems, boundary/eigenvalue problems, dispersion/modal/root relations, conservation laws, ray equations, or named physical definitions/results. Keep transient algebra and one-off substitutions unnumbered.

Do not use numbering changes as an opportunity to alter source equations.

## Build interface and outputs

Python tooling uses uv as the only supported development and CI environment. `pyproject.toml` owns the dependency declarations and `uv.lock` is the exact reference lock. Set up with `uv sync --frozen`; run Python tools with `uv run --frozen`. Make targets enter the uv environment themselves. The Makefile orchestrates the three direct builders: `build_pdf.py`, `build_html.py`, and `build_epub.py`.

Use:

```bash
make pdf
make html
make epub
make all
```

For an individual direct builder, use `uv run --frozen python scripts/build_pdf.py`, `scripts/build_html.py`, or `scripts/build_epub.py` as appropriate.

`build/` and `release/` are generated and untracked. `audit/` is the persistent-but-ignored workspace for temporary review artifacts and must survive publication builds. The flat `release/` root is the complete validated publication tree: HTML, assets, the modern PDF, QA facsimile PDF, EPUB, and `SHA256SUMS`. Normal builds do not create `wave-motions-html.zip`.

Generated reader artifacts carry the exact source build identity. Stable releases use semantic tags such as `v1.0.0`; short commit IDs are build info, not release tags.

`SHA256SUMS` covers the modern PDF and EPUB in the validated publication root. `wave-motions-html.zip` is created only by the stable-tag release job from the entire validated `release/` tree, including the facsimile and checksum manifest. A tagged GitHub Release publishes exactly the ZIP, the modern PDF, and the EPUB.

After any reconstruction `.tex` change:

```bash
uv run --frozen python scripts/sync_readme.py
```

Include resulting README synchronization in the same commit. A coherent local build is `make all`.

## Publish workflow

`.github/workflows/publish.yml` is the single publication workflow. It may build, validate, package, deploy, and publish artifacts; it must never edit tracked source files, create repository commits, or push source changes.

**Never create a temporary GitHub Actions workflow, trigger file, issue-comment trigger, self-removing workflow, or other automation to mutate repository contents.** All agent repository edits are made directly against the latest `main` and committed there through the normal Git object/ref path.

Do not add one-time migration, cleanup, source-editing, reconciliation, or bot-commit logic to `publish.yml`.

Publication automation should remain reproducible from the triggering commit. Build, package, and validate once into `release/`, then upload that exact tree once as the `wave-motions-publication` Pages-format Actions artifact. GitHub Pages deploys the same artifact without rebuilding or copying it into another staging directory. Stable tag runs download that same validated artifact, verify the PDF/EPUB checksums, create `wave-motions-html.zip` from the complete extracted tree, and publish exactly the ZIP, modern PDF, and EPUB. The facsimile stays in the Pages tree and inside the tagged ZIP but remains unlinked and is not a standalone GitHub Release asset.

Direct pushes to `main` should trigger on actual reader/build inputs. Tracking-only files such as `src/ERRATA.md`, `src/FIGURES.md`, and `src/RENDER_QA.md` need not by themselves trigger a full publication build. Pull-request validation remains unfiltered when needed for a required Build check. Source scans are immutable; including them defensively in trigger paths is acceptable so accidental changes cannot bypass CI.

Keep exact dependency/tool pins and TinyTeX cache semantics aligned with repository manifests. Missing/incomplete artifacts and generation/dependency failures are fatal. Development QA categories may warn where deliberately configured; stable `vX.Y.Z` release gates are strict, including exact facsimile pagination and release asset/checksum validation.

Release publication is append-once. Published release assets must not be replaced or deleted by automation. A rerun may verify an existing published release but must fail rather than mutate it on mismatch. Use repository-level release immutability when available before stable public releases.

GitHub Actions and GitHub Pages are enabled. The workflow's Pages deployment runs only for `refs/heads/main`; pull-request and tag runs still produce the validated `wave-motions-publication` artifact but do not deploy Pages. A workflow dispatch on `main` may redeploy the same build path. Stable release tags continue through the separate release job. Pages and release automation remain read-only with respect to tracked repository content.
