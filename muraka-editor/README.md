# Muraka editor — blank-start build

A copy of the Gemini editor, changed so it can actually create letters and so the
font it builds is yours.

    open editor.html            # draw
    ⬇ Export JSON               # → ~/Downloads/dhivehi_muraka_edits.json
    python3 build_font.py
    open DhivehiFont-Regular.ttf

## What changed from the original

**It can draw now.** The original had no way to add a point — only
`nudgeSelectedPoint` on outlines that were already there. Added:

| Button | Does |
|---|---|
| ✎ **Pen** | click anywhere on the canvas to place a point |
| ⌖ **Move** | drag points (the original behaviour) |
| ＋ **New stroke** | start a separate contour of the same letter |
| ◠ **New: Curve** | what the Pen places — smooth curve points (default), or sharp corners |
| ⌇ **Flip point** | flip the selected point between curve and corner |
| ⌫ **Point** | delete the selected point |
| 🗑 **Clear** | empty the letter |

Hold **Shift** to pan while the Pen is active.

This is an **outline** editor: you trace around the edge of the stroke, up one side
and back down the other, not down its middle. A run of points in a straight line
closes into a zero-width sliver.

Curve points are off-curve in TrueType terms — a run of them gets an implied
on-curve point midway between each pair, which is what makes the whole run smooth.

**Every letter starts empty.** `font_data.js` shipped Faruma's coordinates in the
`muraka` field — 34 of 35 byte-identical to `Faruma.ttf` — and the editor loaded
them as your starting outline. Those are now blank. The `faruma` field is kept
and still draws the **red dashed ghost**, which is what a reference is for.

**Two paths that produced a derivative are disabled:**
- `resetCurrentToFaruma()` — the "🔴 Copy Faruma" button, which pasted Faruma's exact outline.
- `downloadModifiedTTF()` — it wrote your glyphs into the embedded
  `MURAKA_TTF_BASE64`, i.e. into Faruma, keeping every glyph you never touched.
  The embedded font is stripped; use `build_font.py`.

**`build_font.py` starts from an empty font.** It opens no existing font at all.
Verified on a test build: no table is byte-identical to Faruma, and the only glyph
names in common are `.notdef` and `space`.

Output: 2048 upm, ascender 1536, descender −512, OS/2 v4, `fsType 0`,
USE_TYPO_METRICS set, overlaps removed, italic angle 0.

## Still to do

- [ ] Draw the 39 consonants and 11 fili
- [ ] Anchors on consonants and fili → `mark` / `mkmk` so vowels sit correctly
- [ ] `ccmp`, kerning
- [ ] Merge an OFL Latin (Inter or Source Sans) — don't draw Latin here
- [ ] `fontbakery --profile googlefonts`, `shaperglot check dv`
- [ ] OFL.txt, FONTLOG.txt, METADATA.pb, DESCRIPTION.en_us.html, public repo

Your original folder in `~/Downloads/DhivehiMuraka` is untouched.
