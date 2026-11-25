"""Sound design + mix v2, built on the real narration.
SFX: Epidemic Sound (licensed, via Higgsfield). Music: music.py (original). VO: src/vo.mp3 (ElevenLabs).
Outputs a float WAV; mastering (loudness/limiter) happens in master.sh."""
import numpy as np, wave, sys, os, argparse, struct
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as TL
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


def loop_seg(x, a, dur):
    out = x[int(a * SR):]
    while len(out) < int(dur * SR):
        out = np.vstack([out, x])
    return out[:int(dur * SR)].copy()


def _res(x, f0, q):
    b, a = signal.iirpeak(f0, q, SR)
    return signal.lfilter(b, a, x)


_rng = np.random.default_rng(11)


def relay_click(f1, f2, dec):
    t = np.arange(int(0.07 * SR)) / SR
    exc = _rng.normal(0, 1, len(t)) * np.exp(-t / 0.0012)
    y = _res(exc, f1, 14) + 0.6 * _res(exc, f2, 10) + 0.3 * np.sin(2 * np.pi * 520 * t) * np.exp(-t / dec)
    y *= np.exp(-t / (dec * 2))
    y /= np.abs(y).max() + 1e-9
    return np.stack([y, y], 1)


def tire_squeal(dur=0.85):
    t = np.arange(int(dur * SR)) / SR
    walk = np.cumsum(_rng.normal(0, 1, len(t)))
    b, a = signal.butter(1, 12 / (SR / 2)); walk = signal.lfilter(b, a, walk); walk /= np.abs(walk).max() + 1e-9
    f0 = 1260 * (1 - 0.13 * t / dur) * (1 + 0.025 * walk) * (1 + 0.006 * np.sin(2 * np.pi * 34 * t))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    tone = np.sin(ph) + 0.5 * np.sin(2 * ph + 0.3) + 0.28 * np.sin(3 * ph + 1.1) + 0.12 * np.sin(4 * ph)
    b, a = signal.butter(2, 70 / (SR / 2)); am = 1 + 0.45 * signal.lfilter(b, a, _rng.normal(0, 6, len(t)))
    b, a = signal.butter(2, [1800 / (SR / 2), 5200 / (SR / 2)], 'band')
    hiss = signal.lfilter(b, a, _rng.normal(0, 1, len(t)))
    hiss /= np.abs(hiss).max() + 1e-9
    rel = dur - 0.32
    envl = np.minimum(1, t / 0.035) * np.where(t < rel, 1.0, np.exp(-(t - rel) / 0.085))
    y = (0.75 * tone * am / 1.9 + 0.55 * hiss) * envl
    y += 0.5 * np.sin(2 * np.pi * 68 * t) * np.exp(-t / 0.11)          # weight transfer thump
    b, a = signal.butter(2, 9000 / (SR / 2)); y = signal.lfilter(b, a, y)
    y /= np.abs(y).max() + 1e-9
    st = np.stack([y, y], 1)
    # short outdoor slap
    d = int(0.045 * SR)
    st[d:] += 0.22 * st[:-d]
    return st / (np.abs(st).max() + 1e-9)


def whoosh(dur=0.6):
    t = np.arange(int(dur * SR)) / SR
    n = _rng.normal(0, 1, len(t))
    b, a = signal.butter(2, [180 / (SR / 2), 1600 / (SR / 2)], 'band')
    y = signal.lfilter(b, a, n)
    e = np.where(t < 0.22, (t / 0.22) ** 2, np.exp(-(t - 0.22) / 0.13))
    y = y * e / (np.abs(y * e).max() + 1e-9)
    pan = np.clip(t / dur, 0, 1)                      # SUV crosses right -> left
    return np.stack([y * (0.35 + 0.65 * pan), y * (1 - 0.65 * pan)], 1)


def pulse(f, dur, duty=0.25, vib=0.0):
    t = np.arange(int(dur * SR)) / SR
    ff = f * (1 + vib * np.sin(2 * np.pi * 6 * t))
    ph = 2 * np.pi * np.cumsum(ff) / SR
    y = np.zeros_like(t)
    k = 1
    while f * k < 15000:
        y += np.sin(np.pi * k * duty) / k * np.cos(k * ph)
        k += 1
    return y


def game_jingle():
    seq = [(784, 0.065), (1047, 0.065), (1319, 0.065), (1568, 0.065)]
    parts = []
    for f, dlen in seq:
        y = pulse(f, dlen); y *= np.minimum(1, np.arange(len(y)) / 60)
        parts.append(y)
    held = int(0.34 * SR); t = np.arange(held) / SR
    top = (pulse(2093, 0.34, vib=0.012) + 0.6 * pulse(1319, 0.34, duty=0.5)) * np.exp(-t / 0.16)
    y = np.concatenate(parts + [top])
    y /= np.abs(y).max() + 1e-9
    st = np.stack([y, y], 1)
    d = int(0.095 * SR)
    echo = np.zeros((len(st) + d, 2)); echo[:len(st)] += st; echo[d:] += 0.3 * st
    return echo / (np.abs(echo).max() + 1e-9)


def blinker_times():
    """turn-signal ON clicks: locked to the visible blink in clip9 shots, regular in between"""
    a, b = TL.S0, TL.S0 + TL.SEG_L
    anchors = []
    for s_ in TL.SHOTS:
        if s_.get('clip') == 9 and s_['t0'] >= a - 1e-6 and s_['t0'] < b:
            sp = s_.get('speed', 1.0)
            for on in TL.BLINK9_ON:
                if s_['src'] - 1e-6 <= on:
                    tt = s_['t0'] + (on - s_['src']) / sp
                    if tt < s_['t1']:
                        anchors.append(tt)
    anchors.sort()
    out = [anchors[0]]
    for x0, x1 in zip(anchors[:-1], anchors[1:]):      # even spacing between visible blinks (no hiccups)
        n = max(1, round((x1 - x0) / TL.BLINK_P))
        out += [x0 + k * (x1 - x0) / n for k in range(1, n + 1)]
    while out[-1] + TL.BLINK_P < b:
        out.append(out[-1] + TL.BLINK_P)
    return out


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
    if hasattr(TL, 'VO2_SEGS'):
        vo2 = signal.lfilter(b, a, load('vo2'), axis=0)
        for sa, sb, off in TL.VO2_SEGS:
            bus.add(TL.S0 + sa + off, fade(seg(vo2, sa, sb), 0.008, 0.008), -2.0)   # match level of narration 1
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
    bed = loop_seg(truck, 3.0, span) * 10 ** (-1 / 20) + loop_seg(van, 2.0, span) * 10 ** (-4 / 20)
    r = lambda x: x - t_in
    pts = [(0, -9), (r(7.25), -2), (r(8.42), -3), (r(9.85), -3), (r(9.95), -7), (r(M['clock_in']), -9),
           (r(M['timelapse_in']), -11)]
    pts += [(r(TL.T_BASE), -12), (r(M['fanfare_in']), -15), (span, -15)]
    g = env(pts, len(bed))
    amb.add(t_in, fade(bed * g[:, None], 0.10, 0.012), 0)
    # the jam slams back on "האדום"
    tb = M['silence_out']; span2 = DURATION - tb
    bed2 = loop_seg(truck, 20.0, span2) * 10 ** (-1 / 20) + loop_seg(van, 8.0, span2) * 10 ** (-4 / 20)
    q = lambda x: x - tb
    p2 = [(0, -4), (q(TL.S0) - 0.01, -5)]
    if hasattr(TL, 'N_WATCH'):     # left-turn segment: junction outside, muffled inside, then only the blinker
        p2 += [(q(TL.S0), -11), (q(TL.N_WATCH) - 0.01, -11), (q(TL.N_WATCH), -17), (q(TL.N_TURN) - 0.01, -17),
               (q(TL.N_TURN), -11), (q(TL.N_CUT) + 0.8, -11), (q(TL.N_CUT) + 1.4, -20),
               (q(M['blinker_only']) - 0.6, -24), (q(M['blinker_only']), -80)]
    p2 += [(span2, -80)]
    g2 = env(p2, len(bed2))
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

    # ---- v3 insert sound design
    if hasattr(TL, 'S0'):
        tick_on = relay_click(2350, 4300, 0.010); tick_off = relay_click(1750, 3300, 0.008)
        for k, tt in enumerate(blinker_times()):
            fx.add(tt, tick_on, -15)
            if tt + 0.35 < TL.S0 + TL.SEG_L:
                fx.add(tt + 0.35, tick_off, -19)
        # time running: accelerating clock while the counter races to 50:00
        for j, tt in enumerate(accel_times(M['counter_start'], M['counter_lock'] - 0.04)):
            fx.add(tt, tick if j % 2 == 0 else tock, -2 + 4 * j / 8)
        # victory trumpet (C major, lands with the orchestra), killed on "חתכו"
        fa = load('fanfare_ascend')
        st = M['victory_hit'] - 0.98
        fa = fade(seg(fa, 0.0, M['victory_cut'] - st), 0.0, 0.006)
        ff_bus.add(st, fa, -7)
        # the cut-off: SUV whoosh + brakes, matched to her wheel smoking (clip10 0.1-0.9 s)
        fx.add(TL.N_CUT - 0.04, whoosh(), -14)
        ff_bus.add(M['squeal'], tire_squeal(0.85), -14)
        if 'jingle' in M:      # removed in v4: the last line is "סעו בזהירות!" and only the blinker is heard
            fx.add(M['jingle'], game_jingle(), -15)

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
    if 'victory_cut' in M:
        gate[int(M['victory_cut'] * SR):] = 0   # victory music dies on "חתכו" and never returns
    mus *= gate[:, None]
    mix = mus + ducked(amb.x, -5) + ducked(fx.x, -4) + ducked(ff_bus.x, -5) + vo * 10 ** (7.5 / 20)
    n_out = int(DURATION * SR)
    mix = mix[:n_out]
    if 'blackout' in M:        # hard cut to black: everything stops dead, then silence + one hopeless honk
        i0 = int(M['blackout'] * SR)
        mix[i0 - 240:i0] *= np.linspace(1, 0, 240)[:, None]
        mix[i0:] = 0
        vo[i0:] = 0; mus[i0:] = 0
        honk = lowpass(load('horn3'), 5000) * 10 ** (9 / 20)
        h0 = int(M['end_honk'] * SR)
        n_h = min(len(honk), n_out - h0)
        mix[h0:h0 + n_h] += honk[:n_h]
    mix = fade(mix, 0.0, 0.008)          # hard cut at the end (8 ms only to avoid a click)
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
