#!/bin/bash
# One command: drawings -> releasable font.
set -e
cd "$(dirname "$0")"
SRC="${1:-$HOME/Downloads/dhivehi_muraka_edits (7).json}"
echo "== 1. outlines from your drawings =="
python3 build_font.py "$SRC"
echo "== 2. anchors, GDEF, mark feature =="
python3 add_features.py
echo "== 3. OFL Latin =="
python3 merge_latin.py .cache/latin-source.ttf DhivehiMuraka-Regular.ttf
echo "== 4. specimen =="
python3 make_specimen.py
echo
echo "Done -> DhivehiMuraka-Regular.ttf"
