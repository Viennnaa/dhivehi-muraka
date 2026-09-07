#!/usr/bin/env python3
"""Regenerate specimen.html from whatever is in DhivehiMuraka-Regular.ttf."""
import os, sys, time, json
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
TTF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "DhivehiMuraka-Regular.ttf")

CONS = [(0x780,"haa"),(0x781,"shaviyani"),(0x782,"noonu"),(0x783,"raa"),(0x784,"baa"),
        (0x785,"lhaviyani"),(0x786,"kaafu"),(0x787,"alifu"),(0x788,"vaavu"),(0x789,"meemu"),
        (0x78A,"faafu"),(0x78B,"dhaalu"),(0x78C,"thaa"),(0x78D,"laamu"),(0x78E,"gaafu"),
        (0x78F,"gnaviyani"),(0x790,"seenu"),(0x791,"daviyani"),(0x792,"zaviyani"),
        (0x793,"taviyani"),(0x794,"yaa"),(0x795,"paviyani"),(0x796,"javiyani"),
        (0x797,"chaviyani"),(0x7B1,"naviyani")]
ARAB = [(0x798,"ttaa"),(0x799,"hhaa"),(0x79A,"khaa"),(0x79B,"thaalu"),(0x79C,"zaa"),
        (0x79D,"sheenu"),(0x79E,"saadhu"),(0x79F,"daadhu"),(0x7A0,"to"),(0x7A1,"zo"),
        (0x7A2,"ainu"),(0x7A3,"ghainu"),(0x7A4,"qaafu"),(0x7A5,"waavu")]
FILI = [(0x7A6,"abafili"),(0x7A7,"aabaafili"),(0x7A8,"ibifili"),(0x7A9,"eebeefili"),
        (0x7AA,"ubufili"),(0x7AB,"ooboofili"),(0x7AC,"ebefili"),(0x7AD,"eybeyfili"),
        (0x7AE,"obofili"),(0x7AF,"oaboafili"),(0x7B0,"sukun")]

WORDS = ["ދިވެހި ރާއްޖެ",
         "ދިވެހި ބަހުން ލިޔެފައިވާ ފޮތެއް",
         "ދިވެހިރާއްޖެއަކީ އިންޑިއާ ކަނޑުގައި އޮންނަ ޖަޒީރާ ޤައުމެކެވެ."]

have = {int(g[3:], 16) for g in TTFont(TTF).getGlyphOrder() if g.startswith("uni")}

def cell(cp, nm):
    ok = cp in have
    shown = (chr(cp) if cp < 0x7A6 else "ހ" + chr(cp)) if ok else "&nbsp;"
    return ('<div class="g%s"><div class="gl">%s</div><div class="nm">%s</div>'
            '<div class="cp">U+%04X</div></div>' % ("" if ok else " miss", shown, nm, cp))

grid = lambda xs: "".join(cell(c, n) for c, n in xs)
ramp = "".join('<div style="font-size:%dpx">ދިވެހި ބަސް %d</div>' % (px, px)
               for px in (12, 14, 16, 20, 28, 40))
n = len(have)

html = """<meta charset="utf-8"><title>Dhivehi Muraka — specimen</title>
<style>
@font-face{font-family:DF;src:url('%s?v=%d')}
body{margin:0;padding:30px 34px;background:#fff;color:#111;max-width:1180px;
     font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
h1{font-size:26px;margin:0 0 4px}h1 span{color:#999;font-weight:400;font-size:17px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#888;
   margin:34px 0 12px;border-bottom:1px solid #eee;padding-bottom:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px}
.g{border:1px solid #eee;border-radius:7px;padding:10px 6px;text-align:center;background:#fafafa}
.g.miss{border-style:dashed;border-color:#e2cfcf;
        background:repeating-linear-gradient(45deg,#fff,#fff 6px,#fafafa 6px,#fafafa 12px)}
.gl{font-family:DF;font-size:44px;line-height:1.35;height:62px}
.nm{font-size:10px;color:#666;margin-top:2px}
.cp{font-size:9px;color:#bbb;font-family:ui-monospace,monospace}
.words{direction:rtl;text-align:right;font-family:DF;background:#fafafa;
       border:1px solid #eee;border-radius:8px;padding:18px 22px;margin-bottom:10px}
.w1{font-size:56px;line-height:1.9}.w2{font-size:26px;line-height:2.1}.w3{font-size:17px;line-height:2.2}
.stat{display:flex;gap:26px;margin:14px 0 0;font-size:13px}
.stat b{font-size:22px;display:block}.stat span{color:#888}
.legend{font-size:12px;color:#777;margin-top:8px}
.k{display:inline-block;width:11px;height:11px;border:1px dashed #e2cfcf;vertical-align:-1px;
   margin:0 4px 0 0;background:repeating-linear-gradient(45deg,#fff,#fff 4px,#fafafa 4px,#fafafa 8px)}
.ts{color:#bbb;font-size:11px;margin-top:26px}
</style>
<h1>Dhivehi Muraka <span>— %d of 50 letters</span></h1>
<div class="stat">
 <div><b>%d</b><span>consonants of 25</span></div>
 <div><b>%d</b><span>Arabic letters of 14</span></div>
 <div><b>%d</b><span>fili of 11</span></div>
 <div><b>%d</b><span>still to draw</span></div>
</div>
<h2>Dhivehi text</h2>
<div class="words w1">%s</div>
<div class="words w2">%s</div>
<div class="words w3">%s</div>
<h2>Size ramp</h2>
<div class="words" style="padding:10px 22px">%s</div>
<h2>Consonants</h2><div class="grid">%s</div>
<h2>Arabic transliteration letters</h2><div class="grid">%s</div>
<h2>Fili — shown on ހ</h2><div class="grid">%s</div>
<p class="legend"><span class="k"></span>not drawn yet</p>
<p class="ts">rebuilt %s · %d letters</p>
""" % (os.path.basename(TTF), int(time.time()), n,
       sum(1 for c, _ in CONS if c in have), sum(1 for c, _ in ARAB if c in have),
       sum(1 for c, _ in FILI if c in have), 50 - n,
       WORDS[0], WORDS[1], WORDS[2], ramp,
       grid(CONS), grid(ARAB), grid(FILI),
       time.strftime("%d %b %Y, %H:%M"), n)

out = os.path.join(HERE, "specimen.html")
open(out, "w", encoding="utf-8").write(html)
print("specimen.html rebuilt — %d letters" % n)
