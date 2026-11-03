#!/usr/bin/env bash
# Rebuild every deliverable of "Shawarma BaKfar" from the delivered sources.
#
#   SOURCES=dir/with/brief-named/clips FONTS=dir/with/Heebo-Black.ttf \
#   LOGO=path/to/logo.(png|webp) OUT=exports bash build.sh
#
# SOURCES must contain (names from the brief):
#   01_tractor_best_take.mp4  02_soccer_field_take.mp4
#   03_coffee_pouring_source.mp4  05_shawarma_food_original.mp4
# FONTS: Heebo-Black.ttf (Google Fonts, SIL OFL - free for commercial use).
# LOGO: any of the three crossed-knives logos; a white-background badge is
#       cut to a circle automatically. Swap logos by changing LOGO only.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${SOURCES:?set SOURCES}" "${FONTS:?set FONTS}" "${LOGO:?set LOGO}"
OUT="${OUT:-$HERE/../exports}"
TAG="${TAG:-}"   # optional suffix, e.g. _logo07
WORK="$(mktemp -d)"
mkdir -p "$OUT"
cd "$HERE"

python3 prep_logo.py "$LOGO" "$WORK/logo.png"

for V in main short; do
  python3 render_audio.py --version "$V" --sources "$SOURCES" --outdir "$WORK"
  python3 render_video.py --version "$V" --sources "$SOURCES" --logo "$WORK/logo.png" \
          --fonts "$FONTS" --out "$WORK/${V}_video.mp4"
done
python3 render_video.py --version main --no-text --sources "$SOURCES" --logo "$WORK/logo.png" \
        --fonts "$FONTS" --out "$WORK/main_video_textless.mp4"

mux () { # video audio out
  ffmpeg -v error -y -i "$1" -i "$2" -map 0:v:0 -map 1:a:0 -c:v copy \
         -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest -movflags +faststart "$3"
}
mux "$WORK/main_video.mp4"          "$WORK/main_mix.wav"      "$OUT/shawarma_bakfar_main_11.5s_1080x1920${TAG}.mp4"
mux "$WORK/main_video.mp4"          "$WORK/main_sfx_only.wav" "$OUT/shawarma_bakfar_main_SFX-only_no-music${TAG}.mp4"
mux "$WORK/main_video_textless.mp4" "$WORK/main_mix.wav"      "$OUT/shawarma_bakfar_main_textless${TAG}.mp4"
mux "$WORK/short_video.mp4"         "$WORK/short_mix.wav"     "$OUT/shawarma_bakfar_short_6.5s_1080x1920${TAG}.mp4"
mux "$WORK/short_video.mp4"         "$WORK/short_sfx_only.wav" "$OUT/shawarma_bakfar_short_SFX-only_no-music${TAG}.mp4"

mkdir -p "$OUT/stems" "$OUT/subtitles"
for V in main short; do
  cp "$WORK/${V}_music_stem.wav" "$WORK/${V}_sfx_stem.wav" "$OUT/stems/"
  python3 make_srt.py --version "$V" --out "$OUT/subtitles/shawarma_bakfar_${V}.he.srt"
done
rm -r "$WORK"
echo "done -> $OUT"
