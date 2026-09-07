#!/usr/bin/env python3
"""
skeleton_to_ufo.py — turn editor.html's skeletons.json into a UFO source and a TTF.

Every outline here is generated from centre-lines drawn by hand in the editor,
expanded by a broad-nib model. Nothing is read from any existing font binary.

    python3 tools/skeleton_to_ufo.py [skeletons.json]

Looks in ~/Downloads/skeletons.json by default (where the browser puts it).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAMILY = "Dhivehi Font"
STYLE = "Regular"
PSNAME = "DhivehiFont-Regular"
SIMPLIFY_TOL = 1.2      # font units; raises/lowers point count
SAMPLES_PER_SEG = 26


# ---------- bezier / sampling (mirrors the JS in editor.html) ----------
def auto_handles(ns):
    H = []
    for i, c in enumerate(ns):
        p = ns[i - 1] if i > 0 else c
        n = ns[i + 1] if i < len(ns) - 1 else c
        dx, dy = (n["x"] - p["x"]) / 6.0, (n["y"] - p["y"]) / 6.0
        H.append({"ho": {"x": c["x"] + dx, "y": c["y"] + dy},
                  "hi": {"x": c["x"] - dx, "y": c["y"] - dy}})
    return H


def sample(stroke, per=SAMPLES_PER_SEG):
    ns = stroke["nodes"]
    if len(ns) < 2:
        return []
    A = auto_handles(ns)
    pts = []
    for i in range(len(ns) - 1):
        a, b = ns[i], ns[i + 1]
        c1 = a.get("ho") or A[i]["ho"]
        c2 = b.get("hi") or A[i + 1]["hi"]
        wa = a.get("w", 1.0)
        wb = b.get("w", 1.0)
        last = per if i == len(ns) - 2 else per - 1
        for k in range(last + 1):
            t = k / per
            u = 1 - t
            pts.append((
                u**3 * a["x"] + 3 * u * u * t * c1["x"] + 3 * u * t * t * c2["x"] + t**3 * b["x"],
                u**3 * a["y"] + 3 * u * u * t * c1["y"] + 3 * u * t * t * c2["y"] + t**3 * b["y"],
                wa + (wb - wa) * t))
    return pts


def nib_half(phi, nib, wmul=1.0):
    """Half-thickness perpendicular to travel. Broad-nib contrast with a hard floor,
    so a stroke running parallel to the nib thins but never vanishes."""
    floor = max(0.02, nib.get("m", 26) / 100.0)
    c = abs(math.sin(phi - math.radians(nib["a"])))
    return (nib["w"] / 2.0) * max(floor, c) * wmul


def cap(cx, cy, av, bv, out, steps=10):
    """Semicircular terminal: arc from av to bv around (cx,cy), bulging toward `out`."""
    ta, tb = math.atan2(av[1], av[0]), math.atan2(bv[1], bv[0])
    r = math.hypot(av[0], av[1])
    d = (tb - ta) % (2 * math.pi)
    for delta in (d, d - 2 * math.pi):
        mid = ta + delta / 2.0
        if math.cos(mid) * out[0] + math.sin(mid) * out[1] > 0:
            break
    return [(cx + r * math.cos(ta + delta * k / steps),
             cy + r * math.sin(ta + delta * k / steps)) for k in range(1, steps)]


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy)
    worst, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / n if n else math.hypot(px - x1, py - y1)
        if d > worst:
            worst, idx = d, i
    if worst > tol:
        return rdp(pts[:idx + 1], tol)[:-1] + rdp(pts[idx:], tol)
    return [pts[0], pts[-1]]


def area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def stroke_outline(stroke, nib):
    p = sample(stroke)
    if len(p) < 2:
        return None
    left, right = [], []
    for i, (x, y, wm) in enumerate(p):
        a = p[max(i - 1, 0)]
        b = p[min(i + 1, len(p) - 1)]
        phi = math.atan2(b[1] - a[1], b[0] - a[0])
        h = nib_half(phi, nib, wm)
        nx, ny = -math.sin(phi), math.cos(phi)
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))

    if stroke.get("caps", True):
        te = (p[-1][0] - p[-2][0], p[-1][1] - p[-2][1])
        ts = (p[0][0] - p[1][0], p[0][1] - p[1][1])
        end_cap = cap(p[-1][0], p[-1][1],
                      (left[-1][0] - p[-1][0], left[-1][1] - p[-1][1]),
                      (right[-1][0] - p[-1][0], right[-1][1] - p[-1][1]), te)
        start_cap = cap(p[0][0], p[0][1],
                        (right[0][0] - p[0][0], right[0][1] - p[0][1]),
                        (left[0][0] - p[0][0], left[0][1] - p[0][1]), ts)
    else:
        end_cap = start_cap = []

    ring = (rdp(left, SIMPLIFY_TOL) + end_cap
            + rdp(right, SIMPLIFY_TOL)[::-1] + start_cap)
    out = [ring[0]]
    for q in ring[1:]:
        if abs(q[0] - out[-1][0]) > .01 or abs(q[1] - out[-1][1]) > .01:
            out.append(q)
    if area(out) > 0:
        out.reverse()
    return [(round(x), round(y)) for x, y in out]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/skeletons.json")
    if not os.path.exists(src):
        sys.exit("Not found: %s\nExport from editor.html first (⇩ Export JSON)." % src)
    doc = json.load(open(src))
    nib = doc["nib"]
    upm, asc, desc = doc["upm"], doc["ascender"], doc["descender"]
    glyphs = doc["glyphs"]
    if not glyphs:
        sys.exit("skeletons.json has no drawn letters yet.")

    rings = {}
    for name, gl in glyphs.items():
        cs = [stroke_outline(s, nib) for s in gl["strokes"]]
        rings[name] = [c for c in cs if c]

    # ---- UFO ----
    try:
        import ufoLib2
        from fontTools.pens.pointPen import SegmentToPointPen
    except ImportError:
        sys.exit("pip3 install --user ufoLib2 fonttools")

    f = ufoLib2.Font()
    i = f.info
    i.familyName, i.styleName = FAMILY, STYLE
    i.unitsPerEm, i.ascender, i.descender = upm, asc, desc
    i.xHeight, i.capHeight = doc.get("bodyHeight", 500), doc.get("bodyHeight", 500)
    i.italicAngle = 0
    i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender = asc, desc
    i.openTypeOS2TypoLineGap = 100
    i.openTypeHheaAscender, i.openTypeHheaDescender, i.openTypeHheaLineGap = asc, desc, 100
    i.openTypeOS2WinAscent, i.openTypeOS2WinDescent = asc, abs(desc)
    i.openTypeOS2Type = []                     # fsType 0, installable
    i.postscriptFontName = PSNAME
    i.copyright = "Copyright %s the Dhivehi Font Project Authors." % doc.get("year", 2026)
    i.openTypeNameLicense = ("This Font Software is licensed under the SIL Open Font "
                             "License, Version 1.1.")
    i.openTypeNameLicenseURL = "https://openfontlicense.org"

    sp = f.newGlyph("space"); sp.width = 260; sp.unicodes = [0x20]
    for name, gl in glyphs.items():
        g = f.newGlyph(name)
        g.width = gl["width"]
        g.unicodes = [gl["unicode"]]
        pen = g.getPen()
        for ring in rings[name]:
            pen.moveTo(ring[0])
            for q in ring[1:]:
                pen.lineTo(q)
            pen.closePath()

    ufo_path = os.path.join(HERE, "sources", "%s.ufo" % PSNAME)
    f.save(ufo_path, overwrite=True)
    pts = sum(len(r) for rs in rings.values() for r in rs)
    print("UFO   %s  (%d glyphs, %d points)" % (ufo_path, len(glyphs), pts))

    # ---- TTF ----
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    order = [".notdef", "space"] + list(glyphs.keys())
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({0x20: "space", **{gl["unicode"]: n for n, gl in glyphs.items()}})

    tt = {}
    p = TTGlyphPen(None); tt[".notdef"] = p.glyph()
    p = TTGlyphPen(None); tt["space"] = p.glyph()
    for name in glyphs:
        p = TTGlyphPen(None)
        for ring in rings[name]:
            p.moveTo(ring[0])
            for q in ring[1:]:
                p.lineTo(q)
            p.closePath()
        tt[name] = p.glyph()
    fb.setupGlyf(tt)
    fb.setupHorizontalMetrics({n: (260 if n in (".notdef", "space") else glyphs[n]["width"], 0)
                               for n in order})
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=100)
    fb.setupNameTable({
        "familyName": FAMILY, "styleName": STYLE,
        "uniqueFontIdentifier": "%s;1.000" % PSNAME,
        "fullName": "%s %s" % (FAMILY, STYLE),
        "version": "Version 1.000", "psName": PSNAME,
        "licenseDescription": i.openTypeNameLicense,
        "licenseInfoURL": i.openTypeNameLicenseURL})
    fb.setupOS2(version=4, sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=100,
                usWinAscent=asc, usWinDescent=abs(desc), fsType=0,
                sxHeight=i.xHeight, sCapHeight=i.capHeight,
                fsSelection=0x40 | 0x80, achVendID="NONE")
    fb.setupPost(italicAngle=0)
    fb.font["head"].unitsPerEm = upm

    try:
        from fontTools.ttLib.removeOverlaps import removeOverlaps
        removeOverlaps(fb.font)
        print("      overlaps removed (skia-pathops)")
    except Exception as e:
        print("      NOTE overlaps NOT removed (%s) — pip3 install --user skia-pathops"
              % type(e).__name__)

    ttf = os.path.join(HERE, "build", "%s.ttf" % PSNAME)
    os.makedirs(os.path.dirname(ttf), exist_ok=True)
    fb.save(ttf)
    print("TTF   %s" % ttf)
    print("\nInstall it (macOS):  open %s" % ttf)


if __name__ == "__main__":
    main()
