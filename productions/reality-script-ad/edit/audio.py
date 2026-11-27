import numpy as np, wave, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from timeline import *
SP = os.environ.get('AINATI_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
SR = 48000
DUR = TOTAL_FRAMES / FPS
N = int(round(DUR * SR))
mix = np.zeros((N, 2), np.float32)
music_bus = np.zeros((N, 2), np.float32)

def load(name):
    w = wave.open(f'{SP}/wav/{name}.wav'); n = w.getnframes()
    return np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768

def db(x): return 10 ** (x / 20)

def rms_db(x):
    a = x.mean(1); a = a[np.abs(a) > 1e-4]
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)

def clip(src, f0, f1=None):
    a = int(f0 * SR); b = len(src) if f1 is None else int(f1 * SR)
    return src[a:b].copy()

def fade(x, fin=0.005, fout=0.005):
    x = x.copy(); n = len(x)
    i = min(n, int(fin * SR)); o = min(n, int(fout * SR))
    if i: x[:i] *= np.linspace(0, 1, i)[:, None]
    if o: x[-o:] *= np.linspace(1, 0, o)[:, None]
    return x

def place(bus, x, t, gain_db=0.0):
    a = int(round(t * SR))
    if a < 0: x = x[-a:]; a = 0
    b = min(N, a + len(x))
    bus[a:b] += x[:b - a] * db(gain_db)

def norm_to(x, target_rms_db):
    return x * db(target_rms_db - rms_db(x))

# ---------- sources
m1 = load('m1_comic'); m2 = load('m2_romance'); m5 = load('m5_finaleB')
roar = load('roar'); snap = load('snap'); typing = load('typing'); enter = load('enter')
glitch = load('glitch'); shimmer = load('shimmer'); boom = load('boom'); whoosh = load('whoosh')

# ---------- keystrokes cut from the typing recording
mono = typing.mean(1); hop = 96
env = np.array([np.abs(mono[i:i + hop]).max() for i in range(0, len(mono) - hop, hop)])
on = [i for i in range(2, len(env)) if env[i] > 0.12 and env[i] > 3 * env[i - 2:i].max() + 1e-4]
keys = []
last = -999
for i in on:
    s = i * hop
    if s - last < int(0.06 * SR): continue
    last = s
    k = typing[max(0, s - int(0.004 * SR)): s + int(0.075 * SR)]
    if len(k) < int(0.05 * SR): continue
    keys.append(fade(k, 0.002, 0.03))
keys = [k / (np.abs(k).max() + 1e-9) for k in keys]
print('keystrokes extracted:', len(keys))
rng = np.random.default_rng(7)
def type_sounds(times, gain=-20.0, bus=mix):
    for t in times:
        k = keys[rng.integers(len(keys))]
        place(bus, k, t, gain + rng.uniform(-2.5, 1.5))
enter_n = enter / np.abs(enter).max()

# ---------- room tone (keeps silences alive, never digital zero)
rt = rng.standard_normal((N, 2)).astype(np.float32)
# pink-ish: cumulative low-pass
from math import exp
a = exp(-2 * np.pi * 900 / SR)
for ch in range(2):
    y = np.zeros(N, np.float32); prev = 0.0
    xin = rt[:, ch]
    # vectorised one-pole via lfilter substitute
    out = np.empty(N, np.float32); acc = 0.0
    for i in range(0, N, 4800):
        seg = xin[i:i + 4800]
        z = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc = a * acc + (1 - a) * v; z[j] = acc
        out[i:i + 4800] = z
    rt[:, ch] = out
rt = norm_to(rt, -58)
mix += rt

# ---------- S1: comic bed + prompt typing
s1 = fade(clip(m1, 0.50, 0.50 + CUT1), 0.004, 0.012)
music_bus_s1 = norm_to(s1, -20)
place(music_bus, music_bus_s1, 0.0)
type_sounds(TYPE1)
type_sounds([SELECT_AT, SELECT_AT + 0.06], gain=-15)
type_sounds(TYPE2)
place(mix, enter_n, ENTER1, -9)

# ---------- S2: lion
ra = fade(clip(roar, 0.25, 1.50), 0.003, 0.08)
rb = fade(clip(roar, 2.30, 3.70), 0.06, 0.25)
lvl = rms_db(np.concatenate([ra, rb]))
place(mix, ra, CUT1, -15.5 - lvl)
place(mix, rb, 6.15, -16 - lvl)
type_sounds(TYPE3)
place(mix, enter_n, ENTER2, -9)

# ---------- S3: romance sting, hard stop
rom = fade(clip(m2, 0.45, 0.45 + (11.60 - CUT2)), 0.003, 0.02)
place(music_bus, norm_to(rom, -19), CUT2)
type_sounds(BKSP, gain=-15)
g = fade(clip(glitch, 0.85, 1.50), 0.004, 0.08)
place(mix, norm_to(g, -21), GLITCH0 - 0.03)
wz = fade(clip(whoosh, 0.15, 1.0), 0.005, 0.1)
place(mix, norm_to(wz, -24), GLITCH0 - 0.10)
back = fade(clip(m1, 2.62, 2.62 + (SNAP_T - 14.30)), 0.05, 0.012)
place(music_bus, norm_to(back, -20), 14.30)

# ---------- S4: snap, shimmer, finale
place(mix, snap / np.abs(snap).max(), SNAP_T - 0.45, -6)
sh = fade(clip(shimmer, 0.0, 4.6), 0.005, 0.6)
place(mix, norm_to(sh, -25), SNAP_T + 0.03)
# reversed shimmer = riser that lands exactly on the reveal impact
rv = clip(shimmer, 0.15, 3.2)[::-1].copy()
rv = fade(rv, 0.4, 0.01)
place(mix, norm_to(rv, -24), 20.46 - len(rv) / SR)
fin = clip(m5, 0.0, DUR - CUT4)
fin = fade(fin, 0.005, 0.35)
fin = norm_to(fin, -19)
place(music_bus, fin, CUT4)
bm = fade(clip(boom, 0.0, 4.0), 0.002, 1.5)
place(mix, norm_to(bm, -21), 20.42)

# ---------- S5: CTA prompt pop + typing (quiet under music)
place(mix, norm_to(fade(clip(whoosh, 0.1, 0.9), 0.005, 0.1), -30), P4_SHOW - 0.08)
type_sounds(TYPE_CTA1 + TYPE_CTA2, gain=-22)

# ---------- duck the music bus under dialogue / VO slots (they get voice later)
duck = np.ones(N, np.float32)
slots = [(d[0], d[1]) for d in DIALOGUE] + [VO_SLOT[:2]]
for (t0, t1) in slots:
    a0, a1 = int((t0 - 0.08) * SR), int((t1 + 0.15) * SR)
    r = int(0.08 * SR)
    seg = np.full(a1 - a0, db(-6), np.float32)
    seg[:r] = np.linspace(1, db(-6), r); seg[-r:] = np.linspace(db(-6), 1, r)
    duck[a0:a1] = np.minimum(duck[a0:a1], seg)
mix += music_bus * duck[:, None]

peak = np.abs(mix).max()
print('pre-master peak dBFS', 20 * np.log10(peak))
mix *= db(-3) / peak
out = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
w = wave.open(f'{SP}/build/mix_raw.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(out.tobytes()); w.close()
print('wrote mix_raw.wav', DUR)

# ---------- master: about -14 LUFS integrated, limiter keeps peaks under -1.5 dBFS
import re, subprocess
meas = subprocess.run(['ffmpeg', '-nostats', '-i', f'{SP}/build/mix_raw.wav', '-af', 'ebur128', '-f', 'null', '-'],
                      capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', meas)[-1])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{SP}/build/mix_raw.wav', '-af',
                f'volume={-14.0 - I:.2f}dB,alimiter=limit=0.82:attack=3:release=60:level=false',
                '-c:a', 'pcm_s16le', f'{SP}/build/mix_master.wav'], check=True)
print(f'mastered: input {I} LUFS -> mix_master.wav')
