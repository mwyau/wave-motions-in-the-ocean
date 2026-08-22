.DEFAULT_GOAL := all
.PHONY: help readme pdf html epub all clean
PYTHON := uv run --with-requirements requirements.txt python

help:
	@printf '%s\n' \
	  'readme         Regenerate README.md' \
	  'pdf            Build PDF editions' \
	  'html           Build HTML edition' \
	  'epub           Build EPUB edition' \
	  'all            Build all editions' \
	  'clean          Remove generated artifacts'
readme:
	$(PYTHON) scripts/sync_readme.py

pdf:
	./scripts/build.sh pdf

html:
	./scripts/build.sh html

epub:
	./scripts/build.sh epub

all: readme
	./scripts/build.sh all

clean:
	rm -rf build dist
