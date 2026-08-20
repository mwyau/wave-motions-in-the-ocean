# Contributing

Pull requests are welcome. Keep changes focused and include the source page or other evidence when correcting text, equations, references, or figures. Pull requests are merged with rebase merge only.

## Setup

The reference environment is Ubuntu 26.04 with Python 3.14, uv 0.12.1, TinyTeX 2026.08, Pillow, Pandoc, Poppler, qpdf, Ghostscript, ImageMagick, and librsvg.

Install the system tools:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  qpdf poppler-utils imagemagick ghostscript pandoc librsvg2-bin texinfo xz-utils
```

Set up Python:

```bash
uv python install "$(cat .python-version)"
uv venv --python "$(cat .python-version)"
uv pip sync requirements.txt
source .venv/bin/activate
```

Install TinyTeX 2026.08, then install the TeX packages used by the book:

```bash
export TINYTEX_VERSION=2026.08
wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
mapfile -t PACKAGES < <(grep -Ev '^\s*(#|$)' tex-packages.txt)
tlmgr install "${PACKAGES[@]}"
```

## Files

- `source/*.pdf` — original scans; do not modify them.
- `reconstruction/chapter1.tex` through `chapter6.tex` — book text and equations.
- `reconstruction/references.bib` — bibliography.
- `reconstruction/ERRATA.md` — corrections and supporting evidence.
- `reconstruction/FIGURES.md` — figure sources and review status.

## Build and check

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For figure changes, also run `scripts/compare-figures.py` for the affected figure.

Do not commit `build/`, `dist/`, caches, or generated comparison images.

## Commits

Use a short, readable subject beginning with a capital letter, for example `Correct chapter 5 dispersion relation`. Do not use prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, or `chore:`.
