"""Build tabular figures, tabular math signs, and a figure space.

Figures are proportional (Regular: 683 357 579 590 631 584 611 563 608 611).
Each is re-centred in a common advance; outlines are unchanged.

Tabular width is the widest figure per master, which is `zero` in all masters,
so no glyph is narrowed. The math signs get `.tnum` copies at the same width,
so `+ − = ×` line up in a column of tabular figures, and U+2007 FIGURE SPACE
takes that width too.

Run after extend_charset.py, which draws `plusminus`.
"""
import copy, sys
import glyphsLib
from glyphsLib.classes import GSClass, GSGlyph, GSLayer

FIGURES = ["zero","one","two","three","four","five","six","seven","eight","nine"]
MATH = ["plus","minus","equal","multiply","divide","less","greater","plusminus"]

def ink_bounds(font, layer, master_id):
    """Horizontal ink extent. Follows components: `nine` is a rotated `six`."""
    xs = [n.position.x for p in layer.paths for n in p.nodes]
    for c in getattr(layer, "components", []):
        ref = font.glyphs[c.name]
        if ref is None:
            continue
        sub = next(l for l in ref.layers if l.layerId == master_id)
        lo, hi = ink_bounds(font, sub, master_id)
        t = c.transform            # (xx, xy, yx, yy, dx, dy)
        for x in (lo, hi):
            xs.append(t[0] * x + t[4])
    return min(xs), max(xs)

def tabular_copy(font, src, width, master_id):
    L = copy.deepcopy(src)
    lo, hi = ink_bounds(font, src, master_id)
    shift = round((width - (hi - lo)) / 2 - lo)
    for p in L.paths:
        for n in p.nodes:
            n.position = type(n.position)(n.position.x + shift, n.position.y)
    for c in getattr(L, "components", []):
        t = list(c.transform); t[4] += shift; c.transform = tuple(t)
    L.width = width
    return L, shift

def glyph(f, name):
    """The named glyph, created at the end if absent; rebuilt in place if not."""
    g = f.glyphs[name]
    if g is None:
        g = GSGlyph(name)
        f.glyphs.append(g)
    for L in list(g.layers):
        del g.layers[L.layerId]
    return g

def set_class(f, name, members):
    code = " ".join(members)
    c = next((c for c in f.classes if c.name == name), None)
    if c is None:
        f.classes.append(GSClass(name, code))
    else:
        c.code = code

def build(path):
    f = glyphsLib.GSFont(path)
    widths = {}
    for m in f.masters:
        widths[m.id] = max(
            next(l for l in f.glyphs[n].layers if l.layerId == m.id).width
            for n in FIGURES)

    made = []
    for name in FIGURES + MATH:
        new = f"{name}.tnum"
        layers = []
        for m in f.masters:
            src = next(l for l in f.glyphs[name].layers if l.layerId == m.id)
            L, shift = tabular_copy(f, src, widths[m.id], m.id)
            L.layerId = L.associatedMasterId = m.id
            layers.append(L)
        g = glyph(f, new)
        for m, L in zip(f.masters, layers):
            g.layers[m.id] = L
        made.append(new)

    g = glyph(f, "figurespace")
    g.unicode = "2007"
    for m in f.masters:
        L = GSLayer()
        L.layerId = L.associatedMasterId = m.id
        L.width = widths[m.id]
        g.layers[m.id] = L

    set_class(f, "Math", MATH)
    set_class(f, "Math_tnum", [f"{n}.tnum" for n in MATH])
    tnum = next(x for x in f.features if x.name == "tnum")
    tnum.code = "    sub @Figures by @Figures_tnum;\n    sub @Math by @Math_tnum;"

    f.save(path)
    print(f"{path}: tabular width per master {[int(widths[m.id]) for m in f.masters]}")
    print(f"   built {len(made)} + figurespace")

for p in sys.argv[1:]:
    build(p)
