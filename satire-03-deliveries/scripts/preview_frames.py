# -*- coding: utf-8 -*-
"""Quick framing preview: one still per segment (start and end of any zoom move),
with the caption band and corner logo marked. No full render needed.

  python3 scripts/preview_frames.py edit/edit_v5_sq.py out.png
"""
import importlib.util
import os
import subprocess
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("e", sys.argv[1])
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
out = sys.argv[2]


def grab(src, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", os.path.join(ROOT, src), "-map", "0:v:0",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    w, h = [int(v) for v in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                             "stream=width,height", "-of", "csv=p=0:s=x", os.path.join(ROOT, src)],
                                            capture_output=True, text=True).stdout.strip().split("x")]
    return np.frombuffer(raw, np.uint8)[: w * h * 3].reshape(h, w, 3)


def frame(img, z, cx, cy):
    sh, sw = img.shape[:2]
    s = max(E.W / sw, E.H / sh) * z
    ww, wh = E.W / s, E.H / s
    cxp = float(np.clip(cx * sw, ww / 2, sw - ww / 2))
    cyp = float(np.clip(cy * sh, wh / 2, sh - wh / 2))
    M = np.float32([[s, 0, E.W / 2 - s * cxp], [0, s, E.H / 2 - s * cyp]])
    return cv2.warpAffine(img, M, (E.W, E.H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)


# caption band per segment (max lines of any shown VO line in it)
cap = E.CAPTIONS
bands = {}
for seg, off, text, hl, opt in E.VO:
    if not opt.get("caption", True):
        continue
    lines = text.count("\\N") + 1
    size = cap["big_size"] if opt.get("big") else (cap["punch_size"] if opt.get("punch") else cap["size"])
    mv = opt.get("marginv", 0) or cap["margin_v"]
    if opt.get("top"):
        y0 = mv
        y1 = y0 + lines * size * 1.22
    else:
        y1 = E.H - mv
        y0 = y1 - lines * size * 1.22
    bands.setdefault(seg, []).append((int(y0), int(y1)))
tiles = []
for sg in E.SEGMENTS:
    if sg["kind"] != "clip":
        continue
    moving = any(k in sg for k in ("zoom_to", "cx_to", "cy_to"))
    for which in (("a", "b") if moving else ("a",)):
        if moving:
            t_seg = 0.15 if which == "a" else min(sg.get("zoom_t1", sg["tout"] - sg["tin"]) + 0.2, sg["tout"] - sg["tin"] - 0.05)
        else:
            t_seg = 0.5 * (sg["tout"] - sg["tin"])
        t = sg["tin"] + t_seg
        img = grab(sg["src"], t)
        z = sg.get("zoom", 1.0) if which == "a" else sg.get("zoom_to", sg.get("zoom", 1.0))
        cx = sg.get("cx", 0.5) if which == "a" else sg.get("cx_to", sg.get("cx", 0.5))
        cy = sg.get("cy", 0.5) if which == "a" else sg.get("cy_to", sg.get("cy", 0.5))
        fr = frame(img, z, cx, cy).copy()
        ov = fr.copy()
        for y0, y1 in bands.get(sg["id"], []):
            cv2.rectangle(ov, (E.CAPTIONS["margin_l"], y0), (E.W - E.CAPTIONS["margin_r"], y1), (255, 0, 255), -1)
        if not sg.get("hide_logo"):
            L = E.LOGO
            cv2.rectangle(ov, (L["x"], L["y"]), (L["x"] + L["width"], L["y"] + int(L["width"] * 667 / 2000)), (0, 255, 255), -1)
        fr = cv2.addWeighted(ov, 0.35, fr, 0.65, 0)
        cv2.putText(fr, f"{sg['id']}{which}", (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 5)
        tiles.append(cv2.resize(fr, (E.W // 3, E.H // 3), interpolation=cv2.INTER_AREA))
cols = 6
rows = (len(tiles) + cols - 1) // cols
th, tw = tiles[0].shape[:2]
sheet = np.zeros((rows * th, cols * tw, 3), np.uint8)
for k, t in enumerate(tiles):
    sheet[(k // cols) * th:(k // cols + 1) * th, (k % cols) * tw:(k % cols + 1) * tw] = t
cv2.imwrite(out, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
print(len(tiles), "tiles ->", out)
