# Source audit skill

Use this skill for scan fidelity, text/equation transcription, scientific verification, and bibliography/reference work.

## Authority and scope

- The committed historical PDFs under `source/` are the source authority.
- Preserve historical wording, organization, notation, and derivation style unless a change is an independently justified correction.
- Work in small, reviewable page/section batches.
- `reconstruction/ERRATA.md` records substantive deviations and suspected source errors. Do not create a second audit ledger.

## Text fidelity

Compare scan ↔ canonical LaTeX directly. Check wording, punctuation, capitalization, symbols, accents, subscripts/superscripts, footnotes, references, page order, headings, and figure labels. Do not modernize prose merely because it sounds dated.

If a source reading is uncertain, inspect the highest-quality source view available and mark the issue `pending-review` rather than guessing.

## Equation transcription

For every audited equation, compare every sign, coefficient, derivative, index, exponent, vector mark, delimiter, and equality with the scan. Check that definitions immediately before/after the equation use the same symbols and conventions.

A transcription check answers “does the reconstruction match the intended source expression?” It is distinct from the scientific audit below.

## Scientific equation audit

Independently test the mathematics and physics:

- dimensions and units;
- signs and numerical factors;
- coordinate and Fourier/sign conventions;
- definitions of frequency, wavenumber, phase/group velocity, rotation and stratification parameters;
- algebra between derivation steps;
- boundary and matching conditions;
- mode/eigenvalue conventions;
- limiting cases and asymptotic behavior;
- consistency with nearby prose and figures.

Where practical, verify a standard result against the cited original paper, relevant Hendershott/Myrl material, and another authoritative physical-oceanography source. Distinguish a historical source error from a reconstruction/transcription error.

Never silently replace scientifically questionable historical material. Record the source expression, proposed reconstruction, reasoning/evidence, and status in `ERRATA.md` before or with the correction.

## Errata entries

New substantive entries should state:

- **Category:** `transcription`, `typographical`, `equation`, `figure`, `reference`, or `editorial`
- **Status:** `pending-review`, `accepted`, or `reverted`
- **Location:** source PDF/physical page and/or printed page/chapter
- **Original**
- **Reconstruction**
- **Reason/evidence**

Simple confirmed-no-change checks do not belong in `ERRATA.md`.

## References

Maintain bibliography data only in `reconstruction/references.bib`. Use BibTeX/citations rather than manually duplicated bibliography prose. Verify new or changed bibliographic metadata against a primary publisher, journal record, DOI record, or equivalent authoritative source.

## Batch completion

After source changes, run the relevant build; for a coherent repository batch use:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

Update `reconstruction/PLAN.md` only when remaining work changes. If the audit affects a figure, also follow `skills/figure-audit/SKILL.md`.
