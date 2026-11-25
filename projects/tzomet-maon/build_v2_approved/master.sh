#!/usr/bin/env bash
# loudness master: integrated -14 LUFS, true peak <= -1 dBTP
set -e
in=$1; out=$2
I=$(ffmpeg -nostats -i "$in" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | awk '{print $2}')
G=$(python3 -c "print(round(-14-($I)+0.75,2))")
ffmpeg -v error -y -i "$in" -af "volume=${G}dB,alimiter=limit=0.79:attack=2:release=80:level=disabled:asc=1" -c:a pcm_s24le -ar 48000 "$out"
ffmpeg -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):"
