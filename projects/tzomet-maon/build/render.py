"""Frame renderer: shots, moves, grading, Hebrew subtitles, calendar time-lapse, end card, logo.
Writes raw RGB frames to ffmpeg (H.264, BT.709) and muxes the mastered audio."""
import numpy as np, cv2, subprocess, sys, os, argparse, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *
from music import accel_times

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_RUBIK = f'{ROOT}/fonts/Rubik.ttf'
FONT_HEEBO = f'{ROOT}/fonts/Heebo.ttf'
LOGO = f'{ROOT}/assets/logo.webp'
SRC_FPS = 24
LAYOUT = dict(sub_y=1250, logo_y=262, logo_right=58, cal=(540, 470, 1.0))

# 1:1 (Facebook feed) framing: same edit, per-shot vertical framing so faces and action stay in
# the square, overlays moved for a 1080x1080 frame. Index = position in the sorted SHOTS list.
SQUARE_CENTERS = {
    0: (0.50, 0.56), 1: (0.50, 0.55), 2: (0.60, 0.68), 3: (0.50, 0.36), 4: (0.55, 0.36),
    5: (0.50, 0.45), 6: (0.50, 0.50), 7: (0.50, 0.52), 8: (0.50, 0.38), 9: (0.50, 0.36),
    10: (0.50, 0.55), 11: (0.50, 0.60), 12: (0.50, 0.62), 13: (0.40, 0.45), 14: (0.50, 0.45),
    15: (0.50, 0.36), 16: (0.42, 0.45), 17: (0.50, 0.45), 18: (0.45, 0.50), 19: (0.42, 0.45),
}


def apply_square():
    global W, H
    W, H = 1080, 1080
    LAYOUT.update(sub_y=880, logo_y=72, logo_right=46, cal=(540, 255, 0.72))
    COUNTER['pos'] = (540, 150)
    assert len(SHOTS) == 21 and SHOTS[-1]['kind'] == 'endcards', 'square framing table is for the v4.2 edit'
    for i, s_ in enumerate(SHOTS):
        if i in SQUARE_CENTERS:
            s_['center'] = SQUARE_CENTERS[i]
    dy = (1920 - 1080) / 2
    ENDCARDS['lines'] = [(t, wg, sz, col, y - dy, a, b) for t, wg, sz, col, y, a, b in ENDCARDS['lines']]
    la, ly, lw = ENDCARDS['logo']
    ENDCARDS['logo'] = (la, ly - dy, lw)


def font(path, size, wght):
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([wght])
    return f


# ----------------------------------------------------------------- sources
def load_clip(i):
    p = f'{ROOT}/src/clip{i}.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-i', p, '-map', '0:v:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    wh = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                         '-of', 'csv=p=0', p], capture_output=True, text=True, check=True).stdout.strip().split('\n')[0]
    w, h = map(int, wh.split(','))
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return fr


CLIPS = {}


def clip_frame(i, t_src):
    fr = CLIPS[i]
    k = int(t_src * SRC_FPS + 1e-6)
    return fr[max(0, min(len(fr) - 1, k))]


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def warp(img, zoom, cx, cy):
    h, w = img.shape[:2]
    s = max(W / w, H / h) * zoom
    hw, hh = (W / 2) / s, (H / 2) / s
    cxp = min(max(cx * w, hw), w - hw)
    cyp = min(max(cy * h, hh), h - hh)
    M = np.float32([[s, 0, W / 2 - s * cxp], [0, s, H / 2 - s * cyp]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    bl = cv2.GaussianBlur(out, (0, 0), 1.3)
    return cv2.addWeighted(out, 1.45, bl, -0.45, 0)


# ----------------------------------------------------------------- overlays
def shadowed(img, radius=7, offset=(0, 5), opacity=0.6):
    a = img.split()[3]
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sa = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * opacity))
    sh.putalpha(sa)
    base = Image.new('RGBA', img.size, (0, 0, 0, 0))
    base.alpha_composite(sh, offset)
    base.alpha_composite(img)
    return base


def text_block(text, fnt, color, maxw, highlights=None, stroke=7, line_gap=1.12):
    """RTL Hebrew block, word-level colors, max 2 lines, centered. Returns RGBA image."""
    highlights = highlights or {}
    words = text.split(' ')
    sp = fnt.getlength(' ', direction='rtl')
    wls = [(wd, fnt.getlength(wd, direction='rtl')) for wd in words]
    total = sum(w for _, w in wls) + sp * (len(wls) - 1)
    if total <= maxw or len(wls) == 1:
        lines = [wls]
    else:   # balanced two-line split
        best = None
        for k in range(1, len(wls)):
            a_ = sum(w for _, w in wls[:k]) + sp * (k - 1)
            b_ = sum(w for _, w in wls[k:]) + sp * (len(wls) - k - 1)
            if max(a_, b_) <= maxw and (best is None or max(a_, b_) < best[0]):
                best = (max(a_, b_), k)
        lines = [wls[:best[1]], wls[best[1]:]]
    assert len(lines) <= 2, text
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    pad = stroke + 24
    widths = [sum(w for _, w in ln) + sp * (len(ln) - 1) for ln in lines]
    bw = int(max(widths)) + 2 * pad
    bh = lh * len(lines) + 2 * pad
    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, ln in enumerate(lines):
        x = bw / 2 + widths[li] / 2          # right edge (RTL starts at the right)
        y = pad + li * lh + lh / 2
        for wd, wl in ln:
            col = highlights.get(wd, color)
            d.text((x, y), wd, font=fnt, fill=col + (255,), anchor='rm', direction='rtl',
                   stroke_width=stroke, stroke_fill=(12, 12, 12, 255))
            x -= wl + sp
    return shadowed(im)


def rgba_np(im):
    return np.array(im, dtype=np.uint8)


def composite(frame, ov, cx, cy, alpha=1.0, scale=1.0):
    """alpha-composite RGBA numpy overlay centered at (cx, cy)"""
    if scale != 1.0:
        h, w = ov.shape[:2]
        ov = cv2.resize(ov, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    h, w = ov.shape[:2]
    x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    o = ov[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    a = o[..., 3:4] / 255.0 * alpha
    region = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = (region * (1 - a) + o[..., :3] * a).astype(np.uint8)


def build_overlays():
    ov = {}
    sub_font = font(FONT_RUBIK, 74, 800)
    ov['subs'] = [rgba_np(text_block(txt, sub_font, (255, 255, 255), 840, hl)) for _, _, txt, hl in SPEECH]
    tf = [font(FONT_RUBIK, 150, 900), font(FONT_RUBIK, 120, 900), font(FONT_RUBIK, 120, 900)]
    ov['titles'] = [rgba_np(text_block(txt, tf[i], col, 1000, stroke=10)) for i, (_, txt, col) in enumerate(TITLES)]
    # logo
    lg = Image.open(LOGO).convert('RGBA')
    lw = 168
    lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    pad = 12
    canvas = Image.new('RGBA', (lg.width + 2 * pad, lg.height + 2 * pad), (0, 0, 0, 0))
    canvas.alpha_composite(lg, (pad, pad))
    ov['logo'] = rgba_np(shadowed(canvas, radius=5, offset=(0, 2), opacity=0.75))
    # draft label (only for drafts)
    if DRAFT_LABEL:
        df = font(FONT_HEEBO, 30, 600)
        tw = int(df.getlength(DRAFT_LABEL, direction='rtl'))
        lab = Image.new('RGBA', (tw + 40, 56), (0, 0, 0, 0))
        d = ImageDraw.Draw(lab)
        d.rounded_rectangle((0, 0, tw + 39, 55), 28, fill=(0, 0, 0, 150))
        d.text((tw + 20, 28), DRAFT_LABEL, font=df, fill=(255, 255, 255, 230), anchor='rm', direction='rtl')
        ov['draft'] = rgba_np(lab)
    # slates
    ov['slates'] = {}
    sf_t = font(FONT_RUBIK, 58, 700)
    sf_b = font(FONT_HEEBO, 40, 500)
    for s in SHOTS:
        if s['kind'] != 'slate':
            continue
        im = Image.new('RGB', (W, H), (20, 20, 22))
        arr = np.array(im).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        stripes = ((xx + yy) // 46) % 2 == 0
        arr[stripes] += 5
        vig = 1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
        arr *= vig[..., None]
        im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((90, 560, W - 90, 1000), 26, outline=(255, 214, 64), width=4)
        d.text((W / 2, 660), s['title'], font=sf_t, fill=(255, 214, 64), anchor='mm', direction='rtl')
        for k, line in enumerate(s['body']):
            d.text((W / 2, 770 + k * 62), line, font=sf_b, fill=(225, 225, 225), anchor='mm', direction='rtl')
        d.text((W / 2, 930), 'ממתין לחומר מעינת', font=font(FONT_HEEBO, 30, 400), fill=(150, 150, 150), anchor='mm', direction='rtl')
        ov['slates'][s['t0']] = np.array(im)
    # calendar pages
    ov['cal'] = calendar_pages()
    if 'ENDCARDS' in globals():
        ov['end_lines'] = []
        # one common size for all main lines (set by the longest one, max 900 px wide), secondary line in proportion
        main = [(txt, wg, sz) for txt, wg, sz, *_ in ENDCARDS['lines'] if wg >= 700]
        common = min(sz for _, _, sz in main)
        while any(font(FONT_RUBIK, common, wg).getlength(txt, direction='rtl') > 900 for txt, wg, _ in main):
            common -= 1
        scale = common / max(sz for _, _, sz in main)
        for txt, wg, sz, col, y, a, b in ENDCARDS['lines']:
            f = font(FONT_RUBIK, common if wg >= 700 else int(round(sz * scale)), wg)
            ov['end_lines'].append(rgba_np(text_block(txt, f, col, 960, stroke=0)))
        print('end-card type size', common, 'secondary', int(round(60 * scale)))
        lg = Image.open(LOGO).convert('RGBA')
        lw = ENDCARDS['logo'][2]
        ov['end_logo'] = rgba_np(lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS))
    if 'COUNTER' in globals():
        ov['counter'] = {k: counter_glyphs(c) for k, c in (('run', (255, 255, 255)), ('lock', (255, 214, 64)))}
    return ov


def counter_glyphs(color):
    f = font(FONT_RUBIK, 118, 800)
    cell = int(max(f.getlength(ch) for ch in '0123456789')) + 4
    g = {}
    for ch in '0123456789:':
        w = cell if ch != ':' else int(f.getlength(':')) + 10
        im = Image.new('RGBA', (w + 16, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text(((w + 16) / 2, 80), ch, font=f, fill=color + (255,), anchor='mm',
                                stroke_width=4, stroke_fill=(10, 10, 10, 255))
        g[ch] = im
    return g


def counter_image(text, glyphs):
    ws = [glyphs[ch].width for ch in text]
    bw, bh = sum(ws) + 64, 196
    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, bw - 7, bh - 7), 34, fill=(14, 14, 18, 190), outline=(255, 255, 255, 70), width=3)
    x = 32
    for ch, w in zip(text, ws):
        im.alpha_composite(glyphs[ch], (x, 18))
        x += w
    return rgba_np(shadowed(im, radius=8, offset=(0, 6), opacity=0.5))


def draw_counter(frame, t, ov):
    c = COUNTER
    if not (c['t_start'] <= t < c['t_end']):
        return
    u = min(1.0, (t - c['t_start']) / (c['t_lock'] - c['t_start']))
    secs = int(round(3000 * u ** 1.7)) if t < c['t_lock'] else 3000
    text = f'{secs // 60:02d}:{secs % 60:02d}'
    locked = t >= c['t_lock']
    img = counter_image(text, ov['counter']['lock' if locked else 'run'])
    alpha = min(1.0, (t - c['t_start']) * FPS / 3, (c['t_end'] - t) * FPS / 4)
    if locked:
        k = (t - c['t_lock']) / 0.28
        sc = 1.18 + 0.16 * max(0.0, 1 - k) * (1 if k < 1 else 0)
    else:
        sc = 0.92 + 0.08 * ease((t - c['t_start']) * FPS / 5)
    composite(frame, img, c['pos'][0], c['pos'][1], alpha, sc)


CAL_PAGES = [(25, 'נובמבר'), (26, 'נובמבר'), (27, 'נובמבר'), (4, 'דצמבר'), (19, 'דצמבר'), (8, 'ינואר'),
             (2, 'מרץ'), (17, 'מאי'), (9, 'אוגוסט'), (21, 'אוקטובר'), (14, 'ינואר'), (6, 'אפריל'),
             (29, 'יולי'), (11, 'נובמבר'), (3, 'פברואר'), (18, 'יוני')]


def calendar_pages():
    pw, ph = 330, 380
    f_m = font(FONT_RUBIK, 50, 700)
    f_d = font(FONT_RUBIK, 190, 900)
    pages = []
    for day, month in CAL_PAGES:
        im = Image.new('RGBA', (pw + 40, ph + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x0, y0 = 20, 20
        d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), 22, fill=(250, 246, 236, 255))
        d.rounded_rectangle((x0, y0, x0 + pw, y0 + 104), 22, fill=(214, 52, 44, 255))
        d.rectangle((x0, y0 + 70, x0 + pw, y0 + 104), fill=(214, 52, 44, 255))
        for rx in (x0 + 80, x0 + pw - 80):
            d.ellipse((rx - 13, y0 - 10, rx + 13, y0 + 16), fill=(60, 60, 64, 255))
            d.ellipse((rx - 6, y0 - 3, rx + 6, y0 + 9), fill=(150, 150, 156, 255))
        d.text((x0 + pw / 2, y0 + 60), month, font=f_m, fill=(255, 255, 255, 255), anchor='mm', direction='rtl')
        d.text((x0 + pw / 2, y0 + 245), str(day), font=f_d, fill=(32, 32, 36, 255), anchor='mm')
        d.line((x0 + 24, y0 + ph - 34, x0 + pw - 24, y0 + ph - 34), fill=(225, 218, 204, 255), width=3)
        pages.append(rgba_np(shadowed(im, radius=10, offset=(0, 8), opacity=0.45)))
    return pages


# ----------------------------------------------------------------- grading
def daynight(img, n):
    """n = 0 day ... 1 night"""
    if n <= 0.001:
        return img
    f = img.astype(np.float32) / 255
    warm = np.sin(math.pi * min(1, n * 1.6)) * (1 - n)
    tint = np.array([1 + 0.18 * warm, 1 - 0.04 * warm, 1 - 0.28 * warm], np.float32)
    night = f * np.array([0.10, 0.15, 0.33], np.float32)
    col = f * tint * (1 - n) + night * n
    lum = f.mean(2)
    bp = np.clip((lum - 0.72) / 0.28, 0, 1) ** 2
    ymask = np.clip((np.arange(H) / H - 0.22) / 0.12, 0, 1)[:, None]
    bp = cv2.GaussianBlur((bp * ymask).astype(np.float32), (0, 0), 7)
    col += (bp[..., None] * np.array([1.0, 0.86, 0.6], np.float32)) * 1.25 * n
    return (np.clip(col, 0, 1) * 255).astype(np.uint8)


def dim_vignette(img, amt):
    f = img.astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - amt * (0.35 + 0.65 * (((xx - W / 2) / (W / 1.2)) ** 2 + ((yy - H * 0.45) / (H / 1.3)) ** 2))
    return np.clip(f * v[..., None], 0, 255).astype(np.uint8)


# ----------------------------------------------------------------- frame
def shot_at(t):
    for s in SHOTS:
        if s['t0'] <= t < s['t1']:
            return s
    return SHOTS[-1]


def render_frame(t, ov, draft=True):
    s = shot_at(t)
    u = (t - s['t0']) / (s['t1'] - s['t0'])
    if s['kind'] == 'endcards':
        return render_endcards(t - s['t0'], ov)
    if s['kind'] == 'slate':
        frame = ov['slates'][s['t0']].copy()
    else:
        z0, z1 = s['zoom']
        if 'ease_from' in s:
            ue = (t - s['ease_from']) / (s['t1'] - s['ease_from'])
            z = z0 + (z1 - z0) * ease(ue)
        else:
            z = z0 + (z1 - z0) * ease(u) if s['kind'] in ('endcard', 'still') else z0 + (z1 - z0) * u
        if s['kind'] == 'clip':
            src = clip_frame(s['clip'], s['src'] + (t - s['t0']) * s.get('speed', 1.0))
        else:
            src = clip_frame(s['clip'], s['src'])
        frame = warp(src, z, *s['center'])
        if s['kind'] == 'timelapse':
            n = 0.5 - 0.5 * math.cos(2 * math.pi * 3 * u)
            frame = daynight(frame, n)
            draw_calendar(frame, t, s, ov)
        if s['kind'] == 'endcard':
            frame = dim_vignette(frame, ENDCARD_DIM * ease((t - s['t0']) / 0.45))
    # subtitles
    for i, (a, b, txt, hl) in enumerate(SPEECH):
        if a <= t < b:
            k = (t - a) * FPS
            alpha = 1.0 if a == 0 else min(1.0, (k + 1) / 3)       # hook text is fully visible on frame 1
            sc = 1.0 if a == 0 else 0.93 + 0.07 * ease((k + 1) / 5)
            composite(frame, ov['subs'][i], 540, LAYOUT['sub_y'], alpha, sc)
    if 'COUNTER' in globals():
        draw_counter(frame, t, ov)
    # end titles
    ys = TITLE_Y
    for i, (a, txt, col) in enumerate(TITLES):
        if t >= a:
            k = (t - a) * FPS
            alpha = min(1.0, (k + 1) / 4)
            sc = 1.0 + 0.22 * (1 - ease((k + 1) / 7))
            composite(frame, ov['titles'][i], 540, ys[i], alpha, sc)
    # logo: small, top-right, below the app UI (safe zone)
    lg = ov['logo']
    composite(frame, lg, W - LAYOUT['logo_right'] - (lg.shape[1] - 24) / 2, LAYOUT['logo_y'], 0.9)
    if draft and DRAFT_LABEL:
        dl = ov['draft']
        composite(frame, dl, 40 + dl.shape[1] / 2, 70, 1.0)
    return frame


def render_endcards(r, ov):
    """black screen, clean white type, then the gold logo. Simple fades only."""
    frame = np.zeros((H, W, 3), np.uint8)
    for img, (txt, wg, sz, col, y, a, b) in zip(ov['end_lines'], ENDCARDS['lines']):
        if a <= r < b:
            al = min(ease((r - a) / 0.28), ease((b - r) / 0.2))
            composite(frame, img, W / 2, y, al)
    la, ly, lw = ENDCARDS['logo']
    if r >= la:
        k = ease((r - la) / 0.6)
        composite(frame, ov['end_logo'], W / 2, ly, k, 0.965 + 0.035 * k)
    return frame


def draw_calendar(frame, t, s, ov):
    pages = ov['cal']
    ticks = accel_times(s['t0'], s['t1'] - 0.15)
    departs = ticks[1:len(pages)]
    cx, cy, cs = LAYOUT['cal']
    pop = ease((t - s['t0']) / 0.18)
    top = sum(1 for d in departs if t >= d)
    # page underneath first
    if top + 1 < len(pages):
        composite(frame, pages[top + 1], cx, cy, pop, cs)
    if top < len(pages):
        composite(frame, pages[top], cx, cy, pop, cs * (0.85 + 0.15 * pop))
    # flying pages
    for j, d in enumerate(departs):
        p = (t - d) / 0.38
        if 0 <= p < 1:
            pg = pages[j]
            ang = -34 * p
            M = cv2.getRotationMatrix2D((pg.shape[1] / 2, pg.shape[0] / 2), ang, 1.0 - 0.12 * p)
            rot = cv2.warpAffine(pg, M, (pg.shape[1], pg.shape[0]), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            al = 1.0 if p < 0.55 else 1 - (p - 0.55) / 0.45
            composite(frame, rot, cx + cs * 400 * p ** 0.85, cy - cs * (130 * p + 380 * p * p), al, cs)


# ----------------------------------------------------------------- main
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--audio', default=None)
    ap.add_argument('--stills', default=None, help='comma list of times -> PNGs instead of video')
    ap.add_argument('--no-draft', action='store_true')
    ap.add_argument('--square', action='store_true', help='1080x1080 version for the Facebook feed')
    a = ap.parse_args()
    if a.square:
        apply_square()
    for i in sorted({s['clip'] for s in SHOTS if 'clip' in s}):
        CLIPS[i] = load_clip(i)
    ov = build_overlays()
    if a.stills:
        os.makedirs(a.out, exist_ok=True)
        for ts in a.stills.split(','):
            fr = render_frame(float(ts), ov, not a.no_draft)
            Image.fromarray(fr).save(f'{a.out}/t{float(ts):06.2f}.png')
        sys.exit()
    nfr = int(round(DURATION * FPS))
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    if a.audio:
        cmd += ['-i', a.audio]
    cmd += ['-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-profile:v', 'high', '-level', '4.2',
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
            '-g', '60', '-movflags', '+faststart']
    if a.audio:
        cmd += ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest']
    cmd += [a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nfr):
        p.stdin.write(render_frame(f / FPS, ov, not a.no_draft).tobytes())
        if f % 150 == 0:
            print('frame', f, '/', nfr, flush=True)
    p.stdin.close(); p.wait()
    print('done', a.out)
