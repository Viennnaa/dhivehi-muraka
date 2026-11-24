# Dhivehi Muraka

An original Thaana typeface for Dhivehi, covering the complete Unicode Thaana
block: 24 base consonants, naviyani, the 14 Arabic transliteration letters, and
all 11 fili. It also draws the Rufiyaa sign (U+20C2), new in Unicode 18.0.

![Dhivehi Muraka specimen](documentation/specimen.png)

**[Open the interactive specimen →](https://viennnaa.github.io/dhivehi-muraka/specimen-interactive.html)**
Type in it, drag the size, and combine any consonant with any fili.

## Provenance

Every Thaana outline in this font was drawn by hand, point by point. No existing
font was opened, imported, traced, or used as a source of coordinates.

An existing Thaana face was shown on screen as a proportion reference while
drawing — the way a printed specimen would be — but none of its outlines are
present here, and that reference layer is not distributed with this repository.
Letters drawn in the Muraka editor enter the source through
`scripts/import_drawings.py`, which compares each one against the reference and
refuses any letter sharing coordinates with it.

Latin glyphs come from [Inter](https://github.com/rsms/inter) under the OFL, and
are credited in the font's name table.

## Layout

    sources/DhivehiMuraka-Regular.ufo   the source: outlines, anchors, kerning
    sources/config.yaml                 gftools builder recipe
    scripts/                            build, editor import, specimen tools
    fonts/ttf/                          the built font
    documentation/                      specimen image
    docs/                               the browsable specimen, served by GitHub Pages
    googlefonts/dhivehimuraka/          Google Fonts submission directory

## Building

Needs Python 3.11 or newer.

    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    scripts/build.sh

`scripts/build.sh` runs `gftools builder sources/config.yaml` (fontmake,
overlaps removed with skia-pathops, unhinted with `gasp` and smart dropout
control), then copies the font into `docs/` and `googlefonts/` and refreshes the
specimen pages.

## Editing

The UFO opens in any UFO editor, such as Fontra or FontForge. The outlines are
quadratic (TrueType) curves, as they were drawn; keep them quadratic. The `mark`
feature, `kern` feature and GDEF classes are generated at build time from the
glyph anchors, the kerning and `public.openTypeCategories`.

To draw in the Muraka editor instead, export JSON from it and import the
letters:

    python3 scripts/import_drawings.py ~/Downloads/dhivehi_muraka_edits.json [uni0780 ...]

## Technical

2048 upm · fsType 0 · OS/2 v4 · USE_TYPO_METRICS · italic angle 0
GDEF glyph classes · GPOS `mark` (fili on every letter and the dotted circle) and `kern` (Latin)
253 glyphs · 50 Thaana · Rufiyaa sign · 200 Latin · 5,020 kern pairs
FontBakery 1.1 `check-googlefonts` on the font: 0 FAIL, 153 PASS

## Licence

SIL Open Font License 1.1. See [OFL.txt](OFL.txt).

Designed by Ashrag Rasheed.
