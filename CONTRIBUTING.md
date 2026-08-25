# Contributing

Keep changes focused. For corrections to reconstructed text, equations,
references, or figures, include the source page or other evidence. Read
`AGENTS.md` before changing reconstructed material.

## Install system prerequisites

On a clean Ubuntu/Debian machine, install the system tools before using the
setup commands below:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  curl git make qpdf poppler-utils pandoc unzip xz-utils wget \
  default-jre-headless nodejs
```

Chromium is separate and optional; install it only for HTML visual and browser
regression QA.

## Set up Python

Python development uses [uv](https://docs.astral.sh/uv/) only. Install uv with
its official installer, then use the Python version in `.python-version`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install "$(cat .python-version)"
uv sync --frozen
uv run --frozen prek install
```

`pyproject.toml` and `uv.lock` are the Python dependency sources.

## Install publication tools

The PDF and EPUB builds use TinyTeX. The HTML JavaScript syntax check also
needs Node.js; it is not needed for the normal build.

### TinyTeX 2026.08

TinyTeX is a compact TeX Live distribution. TinyTeX / TeX Live 2026.08 is the
recommended and tested environment for this repository, using LuaLaTeX and
LuaHBTeX. You do not need both TinyTeX and a separate full TeX Live install.

Install TinyTeX, put its binaries first on `PATH`, and install the packages
listed in `tex-packages.txt`:

```bash
export TINYTEX_VERSION=2026.08
wget -qO- https://tinytex.yihui.org/install-bin-unix.sh | sh

TEXBIN="$(find "$HOME/.TinyTeX/bin" \
  -mindepth 1 -maxdepth 1 -type d | head -n 1)"
export PATH="$TEXBIN:$PATH"

tlmgr update --self
mapfile -t PACKAGES < <(grep -Ev '^\s*(#|$)' tex-packages.txt)
tlmgr install "${PACKAGES[@]}"

command -v lualatex
lualatex --version
command -v tlmgr
```

If an older distro TeX Live also provides `/usr/bin/lualatex`, keep the
TinyTeX directory before it on `PATH`.

A recent full TeX Live installation may also work if it provides the packages
listed in `tex-packages.txt`, but TinyTeX 2026.08 is the environment used and
tested by CI.

### EPUBCheck

EPUBCheck 5.3.0 and Java are required for strict EPUB validation. Unpack it in
a user-owned directory:

```bash
EPUBCHECK_VERSION=5.3.0
mkdir -p "$HOME/.local/share"
curl -fL \
  "https://github.com/w3c/epubcheck/releases/download/v${EPUBCHECK_VERSION}/epubcheck-${EPUBCHECK_VERSION}.zip" \
  -o /tmp/epubcheck.zip
unzip -q /tmp/epubcheck.zip -d "$HOME/.local/share"

export EPUBCHECK_JAR="$HOME/.local/share/epubcheck-${EPUBCHECK_VERSION}/epubcheck.jar"
java -jar "$EPUBCHECK_JAR" --version
```

## Run the checks

For normal source or code work:

```bash
uv run --frozen pytest -q
uv run --frozen prek run --all-files
```

For the HTML JavaScript syntax check, after installing Node.js:

```bash
node --check src/layout/wave-html.js
```

## Build and validate the book

Build all editions with the repository's normal command:

```bash
make all
```

The direct equivalent is:

```bash
uv run --frozen ./scripts/build.sh all
```

After installing EPUBCheck, run strict full validation:

```bash
uv run --frozen python scripts/validate.py all --require-epubcheck
```

## Optional HTML visual QA

Chromium is needed only for optional HTML visual and browser regression QA. It
is not needed for editing, unit tests, hooks, or the basic publication build.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y chromium
chromium --headless --version
```

If Chromium is installed elsewhere, set `WAVE_CHROMIUM` to its executable:

```bash
export WAVE_CHROMIUM=/path/to/chromium
```

After `make all`, run the render QA described in
`skills/render-qa/SKILL.md`:

```bash
uv run --frozen python scripts/render_qa.py release
```

The browser pass includes the narrow direct-fragment check when Chromium is
available.

## Source files

- `src/chapter1.tex` through `src/chapter6.tex` — reconstructed chapters
- `src/references.bib` — bibliography
- `references/chapman-rizzoli-1989/` — original 1989 source scans

For HTML, a TikZ figure with `wave-source` metadata can show either its
reconstructed SVG or an original source-crop PNG. Maintain those generated
same-stem assets beside the TikZ source with:

```bash
uv run --frozen python scripts/compare_figures.py <figure-stem>
```

The SVG and PNG are derived review assets, not independently edited source.
The build checks and copies the committed files into `release/assets/figures/`.

Generated files under `build/`, `release/`, and `audit/` are not committed.

## Before committing

Run:

```bash
uv run --frozen pytest -q
uv run --frozen prek run --all-files
```

For publication or HTML layout changes, also run the relevant build, strict
validation, or render-QA command above.
