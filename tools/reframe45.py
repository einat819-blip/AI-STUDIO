#!/usr/bin/env python3
"""Reframe a 1080x1920 (9:16) video to 1080x1350 (4:5), shot by shot.

Each frame is defined by a source window: top y0 and height H (width = 0.8 * H,
centered horizontally). H <= 1350 is a plain crop. H > 1350 means the window is
wider than the source, so the frame is scaled down and the side gaps are filled
with a blurred, slightly darker copy of the same moment, feathered into the edge.

Reads raw rgb24 frames on stdin, writes raw rgb24 frames on stdout.
Usage: reframe45.py [--preview t1,t2,... outdir]  (preview reads a video path)
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

SW, SH = 1080, 1920
OW, OH = 1080, 1350
FPS = 24.0

# (start_time, y0, H): framing switches on the source's own cuts.
# Times are seconds in the source file.
CUT_PLAN = [
    (0.000, 75, 1480),    # shot 1: invitation, "אבאאא!" top bubble + full card
    (1.500, 120, 1350),   # shot 2: dad walks in (crop)
    (2.333, 75, 1480),    # shot 3: "8:00 בבוקר!" top bubble + full card
    (3.292, 80, 1350),    # shot 4: punch-in "כן, בבוקר!", details box left out
    (3.875, 120, 1350),   # shot 5: dad wide
    (4.167, 120, 1350),   # shot 6: dad at fridge, "בבוקר?!" / "אל תאחר!"
    (7.458, 250, 1350),   # shot 7: boy fixes tallit
    (8.833, 80, 1620),    # pull-back starts with a jump here; bubbles pop at 8.875
]
# Animated window: (t0, t1, from_window, to_window)
EASE = (10.10, 10.70, (80, 1620), (292, 1350))   # gentle push-in to the end card


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def window_at(t):
    t0, t1, a, b = EASE
    if t >= t1:
        return b
    if t >= t0:
        k = smooth((t - t0) / (t1 - t0))
        return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
    y0, H = CUT_PLAN[0][1:]
    for start, yy, hh in CUT_PLAN:
        if t + 1e-6 >= start:
            y0, H = yy, hh
    return y0, H


def feather_mask(w, h, edge):
    m = np.ones((h, w), dtype=np.float32)
    if edge > 0:
        ramp = np.linspace(0.0, 1.0, edge, dtype=np.float32)
        m[:, :edge] *= ramp[None, :]
        m[:, w - edge:] *= ramp[::-1][None, :]
    return m


def render(frame, t):
    y0, H = window_at(t)
    W = 0.8 * H
    s = OH / H
    if W <= SW:
        # plain crop, window fits inside the source width
        x0 = (SW - W) / 2
        box = (x0, y0, x0 + W, y0 + H)
        return np.asarray(frame.resize((OW, OH), Image.LANCZOS, box=box))

    # Foreground: full source width, rows y0..y0+H, scaled by s
    fw = int(round(SW * s))
    fg = frame.resize((fw, OH), Image.LANCZOS, box=(0, y0, SW, y0 + H))

    # Background: the foreground itself stretched to full width and blurred,
    # so each side strip continues the colors right next to it
    bg = fg.resize((OW // 8, OH // 8), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(3)).resize((OW, OH), Image.BICUBIC)
    bg = np.asarray(bg).astype(np.float32) * 0.96

    out = bg
    xo = (OW - fw) // 2
    edge = min(28, max(6, xo // 2))
    m = feather_mask(fw, OH, edge)[..., None]
    region = out[:, xo:xo + fw]
    out[:, xo:xo + fw] = region * (1 - m) + np.asarray(fg).astype(np.float32) * m
    return np.clip(out, 0, 255).astype(np.uint8)


def stream():
    n = 0
    size = SW * SH * 3
    rd = sys.stdin.buffer
    wr = sys.stdout.buffer
    while True:
        buf = rd.read(size)
        if len(buf) < size:
            break
        img = Image.frombuffer("RGB", (SW, SH), buf, "raw", "RGB", 0, 1)
        wr.write(render(img, n / FPS).tobytes())
        n += 1
    sys.stderr.write(f"frames: {n}\n")


def preview(video, times, outdir):
    import subprocess, os
    os.makedirs(outdir, exist_ok=True)
    for t in times:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            check=True, capture_output=True).stdout
        img = Image.frombuffer("RGB", (SW, SH), raw, "raw", "RGB", 0, 1)
        Image.fromarray(render(img, t)).save(os.path.join(outdir, f"pv_{t:06.3f}.png"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview(sys.argv[2], [float(x) for x in sys.argv[3].split(",")], sys.argv[4])
    else:
        stream()
