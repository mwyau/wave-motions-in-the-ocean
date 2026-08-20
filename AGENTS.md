# Repository instructions

Keep this file limited to repository-wide invariants and routing. Read the relevant task skill before specialized work.

## Task skills

- Publication, front matter, README/HTML synchronization, EPUB, builds, and Pages: `skills/publication/SKILL.md`
- Scan fidelity, equations, scientific verification, and references: `skills/source-audit/SKILL.md`
- Figure extraction, vector/raster reconstruction, comparison, and scientific figure review: `skills/figure-audit/SKILL.md`
- For equation-defined or scientifically constrained figures, read both `source-audit` and `figure-audit`.
- For publication work that changes historical or scientific content, also read `source-audit`.

## Git workflow and concurrent work

- External contributor pull requests are accepted. Agent/maintainer work should not create a PR unless explicitly requested.
- Merge pull requests with rebase merge only. Never use merge commits or squash merge.
- When direct integration to `main` is authorized, keep history linear: rebase/fast-forward rather than creating merge commits.
- Before writing or integrating, re-read the latest `main`. Preserve unrelated concurrent changes. If `main` moved, rebase or reconstruct the change on the new tip rather than overwriting newer work.
- Never force-push `main` or replace another active session's work.
- During long audits, reconstructions, or refactors, commit coherent checkpoints frequently. Each checkpoint should leave the repository understandable and should not include generated artifacts.
- Repository history may be squashed or rewritten. Treat the current contents of `main` as authoritative rather than relying on long-lived commit SHAs.
- Write commit subjects as short human-readable sentences beginning with a capital letter. Do not use Conventional Commit prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, `refactor:`, or `chore:`.

## Work coordination with issues

Issues are durable workstreams and handoff records, not a log entry for every finding.

### Session identity and visibility

- For every non-trivial or long-running session, choose a short memorable session name before substantial work begins, for example `Harbor`, `Quartz`, or `Kestrel`. Use the same name in chat and issue comments for the life of that session. Do not identify a session as `owner`, by an account/user name, or only as a generic role such as `CI agent`.
- At the beginning of a long session, make the first visible chat update identify the session and issue state. Use a compact form such as:
  - `Session: Harbor`
  - `Issues — started: #15; working: #15; closed: none; handed over: none`
  - `Scope: software coordination and stale automation cleanup`
- At the end of a long session, print the same session name and summarize issue outcomes in chat: issues started/worked, closed, handed over, or left waiting, plus the final `main`/review SHA when relevant.
- The first issue claim for a session should start with the same name and state, for example `Session: Harbor | status: active | start: <sha>`, followed by the claimed files/area and goal.
- While one session is actively driving an issue, prefer a visible title prefix such as `[internal][Harbor]`. If work is blocked with no active session, use `[internal][waiting]`. The legacy `[internal][active]` form is acceptable only until the active session next checks in and chooses a name. Restore the normal `[internal]` prefix when closing.
- Prefer one primary active session per issue. A second session should usually provide feedback in comments or work through another existing issue rather than silently sharing the same claim. Split into another issue only when the second scope is independently schedulable and substantial enough to justify its own completion criterion.

### Issue lifecycle

- Before non-trivial work, search open and relevant recently closed issues. Reuse the closest active issue whenever the work fits its goal.
- Prefer one umbrella issue for a related audit/integration batch. Open a new `[internal]` issue only when the work is independently schedulable, needs a distinct active session or completion criterion, or would make an existing issue misleading. Do not open a new issue for a small finding when a comment/checklist item is sufficient.
- Before editing, leave a concise claim on the issue when concurrent work is likely: session name, files/area, goal, and the `main` SHA you started from. Claims are file/area-specific, not repository-wide.
- If another active issue has an overlapping claim, do not race it. Leave the finding on that issue with evidence and a recommended action. Transfer the scope only after coordination or explicit instruction, and record the transfer on both records when useful.
- Feedback to another workstream should usually be an issue comment, not a new issue. Include the affected path/behavior, why it matters, enough evidence or reproduction detail to act on it, and whether it blocks current work.
- Use progress comments at meaningful boundaries, not for every operation. Good checkpoints are `reviewed through <sha>`, an integrated commit, a changed decision, a blocker, or a handoff. A long audit should always leave its latest review boundary in the issue.
- Re-read the latest `main` and relevant issue comments immediately before integration. If `main` moved, rebuild the commit on the new tip and preserve unrelated changes.
- Do not leave an issue marked active when no session is working it. If it is waiting on an artifact, decision, or another workstream, mark it `[internal][waiting]` and state the unblock condition. If work is merely deferred, move it to `reconstruction/PLAN.md` or the relevant task record and close the issue until work resumes.
- Close specialist issues when their scoped work and handoff are complete. Do not keep several specialist issues open only because they all await the same repository-wide Build/release gate; record that dependency and let the CI/release or umbrella workstream own the shared gate.
- If an issue becomes redundant, superseded, or folded into an umbrella, leave a short handoff pointing to the surviving record and close it rather than maintaining parallel status threads.
- Do not block straightforward work solely because the Issues API is unavailable. Preserve the same session name, scope, review boundary, and handoff information in chat and update the issue later when practical.
- The final issue comment is the durable handoff. For non-trivial work include completed scope, files/areas changed, relevant commits, validation and results, important decisions, unresolved limitations, temporary branch/workflow/trigger status, and the concrete next review/restart point. Trivial fixes may use a short closeout.

## Automation and temporary branches

- `.github/workflows/publish.yml` is publication automation, not a general repository-mutation hook. Never add one-off migration, cleanup, source-editing, commit, or push logic to it.
- If a task creates a temporary workflow, trigger file, or working branch, record its path/name in the issue claim. Remove it when that task is complete unless explicitly asked to retain it.
- Treat unfamiliar temporary workflows, triggers, and branches as potentially active. Do not remove another active session's automation or branch.
- A temporary workflow/trigger tied to a closed or superseded issue is stale unless its handoff explicitly transfers it to an active issue. Remove stale automation promptly, especially workflows with write permissions or push triggers.
- A working branch with no unique commits relative to `main` and no active issue claim is safe cleanup. A diverged branch with unique commits must be reviewed or handed off before deletion, even if its name looks old.
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
