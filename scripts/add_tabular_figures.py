"""Build tabular figures.

Figures are proportional (Regular: 683 357 579 590 631 584 611 563 608 611).
Each is re-centred in a common advance; outlines are unchanged.

Tabular width is the widest figure per master, which is `zero` in all masters,
so no glyph is narrowed.
"""
import copy, sys
import glyphsLib
from glyphsLib.classes import GSGlyph, GSLayer

FIGURES = ["zero","one","two","three","four","five","six","seven","eight","nine"]

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

def build(path):
    f = glyphsLib.GSFont(path)
    widths = {}
    for m in f.masters:
        widths[m.id] = max(
            next(l for l in f.glyphs[n].layers if l.layerId == m.id).width
            for n in FIGURES)

    made = []
    for name in FIGURES:
        new = f"{name}.tnum"
        if f.glyphs[new]:
            del f.glyphs[new]
        g = GSGlyph(new)
        f.glyphs.append(g)
        for m in f.masters:
            src = next(l for l in f.glyphs[name].layers if l.layerId == m.id)
            L, shift = tabular_copy(f, src, widths[m.id], m.id)
            L.layerId = m.id; L.associatedMasterId = m.id
            g.layers[m.id] = L
        made.append(new)
    f.save(path)
    print(f"{path}: tabular width per master {[int(widths[m.id]) for m in f.masters]}")
    print(f"   created {len(made)}: {made}")

for p in sys.argv[1:]:
    build(p)
