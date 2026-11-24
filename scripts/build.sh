#!/bin/bash
# Build Dhivehi Muraka from sources/DhivehiMuraka-Regular.ufo with gftools builder
# (fontmake), then refresh the copies the specimen site and the Google Fonts folder use.
#
#   python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
#   scripts/build.sh
set -e
cd "$(dirname "$0")/.."
TTF=fonts/ttf/DhivehiMuraka-Regular.ttf

gftools builder sources/config.yaml
cp "$TTF" googlefonts/dhivehimuraka/
cp "$TTF" docs/
python3 scripts/make_specimen.py "$TTF"

# the interactive specimen carries the font inline, so it works offline too
python3 - "$TTF" docs/specimen-interactive.html <<'EOF'
import base64, re, sys
from pathlib import Path
font, page = Path(sys.argv[1]), Path(sys.argv[2])
data = base64.b64encode(font.read_bytes()).decode()
html = page.read_text(encoding="utf-8")
html, n = re.subn(r"data:font/ttf;base64,[A-Za-z0-9+/=]+", lambda m: "data:font/ttf;base64," + data, html, count=1)
assert n == 1, "no inline font found in %s" % page
page.write_text(html, encoding="utf-8")
print("%s updated" % page)
EOF

echo "Done -> $TTF"
