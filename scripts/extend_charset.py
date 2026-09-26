"""Add the characters upstream r11 lacks: the rest of Windows-1252, Latvian
Ļ ļ, Romanian Ș ș Ț ț, and the no-break space.

U+00AD SOFT HYPHEN is left out on purpose: renderers show a hyphen glyph at
the break themselves, and a drawn soft hyphen can appear where it should not.

Every new glyph is built from each master's own parts, so it interpolates:
components where an existing glyph already carries the shape, and
rectangles and rings measured from that master's `bar`, `plus` and `minus`
where it does not. Italic masters are built upright and re-slanted.

Glyphs whose drawing is a construction rather than a design (scaled figures,
stacked `s`, the currency ring) are coloured magenta for review in Glyphs.

Like add_tabular_figures.py this writes into sources/ and is not part of
`make`. It is idempotent: an existing glyph of the same name is rebuilt.
"""
import math, sys
import glyphsLib
from glyphsLib.classes import GSAnchor, GSComponent, GSGlyph, GSLayer, GSNode, GSPath
from glyphsLib.types import Point

REVIEW = 9          # Glyphs colour index: magenta
SUP_SCALE = 0.62    # superiors, fractions and ordinals
FIG_TOP = 699       # top of the figures, overshoot included
KAPPA = 0.5523


class Master:
    """One master's geometry, read upright."""

    def __init__(self, font, master):
        self.font, self.m = font, master
        self.tan = math.tan(math.radians(master.italicAngle or 0))

    def layer(self, name):
        return next(l for l in self.font.glyphs[name].layers if l.layerId == self.m.id)

    def up(self, x, y):
        return x - y * self.tan

    def slant(self, pts):
        return [(round(x + y * self.tan), round(y)) for x, y in pts]

    def oncurves(self, name, path=None):
        paths = self.layer(name).paths if path is None else [self.layer(name).paths[path]]
        return [(self.up(n.position.x, n.position.y), n.position.y)
                for p in paths for n in p.nodes if n.type != "offcurve"]

    def rect(self, name, path=0):
        """Upright box of a rectangle path: x0, y0, x1, y1."""
        pts = self.oncurves(name, path)
        # Upright, a slanted bar's ends are at one x each; average the pairs.
        ys = sorted({y for _, y in pts})
        lo = sorted(x for x, y in pts if y == ys[0])
        hi = sorted(x for x, y in pts if y == ys[-1])
        return (lo[0] + hi[0]) / 2, ys[0], (lo[-1] + hi[-1]) / 2, ys[-1]

    def plus(self):
        """Horizontal bar and vertical stem of `plus`, whichever order they come in."""
        a, b = self.rect("plus", 0), self.rect("plus", 1)
        h, v = (a, b) if a[2] - a[0] > b[2] - b[0] else (b, a)
        return h, v


def ccw(pts):
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if area > 0 else pts[::-1]


def rect(x0, y0, x1, y1):
    return [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def line_path(M, pts):
    p = GSPath()
    for x, y in M.slant(ccw(pts)):
        p.nodes.append(GSNode((x, y), "line"))
    p.closed = True
    return p


def ring_path(M, cx, cy, r, clockwise=False):
    """A circle as four curves; counter-clockwise for ink, clockwise for a counter."""
    step = -90 if clockwise else 90
    pts = []
    for k in range(4):
        a0, a1 = math.radians(k * step), math.radians((k + 1) * step)
        sgn = -1 if clockwise else 1
        t0 = (-math.sin(a0) * sgn, math.cos(a0) * sgn)
        t1 = (-math.sin(a1) * sgn, math.cos(a1) * sgn)
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        pts += [(p0[0] + KAPPA * r * t0[0], p0[1] + KAPPA * r * t0[1], "offcurve"),
                (p1[0] - KAPPA * r * t1[0], p1[1] - KAPPA * r * t1[1], "offcurve"),
                (p1[0], p1[1], "curve")]
    p = GSPath()
    for x, y, kind in pts:
        (sx, sy), = M.slant([(x, y)])
        p.nodes.append(GSNode((sx, sy), kind, smooth=kind == "curve"))
    p.closed = True
    return p


def comp(M, name, dx=0, dy=0, scale=1.0, align=-1):
    """A component moved along the slant, so a raised italic figure stays on its axis."""
    c = GSComponent(name)
    c.transform = (scale, 0, 0, scale, round(dx + dy * M.tan), round(dy))
    c.alignment = align
    return c


def new_layer(M, width, paths=(), comps=(), anchors=()):
    L = GSLayer()
    L.layerId = L.associatedMasterId = M.m.id
    L.width = round(width)
    for p in paths:
        L.paths.append(p)
    for c in comps:
        L.components.append(c)
    for a in anchors:
        L.anchors.append(a)
    return L


# --- builders: each returns a layer for one master ---------------------------

def nbspace(M):
    return new_layer(M, M.layer("space").width)


def brokenbar(M):
    x0, y0, x1, y1 = M.rect("bar")
    gap = max(80, 1.2 * (x1 - x0))
    mid = (y0 + y1) / 2
    return new_layer(M, M.layer("bar").width, paths=[
        line_path(M, rect(x0, y0, x1, mid - gap / 2)),
        line_path(M, rect(x0, mid + gap / 2, x1, y1))])


def logicalnot(M):
    x0, y0, x1, y1 = M.rect("minus")
    _, v = M.plus()
    stem = v[2] - v[0]
    leg = 130 + 0.4 * (y1 - y0)
    return new_layer(M, M.layer("minus").width, paths=[
        line_path(M, rect(x0, y0, x1, y1)),
        line_path(M, rect(x1 - stem, y0 - leg, x1, y1))])


def plusminus(M):
    h, v = M.plus()
    t, stem = h[3] - h[1], v[2] - v[0]
    cx = (v[0] + v[2]) / 2
    gap = 50 + 0.6 * t
    bottom = t + gap
    height = min(v[3] - v[1], M.m.capHeight - bottom)
    cy = bottom + height / 2
    return new_layer(M, M.layer("plus").width, paths=[
        line_path(M, rect(h[0], cy - t / 2, h[2], cy + t / 2)),
        line_path(M, rect(cx - stem / 2, bottom, cx + stem / 2, bottom + height)),
        line_path(M, rect(h[0], 0, h[2], t))])


def dagger(M, double=False):
    h, v = M.plus()
    t, stem = h[3] - h[1], v[2] - v[0]
    cx = (v[0] + v[2]) / 2
    half = 0.85 * (h[2] - h[0]) / 2
    paths = [line_path(M, rect(cx - stem / 2, -150, cx + stem / 2, FIG_TOP)),
             line_path(M, rect(cx - half, 470 - t / 2, cx + half, 470 + t / 2))]
    if double:
        paths.append(line_path(M, rect(cx - half, 70 - t / 2, cx + half, 70 + t / 2)))
    return new_layer(M, M.layer("plus").width, paths=paths)


def currency(M):
    h, v = M.plus()
    t = h[3] - h[1]
    cx, cy = (v[0] + v[2]) / 2, (h[1] + h[3]) / 2
    r = 150 + 0.6 * t
    spoke = 0.28 * r + 0.3 * t
    paths = [ring_path(M, cx, cy, r), ring_path(M, cx, cy, r - t, clockwise=True)]
    for deg in (45, 135, 225, 315):
        d = (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
        n = (-d[1] * t / 2, d[0] * t / 2)
        a = (cx + d[0] * (r - t / 2), cy + d[1] * (r - t / 2))
        b = (cx + d[0] * (r + spoke), cy + d[1] * (r + spoke))
        paths.append(line_path(M, [(a[0] - n[0], a[1] - n[1]), (b[0] - n[0], b[1] - n[1]),
                                   (b[0] + n[0], b[1] + n[1]), (a[0] + n[0], a[1] + n[1])]))
    return new_layer(M, M.layer("plus").width, paths=paths)


def mu(M):
    # u's left stem, carried down to the descender.
    tops = sorted(x for x, y in M.oncurves("u") if y == M.m.xHeight)
    x0, x1 = tops[0], tops[1]
    return new_layer(M, M.layer("u").width,
                     comps=[comp(M, "u")],
                     paths=[line_path(M, rect(x0, M.m.descender + 33, x1, 300))])


def florin(M):
    # f above the x-height, the tail of j below it, sharing f's stem.
    f_left = min(x for x, y in M.oncurves("f", 0) if y == 0)
    j_left = min(x for x, y in M.oncurves("jdotless") if y == M.m.xHeight)
    return new_layer(M, M.layer("f").width,
                     comps=[comp(M, "f"), comp(M, "jdotless", dx=f_left - j_left)])


def section(M):
    s = M.layer("s")
    top = FIG_TOP - 529
    return new_layer(M, s.width, comps=[comp(M, "s", dy=top), comp(M, "s", dy=-130)])


def superior(M, fig):
    w = M.layer(fig).width
    pad = 12
    return new_layer(M, w * SUP_SCALE + 2 * pad,
                     comps=[comp(M, fig, dx=pad, dy=FIG_TOP * (1 - SUP_SCALE), scale=SUP_SCALE)])


def ordinal(M, letter):
    w = M.layer(letter).width
    pad = 12
    return new_layer(M, w * SUP_SCALE + 2 * pad,
                     comps=[comp(M, letter, dx=pad, dy=FIG_TOP - 529 * SUP_SCALE, scale=SUP_SCALE)])


def fraction(M):
    # The slash, cut to figure height, with the sidebearings tucked in.
    src = M.layer("slash").paths[0]
    pts = [(M.up(n.position.x, n.position.y), n.position.y) for n in src.nodes]
    lo, hi = min(y for _, y in pts), max(y for _, y in pts)
    out = []
    for i, (x, y) in enumerate(pts):
        # Each end node's partner is the neighbour at the other end.
        for j in (i - 1, (i + 1) % len(pts)):
            if pts[j][1] != y:
                px, py = pts[j]
        ny = -12 if y == lo else FIG_TOP
        out.append((x + (px - x) * (ny - y) / (py - y), ny))
    xs = [x for x, _ in out]
    side = -60
    shift = side - min(xs)
    out = [(x + shift, y) for x, y in out]
    return new_layer(M, max(xs) - min(xs) + 2 * side, paths=[line_path(M, out)])


def vulgar(M, num, den):
    # Figures directly rather than the superiors, so no component is nested.
    pad = 12
    wn = M.layer(num).width * SUP_SCALE + 2 * pad
    wf = M.layer("fraction").width
    wd = M.layer(den).width * SUP_SCALE
    return new_layer(M, wn + wf + wd + 2 * pad, comps=[
        comp(M, num, dx=pad, dy=FIG_TOP * (1 - SUP_SCALE), scale=SUP_SCALE),
        comp(M, "fraction", dx=wn),
        comp(M, den, dx=wn + wf + pad, scale=SUP_SCALE)])


def commaaccent(M, base):
    b = M.layer(base)
    anchor = next(a for a in b.anchors if a.name == "bottom")
    mark = next(a for a in M.layer("commaaccentcomb").anchors if a.name == "_bottom")
    c = GSComponent("commaaccentcomb")
    c.transform = (1, 0, 0, 1, round(anchor.position.x - mark.position.x),
                   round(anchor.position.y - mark.position.y))
    return new_layer(M, b.width, comps=[comp(M, base, align=0), c])


def ensure_L_bottom_anchor(M):
    """L has no bottom anchor. Centre one on its foot, where N and G carry theirs."""
    L = M.layer("L")
    if any(a.name == "bottom" for a in L.anchors):
        return
    foot = [n.position.x for p in L.paths for n in p.nodes if n.type != "offcurve" and n.position.y == 0]
    anchors = list(L.anchors) + [GSAnchor("bottom", Point(round((min(foot) + max(foot)) / 2), 0))]
    # Glyphs keeps anchors sorted by name and would reorder them on open.
    L.anchors = sorted(anchors, key=lambda a: a.name)


# name, unicode, builder, kerning groups (left, right), review
GLYPHS = [
    ("nbspace", "00A0", nbspace, (None, None), False),
    ("brokenbar", "00A6", brokenbar, (None, None), False),
    ("logicalnot", "00AC", logicalnot, (None, None), False),
    ("plusminus", "00B1", plusminus, (None, None), False),
    ("dagger", "2020", dagger, (None, None), False),
    ("daggerdbl", "2021", lambda M: dagger(M, double=True), (None, None), False),
    ("currency", "00A4", currency, (None, None), True),
    ("mu", "00B5", mu, ("u", "u"), True),
    ("florin", "0192", florin, (None, "f"), True),
    ("section", "00A7", section, (None, None), True),
    ("onesuperior", "00B9", lambda M: superior(M, "one"), (None, None), True),
    ("twosuperior", "00B2", lambda M: superior(M, "two"), (None, None), True),
    ("threesuperior", "00B3", lambda M: superior(M, "three"), (None, None), True),
    ("ordfeminine", "00AA", lambda M: ordinal(M, "a"), (None, None), True),
    ("ordmasculine", "00BA", lambda M: ordinal(M, "o"), (None, None), True),
    ("fraction", "2044", fraction, (None, None), True),
    ("onequarter", "00BC", lambda M: vulgar(M, "one", "four"), (None, None), True),
    ("onehalf", "00BD", lambda M: vulgar(M, "one", "two"), (None, None), True),
    ("threequarters", "00BE", lambda M: vulgar(M, "three", "four"), (None, None), True),
    ("Lcommaaccent", "013B", lambda M: commaaccent(M, "L"), ("L", "L"), False),
    ("lcommaaccent", "013C", lambda M: commaaccent(M, "l"), ("l", "l"), False),
    ("Scommaaccent", "0218", lambda M: commaaccent(M, "S"), ("S", "S"), False),
    ("scommaaccent", "0219", lambda M: commaaccent(M, "s"), ("s", "s"), False),
    ("Tcommaaccent", "021A", lambda M: commaaccent(M, "T"), ("T", "T"), False),
    ("tcommaaccent", "021B", lambda M: commaaccent(M, "t"), ("t", "t"), False),
]


def build(path):
    font = glyphsLib.GSFont(path)
    masters = [Master(font, m) for m in font.masters]
    for M in masters:
        ensure_L_bottom_anchor(M)
    made = []
    for name, uni, builder, (lkg, rkg), review in GLYPHS:
        g = font.glyphs[name]
        if g is None:
            g = GSGlyph(name)
            font.glyphs.append(g)
        g.unicode = uni
        g.leftKerningGroup, g.rightKerningGroup = lkg, rkg
        if review:
            g.color = REVIEW
        # Build all masters before attaching, so a builder never reads a half-made glyph.
        layers = [builder(M) for M in masters]
        for L in list(g.layers):
            del g.layers[L.layerId]
        for M, L in zip(masters, layers):
            g.layers[M.m.id] = L
        made.append(name)
    font.save(path)
    print(f"{path}: {len(made)} glyphs")


for p in sys.argv[1:]:
    build(p)
