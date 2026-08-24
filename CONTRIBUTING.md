# Contributing

Pull requests are welcome. Keep changes focused and include the source page or other evidence when correcting text, equations, references, or figures.

Read `AGENTS.md` before changing reconstructed material.

## Set up the repository

Python tools use [uv](https://docs.astral.sh/uv/).

Install uv, clone the repository, and install the locked dependencies:

```bash
uv sync --frozen
```

Install the Git hooks:

```bash
uv run --frozen prek install
```

## Install publication tools

On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  qpdf poppler-utils pandoc xz-utils wget
```

The PDF build uses TinyTeX 2026.08 and LuaLaTeX. See `tex-packages.txt` and the publication CI workflow for the TeX packages used by the project.

EPUB validation also uses EPUBCheck.

## Install Chromium for HTML render checks

Chromium is needed for visual testing of the HTML edition. It runs headlessly, so a graphical desktop is not required.

Ubuntu distributes Chromium through Snap:

```bash
sudo snap install chromium
chromium --headless --version
```

On Debian:

```bash
sudo apt-get update
sudo apt-get install chromium
chromium --headless --version
```

If Chromium is installed somewhere else, set:

```bash
export WAVE_CHROMIUM=/path/to/chromium
```

Chromium is only needed for browser render checks. It is not needed to edit the book, run unit tests, or run the normal source hooks.

## Run the checks

Run the unit tests:

```bash
uv run --frozen pytest -q
```

Run formatting, linting, and repository checks:

```bash
uv run --frozen prek run --all-files
```

If a hook changes a file, review the change and run the command again.

## Build the book

Build every edition:

```bash
make all
```

Individual targets are also available:

```bash
make pdf
make html
make epub
```

You can also use the build script directly:

```bash
uv run --frozen ./scripts/build.sh all
```

## Check HTML rendering

After changing HTML, CSS, JavaScript, MathJax/MathML rendering, or responsive layout, run the render QA described in `skills/render-qa/SKILL.md`.

It uses headless Chromium to check the reader at the supported viewport and text-size combinations.

## Working with the reconstructed text

The main source files are:

- `src/chapter1.tex` through `chapter6.tex` — reconstructed text and equations
- `src/references.bib` — bibliography
- `src/ERRATA.md` — proposed and reviewed corrections
- `src/FIGURES.md` — figure sources and review status
- `references/chapman-rizzoli-1989/` — original 1989 scans

Use the 1989 scans when checking the reconstruction. Later notes and other references can help check the science, but they do not replace the 1989 source.

For figure changes, run the figure comparison tool for the affected figure.

## Before committing

For most changes:

```bash
uv run --frozen pytest -q
uv run --frozen prek run --all-files
```

For publication changes, also build the affected formats.

For HTML layout or rendering changes, also run the headless Chromium render QA.

Generated files under `build/`, `release/`, `audit/`, and cache directories are not committed.

## Commits

Use a short, readable commit subject beginning with a capital letter, for example:

```text
Correct chapter 5 dispersion relation
```

The repository uses rebase merges for pull requests.
