# -*- coding: utf-8 -*-
"""Render engine for "משלוחים לכל חלקי הארץ*".

  python3 scripts/render.py [edit_module] [output.mp4]

Defaults: edit/edit_v1.py -> renders/draft_v1.mp4
Pipeline: per-segment video (1080x1920, 30 fps, no stretch) -> concat ->
logo + ASS captions -> original music/SFX mix -> loudness to -14 LUFS with a
true-peak ceiling -> H.264 High / AAC 320k MP4.

If source/audio/narration.wav exists together with edit/narration_words.json
(word-level timings from a real transcription), the narration is mixed in,
the music is ducked under it and the captions use the real word times.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
from scipy import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD = os.path.join(ROOT, "build")
SR = 48000


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(" ".join(cmd))
        print(r.stderr[-3000:])
        raise SystemExit(1)
    return r


def load_edit(path):
    spec = importlib.util.spec_from_file_location("edit", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probe_size(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "csv=p=0:s=x", path])
    w, h = r.stdout.strip().split("x")
    return int(w), int(h)


# ======================================================================= timeline
def build_timeline(E):
    t = 0
    segs = []
    for s in E.SEGMENTS:
        dur = (s["tout"] - s["tin"]) if s["kind"] == "clip" else s["dur"]
        nfr = int(round(dur * E.FPS))
        seg = dict(s)
        seg["frames"] = nfr
        seg["start_f"] = t
        seg["start"] = t / E.FPS
        seg["dur"] = nfr / E.FPS
        segs.append(seg)
        t += nfr
    total = t / E.FPS
    by_id = {s["id"]: s for s in segs}
    return segs, by_id, total


def at(by_id, seg, off):
    return by_id[seg]["start"] + off


# ======================================================================= video
def render_clip(E, seg, out):
    src = os.path.join(ROOT, seg["src"])
    sw, sh = probe_size(src)
    zoom = seg.get("zoom", 1.0)
    s0 = max(E.W / sw, E.H / sh) * zoom
    nw, nh = int(round(sw * s0 / 2) * 2), int(round(sh * s0 / 2) * 2)
    cx, cy = seg.get("cx", 0.5), seg.get("cy", 0.5)
    x = int(np.clip(cx * nw - E.W / 2, 0, nw - E.W))
    y = int(np.clip(cy * nh - E.H / 2, 0, nh - E.H))
    sharpen = ",unsharp=5:5:0.6:5:5:0.0" if s0 > 1.7 else ""
    vf = (f"trim=start={seg['tin']}:end={seg['tout'] + 0.2},setpts=PTS-STARTPTS,fps={E.FPS},"
          f"scale={nw}:{nh}:flags=lanczos,crop={E.W}:{E.H}:{x}:{y}{sharpen},setsar=1,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-vf", vf, "-frames:v", str(seg["frames"]),
         "-c:v", "libx264", "-preset", "fast", "-crf", "10", "-r", str(E.FPS), "-an", out])
    seg["scale"] = round(s0, 3)


def INTERMEDIATE_Q(E):
    """Quality of the per-segment intermediates: lossless when the edit asks for it."""
    return ["-qp", "0"] if getattr(E, "LOSSLESS_INTERMEDIATES", False) else ["-crf", "8"]


def _ease(p, kind):
    p = float(np.clip(p, 0, 1))
    if kind == "out":          # fast start, soft landing (crash zoom)
        return 1 - (1 - p) ** 3
    if kind == "in":
        return p ** 3
    if kind == "linear":
        return p
    return p * p * (3 - 2 * p)  # inout


def _billboard_patch(img, spec):
    """Hide text printed in a static part of the frame (e.g. a billboard line) by
    inpainting it from its surroundings. spec: rect (x0,y0,x1,y1) in source px and
    the colour rule of the pixels to remove ("dark_on_yellow")."""
    x0, y0, x1, y1 = spec["rect"]
    blk = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(blk, cv2.COLOR_RGB2HSV)
    yellow = (hsv[..., 0] > 12) & (hsv[..., 0] < 40) & (hsv[..., 1] > 110) & (hsv[..., 2] > 140)
    region = cv2.morphologyEx(yellow.astype(np.uint8), cv2.MORPH_CLOSE,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    text = ((region > 0) & ~yellow).astype(np.uint8)
    if "keep_below" in spec:  # keep only letters that reach below this source y (drops the line above)
        nlab, lab, stats, _ = cv2.connectedComponentsWithStats(text, 8)
        keep = np.zeros_like(text)
        for k in range(1, nlab):
            bottom = y0 + stats[k, cv2.CC_STAT_TOP] + stats[k, cv2.CC_STAT_HEIGHT] - 1
            if bottom > spec["keep_below"]:
                keep[lab == k] = 1
        text = keep
    text = cv2.dilate(text, np.ones((5, 5), np.uint8))
    full = np.zeros(img.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = text
    fixed = cv2.inpaint(img, full, 7, cv2.INPAINT_TELEA)
    m = cv2.GaussianBlur(full.astype(np.float32), (0, 0), 1.0)[..., None]
    return (img * (1 - m) + fixed * m).astype(np.uint8), full


def render_clip_py(E, seg, out):
    """Frame-accurate clip render with sub-pixel animated zoom/pan (no stretching:
    one uniform scale), optional static patch, light sharpening on big upscales."""
    src = os.path.join(ROOT, seg["src"])
    sw, sh = probe_size(src)
    n = seg["frames"]
    dur = seg["dur"]
    base = max(E.W / sw, E.H / sh)
    z0 = seg.get("zoom", 1.0)
    z1 = seg.get("zoom_to", z0)
    cx0, cy0 = seg.get("cx", 0.5), seg.get("cy", 0.5)
    cx1, cy1 = seg.get("cx_to", cx0), seg.get("cy_to", cy0)
    t0, t1 = seg.get("zoom_t0", 0.0), seg.get("zoom_t1", dur)
    ease = seg.get("ease", "inout")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-map", "0:v:0", "-vf",
                            f"trim=start={seg['tin']}:end={seg['tout'] + 0.25},setpts=PTS-STARTPTS,fps={E.FPS}",
                            "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{E.W}x{E.H}", "-r", str(E.FPS), "-i", "-", "-vf", "format=yuv420p",
                            "-c:v", "libx264", "-preset", "fast", *INTERMEDIATE_Q(E), out], stdin=subprocess.PIPE)
    patch = seg.get("patch")
    last = None
    smax = 0
    for i in range(n):
        buf = dec.stdout.read(sw * sh * 3)
        if len(buf) == sw * sh * 3:
            last = np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
        img = last
        if patch:
            img, _ = _billboard_patch(img.copy(), patch)
        t = i / E.FPS
        p = _ease((t - t0) / max(t1 - t0, 1e-3), ease)
        z = z0 + (z1 - z0) * p
        cx = cx0 + (cx1 - cx0) * p
        cy = cy0 + (cy1 - cy0) * p
        s = base * z
        smax = max(smax, s)
        ww, wh = E.W / s, E.H / s
        cxp = float(np.clip(cx * sw, ww / 2, sw - ww / 2))
        cyp = float(np.clip(cy * sh, wh / 2, sh - wh / 2))
        M = np.float32([[s, 0, E.W / 2 - s * cxp], [0, s, E.H / 2 - s * cyp]])
        fr = cv2.warpAffine(img, M, (E.W, E.H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
        if s > 1.7:
            bl = cv2.GaussianBlur(fr, (0, 0), 1.1)
            fr = cv2.addWeighted(fr, 1.5, bl, -0.5, 0)
        enc.stdin.write(fr.tobytes())
    dec.stdout.read()
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    seg["scale"] = round(smax, 3)


def slate_bg(E, seg, path):
    w, h = E.W, E.H
    yy = np.linspace(0, 1, h)[:, None]
    top = np.array([16, 26, 52], float)
    bot = np.array([6, 10, 24], float)
    img = top * (1 - yy[..., None]) + bot * yy[..., None]
    img = np.broadcast_to(img, (h, w, 3)).copy()
    # faint diagonal hatch = "placeholder"
    X, Yg = np.meshgrid(np.arange(w), np.arange(h))
    hatch = ((X + Yg) // 28) % 2 == 0
    img[hatch] += 4
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # dashed frame
    m, dash, gap = 70, 26, 16
    col = (90, 110, 160)
    for x0 in range(m, w - m, dash + gap):
        d.line([(x0, m), (min(x0 + dash, w - m), m)], fill=col, width=3)
        d.line([(x0, h - m), (min(x0 + dash, w - m), h - m)], fill=col, width=3)
    for y0 in range(m, h - m, dash + gap):
        d.line([(m, y0), (m, min(y0 + dash, h - m))], fill=col, width=3)
        d.line([(w - m, y0), (w - m, min(y0 + dash, h - m))], fill=col, width=3)
    im.save(path)


def render_slate(E, seg, out):
    png = out.replace(".mp4", ".png")
    slate_bg(E, seg, png)
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", png, "-frames:v", str(seg["frames"]),
         "-r", str(E.FPS), "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "10",
         "-tune", "stillimage", out])


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def render_endcard(E, seg, out):
    d = os.path.join(ROOT, "assets", "endcard")
    final = np.asarray(Image.open(os.path.join(d, "endcard_final.png")).convert("RGB")).astype(np.float32)
    clean = np.asarray(Image.open(os.path.join(d, "endcard_clean.png")).convert("RGB")).astype(np.float32)
    masks = {n: np.asarray(Image.open(os.path.join(d, f"mask_{n}.png"))).astype(np.float32)[..., None] / 255
             for n, *_ in E.ENDCARD_REVEAL}
    xs = np.arange(E.W, dtype=np.float32)[None, :, None]
    # background for the safe-area layout: the card's own tones, heavily blurred
    safe_bg = cv2.GaussianBlur(clean, (0, 0), 70) * 0.92
    edge_mask = np.zeros((E.H, E.W), np.float32)
    edge_mask[40:-40, 40:-40] = 1
    edge_mask = cv2.GaussianBlur(edge_mask, (0, 0), 22)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{E.W}x{E.H}", "-r", str(E.FPS), "-i", "-", "-vf", "format=yuv420p",
                          "-c:v", "libx264", "-preset", "fast", "-crf", "10", out], stdin=subprocess.PIPE)
    n = seg["frames"]
    for i in range(n):
        t = i / E.FPS
        A = np.zeros((E.H, E.W, 1), np.float32)
        for name, start, dur, mode in E.ENDCARD_REVEAL:
            if mode == "wipe_rtl":
                prog = smoothstep((t - start) / max(dur, 1e-3))
                edge = E.W + 60 - prog * (E.W + 120)
                a = np.clip((xs - edge) / 60 + 0.5, 0, 1) if t >= start else np.zeros_like(xs)
            else:
                a = np.float32(1.0 if dur == 0 and t >= start else smoothstep((t - start) / max(dur, 1e-3)))
            A = np.maximum(A, masks[name] * a)
        frame = clean * (1 - A) + final * A
        z = 1 + E.ENDCARD_PUSH * (t / seg["dur"])
        sfe = getattr(E, "ENDCARD_SAFE", None)
        if sfe:
            s = sfe["scale"] * z
            c_src = (sfe["content_top"] + sfe["content_bottom"]) / 2
            c_dst = (sfe["target_top"] + sfe["target_bottom"]) / 2
            M = np.float32([[s, 0, E.W / 2 - s * E.W / 2], [0, s, c_dst - s * c_src]])
            card = cv2.warpAffine(frame, M, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
            m = cv2.warpAffine(edge_mask, M, (E.W, E.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]
            frame = card * m + safe_bg * (1 - m)
        else:
            M = cv2.getRotationMatrix2D((E.W / 2, E.H * 0.45), 0, z)
            frame = cv2.warpAffine(frame, M, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()


def render_endcard_v4(E, seg, out):
    """Two short clean cards: the yellow-brush fine print, then logo + tagline."""
    d = os.path.join(ROOT, "assets", "endcard")
    C = E.ENDCARD_V4
    bg = np.asarray(Image.open(os.path.join(d, "v4_bg.png")).convert("RGB")).astype(np.float32)
    if bg.shape[0] != E.H:  # other aspect ratios: take a band of the 9:16 background
        y0 = int(C.get("bg_y0", (bg.shape[0] - E.H) // 2))
        bg = np.ascontiguousarray(bg[y0:y0 + E.H, :E.W])

    def rgba(path, width=None):
        im = Image.open(path).convert("RGBA")
        if width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        return a[..., :3], a[..., 3:4] / 255.0

    brush, brush_a = rgba(os.path.join(d, "v4_brush.png"), C["brush_width"])
    logo, logo_a = rgba(os.path.join(ROOT, "source", "images", "ainati_logo_original.webp"), C["logo_width"])
    tag, tag_a = rgba(os.path.join(d, C.get("tagline_file", "v4_tagline.png")))
    # soft gold glow behind the logo
    glow = np.zeros((E.H, E.W), np.float32)
    lx, ly = (E.W - logo.shape[1]) // 2, C["logo_y"] - logo.shape[0] // 2
    glow[ly:ly + logo.shape[0], lx:lx + logo.shape[1]] = logo_a[..., 0]
    glow = cv2.GaussianBlur(glow, (0, 0), 26)
    glow = (glow / (glow.max() + 1e-6))[..., None]
    gold = np.array([255, 186, 80], np.float32)

    def over(canvas, rgb, a, x, y, alpha=1.0, scale=1.0):
        if scale != 1.0:
            h, w = rgb.shape[:2]
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_CUBIC)
            a = cv2.resize(a[..., 0], (nw, nh), interpolation=cv2.INTER_CUBIC)[..., None]
            x += (w - nw) // 2
            y += (h - nh) // 2
        h, w = rgb.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(E.W, x + w), min(E.H, y + h)
        sub = canvas[y0:y1, x0:x1]
        aa = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
        canvas[y0:y1, x0:x1] = sub * (1 - aa) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * aa
        return canvas

    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{E.W}x{E.H}", "-r", str(E.FPS), "-i", "-", "-vf", "format=yuv420p",
                            "-c:v", "libx264", "-preset", "fast", *INTERMEDIATE_Q(E), out], stdin=subprocess.PIPE)
    split, xf = C["card1_dur"], C["crossfade"]
    bx = (E.W - brush.shape[1]) // 2
    by = C["brush_y"] - brush.shape[0] // 2
    xs = np.arange(brush.shape[1], dtype=np.float32)[None, :, None]
    for i in range(seg["frames"]):
        t = i / E.FPS
        # card 1: brush painted in right-to-left, slow settle
        c1 = bg.copy()
        prog = smoothstep(t / C["wipe"])
        edge = brush.shape[1] * (1 - prog) - 40
        wipe = np.clip((xs - edge) / 40, 0, 1)
        c1 = over(c1, brush, brush_a * wipe, bx, by, scale=1.0 + 0.03 * min(t / split, 1))
        # card 2: logo, then tagline
        t2 = t - split
        c2 = bg.copy()
        if t2 > -xf:
            la = smoothstep((t2 + xf) / 0.35)
            c2 = c2 * (1 - 0.18 * glow * la) + gold * (0.18 * glow * la)
            c2 = over(c2, logo, logo_a, lx, ly, alpha=la, scale=0.96 + 0.04 * smoothstep((t2 + xf) / 0.6))
            ta = smoothstep((t2 - C["tagline_delay"]) / 0.35)
            c2 = over(c2, tag, tag_a, 0, C["tagline_y"] - tag.shape[0] // 2, alpha=ta)
        k = smoothstep((t - split + xf) / xf) if xf > 0 else float(t >= split)
        if t2 > -xf:  # slow 2% push on the logo card so it never sits frozen
            z2 = 1 + 0.02 * max(0.0, t2) / max(seg["dur"] - split, 1e-3)
            M2 = cv2.getRotationMatrix2D((E.W / 2, C["logo_y"]), 0, z2)
            c2 = cv2.warpAffine(c2, M2, (E.W, E.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        frame = c1 * (1 - k) + c2 * k
        enc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


def make_logo_png(E, path):
    logo = Image.open(os.path.join(ROOT, "source", "images", "ainati_logo_original.webp")).convert("RGBA")
    w = E.LOGO["width"]
    h = round(logo.height * w / logo.width)
    logo = logo.resize((w, h), Image.LANCZOS)
    pad = 12
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = logo.split()[3]
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_alpha = Image.new("L", canvas.size, 0)
    shadow_alpha.paste(a, (pad + 2, pad + 3))
    shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.55))
    sh.putalpha(shadow_alpha)
    canvas = Image.alpha_composite(canvas, sh)
    canvas.alpha_composite(logo, (pad, pad))
    op = E.LOGO["opacity"]
    alpha = canvas.split()[3].point(lambda v: int(v * op))
    canvas.putalpha(alpha)
    canvas.save(path)
    return pad


# ======================================================================= captions
def ass_time(t):
    t = max(0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


COL = {"yellow": "&H0000D4FF&", "red": "&H00303BFF&", "white": "&H00FFFFFF&"}


def tokenize(text):
    toks = []
    for part in text.replace("\\N", " \\N ").split(" "):
        if part:
            toks.append(part)
    return toks


def word_weight(w):
    letters = len(re.sub(r"[^֐-׿A-Za-z0-9]", "", w))
    pause = 0.0
    if w.endswith("..."):
        pause = 0.35
    elif w.endswith(","):
        pause = 0.12
    elif w[-1:] in "!?.":
        pause = 0.05
    return 0.06 + 0.068 * letters, pause


def estimate_words(text, start):
    """Draft-only: estimated word onsets for a VO line (no narration available)."""
    times = []
    t = start
    for tok in tokenize(text):
        if tok == "\\N":
            continue
        d, pause = word_weight(tok)
        times.append((tok, t, t + d))
        t += d + pause
    return times, t


def build_captions(E, by_id, total, words_override=None):
    lines = []
    for i, (seg, off, text, hl, opt) in enumerate(E.VO):
        start = at(by_id, seg, off)
        words, end = estimate_words(text, start)
        lines.append(dict(idx=i, text=text, hl=hl, opt=opt, start=start, end=end, words=words))
    if words_override:  # real word times (narration seconds) re-anchored to each line's placement
        for ln, real in zip(lines, words_override["lines"]):
            t0 = real[0]["start"]
            anchor = ln["start"]
            # captions lead the voice by 2 frames so each word is readable as it is spoken
            ln["words"] = [(w["w"], anchor + w["start"] - t0 - 0.066, anchor + w["end"] - t0) for w in real]
            ln["end"] = anchor + real[-1]["end"] - t0
    events = []
    cfg = getattr(E, "CAPTIONS", None)
    cols = cfg["colors"] if cfg else COL
    shown = [l for l in lines if l["opt"].get("caption", True)]
    for k, ln in enumerate(shown):
        nxt = shown[k + 1]["start"] if k + 1 < len(shown) else total
        cap_end = min(nxt - 0.04, ln["end"] + 0.55)
        cap_end = max(cap_end, ln["start"] + 0.7)
        opt = ln["opt"]
        if opt.get("big"):
            style = "Big"
        elif opt.get("punch") and cfg:
            style = "Punch"
        else:
            style = "Cap"
        default = (cfg["punch_color"] if style == "Punch" else "white") if cfg else "white"
        mv = opt.get("marginv", 0)
        toks = tokenize(ln["text"])
        onsets = [w[1] for w in ln["words"]]
        for step in range(len(onsets)):
            s = onsets[step]
            e = onsets[step + 1] if step + 1 < len(onsets) else cap_end
            if e - s < 0.01:
                continue
            parts = []
            wi = 0
            for tok in toks:
                if tok == "\\N":
                    parts.append("\\N")
                    continue
                colour = cols.get(ln["hl"].get(tok, default), cols["white"])
                if wi > step:
                    tag = "{\\alpha&HFF&}"
                elif wi == step and cfg and cfg.get("fade_in"):
                    tag = "{\\alpha&HFF&\\t(0,%d,\\alpha&H00&)}" % cfg["fade_in"]
                else:
                    tag = "{\\alpha&H00&}"
                parts.append(f"{tag}{{\\c{colour}}}{tok}")
                wi += 1
            txt = " ".join(parts).replace(" \\N ", "\\N")
            if style in ("Big", "Punch") and step == 0:
                txt = "{\\fscx76\\fscy76\\t(0,130,\\fscx100\\fscy100)}" + txt
            if opt.get("top"):  # caption anchored to the top (MarginV = distance from the top)
                txt = "{\\an8}" + txt
            events.append((s, e, style, txt, mv))
    return events, lines


def write_ass(E, segs, events, path, draft=True):
    cfg = getattr(E, "CAPTIONS", None)
    if cfg:
        o, sh = cfg["outline_color"], cfg["shadow_color"]
        cap_styles = (
            f"Style: Cap,{cfg['font']},{cfg['size']},&H00FFFFFF,&H00FFFFFF,{o},{sh},0,0,0,0,100,100,0,0,1,{cfg['outline']},{cfg['shadow']},2,{cfg['margin_l']},{cfg['margin_r']},{cfg['margin_v']},-1\n"
            f"Style: Punch,{cfg['font']},{cfg['punch_size']},&H00FFFFFF,&H00FFFFFF,{o},{sh},0,0,0,0,100,100,0,0,1,{cfg['outline'] + 1},{cfg['shadow']},2,{cfg['margin_l']},{cfg['margin_r']},{cfg['margin_v']},-1\n"
            f"Style: Big,{cfg['font']},{cfg['big_size']},&H00FFFFFF,&H00FFFFFF,{o},{sh},0,0,0,0,100,100,0,0,1,{cfg['outline'] + 2},{cfg['shadow'] + 1},2,{cfg['margin_l']},{cfg['margin_r']},{cfg['margin_v']},-1\n")
    else:
        cap_styles = ("Style: Cap,Heebo Black,76,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,6,3,2,110,170,520,-1\n"
                      "Style: Big,Heebo Black,118,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,8,4,2,110,170,520,-1\n")
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {E.W}
PlayResY: {E.H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{cap_styles}Style: SlateTitle,Heebo Bold,56,&H00F0F0F0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,-1
Style: SlateDesc,Heebo Medium,42,&H00C8B4A0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,-1
Style: Draft,Heebo Bold,28,&H00FFFFFF,&H00FFFFFF,&H7A000000,&H7A000000,0,0,0,0,100,100,0,0,3,10,0,7,40,40,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = []
    for s, e, style, txt, mv in events:
        rows.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},{style},,0,0,{mv},,{txt}")
    for sg in segs:
        if sg["kind"] == "slate":
            s, e = sg["start"], sg["start"] + sg["dur"]
            rows.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},SlateTitle,,0,0,0,,{{\\pos(540,700)}}{sg['title']}")
            desc = sg["desc"].replace("\n", "\\N")
            rows.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},SlateDesc,,0,0,0,,{{\\pos(540,840)}}{desc}")
    if draft and E.DRAFT_LABEL:
        total = segs[-1]["start"] + segs[-1]["dur"]
        t_draft_end = next((sg["start"] for sg in segs if sg["kind"] in ("endcard", "endcard_v4")), total)
        rows.append(f"Dialogue: 2,{ass_time(0)},{ass_time(t_draft_end)},Draft,,0,0,0,,{{\\an7\\pos(44,140)}}{E.DRAFT_LABEL}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(hdr + "\n".join(rows) + "\n")


# ======================================================================= audio
def load_wav(path):
    x, sr = sf.read(path, always_2d=True)
    assert sr == SR, path
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def db(g):
    return 10 ** (g / 20)


def mix_audio(E, by_id, total, narration=None, vo_spans=None, words=None):
    n = int(round((total + 0.5) * SR))
    music = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    cache = {}

    def get(kind, name):
        key = (kind, name)
        if key not in cache:
            cache[key] = load_wav(os.path.join(ROOT, "assets", kind, name + ".wav"))
        return cache[key]

    def put(buf, x, t0, gain, fin=0.0, fout=0.0):
        x = x.copy()
        if fin > 0:
            k = min(len(x), int(fin * SR))
            x[:k] *= np.linspace(0, 1, k)[:, None]
        if fout > 0:
            k = min(len(x), int(fout * SR))
            x[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
        i0 = int(round(t0 * SR))
        i1 = min(n, i0 + len(x))
        buf[i0:i1] += x[: i1 - i0] * gain

    for ev in E.MUSIC:
        seg, off, cue, cfrom, stop, gdb, fin, fout = ev[:8]
        mopt = ev[8] if len(ev) > 8 else {}
        t0 = at(by_id, seg, off)
        full = get("music", cue)[int(cfrom * SR):]
        x = full
        if stop:
            t1 = at(by_id, *stop)
            L = int((t1 - t0) * SR)
            ts = mopt.get("tapestop", 0.0)
            if ts > 0:  # the music "runs down": playback speed falls from 1 to 0
                T = int(ts * SR)
                head = full[: L - T]
                tt = np.arange(T) / SR
                pos = (L - T) + (tt - tt ** 2 / (2 * ts)) * SR
                idx = np.arange(len(full))
                tail = np.stack([np.interp(pos, idx, full[:, c]) for c in range(2)], axis=1)
                tail *= np.linspace(1, 0.6, T)[:, None]
                x = np.concatenate([head, tail])
            else:
                x = full[:L]
        x = x.copy()
        if "ramp" in mopt:  # gain build: (db_start, db_end, seconds)
            a, b, rd = mopt["ramp"]
            k = min(len(x), int(rd * SR))
            env = np.full(len(x), db(b))
            env[:k] = db(np.linspace(a, b, k))
            x *= env[:, None]
        put(music, x, t0, db(gdb), fin, fout)

    sfx_duck = np.zeros((n, 2))
    for ev in E.SFX:
        seg, off, name, gdb, frm, dur = ev[:6]
        sopt = ev[6] if len(ev) > 6 else {}
        t0 = at(by_id, seg, off)
        if name.startswith("@clip:"):
            x = clip_audio(name[6:], sopt)
        else:
            x = get("sfx", name)
        x = x[int(frm * SR):]
        if dur:
            x = x[: int(dur * SR)]
            fo = min(0.4, dur / 3) if not name.startswith("@clip:") else 0.03
        else:
            fo = 0.01
        put(sfx_duck if sopt.get("duck") else sfx, x, t0, db(gdb), 0.01 if name.startswith("room") else 0.0, fo)

    # ducking: music dips under the voice (real narration envelope, or the
    # estimated VO spans in draft mode so SFX/music balance matches the final)
    if narration is not None:
        vo = np.zeros((n, 2))
        prev_end = -1.0
        for i, (seg, off, _t, _h, opt) in enumerate(E.VO):
            c0, c1 = words["chunks"][i]
            w0 = words["lines"][i][0]["start"]
            t_place = at(by_id, seg, off) - (w0 - c0)
            speech_start = at(by_id, seg, off)
            if speech_start < prev_end + 0.05:
                print(f"  WARNING: VO line {i} starts {prev_end - speech_start:+.2f}s into the previous line's speech")
            chunk = narration[int(c0 * SR):int(c1 * SR)].copy() * db(opt.get("gain_db", 0.0))
            k = int(0.008 * SR)
            chunk[:k] *= np.linspace(0, 1, k)[:, None]
            chunk[-k:] *= np.linspace(1, 0, k)[:, None]
            i0 = int(round(t_place * SR))
            vo[i0:i0 + len(chunk)] += chunk[: max(0, n - i0)]
            prev_end = speech_start + words["lines"][i][-1]["end"] - w0
        env = np.abs(signal.hilbert(vo.mean(1)))
        env = signal.sosfilt(signal.butter(2, 8, fs=SR, output="sos"), env)
        talk = (env > db(-38)).astype(float)
        for a, b in (vo_spans or []):  # extra dips (e.g. key SFX with no voice)
            talk[int(a * SR):int(b * SR)] = 1.0
    else:
        vo = np.zeros((n, 2))
        talk = np.zeros(n)
        for a, b in (vo_spans or []):
            talk[int(a * SR):int(b * SR)] = 1.0
    g = smooth_gate(talk, 0.03, 0.18)
    gain = db(DUCK_DB) ** g  # fixed dip under the voice
    if narration is not None:
        # dynamic part: keep the music at least VO_OVER_MUSIC_DB under the voice's short-term level
        rate = 100
        step = SR // rate
        nfr = n // step

        def env(x):
            p = (x.mean(1)[: nfr * step] ** 2).reshape(nfr, step).mean(1)
            k = 15  # 150 ms window
            p = np.convolve(p, np.ones(k) / k, mode="same")
            return np.sqrt(p + 1e-12)

        ve, me = env(vo), env(music * db(MUSIC_BUS_DB))
        ratio = np.full(nfr, VO_OVER_MUSIC_DB)
        for sg_, of_, du_, r_ in getattr(E, "DUCK_OVERRIDES", []):
            a_ = int(at(by_id, sg_, of_) * rate)
            ratio[a_:a_ + int(du_ * rate)] = r_
        req = np.clip(ve * db(-ratio) / me, 0.02, 1.0)
        req[ve < db(-50)] = 1.0
        # attack 30 ms / release 180 ms on the required gain
        out = np.empty_like(req)
        st = 1.0
        a_att, a_rel = np.exp(-1 / (0.03 * rate)), np.exp(-1 / (0.18 * rate))
        for i, v in enumerate(req):
            c = a_att if v < st else a_rel
            st = c * st + (1 - c) * v
            out[i] = st
        dyn = np.interp(np.arange(n) / step, np.arange(nfr), out)
        gain = np.minimum(gain, dyn)
    music *= gain[:, None]
    sfx += sfx_duck * gain[:, None]
    STEMS.update(vo=vo, music=music * db(MUSIC_BUS_DB), sfx=sfx * db(-3))
    return vo + music * db(MUSIC_BUS_DB) + sfx * db(-3)


STEMS = {}
DUCK_DB = -16.0  # music under the voice
MUSIC_BUS_DB = -7.0
VO_OVER_MUSIC_DB = 13.0


def clip_audio(rel_path, opt):
    """Original clip sound (e.g. effort sounds, foley) kept only where it has events:
    voice-band gate, band-limited. Background bed and music are dropped."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(ROOT, rel_path), "-vn", "-ac", "2",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    lo, hi = opt.get("band", (120, 9000))
    x = signal.sosfilt(signal.butter(4, [lo, hi], btype="band", fs=SR, output="sos"), x, axis=0)
    v = signal.sosfilt(signal.butter(4, [300, 3000], btype="band", fs=SR, output="sos"), x.mean(1))
    hop = int(0.01 * SR)
    nf = len(v) // hop
    e = 20 * np.log10(np.sqrt((v[: nf * hop] ** 2).reshape(nf, hop).mean(1)) + 1e-9)
    gate = (e > opt.get("gate_db", -26)).astype(float)
    gate = np.convolve(gate, np.ones(13), mode="same") > 0  # hold +-60 ms
    g = np.convolve(gate.astype(float), np.ones(3) / 3, mode="same")
    g = np.interp(np.arange(len(x)) / hop, np.arange(nf), g)
    return x * g[:, None]


def smooth_gate(target, att, rel, rate=1000):
    """Attack/release smoothing of a 0..1 gate, computed at a 1 kHz control rate."""
    step = SR // rate
    t = target[::step]
    a_att, a_rel = np.exp(-1 / (att * rate)), np.exp(-1 / (rel * rate))
    out = np.empty_like(t)
    st = 0.0
    for i, v in enumerate(t):
        c = a_att if v > st else a_rel
        st = c * st + (1 - c) * v
        out[i] = st
    return np.interp(np.arange(len(target)) / step, np.arange(len(out)), out)


def true_peak_limit(x, ceiling_db=-1.5, look_ms=5.0, release_ms=80.0):
    ceiling = db(ceiling_db)
    up = signal.resample_poly(x, 4, 1, axis=0)
    pk = np.abs(up).max(axis=1).reshape(-1, 4).max(axis=1)[: len(x)]
    pk = np.pad(pk, (0, len(x) - len(pk)), constant_values=0)
    need = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    la = int(look_ms / 1000 * SR)
    # lookahead: min over the upcoming window
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, size=2 * la + 1, origin=0)
    rel = np.exp(-1 / (release_ms / 1000 * SR))
    g = np.empty_like(need)
    s = 1.0
    for i in range(len(need)):
        s = need[i] if need[i] < s else rel * s + (1 - rel) * need[i]
        g[i] = s
    return x * g[:, None]


def measure_tp(x):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.abs(up).max() + 1e-12)


def master(mix, target=-14.0, ceiling=-2.0):
    meter = pyln.Meter(SR)
    for _ in range(4):
        L = meter.integrated_loudness(mix)
        mix = mix * db(target - L)
        mix = true_peak_limit(mix, ceiling)
    L = meter.integrated_loudness(mix)
    return mix, L, measure_tp(mix)


# ======================================================================= main
def main():
    edit_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "edit", "edit_v1.py")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "renders", "draft_v1.mp4")
    E = load_edit(edit_path)
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    segs, by_id, total = build_timeline(E)

    # narration (final version only)
    nar_path = os.path.join(ROOT, "source", "audio", "narration.wav")
    words_path = os.path.join(ROOT, "edit", "narration_words.json")
    narration, words = None, None
    if os.path.exists(nar_path) and os.path.exists(words_path):
        narration = load_wav(nar_path)
        words = json.load(open(words_path, encoding="utf-8"))
    draft = narration is None

    print(f"timeline {total:.2f}s, {len(segs)} segments, draft={draft}")
    parts = []
    for i, sg in enumerate(segs):
        out = os.path.join(BUILD, f"seg_{i:02d}_{sg['id']}.mp4")
        if sg["kind"] == "clip":
            if getattr(E, "PY_CLIPS", False) or any(k in sg for k in ("zoom_to", "cx_to", "cy_to", "patch")):
                render_clip_py(E, sg, out)
            else:
                render_clip(E, sg, out)
        elif sg["kind"] == "slate":
            render_slate(E, sg, out)
        elif sg["kind"] == "endcard_v4":
            render_endcard_v4(E, sg, out)
        else:
            render_endcard(E, sg, out)
        parts.append(out)
        print(f"  seg {sg['id']:>5}  {sg['start']:6.2f}s  {sg['dur']:5.2f}s  {sg['kind']}"
              + (f"  scale x{sg.get('scale')}" if sg['kind'] == 'clip' else ""))

    lst = os.path.join(BUILD, "concat.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    concat = os.path.join(BUILD, "video_concat.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", concat])

    events, lines = build_captions(E, by_id, total, words)
    if words:  # SRT of the full narration (for platform captions / accessibility)
        def srt_t(t):
            ms = int(round(t * 1000))
            h, ms = divmod(ms, 3600000)
            m, ms = divmod(ms, 60000)
            s_, ms = divmod(ms, 1000)
            return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"
        with open(os.path.splitext(out_path)[0] + ".srt", "w", encoding="utf-8") as f:
            for k, ln in enumerate(lines, 1):
                txt = ln["text"].replace("\\N", "\n")
                nxt = lines[k]["start"] - 0.02 if k < len(lines) else total
                f.write(f"{k}\n{srt_t(ln['start'])} --> {srt_t(min(ln['end'] + 0.3, nxt))}\n{txt}\n\n")
    ass = os.path.join(BUILD, "captions.ass")
    write_ass(E, segs, events, ass, draft=draft)

    logo_png = os.path.join(BUILD, "logo_small.png")
    pad = make_logo_png(E, logo_png)
    t_end = next(sg["start"] for sg in segs if sg["kind"] in ("endcard", "endcard_v4"))

    spans = [(l['start'] - 0.05, l['end'] + 0.1) for l in lines]
    spans += [(at(by_id, sg, off), at(by_id, sg, off) + d) for sg, off, d in getattr(E, 'DUCK_EXTRA', [])]
    mix = mix_audio(E, by_id, total, narration, spans, words)
    mix = mix[: int(round(total * SR))]
    gain_pre = None
    mix, L, tp = master(mix, ceiling=getattr(E, "TP_CEILING", -2.0))
    if STEMS:  # loudness of each stem inside the final master (same gain the master applied)
        meter = pyln.Meter(SR)
        raw = sum(STEMS.values())[: len(mix)]
        g = np.sqrt(np.mean(mix ** 2) / (np.mean(raw ** 2) + 1e-12))
        for k, v in STEMS.items():
            v = v[: len(mix)] * g
            if np.max(np.abs(v)) > 1e-6:
                print(f"  stem {k:5s}: {meter.integrated_loudness(v):6.1f} LUFS")
        if np.max(np.abs(STEMS['vo'])) > 1e-6:
            sf.write(os.path.join(BUILD, "stem_vo.wav"), (STEMS['vo'][: len(mix)] * g).astype(np.float32), SR, subtype="PCM_24")
            sf.write(os.path.join(BUILD, "stem_bed.wav"), ((STEMS['music'] + STEMS['sfx'])[: len(mix)] * g).astype(np.float32), SR, subtype="PCM_24")
            sf.write(os.path.join(BUILD, "stem_music.wav"), (STEMS['music'][: len(mix)] * g).astype(np.float32), SR, subtype="PCM_24")
            sf.write(os.path.join(BUILD, "stem_sfx.wav"), (STEMS['sfx'][: len(mix)] * g).astype(np.float32), SR, subtype="PCM_24")
    wav = os.path.join(BUILD, "mix_master.wav")
    sf.write(wav, mix.astype(np.float32), SR, subtype="PCM_24")
    print(f"master: {L:.2f} LUFS, true peak {tp:.2f} dBTP (pre-encode)")

    fonts = os.path.join(ROOT, "assets", "fonts")
    logo_on = f"lt(t,{t_end:.3f})"
    for sg in segs:  # segments where the logo would cover text printed in the picture
        if sg.get("hide_logo"):
            logo_on += f"*not(between(t,{sg['start']:.3f},{sg['start'] + sg['dur'] - 0.001:.3f}))"
    fc = (f"[0:v][1:v]overlay=x={E.LOGO['x'] - pad}:y={E.LOGO['y'] - pad}:enable='{logo_on}'[v1];"
          f"[v1]ass={ass}:fontsdir={fonts}[v]")
    run(["ffmpeg", "-v", "error", "-y", "-i", concat, "-i", logo_png, "-i", wav, "-filter_complex", fc,
         "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", getattr(E, "FINAL_PRESET", "slow"), "-crf", str(getattr(E, "FINAL_CRF", 17)), "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-r", str(E.FPS), "-g", str(E.FPS * 2),
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", out_path])

    # timeline report for the edit sheet
    report = dict(total_sec=round(total, 3), draft=draft,
                  segments=[dict(id=s["id"], shot=s["shot"], kind=s["kind"], start=round(s["start"], 3),
                                 dur=round(s["dur"], 3), src=s.get("src"), tin=s.get("tin"), tout=s.get("tout"),
                                 zoom=s.get("zoom", 1.0)) for s in segs],
                  captions=[dict(start=round(l["start"], 2), end=round(l["end"], 2), text=l["text"],
                                 shown=l["opt"].get("caption", True)) for l in lines])
    with open(os.path.join(ROOT, "edit", "timeline_" + os.path.splitext(os.path.basename(out_path))[0] + ".json"),
              "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
