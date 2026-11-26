# -*- coding: utf-8 -*-
"""QC: placed VO lines, gaps between lines, and voice-over-bed level per line.

  python3 scripts/qc_vo.py edit/edit_v3.py
Reads build/stem_vo.wav and build/stem_bed.wav written by render.py.
"""
import importlib.util
import json
import sys

import numpy as np
import soundfile as sf

spec = importlib.util.spec_from_file_location("e", sys.argv[1])
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
W = json.load(open("edit/narration_words.json", encoding="utf-8"))
t, starts = 0, {}
for s in E.SEGMENTS:
    d = (s["tout"] - s["tin"]) if s["kind"] == "clip" else s["dur"]
    starts[s["id"]] = t / E.FPS
    t += round(d * E.FPS)
vo, sr = sf.read("build/stem_vo.wav")
bed, _ = sf.read("build/stem_bed.wav")
prev = None
worst = 99
print(f"{'#':>2} {'start':>6} {'end':>6} {'gap':>5} {'VO/bed':>7}  text")
for i, (seg, off, text, hl, opt) in enumerate(E.VO):
    L = W["lines"][i]
    a = starts[seg] + off
    b = a + L[-1]["end"] - L[0]["start"]
    gap = a - prev if prev is not None else 0
    rv = 20 * np.log10(np.sqrt(np.mean(vo[int(a * sr):int(b * sr)] ** 2)) + 1e-9)
    rb = 20 * np.log10(np.sqrt(np.mean(bed[int(a * sr):int(b * sr)] ** 2)) + 1e-9)
    worst = min(worst, rv - rb)
    flag = "  <-- low" if rv - rb < 8 else ""
    print(f"{i:2d} {a:6.2f} {b:6.2f} {gap:5.2f} {rv - rb:6.1f}dB  {text.replace(chr(92) + 'N', ' ')}{flag}")
    prev = b
print(f"lowest voice-over-bed ratio: {worst:.1f} dB")
