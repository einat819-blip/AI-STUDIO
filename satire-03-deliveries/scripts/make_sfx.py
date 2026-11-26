"""Generate the original SFX library for "משלוחים לכל חלקי הארץ*".

Run:  python3 scripts/make_sfx.py
Writes 24-bit 48 kHz WAVs to assets/sfx/.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from audiolib import *  # noqa

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x, peak=-1.0):
    write(os.path.join(OUT, name + ".wav"), fade(to_stereo(x), 0.0005, 0.02), peak_db=peak)
    print("sfx", name, round(len(x) / SR, 2), "s")


# 1. Mouse/trackpad click: press + release
def click():
    out = silence(0.15)
    for t0, g, f in [(0.0, 1.0, 3800), (0.055, 0.55, 3200)]:
        n = int(0.012 * SR)
        x = bp(rng.standard_normal(n), 1800, 7000) * env_exp(n, 0.0015, 0.0002)
        x += 0.5 * sine(f, n) * env_exp(n, 0.002, 0.0002)
        out = place(out, x, t0, g)
    return out


# 2. Order confirmed chime: two soft bell notes upward
def order_confirm():
    out = silence(1.2)
    out = place(out, bell(midi(88), 1.0, tau=0.35), 0.0, 0.8)   # E6
    out = place(out, bell(midi(95), 1.0, tau=0.45), 0.09, 0.9)  # B6
    return reverb(out, wet=0.18, dur=0.9)


# 3. Success ding: quick upward marimba arpeggio
def success_ding():
    out = silence(0.9)
    for i, m in enumerate([nm("C6"), nm("E6"), nm("G6"), nm("C7")]):
        n = int(0.5 * SR)
        x = sine(midi(m), n) * env_exp(n, 0.12, 0.001) + 0.25 * sine(midi(m) * 4, n) * env_exp(n, 0.03, 0.001)
        out = place(out, pan(x, -0.2 + 0.13 * i), 0.055 * i, 0.7)
    return reverb(out, wet=0.15, dur=0.8)


# 4. Cash register "ka-ching"
def cash_register():
    out = silence(1.6)
    # key clack
    n = int(0.04 * SR)
    clack = bp(rng.standard_normal(n), 300, 2500) * env_exp(n, 0.006, 0.0003)
    out = place(out, clack, 0.0, 0.9)
    # drawer roll with rattle
    n = int(0.2 * SR)
    roll = bp(rng.standard_normal(n), 250, 1800) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * np.arange(n) / SR)))
    roll *= env_adsr(n, 0.01, 0.05, 0.6, 0.08)
    out = place(out, roll, 0.05, 0.45)
    # the bell "ching"
    b = bell(2350, 1.4, partials=((1, 1.0, 1.0), (1.5, 0.5, 0.7), (2.0, 0.35, 0.6), (2.76, 0.4, 0.5),
                                   (3.9, 0.2, 0.35), (5.1, 0.12, 0.25)), tau=0.55, detune=0.004)
    out = place(out, pan(b, 0.1), 0.13, 0.85)
    # coins
    for k in range(7):
        n = int(0.12 * SR)
        f = rng.uniform(4200, 7800)
        c = sine(f, n) * env_exp(n, 0.025, 0.0005) + 0.4 * sine(f * 1.47, n) * env_exp(n, 0.015, 0.0005)
        out = place(out, pan(c, rng.uniform(-0.5, 0.5)), 0.16 + rng.uniform(0, 0.35), 0.25)
    return reverb(out, wet=0.12, dur=0.7)


# 5. Wrong-answer buzzer (short, adult, not cartoonish)
def buzzer():
    n = int(0.55 * SR)
    f = np.linspace(148, 132, n)
    x = 0.55 * square(f, n, kmax=25) + 0.45 * saw(f * 1.006, n)
    x = lp(x, 2600)
    x *= env_adsr(n, 0.006, 0.05, 0.85, 0.06)
    return reverb(x, wet=0.08, dur=0.4)


# 6. Crickets bed (awkward silence), 8 s loopable-ish
def crickets(dur=8.0):
    out = silence(dur)
    for (fc, rate, pulses, p, g, ph) in [(4650, 0.62, 3, -0.45, 1.0, 0.0), (4180, 0.71, 4, 0.5, 0.7, 0.21),
                                        (5050, 0.93, 3, 0.1, 0.45, 0.4)]:
        t = ph
        while t < dur - 0.2:
            for k in range(pulses):
                n = int(0.018 * SR)
                x = sine(fc * rng.uniform(0.995, 1.005), n) * np.hanning(n)
                x += 0.3 * sine(fc * 2, n) * np.hanning(n)
                out = place(out, pan(x, p), t + k * 0.032, g * rng.uniform(0.8, 1.0))
            t += rate * rng.uniform(0.92, 1.08)
    wind = lp(noise(dur, "pink", rng), 500) * 0.012
    out[: len(wind)] += to_stereo(fade(wind, 0.5, 0.8))
    return reverb(out, wet=0.25, dur=1.2, damp_hz=7000)


# 7. Engine: vehicle approaches, passes, recedes (Doppler)
def engine_pass(dur=6.0, t_close=2.8, speed=16.0, dist=7.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x_pos = speed * (t - t_close)
    r = np.sqrt(x_pos ** 2 + dist ** 2)
    v_rad = speed * x_pos / r
    c = 343.0
    dop = c / (c + v_rad)
    f0 = 41.0 * dop
    eng = np.zeros(n)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    for k, a in [(1, 1.0), (2, 0.7), (3, 0.45), (4, 0.5), (6, 0.25), (8, 0.18), (12, 0.08)]:
        eng += a * np.sin(k * ph + rng.uniform(0, 6))
    eng *= 1 + 0.15 * np.sin(2 * np.pi * 7 * t)
    road = bp(noise(dur, "white", rng), 300, 3500) * 0.35
    amp = 1.0 / (r / dist) ** 1.3
    closeness = 1.0 / (r / dist)
    sig = (eng * 0.6 + road) * amp
    # brighter when close
    bright = lp(sig, 900)
    sig = bright + (sig - bright) * closeness
    pan_curve = np.clip(x_pos / 25.0, -0.9, 0.9)
    out = pan(sig, pan_curve)
    out *= env_adsr(n, 0.5, 0.1, 1.0, 0.8)[:, None]
    return reverb(out, wet=0.15, dur=1.0)


# 8. Door bell ding-dong
def doorbell():
    out = silence(3.2)
    parts = ((1, 1.0, 1.0), (2.0, 0.28, 0.55), (3.0, 0.12, 0.4), (4.2, 0.06, 0.3))
    out = place(out, bell(midi(nm("E5")), 2.6, partials=parts, tau=0.9, detune=0.003), 0.0, 0.9)
    out = place(out, bell(midi(nm("C5")), 2.6, partials=parts, tau=1.1, detune=0.003), 0.62, 0.9)
    return reverb(out, wet=0.22, dur=1.4, damp_hz=5000)


# 9. Commercial sparkle / shine
def sparkle():
    out = silence(1.4)
    notes = [nm(x) for x in ["D6", "F#6", "A6", "D7", "E7", "F#7", "A7", "D8"]]
    for i, m in enumerate(notes):
        b = bell(midi(m), 0.8, tau=0.18)
        out = place(out, pan(b, -0.6 + 1.2 * i / len(notes)), 0.03 * i, 0.35)
    n = int(0.9 * SR)
    air = hp(noise(0.9, "white", rng), 6000) * np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.25
    out = place(out, air, 0.0, 1.0)
    return reverb(out, wet=0.3, dur=1.2, damp_hz=9000)


# 10. Soft whoosh
def whoosh(dur=0.6):
    n = int(dur * SR)
    x = noise(dur, "pink", rng)
    fc = np.geomspace(300, 3500, n)
    y = tv_lowpass(x, fc)
    y = hp(y, 150)
    y *= np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return pan(y, np.linspace(-0.7, 0.7, n))


# 11. Heavy footsteps on gravel (struggling walk)
def footsteps(dur=5.0, interval=0.62):
    out = silence(dur)
    t, side = 0.05, -1
    while t < dur - 0.3:
        n = int(0.16 * SR)
        crunch = np.zeros(n)
        for _ in range(28):
            i = int(rng.uniform(0, 0.11) * SR)
            m = int(0.004 * SR)
            if i + m < n:
                crunch[i:i + m] += rng.standard_normal(m) * np.hanning(m) * rng.uniform(0.3, 1.0)
        crunch = bp(crunch, 500, 6000) * env_exp(n, 0.06, 0.003)
        m = int(0.08 * SR)
        thump = sine(np.linspace(90, 45, m), m) * env_exp(m, 0.03, 0.002)
        step = crunch * 0.8
        step[:m] += thump * 0.9
        out = place(out, pan(step, 0.15 * side), t + rng.uniform(-0.03, 0.03), rng.uniform(0.75, 1.0))
        t += interval * rng.uniform(0.9, 1.15)
        side *= -1
    return reverb(out, wet=0.1, dur=0.6)


# 12. Cardboard creaks / box strain
def cardboard(dur=4.0):
    out = silence(dur)
    for _ in range(9):
        cd = rng.uniform(0.15, 0.45)
        n = int(cd * SR)
        rate = np.linspace(rng.uniform(25, 60), rng.uniform(60, 140), n)
        ph = np.cumsum(rate) / SR
        pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
        exc = pulses * rng.uniform(0.5, 1.0, n)
        res = bp(exc, rng.uniform(500, 900), rng.uniform(1400, 2600), order=2)
        res += bp(rng.standard_normal(n), 800, 4000) * 0.05
        res *= np.sin(np.linspace(0, np.pi, n)) ** 0.7
        out = place(out, pan(res, rng.uniform(-0.3, 0.3)), rng.uniform(0, dur - cd), rng.uniform(0.5, 1.0))
    return reverb(out, wet=0.08, dur=0.5)


# 13. Clock ticks (time passing)
def clock_ticks(dur=4.0, rate=2.0):
    out = silence(dur)
    k = 0
    t = 0.0
    while t < dur - 0.05:
        n = int(0.03 * SR)
        lo, hi = (2200, 5500) if k % 2 == 0 else (1300, 3600)
        x = bp(rng.standard_normal(n), lo, hi) * env_exp(n, 0.004, 0.0002)
        out = place(out, x, t, 0.8)
        t += 1.0 / rate
        k += 1
    return reverb(out, wet=0.2, dur=0.5)


# 14. Plane fly-by
def plane(dur=5.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x_pos = 60 * (t - dur * 0.5)
    r = np.sqrt(x_pos ** 2 + 40 ** 2)
    dop = 343 / (343 + 60 * x_pos / r)
    roar = lp(noise(dur, "pink", rng), 2500)
    whine = 0.12 * sine(1400 * dop, n) + 0.06 * sine(2800 * dop, n)
    sig = (roar + whine) / (r / 40) ** 1.2
    return pan(sig * env_adsr(n, 0.8, 0.1, 1, 1.0), np.clip(x_pos / 120, -0.9, 0.9))


# 15. Ship horn
def ship_horn(dur=2.6):
    n = int(dur * SR)
    f = 78 * (1 + 0.004 * np.sin(2 * np.pi * 4.5 * np.arange(n) / SR))
    x = saw(f, n) + 0.6 * saw(f * 1.498, n)
    x = lp(x, 1100)
    x = peaking(x, 300, 1.0, 5)
    x *= env_adsr(n, 0.18, 0.2, 0.85, 0.5)
    return reverb(x, wet=0.45, dur=2.8, damp_hz=3000, predelay=0.08)


# 16. Calendar page flip
def page_flip():
    n = int(0.22 * SR)
    x = hp(rng.standard_normal(n), 1800) * np.sin(np.linspace(0, np.pi, n)) ** 3
    x += bp(rng.standard_normal(n), 400, 1500) * env_exp(n, 0.02) * 0.3
    return pan(x, np.linspace(0.4, -0.4, n))


# 17. Room tones (fill under music stops so silence never sounds broken)
def room_office(dur=8.0):
    hum = 0.25 * sine(100, int(dur * SR)) + 0.12 * sine(50, int(dur * SR))
    air = lp(noise(dur, "pink", rng), 1400)
    return to_stereo(air * 0.6 + hum * 0.15)


def room_rural(dur=8.0):
    out = to_stereo(lp(noise(dur, "pink", rng), 700) * 0.5)
    for _ in range(6):  # distant birds
        t0 = rng.uniform(0.2, dur - 0.6)
        for k in range(rng.integers(2, 5)):
            n = int(0.09 * SR)
            f = np.linspace(rng.uniform(3200, 4200), rng.uniform(4500, 6200), n)
            x = sine(f, n) * np.hanning(n)
            out = place(out, pan(x, rng.uniform(-0.8, 0.8)), t0 + 0.12 * k, 0.12)
    return reverb(out, wet=0.3, dur=1.5)


# 18. Huge hit (for the epic -> cut moment)
def impact():
    n = int(1.8 * SR)
    boom = sine(np.geomspace(90, 32, n), n) * env_exp(n, 0.35, 0.002)
    crack = hp(noise(1.8, "white", rng), 1500) * env_exp(n, 0.08, 0.001) * 0.4
    return reverb(boom + crack, wet=0.35, dur=2.2, damp_hz=4000)


if __name__ == "__main__":
    save("click", click(), -4)
    save("order_confirm", order_confirm(), -3)
    save("success_ding", success_ding(), -3)
    save("cash_register", cash_register(), -1)
    save("buzzer_wrong", buzzer(), -3)
    save("crickets", crickets(), -6)
    save("engine_pass", engine_pass(), -2)
    save("doorbell", doorbell(), -2)
    save("sparkle", sparkle(), -4)
    save("whoosh", whoosh(), -4)
    save("footsteps_gravel", footsteps(), -3)
    save("cardboard_creak", cardboard(), -4)
    save("clock_ticks", clock_ticks(), -6)
    save("plane_flyby", plane(), -2)
    save("ship_horn", ship_horn(), -2)
    save("page_flip", page_flip(), -6)
    save("room_office", room_office(), -30)
    save("room_rural", room_rural(), -28)
    save("impact", impact(), -1)
