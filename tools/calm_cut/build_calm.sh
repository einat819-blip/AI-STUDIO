#!/usr/bin/env bash
# Calmer 4:5 Facebook cut of the Yonatan invite (v2), picture only.
#   build_calm.sh <input_9x16.mp4> <work_dir> <output.mp4>
# Reorders the dialogue (dad asks, then the boy answers), drops the 0.3 s flash
# shot, slows the caption shots with frame interpolation, reframes each shot to
# 4:5 and joins them with short soft cuts. Times below are for this video only.
set -euo pipefail
IN=$1; W=$2; OUT=$3
HERE=$(cd "$(dirname "$0")" && pwd)
SLOW="$HERE/slowseg.sh"; RF="$HERE/reframe_seg.py"
mkdir -p "$W/seg" "$W/seg45"

# 1. segments: name start end speed  (speed 1 = untouched)
"$SLOW" "$IN" "$W/seg/A.mp4" 0 1.5 1 &               # "אבאאא!"
"$SLOW" "$IN" "$W/seg/B.mp4" 1.5 2.3333 0.8 &        # dad walks in
"$SLOW" "$IN" "$W/seg/C.mp4" 2.3333 3.2917 0.65 &    # "8:00 בבוקר!"
"$SLOW" "$IN" "$W/seg/D1.mp4" 4.1667 4.4583 0.72 &   # dad "בבוקר?!" (fast camera move
wait
"$SLOW" "$IN" "$W/seg/D2.mp4" 4.4583 4.5833 1 &      #   at 4.5 s stays at normal speed
"$SLOW" "$IN" "$W/seg/D3.mp4" 4.5833 5.2 0.72 &      #   so it does not smear)
"$SLOW" "$IN" "$W/seg/E0.mp4" 3.2917 3.875 0.4 &     # "כן, בבוקר!" now after dad asks
"$SLOW" "$IN" "$W/seg/F.mp4" 5.45 7.4583 1 &         # "אל תאחר!" + high five
wait
"$SLOW" "$IN" "$W/seg/G.mp4" 7.4583 8.8333 1 &       # boy fixes tallit
"$SLOW" "$IN" "$W/seg/H1.mp4" 8.8333 9.1667 1 &      # source zoom out (normal speed)
"$SLOW" "$IN" "$W/seg/H2.mp4" 9.1667 10.1 0.5 &      # "יש הזמנות..." hold
"$SLOW" "$IN" "$W/seg/I.mp4" 10.1 14.6 1 &           # dissolve + end card
wait
ffmpeg -v error -y -i "$W/seg/E0.mp4" -vf "tpad=stop_mode=clone:stop_duration=0.2" \
  -c:v libx264 -crf 8 -preset veryfast -pix_fmt yuv420p "$W/seg/E.mp4"
for g in D H; do
  ls "$W/seg/${g}"[0-9].mp4 | sed "s/.*\///;s/^/file '/;s/$/'/" > "$W/seg/$g.txt"
  ffmpeg -v error -y -f concat -safe 0 -i "$W/seg/$g.txt" -c:v libx264 -crf 8 -preset veryfast -pix_fmt yuv420p "$W/seg/$g.mp4"
done

# 2. reframe each segment to 4:5 (window: top y0, height H; see reframe_seg.py)
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
rf() {
  ffmpeg -v error -i "$W/seg/$1.mp4" -f rawvideo -pix_fmt rgb24 - \
   | python3 -I "$RF" "$2" \
   | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1350 -r 24 -i - \
       -c:v libx264 -crf 10 -preset veryfast -pix_fmt yuv420p "$W/seg45/$1.mp4"
}
A_D=$(dur "$W/seg/A.mp4"); C_D=$(dur "$W/seg/C.mp4"); E_D=$(dur "$W/seg/E.mp4"); G_D=$(dur "$W/seg/G.mp4")
G_T0=$(python3 -c "print(round($G_D-0.5,3))")
rf A "75,1480>75,1436@0-$A_D:lin" & rf B "120,1350" & rf C "75,1480>75,1436@0-$C_D:lin" & rf D "120,1350" & wait
rf E "80,1350>80,1310@0-$E_D:lin" & rf F "120,1350" & rf G "250,1350>80,1620@$G_T0-$G_D:in" & rf H "80,1620" & wait
rf I "80,1620>292,1350@0.0-0.6"
printf "file 'G.mp4'\nfile 'H.mp4'\nfile 'I.mp4'\n" > "$W/seg45/ghi.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$W/seg45/ghi.txt" -c copy "$W/seg45/GHI.mp4"

# 3. join with soft cuts (seconds of overlap into the next shot)
order=(A B C D E F GHI); xd=(0.25 0.1667 0.1667 0.1667 0.1667 0.25)
inputs=(); for n in "${order[@]}"; do inputs+=(-i "$W/seg45/$n.mp4"); done
fc=""; off=0; prev="[0:v]"
for i in $(seq 0 5); do
  d=$(dur "$W/seg45/${order[$i]}.mp4")
  off=$(python3 -c "print(round($off+$d-${xd[$i]},4))")
  out="[v$i]"; [ "$i" -eq 5 ] && out="[vout]"
  fc="$fc$prev[$((i+1)):v]xfade=transition=fade:duration=${xd[$i]}:offset=$off$out;"
  prev="[v$i]"
done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${fc%;}" -map "[vout]" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 24 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
