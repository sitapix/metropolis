# Changes from upstream r11

**Vertical metrics.** Upstream declared `hhea` and `typo` as `795 / -205` with
`lineGap 0`, summing to 1000, which equals the UPM. macOS treats a font whose
ascent plus descent equals the em as having no line metrics and substitutes a
1.2 em line box. `NSFont.ascender - descender` returned 1.0 em while
`NSLayoutManager.defaultLineHeight` returned 1.2 em. This fork uses `1000 / -210 / 0`, summing to 1210. Measured at 100 pt, before and after: line fragment 121,
baseline 100 from the top.

**Windows clipping.** `usWinDescent` was 205. Family ink reaches -306 in Black
Italic, so Ģ Ķ Ņ Ŗ ģ ķ ņ ŗ clipped in the heavy weights. This fork uses `1000 / 310`.

**Variable build failed.** `cent` and `dollar` carry a bracket layer above
`wght 700` splitting the vertical bar into two stubs. Regular and Black had the
bracket, Thin did not, so `cent.BRACKET.varAlt01` had 3 contours at two masters
and 2 at the third. fontmake rejected it. The bars are 4-node parallelograms and
the stub gap closes with weight (Regular 13-504, Black 43-473), so
Thin's cut heights extrapolate off that slope. Italic bars slant 11.75°, so
moved nodes offset in x by `dy * tan`.

**Single-valued axes.** Both sources declared a `Width` axis with the masters
and instances at one value. The italic carried a third undeclared coordinate at
one value. `fvar` shipped `wdth 100..100..100`. This fork removes the unused coordinates; `wght` is the variable axis.

**STAT had no axis values.** fontmake emits the `wght` axis record and no
`AxisValue` entries, and no `ital` axis. The build adds both in `scripts/postprocess_vf.py`.
Roman and italic have incompatible masters and cannot share an `ital` axis in
`fvar`, so STAT links them instead:

```
Metropolis[wght].ttf          wght 100..900, ital 0, LinkedValue 1
Metropolis-Italic[wght].ttf   wght 100..900, ital 1
```

**Stems incomplete.** The font declares 8 stems. Black filled all 8, Regular 6,
Thin 2. Glyphs exported 2 of 18 instances and failed the rest with "Stems can't
be zero". All three masters now carry 4 horizontal and 4 vertical values.

**Substitution features.** Upstream had no substitution features. `kern` and `mark` came from the
kerning data and anchors, but the single-storey `a` was drawn and unreferenced,
and there were no tabular figures. `ss01`, `salt` and `aalt` now reach the
existing alternates. `tnum` re-centres each figure in the widest figure's
advance (`zero`: 674, 683, 736 by master), leaving outlines untouched; it
follows components, because `nine` is a rotated `six` with no paths of its own.

In the variable fonts, `cent` and `dollar` substitute via GSUB feature
variations at `wght 700..900`, which is where the `rvrn` feature comes from.

**Characters missing.** There was no U+00A0 no-break space, so `&nbsp;` fell back to another font's space. Windows-1252 lacked
¤ ¦ § ª ¬ ± ² ³ µ ¹ º ¼ ½ ¾ ƒ † ‡. U+00AD SOFT HYPHEN stays out on purpose: the
renderer draws a hyphen at the break itself. OS/2 claimed Baltic and the font had Ģ Ķ Ņ Ŗ,
but not Ļ ļ. Romanian had only the cedilla forms Ş ş Ţ ţ, although
`commaaccentcomb` was in the font. `scripts/extend_charset.py` builds all of
them from each master's own parts, so they interpolate: components where a
glyph already has the shape (µ is `u` with a descender stem, ƒ is `f` over the
tail of `j`, § is two `s`), and rectangles measured from `bar`, `plus` and
`minus` where none does. The superiors, fractions, ordinals, § ¤ ƒ µ and the
fraction slash use these constructions. Look for their magenta labels in
Glyphs to review them.

**Italic not linked to Regular.** The Regular Italic instance was style-linked
to "Regular", so its name1 was "Metropolis Regular" and Windows grouped
Regular, Bold and Bold Italic with no Italic. It is now the "Italic" of
"Metropolis", `Metropolis-Italic`, matching the variable font.

**Names and embedding.** name IDs 0, 9, 13 and 14 were empty, and `fsType` 8
restricted embedding in a public-domain font. The version stayed 11.000 with
upstream's unique ID, so font caches took this fork for upstream; it is now
12.000.

**Unhinted.** The TrueType fonts had no instructions and no `gasp`, and the CFF
had blue zones but no stem hints. The TrueType builds now also flatten nested
components and decompose scaled ones, which hint badly, and the name tables
drop the legacy Mac records.

**Spacing.** `eogonek`, `edotbelow`, `Edotbelow`, italic `Agrave`, Thin
`Ccedilla` and five more composites had advances up to 35 units off their base
letter, so the same word set wider with an accent. Each now takes its base's
advance. Strikeout was 20 units in every weight; it now matches the hyphen,
from 36 in Thin to 158 in Black. Underline was 20 too, and is now one thickness across the
family, 50 units, so mixed weights underline on one line.
