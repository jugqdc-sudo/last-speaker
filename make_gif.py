#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GIF for the README: the desk log filling in line by line - the real one.
   make_gif.py [runs/<name>] → docs/desk.gif"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).parent
run = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "runs" / "torwali"
lines = [l for l in (run / "log.txt").read_text().splitlines() if l.strip()]
# the GIF skips PHON's every-50th-utterance progress lines, they are noise
lines = [l for l in lines if " PHON   utterance" not in l]
def font(size, bold=False):
    home = pathlib.Path.home()
    for p, idx in [(home / "Library/Fonts" / ("JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf"), 0),
                   (pathlib.Path("/System/Library/Fonts/Menlo.ttc"), 1 if bold else 0)]:
        if p.exists():
            return ImageFont.truetype(str(p), size, index=idx)
    return ImageFont.load_default()


f, fb = font(13), font(13, bold=True)

W, H, PAD, LH = 1120, 440, 18, 21
BG, INK, DIM = (22, 25, 15), (207, 213, 201), (123, 131, 120)
COL = {"CHIEF": (192, 74, 60), "SCOUT": (87, 160, 122), "PHON": (200, 145, 58), "LEX": (91, 127, 160),
       "GRAM": (192, 74, 60), "VOICE": (143, 123, 255), "SCRIBE": (122, 168, 144)}


def frame(shown, cursor_on, done=False):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 26), fill=(30, 34, 22))
    d.text((PAD, 6), "COLD.DESK", font=fb, fill=INK)
    d.text((PAD + 96, 6), "CASE 01 · THE LAST SPEAKER · REAL TAPE · torwali.wav · 72 min · one speaker", font=f, fill=DIM)
    y = 38
    vis = shown[-((H - 60) // LH):]
    for l in vis:
        # 15:59:13  SCOUT  cut the tape ...
        t, who, rest = l[:8], l[10:16].strip(), l[17:]
        d.text((PAD, y), t, font=f, fill=DIM)
        d.text((PAD + 78, y), who, font=fb, fill=COL.get(who, INK))
        d.text((PAD + 140, y), (rest[:124] + "…") if len(rest) > 125 else rest, font=f, fill=INK)
        y += LH
    if cursor_on and not done:
        d.rectangle((PAD + 140, y + 3, PAD + 148, y + 16), fill=(200, 145, 58))
    if done:
        d.rectangle((0, H - 26, W, H), fill=(30, 34, 22))
        d.text((PAD, H - 20), "every line carries a tape position · nothing translated · github: last-speaker", font=f, fill=DIM)
    return im


frames, durs = [], []
shown = []
for i, l in enumerate(lines):
    shown.append(l)
    # a line appears and holds for a moment; key lines hold longer
    hold = 900 if any(k in l for k in ("signed", "done in", "fights", "register shifts", "word candidates")) else 380
    frames.append(frame(shown, True)); durs.append(hold)
    frames.append(frame(shown, False)); durs.append(120)
frames.append(frame(shown, False, done=True)); durs.append(3500)
out = root / "docs" / "desk.gif"; out.parent.mkdir(exist_ok=True)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)
print(out, out.stat().st_size // 1024, "KB ·", len(frames), "frames ·", len(lines), "lines")
