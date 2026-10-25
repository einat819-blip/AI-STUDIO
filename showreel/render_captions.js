// Renders the Hebrew caption overlays as transparent 1080x1920 PNGs.
// Usage: node render_captions.js <fonts_dir> <out_dir>
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const [fontsDir, outDir] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });

// Fonts are inlined as data URLs: Chromium won't load file:// fonts into a setContent() page.
const fontUrl = (f) => 'data:font/ttf;base64,' + fs.readFileSync(path.resolve(fontsDir, f)).toString('base64');

const css = `
@font-face { font-family: Heebo; src: url('${fontUrl('Heebo[wght].ttf')}'); font-weight: 100 900; }
@font-face { font-family: Secular; src: url('${fontUrl('SecularOne-Regular.ttf')}'); }
html, body { margin: 0; width: 1080px; height: 1920px; background: transparent; }
body { position: relative; direction: rtl; font-family: Heebo, 'Noto Color Emoji', sans-serif; color: #fff; }
.emoji { font-family: 'Noto Color Emoji'; }
.ltr { direction: ltr; unicode-bidi: isolate; display: inline-block; }

/* top brand tag, shown through the clips */
.tag { position: absolute; top: 120px; left: 0; right: 0; text-align: center;
  font: 700 34px Heebo; letter-spacing: 1px; color: rgba(255,255,255,.92);
  text-shadow: 0 2px 10px rgba(0,0,0,.55); }

/* hook / statement lines: big white with dark outline */
.hook { position: absolute; top: 300px; left: 60px; right: 60px; text-align: center;
  font: 900 92px/1.12 Heebo; text-shadow: 0 0 2px #000, 0 4px 0 rgba(0,0,0,.35), 0 8px 30px rgba(0,0,0,.6);
  -webkit-text-stroke: 3px rgba(0,0,0,.55); paint-order: stroke fill; }

/* category labels: pink pill */
.pill-wrap { position: absolute; top: 300px; left: 0; right: 0; text-align: center; }
.pill { display: inline-block; padding: 18px 46px 24px; border-radius: 999px;
  background: linear-gradient(135deg, #ff2e83, #ff6fb1); box-shadow: 0 10px 30px rgba(0,0,0,.35);
  font: 900 76px/1.1 Heebo; transform: rotate(-2deg); }

/* end card */
.end { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 26px; text-align: center; }
.end .kicker { font: 700 56px Heebo; text-shadow: 0 4px 18px rgba(0,0,0,.6); }
.end .brand { font: 900 132px/1 Heebo; direction: ltr; margin: 26px 0 6px;
  background: linear-gradient(180deg, #fff3c4 0%, #ffd36b 45%, #ff6fb1 100%); -webkit-background-clip: text; color: transparent;
  filter: drop-shadow(0 6px 22px rgba(0,0,0,.55)); }
.end .slogan { font: 800 70px Heebo; text-shadow: 0 4px 18px rgba(0,0,0,.6); }
.end .phone { margin-top: 30px; padding: 20px 52px 24px; border-radius: 999px; background: linear-gradient(135deg, #ff2e83, #ff6fb1);
  font: 900 74px Heebo; box-shadow: 0 10px 30px rgba(0,0,0,.4); }
.end .follow { margin-top: 18px; font: 700 46px Heebo; opacity: .95; text-shadow: 0 4px 18px rgba(0,0,0,.6); }
`;

const e = (s) => `<span class="emoji">${s}</span>`;

const captions = {
  tag: `<div class="tag"><span class="ltr">AI nati studios</span></div>`,
  hook: `<div class="hook">״אני לא פוטוגני״ ${e('🙄')}</div>`,
  movie: `<div class="hook">אז אני עושה<br>מזה סרט! ${e('🎬')}</div>`,
  birthday: `<div class="pill-wrap"><div class="pill">יום הולדת ${e('🎂')}</div></div>`,
  wedding: `<div class="pill-wrap"><div class="pill">חתונה · <span class="ltr">Save the Date</span> ${e('💍')}</div></div>`,
  business: `<div class="pill-wrap"><div class="pill">פרסומת לעסק שלכם ${e('📢')}</div></div>`,
  photos: `<div class="pill-wrap"><div class="pill">תמונות שמתעוררות לחיים ${e('📸')}</div></div>`,
  end: `<div class="end">
      <div class="kicker">הסרט הבא יכול להיות שלכם ${e('🎬')}</div>
      <div class="brand">AI nati studios</div>
      <div class="slogan">הוליווד במחיר שפוי ${e('💗')}</div>
      <div class="phone"><span class="ltr">054-599-6938</span></div>
      <div class="follow">חפשו אותנו בפייסבוק ותנו עוקב ${e('👍')}</div>
    </div>`,
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const [name, body] of Object.entries(captions)) {
    await page.setContent(`<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outDir, `${name}.png`), omitBackground: true });
  }
  await browser.close();
})();
