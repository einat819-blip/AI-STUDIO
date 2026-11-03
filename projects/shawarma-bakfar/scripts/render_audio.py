# -*- coding: utf-8 -*-
"""Sound design + ORIGINAL music for the ad, frame-synced to edl.py.

Nothing here is sampled from a library: the music and the designed SFX are
synthesised in code (no licence issues). Ambience comes from the delivered
clips' own audio tracks, cut in sync with the picture.

python3 render_audio.py --version main --sources DIR --outdir DIR
 -> <version>_music_stem.wav, <version>_sfx_stem.wav,
    <version>_mix.wav (master), <version>_sfx_only.wav (master, no music)
"""
import argparse
import os
import subprocess

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d

import edl as E

SR = 48000
RNG = np.random.default_rng(7)  # deterministic renders


# ------------------------------------------------------------- helpers ----
def T(frame):
    return frame / E.FPS


def n(sec):
    return int(round(sec * SR))


def tvec(dur):
    return np.arange(n(dur)) / SR


def sos_bp(lo, hi, order=2):
    return signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")


def bp(x, lo, hi, order=2):
    return signal.sosfilt(sos_bp(lo, hi, order), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def noise(dur):
    return RNG.standard_normal(n(dur))


def db(x):
    return 10 ** (x / 20.0)


def fade(x, fin=0.004, fout=0.004):
    x = x.copy()
    a, b = n(fin), n(fout)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def stereo(x, pan=0.0, width=0.0):
    """mono -> stereo with constant-power pan; width adds a tiny decorrelation."""
    if x.ndim == 2:
        return x
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    out = np.stack([x * l, x * r], axis=1) * np.sqrt(2)
    if width > 0:
        d = int(0.0007 * SR)
        out[d:, 1] = (1 - width) * out[d:, 1] + width * out[:-d, 1]
    return out


class Bus:
    def __init__(self, dur):
        self.buf = np.zeros((n(dur), 2))

    def add(self, x, t0, gain_db=0.0, pan=0.0, width=0.0):
        x = stereo(x, pan, width) * db(gain_db)
        i = n(t0)
        if i < 0:
            x, i = x[-i:], 0
        j = min(len(self.buf), i + len(x))
        if j > i:
            self.buf[i:j] += x[: j - i]


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def load_audio(path, t0, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(t0, 0):.5f}", "-t", f"{dur:.5f}", "-i", path,
           "-map", "0:a:0", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    want = n(dur)
    if len(x) < want:
        x = np.vstack([x, np.zeros((want - len(x), 2))])
    return x[:want]


def tape_stop(x, t_stop, dur):
    """'Time stops': from t_stop the playback speed ramps 1 -> 0 over dur."""
    x = x.copy()
    i0 = n(t_stop)
    m = n(dur)
    if i0 >= len(x):
        return x
    rate = np.clip(1.0 - np.arange(m) / m, 0, 1) ** 1.3
    pos = i0 + np.cumsum(rate)
    tail = np.zeros((m, 2))
    src_idx = np.arange(len(x))
    for c in range(2):
        tail[:, c] = np.interp(pos, src_idx, x[:, c], right=0.0)
    tail *= np.linspace(1, 0, m)[:, None] ** 0.7
    end = min(len(x), i0 + m)
    x[i0:end] = tail[: end - i0]
    x[end:] = 0
    return x


def reverb_ir(dur=0.8, damp=4000, seed=3):
    r = np.random.default_rng(seed)
    t = tvec(dur)
    env = np.exp(-6.9 * t / dur)
    ir = np.stack([lp(r.standard_normal(len(t)), damp) * env,
                   lp(r.standard_normal(len(t)), damp) * env], axis=1)
    ir[: n(0.008)] = 0  # pre-delay
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir, wet):
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return x + wet * y


# ---------------------------------------------------------- SFX design ----
def engine_layer(dur):
    """old diesel tractor 'putt-putt' body: firing pulses ~17 Hz."""
    t = tvec(dur)
    f = 17.0 + 0.6 * np.sin(2 * np.pi * 0.7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulses = np.maximum(np.sin(ph), 0) ** 6
    body = lp(pulses + 0.25 * noise(dur) * pulses, 420, 4)
    rattle = bp(noise(dur), 900, 2600) * (0.4 + pulses) * 0.08
    return body + rattle


def brake_screech(dur):
    """squealing brake + gravel skid, rising."""
    t = tvec(dur)
    wander = lp(noise(dur), 8) * 900
    f = 2350 + 260 * (t / dur) + 35 * np.sin(2 * np.pi * 7.3 * t) + wander
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.35 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3 * ph + 1.1)
    rough = 0.75 + 0.25 * np.sin(2 * np.pi * 31 * t + 2 * np.sin(2 * np.pi * 3 * t))
    env = np.clip(t / 0.09, 0, 1) ** 1.5 * (0.55 + 0.45 * t / dur)
    squeal = lp(tone * rough * env, 7000)
    grains = (RNG.random(len(t)) < 0.004).astype(float) * RNG.uniform(0.3, 1.0, len(t))
    gravel = bp(noise(dur) * 0.35 + signal.lfilter([1], [1, -0.97], grains) * 0.8, 350, 3200)
    gravel *= np.clip(t / 0.05, 0, 1) * (0.6 + 0.4 * t / dur)
    return 0.30 * squeal + 0.55 * gravel


def freeze_hit():
    """the recurring 'time-stop' accent: low thump + shutter clack + air-suck."""
    d = 0.45
    t = tvec(d)
    f = 42 + 50 * np.exp(-t / 0.05)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    clack = np.zeros(len(t))
    for off, g in ((0.0, 1.0), (0.021, 0.7)):
        i = n(off)
        c = bp(noise(0.03), 1500, 6500) * np.exp(-tvec(0.03) / 0.004) * g
        clack[i:i + len(c)] += c
    return 0.9 * thump + 0.55 * clack


def air_suck(dur=0.16):
    """short reversed swell that 'pulls' into the freeze."""
    t = tvec(dur)
    x = hp(noise(dur), 1800) * (t / dur) ** 3
    return x * 0.35


def clock_tick(kind="tick"):
    d = 0.12
    t = tvec(d)
    f1, f2 = (3150, 5200) if kind == "tick" else (2500, 4300)
    ping = (np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f2 * t)) * np.exp(-t / 0.012)
    click = bp(noise(d), 2000, 9000) * np.exp(-t / 0.002)
    return 0.5 * ping + 0.9 * click


def clock_stop():
    """last, heavier 'tock' + mechanism clunk: the clock stops."""
    d = 0.5
    t = tvec(d)
    knock = np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.035) + 0.6 * np.sin(2 * np.pi * 690 * t) * np.exp(-t / 0.02)
    ring = (np.sin(2 * np.pi * 2480 * t) + 0.4 * np.sin(2 * np.pi * 3970 * t)) * np.exp(-t / 0.09) * 0.25
    click = bp(noise(d), 1500, 8000) * np.exp(-t / 0.003)
    return 0.9 * knock + ring + 0.9 * click


def fire_flare(dur=1.6):
    """gas flare 'whoomp' + crackle for the spit reveal."""
    t = tvec(dur)
    env = np.clip(t / 0.035, 0, 1) * np.exp(-t / 0.45)
    roar = bp(noise(dur), 90, 1100, 2) * env
    dens = 0.0025 * np.exp(-t / 0.9) + 0.0006
    grains = (RNG.random(len(t)) < dens).astype(float) * RNG.uniform(0.2, 1.0, len(t))
    crackle = bp(signal.lfilter([1], [1, -0.9], grains), 1800, 9000) * 0.9
    return 0.9 * roar + crackle


def sizzle(dur):
    """fat on a hot grill: hiss + dense tiny pops (used as a prelap)."""
    t = tvec(dur)
    hiss = hp(noise(dur), 3500) * 0.12 * (1 + 0.3 * np.sin(2 * np.pi * 5 * t))
    grains = (RNG.random(len(t)) < 0.012).astype(float) * RNG.uniform(0.1, 1.0, len(t))
    pops = bp(signal.lfilter([1], [1, -0.8], grains), 1500, 9000) * 0.5
    return hiss + pops


def knife_slice(dur=0.38):
    """long blade drawn through crusty meat."""
    t = tvec(dur)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8
    scrape = bp(noise(dur), 2500, 9500) * env * 0.5
    grains = (RNG.random(len(t)) < 0.02).astype(float) * RNG.uniform(0.2, 1.0, len(t))
    crunch = bp(signal.lfilter([1], [1, -0.6], grains), 900, 6000) * env * 1.2
    return scrape + crunch


def knife_shing():
    d = 0.5
    t = tvec(d)
    ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
               for f, a, tau in ((2960, 0.5, 0.18), (4870, 0.35, 0.12), (7310, 0.2, 0.08), (9120, 0.12, 0.05)))
    swish = bp(noise(d), 3000, 11000) * np.exp(-t / 0.04)
    return 0.55 * ring + 0.8 * swish


def crunch(dur=0.16):
    t = tvec(dur)
    grains = (RNG.random(len(t)) < 0.06).astype(float) * RNG.uniform(0.3, 1.0, len(t))
    x = bp(signal.lfilter([1], [1, -0.5], grains), 700, 7000) * np.exp(-t / (dur / 2.5))
    return x * 1.5


def meat_flop():
    d = 0.2
    t = tvec(d)
    return np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.04) * 0.8 + bp(noise(d), 300, 1500) * np.exp(-t / 0.02) * 0.4


def logo_pop():
    d = 0.3
    t = tvec(d)
    f = 110 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) + bp(noise(d), 2000, 8000) * np.exp(-t / 0.004) * 0.4


# ------------------------------------------------------------- MUSIC ------
BPM = 120.0
BEAT = 60.0 / BPM  # 0.5 s = 12 frames @ 24 fps
NOTE = {"D2": 73.42, "Eb2": 77.78, "C2": 65.41, "A1": 55.0, "D3": 146.83, "A3": 220.0,
        "D4": 293.66, "Eb4": 311.13, "F#4": 369.99, "G4": 392.0, "A4": 440.0,
        "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "F#3": 185.0}


def kick():
    d = 0.42
    t = tvec(d)
    f = 47 + 110 * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    click = hp(noise(d), 3000) * np.exp(-t / 0.0015) * 0.5
    return np.tanh(1.6 * (body + click)) * 0.9


def clap():
    d = 0.3
    t = tvec(d)
    x = np.zeros(len(t))
    for off in (0.0, 0.009, 0.018):
        i = n(off)
        b = bp(noise(d - off), 900, 4200) * np.exp(-tvec(d - off) / 0.006)
        x[i:] += b
    tail = bp(noise(d), 900, 5000) * np.exp(-t / 0.09) * 0.45
    return (x + tail) * 0.7


def doum():
    d = 0.35
    t = tvec(d)
    f = 88 + 40 * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15) + bp(noise(d), 200, 900) * np.exp(-t / 0.01) * 0.3


def tek(g=1.0):
    d = 0.12
    t = tvec(d)
    ping = np.sin(2 * np.pi * 1320 * t) * np.exp(-t / 0.018) * 0.5
    snap = bp(noise(d), 2200, 10000) * np.exp(-t / 0.012)
    return (ping + snap) * g


def shaker(g=1.0):
    d = 0.07
    t = tvec(d)
    env = np.clip(t / 0.006, 0, 1) * np.exp(-t / 0.02)
    return hp(noise(d), 6500) * env * g


def crash(dur=1.8):
    t = tvec(dur)
    x = hp(noise(dur), 3500) * np.exp(-t / 0.55)
    x += hp(noise(dur) * np.sin(2 * np.pi * 5100 * t), 4000) * np.exp(-t / 0.3) * 0.4
    return x * 0.55


def sub_boom(dur=1.2, f0=55):
    t = tvec(dur)
    f = f0 + 25 * np.exp(-t / 0.05)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.4)


def bass_note(freq, dur):
    t = tvec(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(4 * np.pi * freq * t) + 0.2 * np.sin(6 * np.pi * freq * t)
    env = np.clip(t / 0.006, 0, 1) * (0.55 + 0.45 * np.exp(-t / 0.12))
    env *= np.clip((dur - t) / 0.02, 0, 1)
    return np.tanh(1.8 * x * env) * 0.6


def pluck(freq, dur, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string (oud / saz-like), block-vectorised."""
    N = int(SR / freq)
    total = n(dur)
    out = np.zeros(total + N + 1)
    burst = RNG.uniform(-1, 1, N)
    burst = lp(burst, 1500 + 6000 * bright, 1)
    out[:N] = burst
    k = N
    while k < total + 1:
        m = min(N, total + 1 - k)
        prev = out[k - N: k - N + m]
        prev2 = out[k - N - 1: k - N - 1 + m] if k - N - 1 >= 0 else np.concatenate([[0], prev[:-1]])
        out[k:k + m] = decay * (0.5 * prev + 0.5 * prev2)
        k += m
    y = out[N:N + total]
    body = bp(y, 180, 3500, 1)
    t = tvec(dur)
    env = np.clip((dur - t) / 0.03, 0, 1)
    return (0.65 * y + 0.6 * body) * env


# riff in Hijaz on D, (beat offset, note, length in beats). 2-bar phrase.
RIFF = [
    (0.0, "A4", 0.5), (0.5, "Bb4", 0.25), (0.75, "A4", 0.25),
    (1.0, "G4", 0.25), (1.25, "F#4", 0.25), (1.5, "G4", 0.5),
    (2.0, "A4", 0.5), (2.5, "D5", 0.5),
    (3.0, "C5", 0.25), (3.25, "Bb4", 0.25), (3.5, "A4", 0.5),
    (4.0, "A4", 0.5), (4.5, "Bb4", 0.25), (4.75, "A4", 0.25),
    (5.0, "G4", 0.25), (5.25, "F#4", 0.25), (5.5, "Eb4", 0.5),
    (6.0, "D4", 1.0),
    (7.0, "F#4", 0.25), (7.25, "G4", 0.25), (7.5, "A4", 0.5),
]
# bass in 8ths per bar (None = rest)
BASS = ["D2", None, "D2", "Eb2", "D2", None, "C2", "D2"]


def music(dur, start, final_hit):
    """Energetic darbuka-pop groove from `start` to a clean final hit."""
    bus = Bus(dur)
    beats = int(round((final_hit - start) / BEAT))
    ir = reverb_ir(0.9, 5000)
    perc = Bus(dur)
    for b in range(beats):
        tb = start + b * BEAT
        bar_pos = b % 4
        last = b == beats - 1
        # kick: 1, 2&, 3 (8th grid) ; clap 2 and 4
        if not last:
            if bar_pos in (0, 2):
                bus.add(kick(), tb, -3)
            if bar_pos == 1:
                bus.add(kick(), tb + BEAT / 2, -6)
            if bar_pos in (1, 3):
                perc.add(clap(), tb, -7, width=0.4)
        # darbuka maqsum-ish: D T . T | D . T .
        if not last:
            if bar_pos in (0, 2):
                perc.add(doum(), tb, -6, pan=-0.1)
            perc.add(tek(0.9), tb + BEAT / 2, -9, pan=0.25)
            if bar_pos in (1, 3):
                perc.add(tek(0.6), tb + 3 * BEAT / 4, -14, pan=0.3)
        else:  # build: 32nd-note tek roll, crescendo into the final hit
            for k in range(8):
                perc.add(tek(0.4 + 0.6 * k / 7), tb + k * BEAT / 8, -14 + 7 * k / 7, pan=0.2 - 0.05 * k)
        # shaker 16ths, accent offbeats
        if not last:
            for k in range(4):
                perc.add(shaker(1.0 if k % 2 else 0.55), tb + k * BEAT / 4, -20, pan=0.45)
        # bass 8ths
        if not last:
            for k in range(2):
                note = BASS[(bar_pos * 2 + k) % 8]
                if note:
                    bus.add(bass_note(NOTE[note], BEAT / 2 * 0.92), tb + k * BEAT / 2, -9)
    # riff (loops every 2 bars); stops before the build beat
    phrase_beats = 8.0
    t_end_riff = final_hit - BEAT
    rep = 0
    while start + rep * phrase_beats * BEAT < t_end_riff:
        for off, note, ln in RIFF:
            t0 = start + (rep * phrase_beats + off) * BEAT
            if t0 >= t_end_riff - 1e-6:
                continue
            perc.add(pluck(NOTE[note], ln * BEAT + 0.25, 0.55), t0, -8, pan=-0.2, width=0.3)
        rep += 1
    # drop accents
    bus.add(crash(), start, -10, width=0.6)
    bus.add(sub_boom(0.9, 50), start, -10)
    # FINAL HIT: chord strum + boom + kick + crash, then it rings out clean
    for i, nt in enumerate(("D3", "A3", "D4", "F#4", "A4")):
        perc.add(pluck(NOTE[nt], 1.1, 0.7, 0.9975), final_hit + i * 0.012, -9, pan=-0.3 + 0.15 * i)
    bus.add(kick(), final_hit, -5)
    bus.add(sub_boom(1.1, 48), final_hit, -9)
    perc.add(doum(), final_hit, -4)
    bus.add(crash(1.4), final_hit, -9, width=0.6)
    out = bus.buf + reverb(perc.buf, ir, 0.18)
    # phone-friendly low end: trim sub below ~45 Hz, gentle bus glue (soft clip)
    out = signal.sosfilt(signal.butter(2, 45, btype="high", fs=SR, output="sos"), out, axis=0)
    k = 1.4
    out = np.tanh(k * out) / k
    # end cleanly: fade the last ringing 80 ms to digital silence
    e = n(dur)
    out[e - n(0.08):e] *= np.linspace(1, 0, n(0.08))[:, None]
    return out


# ------------------------------------------------------------ assemble ----
TARGET_RMS = {"tractor": -18, "soccer": -21, "coffee": -26, "food": -25}


def src_audio_for_segment(sources, seg, extra=0.0):
    path = os.path.join(sources, E.SRC[seg["src"]])
    f0, f1 = seg["frames"][0], seg["frames"][-1] + 1
    x = load_audio(path, T(f0), T(f1 - f0) + extra)
    g = db(TARGET_RMS[seg["src"]]) / max(rms(x), db(-60))
    g = min(g, db(30), db(-10) / max(np.abs(x).max(), 1e-9))  # cap transients
    return x * g


def build(version, sources):
    v = E.VERSIONS[version]
    edl, sync = v["edl"], v["sync"]
    dur = T(sync["end"])
    starts = E.segment_starts(edl)
    seg = {s["name"]: (s, st) for s, st in zip(edl, starts)}
    sfx = Bus(dur)
    room = reverb_ir(0.35, 6000, seed=11)

    # ---- 1. tractor: engine + screech, then time stops ------------------
    tf = T(sync["freeze_tractor"])
    tr = Bus(tf + 0.4)
    for name in ("tractor_drive", "tractor_headturn"):
        s, st = seg[name]
        x = src_audio_for_segment(sources, s, extra=0.35 if name == "tractor_headturn" else 0.0)
        tr.add(fade(x, 0.003, 0.006), T(st))
    tr.add(engine_layer(tf + 0.4) * 0.5, 0.0, -8)
    t_scr = 0.27
    tr.add(brake_screech(tf - t_scr + 0.35), t_scr, -7, pan=0.15, width=0.3)
    sfx.add(tape_stop(tr.buf, tf, 0.17), 0.0)
    sfx.add(air_suck(), tf - 0.16, -12, width=0.5)
    sfx.add(reverb(stereo(freeze_hit()), room, 0.25), tf, -4)

    # ---- 2. soccer: kick + field air, freeze ----------------------------
    s, st = seg["soccer_kick"]
    tfz = T(sync["freeze_soccer"])
    x = src_audio_for_segment(sources, s, extra=0.3)
    sb = Bus(dur)
    sb.add(fade(x, 0.003, 0.01), T(st) - 0.02)
    sfx.add(tape_stop(sb.buf, tfz, 0.15), 0.0)
    sfx.add(air_suck(), tfz - 0.16, -12, width=0.5)
    sfx.add(reverb(stereo(freeze_hit()), room, 0.25), tfz, -4)

    # ---- 3. coffee: pour + ticking clock that stops -> dead silence ------
    if "coffee_pour" in seg:
        s, st = seg["coffee_pour"]
        tcf = T(sync["freeze_coffee"])
        x = hp(src_audio_for_segment(sources, s, extra=0.3).T, 150).T
        cb = Bus(dur)
        cb.add(fade(x, 0.004, 0.01), T(st))
        sfx.add(tape_stop(cb.buf, tcf, 0.12), 0.0)
        t0 = T(st)
        for i, tt in enumerate((t0 + 0.01, t0 + 0.18, t0 + 0.35)):
            sfx.add(clock_tick("tick" if i % 2 == 0 else "tock"), tt, -11, pan=0.1)
        sfx.add(reverb(stereo(clock_stop()), room, 0.2), tcf, -10, pan=0.1)

    # ---- 4. prelap sizzle in the silence, then the DROP -----------------
    food = os.path.join(sources, E.SRC["food"])
    td = T(sync["drop"])
    pre = sizzle(0.45) * (np.linspace(0, 1, n(0.45)) ** 2.5)
    sfx.add(pre, td - 0.45, -10, width=0.6)
    sfx.add(fire_flare(), td, -5, width=0.6)
    sfx.add(sub_boom(0.6, 60), td, -9)

    # food beds in sync with picture (spit, pour, hands)
    for name in ("spit_wide", "cut_a", "cut_b", "tahini_pour", "hero_hands"):
        if name in seg:
            s, st = seg[name]
            x = src_audio_for_segment(sources, s)
            sfx.add(fade(x, 0.004, 0.006), T(st))

    # knife work, frame-synced
    if "knife_wide" in sync:
        sfx.add(knife_slice(0.42), T(sync["knife_wide"]), -6, pan=-0.15, width=0.3)
    if "cut_a" in sync:
        sfx.add(knife_shing(), T(sync["cut_a"]), -7, pan=0.1, width=0.3)
        sfx.add(crunch(0.18), T(sync["cut_a"]) + 0.02, -6)
    if "cut_b" in sync:
        sfx.add(crunch(0.22), T(sync["cut_b"]), -3, pan=-0.1)
        sfx.add(knife_slice(0.3), T(sync["cut_b"]), -9, pan=0.1)
        sfx.add(meat_flop(), T(sync["cut_b"]) + 0.28, -8)

    # end card: duck the food bed so the logo + final hit land clean
    lg = n(T(sync["logo"]))
    ramp = np.ones(len(sfx.buf))
    ramp[lg:] = np.maximum(0.2, np.exp(-np.arange(len(ramp) - lg) / (0.25 * SR)))
    sfx.buf *= ramp[:, None]
    sfx.add(logo_pop(), T(sync["logo"]), -8)
    e = n(0.06)
    sfx.buf[-e:] *= np.linspace(1, 0, e)[:, None]

    mus = music(dur, td, T(sync["final_hit"]))
    return sfx.buf, mus


# -------------------------------------------------------------- master ----
def lufs(x):
    """integrated loudness via ffmpeg ebur128 (+ true peak)."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2",
                        "-i", "-", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    txt = p.stderr.decode()
    summ = txt[txt.rfind("Summary:"):]
    I = float(summ.split("I:")[1].split("LUFS")[0])
    tp = float(summ.split("Peak:")[1].split("dBFS")[0])
    return I, tp


def limiter(x, ceiling_db=-1.5, look=0.0025):
    thr = db(ceiling_db)
    L = max(3, n(look) | 1)
    peak = maximum_filter1d(np.max(np.abs(x), axis=1), size=L)
    g = np.minimum(1.0, thr / np.maximum(peak, 1e-9))
    g = minimum_filter1d(g, size=L)
    g = uniform_filter1d(g, size=L)
    rel = n(0.06)
    g = np.minimum(g, uniform_filter1d(minimum_filter1d(g, size=rel), size=rel))
    return x * g[:, None]


def master(x, target=-14.0):
    x = signal.sosfilt(signal.butter(2, 32, btype="high", fs=SR, output="sos"), x, axis=0)
    I, _ = lufs(x)
    y = x * db(target - I)
    for _ in range(3):
        y = limiter(y)
        I2, tp = lufs(y)
        if abs(I2 - target) < 0.3 and tp <= -1.0:
            break
        y = y * db(target - I2) if abs(I2 - target) >= 0.3 else y * db(-1.0 - tp - 0.1)
    y = limiter(y, -1.5)
    return y


def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", path], input=x.astype(np.float32).tobytes(), check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="main", choices=list(E.VERSIONS))
    ap.add_argument("--sources", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    sfx, mus = build(a.version, a.sources)
    mix_bus = sfx * db(0) + mus * db(-3)
    mix = master(mix_bus, -14.0)
    sfx_only = master(sfx, -16.0)
    pre = os.path.join(a.outdir, a.version)
    write_wav(pre + "_sfx_stem.wav", sfx * 0.5)
    write_wav(pre + "_music_stem.wav", mus * db(-3) * 0.5)
    write_wav(pre + "_mix.wav", mix)
    write_wav(pre + "_sfx_only.wav", sfx_only)
    for name, sig in (("mix", mix), ("sfx_only", sfx_only)):
        I, tp = lufs(sig)
        print(f"{a.version}_{name}: {I:.1f} LUFS, true peak {tp:.1f} dBTP, {len(sig) / SR:.3f}s")
