#!/bin/bash
# Drawings -> releasable font. Run from anywhere.
set -e
# resolve the source before changing directory, so a relative path still works
SRC_IN="${1:-}"
if [ -n "$SRC_IN" ]; then SRC="$(cd "$(dirname "$SRC_IN")" && pwd)/$(basename "$SRC_IN")"; fi
cd "$(dirname "$0")"
SRC="${SRC:-$PWD/../drawings.json}"
echo "== 1. outlines from the drawings =="
python3 build_font.py "$SRC"
echo "== 2. OFL Latin =="
python3 merge_latin.py ../latin/Inter-Regular.ttf
echo "== 3. dotted circle, meta, contour direction =="
python3 finalize.py
echo "== 4. GDEF, mark anchors, kerning =="
python3 add_features.py
echo "== 5. specimen =="
python3 make_specimen.py
cp ../../fonts/ttf/DhivehiMuraka-Regular.ttf ../../googlefonts/dhivehimuraka/
cp ../../fonts/ttf/DhivehiMuraka-Regular.ttf ../../docs/
echo
echo "Done -> fonts/ttf/DhivehiMuraka-Regular.ttf"
