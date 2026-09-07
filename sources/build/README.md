# Build

`drawings.json` in the parent directory is the source: every Thaana outline as
the points that were placed by hand. These scripts turn it into the font.

    ./build_all.sh ../drawings.json

| step | script | does |
|---|---|---|
| 1 | `build_font.py` | drawings → TTF outlines, metrics, provenance gate |
| 2 | `merge_latin.py` | merges the OFL Latin, credits it in name ID 10 |
| 3 | `finalize.py` | U+25CC dotted circle, `meta` table, contour direction |
| 4 | `add_features.py` | GDEF classes, GPOS mark anchors for the fili, kerning |
| 5 | `make_specimen.py` | rebuilds `docs/specimen.html` |

`make_banner.sh` regenerates `docs/specimen.png`. It renders through a browser
on purpose: PIL and similar libraries do not shape right-to-left text, so the
fili detach and the letters come out reversed.

The provenance gate in step 1 compares every letter against a reference face and
refuses any glyph sharing coordinates with it. The reference is not distributed;
point `MURAKA_REFERENCE` at a local copy to run that check.

Requires `pip install -r ../../requirements.txt`.
