# -*- coding: utf-8 -*-
"""Refine Whisper word times against the narration's real energy envelope and
split the narration into one chunk per VO line of the edit.

  python3 scripts/align_words.py edit/edit_v3.py

Inputs : source/audio/narration.wav, edit/narration_transcript.json, the edit's VO list
Output : edit/narration_words.json
  lines[i]  -> words of VO line i: {"w", "start", "end"} in narration seconds
  chunks[i] -> [cut_start, cut_end] audio slice for VO line i (cuts sit in the pauses)

Method: speech spans from a 10 ms RMS envelope (-42 dBFS, gaps < 160 ms
bridged). Each Whisper word is assigned to the span that contains its
centre; inside a span the Whisper times are linearly mapped onto the real
span edges (Whisper's onsets run early on this file by 0.1-0.4 s).
"""
import importlib.util
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOP = 0.01


def load_edit(path):
    spec = importlib.util.spec_from_file_location("edit", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(w):
    return re.sub(r"[^א-ת]", "", w)


def speech_spans(x, sr, thr_db=-42.0, bridge=0.16, min_len=0.06):
    hop = int(HOP * sr)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    on = db > thr_db
    spans, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            spans.append([i * HOP, j * HOP])
            i = j
        else:
            i += 1
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < bridge:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [s for s in merged if s[1] - s[0] >= min_len], db


def main():
    edit = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "edit", "edit_v3.py")
    E = load_edit(edit)
    x, sr = sf.read(os.path.join(ROOT, "source", "audio", "narration.wav"))
    if x.ndim == 2:
        x = x.mean(1)
    T = json.load(open(os.path.join(ROOT, "edit", "narration_transcript.json"), encoding="utf-8"))
    words = [w for w in T["words"] if norm(w["w"])]
    spans, db = speech_spans(x, sr)

    # assign words to spans by centre (nearest span if the centre falls in a gap)
    groups = {k: [] for k in range(len(spans))}
    for wi, w in enumerate(words):
        c = 0.5 * (w["start"] + w["end"]) + 0.12
        best = min(range(len(spans)), key=lambda k: 0 if spans[k][0] <= c <= spans[k][1]
                   else min(abs(c - spans[k][0]), abs(c - spans[k][1])))
        groups[best].append(wi)
    refined = [None] * len(words)
    for k, idx in groups.items():
        if not idx:
            continue
        s0, s1 = spans[k]
        w0, w1 = words[idx[0]]["start"], words[idx[-1]]["end"]
        scale = (s1 - s0) / max(w1 - w0, 1e-3)
        for wi in idx:
            w = words[wi]
            refined[wi] = dict(w=w["w"], start=round(s0 + (w["start"] - w0) * scale, 3),
                               end=round(s0 + (w["end"] - w0) * scale, 3), p=w["p"])

    # split into the edit's VO lines (sequential word counts)
    counts = [len([t for t in line[2].replace("\\N", " ").split() if norm(t)]) for line in E.VO]
    assert sum(counts) == len(refined), (sum(counts), len(refined))
    lines, k = [], 0
    for c, line in zip(counts, E.VO):
        seg = refined[k:k + c]
        # sanity: the transcript words must equal the script words of this line
        exp = [norm(t) for t in line[2].replace("\\N", " ").split() if norm(t)]
        got = [norm(w["w"]) for w in seg]
        assert exp == got, (exp, got)
        lines.append(seg)
        k += c

    # cut points: lowest-energy 10 ms frame between consecutive lines
    chunks = []
    total = len(x) / sr
    for i, seg in enumerate(lines):
        a = 0.0 if i == 0 else chunks[-1][1]
        if i + 1 < len(lines):
            g0, g1 = seg[-1]["end"], lines[i + 1][0]["start"]
            f0, f1 = int(g0 / HOP), max(int(g0 / HOP) + 1, int(g1 / HOP))
            cut = (f0 + int(np.argmin(db[f0:f1]))) * HOP if f1 > f0 else 0.5 * (g0 + g1)
        else:
            cut = total
        chunks.append([round(a, 3), round(cut, 3)])

    out = dict(source="narration.wav", transcript_model=T.get("model"), speech_spans=[[round(a, 3), round(b, 3)] for a, b in spans],
               lines=lines, chunks=chunks)
    with open(os.path.join(ROOT, "edit", "narration_words.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for line, seg, ch in zip(E.VO, lines, chunks):
        print(f"{seg[0]['start']:6.2f}-{seg[-1]['end']:6.2f}  cut[{ch[0]:6.2f},{ch[1]:6.2f}]  {line[2]}")
    print(len(spans), "speech spans,", len(refined), "words")


if __name__ == "__main__":
    main()
