"""Soft synthesized bubble pops at caption appearance times -> stereo 48k wav."""
import sys, wave, numpy as np
sr = 48000
length = float(sys.argv[2])
# (time, start_hz, end_hz, peak_dbfs)
POPS = [
    (0.58, 450, 1300, -12),   # "אבאאא!"
    (2.19, 470, 1350, -12),   # "8:00 בבוקר!"
    (3.46, 300, 850, -15),    # dad "בבוקר?!" (lower voice)
    (4.44, 480, 1400, -17),   # "כן, בבוקר!"
    (5.98, 460, 1300, -17),   # "אל תאחר!"
    (8.80, 420, 1200, -15),   # "יש הזמנות"
    (8.86, 520, 1500, -17),   #   second bubble right after
]
out = np.zeros(int(length * sr))
rng = np.random.default_rng(7)
for t0, f0, f1, db in POPS:
    n = int(0.16 * sr); t = np.arange(n) / sr
    f = f0 * (f1 / f0) ** np.minimum(t / 0.045, 1.0)
    ph = 2 * np.pi * np.cumsum(f) / sr
    env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.035)
    s = (np.sin(ph) + 0.15 * np.sin(2 * ph)) * env
    s += 0.08 * rng.standard_normal(n) * np.exp(-t / 0.0015)   # tiny click on the attack
    s *= 10 ** (db / 20) / np.max(np.abs(s))
    i = int(t0 * sr); out[i:i + n] += s[: len(out) - i]
pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
st = np.repeat(pcm[:, None], 2, axis=1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())
