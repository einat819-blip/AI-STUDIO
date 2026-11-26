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
import sys
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


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


# ----------------------------------------------------------------- v4: short, clean end cards
# Card 1: "*הפריפריה נמכרת בנפרד." (the yellow brush from the supplied card)
# Card 2: original logo + "המציאות כותבת את התסריט. / אני רק מנפישה אותה."
def build_v4():
    from PIL import ImageDraw, ImageFont
    clean = np.asarray(Image.open(os.path.join(OUT, "endcard_clean.png")).convert("RGB")).astype(np.float32)
    final = np.asarray(Image.open(os.path.join(OUT, "endcard_final.png")).convert("RGB")).astype(np.float32)
    rng = np.random.default_rng(5)
    bg = clean.copy()
    for y0, y1 in [(616, 658), (1484, 1524)]:  # remove the two gold separator lines
        fill = coons(bg, y0, y1, 0, W)
        fill += rng.normal(0, 0.9, fill.shape).astype(np.float32)
        m = rect_mask(y0, y1, 0, W, feather=3, inset=3)[y0:y1, :, None]
        bg[y0:y1] = bg[y0:y1] * (1 - m) + fill * m
    Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "v4_bg.png"))

    # brush cut-out: yellow paint + the dark text inside it
    y0, y1 = 400, 615
    blk = final[y0:y1].astype(np.uint8)
    hsv = cv2.cvtColor(blk, cv2.COLOR_RGB2HSV)
    yellow = ((hsv[..., 0] > 12) & (hsv[..., 0] < 40) & (hsv[..., 1] > 110) & (hsv[..., 2] > 140)).astype(np.uint8)
    shape = cv2.morphologyEx(yellow, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    shape = cv2.morphologyEx(shape, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    alpha = cv2.GaussianBlur(shape.astype(np.float32), (0, 0), 1.2)
    ys, xs = np.where(shape > 0)
    a0, a1, b0, b1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([blk[a0:a1, b0:b1], (alpha[a0:a1, b0:b1] * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "v4_brush.png"))

    # tagline re-set in Heebo so it is crisp at any size
    font = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Heebo-Bold.ttf"), 54)
    lines = ["המציאות כותבת את התסריט.", "אני רק מנפישה אותה."]
    img = Image.new("RGBA", (W, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, ln in enumerate(lines):
        d.text((W // 2, 40 + k * 80), ln, font=font, fill=(245, 245, 245, 255), anchor="mm", direction="rtl",
               language="he")
    img.save(os.path.join(OUT, "v4_tagline.png"))
    print("v4 end card assets written")


def build_tagline(size, spacing, name):
    """Studio tagline set in Heebo Bold (white), two centred RTL lines."""
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Heebo-Bold.ttf"), size)
    lines = ["המציאות כותבת את התסריט.", "אני רק מנפישה אותה."]
    hgt = spacing + 2 * size
    img = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, ln in enumerate(lines):
        d.text((W // 2, hgt // 2 + (k - 0.5) * spacing), ln, font=font, fill=(245, 245, 245, 255), anchor="mm",
               direction="rtl", language="he")
    img.save(os.path.join(OUT, name))
    print("tagline", size, "px ->", name, img.size)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "v4":
    build_v4()
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "v5":
    build_tagline(68, 100, "v5_tagline.png")   # +25% (54 -> 68 px), spacing scaled with it
