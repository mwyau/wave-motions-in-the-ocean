# Contributing

This repository is an active scholarly reconstruction of *Wave Motions in the Ocean: Myrl's View*. The historical scans in `source/` remain the authority; the reconstructed editions share one corrected LaTeX body.

## Current contribution policy

Pull requests are not part of the active maintainer workflow yet. Do not open a PR unless the repository owner has explicitly enabled PR-based contributions. Dependabot update PRs are the standing exception.

For proposed textual, mathematical, bibliographic, or figure corrections, an issue with the source location and supporting evidence is useful even while PR-based contributions are paused.

## Development environment

The reference build environment is Ubuntu 26.04 with:

- Python 3.14.7, managed with uv 0.12.1
- Pillow from `requirements.txt`
- TinyTeX 2026.08 plus the packages in `tex-packages.txt`
- `pandoc`, `qpdf`, Poppler, Ghostscript, ImageMagick, and `librsvg2-bin`

Install the system tools on Ubuntu with:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  qpdf poppler-utils imagemagick ghostscript pandoc librsvg2-bin
```

Install uv 0.12.1, then create the pinned Python environment:

```bash
uv python install "$(cat .python-version)"
uv venv --python "$(cat .python-version)"
uv pip sync requirements.txt
source .venv/bin/activate
```

Install TinyTeX 2026.08 using the official TinyTeX installer, then install the repository package manifest:

```bash
mapfile -t PACKAGES < <(grep -Ev '^\s*(#|$)' tex-packages.txt)
tlmgr install "${PACKAGES[@]}"
```

## Where to edit

- `source/*.pdf` — immutable historical scans; never modify them.
- `reconstruction/chapter1.tex` … `chapter6.tex` — canonical chapter text and mathematics.
- `reconstruction/frontmatter-modern.tex` — canonical modern front matter.
- `reconstruction/frontmatter-facsimile.tex` — source-faithful facsimile front matter.
- `reconstruction/references.bib` — canonical bibliography.
- `reconstruction/ERRATA.md` — substantive corrections and evidence.
- `reconstruction/FIGURES.md` — figure provenance and audit status.
- `reconstruction/PLAN.md` — remaining work only.

Do not silently modernize historical prose or silently repair questionable science. Preserve the historical form unless a correction is independently supported, and record substantive deviations in `ERRATA.md`.

## Build

Use the single build interface:

```bash
./scripts/build.sh pdf
./scripts/build.sh html
./scripts/build.sh epub
./scripts/build.sh all
```

`build/`, `dist/`, caches, and generated comparison images are temporary and must not be committed.

When canonical front matter or headings change, regenerate the README:

```bash
python3 scripts/sync-views.py --readme
```

Before committing a coherent batch, run:

```bash
python3 scripts/sync-views.py --readme
./scripts/build.sh all
```

For changed figures, also regenerate the relevant source comparison with `scripts/compare-figures.py`.

## Commit messages

Use a short human-readable subject beginning with a capital letter, for example:

```text
Refine shallow-water figures
Pin publication dependencies
Correct the chapter 5 dispersion relation
```

Do not use Conventional Commit prefixes such as `ci:`, `docs:`, `feat:`, `fix:`, or `chore:`.
