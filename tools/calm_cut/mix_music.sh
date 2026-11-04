#!/usr/bin/env bash
# Lay the Suno track (Kitchen Klezmer) under the v3 picture, music only.
#   mix_music.sh <suno.mp3> <picture.mp4> <work_dir> <output.mp4>
# Uses the track from 23.28 s to its end: a kick lands on the first frame, the
# bass drops out under the tagline, the band returns with the end card dissolve
# and the final chord rings out to the last frame. No edits inside the music.
set -euo pipefail
MUS=$1; PIC=$2; W=$3; OUT=$4
mkdir -p "$W"
LEN=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PIC")
FADE_AT=$(python3 -c "print(round($LEN-0.6,3))")
ffmpeg -v error -y -i "$MUS" -af "aresample=48000,atrim=start=23.28:end=42.43,asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st=$FADE_AT:d=0.6,atrim=end=$LEN" \
  -c:a pcm_s16le "$W/music_raw.wav"
GAIN=$(ffmpeg -nostats -v info -i "$W/music_raw.wav" -af loudnorm=I=-14:TP=-1.5:print_format=json -f null - 2>&1 \
  | python3 -c "import sys,json,re; d=json.loads(re.search(r'\{.*\}', sys.stdin.read(), re.S).group()); print(round(-14-float(d['input_i']),2))")
ffmpeg -v error -y -i "$W/music_raw.wav" -af "volume=${GAIN}dB" -c:a pcm_s16le "$W/music.wav"
ffmpeg -v error -y -i "$PIC" -i "$W/music.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
