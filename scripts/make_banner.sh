#!/bin/bash
# Render the specimen image. Must go through a browser: PIL and friends do not
# shape right-to-left text, so the fili detach and the letters come out reversed.
set -e
cd "$(dirname "$0")"
B="$HOME/.claude/skills/gstack/browse/dist/browse"
"$B" viewport 1600x900 --scale 2 >/dev/null
"$B" goto "file://$PWD/banner.html" >/dev/null
sleep 2
"$B" screenshot "$PWD/../documentation/specimen.png" --selector ".card" >/dev/null
echo "documentation/specimen.png rendered"
