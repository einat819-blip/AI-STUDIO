"""Small synthesis toolkit used to build original (studio-owned) music and SFX.

Everything here is generated from math, no samples, so the studio owns the
result outright and there is no third-party licence to clear.
"""
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
RNG = np.random.default_rng(1234)


def t_axis(dur):
    return np.arange(int(round(dur * SR))) / SR


def silence(dur, ch=2):
    return np.zeros((int(round(dur * SR)), ch))


def noise(dur, color="white", rng=RNG):
    n = rng.standard_normal(int(round(dur * SR)))
    if color == "pink":
        # Voss-ish pink via 1/f filter on spectrum
        f = np.fft.rfft(n)
        k = np.arange(len(f))
        k[0] = 1
        f = f / np.sqrt(k)
        n = np.fft.irfft(f, len(n))
    elif color == "brown":
        n = np.cumsum(n)
        n = signal.lfilter([1, -1], [1, -0.995], n)
    return n / (np.max(np.abs(n)) + 1e-9)


def env_adsr(n, a, d, s, r, sustain_len=None):
    """ADSR envelope with times in seconds; returns length n."""
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    if sustain_len is None:
        s_n = max(0, n - a_n - d_n - r_n)
    else:
        s_n = int(sustain_len * SR)
    e = np.concatenate([
        np.linspace(0, 1, max(a_n, 1), endpoint=False),
        np.linspace(1, s, max(d_n, 1), endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, max(r_n, 1)),
    ])
    if len(e) < n:
        e = np.concatenate([e, np.zeros(n - len(e))])
    return e[:n]


def env_exp(n, tau, attack=0.002):
    t = np.arange(n) / SR
    e = np.exp(-t / tau)
    a_n = max(int(attack * SR), 1)
    e[:a_n] *= np.linspace(0, 1, a_n)
    return e


def bp(x, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def lp(x, fc, order=4):
    sos = signal.butter(order, fc, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def hp(x, fc, order=4):
    sos = signal.butter(order, fc, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def peaking(x, f0, q, gain_db):
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a, -2 * np.cos(w0), 1 - alpha * a]
    aa = [1 + alpha / a, -2 * np.cos(w0), 1 - alpha / a]
    return signal.lfilter(b, aa, x, axis=0)


def tv_lowpass(x, fc_curve):
    """Time-varying one-pole lowpass (cheap filter sweep). fc_curve per sample."""
    y = np.zeros_like(x)
    a = np.exp(-2 * np.pi * np.clip(fc_curve, 20, SR / 2.2) / SR)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


_WT_CACHE = {}


def _wavetable(kind, kmax, size=4096):
    key = (kind, kmax)
    if key not in _WT_CACHE:
        ph = 2 * np.pi * np.arange(size) / size
        y = np.zeros(size)
        if kind == "saw":
            for k in range(1, kmax + 1):
                y += np.sin(k * ph) / k
            y *= 2 / np.pi
        else:  # square
            for k in range(1, kmax + 1, 2):
                y += np.sin(k * ph) / k
            y *= 4 / np.pi
        _WT_CACHE[key] = np.append(y, y[0])
    return _WT_CACHE[key]


def _osc(kind, freq, n, phase=0.0, kmax_cap=60):
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, float)
    fmax = float(np.max(f))
    kmax = int(min(kmax_cap, max(1, (SR / 2.6) / fmax)))
    tab = _wavetable(kind, kmax)
    size = len(tab) - 1
    ph = (np.cumsum(f) / SR + phase / (2 * np.pi)) % 1.0
    idx = ph * size
    i0 = idx.astype(int)
    frac = idx - i0
    return tab[i0] * (1 - frac) + tab[i0 + 1] * frac


def saw(freq, n, phase=0.0):
    """Band-limited sawtooth (wavetable)."""
    return _osc("saw", freq, n, phase)


def square(freq, n, kmax=30):
    return _osc("square", freq, n, 0.0, kmax_cap=kmax)


def sine(freq, n, phase=0.0):
    if np.isscalar(freq):
        return np.sin(2 * np.pi * freq * np.arange(n) / SR + phase)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR + phase)


def bell(freq, dur, partials=((1, 1.0, 1.0), (2.0, 0.45, 0.6), (2.76, 0.3, 0.45),
                              (4.07, 0.15, 0.3), (5.4, 0.08, 0.22)), tau=0.6, detune=0.0):
    n = int(dur * SR)
    y = np.zeros(n)
    for ratio, amp, tau_mul in partials:
        y += amp * sine(freq * ratio, n) * env_exp(n, tau * tau_mul, attack=0.001)
        if detune:
            y += amp * 0.5 * sine(freq * ratio * (1 + detune), n) * env_exp(n, tau * tau_mul, 0.001)
    # never end on a hard edge: fade the last 30% to zero
    k = int(n * 0.3)
    y[-k:] *= np.linspace(1, 0, k) ** 2
    return y


def karplus(freq, dur, damping=0.996, bright=0.5, rng=RNG):
    """Karplus-Strong plucked string."""
    n = int(dur * SR)
    period = SR / freq
    p = int(period)
    frac = period - p
    buf = rng.uniform(-1, 1, p + 2)
    buf = lp(buf, 1500 + bright * 9000, order=1) if p > 16 else buf
    out = np.zeros(n)
    idx = 0
    prev = 0.0
    for i in range(n):
        a = buf[idx % len(buf)]
        b = buf[(idx + 1) % len(buf)]
        v = damping * (0.5 * (a + b))
        # fractional delay compensation (allpass-ish)
        v = v * (1 - frac * 0.1) + prev * frac * 0.1
        out[i] = a
        buf[idx % len(buf)] = v
        prev = v
        idx += 1
    return out


def pan(mono, p=0.0):
    """Constant-power pan, p in [-1, 1]."""
    if np.isscalar(p):
        ang = (p + 1) * np.pi / 4
        return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1)
    ang = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1)


def to_stereo(x):
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    return x


def make_ir(dur=1.6, predelay=0.012, damp_hz=6000, rng=RNG, early=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    irs = []
    for ch in range(2):
        nn = rng.standard_normal(n) * np.exp(-6.9 * t / dur)
        nn = lp(nn, damp_hz, order=2)
        pd = np.zeros(int(predelay * SR))
        ir = np.concatenate([pd, nn])
        if early:
            for k in range(6):
                pos = int((0.004 + 0.011 * k + rng.uniform(0, 0.006)) * SR)
                if pos < len(ir):
                    ir[pos] += rng.uniform(0.3, 0.7) * (0.8 ** k)
        irs.append(ir)
    m = max(len(i) for i in irs)
    ir = np.stack([np.pad(i, (0, m - len(i))) for i in irs], axis=1)
    return ir / np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))


def reverb(x, wet=0.25, dur=1.6, damp_hz=6000, predelay=0.012):
    x = to_stereo(x)
    ir = make_ir(dur, predelay, damp_hz)
    out = np.zeros((len(x) + len(ir) - 1, 2))
    for ch in range(2):
        out[:, ch] = signal.fftconvolve(x[:, ch], ir[:, ch])
    dry = np.pad(x, ((0, len(ir) - 1), (0, 0)))
    return dry * (1 - wet) + out * wet * 0.6


def place(dst, src, t0, gain=1.0):
    """Mix src into dst at time t0 (seconds). Grows dst if needed."""
    src = to_stereo(src)
    i0 = int(round(t0 * SR))
    if i0 < 0:
        src = src[-i0:]
        i0 = 0
    end = i0 + len(src)
    if end > len(dst):
        dst = np.concatenate([dst, np.zeros((end - len(dst), 2))])
    dst[i0:end] += src * gain
    return dst


def fade(x, fin=0.003, fout=0.01):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def normalize(x, peak_db=-1.0):
    p = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (peak_db / 20) / p)


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def write(path, x, peak_db=None):
    x = to_stereo(x)
    if peak_db is not None:
        x = normalize(x, peak_db)
    x = np.clip(x, -1, 1)
    sf.write(path, x.astype(np.float32), SR, subtype="PCM_24")


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
NOTE.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})


def nm(name):
    """'F#5' -> midi number."""
    if name[1] in "#b" and len(name) > 2:
        p, o = name[:2], int(name[2:])
    else:
        p, o = name[0], int(name[1:])
    return 12 * (o + 1) + NOTE[p]
