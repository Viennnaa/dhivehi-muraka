# Dhivehi Muraka

An original Thaana typeface for Dhivehi, covering the complete Unicode Thaana
block: 24 base consonants, naviyani, the 14 Arabic transliteration letters, and
all 11 fili.

![specimen](documentation/specimen.png)

## Provenance

Every Thaana outline in this font was drawn by hand, point by point. No existing
font was opened, imported, traced, or used as a source of coordinates.

An existing Thaana face was shown on screen as a proportion reference while
drawing — the way a printed specimen would be — but none of its outlines are
present here, and that reference layer is not distributed with this repository.
The build verifies this on every run: each glyph is compared against the
reference and any letter sharing coordinates with it is refused, not shipped.

Latin glyphs come from [Inter](https://github.com/rsms/inter) under the OFL, and
are credited in the font's name table.

## Layout

    fonts/ttf/                  the built font
    sources/drawings.json       the drawings — the actual source
    sources/latin/              the OFL Latin that gets merged in
    muraka-editor/              the drawing tool, runs in a browser
    documentation/specimen.html specimen page
    googlefonts/dhivehifont/    Google Fonts submission directory

## Building

    cd muraka-editor
    ./build_all.sh ../sources/drawings.json

Four steps: outlines from the drawings, then anchors and the `mark` feature,
then the Latin merge, then the specimen.

| script | does |
|---|---|
| `build_font.py` | drawings → TTF outlines, metrics, provenance gate |
| `add_features.py` | zero-width fili, GDEF classes, GPOS mark-to-base anchors |
| `merge_latin.py` | merges an OFL Latin, credits it in name ID 10 |
| `make_specimen.py` | rebuilds the specimen page |

## Drawing

Open `muraka-editor/editor.html` in a browser. Letters start blank. Pen tool
places points, ⟳ Fix holes corrects contour direction, ⧉ Copy / ⇩ Paste moves a
shape between letters, • Add dot places a round dot. Export with ⬇ Export JSON
and rebuild.

The editor ships with an empty reference layer. To draw against your own
reference, put a `font_data.local.js` beside `font_data.js`; it is gitignored
and never distributed.

## Technical

2048 upm · fsType 0 · OS/2 v4 · USE_TYPO_METRICS · italic angle 0
GDEF glyph classes · GPOS `mark` feature under the `thaa` script
251 glyphs · 50 Thaana · 200 Latin

## Licence

SIL Open Font License 1.1. See [OFL.txt](OFL.txt).

Designed by Ashrag Rasheed.
