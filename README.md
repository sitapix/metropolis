# Metropolis

[![build](https://github.com/sitapix/metropolis/actions/workflows/build.yml/badge.svg)](https://github.com/sitapix/metropolis/actions/workflows/build.yml)

Metropolis is a geometric sans-serif by [Chris Simpson](https://github.com/chrismsimpson),
with nine weights from Thin to Black and matching italics. Use the static fonts
or choose any weight from 100 to 900 with the variable fonts. The family covers
Latin and includes tabular figures and a single-storey `a` alternate.

![Metropolis in white over a city photograph with sunlit skyscrapers.](./documentation/specimen.svg)

**[Download the fonts](https://github.com/sitapix/metropolis/releases/latest)** ·
**[Try the specimen](https://sitapix.github.io/metropolis/)**

Chris released Metropolis into the public domain. This fork preserves his r11
outlines and fixes the variable build, font metadata and character coverage.

## Installation

Download the release ZIP or use the files in [`fonts/`](./fonts/):

| Format | Location | Use |
|---|---|---|
| OTF | `fonts/otf/` | macOS and design apps |
| TTF | `fonts/ttf/` | Windows; hinted static fonts |
| Variable TTF | `fonts/variable/` | Apps with variable font support |
| WOFF2 | `fonts/webfonts/` | Websites; static and variable fonts |

For desktop use, open the OTF or TTF files and choose Install. For web use,
copy the WOFF2 files next to your CSS. The roman variable WOFF2 is 55 KB;
the italic is 60 KB.

## Features

Choose Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold, ExtraBold or
Black, each with an italic. In the variable fonts, set `wght` to any value
between 100 and 900.

| Feature | How to use it |
|---|---|
| Tabular figures and math symbols (`tnum`) | `font-variant-numeric: tabular-nums` |
| Single-storey `a` (`ss01`) | `font-feature-settings: "ss01"` |
| Stylistic alternates (`salt`, `aalt`) | Your app's typography controls |
| Kerning and accent positioning (`kern`, `mark`) | Enabled by default |

Latin coverage includes Western European accents, Latvian Ļ ļ and Romanian
Ș ș Ț ț. Inspect the glyphs and supported languages in the
[specimen](https://sitapix.github.io/metropolis/).

## Web use

```css
@font-face {
  font-family: "Metropolis";
  src: url("Metropolis[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
}

@font-face {
  font-family: "Metropolis";
  src: url("Metropolis-Italic[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: italic;
}

body { font-family: "Metropolis", sans-serif; }
```

For a static font, substitute a file such as `Metropolis-Regular.woff2` and
set `font-weight: 400`.

## Build

Install [uv](https://docs.astral.sh/uv/) and Python 3.12, then run:

```sh
make venv     # Install the pinned toolchain
make          # Build OTF, TTF, variable TTF and WOFF2
make check    # Check the built fonts
```

Edit the roman and italic Glyphs files in [`sources/`](./sources/).
Read the [development notes](./documentation/development.md) for individual
build targets, specimen generation and release packaging.

## Changelog

| Release | Date | Changes |
|---|---|---|
| [2.0.0](https://github.com/sitapix/metropolis/releases/tag/v2.0.0) | 2026-09-25 | Added characters and hinting; fixed italic naming, embedding and accent spacing. |
| [1.0.0](https://github.com/sitapix/metropolis/releases/tag/v1.0.0) | 2026-08-28 | First fork release: variable fonts, metric fixes, tabular figures and stylistic alternates. |

<a id="changes-from-upstream-r11"></a>

See the [changes from upstream r11](./documentation/changes-from-r11.md)
for the technical details.

## Contributing

Report problems through [issues](https://github.com/sitapix/metropolis/issues)
or open a pull request. For font changes, run `make && make check` and commit
the rebuilt fonts. See the [development notes](./documentation/development.md)
for image generation and CI checks.

## Credits

[Chris Simpson](https://github.com/chrismsimpson) designed Metropolis.
[Steven](https://github.com/sitapix) maintains this fork. The added characters
use Chris's glyphs as their starting point.

[Mark Boulton](https://github.com/markboulton) made
[Specimen Builder](https://github.com/markboulton/specimen-builder), which we
use for the interactive specimen.

## License

The fonts use the [Unlicense](./UNLICENSE). You can use, modify and distribute
them for any purpose, with or without attribution. Specimen Builder uses the
[Apache License 2.0](./specimen/LICENSE.txt).
