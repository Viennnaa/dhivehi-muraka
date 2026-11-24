#!/usr/bin/env python3
"""Import letters drawn in the Muraka editor into the UFO source.

sources/DhivehiMuraka-Regular.ufo is the font's source, and any UFO editor can
edit it. The Muraka editor is another way to draw letters for it: use
"Export JSON" in the editor, then

    python3 scripts/import_drawings.py ~/Downloads/dhivehi_muraka_edits.json [uni0780 ...]

and rebuild with scripts/build.sh. Name glyphs to import only those.

Each exported letter replaces that glyph's outline and advance width; kerning
and everything else in the UFO are kept. Fili stay zero-width. Mark anchors
stay where they are unless the outline changed, in which case they move to the
centre of the new outline, as the old build placed them. A letter new to the
font is added with its Unicode value, and Thaana letters get anchors.

Provenance gate: point MURAKA_REFERENCE at the local reference data and any
letter sharing coordinates with it is refused.
"""
import json
import os
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.recordingPen import RecordingPen

UFO = Path(__file__).resolve().parent.parent / "sources" / "DhivehiMuraka-Regular.ufo"
BASES = set(range(0x780, 0x7A6)) | {0x7B1, 0x25CC}
MARKS_BELOW = {0x7A8, 0x7A9}
MARKS = set(range(0x7A6, 0x7B1))


def segment_type(c, i):
    if not c[i][2]:
        return None
    return "qcurve" if not c[i - 1][2] else "line"


def poly_area(c):
    return sum(c[i][0] * c[i - 1][1] - c[i - 1][0] * c[i][1] for i in range(len(c))) / -2.0


def to_path(contours):
    p = pathops.Path()
    pen = PointToSegmentPen(p.getPen())
    for c in contours:
        pen.beginPath()
        for i, (x, y, _) in enumerate(c):
            pen.addPoint((x, y), segment_type(c, i))
        pen.endPath()
    return pathops.simplify(p, fix_winding=True)


def same_fill(a, b):
    ap = AreaPen()
    pathops.op(to_path(a), to_path(b), pathops.PathOp.XOR).draw(ap)
    return abs(ap.value) < 1


def postscript_direction(contours):
    """Outer contours counter-clockwise, keeping the filled shape the editor drew."""
    allccw = [c[::-1] if poly_area(c) < 0 else c for c in contours]
    if same_fill(contours, allccw):
        return allccw
    biggest = max(contours, key=lambda c: abs(poly_area(c)))
    return [c[::-1] for c in contours] if poly_area(biggest) < 0 else contours


def centre_x(contours):
    """Middle of the overlap-removed outline's points: how v1.001 placed every anchor."""
    rec = RecordingPen()
    to_path(contours).draw(rec)
    xs = [round(pt[0]) for _, args in rec.value for pt in args if pt is not None]
    return int(round((min(xs) + max(xs)) / 2.0))


def contours_of(g):
    out, s = [], 0
    for e in g.get("endPts") or []:
        pts, fl = g["coords"][s:e + 1], g["flags"][s:e + 1]
        s = e + 1
        if len(pts) >= 3:
            out.append([(x, y, bool(f)) for (x, y), f in zip(pts, fl)])
    return out


def ufo_contours(glyph):
    return [[(p.x, p.y, p.type is not None) for p in c] for c in glyph.contours]


def provenance_refusals(store):
    ref_path = os.environ.get("MURAKA_REFERENCE", "")
    if not ref_path or not os.path.exists(ref_path):
        return {}
    txt = open(ref_path, encoding="utf-8").read()
    ref = {e["id"]: e for e in json.loads(txt[txt.index("["):txt.rindex("]") + 1])}
    bad = {}
    for gid, g in store.items():
        e = ref.get(gid)
        if not e:
            continue
        pts = {tuple(p) for p in g["coords"]}
        hits = sum(len(pts & {tuple(p) for p in e.get(k, {}).get("coords", [])}) for k in ("faruma", "muraka"))
        if hits:
            bad[gid] = (hits, len(pts))
    return bad


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    store = json.load(open(sys.argv[1], encoding="utf-8"))
    only = set(sys.argv[2:])
    store = {k: v for k, v in store.items()
             if k.startswith("uni") and (v.get("coords") or []) and (not only or k in only)}
    if not os.environ.get("MURAKA_REFERENCE"):
        print("note: MURAKA_REFERENCE not set, so the provenance gate is off")
    bad = provenance_refusals(store)
    for gid, (hits, total) in sorted(bad.items()):
        print("  REFUSED %s: %d of %d points match the reference; redraw it" % (gid, hits, total))

    font = ufoLib2.Font.open(UFO)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    order = font.lib.setdefault("public.glyphOrder", list(font.keys()))
    changed = []
    for gid, g in sorted(store.items()):
        if gid in bad:
            continue
        contours = contours_of(g)
        if not contours:
            continue
        contours = postscript_direction(contours)
        cp = int(gid[3:], 16)
        new = gid not in font
        glyph = font[gid] if not new else font.newGlyph(gid)
        if new:
            glyph.unicodes = [cp]
            order.append(gid)
            if cp in MARKS:
                cats[gid] = "mark"
            elif cp in BASES:
                cats[gid] = "base"
        outline_changed = new or ufo_contours(glyph) != contours
        is_mark = cats.get(gid) == "mark"
        width = 0 if is_mark else int(g.get("advance") or glyph.width)
        if not outline_changed and glyph.width == width:
            continue
        glyph.clearContours()
        pen = glyph.getPointPen()
        for c in contours:
            pen.beginPath()
            for i, (x, y, _) in enumerate(c):
                pen.addPoint((x, y), segmentType=segment_type(c, i))
            pen.endPath()
        glyph.width = width
        if outline_changed and cats.get(gid) in ("base", "mark"):
            centre = centre_x(contours)
            names = (["_bottom"] if cp in MARKS_BELOW else ["_top"]) if is_mark else ["top", "bottom"]
            old = {a.name: a.x for a in glyph.anchors}
            glyph.clearAnchors()
            for n in names:
                glyph.appendAnchor({"name": n, "x": centre, "y": 0})
            moved = ", ".join("%s %s -> %d" % (n, old.get(n, "new"), centre) for n in names if old.get(n) != centre)
            if moved:
                print("  %s anchors: %s" % (gid, moved))
        changed.append(gid + (" (new)" if new else ""))

    if changed:
        font.save()
        print("imported %d letter(s): %s" % (len(changed), ", ".join(changed)))
    else:
        print("nothing changed")
    print("rebuild with scripts/build.sh")


if __name__ == "__main__":
    main()
