"""Compose and synthesize the three original music cues.

  jingle_commercial.wav  D major, 124 BPM, 16 bars. Sparkly, over-happy ad music.
  epic_adventure.wav     D minor -> heroic, 96 BPM. Adventure (A), build (B), epic (C).
  fanfare_victory.wav    Bb major brass "ta-ta-ta-TAAA" for the ironic "בהצלחה!".

Run:  python3 scripts/make_music.py
Cue maps (bar start times) are written to assets/music/cue_map.json.
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from audiolib import *  # noqa

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "music")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)

# ----------------------------------------------------------------- instruments


def kick(gain=1.0):
    n = int(0.35 * SR)
    f = 48 + 95 * np.exp(-np.arange(n) / SR / 0.03)
    x = sine(f, n) * env_exp(n, 0.16, 0.001)
    m = int(0.004 * SR)
    x[:m] += rng.standard_normal(m) * 0.3 * np.linspace(1, 0, m)
    return x * gain


def clap(gain=1.0):
    n = int(0.25 * SR)
    x = np.zeros(n)
    for k, d in enumerate([0.0, 0.011, 0.022]):
        i = int(d * SR)
        m = int(0.012 * SR) if k < 2 else n - i
        seg = rng.standard_normal(m) * env_exp(m, 0.004 if k < 2 else 0.05, 0.0005)
        x[i:i + m] += seg
    return bp(x, 900, 4200) * gain


def hat(open_=False, gain=1.0):
    n = int((0.25 if open_ else 0.06) * SR)
    x = hp(rng.standard_normal(n), 7000) * env_exp(n, 0.08 if open_ else 0.012, 0.0005)
    return x * gain


def crash(dur=2.2, gain=1.0):
    n = int(dur * SR)
    x = hp(noise(dur, "pink", rng), 3000) * env_exp(n, 0.7, 0.002)
    x += bp(rng.standard_normal(n), 2000, 6000) * env_exp(n, 0.25, 0.002) * 0.25
    x = lp(x, 11000)
    return pan(x, 0.25) * gain


def synth_bass(f, dur):
    n = int(dur * SR)
    x = saw(f, n) * 0.6 + sine(f, n) * 0.8
    fc = 250 + 1100 * np.exp(-np.arange(n) / SR / 0.06)
    x = tv_lowpass(x, fc)
    return x * env_adsr(n, 0.004, 0.08, 0.7, 0.04)


def pluck(f, dur=1.2, bright=0.6):
    x = karplus(f, dur, damping=0.995, bright=bright, rng=rng)
    x = hp(x, 120)
    return x * env_adsr(len(x), 0.001, 0.2, 0.8, 0.15)


def glock(f, dur=0.9):
    return bell(f, dur, partials=((1, 1.0, 1.0), (2.76, 0.35, 0.35), (5.4, 0.12, 0.18), (8.93, 0.05, 0.1)),
                tau=0.35)


def whistle(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.6 * t) * np.clip(t / 0.15, 0, 1)
    x = sine(f * vib, n) + 0.06 * sine(2 * f * vib, n)
    x += bp(rng.standard_normal(n), f * 0.8, min(f * 1.6, 20000)) * 0.05
    return x * env_adsr(n, 0.025, 0.05, 0.85, 0.06)


def pad(freqs, dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for d in (-0.004, 0.0, 0.004):
            x += sine(f * (1 + d), n) + 0.3 * sine(2 * f * (1 + d), n)
    x *= 1 + 0.12 * np.sin(2 * np.pi * 4.2 * t)
    return x * env_adsr(n, 0.08, 0.2, 0.8, 0.25) * gain / (len(freqs) * 3)


def strings(f, dur, attack=0.25, release=0.5, voices=5, cutoff=2600, vib=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for v in range(voices):
        det = 1 + (v - (voices - 1) / 2) * 0.0035
        vb = 1 + (0.0035 * np.sin(2 * np.pi * (5.0 + 0.3 * v) * t + v) if vib else 0)
        x += saw(f * det * vb, n, phase=rng.uniform(0, 6))
    x = lp(x / voices, cutoff, order=2)
    return x * env_adsr(n, attack, 0.1, 0.9, release)


def spiccato(f, dur=0.22):
    n = int(dur * SR)
    x = np.zeros(n)
    for v in range(4):
        x += saw(f * (1 + (v - 1.5) * 0.004), n, phase=rng.uniform(0, 6))
    x = lp(x / 4, 3200, order=2)
    return x * env_adsr(n, 0.008, 0.08, 0.35, 0.06)


def brass(f, dur, bright=2200, attack=0.04, scoop=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    pitch = f * (1 - 0.02 * np.exp(-t / 0.04)) if scoop else np.full(n, f)
    pitch = pitch * (1 + 0.003 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.3, 0, 1))
    x = np.zeros(n)
    for d in (-0.003, 0.0, 0.003):
        x += saw(pitch * (1 + d), n)
    fc = 350 + bright * (0.55 + 0.45 * np.exp(-t / 0.18)) * np.clip(t / attack, 0, 1)
    x = tv_lowpass(x / 3, fc)
    x = tv_lowpass(x, fc * 1.4)
    return x * env_adsr(n, attack, 0.15, 0.8, 0.12)


def choir(freqs, dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    src = np.zeros(n)
    for f in freqs:
        for v in range(4):
            vb = 1 + 0.005 * np.sin(2 * np.pi * (4.8 + 0.4 * v) * t + v)
            src += saw(f * (1 + (v - 1.5) * 0.003) * vb, n, phase=rng.uniform(0, 6))
    src /= max(1, len(freqs) * 4)
    y = bp(src, 650, 900, order=2) * 1.0 + bp(src, 1050, 1300, order=2) * 0.6 + bp(src, 2500, 2900, order=2) * 0.25
    y += bp(rng.standard_normal(n), 600, 3000) * 0.02
    return y * env_adsr(n, 0.5, 0.2, 0.85, 0.8) * gain


def taiko(gain=1.0):
    n = int(0.9 * SR)
    f = 52 + 70 * np.exp(-np.arange(n) / SR / 0.05)
    x = sine(f, n) * env_exp(n, 0.32, 0.001)
    x += bp(rng.standard_normal(n), 150, 900) * env_exp(n, 0.035, 0.0005) * 0.6
    return x * gain


def timpani(f, gain=1.0, dur=1.6):
    n = int(dur * SR)
    fp = f * (1 + 0.03 * np.exp(-np.arange(n) / SR / 0.05))
    x = np.zeros(n)
    for r, a, tau in [(1, 1.0, 0.9), (1.5, 0.5, 0.6), (1.98, 0.35, 0.5), (2.44, 0.2, 0.35)]:
        x += a * sine(fp * r, n) * env_exp(n, tau, 0.002)
    x += bp(rng.standard_normal(n), 100, 800) * env_exp(n, 0.03, 0.0005) * 0.4
    return x * gain


def chord_tones(root_name, quality, octave=4):
    root = nm(root_name + str(octave))
    ints = {"maj": [0, 4, 7], "min": [0, 3, 7]}[quality]
    return [root + i for i in ints]


# ----------------------------------------------------------------- 1. jingle

def jingle():
    bpm = 124
    beat = 60 / bpm
    bar = beat * 4
    e8 = beat / 2
    prog = [("D", "maj"), ("A", "maj"), ("B", "min"), ("G", "maj"), ("D", "maj"), ("A", "maj"), ("G", "maj"),
            ("A", "maj"), ("D", "maj"), ("A", "maj"), ("B", "min"), ("G", "maj"), ("E", "min"), ("A", "maj"),
            ("D", "maj"), ("A", "maj")]
    mel = {
        0: [("F#5", 0, 1), ("A5", 1, 1), ("D6", 2, 2), ("A5", 4, 1), ("B5", 5, 1), ("A5", 6, 2)],
        1: [("E5", 0, 1), ("A5", 1, 1), ("C#6", 2, 2), ("B5", 4, 1), ("A5", 5, 1), ("E5", 6, 2)],
        2: [("F#5", 0, 1), ("B5", 1, 1), ("D6", 2, 2), ("C#6", 4, 1), ("B5", 5, 1), ("F#5", 6, 2)],
        3: [("G5", 0, 1), ("B5", 1, 1), ("D6", 2, 1), ("E6", 3, 1), ("D6", 4, 2), ("B5", 6, 1), ("A5", 7, 1)],
        5: [("E5", 0, 1), ("A5", 1, 1), ("C#6", 2, 1), ("E6", 3, 1), ("D6", 4, 1), ("C#6", 5, 1), ("A5", 6, 2)],
        6: [("B5", 0, 1), ("D6", 1, 1), ("G6", 2, 2), ("F#6", 4, 1), ("E6", 5, 1), ("D6", 6, 1), ("B5", 7, 1)],
        7: [("C#6", 0, 2), ("E6", 2, 2), ("A6", 4, 4)],
        12: [("G5", 0, 1), ("B5", 1, 1), ("E6", 2, 2), ("D6", 4, 1), ("B5", 5, 1), ("G5", 6, 2)],
        13: [("A5", 0, 1), ("C#6", 1, 1), ("E6", 2, 2), ("G6", 4, 2), ("E6", 6, 2)],
        14: [("F#6", 0, 2), ("D6", 2, 1), ("A5", 3, 1), ("F#5", 4, 2), ("A5", 6, 2)],
        15: [("E5", 0, 1), ("A5", 1, 1), ("C#6", 2, 1), ("E6", 3, 1), ("A6", 4, 4)],
    }
    mel[4] = mel[0]
    for k in range(8, 12):
        mel[k] = mel[k - 8]

    total = bar * 16 + 2.5
    drums = silence(total)
    bass = silence(total)
    plucks = silence(total)
    lead = silence(total)
    pads = silence(total)

    drums = place(drums, crash(2.4), 0.0, 0.45)
    drums = place(drums, crash(2.4), bar * 8, 0.35)
    for b, (root, q) in enumerate(prog):
        t0 = b * bar
        # drums
        for k in range(4):
            drums = place(drums, kick(), t0 + k * beat, 0.75)
            if k in (1, 3):
                drums = place(drums, pan(clap(), 0.05), t0 + k * beat, 0.55)
        for k in range(8):
            drums = place(drums, pan(hat(open_=(k % 2 == 1 and k == 7)), 0.35), t0 + k * e8 + (0.0 if k % 2 == 0 else 0.012),
                          0.22 if k % 2 == 0 else 0.32)
        # bass: root/octave bounce in 8ths
        rm = nm(root + "2")
        if rm < nm("C#2"):
            rm += 12
        for k in range(8):
            f = midi(rm + (12 if k % 2 == 1 else 0))
            bass = place(bass, synth_bass(f, e8 * 0.9), t0 + k * e8, 0.55 if k % 2 == 0 else 0.4)
        # ukulele-ish strum: D . D U . U D U
        tones = chord_tones(root, q, 4)
        voicing = [tones[0], tones[1], tones[2], tones[0] + 12]
        for step, direction, g in [(0, 1, 1.0), (2, 1, 0.8), (3, -1, 0.6), (5, -1, 0.6), (6, 1, 0.8), (7, -1, 0.6)]:
            order = voicing if direction == 1 else voicing[::-1]
            for i, m in enumerate(order):
                plucks = place(plucks, pan(pluck(midi(m), 0.9), -0.3 + 0.2 * i), t0 + step * e8 + i * 0.011, 0.22 * g)
        # soft pad under everything
        pads = place(pads, hp(pad([midi(m) for m in chord_tones(root, q, 4)], bar + 0.2), 220), t0, 0.5)
        # melody: glockenspiel an octave up, whistle doubling in second half
        for name, st, ln in mel.get(b, []):
            f = midi(nm(name))
            lead = place(lead, pan(glock(f * 2, 0.9), 0.15), t0 + st * e8, 0.42)
            if b >= 8:
                lead = place(lead, pan(whistle(f, ln * e8 * 0.95), -0.15), t0 + st * e8, 0.3)

    mix = drums * 0.9 + bass * 0.9 + plucks * 1.35 + lead * 1.0 + pads * 1.0
    mix = mix[: len(drums)]
    mix = peaking(hp(mix, 35, order=2), 600, 0.8, 2.0)
    mix = reverb(mix, wet=0.14, dur=1.1, damp_hz=7000)
    mix = soft_clip(normalize(mix, -2.0) * 1.15, 1.2)
    cue = {"bpm": bpm, "bar_sec": bar, "bars": 16, "length_sec": bar * 16}
    return mix, cue


# ----------------------------------------------------------------- 2. epic

def epic():
    bpm = 96
    beat = 60 / bpm
    bar = beat * 4
    e8 = beat / 2
    # (root midi for bass, chord tones for pads)
    secA = [("D", "min"), ("Bb", "maj"), ("G", "min"), ("A", "maj")]
    secB = [("D", "min"), ("Bb", "maj"), ("F", "maj"), ("C", "maj")]
    secC = [("Bb", "maj"), ("C", "maj"), ("D", "min"), ("D", "min"), ("Bb", "maj"), ("C", "maj"), ("F", "maj"), ("A", "maj")]
    plan = [("A", c) for c in secA] + [("B", c) for c in secB] + [("C", c) for c in secC]
    nbars = len(plan)
    total = bar * nbars + 4.0
    low = silence(total)
    hi = silence(total)
    perc = silence(total)
    brs = silence(total)
    chr_ = silence(total)

    horn_A = [("D4", 0, 3), ("A4", 3, 1), ("F4", 4, 2), ("G4", 6, 2),  # bar1 (8ths)
              ("F4", 8, 2), ("D4", 10, 2), ("Bb3", 12, 4),
              ("G3", 16, 2), ("Bb3", 18, 2), ("D4", 20, 3), ("C4", 23, 1),
              ("C#4", 24, 4), ("E4", 28, 4)]
    theme_C = [("F4", 0, 3), ("Bb4", 3, 1), ("D5", 4, 4),
               ("C5", 8, 3), ("E5", 11, 1), ("G5", 12, 4),
               ("F5", 16, 6), ("E5", 22, 2),
               ("D5", 24, 8),
               ("D5", 32, 3), ("F5", 35, 1), ("Bb5", 36, 4),
               ("A5", 40, 3), ("G5", 43, 1), ("E5", 44, 4),
               ("F5", 48, 4), ("A5", 52, 4),
               ("A5", 56, 8)]

    for b, (sec, (root, q)) in enumerate(plan):
        t0 = b * bar
        rmid = nm(root + "2")
        if rmid > nm("E2"):
            rmid -= 12
        tones3 = chord_tones(root, q, 3)
        # low string ostinato (16th-ish galloping 8ths)
        pattern = [0, 0, 12, 0, 0, 12, 0, 7] if sec != "A" else [0, 0, 0, 3 if q == "min" else 4, 0, 0, -2, 0]
        for k, iv in enumerate(pattern):
            f = midi(rmid + 12 + iv)
            low = place(low, pan(spiccato(f, e8 * 0.95), -0.3), t0 + k * e8, 0.5 if k % 4 == 0 else 0.38)
        # sustained basses
        low = place(low, strings(midi(rmid), bar + 0.4, attack=0.2, release=0.6, cutoff=900), t0, 0.2)
        # taiko pattern
        for k, g in [(0, 1.0), (2, 0.7), (3.5, 0.5), (3.75, 0.55)] if sec == "A" else [(0, 1.0), (1, 0.6), (2, 0.9), (3, 0.6), (3.5, 0.5), (3.75, 0.6)]:
            perc = place(perc, hp(taiko(), 40, order=2), t0 + k * beat, 0.42 * g)
        if sec == "A":
            # airy high-string tremolo keeps the adventure section from sounding muddy
            trem = sum_strings([m + 12 for m in tones3], bar + 0.5)
            tt = np.arange(len(trem)) / SR
            trem = trem * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 6.4 * tt)))[:, None]
            hi = place(hi, trem, t0, 0.2)
        if sec in ("B", "C"):
            # high strings sustained chord + choir
            hi = place(hi, sum_strings(tones3, bar + 0.5), t0, 0.32 if sec == "B" else 0.42)
            chr_ = place(chr_, choir([midi(m) for m in chord_tones(root, q, 4)], bar + 0.6), t0, 0.5 if sec == "B" else 0.7)
            # brass stabs on 1 and the "and" of 2
            for st, ln in ([(0, 1.5), (3, 1.0)] if sec == "B" else [(0, 3.5)]):
                for m in chord_tones(root, q, 3):
                    brs = place(brs, pan(brass(midi(m), ln * beat, bright=1500), rng.uniform(-0.4, 0.4)), t0 + st * e8, 0.18)
            perc = place(perc, timpani(midi(rmid + 12)), t0, 0.6)
        if sec == "C" and b % 4 == 0:
            perc = place(perc, crash(3.0), t0, 0.5)

    # horn melody section A (8th grid from bar 0)
    for name, st, ln in horn_A:
        brs = place(brs, pan(brass(midi(nm(name)), ln * e8 * 0.98, bright=2000, attack=0.06), 0.2), st * e8, 0.8)
    # big theme section C (starts at bar 8)
    c0 = 8 * bar
    for name, st, ln in theme_C:
        f = midi(nm(name))
        brs = place(brs, pan(brass(f, ln * e8 * 0.98, bright=2400, attack=0.05), 0.1), c0 + st * e8, 0.6)
        brs = place(brs, pan(brass(f / 2, ln * e8 * 0.98, bright=1400, attack=0.05), -0.2), c0 + st * e8, 0.35)
        hi = place(hi, pan(strings(f * 2, ln * e8, attack=0.05, release=0.25, voices=4, cutoff=4500), 0.3), c0 + st * e8, 0.18)
    # timpani roll into section C
    roll_t = 8 * bar - beat * 2
    for k in range(16):
        perc = place(perc, timpani(midi(nm("A2")), dur=0.5), roll_t + k * beat / 8, 0.12 + 0.03 * k)
    # cymbal swell into C
    n = int(beat * 2 * SR)
    sw = hp(rng.standard_normal(n), 3000) * np.linspace(0, 1, n) ** 3
    perc = place(perc, pan(sw, 0.0), 8 * bar - beat * 2, 0.35)
    # final hit
    end_t = nbars * bar
    perc = place(perc, timpani(midi(nm("D2")), dur=3.0), end_t, 1.0)
    perc = place(perc, crash(3.5), end_t, 0.7)
    for m in chord_tones("D", "maj", 3):
        brs = place(brs, brass(midi(m), 2.2, bright=2600), end_t, 0.25)

    L = max(len(x) for x in (low, hi, perc, brs, chr_))
    pad_ = lambda x: np.pad(x, ((0, L - len(x)), (0, 0)))
    mix = pad_(low) * 1.0 + pad_(hi) * 1.0 + pad_(perc) * 0.85 + pad_(brs) * 1.15 + pad_(chr_) * 0.9
    mix = peaking(hp(mix, 32, order=2), 2800, 0.7, 4.0)
    mix = reverb(mix, wet=0.32, dur=2.6, damp_hz=5500, predelay=0.025)
    mix = soft_clip(normalize(mix, -2.0) * 1.2, 1.3)
    cue = {"bpm": bpm, "bar_sec": bar, "bars": nbars, "sections": {"A_adventure": 0.0, "B_build": 4 * bar,
                                                                    "C_epic": 8 * bar, "final_hit": end_t}}
    return mix, cue


def sum_strings(midis, dur):
    out = None
    for i, m in enumerate(midis):
        s = pan(strings(midi(m + 12), dur, attack=0.35, release=0.6, cutoff=3200), -0.5 + 0.5 * i)
        out = s if out is None else out + s
    return out / len(midis)


# ----------------------------------------------------------------- 3. fanfare

def fanfare():
    beat = 60 / 120
    trip = beat / 3
    total = 3.6
    out = silence(total)
    top = ["F4", "F4", "F4", "Bb4"]
    mid = ["D4", "D4", "D4", "F4"]
    low = ["Bb3", "Bb3", "Bb3", "D4"]
    times = [0.0, trip, 2 * trip, beat]
    lens = [trip * 0.85, trip * 0.85, trip * 0.85, 1.9]
    for line, g, p in [(top, 0.55, 0.15), (mid, 0.4, -0.1), (low, 0.35, -0.3)]:
        for name, t, ln in zip(line, times, lens):
            out = place(out, pan(brass(midi(nm(name)), ln, bright=3200, attack=0.02), p), t, g)
    out = place(out, timpani(midi(nm("Bb2")), dur=2.5), beat, 0.45)
    out = place(out, crash(2.8), beat, 0.3)
    for k in range(10):  # snare-ish roll before the hit
        n = int(0.05 * SR)
        s = bp(rng.standard_normal(n), 1500, 6000) * env_exp(n, 0.012)
        out = place(out, s, k * beat / 10, 0.1 + 0.03 * k)
    out = reverb(out, wet=0.3, dur=2.2, damp_hz=6000)
    return soft_clip(normalize(out, -2.0) * 1.1, 1.2)


if __name__ == "__main__":
    cues = {}
    j, cues["jingle_commercial"] = jingle()
    write(os.path.join(OUT, "jingle_commercial.wav"), fade(j, 0.0, 1.5), peak_db=-1.0)
    print("jingle", round(len(j) / SR, 2))
    e, cues["epic_adventure"] = epic()
    write(os.path.join(OUT, "epic_adventure.wav"), fade(e, 0.0, 2.0), peak_db=-1.0)
    print("epic", round(len(e) / SR, 2))
    f = fanfare()
    write(os.path.join(OUT, "fanfare_victory.wav"), fade(f, 0.0, 0.8), peak_db=-1.0)
    print("fanfare", round(len(f) / SR, 2))
    with open(os.path.join(OUT, "cue_map.json"), "w") as fh:
        json.dump(cues, fh, indent=2)
