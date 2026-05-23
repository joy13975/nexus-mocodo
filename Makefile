.PHONY: sync upsert-mods download unzip clean-cache

STARDEW_MODS := $(HOME)/Library/Application Support/Steam/steamapps/common/Stardew Valley/Contents/MacOS/Mods

MODS ?= mods.txt
DEST ?= $(STARDEW_MODS)

sync:
	uv sync

upsert-mods: sync
	uv run python mocodo.py --mods-file "$(MODS)" --dest "$(DEST)"

# Legacy collection.json workflow
download: sync
	uv run python download_mods.py

unzip: sync
	uv run python unzip_mods.py

clean-cache:
	rm -rf downloaded_mods
