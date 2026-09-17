#!/usr/bin/env python3
"""
build_font.py — turn editor.html's `dhivehi_muraka_edits.json` into a FRESH font.

This builder starts from an empty font. Nothing from Faruma or DhivehiMuraka is
opened, read, or carried over: only the contours you drew in the editor go in.

    ⬇ Export JSON  in the editor, then:
    python3 build_font.py [dhivehi_muraka_edits.json]

Defaults to ~/Downloads/dhivehi_muraka_edits.json (where the browser puts it).
"""
import array, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILY, STYLE, PSNAME = "Dhivehi Muraka", "Regular", "DhivehiMuraka-Regular"
VERSION = "1.001"        # name IDs 3 and 5 and head.fontRevision, kept in step
UPM, ASC, DESC, GAP = 2048, 1900, -600, 0     # sum 2500 >= 1.2 em, lineGap 0
VENDOR = "ASHR"          # TODO register at learn.microsoft.com/typography/vendors
YEAR, AUTHOR = 2026, "Ashrag Rasheed"
REPO = "https://github.com/Viennnaa/dhivehi-muraka"
COPYRIGHT = "Copyright %d The %s Project Authors (%s)" % (YEAR, FAMILY, REPO)
OFL_DESC = ("This Font Software is licensed under the SIL Open Font License, "
            "Version 1.1. This license is available with a FAQ at: "
            "https://openfontlicense.org")


REF_DATA = os.environ.get("MURAKA_REFERENCE", "")   # optional local reference; never distributed


def provenance_check(store):
    """Refuse to build any letter whose points came from Faruma / DhivehiMuraka."""
    if not os.path.exists(REF_DATA):
        return store, []
    import re
    txt = open(REF_DATA).read()
    ref = {e["id"]: e for e in json.loads(txt[txt.index("["):txt.rindex("]") + 1])}
    bad = []
    for gid in list(store):
        e = ref.get(gid)
        if not e:
            continue
        pts = set(tuple(p) for p in store[gid]["coords"])
        far = set(tuple(p) for p in e.get("faruma", {}).get("coords", []))
        mur = set(tuple(p) for p in e.get("muraka", {}).get("coords", []))
        hits = len(pts & far) + len(pts & mur)
        if hits:
            bad.append((gid, hits, len(pts)))
            del store[gid]
    return store, bad


def svgs_to_store(paths):
    """Read per-letter SVGs exported by the editor (y_svg = 1400 - y_font)."""
    import re
    store = {}
    for path in paths:
        txt = open(path).read()
        gid = re.search(r'data-glyph-name="(uni[0-9A-Fa-f]{4})"', txt)
        d = re.search(r'id="glyph-outline"[^>]*\sd="([^"]+)"', txt)
        if not gid or not d:
            print("  skipped (no glyph path): %s" % os.path.basename(path)); continue
        adv = re.findall(r'x1="(\d+)"[^>]*stroke="#f59e0b"', txt)
        coords, flags, ends = [], [], []
        for cmd, body in re.findall(r'([MLQZ])([^MLQZ]*)', d[1] if isinstance(d, tuple) else d.group(1)):
            v = [float(x) for x in re.findall(r'-?\d+\.?\d*', body)]
            pts = [(v[i], 1400 - v[i + 1]) for i in range(0, len(v) - 1, 2)]
            if cmd == "M":
                coords += pts; flags += [1] * len(pts)
            elif cmd == "L":
                coords += pts; flags += [1] * len(pts)
            elif cmd == "Q":                      # control, on-curve, control, on-curve...
                for k, p in enumerate(pts):
                    coords.append(p); flags.append(0 if k % 2 == 0 else 1)
            elif cmd == "Z":
                ends.append(len(coords) - 1)
        if not ends and coords:
            ends = [len(coords) - 1]
        # the editor repeats the start point before Z; drop the duplicate
        for e in range(len(ends)):
            st = 0 if e == 0 else ends[e - 1] + 1
            if ends[e] > st and coords[ends[e]] == coords[st]:
                coords.pop(ends[e]); flags.pop(ends[e])
                for j in range(e, len(ends)): ends[j] -= 1
        store[gid.group(1)] = {"coords": [list(p) for p in coords], "flags": flags,
                               "endPts": ends, "advance": int(adv[0]) if adv else 1110}
        print("  %s  %d points, %d contour(s)" % (gid.group(1), len(coords), len(ends)))
    return store



def main():
    args = sys.argv[1:] or [os.path.expanduser("~/Downloads/dhivehi_muraka_edits.json")]
    svgs = []
    for a in args:
        if os.path.isdir(a):
            svgs += [os.path.join(a, f) for f in sorted(os.listdir(a)) if f.endswith(".svg")]
        elif a.endswith(".svg"):
            svgs.append(a)
    jsons = [a for a in args if a.endswith(".json") and os.path.exists(a)]
    if svgs and jsons:
        print("merging %d JSON export(s) + %d SVG file(s)" % (len(jsons), len(svgs)))
    if svgs:
        # Several exports of the same letter pile up in Downloads as "(1)", "(2)".
        # Keep only the newest per glyph, and say which file won.
        import re as _re
        best = {}
        for f in svgs:
            m = _re.search(r'(uni[0-9A-Fa-f]{4})', os.path.basename(f))
            if not m:
                continue
            k = m.group(1)
            if k not in best or os.path.getmtime(f) > os.path.getmtime(best[k]):
                best[k] = f
        dropped = len(svgs) - len(best)
        svgs = [best[k] for k in sorted(best)]
        if dropped:
            print("%d older duplicate export(s) ignored; using newest per letter" % dropped)
        for f in svgs:
            print("  using %s" % os.path.basename(f))
        store = svgs_to_store(svgs)
        for j in jsons:                      # JSON wins where it has real outlines
            for gid, g in json.load(open(j)).items():
                if gid.startswith("uni") and (g.get("coords") or []):
                    store[gid] = g
    else:
        src = args[0]
        if not os.path.exists(src):
            sys.exit("Not found: %s\nExport from the editor first (⬇ Export JSON, or per-letter SVG)." % src)
        store = json.load(open(src))

    drawn = {}
    for gid, g in store.items():
        if not gid.startswith("uni"):
            continue
        coords, flags, ends = g.get("coords") or [], g.get("flags") or [], g.get("endPts") or []
        if len(coords) < 3 or not ends:
            continue
        # drop contours with fewer than 3 points; TrueType cannot draw them
        keep_c, keep_f, keep_e, start, out = [], [], [], 0, 0
        for e in ends:
            seg_c, seg_f = coords[start:e + 1], flags[start:e + 1]
            if len(seg_c) >= 3:
                keep_c += seg_c
                keep_f += seg_f
                out += len(seg_c)
                keep_e.append(out - 1)
            start = e + 1
        if not keep_e:
            continue
        drawn[gid] = {"coords": keep_c, "flags": keep_f, "endPts": keep_e,
                      "advance": int(g.get("advance") or 1110)}

    if "--space" in sys.argv:
        # Non-destructive: your SVGs are untouched, only this build's metrics change.
        SIDE = int(round(32 * UPM / 1000.0))      # 32 units per 1000 em, each side
        print("\n  --space: normalising sidebearings to %d units (%d/1000 em)" % (SIDE, 32))
        for gid, d in drawn.items():
            xs = [p[0] for p in d["coords"]]
            lo, hi = min(xs), max(xs)
            shift = SIDE - lo
            if shift:
                d["coords"] = [[p[0] + shift, p[1]] for p in d["coords"]]
            d["advance"] = int(round((hi - lo) + 2 * SIDE))
        print()

    drawn, bad = provenance_check(drawn)
    if bad:
        print("\n  EXCLUDED — these carry Faruma / DhivehiMuraka coordinates:")
        for gid, hits, tot in bad:
            print("    %s  %d of %d points are not yours — redraw it" % (gid, hits, tot))
        print()

    if not drawn:
        sys.exit("Nothing left to build. Draw a letter from scratch first.")

    from fontTools.fontBuilder import FontBuilder
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    from fontTools.ttLib.tables import ttProgram

    order = [".notdef", "space", "uni00A0"] + sorted(drawn)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({0x20: "space", 0xA0: "uni00A0",
                          **{int(g[3:], 16): g for g in drawn}})

    def blank():
        g = Glyph(); g.numberOfContours = 0
        g.coordinates = GlyphCoordinates([]); g.flags = array.array("B", [])
        g.endPtsOfContours = []
        g.program = ttProgram.Program(); g.program.fromBytecode(b"")
        return g

    def notdef_box():
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        pen = TTGlyphPen(None)
        x0, x1, y0, y1, t = 120, 580, 0, 1300, 90
        for ring in ([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                     [(x0 + t, y0 + t), (x0 + t, y1 - t), (x1 - t, y1 - t), (x1 - t, y0 + t)]):
            pen.moveTo(ring[0])
            for q in ring[1:]:
                pen.lineTo(q)
            pen.closePath()
        return pen.glyph()

    glyfs = {".notdef": notdef_box(), "space": blank(), "uni00A0": blank()}
    for gid, d in drawn.items():
        g = Glyph()
        g.numberOfContours = len(d["endPts"])
        g.coordinates = GlyphCoordinates([tuple(p) for p in d["coords"]])
        g.flags = array.array("B", [1 if f else 0 for f in d["flags"]])
        g.endPtsOfContours = list(d["endPts"])
        g.program = ttProgram.Program(); g.program.fromBytecode(b"")
        glyfs[gid] = g
    fb.setupGlyf(glyfs)
    for g in glyfs.values():
        if g.numberOfContours:
            g.recalcBounds(fb.font["glyf"])

    # lsb must equal the glyph's xMin in TrueType, or renderers that trust hmtx
    # shift the outline sideways.
    def lsb(n):
        if n in (".notdef", "space", "uni00A0"):
            return 0
        return int(min(p[0] for p in drawn[n]["coords"]))
    fb.setupHorizontalMetrics({n: (700 if n in (".notdef", "space", "uni00A0") else drawn[n]["advance"], lsb(n))
                               for n in order})
    fb.setupHorizontalHeader(ascent=ASC, descent=DESC, lineGap=GAP)
    lic = "This Font Software is licensed under the SIL Open Font License, Version 1.1."
    fb.setupNameTable({
        "copyright": COPYRIGHT,
        "familyName": FAMILY, "styleName": STYLE,
        "uniqueFontIdentifier": "%s;%s" % (PSNAME, VERSION),
        "fullName": "%s %s" % (FAMILY, STYLE),
        "version": "Version %s" % VERSION, "psName": PSNAME,
        "designer": AUTHOR, "manufacturer": AUTHOR,
        "licenseDescription": OFL_DESC,
        "licenseInfoURL": "https://openfontlicense.org"})
    ink_hi = max((max(p[1] for p in d["coords"]) for d in drawn.values()), default=ASC)
    ink_lo = min((min(p[1] for p in d["coords"]) for d in drawn.values()), default=DESC)
    fb.setupOS2(version=4, sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=GAP,
                usWinAscent=max(ASC, int(ink_hi) + 10),
                usWinDescent=max(abs(DESC), abs(int(ink_lo)) + 10), fsType=0,
                sxHeight=1024, sCapHeight=1400,
                fsSelection=0x40 | 0x80, achVendID=VENDOR)
    fb.setupPost(italicAngle=0)
    fb.font["head"].fontRevision = float(VERSION)   # must match name IDs 3 and 5

    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import ttProgram as _tp
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 15}
    fb.font["gasp"] = gasp

    prep = newTable("prep")                     # smart dropout control
    prog = _tp.Program()
    prog.fromAssembly(["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"])
    prep.program = prog
    fb.font["prep"] = prep

    os2t = fb.font["OS/2"]
    os2t.ulCodePageRange1 = 1                   # Latin 1
    os2t.ulCodePageRange2 = 0

    try:
        from fontTools.ttLib.removeOverlaps import removeOverlaps
        removeOverlaps(fb.font)
        print("      overlaps removed")
    except Exception as e:
        print("      NOTE overlaps not removed (%s) — pip3 install --user skia-pathops"
              % type(e).__name__)

    out = os.path.join(HERE, "..", "..", "fonts", "ttf", "%s.ttf" % PSNAME)
    fb.save(out)
    pts = sum(len(d["coords"]) for d in drawn.values())
    print("TTF   %s" % out)
    print("      %d letters, %d points, upm %d, fsType 0" % (len(drawn), pts, UPM))
    print("      %s" % ", ".join(sorted(drawn)))
    try:
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "make_specimen.py"), out],
                       check=False, capture_output=True)
        print("SPEC  %s" % os.path.join(HERE, "specimen.html"))
    except Exception:
        pass
    print("\nInstall:  open %s" % out)


if __name__ == "__main__":
    main()
