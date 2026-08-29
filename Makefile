.DEFAULT_GOAL := all
UV ?= uv
UV_RUN = $(UV) run --frozen
.PHONY: help readme pdf html epub all validate clean

help:
	@printf '%s\n' \
	  'readme         Regenerate README.md' \
	  'pdf            Build PDF editions' \
	  'html           Build HTML edition' \
	  'epub           Build EPUB edition' \
	  'all            Build all editions' \
	  'validate       Validate the generated publication' \
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

validate:
	$(UV_RUN) python scripts/validate.py all

clean:
	rm -rf build release
