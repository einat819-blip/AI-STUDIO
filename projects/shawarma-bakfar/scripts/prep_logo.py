"""Cut a round logo out of its white square background -> RGBA PNG.

Usage: python3 prep_logo.py <input image> <output png>
Works for any of the three crossed-knives logo variants as long as the badge
is a circle on a light background.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw


def cut_circle(src, dst, inset=1.5, ss=4):
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        white = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, im)
    im = im.convert("RGB")
    a = np.asarray(im).astype(int)
    nonwhite = a.min(axis=2) < 235
    ys, xs = np.nonzero(nonwhite)
    cx = (xs.min() + xs.max()) / 2.0
    cy = (ys.min() + ys.max()) / 2.0
    r = min(xs.max() - xs.min(), ys.max() - ys.min()) / 2.0 - inset
    w, h = im.size
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).ellipse(
        [(cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss], fill=255
    )
    m = m.resize((w, h), Image.LANCZOS)
    out = im.convert("RGBA")
    out.putalpha(m)
    box = (int(cx - r - 2), int(cy - r - 2), int(cx + r + 3), int(cy + r + 3))
    out.crop(box).save(dst)
    print(f"logo: center=({cx:.1f},{cy:.1f}) r={r:.1f} -> {dst}")


if __name__ == "__main__":
    cut_circle(sys.argv[1], sys.argv[2])
