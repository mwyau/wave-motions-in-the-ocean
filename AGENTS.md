# Repository instructions

Keep this file limited to repository-wide invariants and routing. Read the relevant task skill before specialized work.

## Task skills

- Publication, front matter, README/HTML synchronization, EPUB, builds, CI, Pages, and releases: `skills/publication/SKILL.md`
- Scan fidelity, text/equation transcription, scientific verification, and references: `skills/source-audit/SKILL.md`
- Figure extraction, vector/raster reconstruction, comparison, and scientific figure review: `skills/figure-audit/SKILL.md`
- For equation-defined or scientifically constrained figures, read both `source-audit` and `figure-audit`.
- For publication work that could change historical or scientific content, also read `source-audit`.

## Historical source authority

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- Treat the source PDF text, equations, labels, and figures as the truth for the reconstruction, even when an agent believes the source is scientifically or editorially wrong.
- The default reconstruction rule is fidelity, not correction or modernization.
- The only autonomous exception is a small, unambiguous typographical or transcription typo for which there is no plausible change in scientific, mathematical, bibliographic, or editorial meaning. If there is any doubt, it is substantive.
- For any larger, ambiguous, scientific, mathematical, editorial, reference, or figure correction: preserve or restore the source reading, record the proposed erratum and evidence as pending human review, and ask the human owner for approval before changing the reconstructed content.
- Agents can never approve an erratum. Mathematical correctness, outside references, issue closure, a previous agent decision, a commit message, a build result, or an existing `accepted` label is not human approval.
- An `accepted` erratum is valid only when it reflects explicit human approval. If that approval cannot be established, treat the item as unapproved when it is next reviewed.
- Apply human-approved corrections minimally and document the source reading, approved reconstruction, evidence, and approval status in `reconstruction/ERRATA.md`.

## Maintained content model

- The reconstruction `.tex` files and `reconstruction/references.bib` are the maintained sources for reader editions.
- `README.md`, HTML, and EPUB are generated/synchronized publication views, not independent prose sources.
- Correct shared maintained content once; do not maintain parallel text, equation, bibliography, or metadata copies.
- The authorized license is CC BY-NC-SA 4.0. Do not change or weaken it without explicit instruction.

## Git workflow

- The owner has designated a single agent workflow for repository work. Do not create agent coordination sessions, claims, handoff branches, or competing workstreams.
- Agent edits go directly onto the latest `main` as small linear commits. Do not create a PR or working branch for agent changes unless the owner explicitly requests one.
- Before every commit, re-read the current `main`. If `main` moved, rebase/reconstruct the change on the new tip and re-run affected checks.
- Never force-push, reset `main` backwards, create merge commits, or overwrite newer work. External pull requests, when intentionally merged, use rebase merge.
- Never create a temporary GitHub Actions workflow, trigger file, bot commit path, or other automation to edit tracked repository files. Repository mutations are made directly by the agent and committed to `main`.
- `.github/workflows/publish.yml` is build/publication automation only and must never edit tracked source, create commits, or push repository changes.
- Commit coherent checkpoints frequently enough that completed work is preserved. Commit subjects are short human-readable sentences beginning with a capital letter; do not use Conventional Commit prefixes.
- Treat the current contents of `main` as authoritative; history may be rewritten or squashed.

## Issues and records

Issues may be used for durable project planning or externally useful discussion, but they are not required for agent coordination or permission to edit.

- `reconstruction/ERRATA.md`: substantive source/reconstruction deviations, proposed corrections, evidence, and human review status. It is not an audit-coverage ledger.
- `reconstruction/FIGURES.md`: figure provenance, representation choice, scientific/equation validation, and review status.
- `reconstruction/PLAN.md`: remaining work only; completed history belongs in Git history.

Do not create verification TSVs, duplicate chapter-audit files, source manifests, hash/status ledgers, temporary trigger records, or other parallel tracking systems.

## Dependencies and environment

- Keep versioned development dependencies and GitHub Actions on explicit full-version pins. Let Dependabot propose updates rather than replacing exact pins with floating major tags.
- The reference GitHub-hosted Linux runner is `ubuntu-26.04`. Use the checked-in `.python-version`, `requirements.txt`, TinyTeX release pin, `tex-packages.txt`, and workflow tool pins as the environment authority.

## Build and generated output

Use the single interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh epub
./scripts/build.sh all
```

`build/` and `dist/` are generated and untracked. Generated comparison images and audit scratch files are not committed.

After every change to any reconstruction `.tex` source, run:

```bash
python3 scripts/sync-views.py --readme
```

Include any resulting `README.md` update in the same commit; do not hand-maintain synchronized README content separately from its source.

A successful build does not authorize or validate a substantive departure from the source PDFs. Follow the relevant audit skill and human-approval rule first.

For a coherent repository batch, finish with:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For affected figures, also regenerate the relevant comparison with `scripts/compare-figures.py`.
