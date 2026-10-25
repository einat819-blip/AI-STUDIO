# AI nati studios – showreel 20s

`ai-nati-studios-showreel-20s.mp4` – 1080x1920 (9:16), 30fps, 20s, H.264 + AAC, ‎-14 LUFS. Built for Facebook Reels and feed posts.

| Time | Clip (Higgsfield generation) | Caption |
|---|---|---|
| 0.0–2.35 | `d4c54c44`: awkward in front of the ring light | ״אני לא פוטוגני״ 🙄 |
| 2.35–4.3 | `0c915f0f`: the technician's hero walk | אז אני עושה מזה סרט! 🎬 |
| 4.3–6.25 | `310bfa44`: birthday glow-up | יום הולדת 🎂 |
| 6.25–8.2 | `c3ed9f72`: wedding at golden hour | חתונה · Save the Date 💍 |
| 8.2–13.08 | `efa9432c`, `1685b331`, `ae5eddbb`: AC technician ad | פרסומת לעסק שלכם 📢 |
| 13.08–16.0 | `4c91d2bb`: poster turns into a sunset bike ride | תמונות שמתעוררות לחיים 📸 |
| 16.0–20.0 | End card | AI nati studios · הוליווד במחיר שפוי 💗 · 054-599-6938 |

Music: instrumental generated in Runway (Eleven Music, 30s bed trimmed to 20s). Cuts land on its downbeats (~123 BPM).

## Rebuild

Requires ffmpeg, Node with Playwright, the source clips (`<id>.mp4`), the Heebo font (`Heebo[wght].ttf`) and the music file.

```sh
node render_captions.js <fonts_dir> <captions_dir>
python3 build_showreel.py <clips_dir> <captions_dir> <music.mp3> ai-nati-studios-showreel-20s.mp4
```
