# -*- coding: utf-8 -*-
"""Word-level Hebrew transcription of the narration (ivrit-ai Whisper, CTranslate2).

  python3 scripts/transcribe.py <model_dir> [narration] [out.json]

Model: ivrit-ai/whisper-large-v3-turbo-ct2 (Hugging Face). Output: every word
with start/end seconds and confidence, plus the segment texts.
"""
import json
import os
import subprocess
import sys

import numpy as np

from faster_whisper import WhisperModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    model_dir = sys.argv[1]
    audio = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source", "audio", "narration.wav")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "edit", "narration_transcript.json")
    model = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
    # decode with ffmpeg to 16 kHz mono float32 (avoids PyAV version issues)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, np.float32)
    segments, info = model.transcribe(pcm, language="he", beam_size=5, word_timestamps=True,
                                      vad_filter=False, condition_on_previous_text=False)
    segs, words = [], []
    for s in segments:
        segs.append(dict(start=round(s.start, 3), end=round(s.end, 3), text=s.text.strip()))
        for w in s.words:
            words.append(dict(w=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3),
                              p=round(w.probability, 3)))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dict(model=os.path.basename(model_dir.rstrip("/")), audio=os.path.basename(audio),
                       duration=round(info.duration, 3), segments=segs, words=words), f, ensure_ascii=False, indent=1)
    for s in segs:
        print(f"{s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
    print("words:", len(words), "->", out)


if __name__ == "__main__":
    main()
