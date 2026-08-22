# Repository instructions

Keep this file limited to repository-wide invariants and routing. Read the relevant skill for task-specific procedures.

## Writing

- Use plain, direct English in repository text. Prefer a short, common word when it means the same thing. Do not make writing sound formal just to sound polished. Keep technical and scientific terms when they are the right terms.
- This applies to README text, agent-written documentation, skills, comments, issue-facing guidance stored in the repository, labels, and explanatory prose.
- It does not authorize rewriting source book text, quoted material, work titles, names, equations, scientific terms, license names, or useful code/API terms. For example, use “source” or “earlier” instead of “historical” when that is what you mean, “use” instead of “utilize,” and “before” instead of “prior to.” These are examples, not banned words. If the plain word says the same thing just as clearly, use it.

## Task skills

- Source fidelity, text/equation transcription, scientific verification, errata, and references: `skills/source-audit/SKILL.md`
- Figure extraction, vector/raster reconstruction, comparison, and scientific figure review: `skills/figure-audit/SKILL.md`
- Front matter, reader formats, README/HTML synchronization, builds, CI, Pages, and releases: `skills/publication/SKILL.md`
- Post-build PDF/HTML/EPUB visual and structural review: `skills/render-qa/SKILL.md`
- For equation-defined or scientifically constrained figures, read both `source-audit` and `figure-audit`.
- For publication work that could alter source or scientific content, also read `source-audit`.

## Local environment

- Use the local setup in `CONTRIBUTING.md`; it is kept aligned with the publication CI environment.
- Before diagnosing build, render, or figure failures, make sure the repository Python environment and pinned TinyTeX/`tex-packages.txt` environment are active. Do not change source content to work around missing local dependencies.

## Global source rule

- `references/chapman-rizzoli-1989/*.pdf` is the immutable source set. Never edit, replace, recompress, or rewrite a source PDF.
- Reconstruction defaults to source fidelity, not substantive correction or modernization.
- Main LaTeX uses conventional TeX punctuation; generated reader formats may render equivalent Unicode typography. Small, unambiguous punctuation normalization may be corrected autonomously when it does not change wording, scientific or mathematical meaning, bibliographic identity, or intentional emphasis. Ambiguous or meaning-changing punctuation follows the source-audit approval rule.
- Small, unambiguous spelling, grammar, transcription, or punctuation corrections with no plausible scientific, mathematical, bibliographic, or substantive editorial effect may be corrected autonomously.
- Any substantive or ambiguous departure from the source requires explicit human approval. Agents can never approve an erratum or infer approval from correctness, prior commits, issues, builds, other agents, or an existing status label.
- Follow `skills/source-audit/SKILL.md` for the correction decision process and errata format.

## Maintained content

- The reconstruction `.tex` files and `reconstruction/references.bib` are the maintained reader sources.
- `README.md`, HTML, EPUB, `build/`, and `dist/` are derived/generated views or outputs; follow `skills/publication/SKILL.md` rather than maintaining parallel content.
- `audit/` is the persistent-but-ignored workspace for temporary human/agent audit evidence; it must survive publication builds and must never be committed.
- The authorized license is CC BY-NC-SA 4.0. Do not change it without explicit instruction.

## Git workflow

- Agent edits go directly onto the latest `main` as small linear commits unless the owner explicitly requests a branch or PR.
- Before committing, re-read current `main`; if it moved, reconstruct the change on the new tip.
- Never force-push, reset `main` backwards, create merge commits, or overwrite newer work.
- Do not create agent coordination sessions, claims, handoff branches, or competing workstreams.
- Never create temporary workflows, trigger files, bot commit paths, or other automation to mutate tracked repository files.
- `.github/workflows/publish.yml` is publication automation only: it builds and validates editions, deploys the `main` publication artifact to GitHub Pages, and publishes stable-tag release artifacts. It must never edit tracked source, create commits, or push source changes.
- Treat current `main` as the branch to follow; history may be rewritten or squashed.

## Project records

- `reconstruction/ERRATA.md`: substantive source deviations, proposed corrections, evidence, and human review status.
- `reconstruction/FIGURES.md`: figure source info, representation, and scientific/equation validation.

Do not create duplicate audit ledgers, source manifests, verification TSVs, hash/status ledgers, or temporary trigger records.

For validation, synchronization, dependency pins, publication invariants, and completion commands, follow the relevant skill instead of duplicating them here.
