// Renders the Hebrew caption stickers as tightly-cropped transparent PNGs
// (positioned and popped in by build_showreel.py), plus the end-card shade.
// Usage: node render_captions.js <fonts_dir> <out_dir>
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const [fontsDir, outDir] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });

// Fonts are inlined as data URLs: Chromium won't load file:// fonts into a setContent() page.
const fontUrl = (f) => 'data:font/ttf;base64,' + fs.readFileSync(path.resolve(fontsDir, f)).toString('base64');

const css = `
@font-face { font-family: Rubik; src: url('${fontUrl('Rubik[wght].ttf')}'); font-weight: 300 900; }
html, body { margin: 0; background: transparent; }
body { direction: rtl; font-family: Rubik, 'Noto Color Emoji', sans-serif; }
.emoji { font-family: 'Noto Color Emoji'; }
.ltr { direction: ltr; unicode-bidi: isolate; display: inline-block; }
#cap { display: inline-block; padding: 40px; }
.st { display: inline-block; white-space: nowrap; padding: 10px 40px 18px; border-radius: 26px;
  border: 7px solid #141414; box-shadow: 12px 12px 0 #141414; font-weight: 900; line-height: 1.15; }
.plain { display: inline-block; white-space: nowrap; font-weight: 800; color: #fff;
  text-shadow: 0 3px 0 #141414, 0 0 18px rgba(0,0,0,.7); }
#shade { width: 1080px; height: 1920px;
  background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 50%, rgba(10,0,20,.55) 62%, rgba(10,0,20,.88) 100%); }
`;

const COLORS = {
  yellow: ['#FFE600', '#141414'],
  pink: ['#FF2E93', '#ffffff'],
  cyan: ['#00E1FF', '#141414'],
  purple: ['#8A4DFF', '#ffffff'],
  lime: ['#B6FF00', '#141414'],
  white: ['#ffffff', '#141414'],
};

const e = (s) => `<span class="emoji">${s}</span>`;
const sticker = (html, color, size, rot) => {
  const [bg, fg] = COLORS[color];
  return { html: `<div class="st" style="background:${bg};color:${fg};font-size:${size}px;transform:rotate(${rot}deg)">${html}</div>`, size };
};

const captions = {
  hook1: sticker('יש אנשים שעושים סרטון', 'yellow', 76, -3),
  hook2: sticker('מהחיים שלהם...', 'white', 76, 2),
  movie1: sticker('ואני עושה מהחיים שלהם', 'cyan', 68, 2),
  movie2: sticker(`סרט! ${e('🎬')}`, 'pink', 140, -4),
  birthday: sticker(`יום הולדת ${e('🎂')}`, 'yellow', 92, -3),
  wedding: sticker(`חתונה · <span class="ltr">Save the Date</span> ${e('💍')}`, 'pink', 80, 2),
  business: sticker(`פרסומת לעסק שלכם ${e('📢')}`, 'cyan', 82, -2),
  photos: sticker(`תמונות שהיו רק בדמיון ${e('📸')}`, 'purple', 78, 2),
  alive: sticker(`ועכשיו הן זזות! ${e('✨')}`, 'lime', 88, -3),
  end_kicker: sticker(`הסרט הבא יכול להיות שלכם ${e('🎬')}`, 'white', 54, -2),
  end_slogan: sticker(`הוליווד במחיר שפוי ${e('💗')}`, 'pink', 84, 2),
  end_phone: sticker(`${e('📲')} <span class="ltr">054-599-6938</span>`, 'yellow', 84, -2),
  end_follow: sticker(`תנו עוקב בפייסבוק ${e('👍')}`, 'cyan', 50, 2),
  tag: { html: `<div class="plain" style="font-size:34px"><span class="ltr">AI nati studios</span></div>`, size: 34 },
};

const MAX_W = 1040; // keep every sticker (with its padding) inside the 1080 frame

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const load = (body) => page.setContent(`<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`);

  for (const [name, { html, size }] of Object.entries(captions)) {
    await load(`<div id="cap">${html}</div>`);
    await page.evaluate(() => document.fonts.ready);
    // Shrink the font until the sticker fits the frame width.
    await page.evaluate(([maxW, start]) => {
      const cap = document.getElementById('cap');
      const inner = cap.firstElementChild;
      let s = start;
      while (cap.getBoundingClientRect().width > maxW && s > 20) { s -= 2; inner.style.fontSize = s + 'px'; }
    }, [MAX_W, size]);
    await page.locator('#cap').screenshot({ path: path.join(outDir, `${name}.png`), omitBackground: true });
  }

  await page.setViewportSize({ width: 1080, height: 1920 });
  await load('<div id="shade"></div>');
  await page.locator('#shade').screenshot({ path: path.join(outDir, 'end_shade.png'), omitBackground: true });
  await browser.close();
})();
