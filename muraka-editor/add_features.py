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
LATIN = os.path.join(HERE, ".cache", "latin-source.ttf")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "DhivehiMuraka-Regular.ttf")
DST = sys.argv[2] if len(sys.argv) > 2 else SRC

CONSONANTS = list(range(0x780, 0x798)) + [0x7B1]          # 24 base + naviyani
ARABIC     = list(range(0x798, 0x7A6))                    # transliteration letters
DOTTED     = [0x25CC]          # marks must attach to the dotted circle too
BASES      = CONSONANTS + ARABIC + DOTTED
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


def kern_pairs(font, lat):
    """Lift kern pairs for the Latin we merged, from the face we merged it from."""
    if "GPOS" not in lat:
        return 0
    rev = {}
    for cp, name in font.getBestCmap().items():
        if name.startswith("lat_"):
            rev[cp] = name
    lcmap = lat.getBestCmap()
    lat2ours = {lcmap[cp]: rev[cp] for cp in rev if cp in lcmap}

    pairs = {}
    def classdefs(cd):
        d = {}
        for g, c in (cd.classDefs.items() if cd else []):
            d.setdefault(c, []).append(g)
        return d

    for lk in lat["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            t = getattr(st, "LookupType", None) or lk.LookupType
            if getattr(st, "Format", None) == 2 and hasattr(st, "Class1Record"):
                c1, c2 = classdefs(st.ClassDef1), classdefs(st.ClassDef2)
                cov = set(st.Coverage.glyphs)
                c1.setdefault(0, [g for g in cov if g not in (st.ClassDef1.classDefs if st.ClassDef1 else {})])
                for i, r1 in enumerate(st.Class1Record):
                    for j, r2 in enumerate(r1.Class2Record):
                        v = getattr(r2.Value1, "XAdvance", 0) if r2.Value1 else 0
                        if not v:
                            continue
                        for a in c1.get(i, []):
                            for b in c2.get(j, []):
                                if a in lat2ours and b in lat2ours:
                                    pairs[(lat2ours[a], lat2ours[b])] = v
            elif hasattr(st, "PairSet"):
                for gi, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for pv in ps.PairValueRecord:
                        v = getattr(pv.Value1, "XAdvance", 0) if pv.Value1 else 0
                        if v and gi in lat2ours and pv.SecondGlyph in lat2ours:
                            pairs[(lat2ours[gi], lat2ours[pv.SecondGlyph])] = v
    return pairs



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

    pairs = {}
    if os.path.exists(LATIN):
        try:
            pairs = kern_pairs(font, TTFont(LATIN))
        except Exception as e:
            print("      kerning skipped (%s)" % type(e).__name__)
    if pairs:
        lines.append("")
        lines.append("feature kern {")
        lines.append("  script latn;")
        for (x, y), v in sorted(pairs.items()):
            lines.append("  pos %s %s %d;" % (x, y, v))
        lines.append("} kern;")
    fea = "\n".join(lines) + "\n"

    fea_path = os.path.join(HERE, "features.fea")
    open(fea_path, "w").write(fea)
    addOpenTypeFeatures(font, fea_path)

    font["OS/2"].recalcAvgCharWidth(font)
    font.save(DST)
    print("FEA   %s" % fea_path)
    print("      %d bases anchored, %d marks (%d above, %d below), all zero-width"
          % (len(bases), len(marks), len(above), len(below)))
    print("      %d Latin kern pairs" % len(pairs))
    print("      tables now: %s" % ", ".join(sorted(font.keys())))
    print("TTF   %s" % DST)


if __name__ == "__main__":
    main()
