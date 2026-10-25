#!/usr/bin/env python3
"""Builds the 20s vertical (1080x1920) AI nati studios showreel.

Usage: build_showreel.py <clips_dir> <captions_dir> <music.mp3> <out.mp4>

Clips are the studio's own Higgsfield generations (named by the first 8 chars
of the generation id). Cuts land on the music's downbeats (~123 BPM).
"""
import subprocess
import sys

clips_dir, caps_dir, music, out = sys.argv[1:5]

W, H, FPS = 1080, 1920, 30
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"

# (clip id, source in, source out, timeline start, timeline end, extra pre-filter)
SHOTS = [
    ("d4c54c44", 0.60, 4.06, 0.000, 2.351, ""),                         # hook: awkward in front of the ring light
    ("0c915f0f", 0.50, 2.45, 2.351, 4.301, ""),                         # hero walk
    ("310bfa44", 0.70, 5.30, 4.301, 6.252, ""),                         # birthday glow-up
    ("c3ed9f72", 1.40, 3.84, 6.252, 8.202, ""),                         # wedding, golden hour
    ("efa9432c", 2.20, 4.90, 8.202, 9.665, ""),                         # ad: sunglasses down
    ("1685b331", 0.80, 4.20, 9.665, 11.128, ""),                        # ad: filthy filter reveal
    ("ae5eddbb", 1.00, 4.90, 11.128, 13.079, ""),                       # ad: AC comes back to life
    ("4c91d2bb", 3.00, 10.00, 13.079, 16.004, "crop=779:1385:254:95,"),  # poster comes to life (FB UI cropped off)
]
END_START, END = 16.004, 20.0

# (caption png, start, end)
CAPTIONS = [
    ("hook", 0.15, 2.351),
    ("movie", 2.45, 4.301),
    ("birthday", 4.40, 6.252),
    ("wedding", 6.35, 8.202),
    ("business", 8.30, 13.079),
    ("photos", 13.18, 16.004),
    ("tag", 2.351, 16.004),
    ("end", 16.25, END),
]

inputs, filters, seg_labels = [], [], []

for i, (cid, a, b, t0, t1, pre) in enumerate(SHOTS):
    inputs += ["-i", f"{clips_dir}/{cid}.mp4"]
    speed = (b - a) / (t1 - t0)
    filters.append(
        f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{speed:.4f},{pre}{FILL},fps={FPS},"
        f"trim=duration={t1 - t0:.3f},setsar=1,format=yuv420p[s{i}]"
    )
    seg_labels.append(f"[s{i}]")

# End card background: the last sunset second of the photo clip, slowed, blurred and darkened.
n = len(SHOTS)
inputs += ["-i", f"{clips_dir}/4c91d2bb.mp4"]
end_len = END - END_START
filters.append(
    f"[{n}:v]trim=9.0:10.04,setpts=(PTS-STARTPTS)*{end_len / 1.04:.4f},crop=779:1385:254:95,{FILL},fps={FPS},"
    f"gblur=sigma=22,eq=brightness=-0.30:contrast=0.9:saturation=1.1,vignette=PI/3.5,tpad=stop_mode=clone:stop_duration=1,"
    f"trim=duration={end_len:.3f},fade=in:st=0:d=0.25,setsar=1,format=yuv420p[s{n}]"
)
seg_labels.append(f"[s{n}]")
filters.append(f"{''.join(seg_labels)}concat=n={len(seg_labels)}:v=1:a=0[base]")

# White flash on the drop (hook -> "I make a movie out of it").
k = n + 1
inputs += ["-f", "lavfi", "-i", f"color=white:s={W}x{H}:r={FPS}:d=0.24"]
filters.append(
    f"[{k}:v]format=rgba,colorchannelmixer=aa=0.85,fade=in:st=0:d=0.12:alpha=1,"
    f"fade=out:st=0.12:d=0.12:alpha=1,setpts=PTS+{2.351 - 0.12}/TB[flash]"
)
filters.append("[base][flash]overlay=0:0:eof_action=pass[v0]")

prev = "v0"
for j, (name, t0, t1) in enumerate(CAPTIONS):
    idx = k + 1 + j
    inputs += ["-loop", "1", "-t", f"{END}", "-i", f"{caps_dir}/{name}.png"]
    fade_in = 0.3 if name == "end" else 0.12
    fade_out = "" if t1 >= END else f",fade=out:st={t1 - 0.08:.3f}:d=0.08:alpha=1"
    filters.append(f"[{idx}:v]format=rgba,fade=in:st={t0}:d={fade_in}:alpha=1{fade_out}[c{j}]")
    filters.append(f"[{prev}][c{j}]overlay=0:0:enable='between(t,{t0},{t1})'[v{j + 1}]")
    prev = f"v{j + 1}"

m = k + 1 + len(CAPTIONS)
inputs += ["-i", music]
filters.append(f"[{m}:a]atrim=0:{END},asetpts=PTS-STARTPTS,afade=t=out:st={END - 0.6}:d=0.6,loudnorm=I=-14:TP=-1.5:LRA=11[a]")

cmd = [
    "ffmpeg", "-v", "error", "-y", *inputs,
    "-filter_complex", ";".join(filters),
    "-map", f"[{prev}]", "-map", "[a]",
    "-t", f"{END}", "-r", f"{FPS}",
    "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", out,
]
subprocess.run(cmd, check=True)
