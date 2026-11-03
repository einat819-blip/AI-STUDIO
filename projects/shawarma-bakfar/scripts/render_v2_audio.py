# -*- coding: utf-8 -*-
"""V2 soundtrack in three modes, frame-synced to edl_v2.py.

 1. comic mystery  (0 - 3.0 s)  engine, brakes, time-stop hits, short silences
 2. appetite        (3.0 - 9.5)  original darbuka-pop groove + grill/knife/meat/tahini
 3. studio twist    (9.5 - 15)   music snaps off, comic thump, happy new track

All music and designed SFX are synthesised here (original, no samples).
Ambience comes from the delivered clips' own audio, cut in sync.

python3 render_v2_audio.py --version client|studio --sources DIR --outdir DIR
"""
import argparse
import os

import numpy as np

import edl_v2 as E
import render_audio as A
from render_audio import (BEAT, NOTE, SR, Bus, bp, crash, db, doum, fade, hp, kick, lp, n, noise,
                          pluck, reverb, reverb_ir, sub_boom, tek, tvec)

T = A.T


# ------------------------------------------------------------ new SFX -----
def tahini_pour(dur=1.6):
    """thick, glossy pour: gloopy low-mid noise + small 'blubs'."""
    t = tvec(dur)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (7 + 3 * np.sin(2 * np.pi * 0.8 * t)) * t)
    body = bp(noise(dur), 160, 1100) * lfo
    blubs = np.zeros(len(t))
    for t0 in np.sort(A.RNG.uniform(0.05, dur - 0.1, 9)):
        f = A.RNG.uniform(170, 300)
        tt = tvec(0.08)
        b = np.sin(2 * np.pi * (f + 400 * tt) * tt) * np.exp(-tt / 0.02)
        i = n(t0)
        blubs[i:i + len(b)] += b[: len(blubs) - i] * 0.5
    env = np.clip(t / 0.06, 0, 1) * np.clip((dur - t) / 0.3, 0, 1)
    return (0.5 * body + blubs) * env


def meat_drop():
    """slices landing in the pita: soft thud + short sizzle."""
    d = 0.35
    t = tvec(d)
    thud = np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.035) + bp(noise(d), 250, 1600) * np.exp(-t / 0.018) * 0.5
    sizz = hp(noise(d), 3000) * np.exp(-t / 0.12) * 0.15
    return thud + sizz


def comic_thump():
    """'זה עבד.' - fat boom + slap + woodblock tok."""
    d = 0.7
    t = tvec(d)
    f = 38 + 95 * np.exp(-t / 0.045)
    boom = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22))
    slap = bp(noise(d), 900, 6000) * np.exp(-t / 0.012)
    tok = (np.sin(2 * np.pi * 640 * t) + 0.6 * np.sin(2 * np.pi * 1010 * t)) * np.exp(-t / 0.045)
    return 0.95 * boom + 0.6 * slap + 0.35 * tok


def riser(dur=0.5):
    t = tvec(dur)
    env = (t / dur) ** 2.2
    f = 300 * (5.0 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    air = hp(noise(dur), 1500) * 0.6
    return (tone + air) * env


def whoosh(dur=0.3):
    t = tvec(dur)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return bp(noise(dur), 500, 7000) * env


def pop():
    d = 0.12
    t = tvec(d)
    f = 520 + 600 * (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03) + hp(noise(d), 4000) * np.exp(-t / 0.003) * 0.3


def blip():
    """friendly two-note message blip (generic, not any app's sound)."""
    out = np.zeros(n(0.3))
    for off, fq in ((0.0, 1174.66), (0.07, 1567.98)):
        t = tvec(0.2)
        s = (np.sin(2 * np.pi * fq * t) + 0.25 * np.sin(4 * np.pi * fq * t)) * np.exp(-t / 0.06)
        i = n(off)
        out[i:i + len(s)] += s
    return out * 0.6


def slowmo_bed(sources, dur):
    """hero slow-mo: the shot's own sizzle, played at slow-mo speed (pitched down)."""
    x = A.load_audio(os.path.join(sources, E.SRC["food"]), 9.0, 1.0)
    x = lp(x.T, 6000).T
    m = n(dur)
    pos = np.linspace(0, len(x) - 1, m)
    y = np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1)
    g = db(-27) / max(A.rms(y), 1e-6)
    return fade(y * g, 0.01, 0.2)


# --------------------------------------------------------------- music ----
def shawarma_groove(dur, start, end, final):
    """darbuka-pop in D Hijaz (from render_audio), with or without the final button."""
    if final:
        return A.music(dur, start, end)
    # groove that keeps running until `end` (it gets snapped off by the twist)
    bus = Bus(dur)
    perc = Bus(dur)
    ir = reverb_ir(0.9, 5000)
    beats = int(round((end - start) / BEAT)) + 1
    for b in range(beats):
        tb = start + b * BEAT
        bp_ = b % 4
        if bp_ in (0, 2):
            bus.add(kick(), tb, -3)
            perc.add(doum(), tb, -6, pan=-0.1)
        if bp_ == 1:
            bus.add(kick(), tb + BEAT / 2, -6)
        if bp_ in (1, 3):
            perc.add(A.clap(), tb, -7, width=0.4)
            perc.add(tek(0.6), tb + 3 * BEAT / 4, -14, pan=0.3)
        perc.add(tek(0.9), tb + BEAT / 2, -9, pan=0.25)
        for k in range(4):
            perc.add(A.shaker(1.0 if k % 2 else 0.55), tb + k * BEAT / 4, -20, pan=0.45)
        for k in range(2):
            note = A.BASS[(bp_ * 2 + k) % 8]
            if note:
                bus.add(A.bass_note(NOTE[note], BEAT / 2 * 0.92), tb + k * BEAT / 2, -9)
    rep = 0
    while start + rep * 8 * BEAT < end:
        for off, note, ln in A.RIFF:
            t0 = start + (rep * 8 + off) * BEAT
            if t0 < end:
                perc.add(pluck(NOTE[note], ln * BEAT + 0.25, 0.55), t0, -8, pan=-0.2, width=0.3)
        rep += 1
    bus.add(crash(), start, -10, width=0.6)
    bus.add(sub_boom(0.9, 50), start, -10)
    out = bus.buf + reverb(perc.buf, ir, 0.18)
    from scipy import signal
    out = signal.sosfilt(signal.butter(2, 45, btype="high", fs=SR, output="sos"), out, axis=0)
    return np.tanh(1.4 * out) / 1.4


HN = {"D2": 73.42, "G2": 98.0, "A2": 110.0, "D4": 293.66, "F#4": 369.99, "A4": 440.0, "G4": 392.0,
      "B4": 493.88, "D5": 587.33, "C#5": 554.37, "E5": 659.25, "F#5": 739.99, "A5": 880.0, "B5": 987.77,
      "D6": 1174.66}
CHORDS = {"D": ("D4", "F#4", "A4"), "G": ("G4", "B4", "D5"), "A": ("A4", "C#5", "E5")}
HAPPY_RIFF = [(0.0, "A5", 0.25), (0.25, "B5", 0.25), (0.5, "D6", 0.5),
              (1.0, "B5", 0.25), (1.25, "A5", 0.25), (1.5, "F#5", 0.5)]


def happy_track(dur, start, final_hit):
    """bright, happy four-on-the-floor in D major for the studio part."""
    bus = Bus(dur)
    perc = Bus(dur)
    ir = reverb_ir(0.8, 6500, seed=5)
    beats = int(round((final_hit - start) / BEAT))
    prog = ["D", "D", "G", "G", "A", "A", "A", "A"]
    roots = {"D": "D2", "G": "G2", "A": "A2"}
    for b in range(beats):
        tb = start + b * BEAT
        last = b == beats - 1
        ch = prog[b % len(prog)]
        bus.add(kick(), tb, -3)
        if b % 2 == 1:
            perc.add(A.clap(), tb, -6, width=0.5)
        perc.add(A.shaker(1.0), tb + BEAT / 2, -13, pan=0.3)  # open off-beat hat
        for k in range(4):
            perc.add(A.shaker(0.8 if k % 2 else 0.4), tb + k * BEAT / 4, -21, pan=-0.35)
        r = HN[roots[ch]]
        bus.add(A.bass_note(r, BEAT / 2 * 0.9), tb, -9)
        bus.add(A.bass_note(r * 2, BEAT / 2 * 0.9), tb + BEAT / 2, -11)
        for i, nt in enumerate(CHORDS[ch]):   # off-beat chord stab
            perc.add(pluck(HN[nt], 0.32, 0.8, 0.993), tb + BEAT / 2 + i * 0.008, -15, pan=0.25 - 0.25 * i)
        if last:  # clap roll into the button
            for k in range(4):
                perc.add(A.clap(), tb + k * BEAT / 4, -14 + 3 * k)
    rep = 0
    while start + rep * 2 * BEAT < final_hit - BEAT:
        for off, nt, ln in HAPPY_RIFF:
            t0 = start + (rep * 2 + off) * BEAT
            if t0 < final_hit - BEAT:
                perc.add(pluck(HN[nt], ln * BEAT + 0.2, 0.85, 0.994), t0, -12, pan=-0.15, width=0.3)
        rep += 1
    # drop + final button
    bus.add(crash(), start, -9, width=0.6)
    bus.add(sub_boom(0.8, 55), start, -10)
    for i, nt in enumerate(("D4", "F#4", "A4", "D5", "F#5")):
        perc.add(pluck(HN[nt], 0.9, 0.85, 0.996), final_hit + i * 0.012, -9, pan=-0.3 + 0.15 * i)
    bus.add(kick(), final_hit, -4)
    bus.add(sub_boom(0.6, 50), final_hit, -10)
    bus.add(crash(0.9), final_hit, -9, width=0.6)
    out = bus.buf + reverb(perc.buf, ir, 0.16)
    from scipy import signal
    out = signal.sosfilt(signal.butter(2, 45, btype="high", fs=SR, output="sos"), out, axis=0)
    out = np.tanh(1.4 * out) / 1.4
    e = n(dur)
    out[e - n(0.07):e] *= np.linspace(1, 0, n(0.07))[:, None]
    return out


# ------------------------------------------------------------ assemble ----
def build(version, sources):
    V = E.VERSIONS[version]
    S = V["sync"]
    dur = T(V["frames"])
    st = dict(zip([s["name"] for s in E.AD], E.starts(E.AD)))
    seg = {s["name"]: s for s in E.AD}
    sfx = Bus(dur)
    room = reverb_ir(0.35, 6000, seed=11)

    # ---- MODE 1: comic mystery -----------------------------------------
    tf = T(S["freeze_tractor"])
    tb_ = T(S["brake"])
    tr = Bus(tf + 0.4)
    hs = seg["hook_drive"]["frames"]
    # the take's own audio (engine, then its brake squeal ~1.2 s), in sync with picture
    x = A.load_audio(os.path.join(sources, E.SRC["tractor_new"]), T(hs[0]), T(len(hs)) + 0.35)
    x *= db(-18) / max(A.rms(x), 1e-6)
    x *= min(1.0, db(-8) / max(np.abs(x).max(), 1e-9))
    tr.add(fade(x, 0.003, 0.006), 0.0)
    eng = A.engine_layer(tf + 0.4) * 0.5
    eng[n(tb_):] *= np.linspace(1.0, 0.35, len(eng) - n(tb_))   # engine bogs down under braking
    tr.add(eng, 0.0, -7)
    tr.add(A.brake_screech(tf - tb_ + 0.35), tb_, -4, pan=0.15, width=0.3)      # loud screech from the brake
    sfx.add(A.tape_stop(tr.buf, tf, 0.14), 0.0)
    sfx.add(A.air_suck(0.12), tf - 0.12, -12, width=0.5)
    sfx.add(reverb(A.stereo(A.freeze_hit()), room, 0.25), tf, -2)               # thump on the stop

    ts, tfz = T(S["cut_soccer"]), T(S["freeze_soccer"])
    x = A.load_audio(os.path.join(sources, E.SRC["soccer"]), 0.05, tfz - ts + 0.3)
    x *= db(-20) / max(A.rms(x), 1e-6)
    x *= min(1.0, db(-9) / max(np.abs(x).max(), 1e-9))
    sb = Bus(dur)
    sb.add(fade(x, 0.002, 0.01), ts)
    sfx.add(A.tape_stop(sb.buf, tfz, 0.13), 0.0)
    sfx.add(A.air_suck(0.12), tfz - 0.12, -12, width=0.5)
    sfx.add(reverb(A.stereo(A.freeze_hit()), room, 0.25), tfz, -4)

    tc, tcf = T(S["cut_coffee"]), T(S["freeze_coffee"])
    x = hp(A.src_audio_for_segment(sources, seg["coffee_pour"], extra=0.3).T, 150).T
    cb = Bus(dur)
    cb.add(fade(x, 0.003, 0.01), tc)
    sfx.add(A.tape_stop(cb.buf, tcf, 0.11), 0.0)
    for i, tt in enumerate((tc + 0.01, tc + 0.17)):
        sfx.add(A.clock_tick("tick" if i == 0 else "tock"), tt, -10, pan=0.1)
    sfx.add(reverb(A.stereo(A.clock_stop()), room, 0.2), tcf, -8, pan=0.1)
    # -> silence until the hard cut at 3.0

    # ---- MODE 2: appetite ------------------------------------------------
    td = T(S["drop"])
    sfx.add(A.fire_flare(), td, -4, width=0.6)
    sfx.add(sub_boom(0.6, 60), td, -9)
    for nm in ("spit", "cutting", "into_pita", "tahini"):
        x = A.src_audio_for_segment(sources, seg[nm])
        sfx.add(fade(x, 0.004, 0.006), T(st[nm]))
    sfx.add(A.knife_slice(0.42), T(S["knife_wide"]), -6, pan=-0.15, width=0.3)
    sfx.add(A.knife_shing(), T(S["cutting"]), -7, pan=0.1, width=0.3)
    sfx.add(A.crunch(0.2), T(S["cutting"]) + 0.02, -5)
    sfx.add(A.knife_slice(0.32), T(S["cutting"]) + 0.3, -9, pan=-0.1)
    for k, off in enumerate((0.0, 0.09, 0.2)):
        sfx.add(meat_drop(), T(S["into_pita"]) + off, -6 - 2 * k, pan=0.1 * (k - 1))
    sfx.add(tahini_pour(1.7), T(S["tahini"]), -11, width=0.3)
    th = T(S["hero"])
    sfx.add(slowmo_bed(sources, T(S["end"] if not V["twist"] else E.TWIST_START) - th), th)
    sfx.add(A.logo_pop(), T(S["logo"]), -7)

    if not V["twist"]:
        mus = shawarma_groove(dur, td, T(S["final_hit"]), final=True)
        mus *= db(-3)
        ramp = np.ones(len(sfx.buf))
        lg = n(T(S["logo"]))
        ramp[lg:] = np.maximum(0.3, np.exp(-np.arange(len(ramp) - lg) / (0.3 * SR)))
        sfx.buf *= ramp[:, None]
        e = n(0.06)
        sfx.buf[-e:] *= np.linspace(1, 0, e)[:, None]
        return sfx.buf, mus

    # ---- MODE 3: studio twist -------------------------------------------
    tw = T(S["twist"])
    groove = shawarma_groove(dur, td, tw, final=False)
    groove[n(tw + 0.25):] = 0
    groove = A.tape_stop(groove, tw, 0.12)           # music snaps off at 9.5
    sfx.buf[n(tw):] = 0                               # world goes silent with the freeze
    sfx.add(reverb(A.stereo(A.freeze_hit()), room, 0.3), tw, -2)
    sfx.add(comic_thump(), T(S["it_worked"]), -4)
    sfx.add(riser(T(S["studio_drop"]) - T(S["riser"])), T(S["riser"]), -10, width=0.5)
    # wipe whoosh travels right -> left with the colour bands
    wh = whoosh(0.28)
    pan = np.linspace(0.7, -0.7, len(wh))
    sfx.add(np.stack([wh * np.cos((pan + 1) * np.pi / 4), wh * np.sin((pan + 1) * np.pi / 4)], 1) * 1.4,
            T(S["wipe"]), -6)
    sfx.add(pop(), T(S["q2"]), -12)
    sfx.add(A.air_suck(0.22), T(S["studio_logo"]) - 0.22, -8, width=0.6)
    sfx.add(sub_boom(0.5, 60), T(S["studio_logo"]), -10)
    sfx.add(whoosh(0.22), T(S["tagline"]), -18, width=0.4)
    sfx.add(pop(), T(S["cta"]), -11)
    for wv in S["wiggles"]:
        sfx.add(blip(), T(wv), -13, pan=-0.2)
    happy = happy_track(dur, T(S["studio_drop"]), T(S["studio_final"]))
    mus = groove * db(-3) + happy * db(-3)
    e = n(0.05)
    sfx.buf[-e:] *= np.linspace(1, 0, e)[:, None]
    return sfx.buf, mus


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", choices=list(E.VERSIONS), required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    sfx, mus = build(a.version, a.sources)
    mix = A.master(sfx + mus, -14.0)
    _, tp = A.lufs(mix)
    if tp > -1.0:  # inter-sample overs: trade a few tenths of LUFS for a clean -1 dBTP
        mix *= db(-1.1 - tp)
    pre = os.path.join(a.outdir, a.version)
    A.write_wav(pre + "_mix.wav", mix)
    A.write_wav(pre + "_sfx_stem.wav", sfx * 0.5)
    A.write_wav(pre + "_music_stem.wav", mus * 0.5)
    I, tp = A.lufs(mix)
    print(f"{a.version}: {I:.1f} LUFS, true peak {tp:.1f} dBTP, {len(mix) / SR:.3f}s")
