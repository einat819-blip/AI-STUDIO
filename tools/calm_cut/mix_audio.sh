#!/usr/bin/env bash
# Lay the Suno track under the v2 picture, add caption pops, normalize to -14 LUFS.
#   mix_audio.sh <suno.mp3> <picture.mp4> <work_dir> <output.mp4>
# Uses the last 15.375 s of the track (from 27.055 s): its downbeat lands on the
# first frame, the bass break sits under the tagline, the band returns with the
# end card and the final chord rings out to the last frame. Under dad's
# "בבוקר?!" (3.25 to 4.5 s) the music dips and darkens instead of stopping.
set -euo pipefail
MUS=$1; PIC=$2; W=$3; OUT=$4
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W"
python3 -I "$HERE/pops.py" "$W/pops.wav" 15.375
DIP="st(0,min(clip((t-3.25)/0.2,0,1),clip((4.5-t)/0.2,0,1)))"
cat > "$W/mix.fc" <<FC
[0:a]aresample=48000,atrim=start=27.055:end=42.43,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=14.775:d=0.6,asplit=2[d][w];
[w]lowpass=f=900:p=2,volume='$DIP;0.55*ld(0)*ld(0)*(3-2*ld(0))':eval=frame[wf];
[d]volume='$DIP;1-0.8*ld(0)*ld(0)*(3-2*ld(0))':eval=frame[df];
[df][wf]amix=inputs=2:normalize=0[mus];
[mus][1:a]amix=inputs=2:normalize=0,atrim=end=15.375[mix]
FC
ffmpeg -v error -y -i "$MUS" -i "$W/pops.wav" -filter_complex_script "$W/mix.fc" -map "[mix]" -c:a pcm_s16le "$W/mix_raw.wav"
GAIN=$(ffmpeg -nostats -v info -i "$W/mix_raw.wav" -af loudnorm=I=-14:TP=-1.5:print_format=json -f null - 2>&1 \
  | python3 -c "import sys,json,re; d=json.loads(re.search(r'\{.*\}', sys.stdin.read(), re.S).group()); print(round(-14-float(d['input_i']),2))")
ffmpeg -v error -y -i "$W/mix_raw.wav" -af "volume=${GAIN}dB" -c:a pcm_s16le "$W/mix.wav"
ffmpeg -v error -y -i "$PIC" -i "$W/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
