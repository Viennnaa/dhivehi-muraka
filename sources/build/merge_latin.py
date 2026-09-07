#!/usr/bin/env python3
"""
merge_latin.py — add an OFL Latin to the Thaana font.

The Latin is NOT drawn here; it comes from an OFL-licensed face and is credited
as such. Default is Inter, which is 2048 upm like this font, so glyphs transfer
with no rescaling.

    python3 merge_latin.py [latin.ttf] [target.ttf]
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Scale

HERE = os.path.dirname(os.path.abspath(__file__))
LATIN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "..", "..", "..", "latin", "Inter-400.ttf")
TARGET = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "..", "fonts", "ttf", "DhivehiMuraka-Regular.ttf")

# GF Latin Core: what Google Fonts expects a font to cover for Latin.
CODEPOINTS = (
    list(range(0x0020, 0x007F)) +                       # basic ASCII
    [0x00A0, 0x00A2, 0x00A3, 0x00A5, 0x00A9, 0x00AB, 0x00AE, 0x00BB,
     0x00B0, 0x00B1, 0x00B7, 0x00D7, 0x00F7, 0x00A7, 0x00BF, 0x00A1] +
    list(range(0x00C0, 0x00FF)) +                       # Latin-1 accented
    [0x0152, 0x0153, 0x0160, 0x0161, 0x0178, 0x017D, 0x017E, 0x0192] +
    [0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E,
     0x2020, 0x2021, 0x2022, 0x2026, 0x2030, 0x2039, 0x203A, 0x20AC,
     0x2122, 0x2212, 0xFB01, 0xFB02]
)


def main():
    lat = TTFont(LATIN)
    dst = TTFont(TARGET)
    lcmap, dcmap = lat.getBestCmap(), dst.getBestCmap()
    lgs = lat.getGlyphSet()
    scale = dst["head"].unitsPerEm / float(lat["head"].unitsPerEm)

    glyf, hmtx = dst["glyf"], dst["hmtx"]
    added, skipped = [], []

    for cp in CODEPOINTS:
        if cp in dcmap:                       # never overwrite our own glyphs
            skipped.append(cp); continue
        src = lcmap.get(cp)
        if not src:
            skipped.append(cp); continue
        name = "lat_%04X" % cp
        rec = DecomposingRecordingPen(lgs)
        lgs[src].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, Scale(scale, scale)) if scale != 1 else pen)
        g = pen.glyph()
        glyf[name] = g
        if g.numberOfContours > 0:
            g.recalcBounds(glyf)
        adv = int(round(lat["hmtx"][src][0] * scale))
        hmtx[name] = (adv, g.xMin if g.numberOfContours > 0 else 0)
        added.append((cp, name))     # glyf[name] = g already extends the order

    order = list(glyf.glyphOrder)
    # every cased letter needs its counterpart, or GF fails case_mapping
    import unicodedata
    covered = set(dcmap) | {cp for cp, _ in added}
    extra = []
    for cp in list(covered):
        ch = chr(cp)
        for other in (ch.upper(), ch.lower()):
            if len(other) != 1:
                continue
            ocp = ord(other)
            if ocp > 0x24F:          # stay inside Latin; don't drag Greek in
                continue
            if ocp != cp and ocp not in covered and ocp in lcmap:
                src2 = lcmap[ocp]
                name2 = "lat_%04X" % ocp
                rec2 = DecomposingRecordingPen(lgs)
                lgs[src2].draw(rec2)
                pen2 = TTGlyphPen(None)
                rec2.replay(TransformPen(pen2, Scale(scale, scale)) if scale != 1 else pen2)
                g2 = pen2.glyph()
                glyf[name2] = g2
                if g2.numberOfContours > 0:
                    g2.recalcBounds(glyf)
                hmtx[name2] = (int(round(lat["hmtx"][src2][0] * scale)),
                               g2.xMin if g2.numberOfContours > 0 else 0)
                added.append((ocp, name2)); extra.append(ocp); covered.add(ocp)
    if extra:
        print("  +%d case counterparts" % len(extra))

    dst["maxp"].numGlyphs = len(order)
    for sub in dst["cmap"].tables:
        if sub.isUnicode():
            for cp, name in added:
                sub.cmap[cp] = name

    # credit the Latin source in the name table, as the OFL expects
    nm = dst["name"]
    lat_name = (TTFont(LATIN)["name"].getDebugName(1) or "an OFL font")
    note = ("Latin glyphs from %s, used under the SIL Open Font License 1.1. "
            "Thaana drawn by Ashrag Rasheed." % lat_name)
    for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
        nm.setName(note, 10, pid, eid, lid)

    # Latin glyphs are taller than the Thaana; win metrics must still cover the bbox
    dst["head"].recalcBounds = True
    hi = max((glyf[n].yMax for n in glyf.keys() if glyf[n].numberOfContours > 0), default=0)
    lo = min((glyf[n].yMin for n in glyf.keys() if glyf[n].numberOfContours > 0), default=0)
    os2 = dst["OS/2"]
    os2.usWinAscent = max(os2.usWinAscent, int(hi) + 10)
    os2.usWinDescent = max(os2.usWinDescent, abs(int(lo)) + 10)
    os2.sxHeight = 1080
    os2.sCapHeight = 1490          # Inter's cap height at 2048 upm
    print("  win metrics raised to %d / %d to cover the merged bbox"
          % (os2.usWinAscent, os2.usWinDescent))

    dst.save(TARGET)
    print("merged %d Latin glyphs from %s (scale %.4f)" % (len(added), os.path.basename(LATIN), scale))
    print("  now %d glyphs; %d codepoints already covered or unavailable" % (len(order), len(skipped)))
    print("  name ID 10 credits: %s" % lat_name)


if __name__ == "__main__":
    main()
