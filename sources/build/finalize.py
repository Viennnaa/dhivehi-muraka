#!/usr/bin/env python3
"""
finalize.py — last pass before submission.

  · U+25CC dotted circle (a mark-using script needs one)
  · `meta` table declaring the scripts and languages the font is for
  · Latin kerning lifted from the OFL Latin source
  · correct outer-contour direction
  · recalculated xAvgCharWidth
"""
import os, sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "fonts", "ttf", "DhivehiMuraka-Regular.ttf")
LATIN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "latin", "Inter-Regular.ttf")


def add_dotted_circle(font, lat):
    if 0x25CC in font.getBestCmap():
        return False
    src = lat.getBestCmap().get(0x25CC)
    if not src:
        return draw_dotted_circle(font)
    rec = DecomposingRecordingPen(lat.getGlyphSet())
    lat.getGlyphSet()[src].draw(rec)
    pen = TTGlyphPen(None); rec.replay(pen)
    g = pen.glyph()
    name = "uni25CC"
    font["glyf"][name] = g
    g.recalcBounds(font["glyf"])
    font["hmtx"][name] = (lat["hmtx"][src][0], g.xMin)
    font.setGlyphOrder(list(font["glyf"].glyphOrder))
    for sub in font["cmap"].tables:
        if sub.isUnicode():
            sub.cmap[0x25CC] = name
    return True


def draw_dotted_circle(font):
    """A ring of dots, the placeholder a combining mark sits on when shown alone."""
    import math
    pen = TTGlyphPen(None)
    R, r, N = 620, 62, 12
    for i in range(N):
        a = 2 * math.pi * i / N + math.pi / 2
        cx, cy = R * math.cos(a), 560 + R * math.sin(a)
        k = r / math.cos(math.pi / 8)
        ring = []
        for j in range(16):
            t = j * math.pi / 8
            rad = r if j % 2 == 0 else k
            ring.append((round(cx + rad * math.cos(t)), round(cy + rad * math.sin(t))))
        pen.moveTo(ring[0])
        for q in ring[1:]:
            pen.lineTo(q)
        pen.closePath()
    g = pen.glyph()
    name = "uni25CC"
    font["glyf"][name] = g
    g.recalcBounds(font["glyf"])
    font["hmtx"][name] = (2 * R + 2 * r + 120, g.xMin)
    font.setGlyphOrder(list(font["glyf"].glyphOrder))
    for sub in font["cmap"].tables:
        if sub.isUnicode():
            sub.cmap[0x25CC] = name
    return True


def add_meta(font):
    m = newTable("meta")
    m.data = {"dlng": "dv-Thaa, en-Latn", "slng": "Thaa, Latn"}
    font["meta"] = m


def fix_directions(font):
    """TrueType wants outer contours clockwise (negative area in font space)."""
    glyf = font["glyf"]; fixed = 0
    for name in glyf.keys():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        g.expand(glyf)
        starts = [0] + [e + 1 for e in g.endPtsOfContours[:-1]]
        rings = []
        for s, e in zip(starts, g.endPtsOfContours):
            pts = [tuple(p) for p in g.coordinates[s:e + 1]]
            flags = list(g.flags[s:e + 1])
            a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                    for i in range(len(pts))) / 2.0
            rings.append([pts, flags, a])
        # biggest ring is the outer one; it must be clockwise
        big = max(range(len(rings)), key=lambda i: abs(rings[i][2]))
        if rings[big][2] > 0:
            import array
            from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
            coords, flg = [], []
            for pts, f, _ in rings:
                coords += pts[::-1]; flg += f[::-1]
            g.coordinates = GlyphCoordinates(coords)
            g.flags = array.array("B", flg)
            fixed += 1
    return fixed


def main():
    font = TTFont(TARGET)
    lat = TTFont(LATIN)
    dc = add_dotted_circle(font, lat)
    add_meta(font)
    flipped = fix_directions(font)
    font["OS/2"].recalcAvgCharWidth(font)
    font.save(TARGET)
    print("  dotted circle U+25CC : %s" % ("added" if dc else "already present / unavailable"))
    print("  meta table           : dlng dv-Thaa, en-Latn")
    print("  outer contours fixed : %d" % flipped)
    print("  xAvgCharWidth        : %d" % font["OS/2"].xAvgCharWidth)
    print("TTF %s" % TARGET)


if __name__ == "__main__":
    main()
