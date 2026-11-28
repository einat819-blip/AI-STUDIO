"""Split the ElevenLabs voice take into one clip per line, with word timings for the captions.

Input: the full take (mp3/wav) and words.json (faster-whisper, ivrit-ai large-v3-turbo, word timestamps).
Clip bounds come from the energy envelope (silences), the words from the transcript, re-anchored to
the real onset of each line. Output: <work>/vo/<slot>.wav and <work>/vo/lines.json.
"""
import json, os, subprocess, sys, wave
import numpy as np

TAKE, WORDS, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
SR = 48000
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', TAKE, '-ar', str(SR), '-ac', '1', '-f', 's16le', '-'],
                     capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
words = json.load(open(WORDS))

# slot: (clip start, clip end, [(first word index, actual onset of that word)])  times in seconds in the take
LINES = {
    'd1a':  (0.00, 0.90, [(0, 0.06)]),            # אלגנטית?
    'd1b':  (1.26, 2.46, [(1, 1.31)]),            # התחלת טוב.
    'd2a':  (2.86, 3.53, [(3, 2.91)]),            # אריה?
    'd2b':  (3.67, 4.88, [(4, 3.71)]),            # איזה מקורי.
    'd3a':  (5.05, 5.96, [(6, 5.09)]),            # תמחק, תמחק!
    'd3b':  (6.21, 7.30, [(8, 6.26)]),            # יהודה רואה את זה.
    'd4':   (7.51, 9.64, [(12, 7.55), (14, 8.52)]),  # טוב, מספיק, | תן לי לכתוב את התסריט.
    'd7a':  (16.56, 18.08, [(30, 16.60)]),        # יש לכם רעיון לסרט?
    'brand': (20.15, 22.02, [(38, 20.19)]),       # AI NATI STUDIOS
}
# word index ranges per slot (inclusive start, exclusive end) in words.json order
RANGES = {'d1a': (0, 1), 'd1b': (1, 3), 'd2a': (3, 4), 'd2b': (4, 6), 'd3a': (6, 8), 'd3b': (8, 12),
          'd4': (12, 19), 'd7a': (30, 34), 'brand': (38, 41)}

out_dir = os.path.join(WORK, 'vo'); os.makedirs(out_dir, exist_ok=True)
meta = {}
for slot, (cs, ce, anchors) in LINES.items():
    a, b = int(cs * SR), int(ce * SR)
    clip = x[a:b].copy()
    f = int(0.008 * SR)
    clip[:f] *= np.linspace(0, 1, f); clip[-f:] *= np.linspace(1, 0, f)
    with wave.open(os.path.join(out_dir, f'{slot}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(clip, -1, 1) * 32767).astype(np.int16).tobytes())
    i0, i1 = RANGES[slot]
    ws = []
    for i in range(i0, i1):
        # the most recent anchor at or before this word sets its shift
        anchor_idx, onset = max([an for an in anchors if an[0] <= i], key=lambda an: an[0])
        shift = onset - words[anchor_idx]['s']
        ws.append([words[i]['w'], round(words[i]['s'] + shift - cs, 3), round(words[i]['e'] + shift - cs, 3)])
    meta[slot] = {'dur': round(ce - cs, 3), 'words': ws}
json.dump(meta, open(os.path.join(out_dir, 'lines.json'), 'w'), ensure_ascii=False, indent=1)
for k, v in meta.items():
    print(k, v['dur'], ' '.join(f"{w[0]}@{w[1]:.2f}" for w in v['words']))
