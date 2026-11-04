#!/usr/bin/env bash
# Inspect a video before reviewing it: metadata, timed frames, contact sheets,
# detected cuts (shot map), loudness over time, silences and a waveform image.
#
# Usage: inspect_video.sh <video> [out_dir] [scene_threshold]
#   out_dir          default: video_review
#   scene_threshold  default: 0.3 (lower finds more cuts, higher finds fewer)
#
# Read <out_dir>/summary.txt first, then look at the contact sheets and frames.

set -euo pipefail

in="${1:?usage: inspect_video.sh <video> [out_dir] [scene_threshold]}"
out="${2:-video_review}"
thr="${3:-0.3}"

for bin in ffmpeg ffprobe awk; do
  command -v "$bin" >/dev/null || { echo "missing: $bin" >&2; exit 1; }
done
[ -f "$in" ] || { echo "file not found: $in" >&2; exit 1; }

mkdir -p "$out/frames" "$out/cuts" "$out/sheets"
summary="$out/summary.txt"

# Burned-in timestamps need a working font; fall back to plain frames if not.
stamp="drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6"
if ! ffmpeg -v error -f lavfi -i "color=c=black:s=64x64:d=0.1" -vf "$stamp" -frames:v 1 -f null - 2>/dev/null; then
  stamp="null"
fi

# 1. Metadata
ffprobe -v error \
  -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of default=noprint_wrappers=1 "$in" > "$out/info.txt"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
has_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$in" | head -1)
size=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$in")

{
  echo "file: $in"
  echo "duration_sec: $dur"
  echo "video_size: $size"
  if [ -n "$has_audio" ]; then echo "audio: yes"; else echo "audio: no"; fi
} > "$summary"

# 2. Frames at fixed intervals: 2 per second up to 60s, 1 per second after that
fps=1
awk -v d="$dur" 'BEGIN { exit !(d <= 60) }' && fps=2
ffmpeg -v error -y -i "$in" -vf "fps=$fps,scale=480:-2,$stamp" "$out/frames/f_%04d.jpg"
ls "$out/frames" | grep '^f_.*\.jpg$' | awk -v f="$fps" '{ printf "%s\t%.2f\n", $0, (NR - 1) / f }' > "$out/frames/index.tsv"

# 3. Contact sheets: 1 frame per second, 20 seconds per sheet, read row by row
ffmpeg -v error -y -i "$in" -vf "fps=1,scale=320:-2,$stamp,tile=5x4:padding=4:margin=4" \
  "$out/sheets/sheet_%02d.jpg"

# 4. Cuts and shot map
ffmpeg -v info -y -i "$in" -vf "select='gt(scene,$thr)',showinfo,scale=480:-2" \
  -fps_mode vfr "$out/cuts/c_%03d.jpg" 2> "$out/cuts/ffmpeg.log" || true
grep -o 'pts_time:[0-9.]*' "$out/cuts/ffmpeg.log" | cut -d: -f2 > "$out/cuts/times.txt" || true
awk -v d="$dur" '
  BEGIN { start = 0; n = 0 }
  { n++; printf "shot %d\t%.2f\t%.2f\t%.2fs\n", n, start, $1, $1 - start; start = $1 }
  END { n++; printf "shot %d\t%.2f\t%.2f\t%.2fs\n", n, start, d, d - start }
' "$out/cuts/times.txt" > "$out/shots.tsv"

{
  echo
  echo "shots (start, end, length) from scene threshold $thr:"
  cat "$out/shots.tsv"
} >> "$summary"

# 5. Audio: loudness summary, loudness per second, silences, waveform
if [ -n "$has_audio" ]; then
  ffmpeg -nostats -v info -i "$in" -af "ebur128=peak=true:framelog=info" -f null - 2> "$out/loudness.log" || true
  # M = momentary loudness (last 0.4s), S = short-term (last 3s, empty for the
  # first 3 seconds). Values below about -70 mean silence.
  awk '
    BEGIN { print "second\tM_LUFS\tS_LUFS" }
    / t: / {
      if (!match($0, /t: *[0-9.]+/)) next
      t = substr($0, RSTART, RLENGTH); sub(/t: */, "", t)
      if (!match($0, /M: *-?[0-9.]+/)) next
      m = substr($0, RSTART, RLENGTH); sub(/M: */, "", m)
      if (!match($0, /S: *-?[0-9.]+/)) next
      s = substr($0, RSTART, RLENGTH); sub(/S: */, "", s)
      sec = int(t + 0.5); d = t - sec; if (d < 0) d = -d
      if (t + 0 < 2.95) s = ""
      if (sec > 0 && d < 0.051 && !(sec in seen)) { seen[sec] = 1; printf "%d\t%s\t%s\n", sec, m, s }
    }
  ' "$out/loudness.log" > "$out/loudness_per_second.tsv"
  {
    echo
    echo "loudness summary (integrated I, range LRA, true peak):"
    sed -n '/Summary:/,$p' "$out/loudness.log" | grep -E 'I:|LRA:|Peak:' | sed 's/^ */  /'
    echo
    echo "silences below -40 dB longer than 0.4s:"
    ffmpeg -nostats -v info -i "$in" -af "silencedetect=noise=-40dB:d=0.4" -f null - 2>&1 \
      | grep -oE 'silence_(start|end): *-?[0-9.]+' | sed 's/^/  /' || echo "  none"
  } >> "$summary"
  ffmpeg -v error -y -i "$in" -filter_complex "aformat=channel_layouts=mono,showwavespic=s=1600x240" \
    -frames:v 1 "$out/waveform.png" || true
fi

{
  echo
  echo "outputs:"
  echo "  frames/ ($fps per second, index.tsv maps file to second)"
  echo "  sheets/ (1 frame per second, 20 seconds per sheet)"
  echo "  cuts/ (first frame after each detected cut), shots.tsv"
  [ -n "$has_audio" ] && echo "  loudness_per_second.tsv, waveform.png (left to right = start to end)"
} >> "$summary"

cat "$summary"
