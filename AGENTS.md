# Repository instructions

Keep this file limited to repository-wide invariants and routing. Read the relevant task skill before specialized work.

## Task skills

- Publication, front matter, README/HTML synchronization, EPUB, builds, and Pages: `skills/publication/SKILL.md`
- Scan fidelity, equations, scientific verification, and references: `skills/source-audit/SKILL.md`
- Figure extraction, vector/raster reconstruction, comparison, and scientific figure review: `skills/figure-audit/SKILL.md`

## Git workflow and automation

- External contributor pull requests are accepted. Agent/maintainer work should not create a PR unless the owner requests one.
- Merge pull requests with rebase merge only. Never use merge commits or squash merge.
- When direct integration to `main` is authorized, keep history linear: rebase/fast-forward rather than creating merge commits.
- During long audits, reconstructions, or refactors, commit coherent checkpoints frequently instead of holding a large amount of completed work until the end. Each checkpoint should leave the repository internally understandable and should not introduce temporary generated artifacts.
- The owner may squash or rewrite `main` history at any time. Treat the current contents of `main` as authoritative; do not rely on long-lived commit SHAs or stable historical commit boundaries.
- Write commit subjects as short human-readable sentences beginning with a capital letter. Do not use Conventional Commit prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, `refactor:`, or `chore:`.
- The canonical publication workflow is not a general-purpose repository mutation hook. Never add one-off migration, cleanup, source-editing, commit, or push logic to it.
- If a temporary or task-specific GitHub Actions job must modify tracked repository contents, create a separate purpose-specific workflow. Remove that workflow after the task unless the owner explicitly wants it retained.
- Keep versioned development dependencies and GitHub Actions on explicit full-version pins. Let Dependabot propose updates rather than replacing exact pins with floating major tags.
- The reference GitHub-hosted Linux runner is `ubuntu-26.04`. Use the checked-in `.python-version`, `requirements.txt`, TinyTeX release pin, and workflow tool pins as the environment authority.

## Canonical sources

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- `reconstruction/frontmatter-modern.tex` is the canonical modern front matter. `reconstruction/frontmatter-facsimile.tex` remains source-faithful.
- `reconstruction/chapter1.tex` through `chapter6.tex` are the canonical chapter bodies and heading structure for every edition.
- `reconstruction/references.bib` is the canonical bibliography. Use BibTeX/citations rather than manually duplicating references.
- Correct shared content once. Record every substantive correction or suspected source error in `reconstruction/ERRATA.md`.
- Do not maintain duplicate prose, equations, chapter/section metadata, replacement registries, or separate HTML/Markdown content trees.
- The authorized license is CC BY-NC-SA 4.0. Do not change or weaken it without explicit instruction.

## Editions and shared content

The repository publishes four reader outputs from one corrected canonical body:

- **Facsimile PDF:** source-compatible typography/page boundaries; accepted pagination is 184 pages.
- **Modern PDF:** modern typography and front matter.
- **Modern HTML:** chapter-split GitHub Pages reading edition.
- **EPUB:** reflowable e-book edition generated from the same canonical material.

`README.md` is not an independent edition; it is a synchronized Markdown publication view. Scientific/textual content and errata are shared. Facsimile and modern outputs may differ only in intentional presentation such as front matter, typography, spacing, navigation, and pagination behavior.

## Publication invariants

- Modern title page: unnumbered. Front matter then uses lower-case Roman numerals beginning at `i`; Chapter 1 resets to Arabic page `1`.
- Modern contents stop at **Chapter → Section**. Do not include subsections or deeper headings in the modern PDF, README, HTML index, or EPUB TOC.
- The Editor's note is listed as `Editor's note` without the editor's name. Its signature remains in the note itself.
- Keep original authorship visually distinct from the digital-editor credit; the editor must not appear to be a third author. On modern page iii, keep the digital-edition credit at the bottom in the same serif family as the authors but at lower visual prominence.
- Use plain publication wording. Prefer `Digital edition by` to `Digital edition prepared by` and `original source scan` to `historical source scan`; avoid inflated editorial terminology when simpler wording is precise.
- Preserve the established Lake Como photograph provenance/caption. Do not reintroduce unsupported attribution such as “Photograph by George.”
- README and `index.html` must present the same front-matter/publication content apart from URL relativity, web controls, and README-only badges.
- Link the historical UNH page `https://oxbow.sr.unh.edu/ChapmanRizzoli/Wave_Motions_in_the_Ocean.html` as **Original online source** in README and HTML only. Do not add that web-navigation link to either PDF or the EPUB unless the owner requests it.
- Shared Downloads list **PDF**, **Facsimile PDF**, and **EPUB**.
- HTML is the browser reading/preview experience. EPUB is published as a download; do not add an embedded EPUB reader unless explicitly requested.

Read `skills/publication/SKILL.md` before changing these details.

## Records

- `reconstruction/ERRATA.md`: substantive source/reconstruction deviations, corrections, evidence, and review status. It is not an audit-coverage ledger.
- `reconstruction/FIGURES.md`: figure provenance, reconstruction type, and review status.
- `reconstruction/PLAN.md`: remaining work only; completed history belongs in Git history.

Do not create verification TSVs, source manifests, hash/status ledgers, duplicate chapter audit files, or other parallel tracking systems.

## Build and generated output

Use the single interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh epub
./scripts/build.sh all
```

`build/` is temporary. `dist/` is the flat publish root and contains the HTML site plus `wave-motions.pdf`, `wave-motions-facsimile.pdf`, and `wave-motions.epub`. Generated outputs and comparison images are not committed.

After every change to any reconstruction `.tex` source, run `python3 scripts/sync-views.py --readme` before committing. Include any resulting `README.md` update in the same commit; do not hand-maintain synchronized README content separately from its source.

GitHub Pages deploys `dist/`. Keep production Pages deployment concurrency with `cancel-in-progress: false` so an active deployment is not interrupted by a newer push.

## Audit requirement

A successful build does not complete the reconstruction. Continue independent text/equation/scientific and figure audits according to the task skills. Preserve historical prose and derivation style; do not silently “fix” scientifically questionable historical material.

## Completion gate

Before considering a coherent batch complete:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For affected figures, also regenerate the relevant comparison with `scripts/compare-figures.py`.

Verify at minimum that the facsimile remains 184 pages unless explicitly reviewed otherwise; PDFs, EPUB, and HTML are structurally valid; README synchronization passes; modern contents stop at sections; all three downloads are published; section anchors work; and `PLAN.md`, `ERRATA.md`, or `FIGURES.md` are updated when the batch changes their scope.
