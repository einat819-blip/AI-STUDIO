"""Sound design and mix for the AI NATI STUDIOS "reality script" ad, version 4.

Places music cues, sound effects and (when present) the voice files on the timeline,
ducks the music under every dialogue / voice-over slot, then masters to about -14 LUFS.
Voice files are picked up automatically from <work>/vo/<slot>.wav (d1..d5, vo).
"""
import numpy as np, wave, sys, os, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *

SP = os.environ.get('AINATI_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
SR = 48000
DUR = TOTAL_FRAMES / FPS
N = int(round(DUR * SR))
mix = np.zeros((N, 2), np.float32)
music_bus = np.zeros((N, 2), np.float32)
vo_bus = np.zeros((N, 2), np.float32)


def load(path):
    w = wave.open(path); n = w.getnframes()
    d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    return d.reshape(-1, w.getnchannels()) if w.getnchannels() == 2 else np.repeat(d[:, None], 2, 1)


def lw(name):
    return load(f'{SP}/wav/{name}.wav')


def db(x):
    return 10 ** (x / 20)


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


def place(bus, x, t, gain_db=0.0, until=None):
    a = int(round(t * SR))
    if a < 0:
        x = x[-a:]; a = 0
    b = min(N, a + len(x))
    if until is not None:
        b = min(b, int(round(until * SR)))
        x = fade(x[:b - a], 0.0, 0.012)
    bus[a:b] += x[:b - a] * db(gain_db)


def norm_to(x, target):
    return x * db(target - rms_db(x))


m1, m2, m5 = lw('m1_comic'), lw('m2_romance'), lw('m5_finaleB')
roar, snap, typing, enter = lw('roar'), lw('snap'), lw('typing'), lw('enter')
glitch, shimmer, boom, whoosh = lw('glitch'), lw('shimmer'), lw('boom'), lw('whoosh')

# keystrokes cut from the typing recording
mono = typing.mean(1); hop = 96
env = np.array([np.abs(mono[i:i + hop]).max() for i in range(0, len(mono) - hop, hop)])
keys, last = [], -10 ** 9
for i in range(2, len(env)):
    if env[i] > 0.12 and env[i] > 3 * env[i - 2:i].max() + 1e-4:
        s = i * hop
        if s - last < int(0.06 * SR):
            continue
        last = s
        k = typing[max(0, s - int(0.004 * SR)): s + int(0.075 * SR)]
        if len(k) >= int(0.05 * SR):
            k = fade(k, 0.002, 0.03); keys.append(k / (np.abs(k).max() + 1e-9))
rng = np.random.default_rng(7)


def type_sounds(times, gain=-20.0):
    for t in times:
        place(mix, keys[rng.integers(len(keys))], t, gain + rng.uniform(-2.5, 1.5))


enter_n = enter / np.abs(enter).max()

# room tone so the comic silences never drop to digital zero
noise = rng.standard_normal((N, 2)).astype(np.float32)
spec = np.fft.rfft(noise, axis=0)
f = np.fft.rfftfreq(N, 1 / SR)
spec *= (1 / np.sqrt(np.maximum(f, 20)))[:, None] * (f < 6000)[:, None]
mix += norm_to(np.fft.irfft(spec, n=N, axis=0).astype(np.float32), -58)

# S1 opening: comic bed until the reveal, typing, Enter
place(music_bus, norm_to(fade(clip(m1, 0.50, 0.50 + REVEAL[0]), 0.004, 0.012), -20), 0.0)
type_sounds(TYPE1)
type_sounds([SELECT_AT, SELECT_AT + 0.06], gain=-17)
type_sounds(TYPE2)
place(mix, enter_n, ENTER1, -9)

# S2 lion: roar on the pull back, sub drop, cut dead into the deadpan
ra = fade(clip(roar, 0.25, 1.50), 0.003, 0.06)
rb = fade(clip(roar, 2.30, 3.70), 0.05, 0.01)
lvl = rms_db(np.concatenate([ra, rb]))
place(mix, ra, ROAR_ON - 0.05, -15 - lvl)
place(mix, rb, ROAR_ON + 0.95, -15.5 - lvl, until=CUT_B)
tt = np.arange(int(1.2 * SR)) / SR
sub = np.sin(2 * np.pi * np.cumsum(np.linspace(58, 32, len(tt))) / SR) * np.exp(-tt * 3.2)
sub = fade(np.repeat(sub[:, None], 2, 1).astype(np.float32), 0.004, 0.2)
place(mix, norm_to(sub, -19), ROAR_ON + 0.05)
type_sounds(TYPE3)
place(mix, enter_n, ENTER2, -9)

# S3 the man: romance sting, dead stop on her look, panic backspace, clean digital delete
place(music_bus, norm_to(fade(clip(m2, 0.45, 0.45 + (LOOK_T - CUT_C)), 0.003, 0.008), -19), CUT_C)
type_sounds(BKSP, gain=-16)
place(mix, enter_n, ERASE_T, -12)
place(mix, norm_to(fade(clip(whoosh, 0.15, 0.95), 0.004, 0.12), -23), ERASE_T + 0.02)
place(mix, norm_to(fade(clip(glitch, 0.85, 1.10), 0.003, 0.05), -28), ERASE_T + 0.10)
place(music_bus, norm_to(fade(clip(m1, 2.62, 2.62 + (CUT_D - PIX_OUT - S3E_T)), 0.05, 0.015), -20), S3E_T)

# laptop rebuild: a short data whoosh and block ticks
place(mix, norm_to(fade(clip(whoosh, 0.10, 0.80), 0.003, 0.08), -24), CUT_D - PIX_OUT - 0.03)
place(mix, norm_to(fade(clip(glitch, 1.20, 1.45), 0.003, 0.05), -29), CUT_D)

# S4 snap, shimmer, riser into the reveal impact
place(mix, snap / np.abs(snap).max(), SNAP_T - 0.45, -6)
place(mix, norm_to(fade(clip(shimmer, 0.0, 4.6), 0.005, 0.6), -25), SNAP_T + 0.03)
rv = fade(clip(shimmer, 0.15, 3.2)[::-1].copy(), 0.4, 0.01)
place(mix, norm_to(rv, -24), IMPACT_T - len(rv) / SR)
place(mix, norm_to(fade(clip(boom, 0.0, 4.0), 0.002, 1.5), -21), IMPACT_T - 0.05)

# finale cue with a 4-bar loop so it keeps building to the last frame, final hit on the end card
xf = int(0.015 * SR)
part_a = clip(m5, 0.0, LOOP_E)
part_b = clip(m5, LOOP_S, None)
ramp = np.linspace(0, 1, xf)[:, None]
joined = np.concatenate([part_a[:-xf], part_a[-xf:] * (1 - ramp) + part_b[:xf] * ramp, part_b[xf:]])
fin = norm_to(fade(joined[: int((DUR - MUSIC_FINALE_START) * SR)], 0.005, 0.25), -19)
# lift: the cue grows about 3.5 dB from the studio name to the final hit
n0 = int((COMPACT_T - MUSIC_FINALE_START) * SR); n1 = int((FINAL_HIT - MUSIC_FINALE_START) * SR)
gain = np.ones(len(fin), np.float32)
gain[n0:n1] = np.linspace(1, db(3.5), max(1, n1 - n0)); gain[n1:] = db(3.5)
place(music_bus, fin * gain[:, None], MUSIC_FINALE_START)

# golden-light transition: shimmer rising into the cut, a soft whoosh through it
place(mix, norm_to(fade(clip(shimmer, 0.0, 1.6), 0.25, 0.5), -24), SWIRL[0])
place(mix, norm_to(fade(clip(whoosh, 0.10, 0.95), 0.01, 0.15), -26), CUT_E - 0.22)
# her fingertip light and the lines written by it
place(mix, norm_to(fade(clip(shimmer, 0.5, 1.4), 0.02, 0.4), -26), FINGER_T)
place(mix, norm_to(fade(clip(shimmer, 0.6, 1.2), 0.02, 0.3), -30), CTA2_T)
# studio name glint
place(mix, norm_to(fade(clip(shimmer, 0.3, 1.5), 0.02, 0.5), -27), NAME_T)
# a soft pop for each network badge, on the beat
tt = np.arange(int(0.12 * SR)) / SR
thump = np.sin(2 * np.pi * np.cumsum(np.linspace(190, 90, len(tt))) / SR) * np.exp(-tt * 38)
tick = rng.standard_normal(len(tt)) * np.exp(-tt * 140)
pop = np.repeat((thump * 0.8 + tick * 0.25)[:, None], 2, 1).astype(np.float32)
pop = fade(pop, 0.001, 0.03)
for i, ts in enumerate(SOC_TIMES):
    place(mix, norm_to(pop, -21 + i * 0.8), ts - 0.005)
# build into the final hit, then an airy tail under the last second
rv2 = fade(clip(shimmer, 0.15, 3.0)[::-1].copy(), 0.5, 0.01)
place(mix, norm_to(rv2, -23), FINAL_HIT - len(rv2) / SR)
place(mix, norm_to(fade(clip(boom, 0.0, DUR - FINAL_HIT + 0.05), 0.002, 0.2), -20), FINAL_HIT - 0.04)

# voice: dialogue and voice-over slots (files optional until the recordings arrive)
slots = [(name, lines[0][0][2], t_end) for name, lines, t_end, _ in DIALOGUE] + [VO_SLOT]
for name, t0, t1 in slots:
    p = f'{SP}/vo/{name}.wav'
    if os.path.exists(p):
        place(vo_bus, norm_to(load(p), -17), t0)
        print('voice placed', name)

duck = np.ones(N, np.float32)
for name, t0, t1 in slots:
    a0, a1 = int((t0 - 0.08) * SR), int((t1 + 0.15) * SR)
    r = int(0.08 * SR)
    seg = np.full(a1 - a0, db(-6), np.float32)
    seg[:r] = np.linspace(1, db(-6), r); seg[-r:] = np.linspace(db(-6), 1, r)
    duck[a0:a1] = np.minimum(duck[a0:a1], seg)
mix += music_bus * duck[:, None] + vo_bus

end_f = int(0.25 * SR)
mix[-end_f:] *= np.linspace(1, 0, end_f)[:, None]
mix *= db(-3) / np.abs(mix).max()
os.makedirs(f'{SP}/build', exist_ok=True)
w = wave.open(f'{SP}/build/mix_raw.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

meas = subprocess.run(['ffmpeg', '-nostats', '-i', f'{SP}/build/mix_raw.wav', '-af', 'ebur128', '-f', 'null', '-'],
                      capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', meas)[-1])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{SP}/build/mix_raw.wav', '-af',
                f'volume={-14.0 - I:.2f}dB,alimiter=limit=0.78:attack=2:release=60:level=false',
                '-c:a', 'pcm_s16le', f'{SP}/build/mix_master.wav'], check=True)
print(f'mix {DUR:.2f}s, input {I} LUFS -> mix_master.wav')
