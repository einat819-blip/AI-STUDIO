"""Compositor for the AI NATI STUDIOS approval cut.

Reads the five source clips, upscales to 1080x1920, draws the prompt windows,
dialogue captions, review markers, erase glitch, tagline pulse and end card,
and pipes frames to ffmpeg together with the mastered mix.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

sys.path.insert(0, os.path.dirname(__file__))
from timeline import *

SP = os.environ.get('AINATI_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{SP}/build/approval.mp4'
REVIEW_MARKERS = os.environ.get('MARKERS', '1') == '1'
ONLY = os.environ.get('ONLY')  # comma separated frame indices for stills
FONT = lambda name, size: ImageFont.truetype(f'{SP}/fonts/{name}.ttf', size)

F_UI = FONT('heebo-500', 46)
F_LABEL = FONT('heebo-500', 24)
F_CTA1 = FONT('heebo-700', 52)
F_CTA2 = FONT('heebo-500', 44)
F_CAP = FONT('rubik-800', 66)
F_MARK = FONT('heebo-500', 26)
F_INFO = FONT('heebo-700', 34)
F_SOC_L = FONT('heebo-500', 25)
F_SOC = FONT('heebo-500', 31)

GOLD = (255, 201, 60)
CORAL = (255, 92, 92)
WHITE = (255, 255, 255)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, k=1.9):
    x = clamp(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


# ------------------------------------------------------------------ sources
SRC_SIZE = {}
for c in ('v1', 'v2', 'v3', 'v4', 'v5'):
    w, h = subprocess.check_output(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height', '-of', 'csv=p=0', f'{SP}/src/{c}.mp4']).decode().strip().split(',')
    SRC_SIZE[c] = (int(w), int(h))


def read_segment(clip, a, n):
    w, h = SRC_SIZE[clip]
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', f'{SP}/src/{clip}.mp4', '-map', '0:v:0',
         '-vf', f'trim=start_frame={a}:end_frame={a + n},setpts=PTS-STARTPTS',
         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    size = w * h * 3
    for _ in range(n):
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        yield Image.frombuffer('RGB', (w, h), buf, 'raw', 'RGB', 0, 1)
    p.stdout.close(); p.wait()


PUNCH_CENTER = {('v2', 138): (330.0, 610.0)}


def fit_frame(img, clip, a, zoom):
    w, h = img.size
    if w / h >= 9 / 16:
        ch, cw = h, h * 9 / 16
    else:
        cw, ch = w, w * 16 / 9
    cw /= zoom; ch /= zoom
    cx, cy = PUNCH_CENTER.get((clip, a), (w / 2, h / 2))
    x0 = clamp(cx - cw / 2, 0, w - cw); y0 = clamp(cy - ch / 2, 0, h - ch)
    out = img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=45, threshold=2))


# ------------------------------------------------------------------ drawing helpers
def rrect_mask(w, h, r):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def star(d, cx, cy, r, fill):
    pts = []
    for k in range(8):
        ang = k * math.pi / 4 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.3
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


def tlen(text, font):
    if not text:
        return 0
    return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(text, font=font, direction='rtl')


BOX_M = 50  # margin around panel for shadow and glow


def render_panel(width, lines, label, cursor_line, cursor_on, select=False,
                 enter_glow=0.0, tint=None, sweep=None):
    """lines: list of (text, font, rgba). Returns (layer RGBA, panel mask L)."""
    pad_x, pad_top, head_h, gap, pad_bot = 40, 22, 32, 12, 26
    line_h = [int(f.size * 1.32) for _, f, _ in lines]
    h = pad_top + head_h + gap + sum(line_h) + pad_bot
    M = BOX_M
    L = Image.new('RGBA', (width + 2 * M, h + 2 * M), (0, 0, 0, 0))
    pm = rrect_mask(width, h, 30)

    # drop shadow
    sh = Image.new('L', L.size, 0)
    sh.paste(pm, (M, M + 12))
    sh = sh.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.42))
    L.paste(Image.new('RGBA', L.size, (0, 0, 0, 255)), (0, 0), sh)

    # outer glow on enter
    if enter_glow > 0:
        g = Image.new('L', L.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((M - 3, M - 3, M + width + 2, M + h + 2), 33, outline=255, width=8)
        g = g.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.9 * enter_glow))
        L.paste(Image.new('RGBA', L.size, GOLD + (255,)), (0, 0), g)

    if tint is not None:
        g = Image.new('L', L.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((M - 3, M - 3, M + width + 2, M + h + 2), 33, outline=255, width=6)
        g = g.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.55))
        L.paste(Image.new('RGBA', L.size, tint + (255,)), (0, 0), g)

    panel = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((0, 0, width - 1, h - 1), 30, fill=(14, 13, 20, 118))
    # top sheen
    sheen = Image.new('L', (width, h), 0)
    sd = ImageDraw.Draw(sheen)
    for y in range(h // 2):
        sd.line((0, y, width, y), fill=int(34 * (1 - y / (h / 2))))
    sheen = ImageChops.multiply(sheen, pm)
    panel.paste(Image.new('RGBA', (width, h), (255, 255, 255, 255)), (0, 0),
                ImageChops.multiply(sheen, Image.new('L', (width, h), 255)))
    pd = ImageDraw.Draw(panel)
    bcol = (255, 255, 255, 78)
    bw_ = 2
    if tint is not None:
        bcol = tint + (235,); bw_ = 3
    if enter_glow > 0:
        bcol = tuple(int(bcol[i] + (GOLD[i] - bcol[i]) * enter_glow) for i in range(3)) + (int(78 + 177 * enter_glow),)
    pd.rounded_rectangle((0, 0, width - 1, h - 1), 30, outline=bcol, width=bw_)

    # header: sparkle + label on the right, enter key on the left
    hy = pad_top + head_h // 2
    star(pd, width - pad_x - 9, hy, 11, GOLD + (235,))
    pd.text((width - pad_x - 28, hy), label, font=F_LABEL, fill=(255, 255, 255, 170), anchor='rm', direction='rtl')
    kx, ky, kw, kh = pad_x, hy - 17, 46, 34
    kfill = (255, 255, 255, 26) if enter_glow <= 0 else GOLD + (int(60 + 195 * enter_glow),)
    pd.rounded_rectangle((kx, ky, kx + kw, ky + kh), 9, fill=kfill, outline=(255, 255, 255, 90), width=1)
    acol = (255, 255, 255, 200) if enter_glow <= 0 else (20, 16, 8, 255)
    ax = kx + kw - 13
    pd.line((ax, ky + 9, ax, ky + 21, kx + 13, ky + 21), fill=acol, width=3, joint='curve')
    pd.polygon(((kx + 9, ky + 21), (kx + 17, ky + 15), (kx + 17, ky + 27)), fill=acol)

    # text lines, right aligned (RTL)
    rx = width - pad_x
    y = pad_top + head_h + gap
    for i, (text, font, col) in enumerate(lines):
        tw = tlen(text, font)
        if select and text:
            pd.rounded_rectangle((rx - tw - 8, y + 2, rx + 6, y + line_h[i] - 4), 8, fill=(74, 128, 255, 150))
        if text:
            pd.text((rx, y + line_h[i] // 2), text, font=font, fill=col, anchor='rm', direction='rtl')
        if i == cursor_line and cursor_on:
            cx = rx - tw - (10 if text else 2)
            ch = int(font.size * 1.02)
            cy = y + line_h[i] // 2 - ch // 2
            pd.rounded_rectangle((cx - 4, cy, cx, cy + ch), 2, fill=GOLD + (255,))
        y += line_h[i]

    # light sweep after Enter (right to left, like the text direction)
    if sweep is not None:
        band = Image.new('L', (width, h), 0)
        bd = ImageDraw.Draw(band)
        cxs = width * (1.15 - 1.3 * sweep)
        for k in range(-60, 61, 3):
            a = int(70 * (1 - abs(k) / 60))
            bd.line((cxs + k - 40, h, cxs + k + 40, 0), fill=a, width=3)
        band = ImageChops.multiply(band, pm)
        panel.paste(Image.new('RGBA', (width, h), (255, 245, 220, 255)), (0, 0), band)

    L.alpha_composite(panel, (M, M))
    full_mask = Image.new('L', L.size, 0)
    full_mask.paste(pm, (M, M))
    return L, full_mask


def composite_panel(frame, layer, pmask, x, y, alpha=1.0, scale=1.0, jitter=0):
    """x, y = top-left of the panel (excluding margin)."""
    if alpha <= 0.002:
        return
    if scale != 1.0:
        nw, nh = int(layer.width * scale), int(layer.height * scale)
        cx = x + (layer.width - 2 * BOX_M) / 2
        layer = layer.resize((nw, nh), Image.BILINEAR)
        pmask = pmask.resize((nw, nh), Image.BILINEAR)
        lx = int(cx - nw / 2); ly = int(y - BOX_M * scale)
    else:
        lx, ly = x - BOX_M, y - BOX_M
    lx += jitter
    # frosted glass: blur what is under the panel
    box = (max(0, lx), max(0, ly), min(W, lx + layer.width), min(H, ly + layer.height))
    region = frame.crop(box).filter(ImageFilter.GaussianBlur(22))
    mk = pmask.crop((box[0] - lx, box[1] - ly, box[2] - lx, box[3] - ly))
    if alpha < 1:
        mk = mk.point(lambda v: int(v * alpha))
    frame.paste(region, box[:2], mk)
    lay = layer.crop((box[0] - lx, box[1] - ly, box[2] - lx, box[3] - ly))
    if alpha < 1:
        a = lay.getchannel('A').point(lambda v: int(v * alpha))
        lay.putalpha(a)
    frame.paste(lay, box[:2], lay)


def typed(text, times, t):
    return text[:sum(1 for x in times if x <= t)]


def cursor_state(times, t):
    if times and times[0] - 0.05 <= t <= times[-1] + 0.25:
        return True
    return (t * 2.2) % 1.0 < 0.55


# ------------------------------------------------------------------ prompt windows
PX, PY, PW = 80, 168, 920


def pop(t, t0, dur=0.18):
    u = clamp((t - t0) / dur)
    return smooth(u), 0.93 + 0.07 * ease_out_back(u, 1.4)


def draw_prompts(frame, t):
    # P1: opening prompt and the lion prompt
    if 0 <= t < CUT1:
        a, s = pop(t, 0.0, 0.12)
        sel = SELECT_AT <= t < CLEAR_AT
        if t < CLEAR_AT:
            text, times = typed(T1, TYPE1, t), TYPE1
        else:
            text, times = typed(T2, TYPE2, t), TYPE2
        glow = clamp((t - ENTER1) / 0.06) if t >= ENTER1 else 0.0
        sweep = clamp((t - ENTER1) / 0.22) if t >= ENTER1 else None
        cur = cursor_state(times, t) and t < ENTER1 and not sel
        lay, pm = render_panel(PW, [(text, F_UI, (255, 255, 255, 245))], 'פרומפט', 0, cur, sel, glow, None, sweep)
        composite_panel(frame, lay, pm, PX, PY, a, s)
    # P2: mysterious man prompt
    if P2_SHOW <= t < CUT2:
        a, s = pop(t, P2_SHOW)
        text = typed(T3, TYPE3, t)
        glow = clamp((t - ENTER2) / 0.06) if t >= ENTER2 else 0.0
        sweep = clamp((t - ENTER2) / 0.2) if t >= ENTER2 else None
        cur = cursor_state(TYPE3, t) and t < ENTER2
        lay, pm = render_panel(PW, [(text, F_UI, (255, 255, 255, 245))], 'פרומפט', 0, cur, False, glow, None, sweep)
        composite_panel(frame, lay, pm, PX, PY, a, s)
    # P3: panic erase
    if P3_SHOW <= t < P3_HIDE + 0.13:
        a, s = pop(t, P3_SHOW)
        n_del = sum(1 for x in BKSP if x <= t)
        text = T3[:len(T3) - n_del]
        cur = True if t < BKSP[-1] + 0.1 else (t * 2.2) % 1 < 0.55
        jit = 0
        if t >= P3_HIDE:
            u = (t - P3_HIDE) / 0.13
            a *= 1 - u
            jit = int(((-1) ** int(t * 96)) * 26 * u)
        lay, pm = render_panel(PW, [(text, F_UI, (255, 255, 255, 245))], 'פרומפט', 0, cur, False, 0.0, CORAL)
        composite_panel(frame, lay, pm, PX, PY, a, s, jit)


def draw_cta(frame, t):
    if t < P4_SHOW:
        return
    # legibility gradient under the end-card text
    ga = smooth((t - P4_SHOW) / 0.35)
    grad = np.zeros((H, 1), np.float32)
    ys = np.arange(H)
    grad[:, 0] = np.clip((ys - 1000) / 520, 0, 1) ** 1.3 * 0.62 * ga
    g = Image.fromarray((grad * 255).astype(np.uint8)).resize((W, H))
    frame.paste(Image.new('RGB', (W, H), (8, 6, 12)), (0, 0), g)

    a, s = pop(t, P4_SHOW, 0.22)
    l1 = typed(CTA1, TYPE_CTA1, t)
    l2 = typed(CTA2, TYPE_CTA2, t)
    cl = 0 if t < TYPE_CTA2[0] - 0.05 else 1
    cur = cursor_state(TYPE_CTA1 if cl == 0 else TYPE_CTA2, t)
    lay, pm = render_panel(900, [(l1, F_CTA1, (255, 255, 255, 250)), (l2, F_CTA2, (255, 255, 255, 230))],
                           'התסריט שלכם', cl, cur)
    composite_panel(frame, lay, pm, 90, 1118, a, s)

    if t >= INFO_IN:
        u = smooth((t - INFO_IN) / 0.28)
        info = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
        d = ImageDraw.Draw(info)
        d.text((W // 2, 30), 'סרטים אישיים | פרסומות | הזמנות לאירועים', font=F_INFO, fill=GOLD + (255,),
               anchor='mm', direction='rtl')
        rows = [('Instagram', '@ainati_studios'), ('TikTok', '@einat.cohen.elyas'), ('Facebook', 'AI NATI STUDIOS')]
        for i, (lab, handle) in enumerate(rows):
            y = 92 + i * 46
            lw = d.textlength(lab, font=F_SOC_L); hw = d.textlength(handle, font=F_SOC)
            x0 = W // 2 - (lw + 14 + hw) / 2
            d.text((x0, y), lab, font=F_SOC_L, fill=(255, 255, 255, 150), anchor='lm')
            d.text((x0 + lw + 14, y), handle, font=F_SOC, fill=(255, 255, 255, 245), anchor='lm')
        sh = info.getchannel('A').filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.55))
        shadow = Image.new('RGBA', info.size, (0, 0, 0, 0)); shadow.putalpha(sh)
        base = Image.new('RGBA', info.size, (0, 0, 0, 0))
        base.alpha_composite(shadow, (0, 3)); base.alpha_composite(info)
        base.putalpha(base.getchannel('A').point(lambda v: int(v * u)))
        frame.paste(base, (0, int(1356 + 14 * (1 - u))), base)


# ------------------------------------------------------------------ dialogue captions
_word_cache = {}


def word_sprite(word, hl):
    key = (word, hl)
    if key in _word_cache:
        return _word_cache[key]
    tw = int(tlen(word, F_CAP)); asc, desc = F_CAP.getmetrics()
    M = 22
    if hl:
        px, py = 18, 8
        bw, bh = tw + 2 * px, asc + desc + 2 * py - 10
        im = Image.new('RGBA', (bw + 2 * M, bh + 2 * M), (0, 0, 0, 0))
        sh = Image.new('L', im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((M, M + 6, M + bw, M + bh + 6), 16, fill=150)
        im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(im)
        col = GOLD if hl == 'gold' else CORAL
        d.rounded_rectangle((M, M, M + bw, M + bh), 16, fill=col + (255,))
        d.text((M + bw // 2, M + bh // 2 + 1), word, font=F_CAP, fill=(18, 14, 10, 255), anchor='mm', direction='rtl')
        vis = bw
    else:
        bw, bh = tw, asc + desc
        im = Image.new('RGBA', (bw + 2 * M, bh + 2 * M), (0, 0, 0, 0))
        tl = Image.new('L', im.size, 0)
        ImageDraw.Draw(tl).text((M + bw // 2, M + bh // 2), word, font=F_CAP, fill=255, anchor='mm', direction='rtl',
                                stroke_width=3, stroke_fill=255)
        im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 4), tl.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.75)))
        d = ImageDraw.Draw(im)
        d.text((M + bw // 2, M + bh // 2), word, font=F_CAP, fill=(255, 255, 255, 255), anchor='mm', direction='rtl',
               stroke_width=2, stroke_fill=(0, 0, 0, 90))
        vis = bw
    _word_cache[key] = (im, vis, M)
    return _word_cache[key]


def pill(frame, text, cx, cy, alpha):
    if alpha <= 0:
        return
    tw = int(tlen(text, F_MARK))
    w, h = tw + 64, 44
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=(200, 30, 52, 205))
    d.ellipse((w - 32, h // 2 - 7, w - 18, h // 2 + 7), fill=(255, 255, 255, 255))
    d.text((w - 42, h // 2), text, font=F_MARK, fill=(255, 255, 255, 255), anchor='rm', direction='rtl')
    im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.paste(im, (int(cx - w / 2), int(cy - h / 2)), im)


CAP_CY = 1245
LINE_H = 96
WORD_GAP = 20


def draw_dialogue(frame, t):
    for (t0, t1, lines, marker) in DIALOGUE:
        if not (t0 - 0.15 <= t < t1 + 0.14):
            continue
        out_a = 1.0 - clamp((t - t1) / 0.14)
        n_words = sum(len(l) for l in lines)
        step = min(0.30, 0.62 * (t1 - t0) / n_words)
        block_h = LINE_H * len(lines)
        top = CAP_CY - block_h / 2
        if REVIEW_MARKERS:
            pill(frame, marker, W / 2, top - 44, smooth((t - (t0 - 0.15)) / 0.12) * out_a)
        wi = 0
        for li, line in enumerate(lines):
            sprites = [word_sprite(w, hl) for w, hl in line]
            total = sum(s[1] for s in sprites) + WORD_GAP * (len(line) - 1)
            x_right = W / 2 + total / 2
            cy = top + LINE_H * li + LINE_H / 2
            for (im, vis, M) in sprites:
                tw = t0 + wi * step
                p = clamp((t - tw) / 0.16)
                wi += 1
                if p <= 0:
                    x_right -= vis + WORD_GAP
                    continue
                sc = 0.62 + 0.38 * ease_out_back(p, 2.2)
                a = smooth(p * 1.7) * out_a
                cx = x_right - vis / 2
                spr = im
                if abs(sc - 1) > 0.01:
                    spr = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
                if a < 0.999:
                    spr = spr.copy(); spr.putalpha(spr.getchannel('A').point(lambda v: int(v * a)))
                frame.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)
                x_right -= vis + WORD_GAP
    vs, ve, vlabel = VO_SLOT
    if REVIEW_MARKERS and vs - 0.1 <= t < ve:
        pill(frame, vlabel, W / 2, CAP_CY, smooth((t - vs + 0.1) / 0.12) * (1 - clamp((t - ve + 0.12) / 0.12)))


# ------------------------------------------------------------------ effects
def glitch(frame, t):
    if not (GLITCH0 <= t < GLITCH1):
        return frame
    u = (t - GLITCH0) / (GLITCH1 - GLITCH0)
    k = math.sin(math.pi * u) ** 0.7
    rng = np.random.default_rng(int(t * 1000))
    arr = np.array(frame)
    x0, x1, y0, y1 = 420, W, 140, 1560
    reg = arr[y0:y1, x0:x1].copy()
    y = 0
    while y < reg.shape[0]:
        bh = int(rng.integers(6, 54))
        if rng.random() < 0.55:
            sh = int(rng.integers(-70, 71) * k)
            reg[y:y + bh] = np.roll(reg[y:y + bh], sh, axis=1)
        y += bh
    s = int(9 * k) + 1
    reg[:, :, 0] = np.roll(reg[:, :, 0], s, axis=1)
    reg[:, :, 2] = np.roll(reg[:, :, 2], -s, axis=1)
    # feather the region edge on the left so it does not show a seam
    fe = np.clip(np.arange(x1 - x0) / 60.0, 0, 1)[None, :, None]
    arr[y0:y1, x0:x1] = (reg * fe + arr[y0:y1, x0:x1] * (1 - fe)).astype(np.uint8)
    return Image.fromarray(arr)


BANNER = (328, 437, 764, 548)  # "אתם כן." gold stroke in the end card, output pixels


def banner_pulse(frame, t):
    if not (PULSE0 <= t < PULSE1):
        return
    u = (t - PULSE0) / (PULSE1 - PULSE0)
    s = 1 + 0.11 * math.sin(math.pi * u) ** 1.5
    x0, y0, x1, y1 = BANNER
    reg = frame.crop(BANNER)
    w, h = reg.size
    big = reg.resize((int(w * s), int(h * s)), Image.LANCZOS)
    arr = np.array(big).astype(np.float32)
    # glint across gold pixels only
    gold = ((arr[:, :, 0] > 170) & (arr[:, :, 1] > 115) & (arr[:, :, 2] < 120)).astype(np.float32)
    xx = np.arange(arr.shape[1])[None, :] + 0.45 * np.arange(arr.shape[0])[:, None]
    gx = arr.shape[1] * (1.25 - 1.6 * u)
    band = np.clip(1 - np.abs(xx - gx) / 46, 0, 1) ** 1.5
    arr += (gold * band * 120)[:, :, None]
    big = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    bw, bh = big.size
    m = rrect_mask(bw, bh, 26).filter(ImageFilter.GaussianBlur(9))
    frame.paste(big, (int((x0 + x1) / 2 - bw / 2), int((y0 + y1) / 2 - bh / 2)), m)


# ------------------------------------------------------------------ main loop
def frames(keep=None):
    """keep: optional set of output frame indices to produce (for stills)."""
    k = 0
    for (clip, a, n, z0, z1) in SEGMENTS:
        if keep is not None and not any(k <= x < k + n for x in keep):
            k += n
            continue
        for i, img in enumerate(read_segment(clip, a, n)):
            if keep is None or k in keep:
                z = z0 + (z1 - z0) * (i / max(1, n - 1))
                yield k, fit_frame(img, clip, a, z)
            k += 1


def main():
    keep = None
    if ONLY:
        keep = set(int(x) for x in ONLY.split(','))
        os.makedirs(f'{SP}/build/stills', exist_ok=True)
        enc = None
    else:
        enc = subprocess.Popen(
            ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
             '-i', '-', '-i', f'{SP}/build/mix_master.wav',
             '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
             '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
             '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT],
            stdin=subprocess.PIPE)
    for k, fr in frames(keep):
        t = k / FPS
        fr = glitch(fr, t)
        banner_pulse(fr, t)
        draw_cta(fr, t)
        draw_prompts(fr, t)
        draw_dialogue(fr, t)
        if enc:
            enc.stdin.write(fr.tobytes())
        else:
            fr.save(f'{SP}/build/stills/f{k:04d}.jpg', quality=90)
        if k % 120 == 0:
            print('frame', k, flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
        print('wrote', OUT)


if __name__ == '__main__':
    main()
