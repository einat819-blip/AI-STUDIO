"""Assemble part 1 (scenes 1-5) of the court comedy.

Timeline at 25 fps. Scenes 2 and 3 are labelled stills with the real dub,
because no animated video exists for them yet.
"""
import json, subprocess, sys

SP = "/tmp/claude-0/-home-user-AI-STUDIO/81365eae-bc91-54f8-8929-0a71d709335c/scratchpad"
U = "/root/.claude/uploads/81365eae-bc91-54f8-8929-0a71d709335c"
B = f"{SP}/edit/build"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT_MIX = f"{B}/mix_raw.wav"
OUT = sys.argv[1]

# scene lengths, all multiples of 1/25 s
L1, L2, L3, L4, L5 = 8.00, 5.72, 8.76, 5.00, 10.76
T2 = L1
T3 = T2 + L2
T4 = T3 + L3
T5 = T4 + L4
TOTAL = T5 + L5

inputs = [
    ["-i", f"{SP}/edit/src/A_c458.mp4"],                                   # 0 judge, scene 1
    ["-loop", "1", "-framerate", "25", "-t", f"{L2}", "-i", f"{B}/still_s2.webp"],  # 1 Einat still
    ["-loop", "1", "-framerate", "25", "-t", f"{L3}", "-i", f"{B}/still_s3.png"],   # 2 judge still
    ["-i", f"{SP}/hedra_lib/h0924_unnamed.mp4"],                          # 3 Einat, scene 4
    ["-i", "/home/user/AI-STUDIO/shots/prosecutor-evidence-1/prosecutor_evidence1_shot.mp4"],  # 4 prosecutor
    ["-i", f"{U}/93560c92-_____1.ogg"],                                    # 5 scene 2 dub
    ["-i", f"{SP}/hedra_lib/aud_0931.mp3"],                                # 6 scene 3 dub
    ["-i", f"{U}/68e7f97f-___________1.mp3"],                              # 7 scene 5 dub (original quality)
    ["-i", f"{SP}/edit/audio/music.mp3"],                                  # 8 music
    ["-stream_loop", "2", "-i", f"{SP}/edit/audio/roomtone.mp3"],          # 9 room tone
]

def ms(t):
    return int(round(t * 1000))

V = "scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p"
label = (f"drawtext=fontfile={FONT}:textfile={{f}}:fontsize=34:fontcolor=white:"
         "box=1:boxcolor=black@0.55:boxborderw=14:x=w-tw-40:y=40")

DIA = "aformat=sample_rates=48000:channel_layouts=mono"
fg = [
    # ---- picture
    f"[0:v]trim=0:{L1},setpts=PTS-STARTPTS,fps=25,{V}[v1]",
    f"[1:v]fps=25,{V},{label.format(f=B + '/label_s2.txt')},trim=end_frame={round(L2*25)}[v2]",
    f"[2:v]fps=25,{V},{label.format(f=B + '/label_s3.txt')},trim=end_frame={round(L3*25)}[v3]",
    f"[3:v]trim=0:{L4},setpts=PTS-STARTPTS,fps=25,{V}[v4]",
    f"[4:v]fps=25,tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame={round(L5*25)},setpts=PTS-STARTPTS,"
    f"scale=1920:1080:flags=lanczos,unsharp=5:5:0.35,setsar=1,format=yuv420p[v5]",
    "[v1][v2][v3][v4][v5]concat=n=5:v=1:a=0[vout]",
    # ---- dialogue, each levelled to about -18 LUFS
    f"[0:a]atrim=0:{L1},asetpts=PTS-STARTPTS,{DIA},volume=-1.0dB,afade=t=out:st={L1-0.008}:d=0.008[d1]",
    f"[5:a]atrim=1.11:5.935,asetpts=PTS-STARTPTS,{DIA},highpass=f=80,volume=-1.6dB,"
    f"afade=t=in:d=0.01,afade=t=out:st=4.81:d=0.015,adelay={ms(T2)}[d2]",
    f"[6:a]atrim=0:8.45,asetpts=PTS-STARTPTS,{DIA},volume=0.8dB,afade=t=out:st=8.41:d=0.04,"
    f"adelay={ms(T3 + 0.30)}[d3]",
    f"[3:a]atrim=0:{L4},asetpts=PTS-STARTPTS,{DIA},volume=1.6dB,afade=t=out:st={L4-0.015}:d=0.015,"
    f"adelay={ms(T4)}[d4]",
    f"[7:a]atrim=0:10.446,asetpts=PTS-STARTPTS,{DIA},volume=3.3dB,afade=t=out:st=10.438:d=0.008,"
    f"adelay={ms(T5)}[d5]",
    # ---- music: under the indictment, hard stop on Einat's first word; back, lower, under the prosecutor
    f"[8:a]asplit=2[m1s][m2s]",
    f"[m1s]atrim=0:7.95,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,volume=-5dB,"
    f"afade=t=in:d=1.2,afade=t=out:st=7.91:d=0.04,adelay={ms(0.35)}|{ms(0.35)}[m1]",
    f"[m2s]atrim=20:{20+L5},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,volume=-6.5dB,"
    f"afade=t=in:d=1.0,afade=t=out:st={L5-0.06}:d=0.06,adelay={ms(T5)}|{ms(T5)}[m2]",
    # ---- room tone bed across the whole part, glues the stills and the pauses
    f"[9:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,volume=15dB,"
    f"afade=t=in:d=0.3,afade=t=out:st={TOTAL-0.05}:d=0.05[rt]",
    # ---- mix
    "[d1][d2][d3][d4][d5]amix=inputs=5:normalize=0:duration=longest,"
    "aformat=channel_layouts=stereo[dia]",
    f"[dia][m1][m2][rt]amix=inputs=4:normalize=0:duration=longest,atrim=0:{TOTAL}[aout]",
]

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
for i in inputs:
    cmd += i
cmd += ["-filter_complex", ";".join(fg),
        "-map", "[vout]", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-r", "25",
        "-pix_fmt", "yuv420p", "-an", f"{B}/video_only.mp4",
        "-map", "[aout]", "-c:a", "pcm_s24le", "-ar", "48000", OUT_MIX]
subprocess.run(cmd, check=True)

# ---- master: measure, bring to -16 LUFS, limit true peak to -1.5 dBTP
meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", OUT_MIX, "-af",
                       "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
gain = -16.0 - float(j["input_i"])
print("mix integrated", j["input_i"], "LUFS, true peak", j["input_tp"], "-> gain", round(gain, 2), "dB")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", f"{B}/video_only.mp4", "-i", OUT_MIX,
                "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=disabled",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print(json.dumps({"T2": T2, "T3": T3, "T4": T4, "T5": T5, "TOTAL": TOTAL}))
