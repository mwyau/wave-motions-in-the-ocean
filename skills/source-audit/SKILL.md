# Source audit skill

Use this skill for scan fidelity, text/equation transcription, scientific verification, and bibliography/reference work.

## Governing rule

The five 1989 PDFs under `references/chapman-rizzoli-1989/` control source-fidelity checks. The reconstruction should reproduce them faithfully, not silently make substantive changes.

Scientific review is diagnostic. It can identify a likely error and support a proposed erratum, but it does not authorize changing substantive source content.

## Check order

Use this order when a source reading or scientific result is in question:

1. Check the 1989 PDF for what the source actually says.
2. Independently check the science or math when needed.
3. Use the 2008 MIT OpenCourseWare notes and other references to help understand or check a possible error.

The 1989 PDFs control transcription and source-fidelity questions. The 2008 notes can support a proposed correction, but a difference in those notes does not by itself justify silently changing the reconstruction. Agreement between the 1989 notes and a later source is also not an independent scientific check: later notes can repeat the same error. When scientific correctness matters, independently derive, calculate, or otherwise test the result.

## Correction decision order

For every difference or suspected error, use this order:

1. **Reconstruction differs from the PDF unintentionally:** restore the PDF reading unless the difference is a minor mechanical correction allowed by item 2.
2. **Small unambiguous mechanical correction:** spelling, grammar, transcription, punctuation, or TeX punctuation syntax may be corrected autonomously when there is no plausible change in scientific, mathematical, bibliographic, or substantive editorial meaning. If uncertain, do not use this exception.
3. **Substantive or ambiguous source problem:** keep or restore the source reading in the reconstruction, record the proposed correction and evidence in `src/ERRATA.md` with `pending-human-approval`, and ask the human owner for approval.
4. **Explicit human approval in chat:** only when the owner directly instructs approval in the current chat may an agent apply the substantive correction and change the entry to `human-approved`.

Agents can never approve an erratum. Do not infer approval from mathematical correctness, external literature, issue closure, another agent's judgment, an existing commit, or another status. An existing `human-approved` entry may be kept as maintained project state, but an agent must never create or promote that status without a direct approval instruction in the current chat.

A minor autonomous correction need not be added to `ERRATA.md`. If it is useful to keep one there, use `minor-correction`.

## Text fidelity

Compare the scan and main LaTeX directly. Check wording, punctuation, capitalization, symbols, accents, subscripts/superscripts, footnotes, references, page order, headings, and figure labels.

Preserve source wording, organization, notation, and derivation style. Do not modernize prose, terminology, equations, or references merely because another form appears clearer or more correct.

If a source reading is uncertain, inspect the highest-quality source view available and leave the reconstruction at the best-supported literal source reading. Record genuine ambiguity as `pending-human-approval` rather than guessing.

Canonical `.tex` uses conventional TeX punctuation. Minor punctuation normalization is allowed when the intended punctuation is unambiguous and the change is purely mechanical: for example, correct quote pairing/apostrophes, distinguish hyphen/en dash/em dash by context, normalize an obvious prose ellipsis, or fix punctuation spacing. Use `-` for hyphens and math minus, `--` for ranges/en dashes, and `---` for parenthetical em dashes. Do not use a blind global replacement: punctuation that could change meaning, scope, emphasis, a citation/title, or mathematical notation is ambiguous and follows the human-approval rule.

## Equation transcription

For every audited equation, compare every sign, coefficient, derivative, index, exponent, vector mark, delimiter, and equality with the scan. Check that definitions immediately before and after the equation use the same symbols and conventions.

A transcription check answers: **does the reconstruction match the source?** It is distinct from the scientific audit below.

If the scan itself appears mathematically wrong, preserve it pending human approval. Do not substitute the equation that the derivation “must have meant.”

## Scientific equation audit

Independently test the mathematics and physics where useful:

- dimensions and units;
- signs and numerical factors;
- coordinate and Fourier/sign conventions;
- definitions of frequency, wavenumber, phase/group velocity, rotation and stratification parameters;
- algebra between derivation steps;
- boundary and matching conditions;
- mode/eigenvalue conventions;
- limiting cases and asymptotic behavior;
- consistency with nearby prose and figures.

Where practical, verify a standard result against the cited original paper, relevant Hendershott/Myrl material, and another reliable physical-oceanography source. Clearly distinguish external checks from what the 1989 PDF actually says.

The outcome of this audit is one of:

- source and reconstruction agree and the science checks;
- reconstruction mistranscribed the source and must be restored;
- source appears questionable and a `pending-human-approval` erratum should be proposed;
- a `human-approved` erratum authorizes a minimal departure from the source.

Never let a scientific audit silently rewrite chapter prose or equations.

## Errata entries

Keep entries ordered by chapter, then printed page, then item on the same page.

Use these statuses consistently:

- `pending-human-approval` — substantive source issue or proposed correction; reconstruction follows the source until direct human approval.
- `minor-correction` — kept record of a small autonomous correction with no plausible substantive effect.
- `human-approved` — substantive departure explicitly approved by the owner; agents may assign this only when directly instructed in the current chat.

Pending substantive entries should use this field order:

1. **Category:** `transcription`, `typographical`, `equation`, `figure`, `reference`, or `editorial`
2. **Status**
3. **Location**
4. **Source**
5. **Proposed correction**
6. **Reason/evidence**

Do not add a per-entry field saying that the reconstruction was restored to or still follows the source; `pending-human-approval` already implies that state. For `human-approved`, use **Approved correction** instead of **Proposed correction**. For a recorded `minor-correction`, use **Correction** to show the applied text. Do not add a separate approval-evidence field.

Simple confirmed-no-change checks do not belong in `ERRATA.md`. Do not create a second audit ledger. If an erratum concerns a figure, `ERRATA.md` owns the source discrepancy, proposed correction, evidence, and approval state; `FIGURES.md` should only cross-reference the erratum while recording the figure asset and its checks.

## References

Maintain bibliography data only in `src/references.bib`. Verify metadata against primary records when auditing, but source fidelity still governs the rendered reconstruction.

A change that alters a source author name, title, year, citation, quotation, or other bibliographic content is substantive unless it merely restores a mistranscription or makes a clearly mechanical punctuation correction without changing bibliographic identity. Do not silently normalize a source bibliographic error from an external database; propose it for human approval.

## Batch completion

After source changes, run the relevant build. For a coherent repository batch use:

```bash
uv run --frozen python scripts/sync_readme.py
./scripts/build.sh all
```

If the audit affects a figure, also follow `skills/figure-audit/SKILL.md`.
