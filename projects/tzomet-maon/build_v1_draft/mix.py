"""Sound design + mix. SFX: Epidemic Sound (via Higgsfield, licensed). Music: music.py (original).
Optional narration: pass --vo path.wav (48k stereo/mono) to duck music/SFX under the real voice."""
import numpy as np, wave, sys, subprocess, argparse, os
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import MARKS as M, SPEECH, DURATION, TITLES
from music import accel_times

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, path=None):
    p = path or f'{ROOT}/wav/{name}.wav'
    w = wave.open(p)
    ch = w.getnchannels()
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    d = d.reshape(-1, ch)
    if ch == 1:
        d = np.repeat(d, 2, 1)
    return d


def seg(x, a, b):
    return x[int(a * SR):int(b * SR)].copy()


def fade(x, fin=0.0, fout=0.0):
    n = len(x)
    if fin > 0:
        k = min(n, int(fin * SR)); x[:k] *= np.linspace(0, 1, k)[:, None]
    if fout > 0:
        k = min(n, int(fout * SR)); x[n - k:] *= np.linspace(1, 0, k)[:, None]
    return x


class Bus:
    def __init__(self):
        self.x = np.zeros((int((DURATION + 1) * SR), 2))

    def add(self, t, sig, db=0.0):
        i = int(round(t * SR))
        n = min(len(sig), len(self.x) - i)
        if n > 0:
            self.x[i:i + n] += sig[:n] * 10 ** (db / 20)


def env(points, n):
    """piecewise-linear gain envelope in dB -> linear, points [(t, db)]"""
    t = np.arange(n) / SR
    ts, ds = zip(*points)
    return 10 ** (np.interp(t, ts, ds) / 20)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2))
    return signal.lfilter(b, a, x, axis=0)


def speech_mask(n, vo=None):
    if vo is not None:   # real sidechain from narration envelope
        e = np.abs(vo).max(1)
        k = int(0.03 * SR)
        e = np.convolve(e, np.ones(k) / k, 'same')
        m = (e > 10 ** (-38 / 20)).astype(float)
    else:
        m = np.zeros(n)
        for a, b, *_ in SPEECH:
            m[int(a * SR):int(b * SR)] = 1
    # attack 80ms / release 300ms smoothing
    out = np.zeros_like(m); g = 0.0
    att = 1 - np.exp(-1 / (0.08 * SR)); rel = 1 - np.exp(-1 / (0.30 * SR))
    # vectorized-ish: process in python but on decimated grid
    step = 48
    md = m[::step]; od = np.zeros_like(md)
    a1 = 1 - np.exp(-step / (0.08 * SR)); r1 = 1 - np.exp(-step / (0.30 * SR))
    for i, v in enumerate(md):
        g += (v - g) * (a1 if v > g else r1)
        od[i] = g
    return np.interp(np.arange(n), np.arange(len(od)) * step, od)


def build(vo_path=None):
    n = int((DURATION + 1) * SR)
    music = load('music', f'{ROOT}/out/music.wav')
    music = np.vstack([music, np.zeros((max(0, n - len(music)), 2))])[:n]
    vo = None
    if vo_path:
        vo = load('vo', vo_path)
        vo = np.vstack([vo, np.zeros((max(0, n - len(vo)), 2))])[:n]
    duck = speech_mask(n, vo)

    amb = Bus(); fx = Bus()
    # --- birds: pastoral opening, and again in the awkward silence
    birds = load('birds')
    b1 = fade(seg(birds, 10.0, 10.0 + M['birds_out']), 0.0, 0.5)
    amb.add(0.0, b1, 9)
    sil = M['silence_out'] - M['fanfare_cut']
    b2 = fade(seg(birds, 30.0, 30.0 + sil), 0.02, 0.01)
    amb.add(M['fanfare_cut'], b2, 3)

    # --- traffic bed (stationary jam): truck idle + van diesel idle
    truck = load('truck_idle'); van = load('van_idle')
    t_in = M['traffic_in']
    seg1 = seg(truck, 3.0, 3.0 + (M['fanfare_cut'] - t_in))
    seg2 = seg(van, 2.0, 2.0 + (M['fanfare_cut'] - t_in))
    bed = seg1 * 10 ** (-1 / 20) + seg2 * 10 ** (-4 / 20)
    L = len(bed)
    tt = lambda x: x - t_in
    g = env([(0, -9), (tt(8.0), -2), (tt(8.95), 1), (tt(10.9), 1), (tt(11.0), -7), (tt(12.95), -9),
             (tt(15.45), -11), (tt(17.9), -14), (tt(M['fanfare_cut']), -14)], L)
    bed = fade(bed * g[:, None], 0.12, 0.012)
    amb.add(t_in, bed, 0)
    # hard return of the jam on "האדום"
    t_back = M['silence_out']
    seg3 = seg(truck, 20.0, 20.0 + (DURATION - t_back))
    seg4 = seg(van, 8.0, 8.0 + (DURATION - t_back))
    bed2 = seg3 * 10 ** (-1 / 20) + seg4 * 10 ** (-4 / 20)
    g2 = env([(0, 0), (M['end_music'] - t_back, -1), (27.0 - t_back, -12), (DURATION - t_back, -16)], len(bed2))
    bed2 = fade(bed2 * g2[:, None], 0.01, 0.6)
    amb.add(t_back, bed2, 0)

    # --- honks
    fx.add(M['honk1'], load('horn2'), 7)
    fx.add(M['honk2'], load('horn1'), -9)
    desperate = lowpass(load('horn3'), 5000)
    fx.add(M['honk_desperate'], desperate, 9)

    # --- road works (ironically cheerful under the music)
    exc = fade(seg(load('excavator'), 12.0, 12.0 + (M['works_out'] - M['works_in'])), 0.03, 0.3)
    fx.add(M['works_in'], exc, -6)
    jh = fade(seg(load('jackhammer'), 0.8, 0.8 + 1.7), 0.02, 0.25)
    fx.add(M['works_in'] + 0.2, jh, -9)

    # --- clock: steady under the watch check, then accelerating with the time-lapse
    clock = load('clock')
    steady = fade(seg(clock, 0.05, 0.05 + (M['timelapse_in'] - M['clock_in'])), 0.01, 0.05)
    fx.add(M['clock_in'], steady, 5)
    tick = fade(seg(clock, 0.075, 0.075 + 0.14), 0.002, 0.04)
    tock = fade(seg(clock, 1.08, 1.08 + 0.14), 0.002, 0.04)
    times = accel_times(M['timelapse_in'], M['timelapse_out'])
    for j, t in enumerate(times):
        fx.add(t, tick if j % 2 == 0 else tock, -1 + 5 * j / len(times))
    # calendar pages
    pf = load('pages_flip'); pfast = load('pages_fast')
    fx.add(M['timelapse_in'] - 0.42, pf, -15)
    for k, t in enumerate([M['timelapse_in'] + 0.25, M['timelapse_in'] + 0.8, M['timelapse_in'] + 1.3, M['timelapse_in'] + 1.65]):
        fx.add(t - 0.1, pfast, -11 + k)

    # --- fanfare: stretched to span the sentence, then cut dead at the reveal
    ff = load('fanfare_st', f'{ROOT}/wav/fanfare_stretched.wav')
    span = M['fanfare_cut'] - M['fanfare_in']
    ff = seg(ff, 0.0, span)
    ff = fade(ff, 0.0, 0.006)
    fx.add(M['fanfare_in'], ff, -9)

    # --- duck music and SFX under narration
    mus = music * (1 - duck * (1 - 10 ** (-7 / 20)))[:, None]
    # music must be dead silent in the awkward silence and on the punch
    ms = np.ones(n)
    a = int(M['fanfare_cut'] * SR); b = int((M['end_music']) * SR)
    ms[a:b] = 0
    mus = mus * ms[:, None]
    ambx = amb.x * (1 - duck * (1 - 10 ** (-4 / 20)))[:, None]
    fxx = fx.x * (1 - duck * (1 - 10 ** (-3 / 20)))[:, None]
    # duck the fanfare harder under voice? keep it proud: only -3 dB
    mix = mus * 10 ** (0 / 20) + ambx + fxx
    if vo is not None:
        mix = mix + vo * 10 ** (0 / 20)
    return mix[: int(DURATION * SR)]


def write_f32(path, x):
    import struct
    d = x.astype('<f4').tobytes()
    with open(path, 'wb') as f:
        n = len(d)
        f.write(b'RIFF' + struct.pack('<I', 36 + n) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 3, 2, SR, SR * 8, 8, 32))
        f.write(b'data' + struct.pack('<I', n) + d)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--vo', default=None)
    a = ap.parse_args()
    x = build(a.vo)
    write_f32(a.out, x)
    print('mix ok, peak', round(20 * np.log10(np.abs(x).max() + 1e-9), 1), 'dBFS')
