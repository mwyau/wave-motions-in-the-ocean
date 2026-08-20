# Repository instructions

Keep this file limited to repository-wide invariants and routing. Read the relevant task skill before specialized work.

## Task skills

- Publication, front matter, README/HTML synchronization, EPUB, builds, and Pages: `skills/publication/SKILL.md`
- Scan fidelity, equations, scientific verification, and references: `skills/source-audit/SKILL.md`
- Figure extraction, vector/raster reconstruction, comparison, and scientific figure review: `skills/figure-audit/SKILL.md`
- For equation-defined or scientifically constrained figures, read both `source-audit` and `figure-audit`.
- For publication work that changes historical or scientific content, also read `source-audit`.

## Git workflow and concurrent work

- External contributor pull requests are accepted. Agent/maintainer work should not create a PR unless the owner requests one.
- Merge pull requests with rebase merge only. Never use merge commits or squash merge.
- When direct integration to `main` is authorized, keep history linear: rebase/fast-forward rather than creating merge commits.
- Before writing or integrating, re-read the latest `main`. Preserve unrelated concurrent changes. If `main` moved, rebase or reconstruct the change on the new tip rather than overwriting newer work.
- Never force-push `main` or replace another active session's work.
- During long audits, reconstructions, or refactors, commit coherent checkpoints frequently. Each checkpoint should leave the repository understandable and should not include generated artifacts.
- The owner may squash or rewrite `main` history at any time. Treat the current contents of `main` as authoritative rather than relying on long-lived commit SHAs.
- Write commit subjects as short human-readable sentences beginning with a capital letter. Do not use Conventional Commit prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, `refactor:`, or `chore:`.

## Work coordination with issues

- When GitHub Issues access is readily available, use Issues to coordinate non-trivial agent/session work. Before modifying the repository, search open and relevant recently closed issues for overlapping or prior work. Reuse a matching open issue. If a closed issue directly covers a continuation or follow-up, reopen and reuse it when practical; otherwise create one concise issue for the coherent task.
- Do not block straightforward work solely because the Issues API is unavailable or impractical to reach. Preserve the same scope/ownership and handoff information in the working session, then create or update the relevant issue later when practical.
- Agent/session coordination issues should normally use the `[internal]` title prefix so they are easy to distinguish from public or reader-facing issues. Do not rename unrelated public issues merely to impose this convention.
- The issue should state what is being changed, the main files/areas involved, and any temporary branch, workflow, or trigger it owns.
- When issue access is readily available, add concise progress notes when useful: scope changes, meaningful checkpoints during long work, blockers, or findings another agent may need. Do not interrupt straightforward work merely to report routine progress.
- Before integrating, re-check open issues, relevant recently closed issues, and the latest `main` for newly overlapping work when issue access is available.
- If another active issue overlaps, preserve its work and avoid competing edits; coordinate or split scope before proceeding.
- For non-trivial work, the final issue comment is the durable handoff document and should be detailed enough for another agent to continue without the original session context. Include the completed scope, files/areas changed, relevant commits, validation performed and results, important findings and decisions with rationale, unresolved questions or known limitations, status of temporary branches/workflows/triggers, and concrete next steps or restart points. Trivial fixes may use a short closeout.
- After writing the handoff, close the issue. If the task is abandoned or superseded, still record the findings, current state, and restart/handoff information before closing it rather than leaving a misleading active claim.

## Automation

- `.github/workflows/publish.yml` is publication automation, not a general repository-mutation hook. Never add one-off migration, cleanup, source-editing, commit, or push logic to it.
- If your task creates a temporary workflow or trigger file, remove it when that task is complete unless the owner asks to retain it.
- Treat unfamiliar temporary workflows and trigger files as potentially active. Do not remove automation created by another active session or agent. Remove unrelated temporary automation only when it is clearly stale and no longer serving active work.
- Keep versioned development dependencies and GitHub Actions on explicit full-version pins. Let Dependabot propose updates rather than replacing exact pins with floating major tags.
- The reference GitHub-hosted Linux runner is `ubuntu-26.04`. Use the checked-in `.python-version`, `requirements.txt`, TinyTeX release pin, and workflow tool pins as the environment authority.

## Source and content model

- `source/*.pdf` is the immutable historical authority. Never edit, recompress, replace, or rewrite a source PDF.
- The reconstruction `.tex` files and `reconstruction/references.bib` are the maintained source for reader editions. Correct shared content once rather than maintaining parallel HTML, Markdown, equation, or metadata copies.
- `README.md` is a synchronized publication view, not an independent prose source.
- Record substantive corrections or suspected source errors in `reconstruction/ERRATA.md`.
- The authorized license is CC BY-NC-SA 4.0. Do not change or weaken it without explicit instruction.

## Records

- `reconstruction/ERRATA.md`: substantive source/reconstruction deviations, corrections, evidence, and review status; not an audit-coverage ledger.
- `reconstruction/FIGURES.md`: figure provenance, reconstruction type, scientific/equation validation, and review status.
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

`build/` and `dist/` are generated and untracked. Generated comparison images are not committed.

After every change to any reconstruction `.tex` source, run:

```bash
python3 scripts/sync-views.py --readme
```

Include any resulting `README.md` update in the same commit; do not hand-maintain synchronized README content separately from its source.

## Completion

A successful build alone does not complete reconstruction work. Follow the relevant task skill and update `PLAN.md`, `ERRATA.md`, or `FIGURES.md` when the batch changes their scope.

For a coherent repository batch, finish with:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For affected figures, also regenerate the relevant comparison with `scripts/compare-figures.py`.
