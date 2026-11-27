"""Compositor for the AI NATI STUDIOS "reality script" ad, version 2 (1080x1920, 30 fps).

Reads the five source clips (24 fps), maps every output frame to the nearest earlier
source frame (no interpolation, faces are never re-synthesised), applies the camera
moves, then draws the prompt windows, dialogue captions, erase glitch, tagline pulse
and the end card. Frames are piped to ffmpeg together with the mastered mix.

Env:
  AINATI_WORK  work folder with src/, fonts/, icons/, build/mix_master.wav
  ONLY         comma separated output frame numbers -> stills in build/stills
  MARKERS=1    draw small "dialogue slot" tags (review aid, off by default)
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import *

SP = os.environ.get('AINATI_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work'))
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{SP}/build/approval_v2.mp4'
MARKERS = os.environ.get('MARKERS', '0') == '1'
ONLY = os.environ.get('ONLY')


def FONT(name, size):
    return ImageFont.truetype(f'{SP}/fonts/{name}.ttf', size)


# Typography ----------------------------------------------------------------
F_PROMPT = FONT('heebo-600', 58)
F_PLABEL = FONT('heebo-600', 28)
F_CAP = FONT('rubik-800', 72)
F_HEAD = FONT('rubik-800', 84)
F_LINE2 = FONT('rubik-700', 64)
F_SERV = FONT('heebo-700', 38)
F_SOC = FONT('heebo-600', 38)
F_MARK = FONT('heebo-600', 26)

GOLD = (255, 200, 61)
CORAL = (255, 77, 109)
CYAN = (61, 217, 255)
INK = (21, 17, 26)
HL = {'gold': GOLD, 'coral': CORAL, 'cyan': CYAN}

# Safe area for Reels / TikTok / Shorts interface (organic placements)
SAFE_L, SAFE_R = 90, 990
SAFE_TOP, SAFE_BOTTOM = 200, 1520


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, k=1.9):
    x = clamp(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    return im


def tlen(text, font, direction='rtl'):
    if not text:
        return 0
    return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(text, font=font, direction=direction)


# Sources and camera ----------------------------------------------------------
SRC_SIZE = {}
for c in ('v1', 'v2', 'v3', 'v4', 'v5'):
    w, h = subprocess.check_output(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height', '-of', 'csv=p=0', f'{SP}/src/{c}.mp4']).decode().strip().split(',')
    SRC_SIZE[c] = (int(w), int(h))


def read_source(clip, a, n):
    w, h = SRC_SIZE[clip]
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', f'{SP}/src/{clip}.mp4', '-map', '0:v:0',
         '-vf', f'trim=start_frame={a}:end_frame={a + n},setpts=PTS-STARTPTS',
         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    size = w * h * 3
    out = []
    for _ in range(n):
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        out.append(Image.frombuffer('RGB', (w, h), buf, 'raw', 'RGB', 0, 1).copy())
    p.stdout.close(); p.wait()
    return out


def roar_envelope(t):
    """Two roar takes; mirrors the audio placement in audio.py."""
    if not (CUT1 <= t < CUT2A):
        return 0.0
    a = math.exp(-((t - 5.62) / 0.42) ** 2)
    b = math.exp(-((t - 6.82) / 0.45) ** 2)
    return max(a, b)


def camera(kind, t):
    """(zoom, anchor point in source px, where the anchor sits on screen at full zoom, shake px)."""
    if kind == 'roar':
        u = (t - CUT1) / (CUT2A - CUT1)
        z = 1.05 + 0.07 * ease_in_out(u)
        e = roar_envelope(t)
        sx = e * 9 * (math.sin(t * 71.0) * 0.6 + math.sin(t * 113.0 + 1.3) * 0.4)
        sy = e * 7 * (math.sin(t * 83.0 + 0.7) * 0.6 + math.sin(t * 131.0 + 2.1) * 0.4)
        return z, (351, 470), (540, 723), (sx, sy)
    if kind == 'deadpan':
        u = (t - CUT2A) / (CUT2 - CUT2A)
        return 1.24 + 0.08 * u, (202, 380), (322, 660), (0, 0)
    if kind == 'erase':
        z = 1.0
        for (t0, t1, z0, z1), f in ((SNAP_IN, ease_out_cubic), (YEHUDA_PUSH, ease_out_cubic), (ZOOM_OUT, ease_in_out)):
            if t >= t1:
                z = z1
            elif t >= t0:
                z = z0 + (z1 - z0) * f((t - t0) / (t1 - t0))
        return z, (153, 300), (300, 600), (0, 0)
    return 1.0, None, None, (0, 0)


def fit_frame(img, kind, t):
    w, h = img.size
    if w / h >= 9 / 16:
        ch0, cw0 = h, h * 9 / 16
    else:
        cw0, ch0 = w, w * 16 / 9
    z, a_src, a_out, (sx, sy) = camera(kind, t)
    cw, ch = cw0 / z, ch0 / z
    if a_src is None:
        x0, y0 = (w - cw) / 2, (h - ch) / 2
    else:
        # the anchor glides from its unzoomed screen position to a_out as the zoom builds
        k = clamp((z - 1.0) / 0.25)
        nx = (a_src[0] - (w - cw0) / 2) * W / cw0
        ny = (a_src[1] - (h - ch0) / 2) * H / ch0
        ox = nx + (a_out[0] - nx) * k
        oy = ny + (a_out[1] - ny) * k
        x0 = a_src[0] - ox * cw / W
        y0 = a_src[1] - oy * ch / H
    x0 -= sx * cw / W
    y0 -= sy * ch / H
    x0 = clamp(x0, 0, w - cw)
    y0 = clamp(y0, 0, h - ch)
    out = img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    sharp = 45 + int(25 * clamp((z - 1.0) / 0.3))
    return out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=sharp, threshold=2))


# Prompt window ---------------------------------------------------------------
P_PAD_X, P_PAD_TOP, P_HEAD, P_GAP, P_PAD_BOT = 52, 26, 38, 12, 30
P_LINE = int(F_PROMPT.size * 1.34)
P_H = P_PAD_TOP + P_HEAD + P_GAP + P_LINE + P_PAD_BOT
P_R = 34
P_TOP = 206
BOX_M = 56


def rrect_mask(w, h, r):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def sparkle(d, cx, cy, r, fill):
    pts = []
    for k in range(8):
        ang = k * math.pi / 4 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.3
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


def prompt_width(*texts):
    widest = max(tlen(t, F_PROMPT) for t in texts)
    return int(max(640, min(W - 2 * 56, widest + 2 * P_PAD_X + 24)))


_panel_cache = {}


def panel_base(width, glow):
    """Static parts of the panel: shadow, glass tint, border and header."""
    key = (width, round(glow, 2))
    if key in _panel_cache:
        return _panel_cache[key]
    M, h = BOX_M, P_H
    L = Image.new('RGBA', (width + 2 * M, h + 2 * M), (0, 0, 0, 0))
    pm = rrect_mask(width, h, P_R)
    sh = Image.new('L', L.size, 0)
    sh.paste(pm, (M, M + 14))
    sh = sh.filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.55))
    L.paste(Image.new('RGBA', L.size, (0, 0, 0, 255)), (0, 0), sh)
    if glow > 0:
        g = Image.new('L', L.size, 0)
        ImageDraw.Draw(g).rounded_rectangle((M - 3, M - 3, M + width + 2, M + h + 2), P_R + 3, outline=255, width=9)
        g = g.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.95 * glow))
        L.paste(Image.new('RGBA', L.size, GOLD + (255,)), (0, 0), g)
    panel = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((0, 0, width - 1, h - 1), P_R, fill=(9, 8, 15, 172))
    sheen = Image.new('L', (width, h), 0)
    sd = ImageDraw.Draw(sheen)
    for y in range(h // 2):
        sd.line((0, y, width, y), fill=int(30 * (1 - y / (h / 2))))
    panel.paste(Image.new('RGBA', (width, h), (255, 255, 255, 255)), (0, 0), ImageChops.multiply(sheen, pm))
    pd = ImageDraw.Draw(panel)
    bcol = (255, 255, 255, 110)
    if glow > 0:
        bcol = tuple(int(bcol[i] + (GOLD[i] - bcol[i]) * glow) for i in range(3)) + (int(110 + 145 * glow),)
    pd.rounded_rectangle((0, 0, width - 1, h - 1), P_R, outline=bcol, width=3)
    hy = P_PAD_TOP + P_HEAD // 2
    sparkle(pd, width - P_PAD_X - 11, hy, 13, GOLD + (255,))
    pd.text((width - P_PAD_X - 34, hy), 'פרומפט', font=F_PLABEL, fill=GOLD + (235,), anchor='rm', direction='rtl')
    kx, ky, kw, kh = P_PAD_X, hy - 20, 56, 40
    kfill = (255, 255, 255, 30) if glow <= 0 else GOLD + (int(70 + 185 * glow),)
    pd.rounded_rectangle((kx, ky, kx + kw, ky + kh), 10, fill=kfill, outline=(255, 255, 255, 110), width=2)
    acol = (255, 255, 255, 220) if glow <= 0 else INK + (255,)
    ax = kx + kw - 15
    pd.line((ax, ky + 10, ax, ky + 25, kx + 16, ky + 25), fill=acol, width=4, joint='curve')
    pd.polygon(((kx + 10, ky + 25), (kx + 20, ky + 18), (kx + 20, ky + 32)), fill=acol)
    L.alpha_composite(panel, (M, M))
    full_mask = Image.new('L', L.size, 0)
    full_mask.paste(pm, (M, M))
    _panel_cache[key] = (L, full_mask)
    return L, full_mask


def render_prompt(width, text, cursor_on, cursor_col=GOLD, select=False, glow=0.0, sweep=None):
    base, pmask = panel_base(width, glow)
    L = base.copy()
    d = ImageDraw.Draw(L)
    M = BOX_M
    rx = M + width - P_PAD_X
    cy = M + P_PAD_TOP + P_HEAD + P_GAP + P_LINE // 2
    tw = tlen(text, F_PROMPT)
    if select and text:
        d.rounded_rectangle((rx - tw - 10, cy - P_LINE // 2 + 6, rx + 8, cy + P_LINE // 2 - 6), 10, fill=(74, 128, 255, 165))
    if text:
        d.text((rx, cy), text, font=F_PROMPT, fill=(255, 255, 255, 255), anchor='rm', direction='rtl')
    if cursor_on:
        cx = rx - tw - (12 if text else 2)
        chh = int(F_PROMPT.size * 1.04)
        d.rounded_rectangle((cx - 5, cy - chh // 2, cx, cy + chh // 2), 2, fill=cursor_col + (255,))
    if sweep is not None:
        band = Image.new('L', L.size, 0)
        bd = ImageDraw.Draw(band)
        cxs = M + width * (1.15 - 1.3 * sweep)
        for k in range(-70, 71, 3):
            bd.line((cxs + k - 46, M + P_H, cxs + k + 46, M), fill=int(80 * (1 - abs(k) / 70)), width=3)
        band = ImageChops.multiply(band, pmask)
        L.paste(Image.new('RGBA', L.size, (255, 246, 222, 255)), (0, 0), band)
    return L, pmask


def composite_panel(frame, layer, pmask, x, y, alpha=1.0, scale=1.0, jitter=0):
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
    box = (max(0, lx), max(0, ly), min(W, lx + layer.width), min(H, ly + layer.height))
    region = frame.crop(box).filter(ImageFilter.GaussianBlur(28))
    mk = pmask.crop((box[0] - lx, box[1] - ly, box[2] - lx, box[3] - ly))
    if alpha < 1:
        mk = mk.point(lambda v: int(v * alpha))
    frame.paste(region, box[:2], mk)
    lay = with_alpha(layer.crop((box[0] - lx, box[1] - ly, box[2] - lx, box[3] - ly)), alpha)
    frame.paste(lay, box[:2], lay)


def typed(text, times, t):
    return text[:sum(1 for x in times if x <= t)]


def cursor_blink(times, t):
    if times and times[0] - 0.05 <= t <= times[-1] + 0.2:
        return True
    return (t * 1.9) % 1.0 < 0.55


def pop(t, t0, dur=0.16):
    u = clamp((t - t0) / dur)
    return smooth(u), 0.92 + 0.08 * ease_out_back(u, 1.5)


PW1 = prompt_width(T1, T2)
PW3 = prompt_width(T3)


def centered_x(w):
    return int((W - w) / 2)


P3_X = W - 56 - PW3   # the erase prompt sits top right, clear of her zoomed face


def draw_prompts(frame, t):
    if 0 <= t < CUT1:
        a, s = pop(t, 0.0, 0.10)
        sel = SELECT_AT <= t < CLEAR_AT
        if t < CLEAR_AT:
            text, times = typed(T1, TYPE1, t), TYPE1
        else:
            text, times = typed(T2, TYPE2, t), TYPE2
        glow = clamp((t - ENTER1) / 0.05) if t >= ENTER1 else 0.0
        sweep = clamp((t - ENTER1) / 0.22) if t >= ENTER1 else None
        cur = cursor_blink(times, t) and t < ENTER1 and not sel
        lay, pm = render_prompt(PW1, text, cur, select=sel, glow=glow, sweep=sweep)
        composite_panel(frame, lay, pm, centered_x(PW1), P_TOP, a, s)
    if P2_SHOW <= t < CUT2:
        a, s = pop(t, P2_SHOW)
        text = typed(T3, TYPE3, t)
        glow = clamp((t - ENTER2) / 0.05) if t >= ENTER2 else 0.0
        sweep = clamp((t - ENTER2) / 0.2) if t >= ENTER2 else None
        lay, pm = render_prompt(PW3, text, cursor_blink(TYPE3, t) and t < ENTER2, glow=glow, sweep=sweep)
        composite_panel(frame, lay, pm, centered_x(PW3), P_TOP, a, s)
    if P3_SHOW <= t < P3_HIDE + 0.15:
        a, s = pop(t, P3_SHOW)
        n_del = sum(1 for x in BKSP if x <= t)
        text = T3[:len(T3) - n_del]
        jit = 0
        if t >= P3_HIDE:
            u = (t - P3_HIDE) / 0.15
            a *= 1 - u
            jit = int(((-1) ** int(t * 120)) * 30 * u)
        cur = True if t < BKSP[-1] + 0.1 else (t * 1.9) % 1 < 0.55
        lay, pm = render_prompt(PW3, text, cur, cursor_col=CORAL)
        composite_panel(frame, lay, pm, P3_X, P_TOP, a, s, jit)


# Dialogue captions -----------------------------------------------------------
CAP_CY = 1150
CAP_LINE_H = 104
CAP_GAP = 20
_sprite_cache = {}


def text_sprite(word, font, fill=(255, 255, 255), shadow=0.7):
    key = ('t', word, font.path, font.size, fill, shadow)
    if key in _sprite_cache:
        return _sprite_cache[key]
    tw = int(tlen(word, font)); asc, desc = font.getmetrics()
    M = 26
    im = Image.new('RGBA', (tw + 2 * M, asc + desc + 2 * M), (0, 0, 0, 0))
    tl = Image.new('L', im.size, 0)
    ImageDraw.Draw(tl).text((M + tw // 2, M + (asc + desc) // 2), word, font=font, fill=255, anchor='mm',
                            direction='rtl', stroke_width=7, stroke_fill=255)
    # soft wide halo plus a tighter contact shadow: readable on cream cushions and on lion fur
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 4),
             tl.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(min(255, v * shadow * 1.25))))
    im.alpha_composite(Image.new('RGBA', im.size, (0, 0, 0, 0)))
    tight = Image.new('L', im.size, 0)
    ImageDraw.Draw(tight).text((M + tw // 2, M + (asc + desc) // 2 + 3), word, font=font, fill=255, anchor='mm',
                               direction='rtl', stroke_width=3, stroke_fill=255)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0),
             tight.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.55)))
    ImageDraw.Draw(im).text((M + tw // 2, M + (asc + desc) // 2), word, font=font, fill=fill + (255,), anchor='mm',
                            direction='rtl', stroke_width=2, stroke_fill=(10, 8, 14, 150))
    _sprite_cache[key] = (im, tw)
    return _sprite_cache[key]


def chip_sprite(word, font, color, tilt):
    key = ('c', word, font.path, font.size, color, tilt)
    if key in _sprite_cache:
        return _sprite_cache[key]
    tw = int(tlen(word, font)); asc, desc = font.getmetrics()
    px, py = 22, 6
    bw, bh = tw + 2 * px, asc + desc + 2 * py - 12
    M = 30
    im = Image.new('RGBA', (bw + 2 * M, bh + 2 * M), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((M, M + 8, M + bw, M + bh + 8), 18, fill=170)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((M, M, M + bw, M + bh), 18, fill=color + (255,))
    d.rounded_rectangle((M + 3, M + 3, M + bw - 3, M + bh // 2), 15, fill=tuple(min(255, c + 22) for c in color) + (90,))
    d.text((M + bw // 2, M + bh // 2 + 1), word, font=font, fill=INK + (255,), anchor='mm', direction='rtl')
    if tilt:
        im = im.rotate(tilt, resample=Image.BICUBIC, expand=True)
    _sprite_cache[key] = (im, bw)
    return _sprite_cache[key]


TILTS = {'gold': -2.5, 'coral': 2.0, 'cyan': -2.0}


def place_sprite(frame, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01:
        return
    if rot:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.008:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    spr = with_alpha(spr, alpha)
    frame.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)


def layout_line(items, cx_center, gap=CAP_GAP):
    """items: (sprite, visual width). Returns the centre x of each item, right to left."""
    total = sum(v for _, v in items) + gap * (len(items) - 1)
    x = cx_center + total / 2
    out = []
    for _, v in items:
        out.append(x - v / 2)
        x -= v + gap
    return out


def animate_word(frame, spr, cx, cy, t, tw, out_a, chip=False):
    p = clamp((t - tw) / (0.22 if chip else 0.16))
    if p <= 0:
        return
    if chip:
        sc = 0.45 + 0.55 * ease_out_back(p, 2.8)
        rot = 9 * (1 - ease_out_cubic(p))
        dy = 0
    else:
        sc = 0.86 + 0.14 * ease_out_back(p, 1.6)
        rot = 0
        dy = 20 * (1 - ease_out_cubic(p))
    place_sprite(frame, spr, cx, cy + dy, sc, smooth(p * 1.8) * out_a, rot)


def marker(frame, text, cx, cy, alpha):
    if alpha <= 0:
        return
    tw = int(tlen(text, F_MARK))
    w, h = tw + 64, 44
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=(200, 30, 52, 205))
    d.ellipse((w - 32, h // 2 - 7, w - 18, h // 2 + 7), fill=(255, 255, 255, 255))
    d.text((w - 42, h // 2), text, font=F_MARK, fill=(255, 255, 255, 255), anchor='rm', direction='rtl')
    im = with_alpha(im, alpha)
    frame.paste(im, (int(cx - w / 2), int(cy - h / 2)), im)


SLOT_NAMES = {'d1': 'דיאלוג 1', 'd2': 'דיאלוג 2', 'd3': 'דיאלוג 3', 'd4': 'דיאלוג 4', 'd5': 'דיאלוג 5',
              'vo': 'קריינות הסיום'}


def draw_dialogue(frame, t):
    for name, lines, t_end in DIALOGUE:
        t0 = lines[0][0][2]
        if not (t0 - 0.05 <= t < t_end + 0.16):
            continue
        out_u = clamp((t - t_end) / 0.16)
        out_a = 1 - out_u
        top = CAP_CY - CAP_LINE_H * len(lines) / 2
        if MARKERS:
            marker(frame, SLOT_NAMES[name], W / 2, top - 40, out_a)
        for li, line in enumerate(lines):
            items = []
            for word, hl, tw in line:
                items.append(chip_sprite(word, F_CAP, HL[hl], TILTS[hl]) if hl else text_sprite(word, F_CAP))
            xs = layout_line(items, W / 2)
            cy = top + CAP_LINE_H * li + CAP_LINE_H / 2 + 8 * out_u
            for (spr, vis), cx, (word, hl, tw) in zip(items, xs, line):
                animate_word(frame, spr, cx, cy, t, tw, out_a, chip=bool(hl))
    if MARKERS:
        name, vs, ve = VO_SLOT
        if vs <= t < ve:
            marker(frame, SLOT_NAMES[name], W / 2, CAP_CY, 1.0)


# Effects ---------------------------------------------------------------------
def glitch(frame, t):
    if not (GLITCH0 <= t < GLITCH1):
        return frame
    u = (t - GLITCH0) / (GLITCH1 - GLITCH0)
    k = math.sin(math.pi * u) ** 0.7
    rng = np.random.default_rng(int(t * 1000))
    arr = np.array(frame)
    x0, x1, y0, y1 = 430, W, 150, 1560
    reg = arr[y0:y1, x0:x1].copy()
    y = 0
    while y < reg.shape[0]:
        bh = int(rng.integers(6, 54))
        if rng.random() < 0.55:
            reg[y:y + bh] = np.roll(reg[y:y + bh], int(rng.integers(-70, 71) * k), axis=1)
        y += bh
    s = int(9 * k) + 1
    reg[:, :, 0] = np.roll(reg[:, :, 0], s, axis=1)
    reg[:, :, 2] = np.roll(reg[:, :, 2], -s, axis=1)
    fe = np.clip(np.arange(x1 - x0) / 60.0, 0, 1)[None, :, None]
    arr[y0:y1, x0:x1] = (reg * fe + arr[y0:y1, x0:x1] * (1 - fe)).astype(np.uint8)
    return Image.fromarray(arr)


BANNER = (328, 437, 764, 548)


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
    gold = ((arr[:, :, 0] > 170) & (arr[:, :, 1] > 115) & (arr[:, :, 2] < 120)).astype(np.float32)
    xx = np.arange(arr.shape[1])[None, :] + 0.45 * np.arange(arr.shape[0])[:, None]
    gx = arr.shape[1] * (1.25 - 1.6 * u)
    band = np.clip(1 - np.abs(xx - gx) / 46, 0, 1) ** 1.5
    arr += (gold * band * 120)[:, :, None]
    big = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    bw, bh = big.size
    m = rrect_mask(bw, bh, 26).filter(ImageFilter.GaussianBlur(9))
    frame.paste(big, (int((x0 + x1) / 2 - bw / 2), int((y0 + y1) / 2 - bh / 2)), m)


# End card --------------------------------------------------------------------
ICON_PX = 50
ICONS = {n: Image.open(f'{SP}/icons/{n}.png').convert('RGBA').resize((ICON_PX, ICON_PX), Image.LANCZOS)
         for n in ('instagram', 'facebook', 'tiktok')}
_grad = None


def end_gradient():
    global _grad
    if _grad is None:
        ys = np.arange(H, dtype=np.float32)
        a = np.clip((ys - 860) / (1920 - 860), 0, 1) ** 1.15 * 0.80
        _grad = Image.fromarray((a * 255).astype(np.uint8)[:, None].repeat(W, 1))
    return _grad


HEAD_Y, LINE2_Y, SERV_Y, SOC_Y0, SOC_DY = 1062, 1166, 1268, 1352, 64
_soc_cache = {}


def handle_sprite(handle):
    if handle in _soc_cache:
        return _soc_cache[handle]
    hw = int(tlen(handle, F_SOC, 'ltr'))
    row = Image.new('RGBA', (hw + 40, 80), (0, 0, 0, 0))
    tl = Image.new('L', row.size, 0)
    ImageDraw.Draw(tl).text((20, 40), handle, font=F_SOC, fill=255, anchor='lm', stroke_width=3, stroke_fill=255)
    row.paste(Image.new('RGBA', row.size, (0, 0, 0, 255)), (0, 4),
              tl.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.6)))
    ImageDraw.Draw(row).text((20, 40), handle, font=F_SOC, fill=(255, 255, 255, 255), anchor='lm')
    _soc_cache[handle] = (row, hw)
    return _soc_cache[handle]


def draw_cta(frame, t):
    if t < CTA_IN - 0.1:
        return
    ga = smooth((t - CTA_IN + 0.1) / 0.35)
    frame.paste(Image.new('RGB', (W, H), (7, 5, 12)), (0, 0), end_gradient().point(lambda v: int(v * ga)))

    items = [text_sprite(w, F_HEAD, shadow=0.8) for w, _ in CTA_HEAD]
    for (spr, vis), cx, (_, tw) in zip(items, layout_line(items, W / 2, gap=24), CTA_HEAD):
        animate_word(frame, spr, cx, HEAD_Y, t, tw, 1.0)

    last = len(CTA_LINE2) - 1
    items = [chip_sprite(w, F_LINE2, GOLD, -2.0) if i == last else text_sprite(w, F_LINE2, shadow=0.8)
             for i, (w, _) in enumerate(CTA_LINE2)]
    for i, ((spr, vis), cx, (_, tw)) in enumerate(zip(items, layout_line(items, W / 2, gap=20), CTA_LINE2)):
        animate_word(frame, spr, cx, LINE2_Y, t, tw, 1.0, chip=(i == last))

    if t >= SERVICES_IN:
        u = ease_out_cubic((t - SERVICES_IN) / 0.25)
        parts = [text_sprite(s, F_SERV, shadow=0.75) for s in SERVICES]
        sep_w = 36
        total = sum(v for _, v in parts) + sep_w * (len(parts) - 1)
        x = W / 2 + total / 2
        y = SERV_Y + 16 * (1 - u)
        for i, (spr, vis) in enumerate(parts):
            place_sprite(frame, spr, x - vis / 2, y, 1.0, u)
            x -= vis
            if i < len(parts) - 1:
                bar = Image.new('RGBA', (4, 34), GOLD + (int(255 * u),))
                frame.paste(bar, (int(x - sep_w / 2 - 2), int(y - 17)), bar)
                x -= sep_w

    widest = max(handle_sprite(h)[1] for _, h, _ in SOCIALS)
    bx = int(W / 2 - (ICON_PX + 20 + widest) / 2)
    for i, (icon, handle, tin) in enumerate(SOCIALS):
        if t < tin:
            continue
        p = clamp((t - tin) / 0.22)
        u = ease_out_cubic(p)
        y = SOC_Y0 + i * SOC_DY
        dx = int(-28 * (1 - u))
        place_sprite(frame, ICONS[icon], bx + ICON_PX / 2 + dx, y, 0.7 + 0.3 * ease_out_back(p, 2.2), u)
        row, hw = handle_sprite(handle)
        row = with_alpha(row, u)
        frame.paste(row, (bx + ICON_PX + 20 - 20 + dx, int(y - 40)), row)


# Main loop -------------------------------------------------------------------
def frames(keep=None):
    for (clip, a, f0, f1, kind) in SEGMENTS:
        if keep is not None and not any(f0 <= k < f1 for k in keep):
            continue
        n_src = int(math.floor((f1 - f0 - 1) * SRC_FPS / FPS + 1e-6)) + 1
        src = read_source(clip, a, n_src)
        for k in range(f0, f1):
            if keep is not None and k not in keep:
                continue
            i = min(len(src) - 1, int(math.floor((k - f0) * SRC_FPS / FPS + 1e-6)))
            yield k, fit_frame(src[i], kind, k / FPS)


def main():
    keep, enc = None, None
    if ONLY:
        keep = set(int(x) for x in ONLY.split(','))
        os.makedirs(f'{SP}/build/stills', exist_ok=True)
    else:
        enc = subprocess.Popen(
            ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
             '-i', '-', '-i', f'{SP}/build/mix_master.wav',
             '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
             '-maxrate', '14M', '-bufsize', '28M',
             '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
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
        if k % 150 == 0:
            print('frame', k, flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
        print('wrote', OUT)


if __name__ == '__main__':
    main()
