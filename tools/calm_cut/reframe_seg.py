#!/usr/bin/env python3
"""Reframe a 1080x1920 (9:16) video to 1080x1350 (4:5), shot by shot.

Each frame is defined by a source window: top y0 and height H (width = 0.8 * H,
centered horizontally). H <= 1350 is a plain crop. H > 1350 means the window is
wider than the source, so the frame is scaled down and the side gaps are filled
with a blurred, slightly darker copy of the same moment, feathered into the edge.

Reads raw rgb24 frames on stdin, writes raw rgb24 frames on stdout.
Usage: reframe_seg.py "<window spec>"  < raw frames  > raw frames
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

SW, SH = 1080, 1920
OW, OH = 1080, 1350
FPS = 24.0

# Window spec from argv[1]:
#   "y0,H"                         constant window
#   "y0,H>y0b,Hb@t0-t1[:in]"       animate between t0 and t1 (segment-local
#                                  seconds); ":in" = ease-in, ":lin" = linear, else smoothstep
SPEC = None


def parse(spec):
    if ">" not in spec:
        y0, H = map(float, spec.split(","))
        return ("const", (y0, H))
    a, rest = spec.split(">")
    b, rest = rest.split("@")
    mode = "smooth"
    if ":" in rest:
        rest, mode = rest.split(":")
    t0, t1 = map(float, rest.split("-"))
    return ("anim", tuple(map(float, a.split(","))), tuple(map(float, b.split(","))), t0, t1, mode)


def window_at(t):
    if SPEC[0] == "const":
        return SPEC[1]
    _, a, b, t0, t1, mode = SPEC
    x = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    if mode == "in":
        k = x * x
    elif mode == "lin":
        k = x
    else:
        k = x * x * (3 - 2 * x)
    return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k


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
    SPEC = parse(sys.argv[1])
    stream()
