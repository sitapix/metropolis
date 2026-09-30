# Development

Use [uv](https://docs.astral.sh/uv/) and Python 3.12 for the font build.
Install [Bun](https://bun.sh) to work on the interactive specimen.
The pinned dependencies are in [`requirements.txt`](../requirements.txt).

## Repository layout

| Path | Contents |
|---|---|
| `sources/` | Roman and italic Glyphs sources |
| `fonts/otf/` | 18 static OTFs |
| `fonts/ttf/` | 18 static TTFs |
| `fonts/variable/` | Roman and italic variable TTFs, `wght` 100-900 |
| `fonts/webfonts/` | 20 WOFF2s, including both variable fonts |
| `scripts/` | Build, postprocessing and validation scripts |
| `specimen/` | Interactive specimen site |
| `documentation/` | Specimen artwork and technical notes |

Each source has Thin, Regular and Black masters and nine named instances.
The sources contain 373 glyphs: 361 export and 333 have Unicode values.
The UPM is 1000. The roman masters contain 7381, 7523 and 6934 kerning pairs.

## Build targets

```sh
make venv                 # Install the toolchain
make                      # Build all font formats
make check                # Validate the outputs
make specimen-image       # Generate the outlined SVG artwork
make specimen             # Build the specimen site
make dist VERSION=2.0.0   # Package a release
```

Use `make static`, `make ttf`, `make variable` or `make webfonts` to build one
format. `make clean` removes the built fonts, site, distribution archives and
fontmake intermediates.

For static fonts, `postprocess_static.py` removes unreachable bracket
alternates. The build hints OTFs with `otfautohint` and restores CFF subroutines
with `cffsubr`; fontmake hints TTFs with ttfautohint. For variable fonts,
`postprocess_vf.py` adds STAT values, instance names, `gasp` and smart dropout
control. `make_webfonts.py` compresses the TTFs to WOFF2.

The release packer sorts entries, fixes permissions and takes timestamps from
`SOURCE_DATE_EPOCH` or the current commit. Use the same tag to reproduce an
archive.

`extend_charset.py` and `add_tabular_figures.py` edit the sources. They are
outside the build. Run them in that order after changing the glyphs they use,
then commit the updated sources and rebuilt fonts.

## Specimen site

```sh
make specimen
cd specimen && bun run start
```

Open `localhost:8080` to work on the site. The build copies the variable WOFF2s
from `fonts/webfonts/` into `specimen/src/fonts/`.

The site workflow publishes to [GitHub Pages](https://sitapix.github.io/metropolis/)
after pushes to `main` that affect `specimen/` or `fonts/webfonts/`.
The [specimen README](../specimen/README.md) describes the changes to Specimen
Builder, including fontkit's handling of default variable font instance names.

## Artwork

`make specimen-image` generates the README cover at 760 × 506, the GitHub
card at 1280 × 640, and the detailed light and dark feature sheets. The renderer
shapes the font with HarfBuzz and writes the glyph outlines as paths.

The README uses `specimen.svg`, with outlined lettering over `cover-city.jpg`.
The SVG embeds the photograph and needs no external font or image files.

To export the GitHub upload, install librsvg and ImageMagick
(`brew install librsvg imagemagick` on macOS,
`apt install librsvg2-bin imagemagick` on Ubuntu), then run:

```sh
make social-preview
```

This exports `social-preview.jpg` at 2560 × 1280 for GitHub.
The README's lettering stays sharp at any scale; the photograph has a fixed resolution.

Upload `documentation/social-preview.jpg` in the repository's
**Settings → General → Social preview**. Committing the image does not set
GitHub's preview. Regenerate the JPEG after editing the cover or the fonts.

## Validation

`make check` checks font metrics, naming, embedding permissions, character
coverage, OpenType features, hinting and variable font metadata. See
[`check_fonts.py`](../scripts/check_fonts.py) for the assertions.

Before submitting font changes, run `make && make check` and commit the rebuilt
outputs. Run `make specimen-image` after editing the fonts or artwork renderer;
run `make social-preview` to update the upload image.

CI checks the committed fonts, regenerates the SVGs and rejects artwork drift.
It then rebuilds the fonts and uses `compare_fonts.py` to compare their tables
with the committed files. Add an assertion to `check_fonts.py` for a font fix
that needs a regression check.
