"""Assert vertical-metric, axis, and STAT invariants on every built font.

Each check corresponds to a defect present in upstream r11.
"""
import glob, sys
from fontTools.ttLib import TTFont

LINE_BOX = 1210          # hhea and typo must sum to this
fails = []
files = sorted(glob.glob("fonts/**/*.otf", recursive=True) + glob.glob("fonts/**/*.ttf", recursive=True))
if not files:
    sys.exit("no fonts built")

for path in files:
    f = TTFont(path, lazy=True)
    head, hhea, os2 = f["head"], f["hhea"], f["OS/2"]

    def bad(msg):
        fails.append(f"{path}: {msg}")

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
    if "fvar" in f:
        tags = [a.axisTag for a in f["fvar"].axes]
        for a in f["fvar"].axes:
            if a.minValue == a.maxValue:
                bad(f"single-valued axis {a.axisTag}")
        stat = f["STAT"].table
        if not stat.AxisValueArray or not stat.AxisValueArray.AxisValue:
            bad("STAT has no axis values")
        if "ital" not in [a.AxisTag for a in stat.DesignAxisRecord.Axis]:
            bad("STAT has no ital axis")

for x in fails:
    print("FAIL", x)
print(f"{'FAILED' if fails else 'ok'}: {len(files)} fonts, {len(fails)} problems")
sys.exit(1 if fails else 0)
