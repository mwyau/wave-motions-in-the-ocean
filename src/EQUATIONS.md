# Equation audit

<!-- Generated from src/chapter1.tex through src/chapter6.tex. -->

This is generated review material for the display equations in the six maintained chapter TeX files. The chapter ledgers are the detailed review surface; the mathematical source of truth remains `src/chapter1.tex` through `src/chapter6.tex`.

Each entry shows the source-page crop, a MathJax rendering, and a native MathML rendering. The Markdown math and the raw `<details>` LaTeX block come from the same extracted display. Review the three images against the source PDF and the maintained chapter source.

Run:

```sh
uv run --frozen python scripts/publication.py equations
uv run --frozen python scripts/publication.py equations --check
uv run --frozen python scripts/publication.py equations --assets
uv run --frozen python scripts/publication.py equations --assets --check
```

`--check` regenerates all seven Markdown files in temporary storage and compares their bytes. `--assets` refreshes stable input metadata on the checked-in review PNGs; it does not run during ordinary publication builds. The metadata records the extracted TeX, renderer configuration, and source PDF/page identity, so validation can identify obvious stale assets without recapturing browser screenshots.

The six chapters contain **617 display equations**.

| Chapter | Displays | Ledger |
| --- | ---: | --- |
| Chapter 1 | 48 | [CHAPTER1](equations/CHAPTER1.md) |
| Chapter 2 | 77 | [CHAPTER2](equations/CHAPTER2.md) |
| Chapter 3 | 129 | [CHAPTER3](equations/CHAPTER3.md) |
| Chapter 4 | 120 | [CHAPTER4](equations/CHAPTER4.md) |
| Chapter 5 | 174 | [CHAPTER5](equations/CHAPTER5.md) |
| Chapter 6 | 69 | [CHAPTER6](equations/CHAPTER6.md) |

The raw LaTeX blocks are maintained source excerpts for review. Do not edit them in Markdown; change the chapter TeX only after following the source-audit rules.
