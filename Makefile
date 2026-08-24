.DEFAULT_GOAL := all
UV ?= uv
UV_RUN = $(UV) run --frozen
.PHONY: help readme pdf html epub all clean

help:
	@printf '%s\n' \
	  'readme         Regenerate README.md' \
	  'pdf            Build PDF editions' \
	  'html           Build HTML edition' \
	  'epub           Build EPUB edition' \
	  'all            Build all editions' \
	  'clean          Remove generated artifacts'
readme:
	$(UV_RUN) python scripts/sync_readme.py

pdf:
	$(UV_RUN) ./scripts/build.sh pdf

html:
	$(UV_RUN) ./scripts/build.sh html

epub:
	$(UV_RUN) ./scripts/build.sh epub

all: readme
	$(UV_RUN) ./scripts/build.sh all

clean:
	rm -rf build release
