"""Print octave-band energy (dB, relative to the 1 kHz band) of a WAV file section."""
import sys
import numpy as np
import soundfile as sf
from scipy import signal

def bands(path, t0=0, t1=None):
    x, sr = sf.read(path)
    if x.ndim == 2:
        x = x.mean(axis=1)
    x = x[int(t0 * sr): int(t1 * sr) if t1 else None]
    f, p = signal.welch(x, sr, nperseg=8192)
    centers = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    out = {}
    for c in centers:
        lo, hi = c / np.sqrt(2), c * np.sqrt(2)
        m = (f >= lo) & (f < hi)
        out[c] = 10 * np.log10(np.sum(p[m]) + 1e-20)
    ref = out[1000]
    return {k: round(v - ref, 1) for k, v in out.items()}

if __name__ == "__main__":
    path = sys.argv[1]
    t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    t1 = float(sys.argv[3]) if len(sys.argv) > 3 else None
    print(path, t0, t1, bands(path, t0, t1))
