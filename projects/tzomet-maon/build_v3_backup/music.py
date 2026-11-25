"""Original score, synthesized from scratch (no third-party music = no licensing issue).
Style: innocent 'educational film' cue. Pizzicato strings (Karplus-Strong), xylophone,
glockenspiel, woodblock, shaker, small-room reverb."""
import numpy as np
from scipy import signal
import sys, wave
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from timeline import MARKS, DURATION, TITLES

SR = 48000
OS = 4
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6,
        'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(n):
    if isinstance(n, str):
        n = 12 * (int(n[-1]) + 1) + NOTE[n[:-1]]
    return 440.0 * 2 ** ((n - 69) / 12)


rng = np.random.default_rng(7)


def pizz(f, t60=None, bright=0.45, dur=1.6):
    """Karplus-Strong pluck at 4x oversampling, block-vectorized."""
    sr = SR * OS
    N = max(2, int(round(sr / f - 0.5)))
    if t60 is None:
        t60 = float(np.interp(f, [50, 150, 400, 1000], [1.1, 0.7, 0.42, 0.28]))
    a = 10 ** (-3.0 / (t60 * f))
    L = int(dur * sr)
    exc = rng.uniform(-1, 1, N)
    b, aa = signal.butter(2, min(0.95, (900 + bright * 9000) / (sr / 2)))
    exc = signal.lfilter(b, aa, exc)
    exc -= exc.mean()
    y = np.zeros(L + 2 * N)
    y[:N] = exc
    k = 1
    while k * N < L:
        s = k * N
        prev = y[s - N:s]
        prev1 = y[s - N - 1:s - 1] if s - N - 1 >= 0 else np.concatenate(([0.0], y[s - N:s - 1]))
        y[s:s + N] = 0.5 * a * (prev + prev1)
        k += 1
    y = y[:L]
    y = signal.resample_poly(y, 1, OS)
    # finger thump
    n = len(y)
    t = np.arange(n) / SR
    thump = rng.normal(0, 1, n) * np.exp(-t / 0.004)
    bt, at = signal.butter(2, 600 / (SR / 2))
    y = y + 0.25 * signal.lfilter(bt, at, thump)
    y *= np.minimum(1, t / 0.002)
    return y / (np.abs(y).max() + 1e-9)


def xylo(f, dur=1.2):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for r, amp, t60 in [(1.0, 1.0, 0.55), (3.0, 0.32, 0.16), (6.2, 0.10, 0.07), (9.9, 0.04, 0.035)]:
        if f * r < 18000:
            y += amp * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6.28)) * np.exp(-6.9 * t / t60)
    click = rng.normal(0, 1, len(t)) * np.exp(-t / 0.0015)
    b, a = signal.butter(2, 2500 / (SR / 2), 'high')
    y += 0.18 * signal.lfilter(b, a, click)
    y *= np.minimum(1, t / 0.0008)
    return y / (np.abs(y).max() + 1e-9)


def glock(f, dur=2.5):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for r, amp, t60 in [(1.0, 1.0, 1.9), (2.76, 0.22, 0.55), (5.40, 0.09, 0.22), (8.93, 0.04, 0.1)]:
        if f * r < 19000:
            y += amp * np.sin(2 * np.pi * f * r * t) * np.exp(-6.9 * t / t60)
    y *= np.minimum(1, t / 0.0006)
    return y / (np.abs(y).max() + 1e-9)


def woodblock(f=880, dur=0.25):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-6.9 * t / 0.06) + 0.5 * np.sin(2 * np.pi * f * 1.73 * t) * np.exp(-6.9 * t / 0.035)
    y += 0.3 * rng.normal(0, 1, len(t)) * np.exp(-t / 0.001)
    return y / (np.abs(y).max() + 1e-9)


def snare(dur=0.2):
    t = np.arange(int(dur * SR)) / SR
    n = rng.normal(0, 1, len(t))
    b, a = signal.butter(2, [1500 / (SR / 2), 9000 / (SR / 2)], 'band')
    y = signal.lfilter(b, a, n) * np.exp(-t / 0.032)
    y += 0.55 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.045) + 0.3 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.03)
    y *= np.minimum(1, t / 0.0007)
    return y / (np.abs(y).max() + 1e-9)


def cymbal(dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    n = rng.normal(0, 1, len(t))
    b, a = signal.butter(2, 3500 / (SR / 2), 'high')
    y = signal.lfilter(b, a, n) * (np.exp(-t / 0.35) * 0.8 + np.exp(-t / 0.05) * 0.6)
    y *= np.minimum(1, t / 0.002)
    return y / (np.abs(y).max() + 1e-9)


def shaker(dur=0.15):
    t = np.arange(int(dur * SR)) / SR
    n = rng.normal(0, 1, len(t))
    b, a = signal.butter(2, [5000 / (SR / 2), 12000 / (SR / 2)], 'band')
    env = np.minimum(1, t / 0.012) * np.exp(-t / 0.045)
    y = signal.lfilter(b, a, n) * env
    return y / (np.abs(y).max() + 1e-9)


class Track:
    def __init__(self, dur):
        self.L = int(dur * SR) + SR * 3
        self.buf = np.zeros((self.L, 2))

    def add(self, t, sig, gain_db=0.0, pan=0.0):
        i = int(round(t * SR))
        if i >= self.L:
            return
        g = 10 ** (gain_db / 20)
        sig = sig[: self.L - i]
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        self.buf[i:i + len(sig), 0] += sig * g * l * 1.414
        self.buf[i:i + len(sig), 1] += sig * g * r * 1.414


def reverb(x, t60=1.1, wet=0.2):
    n = int(t60 * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for c in range(2):
        noise = rng.normal(0, 1, n) * np.exp(-6.9 * t / t60)
        b, a = signal.butter(1, 5500 / (SR / 2))
        ir[:, c] = signal.lfilter(b, a, noise)
    pre = int(0.014 * SR)
    ir = np.vstack([np.zeros((pre, 2)), ir])
    ir /= np.sqrt((ir ** 2).sum(0))
    out = np.zeros_like(x)
    for c in range(2):
        out[:, c] = signal.fftconvolve(x[:, c], ir[:, c])[: len(x)]
    return x * (1 - wet) + out * wet * 1.6


# ---------------------------------------------------------------- score
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT

CHORDS_A = ['C', 'G7', 'C', 'G', 'F', 'C', 'G7', 'C']
CH = {
    'C': (['C3', 'G2'], ['E4', 'G4', 'C5']),
    'G7': (['G2', 'D3'], ['F4', 'B4', 'D5']),
    'G': (['G2', 'D3'], ['D4', 'G4', 'B4']),
    'F': (['F2', 'C3'], ['F4', 'A4', 'C5']),
}
MEL = [
    [(0, 'E5'), (1, 'G5'), (1.5, 'E5'), (2, 'C5'), (3, 'D5'), (3.5, 'E5')],
    [(0, 'F5'), (1, 'D5'), (1.5, 'B4'), (2, 'G4'), (3, 'A4'), (3.5, 'B4')],
    [(0, 'C5'), (0.5, 'E5'), (1, 'G5'), (1.5, 'C6'), (2, 'B5'), (2.5, 'G5'), (3, 'E5')],
    [(0, 'D5'), (1, 'G5'), (1.5, 'F5'), (2, 'D5'), (3, 'B4')],
    [(0, 'A5'), (1, 'C6'), (1.5, 'A5'), (2, 'F5'), (3, 'G5'), (3.5, 'A5')],
    [(0, 'G5'), (1, 'E5'), (1.5, 'C5'), (2, 'E5'), (3, 'G5')],
    [(0, 'F5'), (0.5, 'E5'), (1, 'D5'), (1.5, 'C5'), (2, 'B4'), (3, 'D5'), (3.5, 'F5')],
    [(0, 'E5'), (1, 'C5'), (2, 'G4'), (3, 'C5')],
]

cache = {}


def S(kind, note, **kw):
    key = (kind, note, tuple(sorted(kw.items())))
    if key not in cache:
        f = hz(note) if note is not None else None
        cache[key] = {'pizz': lambda: pizz(f, **kw), 'xylo': lambda: xylo(f), 'glock': lambda: glock(f),
                      'wood': lambda: woodblock(**kw), 'shaker': lambda: shaker(), 'snare': lambda: snare(), 'cymbal': lambda: cymbal()}[kind]()
    return cache[key]


def build():
    tr = Track(DURATION)
    a_end = MARKS['clock_in'] + 0.05      # section A runs until beat 6
    # ---- Section A
    for b in range(8):
        t0 = b * BAR
        if t0 >= a_end:
            break
        bass, chord = CH[CHORDS_A[b]]
        for beat, note in [(0, bass[0]), (2, bass[1])]:
            tt = t0 + beat * BEAT
            if tt < a_end:
                tr.add(tt, S('pizz', note, t60=0.75, bright=0.3), -6, 0.0)
        for beat in (1, 3):
            tt = t0 + beat * BEAT
            if tt < a_end:
                for k, n in enumerate(chord):
                    tr.add(tt + 0.004 * k, S('pizz', n, t60=0.3, bright=0.5), -15, 0.3)
                tr.add(tt, S('wood', None, f=900), -21, -0.4)
        for e in range(8):
            tt = t0 + e * BEAT / 2
            if tt < a_end:
                tr.add(tt, S('shaker', None), -30 if e % 2 else -27, 0.45)
        for beat, n in MEL[b]:
            tt = t0 + beat * BEAT
            if tt < a_end:
                tr.add(tt, S('xylo', n), -9, -0.15)
                if beat == 0 and b % 2 == 0:
                    tr.add(tt, S('glock', n[:-1] + str(int(n[-1]) + 1)), -21, 0.3)
    # "תוסיפו עבודות!" : ironic 'add the secret ingredient' flourish
    run = ['C6', 'D6', 'E6', 'F6', 'G6', 'A6', 'B6']
    t_land = MARKS['flourish_land']
    for i, n in enumerate(run):
        tr.add(t_land - 0.26 + i * 0.037, S('xylo', n), -15 + i * 0.6, -0.1 + i * 0.05)
    tr.add(t_land, S('glock', 'C7'), -18, 0.25)
    tr.add(t_land, S('xylo', 'C6'), -14, 0.0)

    # ---- Section B : waiting (pendulum pizz under the clock)
    t = MARKS['clock_in'] + 0.05
    pend = [('A2', 'E3'), ('F2', 'C3'), ('D2', 'A2'), ('E2', 'B2')]
    gl = ['C6', 'A5', 'F5', 'G#5']
    i = 0
    while t < MARKS['timelapse_in'] - 0.05:
        pair = pend[(i // 4) % 4]
        tr.add(t, S('pizz', pair[i % 2], t60=0.6, bright=0.25), -9, 0.0)
        if i % 4 == 0:
            tr.add(t, S('glock', gl[(i // 4) % 4]), -24, 0.3)
        t += BEAT
        i += 1
    # ---- time-lapse accelerando: pizz pulses speeding up with the clock
    ta, tb = MARKS['timelapse_in'], MARKS['timelapse_out']
    times = accel_times(ta, tb)
    for j, tt in enumerate(times):
        note = 52 + (j // 3)            # rising, one semitone every 3 hits
        tr.add(tt, S('pizz', note, t60=0.25, bright=0.35), -16 + 6 * j / len(times), 0.2 if j % 2 else -0.2)

    # ---- v3 insert: left turn from Ofakim
    if 'seg_in' in MARKS:
        s0, lock = MARKS['seg_in'], MARKS['counter_lock']
        # innocent theme returns under the blinker
        for bi in range(3):
            t0 = s0 + bi * BAR
            bass, chord = CH[CHORDS_A[bi]]
            for beat, note in [(0, bass[0]), (2, bass[1])]:
                tt = t0 + beat * BEAT
                if tt < lock - 0.02:
                    tr.add(tt, S('pizz', note, t60=0.75, bright=0.3), -6, 0.0)
            for beat in (1, 3):
                tt = t0 + beat * BEAT
                if tt < lock - 0.02:
                    for k, n in enumerate(chord):
                        tr.add(tt + 0.004 * k, S('pizz', n, t60=0.3, bright=0.5), -15, 0.3)
            for beat, n in MEL[bi]:
                tt = t0 + beat * BEAT
                if tt < lock - 0.02:
                    tr.add(tt, S('xylo', n), -10, -0.15)
        # counter locks on 50:00 -> one bright ding, then the music is gone
        tr.add(lock, S('glock', 'C7'), -12, 0.1)
        tr.add(lock, S('xylo', 'G6'), -15, -0.1)
        # victory: rising build from "ובסוף", C major hit under the trumpet, celebration cut dead
        vb, vh = MARKS['victory_build'], MARKS['victory_hit']
        arp = ['C4', 'E4', 'G4', 'C5', 'E5', 'G5', 'C6']
        n_b = int((vh - vb) / 0.125)
        for j in range(n_b):
            tt = vb + j * 0.125
            tr.add(tt, S('pizz', arp[j % len(arp)] if j < 7 else arp[(j % 3) + 4], t60=0.25, bright=0.45),
                   -24 + 12 * j / max(1, n_b - 1), 0.25 if j % 2 else -0.25)
        for n in ['C2', 'C3']:
            tr.add(vh, S('pizz', n, t60=1.2, bright=0.3), -5, 0)
        for k, n in enumerate(['C4', 'E4', 'G4', 'C5']):
            tr.add(vh + 0.008 * k, S('pizz', n, t60=0.6, bright=0.6), -11, 0.25)
        tr.add(vh, S('glock', 'C7'), -14, 0.3)
        tr.add(vh, S('xylo', 'E6'), -12, -0.2)
        tr.add(vh, S('cymbal', None), -14, 0.0)
        run = [(0.25, 'G5'), (0.375, 'C6'), (0.5, 'E6'), (0.625, 'G6'), (0.75, 'E6'), (0.875, 'C6')]
        for dt, n in run:
            tr.add(vh + dt, S('xylo', n), -15, -0.15)
        for dt, n in [(0.25, 'G2'), (0.5, 'C3'), (0.75, 'G2')]:
            tr.add(vh + dt, S('pizz', n, t60=0.5, bright=0.3), -10, 0)
        for dt in (0.375, 0.625, 0.875):
            for k, n in enumerate(['E4', 'G4', 'C5']):
                tr.add(vh + dt + 0.004 * k, S('pizz', n, t60=0.3, bright=0.5), -17, 0.3)

    # ---- "והנה לכם..." : snare roll crescendo into the fanfare (fanfare itself is an SFX)
    t, k = MARKS['roll_in'], 0
    ra, rb = MARKS['roll_in'], MARKS['fanfare_in']
    while t < rb:
        u = (t - ra) / (rb - ra)
        tr.add(t + rng.uniform(-0.003, 0.003), S('snare', None), -31 + 17 * u ** 1.3 + (1.2 if k % 2 else -1.2), 0.05)
        t += 1 / 26
        k += 1

    # ---- End card hits
    hits = [
        (TITLES[0][0], ['C3'], ['E4', 'G4', 'C5'], ['C6'], ['E6']),
        (TITLES[1][0], ['F2'], ['A4', 'C5', 'F5'], ['A6'], ['F6']),
        (TITLES[2][0], ['G2'], ['F4', 'B4', 'D5'], ['B5'], ['D6']),
    ]
    for tt, bass, chord, gls, xys in hits:
        for n in bass:
            tr.add(tt, S('pizz', n, t60=0.9, bright=0.3), -11, 0)
        for k, n in enumerate(chord):
            tr.add(tt + 0.012 * k, S('pizz', n, t60=0.45, bright=0.5), -18, 0.25)
        for n in gls:
            tr.add(tt, S('glock', n), -22, 0.3)
        for n in xys:
            tr.add(tt, S('xylo', n), -16, -0.15)
    # soft walking xylophone between hits, keeps the 'film' feeling alive
    t1, t2, t3 = TITLES[0][0], TITLES[1][0], TITLES[2][0]
    walk = [(t1 + 0.55, 'G5'), (t1 + 0.80, 'E5'), (t2 + 0.55, 'C6'), (t2 + 0.80, 'A5'),
            (t3 + 0.45, 'G5'), (t3 + 0.70, 'F5'), (t3 + 0.85, 'D5')]
    for tt, n in walk:
        tr.add(tt, S('xylo', n), -21, -0.2)
    fc = MARKS['final_chord']
    for n in ['C2', 'C3']:
        tr.add(fc, S('pizz', n, t60=1.4, bright=0.3), -7, 0)
    for k, n in enumerate(['E4', 'G4', 'C5', 'E5']):
        tr.add(fc + 0.01 * k, S('pizz', n, t60=0.7, bright=0.55), -12, 0.25)
    tr.add(fc, S('xylo', 'C6'), -10, -0.1)
    tr.add(fc, S('glock', 'C7'), -13, 0.3)
    tr.add(fc, S('wood', None, f=900), -18, -0.4)

    out = reverb(tr.buf, t60=1.0, wet=0.22)
    # gentle bus glue: highpass + soft clip
    b, a = signal.butter(2, 45 / (SR / 2), 'high')
    out = signal.lfilter(b, a, out, axis=0)
    out = out / (np.abs(out).max() + 1e-9) * 0.7
    return out


def accel_times(ta, tb):
    """tick times accelerating from 2/s to ~14/s between ta and tb"""
    times, t, dt = [], ta, 0.42
    while t < tb:
        times.append(t)
        t += dt
        dt = max(0.065, dt * 0.84)
    return times


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    d = (x * 32767).astype(np.int16)
    w = wave.open(path, 'wb')
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(d.tobytes()); w.close()


if __name__ == '__main__':
    import time
    t = time.time()
    m = build()
    write_wav(sys.argv[1], m[: int((DURATION + 0.5) * SR)])
    print('music ok', round(time.time() - t, 1), 's')
