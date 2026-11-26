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
    if words_override:  # real timings from transcription: {"lines": [[{"w":..,"start":..,"end":..}, ...], ...]}
        for ln, real in zip(lines, words_override["lines"]):
            ln["words"] = [(w["w"], w["start"], w["end"]) for w in real]
            ln["start"], ln["end"] = real[0]["start"], real[-1]["end"]
    events = []
    shown = [l for l in lines if l["opt"].get("caption", True)]
    for k, ln in enumerate(shown):
        nxt = shown[k + 1]["start"] if k + 1 < len(shown) else total
        cap_end = min(nxt - 0.04, ln["end"] + 0.55)
        cap_end = max(cap_end, ln["start"] + 0.7)
        style = "Big" if ln["opt"].get("big") else "Cap"
        mv = ln["opt"].get("marginv", 0)
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
                colour = COL.get(ln["hl"].get(tok, "white"))
                hidden = wi > step
                tag = "{\\alpha&HFF&}" if hidden else "{\\alpha&H00&}"
                parts.append(f"{tag}{{\\c{colour}}}{tok}")
                wi += 1
            txt = " ".join(parts).replace(" \\N ", "\\N")
            # a short pop on the first word of a punch line
            if style == "Big" and step == 0:
                txt = "{\\fscx70\\fscy70\\t(0,120,\\fscx100\\fscy100)}" + txt
            events.append((s, e, style, txt, mv))
    return events, lines


def write_ass(E, segs, events, path, draft=True):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {E.W}
PlayResY: {E.H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Heebo Black,76,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,6,3,2,110,170,520,-1
Style: Big,Heebo Black,118,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0,0,1,8,4,2,110,170,520,-1
Style: SlateTitle,Heebo Bold,56,&H00F0F0F0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,-1
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
    if draft:
        total = segs[-1]["start"] + segs[-1]["dur"]
        t_draft_end = next((sg["start"] for sg in segs if sg["kind"] == "endcard"), total)
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


def mix_audio(E, by_id, total, narration=None, vo_spans=None):
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

    for seg, off, cue, cfrom, stop, gdb, fin, fout in E.MUSIC:
        t0 = at(by_id, seg, off)
        x = get("music", cue)
        x = x[int(cfrom * SR):]
        if stop:
            t1 = at(by_id, *stop)
            x = x[: int((t1 - t0) * SR)]
        put(music, x, t0, db(gdb), fin, fout)

    for seg, off, name, gdb, frm, dur in E.SFX:
        t0 = at(by_id, seg, off)
        x = get("sfx", name)[int(frm * SR):]
        if dur:
            x = x[: int(dur * SR)]
            fo = min(0.4, dur / 3)
        else:
            fo = 0.01
        put(sfx, x, t0, db(gdb), 0.01 if name.startswith("room") else 0.0, fo)

    # ducking: music dips under the voice (real narration envelope, or the
    # estimated VO spans in draft mode so SFX/music balance matches the final)
    if narration is not None:
        vo = narration[:n]
        vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
        env = np.abs(signal.hilbert(vo.mean(1)))
        env = signal.sosfilt(signal.butter(2, 8, fs=SR, output="sos"), env)
        talk = (env > db(-38)).astype(float)
    else:
        vo = np.zeros((n, 2))
        talk = np.zeros(n)
        for a, b in (vo_spans or []):
            talk[int(a * SR):int(b * SR)] = 1.0
    g = smooth_gate(talk, 0.04, 0.35)
    music *= (db(-9) ** g)[:, None]
    return vo + music * db(-6) + sfx * db(-3)


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
            render_clip(E, sg, out)
        elif sg["kind"] == "slate":
            render_slate(E, sg, out)
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
    ass = os.path.join(BUILD, "captions.ass")
    write_ass(E, segs, events, ass, draft=draft)

    logo_png = os.path.join(BUILD, "logo_small.png")
    pad = make_logo_png(E, logo_png)
    t_end = by_id["14"]["start"]

    spans = [(l['start'] - 0.05, l['end'] + 0.1) for l in lines]
    spans += [(at(by_id, sg, off), at(by_id, sg, off) + d) for sg, off, d in getattr(E, 'DUCK_EXTRA', [])]
    mix = mix_audio(E, by_id, total, narration, spans)
    mix = mix[: int(round(total * SR))]
    mix, L, tp = master(mix)
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
         "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
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
