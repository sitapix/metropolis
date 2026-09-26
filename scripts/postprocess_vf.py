"""Build STAT axis values, typographic names and rasteriser hints on the
variable fonts.

fontmake emits a STAT containing the `wght` axis record with no AxisValue
entries and no `ital` axis.

ttfautohint cannot hint a variable font, so the fonts ship unhinted with a
`gasp` table asking for smoothing at every size and a `prep` program that
turns on smart dropout control, which keeps thin stems from breaking up.

Roman and italic have incompatible masters, so `ital` cannot be an fvar axis.
Each file pins a fixed `ital` location in STAT; the roman carries a LinkedValue
pointing at the italic.
"""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
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

def name_instances(font, is_italic):
    """fvar instance names agree with name 17 and STAT: the default italic is
    "Italic", not "Regular Italic". Each instance also gets a PostScript name."""
    prefix = font["name"].getDebugName(25)
    names = dict(WEIGHTS)
    spaced = {"ExtraLight": "Extra Light", "SemiBold": "Semi Bold", "ExtraBold": "Extra Bold"}
    default = {a.axisTag: a.defaultValue for a in font["fvar"].axes}
    for inst in font["fvar"].instances:
        weight = names[int(inst.coordinates["wght"])]
        style = spaced.get(weight, weight)
        if is_italic:
            style = "Italic" if weight == "Regular" else f"{style} Italic"
        inst.subfamilyNameID = font["name"].addMultilingualName({"en": style}, mac=False)
        if inst.coordinates == default:
            # The default instance is the font itself, so it takes name 6.
            inst.postscriptNameID = 6
        else:
            ps = f"{prefix}-{style.replace(' ', '')}"
            inst.postscriptNameID = font["name"].addMultilingualName({"en": ps}, mac=False)
    # Drop the names fontmake gave the instances; this also scans GSUB
    # featureNames, STAT and fvar, so nothing still referenced goes.
    font["name"].removeUnusedNames(font)

def smart_dropout(font):
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000F}
    font["gasp"] = gasp
    prep = newTable("prep")
    prep.program = ttProgram.Program()
    prep.program.fromAssembly(["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"])
    font["prep"] = prep
    font["maxp"].maxStackElements = max(font["maxp"].maxStackElements, 1)

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
        name_instances(font, is_italic)
        # Only the Windows records are read anywhere current.
        font["name"].removeNames(platformID=1)
        smart_dropout(font)

        font.save(path)
        stat = font["STAT"].table
        n = len(stat.AxisValueArray.AxisValue) if stat.AxisValueArray else 0
        print(f"{path}: STAT axes={[a.AxisTag for a in stat.DesignAxisRecord.Axis]} values={n} italic={is_italic}")

if __name__ == "__main__":
    main(sys.argv[1:])
