.DEFAULT_GOAL := all
UV ?= uv
UV_RUN = $(UV) run --frozen
.PHONY: help readme pdf html epub all check validate qa qa-release clean

help:
	@printf '%s\n' \
	  'readme         Regenerate README.md' \
	  'pdf            Build PDF editions' \
	  'html           Build HTML edition' \
	  'epub           Build EPUB edition' \
	  'all            Build all editions' \
	  'check          Run source checks and tests' \
	  'validate       Validate the generated publication' \
	  'qa             Run strict publication render QA' \
	  'qa-release     Run full stable-release QA' \
	  'clean          Remove generated artifacts'

readme:
	$(UV_RUN) python scripts/sync_readme.py

pdf:
	$(UV_RUN) python scripts/build_pdf.py

html:
	$(UV_RUN) python scripts/build_html.py

epub:
	$(UV_RUN) python scripts/build_epub.py

all:
	$(MAKE) --no-print-directory clean
	$(MAKE) --no-print-directory pdf
	$(MAKE) --no-print-directory epub
	$(MAKE) --no-print-directory html
	$(UV_RUN) python scripts/release.py finalize --root release

check:
	$(UV_RUN) python -m pytest -q
	node --check src/layout/wave-html.js
	node --check src/layout/wave-service-worker.js
	$(UV_RUN) python scripts/publication.py audit-check --all
	$(UV_RUN) prek run --all-files --skip audit-freshness

validate:
	$(UV_RUN) python scripts/validate.py all

qa:
	$(UV_RUN) python scripts/render_qa.py release --strict

qa-release:
	$(UV_RUN) python scripts/render_qa.py release --strict --visual
	$(UV_RUN) python scripts/validate.py release

clean:
	rm -rf build release
