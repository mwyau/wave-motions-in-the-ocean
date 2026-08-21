# Source audit skill

Use this skill for scan fidelity, text/equation transcription, scientific verification, and bibliography/reference work.

## Governing rule

The committed historical PDFs under `source/` are the source authority. The purpose of the reconstruction is to reproduce them faithfully, not to silently make substantive changes.

Scientific review is diagnostic. It can identify a likely error and support a proposed erratum, but it does not authorize changing substantive historical content.

## Correction decision order

For every difference or suspected error, use this order:

1. **Reconstruction differs from the PDF unintentionally:** restore the PDF reading unless the difference is a minor mechanical correction allowed by item 2.
2. **Small unambiguous mechanical correction:** spelling, grammar, transcription, punctuation, or TeX punctuation syntax may be corrected autonomously when there is no plausible change in scientific, mathematical, bibliographic, or substantive editorial meaning. If uncertain, do not use this exception.
3. **Substantive or ambiguous source problem:** keep or restore the source reading in the reconstruction, record the proposed correction and evidence in `reconstruction/ERRATA.md` with `pending-human-approval`, and ask the human owner for approval.
4. **Explicit human approval:** only then apply the substantive correction and record it as `human-approved`, with enough context to identify what was approved.

Agents can never approve an erratum. Do not infer approval from mathematical correctness, external literature, issue closure, another agent's judgment, an existing commit, or an existing status. If an older substantive entry lacks traceable explicit human approval, do not treat it as precedent or permission; flag it for human review when encountered.

A minor autonomous correction need not be added to `ERRATA.md`. If it is useful to retain one there, use the existing `minor-typo-correction` status.

## Text fidelity

Compare scan ↔ canonical LaTeX directly. Check wording, punctuation, capitalization, symbols, accents, subscripts/superscripts, footnotes, references, page order, headings, and figure labels.

Preserve historical wording, organization, notation, and derivation style. Do not modernize prose, terminology, equations, or references merely because another form appears clearer or more correct.

If a source reading is uncertain, inspect the highest-quality source view available and leave the reconstruction at the best-supported literal source reading. Record genuine ambiguity as `pending-human-approval` rather than guessing.

Canonical `.tex` uses conventional TeX punctuation. Minor punctuation normalization is allowed when the intended punctuation is unambiguous and the change is purely mechanical: for example, correct quote pairing/apostrophes, distinguish hyphen/en dash/em dash by context, normalize an obvious prose ellipsis, or fix punctuation spacing. Use `-` for hyphens and math minus, `--` for ranges/en dashes, and `---` for parenthetical em dashes. Do not use a blind global replacement: punctuation that could change meaning, scope, emphasis, a citation/title, or mathematical notation is ambiguous and follows the human-approval rule.

## Equation transcription

For every audited equation, compare every sign, coefficient, derivative, index, exponent, vector mark, delimiter, and equality with the scan. Check that definitions immediately before and after the equation use the same symbols and conventions.

A transcription check answers: **does the reconstruction match the historical source?** It is distinct from the scientific audit below.

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

Where practical, verify a standard result against the cited original paper, relevant Hendershott/Myrl material, and another authoritative physical-oceanography source. Clearly distinguish external verification from what the historical PDF actually says.

The outcome of this audit is one of:

- source and reconstruction agree and the science checks;
- reconstruction mistranscribed the source and must be restored;
- source appears questionable and a `pending-human-approval` erratum should be proposed;
- a `human-approved` erratum authorizes a minimal departure from the source.

Never let a scientific audit silently rewrite chapter prose or equations.

## Errata entries

Substantive entries should state:

- **Category:** `transcription`, `typographical`, `equation`, `figure`, `reference`, or `editorial`
- **Status:** `pending-human-approval` for a substantive proposal; `human-approved` only after explicit human approval; `minor-typo-correction` only for a retained record of an autonomous minor correction
- **Location:** source PDF/physical page and/or printed page/chapter
- **Original**
- **Proposed/approved reconstruction**
- **Reason/evidence**
- **Human approval evidence** when status is `human-approved`

Simple confirmed-no-change checks do not belong in `ERRATA.md`. Do not create a second audit ledger.

## References

Maintain bibliography data only in `reconstruction/references.bib`. Verify metadata against primary records when auditing, but source fidelity still governs the rendered reconstruction.

A change that alters a historical author name, title, year, citation, quotation, or other bibliographic content is substantive unless it merely restores a mistranscription or makes a clearly mechanical punctuation correction without changing bibliographic identity. Do not silently normalize a historical bibliographic error from an external database; propose it for human approval.

## Batch completion

After source changes, run the relevant build. For a coherent repository batch use:

```bash
python3 scripts/sync_readme.py
./scripts/build.sh all
```

If the audit affects a figure, also follow `skills/figure-audit/SKILL.md`.
