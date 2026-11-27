"""Prepare the work folder (.work) that audio.py and video.py read from.

Steps:
  1. Fonts: Heebo and Rubik from npm (@fontsource), Hebrew + Latin subsets merged into TTF.
  2. Source clips: linked from ../source as .work/src/v1..v5.mp4.
  3. Audio: music from ../audio/music and sound effects from .work/sfx converted to 48 kHz WAV.

Sound effects are Epidemic Sound files licensed through Higgsfield and are not stored in
the repository. Download them again with the Higgsfield tools (download_sound_effect)
using the IDs below, and save them as .work/sfx/<name>.mp3 before running this script.

Requires: ffmpeg, node/npm, pip install fonttools brotli numpy pillow
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get('AINATI_WORK', os.path.join(HERE, '..', '.work'))
ROOT = os.path.join(HERE, '..')

SFX_IDS = {
    'roar': 'epidemic_sound:8a07bf38-a160-48cd-a6ce-d6db5c88fe03',      # Lion, Roar, Close
    'snap': 'epidemic_sound:717760b7-b623-4166-b574-65c382fa8de5',      # Finger, Snap 04
    'typing': 'epidemic_sound:3a722cb7-a75f-4d43-9fc8-ec95a175757e',    # Laptop typing, fast
    'enter': 'epidemic_sound:8acc18a4-c289-4274-8975-91157a02843b',     # Return / Enter key
    'glitch': 'epidemic_sound:9bd7d039-8a09-46a6-b081-acf616647be9',    # UI Glitch Data Processing 02
    'shimmer': 'epidemic_sound:bf4716be-4f43-4a79-8c21-f3325bc3f8cf',   # Magic shimmer, transform 04
    'boom': 'epidemic_sound:cdd4ddcb-5158-4612-9633-0cb737e0c1c5',      # Cinematic hit, bright, airy
    'whoosh': 'epidemic_sound:27384f5f-7e69-4f29-916d-b31071cf0112',    # Tech data transition 02
    'notify1': 'epidemic_sound:a6dae59d-6111-42cb-887d-9bad152480e1',   # UI alert, notification, message
}
MUSIC = {
    'm1_comic': 'm1_comic.mp3',        # ElevenLabs Music v2.5 via Higgsfield, 14 s comic pizzicato bed
    'm2_romance': 'm2_romance.mp3',    # 10 s melodramatic romance sting
    'm5_finaleB': 'm5_finaleB.mp3',    # 15 s riser, impact at 3.93 s, final hit at 11.85 s (fantasy ending, archived)
    'm6_brandA': 'm6_brandA.mp3',      # 13 s confident intro, joyful peak at 7.37 s, final hit at 11.68 s
}


def run(cmd, **kw):
    print('+', ' '.join(cmd)); subprocess.run(cmd, check=True, **kw)


def fonts():
    from fontTools.ttLib import TTFont
    from fontTools.merge import Merger
    pkg = os.path.join(WORK, 'fontpkg')
    os.makedirs(pkg, exist_ok=True)
    if not os.path.exists(os.path.join(pkg, 'node_modules', '@fontsource', 'heebo')):
        run(['npm', 'init', '-y'], cwd=pkg, stdout=subprocess.DEVNULL)
        run(['npm', 'install', '--silent', '@fontsource/heebo', '@fontsource/rubik', 'simple-icons'], cwd=pkg)
    out = os.path.join(WORK, 'fonts'); os.makedirs(out, exist_ok=True)
    base = os.path.join(pkg, 'node_modules', '@fontsource')
    for fam, w in [('heebo', 600), ('heebo', 700), ('rubik', 700), ('rubik', 800)]:
        parts = []
        for sub in ('hebrew', 'latin', 'latin-ext'):
            p = f'{base}/{fam}/files/{fam}-{sub}-{w}-normal.woff2'
            if os.path.exists(p):
                f = TTFont(p); f.flavor = None
                tmp = f'{out}/_{fam}-{sub}-{w}.ttf'; f.save(tmp); parts.append(tmp)
        Merger().merge(parts).save(f'{out}/{fam}-{w}.ttf')
        print('font', fam, w)


ICON_JS = r'''
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 256, height: 256 } });
  for (const n of ['instagram', 'facebook', 'tiktok']) {
    const svg = fs.readFileSync(`${process.argv[2]}/${n}.svg`, 'utf8').replace('<svg ', '<svg fill="#ffffff" width="256" height="256" ');
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await p.screenshot({ path: `${process.argv[3]}/${n}.png`, omitBackground: true, clip: { x: 0, y: 0, width: 256, height: 256 } });
  }
  await b.close();
})();
'''


def icons():
    """White Instagram / Facebook / TikTok glyphs from simple-icons (CC0), rendered with Playwright."""
    out = os.path.join(WORK, 'icons'); os.makedirs(out, exist_ok=True)
    js = os.path.join(out, 'render_icons.js')
    open(js, 'w').write(ICON_JS)
    src = os.path.join(WORK, 'fontpkg', 'node_modules', 'simple-icons', 'icons')
    env = dict(os.environ, NODE_PATH=subprocess.check_output(['npm', 'root', '-g']).decode().strip())
    run(['node', js, src, out], env=env)
    # the studio logo, lifted from clip 5 (replace icons/logo.png with the original file when available)
    run([sys.executable, os.path.join(HERE, 'logo_extract.py'), os.path.abspath(f'{ROOT}/source/v5.mp4'), os.path.join(out, 'logo.png')])


def sources():
    d = os.path.join(WORK, 'src'); os.makedirs(d, exist_ok=True)
    for i in range(1, 8):
        dst = f'{d}/v{i}.mp4'
        if not os.path.exists(dst):
            os.symlink(os.path.abspath(f'{ROOT}/source/v{i}.mp4'), dst)


def audio():
    d = os.path.join(WORK, 'wav'); os.makedirs(d, exist_ok=True)
    for name, f in MUSIC.items():
        run(['ffmpeg', '-v', 'error', '-y', '-i', f'{ROOT}/audio/music/{f}', '-ar', '48000', '-ac', '2', f'{d}/{name}.wav'])
    missing = []
    for name in SFX_IDS:
        src = os.path.join(WORK, 'sfx', f'{name}.mp3')
        if not os.path.exists(src):
            missing.append(name); continue
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ar', '48000', '-ac', '2', f'{d}/{name}.wav'])
    if missing:
        print('\nMissing sound effects (download with Higgsfield, save to .work/sfx/<name>.mp3):')
        for n in missing:
            print(f'  {n}: {SFX_IDS[n]}')


if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    fonts(); icons(); sources(); audio()
    os.makedirs(os.path.join(WORK, 'build'), exist_ok=True)
    print('\nThen: python3 audio.py && python3 video.py <out.mp4>')
