ROMAN := sources/Metropolis.glyphs
ITALIC := sources/Metropolis-Italic.glyphs

all: static ttf variable webfonts

venv:
	uv venv
	uv pip install -q -r requirements.txt

static:
	@mkdir -p fonts/otf
	$(VENV)/fontmake -g $(ROMAN)  -i -o otf --output-dir fonts/otf
	$(VENV)/fontmake -g $(ITALIC) -i -o otf --output-dir fonts/otf
	$(VENV)/python scripts/postprocess_static.py fonts/otf/*.otf
	@# fontmake does not hint CFF. otfautohint drops the subroutines, so put them back.
	$(VENV)/otfautohint fonts/otf/*.otf
	for f in fonts/otf/*.otf; do $(VENV)/cffsubr -i "$$f"; done

# Hinted TrueType wants neither nested nor scaled components; the superiors
# and fractions have scaled ones.
TTF_FILTERS := --filter '...' --filter FlattenComponentsFilter --filter DecomposeTransformedComponentsFilter

ttf:
	@mkdir -p fonts/ttf
	$(VENV)/fontmake -g $(ROMAN)  -i -o ttf --autohint $(TTF_FILTERS) --output-dir fonts/ttf
	$(VENV)/fontmake -g $(ITALIC) -i -o ttf --autohint $(TTF_FILTERS) --output-dir fonts/ttf
	$(VENV)/python scripts/postprocess_static.py fonts/ttf/*.ttf

variable:
	@mkdir -p fonts/variable
	$(VENV)/fontmake -g $(ROMAN)  -o variable $(TTF_FILTERS) --output-path 'fonts/variable/Metropolis[wght].ttf'
	$(VENV)/fontmake -g $(ITALIC) -o variable $(TTF_FILTERS) --output-path 'fonts/variable/Metropolis-Italic[wght].ttf'
	@# fontmake emits STAT with no axis values and no ital axis.
	$(VENV)/python scripts/postprocess_vf.py 'fonts/variable/Metropolis[wght].ttf' 'fonts/variable/Metropolis-Italic[wght].ttf'

webfonts:
	$(VENV)/python scripts/make_webfonts.py

check:
	$(VENV)/python scripts/check_fonts.py
