# -*- coding: utf-8 -*-
"""Render the picture for one version of the ad (video only, no audio).

python3 render_video.py --version main --sources DIR --logo LOGO.png \
        --fonts DIR --out out.mp4 [--no-text] [--preview sheet.jpg]

Frame-accurate: every output frame is chosen explicitly from the EDL, freezes
are the identical decoded frame repeated (true freeze frames, nothing moves).
"""
import argparse
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import edl as E

SRC_W, SRC_H = 720, 1264  # all delivered clips are 720x1264 @ 24 fps

# Gentle, realistic grades. Village: warm + natural. Food: warm + rich but the
# source is already very orange, so saturation is pulled back slightly and the
# hottest highlights are nudged away from "burnt orange".
GRADES = {
    "village": "eq=contrast=1.04:saturation=1.03:gamma=0.985,"
               "colorbalance=rs=0.015:bs=-0.025:rm=0.012:bm=-0.015",
    "food": "eq=contrast=1.05:saturation=0.92:gamma=0.98,"
            "colorbalance=rh=-0.03:gh=-0.005:bh=0.02:rm=-0.01",
}
SHARPEN = "unsharp=5:5:0.30:5:5:0.0"


def crop_box(zoom=1.0, center=(0.5, 0.5)):
    """9:16 crop in source pixels (no stretching), optional punch-in."""
    h = SRC_H / zoom
    w = h * 9.0 / 16.0
    if w > SRC_W:  # never happens for 720x1264, kept for safety
        w = SRC_W
        h = w * 16.0 / 9.0
    cx, cy = center[0] * SRC_W, center[1] * SRC_H
    x = min(max(cx - w / 2, 0), SRC_W - w)
    y = min(max(cy - h / 2, 0), SRC_H - h)
    # even integers for clean chroma
    w, h = int(round(w / 2) * 2), int(round(h / 2) * 2)
    return w, h, int(round(x)), int(round(y))


def decode_frames(path, indices, grade, zoom=1.0, center=(0.5, 0.5)):
    """Decode exactly the requested source frames, graded + fitted to 1080x1920."""
    a, b = min(indices), max(indices)
    w, h, x, y = crop_box(zoom, center)
    vf = (
        f"select='between(n\\,{a}\\,{b})',"
        f"crop={w}:{h}:{x}:{y},"
        f"scale={E.W}:{E.H}:flags=lanczos+accurate_rnd+full_chroma_int:"
        f"in_color_matrix=bt709:in_range=tv,"
        f"format=gbrp,{GRADES[grade]},{SHARPEN},format=rgb24"
    )
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-vf", vf,
           "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    fsz = E.W * E.H * 3
    n = len(raw) // fsz
    assert n == b - a + 1, f"{path}: wanted {b - a + 1} frames, got {n}"
    arr = np.frombuffer(raw, np.uint8).reshape(n, E.H, E.W, 3)
    return {a + i: arr[i] for i in range(n)}


# ---------------------------------------------------------------- text ----
def font(fonts_dir, size):
    return ImageFont.truetype(os.path.join(fonts_dir, "Heebo-Black.ttf"), size)


def text_plate(cue, fonts_dir):
    """Full-frame RGBA plate. Hebrew RTL, runs laid out right-to-left."""
    f = font(fonts_dir, cue["size"])
    line_h = int(cue["size"] * 1.12)
    plate = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)
    n = len(cue["lines"])
    base0 = cue["y"] - (n - 1) * line_h / 2 + cue["size"] * 0.36
    for li, runs in enumerate(cue["lines"]):
        widths = [f.getlength(t, direction="rtl", language="he") for t, _ in runs]
        total = sum(widths)
        assert total < E.W - 160, f"line too wide for safe area: {total}"
        x_right = E.W / 2 + total / 2
        base = base0 + li * line_h
        for (t, col), w in zip(runs, widths):
            d.text((x_right, base), t, font=f, fill=col + (255,), anchor="rs",
                   direction="rtl", language="he")
            x_right -= w
    # soft dark halo for legibility on bright daylight (no hard outline/box)
    alpha = plate.getchannel("A")
    halo = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(20))
    halo = halo.point(lambda v: int(v * 0.55))
    tight = alpha.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.55))
    shadow = Image.new("RGBA", (E.W, E.H), (20, 12, 6, 0))
    shadow.putalpha(Image.fromarray(np.maximum(np.asarray(halo), np.asarray(tight))))
    shadow = shadow.transform(shadow.size, Image.AFFINE, (1, 0, 0, 0, 1, -5))  # +5px down
    out = Image.alpha_composite(shadow, plate)
    bbox = out.getchannel("A").getbbox()
    return out, bbox


def ease_out_back(x, k=1.6):
    x = min(max(x, 0.0), 1.0)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def paste_scaled(base, plate, bbox, scale, opacity, dy=0):
    """alpha-composite plate's bbox region scaled about its center."""
    region = plate.crop(bbox)
    if abs(scale - 1.0) > 1e-3:
        nw = max(1, int(round(region.width * scale)))
        nh = max(1, int(round(region.height * scale)))
        region = region.resize((nw, nh), Image.LANCZOS)
    if opacity < 0.999:
        a = region.getchannel("A").point(lambda v: int(v * opacity))
        region.putalpha(a)
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2 + dy
    x = int(round(cx - region.width / 2))
    y = int(round(cy - region.height / 2))
    base.alpha_composite(region, (x, y))


def apply_text(img, cue_plates, f):
    for cue, plate, bbox in cue_plates:
        if cue["start"] <= f <= cue["end"]:
            k = f - cue["start"]
            # quick pop: 3 frames in, settles with a tiny overshoot, no bounce
            scale = 1.0 + 0.16 * (1 - ease_out_cubic(k / 3.0))
            opacity = min(1.0, (k + 1) / 2.0)
            paste_scaled(img, plate, bbox, scale, opacity)


# ------------------------------------------------------------- endcard ----
def endcard_assets(bg_frame, logo_path, fonts_dir):
    bg = Image.fromarray(bg_frame).filter(ImageFilter.GaussianBlur(26))
    arr = np.asarray(bg).astype(np.float32)
    # darken + radial vignette so the badge pops but the warmth stays
    yy, xx = np.mgrid[0:E.H, 0:E.W]
    r = np.sqrt(((xx - E.W / 2) / (E.W * 0.75)) ** 2 + ((yy - E.H * 0.45) / (E.H * 0.6)) ** 2)
    vig = np.clip(1.0 - 0.55 * r ** 2, 0.35, 1.0)
    arr = arr * 0.42 * vig[..., None]
    bg = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    logo = Image.open(logo_path).convert("RGBA")
    d = E.ENDCARD["logo_d"]
    logo = logo.resize((d, d), Image.LANCZOS)
    pad = 80
    plate = Image.new("RGBA", (d + 2 * pad, d + 2 * pad), (0, 0, 0, 0))
    sh_a = logo.getchannel("A").filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.6))
    sh = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    sh.putalpha(sh_a)
    plate.alpha_composite(sh, (pad, pad + 14))
    plate.alpha_composite(logo, (pad, pad))
    full = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    full.alpha_composite(plate, (E.W // 2 - plate.width // 2, E.ENDCARD["logo_y"] - plate.height // 2))
    logo_bbox = full.getchannel("A").getbbox()

    tag_cue = dict(y=E.ENDCARD["tag_y"], size=E.ENDCARD["tag_size"],
                   lines=[[(E.ENDCARD["tag"], E.CREAM)]])
    tag_plate, tag_bbox = text_plate(tag_cue, fonts_dir)
    return bg, (full, logo_bbox), (tag_plate, tag_bbox)


def endcard_frame(k, assets, with_text=True):
    bg, (logo, lb), (tag, tb) = assets
    img = bg.copy()
    ec = E.ENDCARD
    # logo: quick settle-in (0.33 s) then a very slow push - "light motion"
    li = k - ec["logo_in"]
    s = 0.86 + 0.14 * ease_out_back(li / 8.0, 1.2)
    s *= 1.0 + 0.0006 * max(0, li - 8)
    hk = k - ec["hit"]
    if hk >= 0:  # tiny pulse on the final music hit
        s *= 1.0 + 0.018 * math.exp(-hk / 3.0)
    paste_scaled(img, logo, lb, s, min(1.0, (li + 1) / 4.0))
    if with_text and k >= ec["tag_in"]:
        tk = k - ec["tag_in"]
        paste_scaled(img, tag, tb, 1.0, min(1.0, (tk + 1) / 4.0),
                     dy=int(24 * (1 - ease_out_cubic(tk / 6.0))))
    return img


# ---------------------------------------------------------------- main ----
def render(version, sources, logo, fonts_dir, out, with_text=True, preview=None):
    v = E.VERSIONS[version]
    edl, cues = v["edl"], v["text"]
    cue_plates = []
    if with_text:
        for c in cues:
            p, bb = text_plate(c, fonts_dir)
            cue_plates.append((c, p, bb))

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{E.W}x{E.H}", "-r", str(E.FPS), "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
         "-tune", "film", "-g", "24", "-bf", "2",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-color_range", "tv", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    f_out = 0
    thumbs = []
    for seg in edl:
        if seg.get("src"):
            path = os.path.join(sources, E.SRC[seg["src"]])
            frames = decode_frames(path, seg["frames"], seg["grade"],
                                   seg.get("zoom", 1.0), seg.get("center", (0.5, 0.5)))
            for idx in seg["frames"]:
                img = Image.fromarray(frames[idx]).convert("RGBA")
                apply_text(img, cue_plates, f_out)
                rgb = img.convert("RGB")
                enc.stdin.write(rgb.tobytes())
                if preview is not None and f_out % 6 == 0:
                    thumbs.append((f_out, rgb.resize((180, 320))))
                f_out += 1
        else:
            bsrc, bidx = seg["bg"]
            bg_frame = decode_frames(os.path.join(sources, E.SRC[bsrc]), [bidx], "food")[bidx]
            assets = endcard_assets(bg_frame, logo, fonts_dir)
            for k in range(seg["count"]):
                img = endcard_frame(k, assets, with_text)
                rgb = img.convert("RGB")
                enc.stdin.write(rgb.tobytes())
                if preview is not None and f_out % 6 == 0:
                    thumbs.append((f_out, rgb.resize((180, 320))))
                f_out += 1
    enc.stdin.close()
    assert enc.wait() == 0
    print(f"{out}: {f_out} frames ({f_out / E.FPS:.3f}s)")

    if preview:
        cols = 12
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * 180, rows * 340), (0, 0, 0))
        dd = ImageDraw.Draw(sheet)
        for i, (fn, t) in enumerate(thumbs):
            x, y = (i % cols) * 180, (i // cols) * 340
            sheet.paste(t, (x, y))
            dd.text((x + 4, y + 322), f"{fn} ({fn / E.FPS:.2f}s)", fill=(255, 255, 0))
        sheet.save(preview, quality=88)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="main", choices=list(E.VERSIONS))
    ap.add_argument("--sources", required=True)
    ap.add_argument("--logo", required=True)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-text", action="store_true")
    ap.add_argument("--preview")
    a = ap.parse_args()
    render(a.version, a.sources, a.logo, a.fonts, a.out, not a.no_text, a.preview)
