#!/usr/bin/env python3
"""
add_features.py — turn the drawn letters into a font that actually shapes Dhivehi.

Adds:
  · zero-width fili (combining marks must not advance the pen)
  · GDEF glyph classes (bases vs marks)
  · GPOS `mark` feature with per-letter anchors, so a fili centres itself on
    whatever consonant it follows instead of sitting where it was drawn

    python3 add_features.py [in.ttf] [out.ttf]
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeatures

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "DhivehiMuraka-Regular.ttf")
DST = sys.argv[2] if len(sys.argv) > 2 else SRC

CONSONANTS = list(range(0x780, 0x798)) + [0x7B1]          # 24 base + naviyani
ARABIC     = list(range(0x798, 0x7A6))                    # transliteration letters
BASES      = CONSONANTS + ARABIC
MARKS_ABOVE = [0x7A6, 0x7A7, 0x7AA, 0x7AB, 0x7AC, 0x7AD, 0x7AE, 0x7AF, 0x7B0]
MARKS_BELOW = [0x7A8, 0x7A9]

g = lambda cp: "uni%04X" % cp


def ink_centre(font, name):
    gl = font["glyf"][name]
    if gl.numberOfContours <= 0:
        return 0
    gl.expand(font["glyf"])
    xs = [p[0] for p in gl.coordinates]
    return int(round((min(xs) + max(xs)) / 2.0))


def main():
    font = TTFont(SRC)
    order = set(font.getGlyphOrder())
    bases = [g(c) for c in BASES if g(c) in order]
    above = [g(c) for c in MARKS_ABOVE if g(c) in order]
    below = [g(c) for c in MARKS_BELOW if g(c) in order]
    marks = above + below
    if not marks:
        sys.exit("No fili in this font yet — draw them first.")

    # 1. marks must not advance the pen
    hmtx = font["hmtx"]
    for m in marks:
        hmtx[m] = (0, font["glyf"][m].xMin if font["glyf"][m].numberOfContours > 0 else 0)

    # 2. anchors. Both sides use y=0, so a mark keeps the height you drew it at
    #    and only gets moved sideways onto the letter's centre.
    lines = []
    lines.append("@BASE = [%s];" % " ".join(bases))
    lines.append("@MARK = [%s];" % " ".join(marks))
    lines.append("")
    lines.append("table GDEF {")
    lines.append("  GlyphClassDef @BASE, , @MARK, ;")
    lines.append("} GDEF;")
    lines.append("")
    lines.append("feature mark {")
    lines.append("  script thaa;")
    for m in above:
        lines.append("  markClass %s <anchor %d 0> @TOP;" % (m, ink_centre(font, m)))
    for m in below:
        lines.append("  markClass %s <anchor %d 0> @BOT;" % (m, ink_centre(font, m)))
    lines.append("")
    for b in bases:
        c = ink_centre(font, b)
        lines.append("  pos base %s <anchor %d 0> mark @TOP <anchor %d 0> mark @BOT;" % (b, c, c))
    lines.append("} mark;")
    fea = "\n".join(lines) + "\n"

    fea_path = os.path.join(HERE, "features.fea")
    open(fea_path, "w").write(fea)
    addOpenTypeFeatures(font, fea_path)

    font.save(DST)
    print("FEA   %s" % fea_path)
    print("      %d bases anchored, %d marks (%d above, %d below), all zero-width"
          % (len(bases), len(marks), len(above), len(below)))
    print("      tables now: %s" % ", ".join(sorted(font.keys())))
    print("TTF   %s" % DST)


if __name__ == "__main__":
    main()
