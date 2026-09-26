"""Drop the bracket-layer alternates and the Mac name records from the static
fonts, and flag hinted TrueType as rounding to integer ppem.

`cent` and `dollar` carry a bracket layer above wght 700. In a static instance
fontmake swaps the right drawing into `cent`/`dollar` and still ships the other
one as `*.BRACKET.varAlt01`, which nothing in cmap or GSUB can reach. The
variable fonts need both and are not touched.

Everything else is kept as fontmake wrote it: names, hinting, features and
glyph names pass through the subsetter unchanged.
"""
import sys
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont


def options():
    o = Options()
    o.glyph_names = True
    o.legacy_kern = True
    o.layout_features = ["*"]
    o.layout_scripts = ["*"]
    o.name_IDs = ["*"]
    o.name_languages = ["*"]
    o.name_legacy = True
    o.notdef_glyph = o.notdef_outline = True
    o.recommended_glyphs = True
    o.hinting = True
    o.hinting_tables = ["*"]
    o.drop_tables = []
    o.passthrough_tables = True
    o.prune_unicode_ranges = False
    o.prune_codepage_ranges = False
    o.symbol_cmap = True
    return o


def main(paths):
    for path in paths:
        font = TTFont(path)
        # Only the Windows name records are read anywhere current.
        font["name"].removeNames(platformID=1)
        # ttfautohint's instructions assume integer ppem sizes.
        if "fpgm" in font:
            font["head"].flags |= 1 << 3
        dead = [g for g in font.getGlyphOrder() if ".BRACKET." in g]
        if not dead:
            font.save(path)
            continue
        keep = [g for g in font.getGlyphOrder() if g not in dead]
        s = Subsetter(options())
        s.populate(glyphs=keep, unicodes=font.getBestCmap().keys())
        s.subset(font)
        font.save(path)
        print(f"{path}: dropped {', '.join(dead)}")


if __name__ == "__main__":
    main(sys.argv[1:])
