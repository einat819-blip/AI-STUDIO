# -*- coding: utf-8 -*-
"""TEMPORARY typographic wordmark for AI NATI STUDIOS.

No official studio logo file was supplied, so the showreel uses this
placeholder. Replace it by passing --studio-logo <official.png> to
render_v2.py (transparent PNG, any size; it is fitted to the same width).

python3 make_studio_wordmark.py <fonts dir> <out.png>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

PINK = (255, 46, 136, 255)
YELLOW = (255, 212, 0, 255)
WHITE = (255, 255, 255, 255)


def sparkle(d, cx, cy, r, fill):
    """4-point AI sparkle."""
    k = r * 0.28
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    d.polygon(pts, fill=fill)


def make(fonts, out, ss=3):
    big = ImageFont.truetype(os.path.join(fonts, "Rubik-Black.ttf"), 200 * ss)
    small = ImageFont.truetype(os.path.join(fonts, "Rubik-Black.ttf"), 62 * ss)
    w_ai = big.getlength("AI")
    w_sp = big.getlength(" ") * 0.85
    w_nati = big.getlength("NATI")
    total = w_ai + w_sp + w_nati
    track = 0.42 * 62 * ss
    letters = "STUDIOS"
    w_st = sum(small.getlength(c) for c in letters) + track * (len(letters) - 1)
    W = int(max(total, w_st) + 120 * ss)
    H = int(330 * ss)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0 = (W - total) / 2
    base = 205 * ss
    d.text((x0, base), "AI", font=big, fill=YELLOW, anchor="ls")
    d.text((x0 + w_ai + w_sp, base), "NATI", font=big, fill=WHITE, anchor="ls")
    # sparkle tucked at the top-right of "AI"
    sparkle(d, x0 + w_ai + 10 * ss, 42 * ss, 30 * ss, PINK)
    # pink rule + tracked STUDIOS
    y_rule = 236 * ss
    d.rounded_rectangle([x0 + 6 * ss, y_rule, x0 + 6 * ss + 70 * ss, y_rule + 9 * ss], 4 * ss, fill=PINK)
    d.rounded_rectangle([x0 + total - 76 * ss, y_rule, x0 + total - 6 * ss, y_rule + 9 * ss], 4 * ss, fill=PINK)
    x = (W - w_st) / 2
    for c in letters:
        d.text((x, 268 * ss), c, font=small, fill=PINK, anchor="lm")
        x += small.getlength(c) + track
    im = im.resize((W // ss, H // ss), Image.LANCZOS)
    im = im.crop(im.getbbox())
    im.save(out)
    print("wordmark", im.size, "->", out)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2])
