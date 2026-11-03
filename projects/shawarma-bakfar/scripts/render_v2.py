# -*- coding: utf-8 -*-
"""V2 picture: client cut (9.5 s) and AI NATI STUDIOS showreel (15 s).

python3 render_v2.py --version client|studio --sources DIR --fonts DIR \
    --logo shawarma_logo.png [--studio-logo official.png] --out out.mp4 [--preview sheet.jpg]
"""
import argparse
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import edl_v2 as E
import render_video as R1  # crop_box, GRADES, SHARPEN, easing

FONT_FILES = {"heebo": "Heebo-Black.ttf", "rubik": "Rubik-Black.ttf"}


# ------------------------------------------------------------ decoding ----
def decode(path, seg):
    """Return the list of output frames (RGB uint8) for one picture segment."""
    zoom, center = seg.get("zoom", 1.0), seg.get("center", (0.5, 0.5))
    w, h, x, y = R1.crop_box(zoom, center)
    fit = (f"crop={w}:{h}:{x}:{y},"
           f"scale={E.W}:{E.H}:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709:in_range=tv,"
           f"format=gbrp,{R1.GRADES[seg['grade']]},{R1.SHARPEN},format=rgb24")
    if "slowmo" in seg:
        a, b, nout = seg["slowmo"]
        factor = nout / (b - a + 1)
        vf = (f"select='between(n\\,{a}\\,{b})',setpts=N/24/TB,setpts=PTS*{factor:.5f},"
              f"minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,{fit}")
        want = nout
        order = None
    else:
        a, b = min(seg["frames"]), max(seg["frames"])
        vf = f"select='between(n\\,{a}\\,{b})',{fit}"
        want = b - a + 1
        order = [i - a for i in seg["frames"]]
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-vf", vf,
           "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    fsz = E.W * E.H * 3
    arr = np.frombuffer(raw, np.uint8).reshape(-1, E.H, E.W, 3)
    if order is None:
        frames = [arr[min(i, len(arr) - 1)] for i in range(want)]
    else:
        assert len(arr) == want, (path, len(arr), want)
        frames = [arr[i] for i in order]
    return frames


# ---------------------------------------------------------------- text ----
def line_plate(runs, font, y, halo):
    """One RTL line on a full-frame transparent plate."""
    plate = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)
    widths = [font.getlength(t, direction="rtl", language="he") for t, _ in runs]
    total = sum(widths)
    assert total < E.W - 120, f"line too wide: {total:.0f}px {runs}"
    x_right = E.W / 2 + total / 2
    base = y + font.size * 0.36
    for (t, col), w in zip(runs, widths):
        d.text((x_right, base), t, font=font, fill=tuple(col) + (255,), anchor="rs",
               direction="rtl", language="he")
        x_right -= w
    return add_shadow(plate, halo)


def add_shadow(plate, halo):
    a = plate.getchannel("A")
    if halo == "warm":      # soft dark halo for daylight footage
        h1 = a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.6))
        h2 = a.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.6))
        sh_a = Image.fromarray(np.maximum(np.asarray(h1), np.asarray(h2)))
        col, dy = (20, 12, 6), 5
    else:                   # crisp graphic drop shadow for the studio look
        sh_a = a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.55))
        col, dy = (16, 0, 34), 8
    sh = Image.new("RGBA", plate.size, col + (0,))
    sh.putalpha(sh_a)
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    return Image.alpha_composite(sh, plate)


def cue_plates(cue, fonts):
    font = ImageFont.truetype(os.path.join(fonts, FONT_FILES[cue["font"]]), cue["size"])
    halo = "warm" if cue["font"] == "heebo" or cue.get("bg") == "freeze" else "graphic"
    n = len(cue["lines"])
    lh = int(cue["size"] * 1.12)
    out = []
    for i, runs in enumerate(cue["lines"]):
        y = cue["y"] - (n - 1) * lh / 2 + i * lh
        p = line_plate(runs, font, y, halo)
        out.append((p, p.getchannel("A").getbbox()))
    return out


def paste(base, plate, bbox, scale=1.0, opacity=1.0, dx=0, dy=0, angle=0.0):
    region = plate.crop(bbox)
    if abs(scale - 1) > 1e-3:
        region = region.resize((max(1, int(region.width * scale)), max(1, int(region.height * scale))),
                               Image.LANCZOS)
    if abs(angle) > 0.05:
        region = region.rotate(angle, resample=Image.BICUBIC, expand=True)
    if opacity < 0.999:
        region.putalpha(region.getchannel("A").point(lambda v: int(v * max(0, opacity))))
    cx = (bbox[0] + bbox[2]) / 2 + dx
    cy = (bbox[1] + bbox[3]) / 2 + dy
    base.alpha_composite(region, (int(round(cx - region.width / 2)), int(round(cy - region.height / 2))))


eoc = R1.ease_out_cubic
eob = R1.ease_out_back


def anim_params(kind, k, smax=1.32):
    """scale, opacity, dy for an entrance animation at local frame k (>=0).
    smax caps the starting scale so a line never leaves the frame."""
    if kind == "slam":    # sharp: big -> 1.0 in 3 frames
        return 1 + (smax - 1) * (1 - eoc(k / 3)), min(1.0, (k + 1) / 2), 0
    if kind == "punch":   # comic slam with overshoot
        top = min(1.9, smax)
        keys = [top, 1 + (top - 1) * 0.35, 0.93, 0.985, 1.0]
        return (keys[k] if k < len(keys) else 1.0), 1.0, 0
    if kind == "pop":
        return 0.55 + 0.45 * eob(k / 6, 1.5), min(1.0, (k + 1) / 3), 0
    if kind == "rise":
        return 1.0, min(1.0, (k + 1) / 4), 34 * (1 - eoc(k / 6))
    return 1.0, 1.0, 0


def draw_cues(img, cues, f):
    for cue, plates in cues:
        if not (cue["start"] <= f <= cue["end"]):
            continue
        for i, (p, bb) in enumerate(plates):
            k = f - cue["start"] - i * cue.get("stagger", 0)
            if k < 0:
                continue
            smax = min(1.32 if cue["anim"] != "punch" else 1.9, (E.W - 30) / (bb[2] - bb[0]))
            s, o, dy = anim_params(cue["anim"], k, smax)
            if cue.get("exit") == "shrink":
                j = f - (cue["end"] - 2)
                if j >= 0:
                    s *= 1 - 0.22 * (j + 1) / 3
                    o *= 1 - (j + 1) / 3.5
            paste(img, p, bb, s, o, dy=dy)


# ------------------------------------------------------ client logo -------
def client_logo_assets(logo_path):
    logo = Image.open(logo_path).convert("RGBA")
    d = E.CLIENT_LOGO["d"]
    logo = logo.resize((d, d), Image.LANCZOS)
    pad = 70
    plate = Image.new("RGBA", (d + 2 * pad, d + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    sh.putalpha(logo.getchannel("A").filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.65)))
    plate.alpha_composite(sh, (pad, pad + 12))
    plate.alpha_composite(logo, (pad, pad))
    full = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    full.alpha_composite(plate, (E.W // 2 - plate.width // 2, E.CLIENT_LOGO["y"] - plate.height // 2))
    # top gradient so the badge sits on darkness while the pita stays visible
    g = np.zeros((E.H, E.W), np.float32)
    ys = np.arange(E.H)[:, None]
    g[:] = np.clip(1 - ys / 980.0, 0, 1) ** 1.6 * 0.8
    grad = Image.new("RGBA", (E.W, E.H), (8, 4, 2, 0))
    grad.putalpha(Image.fromarray((g * 255).astype(np.uint8)))
    return full, full.getchannel("A").getbbox(), grad


def draw_client_logo(img, assets, f):
    st = E.CLIENT_LOGO["start"]
    if f < st:
        return
    full, bb, grad = assets
    k = f - st
    ga = min(1.0, (k + 1) / 5)
    if ga < 1:
        g = grad.copy()
        g.putalpha(g.getchannel("A").point(lambda v: int(v * ga)))
        img.alpha_composite(g)
    else:
        img.alpha_composite(grad)
    s = (0.72 + 0.28 * eob(k / 7, 1.3)) * (1 + 0.0007 * max(0, k - 7))
    paste(img, full, bb, s, min(1.0, (k + 1) / 3))


# ------------------------------------------------------ studio world ------
def studio_background():
    yy, xx = np.mgrid[0:E.H, 0:E.W].astype(np.float32)
    r = np.sqrt(((xx - E.W * 0.5) / E.W) ** 2 + ((yy - E.H * 0.42) / (E.H * 0.75)) ** 2)
    t = np.clip(r / 0.85, 0, 1)[..., None]
    c0 = np.array(E.PURPLE_2, np.float32)
    c1 = np.array(E.PURPLE, np.float32)
    arr = c0 * (1 - t) + c1 * t
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


def slant_band(d, x, width, color, slope=420):
    """diagonal band whose left edge sits at x on the top row."""
    d.polygon([(x, 0), (x + width, 0), (x + width - slope, E.H), (x - slope, E.H)], fill=color)


def studio_accents(img, f):
    """two thin brand stripes in the corners, drifting slowly."""
    d = ImageDraw.Draw(img)
    drift = (f % 400) * 0.6
    for i, col in enumerate((E.PINK, E.YELLOW)):
        x = E.W - 150 + i * 46 + drift
        d.polygon([(x, -10), (x + 22, -10), (x + 22 - 260, 260), (x - 260, 260)], fill=col + (255,))
        x2 = -40 + i * 46 - drift
        d.polygon([(x2 + 260, E.H - 260), (x2 + 282, E.H - 260), (x2 + 22, E.H + 10), (x2, E.H + 10)],
                  fill=col + (255,))


def wipe(img, k, n):
    """energetic right-to-left diagonal wipe: pink, yellow, then purple."""
    p = eoc((k + 1) / n)
    X = E.W + 440 - p * (E.W + 1300)
    over = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    slant_band(d, X, 190, E.PINK + (255,))
    slant_band(d, X + 190, 170, E.YELLOW + (255,))
    d.polygon([(X + 360, 0), (E.W + 600, 0), (E.W + 600, E.H), (X + 360 - 420, E.H)],
              fill=E.PURPLE + (255,))
    img.alpha_composite(over)


def message_icon(size=96):
    ss = 3
    s = size * ss
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([s * 0.04, s * 0.08, s * 0.96, s * 0.74], radius=s * 0.2, fill=(255, 255, 255, 255))
    d.polygon([(s * 0.22, s * 0.66), (s * 0.44, s * 0.70), (s * 0.16, s * 0.94)], fill=(255, 255, 255, 255))
    for i in range(3):
        cx = s * (0.30 + i * 0.20)
        d.ellipse([cx - s * 0.065, s * 0.41 - s * 0.065, cx + s * 0.065, s * 0.41 + s * 0.065], fill=E.PURPLE + (255,))
    return im.resize((size, size), Image.LANCZOS)


def studio_assets(fonts, studio_logo):
    logo = Image.open(studio_logo).convert("RGBA")
    w = E.STUDIO_LOGO["width"]
    logo = logo.resize((w, int(logo.height * w / logo.width)), Image.LANCZOS)
    full = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    sh = Image.new("RGBA", logo.size, (16, 0, 34, 0))
    sh.putalpha(logo.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.5)))
    x0, y0 = E.W // 2 - logo.width // 2, E.STUDIO_LOGO["y"] - logo.height // 2
    full.alpha_composite(sh, (x0, y0 + 9))
    full.alpha_composite(logo, (x0, y0))
    # handle (latin, LTR)
    hf = ImageFont.truetype(os.path.join(fonts, "Rubik-Black.ttf"), E.HANDLE["size"])
    hp = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    ImageDraw.Draw(hp).text((E.W / 2, E.HANDLE["y"]), E.HANDLE["text"], font=hf, fill=(255, 255, 255, 255),
                            anchor="mm")
    hp = add_shadow(hp, "graphic")
    return dict(logo=(full, full.getchannel("A").getbbox()), bg=studio_background(),
                handle=(hp, hp.getchannel("A").getbbox()), icon=message_icon(100))


def draw_end_card(img, A, f, cue_map):
    st = E.STUDIO_LOGO["start"]
    if f >= st:
        k = f - st
        s = 0.62 + 0.38 * eob(k / 9, 1.35)
        paste(img, *A["logo"], s, min(1.0, (k + 1) / 3), dy=40 * (1 - eoc(k / 9)))
    if f >= E.HANDLE["start"]:
        k = f - E.HANDLE["start"]
        paste(img, *A["handle"], 1.0, min(1.0, (k + 1) / 4), dy=30 * (1 - eoc(k / 6)))
    ci = E.CTA_ICON
    if f >= ci["start"]:
        # icon sits left of the CTA text (end of the RTL line), wiggles twice
        cta_bb = cue_map["cta"][0][1]
        k = f - ci["start"]
        s = 0.55 + 0.45 * eob(k / 6, 1.5)
        ang, bounce = 0.0, 0.0
        for wv in ci["wiggles"]:
            j = f - wv
            if 0 <= j <= 12:
                ang += 16 * math.sin(2 * math.pi * j / 6) * math.exp(-j / 5)
                bounce += -14 * abs(math.sin(math.pi * j / 6)) * math.exp(-j / 4)
        icon = A["icon"]
        tmp = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
        cx = cta_bb[0] - 30 - icon.width / 2
        cy = (cta_bb[1] + cta_bb[3]) / 2 - 4
        tmp.alpha_composite(icon, (int(cx - icon.width / 2), int(cy - icon.height / 2)))
        bb = (int(cx - icon.width / 2), int(cy - icon.height / 2), int(cx + icon.width / 2), int(cy + icon.height / 2))
        paste(img, tmp, bb, s, min(1.0, (k + 1) / 3), dy=bounce, angle=ang)


def dim(arr, k):
    """freeze treatment: quick dim + partial desaturation."""
    a = min(1.0, (k + 1) / 2)
    x = arr.astype(np.float32)
    grey = x.mean(axis=2, keepdims=True)
    x = x * (1 - 0.55 * a) + grey * 0.55 * a
    x *= 1 - 0.5 * a
    return Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).convert("RGBA")


def shake(img, k):
    offs = [(16, -12), (-12, 9), (7, -6), (-3, 3)]
    if k >= len(offs):
        return img
    dx, dy = offs[k]
    big = img.resize((int(E.W * 1.03), int(E.H * 1.03)), Image.BILINEAR)
    x0 = (big.width - E.W) // 2 + dx
    y0 = (big.height - E.H) // 2 + dy
    return big.crop((x0, y0, x0 + E.W, y0 + E.H))


# ---------------------------------------------------------------- main ----
def render(version, sources, fonts, logo, studio_logo, out, preview=None):
    V = E.VERSIONS[version]
    n_total = V["frames"]
    cues = [(c, cue_plates(c, fonts)) for c in E.AD_TEXT]
    tw_cues = [(c, cue_plates(c, fonts)) for c in E.TWIST_TEXT] if V["twist"] else []
    cue_map = {c["id"]: p for c, p in cues + tw_cues}
    cl_assets = client_logo_assets(logo)
    st_assets = studio_assets(fonts, studio_logo) if V["twist"] else None

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}",
         "-r", str(E.FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-tune", "film",
         "-g", "24", "-bf", "2", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-color_range", "tv", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    thumbs = []

    def emit(img, f):
        rgb = img.convert("RGB")
        enc.stdin.write(rgb.tobytes())
        if preview and f % 6 == 0:
            thumbs.append((f, rgb.resize((180, 320))))

    f = 0
    last = None
    for seg in E.AD:
        frames = decode(os.path.join(sources, E.SRC[seg["src"]]), seg)
        for fr in frames:
            img = Image.fromarray(fr).convert("RGBA")
            draw_client_logo(img, cl_assets, f)
            draw_cues(img, cues, f)
            last = img
            emit(img, f)
            f += 1
    assert f == E.TWIST_START

    if V["twist"]:
        frozen = np.asarray(last.convert("RGB"))
        w0, w1 = E.TWIST["wipe"]
        while f < n_total:
            if f <= E.TWIST["freeze_end"]:
                img = dim(frozen, f - E.TWIST_START)
                draw_cues(img, tw_cues, f)
                if f >= 246:
                    img = shake(img, f - 246)
                if w0 <= f <= w1 - 1:
                    wipe(img, f - w0, w1 - w0)
            else:
                img = st_assets["bg"].copy()
                studio_accents(img, f)
                draw_cues(img, tw_cues, f)
                draw_end_card(img, st_assets, f, cue_map)
            emit(img, f)
            f += 1

    enc.stdin.close()
    assert enc.wait() == 0
    print(f"{out}: {f} frames ({f / E.FPS:.3f}s)")
    if preview:
        cols = 12
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * 180, rows * 340))
        dd = ImageDraw.Draw(sheet)
        for i, (fn, t) in enumerate(thumbs):
            x, y = (i % cols) * 180, (i // cols) * 340
            sheet.paste(t, (x, y))
            dd.text((x + 4, y + 322), f"{fn} ({fn / E.FPS:.2f}s)", fill=(255, 255, 0))
        sheet.save(preview, quality=88)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", choices=list(E.VERSIONS), required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--logo", required=True)
    ap.add_argument("--studio-logo", default=os.path.join(os.path.dirname(__file__), "..", "assets",
                                                          "ainati_logo_official.png"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview")
    a = ap.parse_args()
    render(a.version, a.sources, a.fonts, a.logo, a.studio_logo, a.out, a.preview)
