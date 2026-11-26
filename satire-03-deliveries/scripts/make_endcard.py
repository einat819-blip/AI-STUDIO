"""End card: upscale the supplied slide to 1080x1920, replace the AI-generated
logo with the original AINATI STUDIOS logo, and prepare reveal masks so the
render can bring the lines in one by one (the "*הפריפריה נמכרת בנפרד." punch
lands a beat after the headline instead of being read in advance).

The empty background ("clean plate") is rebuilt with Coons-patch interpolation
from clean rows/columns around each text block, so no letter-shaped ghosts
remain where the old AI logo was.

Run:  python3 scripts/make_endcard.py
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter1d

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(ROOT, "source", "images", "end_card_original.webp")
LOGO = os.path.join(ROOT, "source", "images", "ainati_logo_original.webp")
OUT = os.path.join(ROOT, "assets", "endcard")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920

# Patch rectangles (y0, y1, x0, x1) on the 1080x1920 upscale. Boundaries sit on
# measured clean background rows, between the separators and the swoosh.
PATCHES = {
    "top": (88, 606, 0, W),        # headline + yellow brush
    "middle": (652, 1087, 0, W),   # satire lines + "שייקח כיסא"
    "logo": (1087, 1491, 0, W),    # AI logo (removed for good)
    "tagline": (1532, 1692, 140, 940),
}
# Reveal masks (y0, y1, x0, x1)
REVEALS = {
    "title": (88, 409, 0, W),
    "brush": (409, 606, 0, W),
    "satire": (652, 852, 0, W),
    "wait": (852, 1087, 0, W),
    "logo": (1087, 1491, 0, W),
    "tagline": (1532, 1692, 140, 940),
}


def coons(img, y0, y1, x0, x1):
    blk = img[y0:y1, x0:x1]
    h, w = blk.shape[:2]
    top = gaussian_filter1d(img[y0:y0 + 3, x0:x1].mean(0), 14, axis=0)
    bot = gaussian_filter1d(img[y1 - 3:y1, x0:x1].mean(0), 14, axis=0)
    lc = slice(max(x0, 0), max(x0, 0) + 3)
    rc = slice(min(x1, W) - 3, min(x1, W))
    left = gaussian_filter1d(img[y0:y1, lc].mean(1), 10, axis=0)
    right = gaussian_filter1d(img[y0:y1, rc].mean(1), 10, axis=0)
    u = np.linspace(0, 1, w)[None, :, None]
    v = np.linspace(0, 1, h)[:, None, None]
    p00, p10 = top[0], top[-1]
    p01, p11 = bot[0], bot[-1]
    P = ((1 - v) * top[None] + v * bot[None] + (1 - u) * left[:, None] + u * right[:, None]
         - ((1 - u) * (1 - v) * p00 + u * (1 - v) * p10 + (1 - u) * v * p01 + u * v * p11))
    return P


def rect_mask(y0, y1, x0, x1, feather=5, inset=0):
    m = np.zeros((H, W), np.float32)
    m[y0 + inset:y1 - inset, x0 + inset:x1 - inset] = 1
    if feather:
        m = cv2.GaussianBlur(m, (0, 0), feather)
    return m


def main():
    card = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
    card = card.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    img = np.asarray(card).astype(np.float32)
    rng = np.random.default_rng(3)

    clean = img.copy()
    for name, (y0, y1, x0, x1) in PATCHES.items():
        fill = coons(img, y0, y1, x0, x1)
        fill += rng.normal(0, 0.9, fill.shape).astype(np.float32)
        m = rect_mask(y0, y1, x0, x1, feather=3, inset=3)[y0:y1, x0:x1, None]
        if name == "tagline":
            # keep the orange swoosh pixels untouched
            blk = img[y0:y1, x0:x1]
            orange = ((blk.max(2) - blk.min(2)) > 45) & (blk.max(2) > 50)
            orange = cv2.dilate(orange.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
            orange = cv2.GaussianBlur(orange, (0, 0), 3)
            m = m * (1 - orange[..., None])
        clean[y0:y1, x0:x1] = blk_mix = img[y0:y1, x0:x1] * (1 - m) + fill * m

    # final card = original with the AI logo area replaced by clean plate + original logo
    final = img.copy()
    y0, y1, x0, x1 = PATCHES["logo"]
    final[y0:y1, x0:x1] = clean[y0:y1, x0:x1]
    logo = Image.open(LOGO).convert("RGBA")
    lw = 600
    lh = round(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    cx, cy = W // 2, 1282
    lx, ly = cx - lw // 2, cy - lh // 2
    la = np.asarray(logo).astype(np.float32)
    alpha = la[..., 3:4] / 255.0
    glow = np.zeros((H, W), np.float32)
    glow[ly:ly + lh, lx:lx + lw] = alpha[..., 0]
    glow = cv2.GaussianBlur(glow, (0, 0), 24)
    glow = glow / (glow.max() + 1e-6)
    gold = np.array([255, 186, 80], np.float32)
    final = final * (1 - 0.16 * glow[..., None]) + gold * (0.16 * glow[..., None])
    region = final[ly:ly + lh, lx:lx + lw]
    final[ly:ly + lh, lx:lx + lw] = region * (1 - alpha) + la[..., :3] * alpha

    final = np.clip(final, 0, 255).astype(np.uint8)
    clean = np.clip(clean, 0, 255).astype(np.uint8)
    Image.fromarray(final).save(os.path.join(OUT, "endcard_final.png"))
    Image.fromarray(clean).save(os.path.join(OUT, "endcard_clean.png"))
    for name, (a, b, c, d) in REVEALS.items():
        m = (rect_mask(a, b, c, d, feather=4) * 255).astype(np.uint8)
        Image.fromarray(m).save(os.path.join(OUT, f"mask_{name}.png"))
    print("endcard written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
