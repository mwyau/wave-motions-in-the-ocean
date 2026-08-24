# Contributing

Pull requests are welcome. Keep changes focused and include the source page or other evidence when correcting text, equations, references, or figures. Pull requests are merged with rebase merge only.

## Setup

The reference environment matches publication CI: Ubuntu 26.04, Python from `.python-version`, uv, TinyTeX 2026.08, and the dependencies in `pyproject.toml`/`uv.lock`. Python tooling also works in a compatible ordinary virtual environment.

Install system tools:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  qpdf poppler-utils pandoc xz-utils wget
```

Set up Python (uv is recommended, but standard venv works):

```bash
# Using uv (recommended)
uv sync

# Or standard venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install the hooks:

```bash
# Using uv
uv run prek install

# Or, from an activated pip/venv environment
prek install
```

## Files

- `references/chapman-rizzoli-1989/*.pdf` — original scans; do not modify them.
- `src/chapter1.tex` through `chapter6.tex` — book text and equations.
- `src/references.bib` — bibliography.
- `src/ERRATA.md` — corrections and supporting evidence.
- `src/FIGURES.md` — figure sources and review status.

## Build and check

Use the caller-selected environment to build editions and run checks:

```bash
# Recommended uv path
uv run make all
uv run pytest -q
uv run prek run --all-files

# Or, from an activated pip/venv environment
make all
python -m pytest -q
prek run --all-files
```

Alternatively, run `./scripts/build.sh [pdf|html|epub|all]`. The script uses the Python already selected by the caller and does not manage dependencies.
For the direct all-editions command, use `uv run ./scripts/build.sh all` in the reference environment or `./scripts/build.sh all` from the activated fallback environment.

The individual Make targets remain available for PDF, HTML, EPUB, README, and clean operations.

CI checks that the generated `requirements.txt` still matches the frozen uv export. Regenerate it after dependency changes with:

```bash
uv export --frozen --format requirements.txt --all-groups --no-hashes --no-header --no-emit-project --output-file requirements.txt
```

For figure changes, also run `scripts/compare_figures.py` for the affected figure.

Do not commit `build/`, `dist/`, caches, or `audit/` review material.

## Commits

Before committing, run all hooks:

```bash
# Using uv
uv run prek run --all-files

# Or, from an activated pip/venv environment
prek run --all-files
```

If a hook changes files, review those changes and rerun the command until all hooks pass. GitHub Actions runs the same checks on pushes and pull requests.

Use a short, readable subject beginning with a capital letter, for example `Correct chapter 5 dispersion relation`. Do not use prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, or `chore:`.
