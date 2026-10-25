# AI nati studios – showreel 20s

`ai-nati-studios-showreel-20s.mp4` – 1080x1920 (9:16), 30fps, 20s, H.264 + AAC, ‎-14 LUFS. Built for Facebook Reels and feed posts.

| Time | Media | Caption sticker |
|---|---|---|
| 0.0–2.35 | `dragon.mp4`: push-in to the glowing eye | יש אנשים שעושים סרט / מהחיים שלהם... |
| 2.35–4.3 | `rose.mp4`: black & white bursts into red roses | ואני עושה מהחיים שלהם / סרט! 🎬 |
| 4.3–6.25 | `310bfa44`: birthday glow-up | יום הולדת 🎂 |
| 6.25–8.2 | `c3ed9f72` + `parents_wedding.mp4` | חתונה · Save the Date 💍 |
| 8.2–12.1 | `cake.mp4` (bakery ad), `efa9432c`, `ae5eddbb` (AC ad) | פרסומת לעסק שלכם 📢 |
| 12.1–14.05 | Stills: `cloud`, `warrior`, `sunflower_frame` (from `3be36905`), `earth` | תמונות שהיו רק בדמיון 📸 |
| 14.05–16.0 | `4c91d2bb`: poster turns into a sunset bike ride | ועכשיו הן זזות! ✨ |
| 16.0–20.0 | `studio_couple.jpg` under the studio sign | הסרט הבא יכול להיות שלכם · הוליווד במחיר שפוי 💗 · 054-599-6938 |

8-character names are Higgsfield generation ids. Music: instrumental generated in Runway (Eleven Music, 30s bed trimmed to 20s). Cuts land on its beats (~123 BPM).

## Rebuild

Requires ffmpeg, Node with Playwright, the media files in one folder (names as in `SHOTS`), the Rubik font (`Rubik[wght].ttf`) and the music file.

```sh
node render_captions.js <fonts_dir> <captions_dir>
python3 build_showreel.py <media_dir> <captions_dir> <music.mp3> ai-nati-studios-showreel-20s.mp4
```
