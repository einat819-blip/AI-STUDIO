#!/usr/bin/env bash
# slowseg.sh <src> <out> <start> <end> <speed>   (speed 1 = no change)
set -euo pipefail
src=$1; out=$2; s=$3; e=$4; sp=$5
MI="minterpolate=fps=24:mi_mode=mci:mc_mode=obmc:me_mode=bidir:scd=none"
if [ "$sp" = "1" ]; then vf="trim=start=$s:end=$e,setpts=PTS-STARTPTS"
else vf="trim=start=$s:end=$e,setpts=PTS-STARTPTS,setpts=PTS/$sp,$MI"; fi
ffmpeg -v error -y -i "$src" -an -vf "$vf" -c:v libx264 -crf 8 -preset veryfast -pix_fmt yuv420p "$out"
echo "$out $(ffprobe -v error -select_streams v -show_entries stream=nb_frames,duration -of csv=p=0 "$out")"
