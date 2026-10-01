VENV := .venv/bin
.DEFAULT_GOAL := all

.PHONY: all static ttf variable webfonts specimen specimen-image social-preview dist check clean venv

include make/fonts.mk make/artwork.mk make/specimen.mk

dist:
	$(VENV)/python scripts/make_dist.py $(VERSION)

clean:
	rm -rf fonts master_ufo instance_ufo variable_ttf specimen/_site dist
