#!/bin/bash
# One command: drawings -> releasable font.
set -e
cd "$(dirname "$0")"
SRC="${1:-../sources/drawings.json}"
echo "== 1. outlines from your drawings =="
python3 build_font.py "$SRC"
echo "== 2. OFL Latin =="
python3 merge_latin.py .cache/latin-source.ttf DhivehiMuraka-Regular.ttf
echo "== 3. dotted circle, meta, contour direction =="
python3 finalize.py
echo "== 4. GDEF, mark anchors, kerning =="
python3 add_features.py
echo "== 5. specimen =="
python3 make_specimen.py
echo
echo "Done -> DhivehiMuraka-Regular.ttf"
