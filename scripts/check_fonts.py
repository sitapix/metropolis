"""Assert metadata, coverage and hinting invariants on every built font.

Each check corresponds to a defect present in upstream r11 or in this fork's
first release.
"""
import glob, sys
from fontTools.ttLib import TTFont

LINE_BOX = 1210          # hhea and typo must sum to this
# Windows-1252, which upstream r11 did not cover, plus the controls and
# spaces that a web page reaches for.
# U+00AD SOFT HYPHEN is deliberately absent: the renderer draws the hyphen.
WIN1252 = ([c for c in range(0x20, 0x100) if not 0x7F <= c < 0xA0 and c != 0xAD]
           + [0x152, 0x153, 0x160, 0x161, 0x178, 0x17D, 0x17E, 0x192, 0x2C6, 0x2DC,
              0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E,
              0x2020, 0x2021, 0x2022, 0x2026, 0x2030, 0x2039, 0x203A, 0x20AC, 0x2122])
# Latvian and Romanian, which the OS/2 code-page bits and the glyph set imply.
LATIN_EXTRA = [0x13B, 0x13C, 0x218, 0x219, 0x21A, 0x21B, 0x2007, 0x2044]
TNUM = ["zero", "plus", "minus", "equal", "multiply", "divide", "less", "greater", "plusminus"]

fails = []
files = sorted(glob.glob("fonts/**/*.otf", recursive=True) + glob.glob("fonts/**/*.ttf", recursive=True))
if not files:
    sys.exit("no fonts built")

for path in files:
    f = TTFont(path, lazy=True)
    head, hhea, os2, name = f["head"], f["hhea"], f["OS/2"], f["name"]
    variable = "fvar" in f

    def bad(msg):
        fails.append(f"{path}: {msg}")

    # Vertical metrics.
    if hhea.ascent - hhea.descent + hhea.lineGap != LINE_BOX:
        bad(f"line box {hhea.ascent - hhea.descent + hhea.lineGap} != {LINE_BOX}")
    if os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap != LINE_BOX:
        bad("typo metrics disagree with hhea")
    # macOS substitutes a 1.2 em line box when ascent + descent equals the UPM.
    if hhea.ascent - hhea.descent == head.unitsPerEm:
        bad("ascent + descent equals the UPM")
    if os2.usWinAscent < head.yMax or os2.usWinDescent < abs(head.yMin):
        bad(f"win metrics clip the ink ({head.yMin}..{head.yMax})")
    if not os2.fsSelection & (1 << 7):
        bad("USE_TYPO_METRICS not set")
    if os2.version < 4:
        bad(f"OS/2 version {os2.version} < 4, so USE_TYPO_METRICS is not legal")

    # Names and licensing. A public-domain font must not restrict embedding.
    for nid, what in ((0, "copyright"), (9, "designer"), (13, "license"), (14, "license URL")):
        if not name.getDebugName(nid):
            bad(f"name {nid} ({what}) is empty")
    if any(n.platformID == 1 for n in name.names):
        bad("carries Mac name records")
    if os2.fsType != 0:
        bad(f"fsType {os2.fsType} restricts embedding")
    # Style linking: every weight-400 italic belongs to the family "Metropolis",
    # or Windows finds no Italic for Regular.
    if not variable and os2.fsSelection & 1 and os2.usWeightClass == 400:
        if (name.getDebugName(1), name.getDebugName(2)) != ("Metropolis", "Italic"):
            bad(f"Italic named {name.getDebugName(1)!r} / {name.getDebugName(2)!r}")

    # Coverage.
    cmap = f.getBestCmap()
    missing = [f"U+{c:04X}" for c in WIN1252 + LATIN_EXTRA if c not in cmap]
    if missing:
        bad(f"missing {' '.join(missing)}")
    if not variable and any(".BRACKET." in g for g in f.getGlyphOrder()):
        bad("ships an unreachable bracket-layer glyph")

    # Layout: latn in GSUB, and tabular math at the tabular figure width.
    if "latn" not in [s.ScriptTag for s in f["GSUB"].table.ScriptList.ScriptRecord]:
        bad("GSUB has no latn script")
    hmtx = f["hmtx"]
    widths = {hmtx[f"{g}.tnum"][0] for g in TNUM if f"{g}.tnum" in hmtx.metrics}
    figure_space = {hmtx[cmap[0x2007]][0]} if 0x2007 in cmap else set()
    if len(widths) != 1 or widths != figure_space:
        bad(f"tabular glyphs and figure space disagree: {sorted(widths)}")

    # Hinting. Static TrueType is ttfautohinted; variable TrueType gets smart
    # dropout and gasp; CFF carries stem hints.
    if "glyf" in f:
        if "gasp" not in f or "prep" not in f:
            bad("TrueType without gasp and prep")
        if not variable and "fpgm" not in f:
            bad("static TrueType is not hinted")
    else:
        cff = f["CFF "].cff
        cff.desubroutinize()
        cs = cff.topDictIndex[0].CharStrings["H"]
        cs.decompile()
        hinted = any(isinstance(x, str) and "stem" in x for x in cs.program)
        if not hinted:
            bad("CFF is not hinted")

    if variable:
        tags = [a.axisTag for a in f["fvar"].axes]
        for a in f["fvar"].axes:
            if a.minValue == a.maxValue:
                bad(f"single-valued axis {a.axisTag}")
        stat = f["STAT"].table
        if not stat.AxisValueArray or not stat.AxisValueArray.AxisValue:
            bad("STAT has no axis values")
        if "ital" not in [a.AxisTag for a in stat.DesignAxisRecord.Axis]:
            bad("STAT has no ital axis")
        # The default instance carries the same subfamily name as the font.
        default = {a.axisTag: a.defaultValue for a in f["fvar"].axes}
        typo = name.getDebugName(17) or name.getDebugName(2)
        for inst in f["fvar"].instances:
            if inst.coordinates == default and name.getDebugName(inst.subfamilyNameID) != typo:
                bad(f"default instance named {name.getDebugName(inst.subfamilyNameID)!r}, not {typo!r}")
            if inst.postscriptNameID in (None, 0xFFFF):
                bad("fvar instance without a PostScript name")

for x in fails:
    print("FAIL", x)
print(f"{'FAILED' if fails else 'ok'}: {len(files)} fonts, {len(fails)} problems")
sys.exit(1 if fails else 0)
