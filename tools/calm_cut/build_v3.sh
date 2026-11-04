#!/usr/bin/env bash
# v3 Facebook 4:5 picture: dad asks before the boy answers, no flash shot, each
# caption held about 1.5 to 1.7 s (2.2 s for the tagline) with interpolated slow motion,
# freeze holds on the dad and the boy, normal speed through fast camera moves and
# pose jumps, soft 4 to 6 frame transitions. Times are for this video only.
#   build_v3.sh <input_9x16.mp4> <work_dir> <output_picture.mp4> [end_card_src_end]
set -euo pipefail
IN=$1; W=$2; OUT=$3; IEND=${4:-14.4375}
HERE=$(cd "$(dirname "$0")" && pwd)
SLOW="$HERE/slowseg.sh"; RF="$HERE/reframe_seg.py"
mkdir -p "$W/seg" "$W/seg45"
S() { "$SLOW" "$IN" "$W/seg/$1.mp4" "$2" "$3" "$4" >/dev/null; }
S A1 0 0.6 1 & S A2 0.6 1.5 0.45 & S B 1.5 2.3333 0.8 & S C 2.3333 3.2917 0.45 & wait
S D1 4.1667 4.4583 0.6 & S D2 4.4583 4.5833 1 & S D3 4.5833 4.95 0.6 & S E0 3.2917 3.875 0.4 & wait
S F1 5.45 5.70 1 & S F2 5.70 6.6667 0.5 & S F3 6.6667 7.4583 1 & S G 7.4583 8.8333 1 & wait
S H1 8.8333 9.1667 1 & S H2 9.1667 10.1 0.4 & S I 10.1 "$IEND" 1 & wait
join() { local name=$1; shift; : > "$W/seg/$name.txt"
  for p in "$@"; do echo "file '$p.mp4'" >> "$W/seg/$name.txt"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$W/seg/$name.txt" -c:v libx264 -crf 8 -preset veryfast -pix_fmt yuv420p "$W/seg/$name.mp4"; }
join A A1 A2; join F F1 F2 F3; join H H1 H2; join D0 D1 D2 D3
hold() { ffmpeg -v error -y -i "$W/seg/$1.mp4" -vf "tpad=stop_mode=clone:stop_duration=$3" \
  -c:v libx264 -crf 8 -preset veryfast -pix_fmt yuv420p "$W/seg/$2.mp4"; }
hold D0 D 1.0 & hold E0 E 0.6 & wait
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
rf() { ffmpeg -v error -i "$W/seg/$1.mp4" -f rawvideo -pix_fmt rgb24 - | python3 -I "$RF" "$2" \
  | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1350 -r 24 -i - -c:v libx264 -crf 10 -preset veryfast -pix_fmt yuv420p "$W/seg45/$1.mp4"; }
A_D=$(dur "$W/seg/A.mp4"); C_D=$(dur "$W/seg/C.mp4"); D_D=$(dur "$W/seg/D.mp4"); E_D=$(dur "$W/seg/E.mp4"); G_D=$(dur "$W/seg/G.mp4")
D_T0=$(python3 -c "print(round($D_D-1.0,3))"); G_T0=$(python3 -c "print(round($G_D-0.5,3))")
rf A "75,1480>75,1436@0-$A_D:lin" & rf B "120,1350" & rf C "75,1480>75,1436@0-$C_D:lin" & rf D "120,1350>110,1300@$D_T0-$D_D" & wait
rf E "80,1350>80,1310@0-$E_D:lin" & rf F "120,1350" & rf G "250,1350>80,1620@$G_T0-$G_D:in" & rf H "80,1620" & wait
rf I "80,1620>292,1350@0.0-0.6"
printf "file 'G.mp4'\nfile 'H.mp4'\nfile 'I.mp4'\n" > "$W/seg45/ghi.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$W/seg45/ghi.txt" -c copy "$W/seg45/GHI.mp4"
order=(A B C D E F GHI); xd=(0.25 0.1667 0.1667 0.1667 0.1667 0.25)
inputs=(); for n in "${order[@]}"; do inputs+=(-i "$W/seg45/$n.mp4"); done
fc=""; off=0; prev="[0:v]"; starts="A:0"
for i in $(seq 0 5); do
  d=$(dur "$W/seg45/${order[$i]}.mp4")
  off=$(python3 -c "print(round($off+$d-${xd[$i]},4))")
  starts="$starts ${order[$((i+1))]}:$off"
  out="[v$i]"; [ "$i" -eq 5 ] && out="[vout]"
  fc="$fc$prev[$((i+1)):v]xfade=transition=fade:duration=${xd[$i]}:offset=$off$out;"
  prev="[v$i]"
done
echo "segment starts: $starts"
echo "G/H/I: G=$(dur "$W/seg45/G.mp4") H=$(dur "$W/seg45/H.mp4") I=$(dur "$W/seg45/I.mp4")"
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${fc%;}" -map "[vout]" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 24 -movflags +faststart "$OUT"
echo "total: $(dur "$OUT")"
