"""Render the README specimen as SVG, in a light and a dark ink palette.

HarfBuzz shapes the text, so the OpenType features shown are the font's own
rather than a mock-up, and every outline is written out as a path, so the image
carries no webfont and renders identically wherever SVG does.
"""
import os
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb

ROMAN = "fonts/variable/Metropolis[wght].ttf"
ITALIC = "fonts/variable/Metropolis-Italic[wght].ttf"
OUT = "documentation"

WEIGHTS = [
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
    (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
    (900, "Black"),
]

CITIES = [
    "Kraków · Reykjavík · İzmir · Malmö",
    "Łódź · Zürich · Timişoara · Kaunas",
]

# Each palette paints its own background. A transparent one would look better on
# GitHub's themes, but `prefers-color-scheme` follows the operating system rather
# than the GitHub appearance setting, so a reader whose two settings disagree is
# served the wrong variant -- and transparent means white ink on a white page.
# An opaque card makes that mismatch merely wrong-looking instead of invisible.
PALETTES = {
    "light": dict(ink="#1f2328", muted="#59636e", rule="#d1d9e0",
                  bg="#ffffff", edge="#d1d9e0"),
    "dark": dict(ink="#e6edf3", muted="#8b949e", rule="#30363d",
                 bg="#0d1117", edge="#30363d"),
}

WIDTH = 1640
MARGIN = 64
GUTTER = 80
LEFT_COL = 560
RIGHT_COL = WIDTH - 2 * MARGIN - GUTTER - LEFT_COL

LABEL = 18          # the grey labels
HEADING = 17        # the letterspaced section headings
SAMPLE = 66         # the weight ladder and the italics
FEATURE = 44        # the tnum and ss01 comparisons
CITY = 34           # the language sample

LADDER_STEP = 74
HEADING_TRACK = 90  # letterspacing, in font units per glyph
HEADING_GAP = 14    # clear space between a rule and the ink below it


class Renderer:
    """Shapes runs of text and collects their outlines as SVG paths."""

    def __init__(self):
        self.fonts = {}
        for style, path in (("roman", ROMAN), ("italic", ITALIC)):
            with open(path, "rb") as f:
                face = hb.Face(f.read())
            self.fonts[style] = (face, hb.Font(face))
        self.upem = self.fonts["roman"][0].upem
        self.paths = []

    def _shape(self, text, style, weight, features):
        face, font = self.fonts[style]
        font.set_variations({"wght": weight})
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features)
        return font, buf

    def width(self, text, size, style="roman", weight=400, features=None, tracking=0):
        _, buf = self._shape(text, style, weight, features)
        advance = sum(p.x_advance + tracking for p in buf.glyph_positions)
        return advance * size / self.upem

    def draw(self, text, x, y, size, color, style="roman", weight=400,
             features=None, tracking=0):
        """Set `text` with its baseline starting at (x, y)."""
        font, buf = self._shape(text, style, weight, features)
        scale = size / self.upem
        pen_x = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            svg = SVGPathPen(None, ntos=lambda v: f"{v:.1f}")
            font.draw_glyph_with_pen(
                info.codepoint,
                TransformPen(
                    svg,
                    (
                        scale, 0, 0, -scale,
                        x + (pen_x + pos.x_offset) * scale,
                        y - pos.y_offset * scale,
                    ),
                ),
            )
            d = svg.getCommands()
            if d:
                self.paths.append(f'<path fill="{color}" d="{d}"/>')
            pen_x += pos.x_advance + tracking

    def ramp(self, text, x, y, size, color, low, high):
        """Set `text` with the weight stepping from `low` to `high` across it.

        Each glyph is shaped at its own weight, so the run carries no kerning.
        """
        letters = [c for c in text if not c.isspace()]
        steps = max(len(letters) - 1, 1)
        i = 0
        for char in text:
            weight = low + (high - low) * i / steps
            self.draw(char, x, y, size, color, weight=weight)
            x += self.width(char, size, weight=weight)
            if not char.isspace():
                i += 1

    def ink_top(self, text, size, style="roman", weight=400, features=None,
                tracking=0):
        """How far the run's ink rises above its baseline, in user units."""
        font, buf = self._shape(text, style, weight, features)
        top = 0
        for info in buf.glyph_infos:
            bounds = BoundsPen(None)
            font.draw_glyph_with_pen(info.codepoint, bounds)
            if bounds.bounds:
                top = max(top, bounds.bounds[3])
        return top * size / self.upem

    def baseline_after(self, rule_y, text, size, **kw):
        """First baseline under a rule that clears the row's ascenders.

        A fixed drop does not: at size 66 the ink rises 46 units at wght 100 and
        51 at wght 900, so a constant tuned for one weight collides at another.
        """
        return rule_y + HEADING_GAP + self.ink_top(text, size, **kw)

    def right(self, text, x_end, y, size, color, **kw):
        self.draw(text, x_end - self.width(text, size, **kw), y, size, color, **kw)

    def rule(self, x, y, length, color):
        self.paths.append(
            f'<path stroke="{color}" stroke-width="1" '
            f'd="M{x:.1f} {y + 0.5:.1f}h{length:.1f}"/>'
        )

    def heading(self, text, x, y, width, palette, trailing=None):
        """A letterspaced section heading over a hairline rule. Returns the rule's y."""
        self.draw(text, x, y, HEADING, palette["muted"], weight=600,
                  tracking=HEADING_TRACK)
        if trailing:
            self.right(trailing, x + width, y, LABEL, palette["muted"])
        rule_y = y + 17
        self.rule(x, rule_y, width, palette["rule"])
        return rule_y


def build(palette):
    r = Renderer()
    ink, muted = palette["ink"], palette["muted"]
    top = MARGIN + HEADING
    left = MARGIN
    right = MARGIN + LEFT_COL + GUTTER

    # Left column: one line of the family name per named instance, which is the
    # only view that shows the whole axis at once.
    rule = r.heading("WEIGHT AXIS", left, top, LEFT_COL, palette,
                     trailing="wght 100 – 900")
    y = r.baseline_after(rule, "Metropolis", SAMPLE, weight=WEIGHTS[0][0])
    for weight, name in WEIGHTS:
        r.right(str(weight), left + 40, y, LABEL, muted)
        r.draw("Metropolis", left + 60, y, SAMPLE, ink, weight=weight)
        r.right(name, left + LEFT_COL, y, LABEL, muted)
        y += LADDER_STEP

    rule = r.heading("CONTINUOUS", left, y + 20, LEFT_COL, palette,
                     trailing="every value between")
    # The ramp ends at wght 900, which is the tallest ink in the run.
    y = r.baseline_after(rule, "Metropolis", SAMPLE, weight=900)
    r.ramp("Metropolis", left, y, SAMPLE, ink, 100, 900)
    left_bottom = y + SAMPLE * 0.25

    # Right column: the italics, then the three things this build added.
    rule = r.heading("MATCHING ITALICS", right, top, RIGHT_COL, palette)
    y = r.baseline_after(rule, "Metropolis", SAMPLE, style="italic", weight=300)
    for weight in (300, 700):
        r.right(str(weight), right + 40, y, LABEL, muted)
        r.draw("Metropolis", right + 60, y, SAMPLE, ink, style="italic", weight=weight)
        y += LADDER_STEP

    rule = r.heading("TABULAR FIGURES", right, y + 26, RIGHT_COL, palette)
    y = r.baseline_after(rule, "0000 1111 0123456789", FEATURE)
    for label, features in (("default", None), ("tnum", {"tnum": True})):
        r.right(label, right + 62, y, LABEL, muted)
        r.draw("0000 1111 0123456789", right + 84, y, FEATURE, ink, features=features)
        y += 60

    rule = r.heading("SINGLE-STOREY A", right, y + 26, RIGHT_COL, palette)
    y = r.baseline_after(rule, "aaa abcdefg", FEATURE)
    for label, features in (("default", None), ("ss01", {"ss01": True})):
        r.right(label, right + 62, y, LABEL, muted)
        r.draw("aaa abcdefg", right + 84, y, FEATURE, ink, features=features)
        y += 60

    rule = r.heading("LATIN, 263 LANGUAGES", right, y + 26, RIGHT_COL, palette)
    y = r.baseline_after(rule, CITIES[0], CITY, weight=350)
    for line in CITIES:
        r.draw(line, right, y, CITY, ink, weight=350)
        y += 48
    right_bottom = y - 48 + CITY * 0.25

    height = round(max(left_bottom, right_bottom) + MARGIN)
    card = (
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" '
        f'fill="{palette["bg"]}" stroke="{palette["edge"]}"/>'
    )
    body = "\n".join([card] + r.paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Metropolis specimen: the nine weights of the variable font, '
        f'matching italics, tabular figures, a single-storey a, and Latin accents.">'
        f'\n{body}\n</svg>\n'
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, palette in PALETTES.items():
        path = os.path.join(OUT, f"specimen-{name}.svg")
        with open(path, "w") as f:
            f.write(build(palette))
        print(f"  {path}  {os.path.getsize(path) / 1024:.0f}K")


if __name__ == "__main__":
    main()
