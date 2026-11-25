"""Sound design + mix v2, built on the real narration.
SFX: Epidemic Sound (licensed, via Higgsfield). Music: music.py (original). VO: src/vo.mp3 (ElevenLabs).
Outputs a float WAV; mastering (loudness/limiter) happens in master.sh."""
import numpy as np, wave, sys, os, argparse, struct
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import MARKS as M, VO_SEGS, DURATION
from music import accel_times

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = int((DURATION + 1) * SR)


def load(name, path=None):
    p = path or f'{ROOT}/wav/{name}.wav'
    w = wave.open(p)
    ch, sw = w.getnchannels(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
    d = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
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
        self.x = np.zeros((N, 2))

    def add(self, t, sig, db=0.0):
        i = int(round(t * SR))
        n = min(len(sig), N - i)
        if n > 0:
            self.x[i:i + n] += sig[:n] * 10 ** (db / 20)


def env(points, n):
    t = np.arange(n) / SR
    ts, ds = zip(*points)
    return 10 ** (np.interp(t, ts, ds) / 20)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2))
    return signal.lfilter(b, a, x, axis=0)


def build_vo():
    vo = load('vo')
    b, a = signal.butter(2, 70 / (SR / 2), 'high')
    vo = signal.lfilter(b, a, vo, axis=0)
    bus = Bus()
    for sa, sb, off in VO_SEGS:
        piece = fade(seg(vo, sa, sb), 0.008, 0.008)
        bus.add(sa + off, piece, 0)
    return bus.x


def duck_curve(vo):
    """smooth 0..1 'voice present' curve: attack 60 ms, release 350 ms, from the real narration"""
    e = np.abs(vo).max(1)
    k = int(0.02 * SR)
    e = np.convolve(e, np.ones(k) / k, 'same')
    m = (e > 10 ** (-42 / 20)).astype(float)
    step = 48
    md = m[::step]; od = np.zeros_like(md); g = 0.0
    a1 = 1 - np.exp(-step / (0.06 * SR)); r1 = 1 - np.exp(-step / (0.35 * SR))
    for i, v in enumerate(md):
        g += (v - g) * (a1 if v > g else r1)
        od[i] = g
    return np.interp(np.arange(len(m)), np.arange(len(od)) * step, od)


def build():
    vo = build_vo()
    duck = duck_curve(vo)
    music = load('music', f'{ROOT}/out/music.wav')
    music = np.vstack([music, np.zeros((max(0, N - len(music)), 2))])[:N]

    amb = Bus(); fx = Bus(); ff_bus = Bus()
    # birds: pastoral opening, and the awkward silence under the empty sky
    birds = load('birds')
    amb.add(0.0, fade(seg(birds, 10.0, 10.0 + M['birds_out']), 0.0, 0.5), 9)
    sil = M['silence_out'] - M['fanfare_cut']
    amb.add(M['fanfare_cut'], fade(seg(birds, 30.0, 30.0 + sil), 0.02, 0.01), 4)

    # stationary jam bed
    truck = load('truck_idle'); van = load('van_idle')
    t_in = M['traffic_in']; span = M['fanfare_cut'] - t_in
    bed = seg(truck, 3.0, 3.0 + span) * 10 ** (-1 / 20) + seg(van, 2.0, 2.0 + span) * 10 ** (-4 / 20)
    r = lambda x: x - t_in
    g = env([(0, -9), (r(7.25), -2), (r(8.42), -3), (r(9.85), -3), (r(9.95), -7), (r(M['clock_in']), -9),
             (r(M['timelapse_in']), -11), (r(15.55), -12), (r(M['fanfare_in']), -15), (span, -15)], len(bed))
    amb.add(t_in, fade(bed * g[:, None], 0.10, 0.012), 0)
    # the jam slams back on "האדום"
    tb = M['silence_out']; span2 = DURATION - tb
    bed2 = seg(truck, 20.0, 20.0 + span2) * 10 ** (-1 / 20) + seg(van, 8.0, 8.0 + span2) * 10 ** (-4 / 20)
    g2 = env([(0, -4), (M['end_music'] - tb, -5), (M['end_music'] - tb + 1.2, -13), (span2, -18)], len(bed2))
    amb.add(tb, fade(bed2 * g2[:, None], 0.01, 0.5), 0)

    # honks: two short ones in the squeeze, one hopeless one after the punch
    fx.add(M['honk1'], load('horn2'), 7)
    fx.add(M['honk2'], load('horn1'), -9)
    fx.add(M['honk_desperate'], lowpass(load('horn3'), 5000), 9)

    # road works
    wdur = M['works_out'] - M['works_in']
    fx.add(M['works_in'], fade(seg(load('excavator'), 12.0, 12.0 + wdur), 0.03, 0.3), -6)
    fx.add(M['works_in'] + 0.15, fade(seg(load('jackhammer'), 0.8, 0.8 + wdur - 0.2), 0.02, 0.25), -9)

    # clock under the watch check, then accelerating ticks + calendar pages in the time-lapse
    clock = load('clock')
    fx.add(M['clock_in'], fade(seg(clock, 0.05, 0.05 + (M['timelapse_in'] - M['clock_in'])), 0.01, 0.05), 5)
    tick = fade(seg(clock, 0.075, 0.215), 0.002, 0.04)
    tock = fade(seg(clock, 1.08, 1.22), 0.002, 0.04)
    times = accel_times(M['timelapse_in'], M['timelapse_out'])
    for j, t in enumerate(times):
        fx.add(t, tick if j % 2 == 0 else tock, -1 + 5 * j / len(times))
    pf = load('pages_flip'); pfast = load('pages_fast')
    fx.add(M['timelapse_in'] - 0.42, pf, -15)
    ti = M['timelapse_in']
    for k, t in enumerate([ti + 0.25, ti + 0.8, ti + 1.3, ti + 1.7]):
        fx.add(t - 0.1, pfast, -11 + k)

    # fanfare: stretched to the sentence, killed dead the instant the sky is revealed
    ff = load('fanfare_st', f'{ROOT}/wav/fanfare_stretched.wav')
    ff = fade(seg(ff, 0.0, M['fanfare_cut'] - M['fanfare_in']), 0.0, 0.005)
    ff_bus.add(M['fanfare_in'], ff, -9)

    # ---- ducking under the real narration
    def ducked(x, db):
        return x * (1 - duck * (1 - 10 ** (db / 20)))[:, None]
    mus = ducked(music, -9)
    gate = np.ones(N)
    gate[int(M['fanfare_cut'] * SR):int(M['end_music'] * SR)] = 0       # music dead from the reveal to the end card
    mus *= gate[:, None]
    mix = mus + ducked(amb.x, -5) + ducked(fx.x, -4) + ducked(ff_bus.x, -5) + vo * 10 ** (7.5 / 20)
    n_out = int(DURATION * SR)
    mix = mix[:n_out]
    mix = fade(mix, 0.0, 0.35)
    stems = dict(vo=(vo * 10 ** (7.5 / 20))[:n_out], music=mus[:n_out], fx=(ducked(amb.x, -5) + ducked(fx.x, -4) + ducked(ff_bus.x, -5))[:n_out])
    return mix, stems


def write_f32(path, x):
    d = x.astype('<f4').tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(d)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 3, 2, SR, SR * 8, 8, 32))
        f.write(b'data' + struct.pack('<I', len(d)) + d)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--stems', default=None, help='dir to write vo/music/fx stems')
    a = ap.parse_args()
    x, stems = build()
    write_f32(a.out, x)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for k, v in stems.items():
            write_f32(f'{a.stems}/{k}.wav', v)
    print('mix ok, peak', round(20 * np.log10(np.abs(x).max() + 1e-9), 1), 'dBFS')
