VENV := .venv/bin
ROMAN  := sources/Metropolis.glyphs
ITALIC := sources/Metropolis-Italic.glyphs

.PHONY: all static ttf variable webfonts specimen specimen-image dist check clean venv

all: static ttf variable webfonts

venv:
	uv venv
	uv pip install -q -r requirements.txt

static:
	@mkdir -p fonts/otf
	$(VENV)/fontmake -g $(ROMAN)  -i -o otf --output-dir fonts/otf
	$(VENV)/fontmake -g $(ITALIC) -i -o otf --output-dir fonts/otf

ttf:
	@mkdir -p fonts/ttf
	$(VENV)/fontmake -g $(ROMAN)  -i -o ttf --output-dir fonts/ttf
	$(VENV)/fontmake -g $(ITALIC) -i -o ttf --output-dir fonts/ttf

variable:
	@mkdir -p fonts/variable
	$(VENV)/fontmake -g $(ROMAN)  -o variable --output-path 'fonts/variable/Metropolis[wght].ttf'
	$(VENV)/fontmake -g $(ITALIC) -o variable --output-path 'fonts/variable/Metropolis-Italic[wght].ttf'
	@# fontmake emits STAT with no axis values and no ital axis.
	$(VENV)/python scripts/postprocess_vf.py 'fonts/variable/Metropolis[wght].ttf' 'fonts/variable/Metropolis-Italic[wght].ttf'

webfonts:
	$(VENV)/python scripts/make_webfonts.py

specimen-image:
	$(VENV)/python scripts/make_specimen_image.py

specimen:
	@mkdir -p specimen/src/fonts
	cp 'fonts/webfonts/Metropolis[wght].woff2' 'fonts/webfonts/Metropolis-Italic[wght].woff2' specimen/src/fonts/
	cd specimen && bun install --frozen-lockfile && bun run build
	@echo "built specimen/_site/index.html"

dist:
	$(VENV)/python scripts/make_dist.py $(VERSION)

check:
	$(VENV)/python scripts/check_fonts.py

clean:
	rm -rf fonts master_ufo instance_ufo variable_ttf specimen/_site dist
