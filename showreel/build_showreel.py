#!/usr/bin/env python3
"""Builds the 20s vertical (1080x1920) AI nati studios showreel.

Usage: build_showreel.py <media_dir> <captions_dir> <music.mp3> <out.mp4>

<media_dir> holds the studio's clips and stills under the names used in SHOTS
(Higgsfield generations are named by the first 8 chars of the generation id).
Cuts land on the music's beats (~123 BPM, downbeat every ~1.95s).
"""
import subprocess
import sys

media, caps, music, out = sys.argv[1:5]

W, H, FPS = 1080, 1920, 30
END = 20.0
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
NINE_SIXTEEN = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'"

# kind, file, (source in, source out) or (start zoom, zoom per frame), timeline start, timeline end, mode, pre-filter
SHOTS = [
    ("video", "dragon.mp4", (10.50, 14.60), 0.000, 2.351, "fill", ""),             # hook: push-in to the glowing eye
    ("video", "0c915f0f.mp4", (0.50, 2.45), 2.351, 4.301, "fill", ""),             # hero walk
    ("video", "310bfa44.mp4", (0.70, 5.30), 4.301, 6.252, "fill", ""),             # birthday glow-up
    ("video", "c3ed9f72.mp4", (1.40, 2.60), 6.252, 7.227, "fill", ""),             # wedding, golden hour
    ("video", "parents_wedding.mp4", (4.20, 5.60), 7.227, 8.202, "fill", "crop=607:1080:654:0,"),
    ("video", "cake.mp4", (1.00, 5.90), 8.202, 10.153, "fit", ""),                 # bakery ad: same cake, new story
    ("video", "efa9432c.mp4", (2.60, 4.60), 10.153, 11.128, "fill", ""),           # AC ad: sunglasses down
    ("video", "ae5eddbb.mp4", (1.20, 3.60), 11.128, 12.103, "fill", ""),           # AC ad: the cheer
    ("image", "cloud.jpg", (1.0, 0.004), 12.103, 12.591, "fill", NINE_SIXTEEN + ","),
    ("image", "warrior.jpg", (1.0, 0.004), 12.591, 13.079, "fill", NINE_SIXTEEN + ","),
    ("image", "sunglasses.jpg", (1.0, 0.004), 13.079, 13.566, "fill", NINE_SIXTEEN + ","),
    ("image", "earth.jpg", (1.0, 0.004), 13.566, 14.054, "fill", NINE_SIXTEEN + ","),
    ("video", "4c91d2bb.mp4", (5.50, 10.00), 14.054, 16.004, "fill", "crop=779:1385:254:95,"),  # poster comes alive
    ("image", "studio_couple.jpg", (1.06, -0.0005), 16.004, END, "fill", "crop=631:1122:410:0,"),  # end: pull back to the full sign
]

# png, start, end, vertical centre (None = full-frame overlay), pop-in animation
CAPTIONS = [
    ("hook1", 0.12, 2.351, 330, True),
    ("hook2", 0.60, 2.351, 500, True),
    ("movie1", 2.40, 4.301, 330, True),
    ("movie2", 2.70, 4.301, 520, True),
    ("birthday", 4.35, 6.252, 340, True),
    ("wedding", 6.30, 8.202, 340, True),
    ("business", 8.25, 12.103, 330, True),
    ("photos", 12.15, 14.054, 340, True),
    ("alive", 14.10, 16.004, 340, True),
    ("tag", 2.351, 16.004, 150, False),
    ("end_shade", 16.004, END, None, False),
    ("end_kicker", 16.25, END, 1100, True),
    ("end_slogan", 16.55, END, 1245, True),
    ("end_phone", 16.85, END, 1395, True),
    ("end_follow", 17.15, END, 1530, True),
]
FLASHES = [2.351, 16.004]

inputs, filters, segs = [], [], []


def add_input(*args):
    inputs.extend(args)
    return len([a for a in inputs if a == "-i"]) - 1


for kind, name, src, t0, t1, mode, pre in SHOTS:
    dur = t1 - t0
    label = f"s{len(segs)}"
    if kind == "video":
        idx = add_input("-i", f"{media}/{name}")
        a, b = src
        head = f"[{idx}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{(b - a) / dur:.4f},{pre}fps={FPS}"
        if mode == "fit":  # letterbox over a blurred, saturated copy of itself
            filters.append(
                f"{head},split[{label}a][{label}b];"
                f"[{label}a]{FILL},gblur=sigma=30,eq=brightness=-0.15:saturation=1.3[{label}bg];"
                f"[{label}b]scale={W}:-2[{label}fg];"
                f"[{label}bg][{label}fg]overlay=(W-w)/2:(H-h)/2,trim=duration={dur:.3f},setsar=1,format=yuv420p[{label}]"
            )
        else:
            filters.append(f"{head},{FILL},trim=duration={dur:.3f},setsar=1,format=yuv420p[{label}]")
    else:  # still image with a slow push-in
        idx = add_input("-loop", "1", "-framerate", f"{FPS}", "-t", f"{dur:.3f}", "-i", f"{media}/{name}")
        filters.append(
            f"[{idx}:v]{pre}scale={2 * W}:{2 * H},"
            f"zoompan=z='{src[0]}+{src[1]}*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
            f"trim=duration={dur:.3f},setsar=1,format=yuv420p[{label}]"
        )
    segs.append(f"[{label}]")

filters.append(f"{''.join(segs)}concat=n={len(segs)}:v=1:a=0[v0]")
prev = "v0"

for i, t in enumerate(FLASHES):
    idx = add_input("-f", "lavfi", "-i", f"color=white:s={W}x{H}:r={FPS}:d=0.24")
    filters.append(
        f"[{idx}:v]format=rgba,colorchannelmixer=aa=0.85,fade=in:st=0:d=0.12:alpha=1,"
        f"fade=out:st=0.12:d=0.12:alpha=1,setpts=PTS+{t - 0.12:.3f}/TB[fl{i}]"
    )
    filters.append(f"[{prev}][fl{i}]overlay=0:0:eof_action=pass[vf{i}]")
    prev = f"vf{i}"

for j, (name, t0, t1, yc, pop) in enumerate(CAPTIONS):
    idx = add_input("-loop", "1", "-framerate", f"{FPS}", "-t", f"{END}", "-i", f"{caps}/{name}.png")
    chain = f"[{idx}:v]format=rgba"
    if pop:  # overshoot to 115% then settle at 100%
        s = (f"if(lt(t,{t0}),0.05,if(lt(t,{t0 + 0.10:.3f}),0.4+7.5*(t-{t0}),"
             f"if(lt(t,{t0 + 0.18:.3f}),1.15-1.875*(t-{t0 + 0.10:.3f}),1)))")
        chain += f",scale=w='max(2,iw*{s})':h='max(2,ih*{s})':eval=frame"
    else:
        chain += f",fade=in:st={t0}:d=0.25:alpha=1"
    if t1 < END:
        chain += f",fade=out:st={t1 - 0.08:.3f}:d=0.08:alpha=1"
    filters.append(f"{chain}[c{j}]")
    pos = "0:0" if yc is None else f"x='(W-w)/2':y='{yc}-h/2'"
    filters.append(f"[{prev}][c{j}]overlay={pos}:enable='between(t,{t0},{t1})'[v{j + 1}]")
    prev = f"v{j + 1}"

m = add_input("-i", music)
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
