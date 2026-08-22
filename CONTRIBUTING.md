# Contributing

Pull requests are welcome. Keep changes focused and include the source page or other evidence when correcting text, equations, references, or figures. Pull requests are merged with rebase merge only.

## Setup

The reference environment matches publication CI: Ubuntu 26.04, Python from `.python-version`, uv (recommended), TinyTeX 2026.08, and the dependencies below.

Install system tools:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  qpdf poppler-utils pandoc xz-utils wget
```

Set up Python (uv is recommended, but standard venv works):

```bash
# Using uv (recommended)
uv python install "$(cat .python-version)"
uv venv --python "$(cat .python-version)"
uv pip sync requirements.txt
source .venv/bin/activate

# Or standard venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install TinyTeX and the repository TeX packages:

```bash
export TINYTEX_VERSION=2026.08
wget -qO- "https://tinytex.yihui.org/install-bin-unix.sh" | sh
export PATH="$(find "$HOME/.TinyTeX/bin" -mindepth 1 -maxdepth 1 -type d | head -n 1):$PATH"

tlmgr update --self
mapfile -t PACKAGES < <(grep -Ev '^\s*(#|$)' tex-packages.txt)
tlmgr install "${PACKAGES[@]}"
```

Install pre-commit hooks (`prek` or `pre-commit`):

```bash
prek install       # or pre-commit install
prek run --all-files
```

## Files

- `references/chapman-rizzoli-1989/*.pdf` — original scans; do not modify them.
- `reconstruction/chapter1.tex` through `chapter6.tex` — book text and equations.
- `reconstruction/references.bib` — bibliography.
- `reconstruction/ERRATA.md` — corrections and supporting evidence.
- `reconstruction/FIGURES.md` — figure sources and review status.

## Build and check

Use `make` to build editions and run checks:

```bash
make all      # Build all editions and synchronize README
make pdf      # Build PDF editions (facsimile and modern)
make html     # Build HTML edition
make epub     # Build EPUB edition
make readme   # Synchronize README.md
make clean    # Remove build artifacts
```

Alternatively, run `./scripts/build.sh [pdf|html|epub|all]`.

For figure changes, also run `scripts/compare_figures.py` for the affected figure.

Do not commit `build/`, `dist/`, caches, or `audit/` review material.

## Commits

Use a short, readable subject beginning with a capital letter, for example `Correct chapter 5 dispersion relation`. Do not use prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, or `chore:`.
