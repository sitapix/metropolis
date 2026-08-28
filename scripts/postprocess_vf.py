"""Build STAT axis values and typographic names on the variable fonts.

fontmake emits a STAT containing the `wght` axis record with no AxisValue
entries and no `ital` axis.

Roman and italic have incompatible masters, so `ital` cannot be an fvar axis.
Each file pins a fixed `ital` location in STAT; the roman carries a LinkedValue
pointing at the italic.
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildStatTable

ELIDABLE = 0x2

WEIGHTS = [
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
    (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
    (900, "Black"),
]

def stat_axes(is_italic):
    weight = dict(
        tag="wght", name="Weight", ordering=0,
        values=[
            dict(value=v, name=n, flags=(ELIDABLE if v == 400 else 0))
            for v, n in WEIGHTS
        ],
    )
    if is_italic:
        italic = dict(tag="ital", name="Italic", ordering=1,
                      values=[dict(value=1, name="Italic")])
    else:
        # Elided: "Metropolis Regular", not "Metropolis Roman Regular".
        italic = dict(tag="ital", name="Italic", ordering=1,
                      values=[dict(value=0, name="Roman", flags=ELIDABLE, linkedValue=1)])
    return [weight, italic]

def set_name(font, nameID, string):
    font["name"].setName(string, nameID, 3, 1, 0x409)
    font["name"].setName(string, nameID, 1, 0, 0)

def main(paths):
    for path in paths:
        font = TTFont(path)
        is_italic = bool(font["OS/2"].fsSelection & 1)
        family = font["name"].getDebugName(1)

        buildStatTable(font, stat_axes(is_italic), elidedFallbackName=2)

        # Nine weights exceed what name1/name2 can express.
        set_name(font, 16, family)
        set_name(font, 17, "Italic" if is_italic else "Regular")
        # Variable PostScript name prefix.
        set_name(font, 25, family.replace(" ", "") + ("Italic" if is_italic else ""))

        font.save(path)
        stat = font["STAT"].table
        n = len(stat.AxisValueArray.AxisValue) if stat.AxisValueArray else 0
        print(f"{path}: STAT axes={[a.AxisTag for a in stat.DesignAxisRecord.Axis]} values={n} italic={is_italic}")

if __name__ == "__main__":
    main(sys.argv[1:])
