# Metropolis specimen

An interactive specimen for Metropolis. The hero word swells toward the pointer.
The playground has a weight slider with the nine named stops, an Animate
button, size, line height, letter spacing, alignment, the `ss01` and `tnum`
switches, four colour schemes, and a Copy link button that reopens the same
setting. Below it are the nine weights, live demos of the OpenType features and
the bracketed `$ ¢`, a filterable glyph grid with a metrics inspector, and a
searchable language list.

```sh
make specimen                 # from the repository root: build to specimen/_site
cd specimen && bun run start  # serve at localhost:8080 with live reload
```

`make specimen` copies the two variable WOFF2 files out of `fonts/webfonts/`
into `src/fonts/`, so they are not committed twice. `bun run start` needs them
to be there already, which `make specimen` arranges.

Published to [sitapix.github.io/metropolis](https://sitapix.github.io/metropolis/)
by `.github/workflows/pages.yml`, which deploys with `actions/deploy-pages` and
needs no secret. Upstream's `docs/github_pages_auto_deploy.md` described a
deploy-key flow instead; it is dropped, since following it would mean creating a
write-scoped SSH key for nothing.

## What this is

[Specimen Builder](https://github.com/markboulton/specimen-builder) by Mark
Boulton, vendored here and configured for Metropolis. It is built on
[Specimen Skeleton](https://github.com/googlefonts/specimen-skeleton), which
reads the font's `fvar` table and generates the `@font-face` rules, the named
instances, the axis ranges and the character set that the page is built from.

The build pipeline (Eleventy, webpack, the font-data generator) is upstream's.
The templates, CSS and JavaScript under `src/` were rewritten for Metropolis in
2026 and share no code with upstream's theme.

Vendoring rather than depending on it keeps the fixes below in the repository
and keeps the specimen buildable from a checkout alone. Upstream is Apache-2.0,
which `LICENSE.txt` preserves; the rest of this repository is public domain.

Dependencies are installed with [Bun](https://bun.sh). `bun.lock` was migrated
from the original `yarn.lock` and produces a byte-identical build, content
hashes included.

## Changes from upstream

**fvar instances named by name ID 2.** `bun run fontdata` died on the roman with
`TypeError: Cannot read properties of undefined (reading 'en')`. fontkit files
name records below ID 256 under a string key — ID 2 becomes `fontSubfamily` —
but resolves an `fvar` instance's name through the numeric key, so an instance
pointing at ID 2 or 17 resolves to `undefined` and `namedVariations` throws. The
[OpenType spec](https://learn.microsoft.com/en-us/typography/opentype/spec/fvar)
asks for exactly that pointer: "If an instance record is included for the
default instance … then the nameID value should be set to 2 or 17 or to a name
ID with the same value as name ID 2 or 17." Metropolis follows it, and so does
every variable font macOS ships. `_tools/generateFontData.js` resolves those two
IDs itself rather than the font working around the library.

**md4 hashing.** webpack 4 and file-loader name output files with md4, which
OpenSSL 3 does not provide, so every build on Node 17 or later died with
`ERR_OSSL_EVP_UNSUPPORTED`. `webpack.config.js` maps md4 to sha256 at the
`crypto.createHash` call. Doing it there rather than through
`NODE_OPTIONS=--openssl-legacy-provider` keeps the fix working on the older Node
versions that reject that flag.

**`fs.rmdirSync(path, { recursive: true })`.** Removed in Node 16; now
`fs.rmSync`.

**An unpinned git dependency.** `specimen-skeleton-support` was declared as
`…/specimen-skeleton-support.git#master`, so the build was reproducible only by
accident of the lockfile: upstream's `master` had moved on, and regenerating the
lock silently swapped the resolved commit — which changed the generated
`font-family` from `Metropolis-Regular` to `Metropolis Regular`. It is now
pinned to `33a0e910`, the commit the original lockfile had frozen, so the
manifest states the version rather than the lockfile alone carrying it.

Three smaller changes: `build` and `start` run `fontdata` first, since
nothing renders until the generated CSS exists and it is not committed;
`fontdata.json` keeps its hand-edited order and style labels across a
regenerate, because the generator used to overwrite them and derives "unknown"
from a filename like `Metropolis[wght].woff2`; and husky is gone, because
husky 3 installs its pre-commit hook into the enclosing repository, which from
here is the font repository.

## Editing the specimen

| file | contents |
|---|---|
| `src/_data/site.js` | title, description, designer, language list |
| `src/_data/content.js` | every string the page sets |
| `src/_data/fontdata.json` | font order and the style labels |
| `src/_includes/*.html` | one file per section of the page |
| `src/css/tokens.css` | colours, spacing, radii and easing, light and dark |
| `src/css/controls.css` | buttons, chips, sliders, switches, swatches |
| `src/css/sections.css` | layout for each section, top to bottom |
| `src/js/main.js` | every interaction, with no runtime dependencies |

Weight is always set through the `--wght` custom property, never
`font-weight`: `fonts.css` maps `--wght` onto `font-variation-settings`, so
setting it on an element restyles everything inside.

`src/_data/fonts/` and `src/css/fonts.css` are generated by `bun run fontdata` and
are not committed. `fontdata.json` is, because its order and its style labels
are hand-edited; the generator carries them across but does not carry `name`,
which `fonts.css` keys off.

The 270-language list in `site.js` came from
[hyperglot](https://github.com/rosettatype/hyperglot):

```sh
hyperglot 'fonts/variable/Metropolis[wght].ttf'
```
