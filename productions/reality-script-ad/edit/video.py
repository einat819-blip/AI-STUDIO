"""Compositor for the AI NATI STUDIOS "reality script" ad, version 4 (1080x1920, 30 fps).

Every output frame maps to a source frame through the edit list in timeline.py
(forward, reverse, hold), gets a camera crop in source pixels (no interpolation of
faces, only crop and scale), then the overlays: prompt windows, dialogue captions,
the erase effect, the pixel re-render into the laptop shot and the staged end card.

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
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{SP}/build/out.mp4'
MARKERS = os.environ.get('MARKERS', '0') == '1'
ONLY = os.environ.get('ONLY')


def FONT(name, size):
    return ImageFont.truetype(f'{SP}/fonts/{name}.ttf', size)


F_PROMPT = FONT('heebo-600', 58)
F_PLABEL = FONT('heebo-600', 28)
F_CAP = FONT('rubik-800', 80)
F_CAP_HL = FONT('rubik-800', 88)
F_HEAD = FONT('rubik-800', 90)
F_LINE2 = FONT('rubik-800', 72)
F_LINE2_HL = FONT('rubik-800', 78)
F_SERV = FONT('heebo-700', 46)
F_SOC = FONT('heebo-700', 56)
F_MARK = FONT('heebo-600', 26)

GOLD = (255, 200, 61)
TEAL = (40, 226, 214)
CORAL = (255, 92, 108)
INK = (21, 17, 26)
CONTOUR = (12, 9, 16)
HL = {'gold': GOLD, 'teal': TEAL, 'coral': CORAL}


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp(x)
    return x ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, k=1.9):
    x = clamp(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def lerp(a, b, u):
    return a + (b - a) * u


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


# ============================================================ sources
SRC_SIZE = {}
for c in ('v1', 'v2', 'v3', 'v4', 'v5'):
    w, h = subprocess.check_output(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height', '-of', 'csv=p=0', f'{SP}/src/{c}.mp4']).decode().strip().split(',')
    SRC_SIZE[c] = (int(w), int(h))
N_SRC = 193


def read_frames(clip, a, b):
    """Decode source frames a..b inclusive (24 fps indices)."""
    w, h = SRC_SIZE[clip]
    a = max(0, a); b = min(N_SRC - 1, b)
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', f'{SP}/src/{clip}.mp4', '-map', '0:v:0',
         '-vf', f'trim=start_frame={a}:end_frame={b + 1},setpts=PTS-STARTPTS',
         '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    size = w * h * 3
    out = {}
    for i in range(a, b + 1):
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        out[i] = Image.frombuffer('RGB', (w, h), buf, 'raw', 'RGB', 0, 1).copy()
    p.stdout.close(); p.wait()
    return out


def src_time(fn, t, t0):
    u = t - t0
    kind = fn[0]
    if kind == 'lin':
        return fn[1] + u
    if kind == 'rev':
        return fn[1] - u
    if kind == 'hold':
        return fn[1]
    if kind == 'pingpong':
        a, b = fn[1], fn[2]
        return a + u if u <= b - a else b - (u - (b - a))
    if kind == 'clamp':
        return min(fn[1] + u, fn[2])
    raise ValueError(kind)


def src_index(s):
    return int(clamp(math.floor(s * SRC_FPS + 1e-6), 0, N_SRC - 1))


# ============================================================ camera
FACE_V1 = (376, 448)          # clip 1 face centre, source px (detected)
FACE_V2T = (205, 410)         # clip 2 face centre at the start (turned towards the lion)
V1_PUSH_END = (1.12, (515, 700))
V2_TIGHT = (1.62, (512, 700))


def base_crop(clip):
    w, h = SRC_SIZE[clip]
    if w / h >= 9 / 16:
        return h * 9 / 16, h
    return w, w * 16 / 9


def rect_from_anchor(clip, z, a_src, a_out):
    """Crop rect (x0, y0, cw, ch) at zoom z that puts source point a_src at output a_out."""
    w, h = SRC_SIZE[clip]
    cw0, ch0 = base_crop(clip)
    cw, ch = cw0 / z, ch0 / z
    x0 = a_src[0] - a_out[0] * cw / W
    y0 = a_src[1] - a_out[1] * ch / H
    return x0, y0, cw, ch


def rect_centered(clip, z):
    w, h = SRC_SIZE[clip]
    cw0, ch0 = base_crop(clip)
    cw, ch = cw0 / z, ch0 / z
    return (w - cw) / 2, (h - ch) / 2, cw, ch


def out_pos(clip, a_src):
    """Where a source point sits on screen with the plain (zoom 1) framing."""
    x0, y0, cw, ch = rect_centered(clip, 1.0)
    return (a_src[0] - x0) * W / cw, (a_src[1] - y0) * H / ch


def lerp_rect(r0, r1, u):
    return tuple(lerp(a, b, u) for a, b in zip(r0, r1))


def roar_envelope(t):
    if not (REVEAL[0] <= t < CUT_B):
        return 0.0
    a = math.exp(-((t - (ROAR_ON + 0.45)) / 0.40) ** 2)
    b = math.exp(-((t - (ROAR_ON + 1.25)) / 0.45) ** 2)
    return max(a, b)


def camera_rect(kind, clip, t):
    if kind == 's1':
        u = ease_in_out((t - PUSH1[0]) / (PUSH1[1] - PUSH1[0]))
        z = lerp(1.0, V1_PUSH_END[0], u)
        p0 = out_pos('v1', FACE_V1)
        a_out = (lerp(p0[0], V1_PUSH_END[1][0], u), lerp(p0[1], V1_PUSH_END[1][1], u))
        return rect_from_anchor('v1', z, FACE_V1, a_out), (0, 0)
    if kind == 's2':
        tight = rect_from_anchor('v2', V2_TIGHT[0], FACE_V2T, V2_TIGHT[1])
        if t < REVEAL[0]:
            return tight, (0, 0)
        roar_u = clamp((t - REVEAL[1]) / max(0.01, CUT_B - REVEAL[1]))
        wide = rect_from_anchor('v2', 1.05 + 0.05 * ease_in_out(roar_u), (351, 470), out_pos('v2', (351, 470)))
        u = ease_in_out((t - REVEAL[0]) / (REVEAL[1] - REVEAL[0]))
        e = roar_envelope(t)
        sx = e * 9 * (math.sin(t * 71.0) * 0.6 + math.sin(t * 113.0 + 1.3) * 0.4)
        sy = e * 7 * (math.sin(t * 83.0 + 0.7) * 0.6 + math.sin(t * 131.0 + 2.1) * 0.4)
        return lerp_rect(tight, wide, u), (sx, sy)
    if kind == 'deadpan':
        u = (t - CUT_B) / (CUT_C - CUT_B)
        return rect_from_anchor('v2', 1.24 + 0.10 * u, (202, 380), (322, 660)), (0, 0)
    if kind == 's3':
        z = 1.0
        for (t0, t1, z0, z1), f in ((SNAP_IN, ease_out_cubic), (YEHUDA_PUSH, ease_out_cubic), (ZOOM_OUT, ease_in_out)):
            if t >= t1:
                z = z1
            elif t >= t0:
                z = z0 + (z1 - z0) * f((t - t0) / (t1 - t0))
        k = clamp((z - 1.0) / 0.26)
        a_src = (153, 300)
        p0 = out_pos('v3', a_src)
        a_out = (lerp(p0[0], 300, k), lerp(p0[1], 600, k))
        return rect_from_anchor('v3', z, a_src, a_out), (0, 0)
    if kind == 's5':
        matched = rect_from_anchor('v5', 1.13, (327, 522), (545, 706))
        if t < PULLBACK[0]:
            return matched, (0, 0)
        if t < PULLBACK[1]:
            return lerp_rect(matched, rect_centered('v5', 1.0), ease_in_out((t - PULLBACK[0]) / (PULLBACK[1] - PULLBACK[0]))), (0, 0)
        u = clamp((t - PULLBACK[1]) / (END_T - PULLBACK[1]))
        return rect_centered('v5', 1.0 + 0.035 * ease_in_out(u)), (0, 0)
    return rect_centered(clip, 1.0), (0, 0)


def crop_resize(img, clip, rect, shake=(0, 0), resample=Image.LANCZOS, size=(W, H)):
    w, h = SRC_SIZE[clip]
    x0, y0, cw, ch = rect
    x0 -= shake[0] * cw / W
    y0 -= shake[1] * ch / H
    x0 = clamp(x0, 0, w - cw); y0 = clamp(y0, 0, h - ch)
    return img.resize(size, resample, box=(x0, y0, x0 + cw, y0 + ch))


def finish(img, z):
    sharp = 45 + int(30 * clamp((z - 1.0) / 0.4))
    return img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=sharp, threshold=2))


# ============================================================ prompt window (unchanged design from v2)
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
P3_X = W - 56 - PW3


def centered_x(w):
    return int((W - w) / 2)


def draw_prompts(frame, t):
    # opening prompt, then the lion prompt; it rides across the matched cut and leaves on the reveal
    if 0 <= t < REVEAL[0] + 0.15:
        a, s = pop(t, 0.0, 0.10)
        if t >= REVEAL[0]:
            a *= 1 - smooth((t - REVEAL[0]) / 0.15)
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
    # the mysterious man prompt, typed only after the lion punch
    if P2_SHOW <= t < CUT_C:
        a, s = pop(t, P2_SHOW)
        text = typed(T3, TYPE3, t)
        glow = clamp((t - ENTER2) / 0.05) if t >= ENTER2 else 0.0
        sweep = clamp((t - ENTER2) / 0.2) if t >= ENTER2 else None
        lay, pm = render_prompt(PW3, text, cursor_blink(TYPE3, t) and t < ENTER2, glow=glow, sweep=sweep)
        composite_panel(frame, lay, pm, centered_x(PW3), P_TOP, a, s)
    # panic: the same prompt comes back and is deleted
    if P3_SHOW <= t < ERASE_T + 0.12:
        a, s = pop(t, P3_SHOW)
        n_del = sum(1 for x in BKSP if x <= t)
        text = T3[:len(T3) - n_del]
        if t >= ERASE_T:
            a *= 1 - (t - ERASE_T) / 0.12
        cur = True if t < BKSP[-1] + 0.1 else (t * 1.9) % 1 < 0.55
        lay, pm = render_prompt(PW3, text, cur, cursor_col=CORAL)
        composite_panel(frame, lay, pm, P3_X, P_TOP, a, s)


# ============================================================ captions: white with a dark contour, teal / gold keys
_sprite_cache = {}


def word_sprite(word, font, fill=(255, 255, 255)):
    key = (word, font.path, font.size, fill)
    if key in _sprite_cache:
        return _sprite_cache[key]
    tw = int(tlen(word, font)); asc, desc = font.getmetrics()
    M = 30
    im = Image.new('RGBA', (tw + 2 * M, asc + desc + 2 * M), (0, 0, 0, 0))
    c = (M + tw // 2, M + (asc + desc) // 2)
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).text(c, word, font=font, fill=255, anchor='mm', direction='rtl', stroke_width=8, stroke_fill=255)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 6), sh.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
    ImageDraw.Draw(im).text(c, word, font=font, fill=fill + (255,), anchor='mm', direction='rtl',
                            stroke_width=6, stroke_fill=CONTOUR + (255,))
    _sprite_cache[key] = (im, tw)
    return _sprite_cache[key]


def place_sprite(frame, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01:
        return
    if rot:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.008:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    spr = with_alpha(spr, alpha)
    frame.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)


def layout_line(items, cx_center, gap):
    total = sum(v for _, v in items) + gap * (len(items) - 1)
    x = cx_center + total / 2
    out = []
    for _, v in items:
        out.append(x - v / 2)
        x -= v + gap
    return out


def animate_word(frame, spr, cx, cy, t, tw, out_a, key=False, shake=False):
    p = clamp((t - tw) / (0.22 if key else 0.16))
    if p <= 0:
        return
    if key:
        sc = 0.55 + 0.45 * ease_out_back(p, 2.6)
        dy = 0
    else:
        sc = 0.86 + 0.14 * ease_out_back(p, 1.6)
        dy = 18 * (1 - ease_out_cubic(p))
    dx = 0
    if shake:
        age = t - tw
        dx = 6 * math.sin(age * 115) * math.exp(-age * 4.5)
    place_sprite(frame, spr, cx + dx, cy + dy, sc, smooth(p * 1.8) * out_a)


CAP_CY = 1150
CAP_LINE_H = 112
CAP_GAP = 22
CAP_MAXW = 860


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


def draw_dialogue(frame, t):
    for name, lines, t_end, style in DIALOGUE:
        t0 = lines[0][0][2]
        if not (t0 - 0.05 <= t < t_end + 0.14):
            continue
        out_u = clamp((t - t_end) / 0.14)
        out_a = 1 - out_u
        top = CAP_CY - CAP_LINE_H * len(lines) / 2
        if MARKERS:
            marker(frame, name, W / 2, top - 30, out_a)
        for li, line in enumerate(lines):
            items = [word_sprite(w, F_CAP_HL if c else F_CAP, HL[c] if c else (255, 255, 255)) for w, c, _ in line]
            gap = CAP_GAP + (14 if sum(1 for _, c, _ in line if c) > 1 else 0)
            xs = layout_line(items, W / 2, gap)
            cy = top + CAP_LINE_H * li + CAP_LINE_H / 2 + 8 * out_u
            for (spr, vis), cx, (word, c, tw) in zip(items, xs, line):
                animate_word(frame, spr, cx, cy, t, tw, out_a, key=bool(c), shake=(style == 'shake'))
    if MARKERS:
        name, vs, ve = VO_SLOT
        if vs <= t < ve:
            marker(frame, 'קריינות', W / 2, CAP_CY, 1.0)


# ============================================================ erase: a clean digital delete of the man
def make_erase_assets():
    """Empty-room plate aligned to the held frame, and the man's silhouette from their difference."""
    import cv2
    held = np.array(list(read_frames('v3', src_index(V3_ERASE), src_index(V3_ERASE)).values())[0])
    plate = np.array(list(read_frames('v3', src_index(7.00), src_index(7.00)).values())[0])
    ga = cv2.cvtColor(held[0:160, 0:220], cv2.COLOR_RGB2GRAY).astype(np.float32)
    gb = cv2.cvtColor(plate[0:160, 0:220], cv2.COLOR_RGB2GRAY).astype(np.float32)
    (dx, dy), _ = cv2.phaseCorrelate(ga, gb)
    plate = cv2.warpAffine(plate, np.float32([[1, 0, -dx], [0, 1, -dy]]), (plate.shape[1], plate.shape[0]),
                           borderMode=cv2.BORDER_REPLICATE)
    # the man and the bouquet, traced on the held frame (source px)
    poly = [(704, 138), (560, 142), (530, 195), (519, 288), (535, 348), (505, 350), (440, 343), (330, 356),
            (276, 396), (264, 470), (262, 525), (272, 578), (300, 610), (328, 690), (338, 790), (346, 850),
            (378, 892), (430, 900), (472, 866), (492, 808), (492, 1248), (704, 1248)]
    m = Image.new('L', SRC_SIZE['v3'], 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    filled = np.array(m)
    return Image.fromarray(plate), Image.fromarray(filled).filter(ImageFilter.GaussianBlur(2))


ERASE_PLATE = None


def erase_frame(frame_src, t, rect):
    """A clean digital delete: teal selection on his silhouette, then slices slide out to the empty room."""
    global ERASE_PLATE
    if ERASE_PLATE is None:
        ERASE_PLATE = make_erase_assets()
    plate_src, mask_src = ERASE_PLATE
    base = crop_resize(frame_src, 'v3', rect)
    plate = crop_resize(plate_src, 'v3', rect)
    mask = crop_resize(mask_src.convert('RGB'), 'v3', rect, resample=Image.BILINEAR).convert('L')
    u = clamp((t - ERASE_T) / ERASE_DUR)
    A = np.array(base).astype(np.float32)
    P = np.array(plate).astype(np.float32)
    Mk = np.array(mask).astype(np.float32)[:, :, None] / 255.0
    edge_img = mask.filter(ImageFilter.MaxFilter(7))
    edge = np.clip(np.array(edge_img).astype(np.float32) / 255.0 - Mk[:, :, 0], 0, 1)[:, :, None]
    teal = np.array(TEAL, np.float32)
    sel = clamp(u / 0.2)
    obj = A * (1 - 0.22 * sel) + teal * 0.22 * sel
    rng = np.random.default_rng(5)
    removed = np.zeros(H, np.float32); offsets = np.zeros(H, np.float32)
    y = 0
    while y < H:
        bh = int(rng.integers(10, 28))
        d0 = 0.20 + 0.50 * (y / H) + rng.uniform(-0.07, 0.07)
        v = clamp((u - d0) / 0.25)
        removed[y:y + bh] = v
        offsets[y:y + bh] = 220 * ease_in_cubic(v)
        y += bh
    shifted = obj.copy()
    Ms = np.repeat(Mk, 1, axis=2)
    for yy in np.nonzero(offsets > 0.5)[0]:
        o = int(offsets[yy])
        shifted[yy] = np.roll(obj[yy], o, axis=0)
        Ms[yy] = np.roll(Mk[yy], o, axis=0)
    keep = (1 - removed)[:, None, None]
    # what remains of him (moved slices) over the empty room
    piece = Ms * keep
    img = P * (1 - piece) + shifted * piece
    # outside his silhouette the frame is untouched (her side stays as it was)
    union = np.maximum(Mk, piece)
    res = A * (1 - union) + img * union
    # thin teal outline while selected, fading as he dissolves
    ol = edge * sel * (1 - clamp((u - 0.45) / 0.3)) * 0.9
    res = res * (1 - ol) + teal * ol
    return Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))


# ============================================================ pixel re-render into the laptop shot
def pixelate(img, block):
    if block <= 1.5:
        return img
    b = int(round(block))
    small = img.resize((max(1, W // b), max(1, H // b)), Image.BILINEAR)
    return small.resize((W, H), Image.NEAREST)


BLOCK = 28
LAPTOP_OUT = (560, 1280)
_last_v3 = {}


def last_v3_frame():
    if 'f' not in _last_v3:
        i = src_index(V3_OUT - 1 / SRC_FPS)
        src = list(read_frames('v3', i, i).values())[0]
        rect, _ = camera_rect('s3', 'v3', CUT_D - 1 / FPS)
        _last_v3['f'] = finish(crop_resize(src, 'v3', rect), 1.0)
    return _last_v3['f']


def block_order():
    if 'order' not in _last_v3:
        gx, gy = np.meshgrid(np.arange(0, W, BLOCK) + BLOCK / 2, np.arange(0, H, BLOCK) + BLOCK / 2)
        d = np.hypot(gx - LAPTOP_OUT[0], (gy - LAPTOP_OUT[1]) * 0.8)
        d = d / d.max()
        rnd = np.random.default_rng(9).uniform(0, 1, d.shape)
        _last_v3['order'] = np.clip(0.82 * d + 0.18 * rnd, 0, 1)
    return _last_v3['order']


def pixel_transition(frame, t):
    """Reality is re-rendered: clip 3 breaks into blocks, the new blocks switch in from the laptop outward."""
    if CUT_D - PIX_OUT <= t < CUT_D:
        u = ease_in_cubic((t - (CUT_D - PIX_OUT)) / PIX_OUT)
        return pixelate(frame, 1 + (BLOCK - 1) * u)
    if CUT_D <= t < CUT_D + PIX_SWAP:
        u = (t - CUT_D) / PIX_SWAP
        old = np.array(pixelate(last_v3_frame(), BLOCK))
        new = np.array(pixelate(frame, BLOCK))
        order = block_order()
        on = (order <= u).astype(np.uint8)
        m = np.kron(on, np.ones((BLOCK, BLOCK), np.uint8))[:H, :W][:, :, None]
        out = old * (1 - m) + new * m
        img = Image.fromarray(out.astype(np.uint8))
        d = ImageDraw.Draw(img)
        fresh = np.argwhere((order <= u) & (order > u - 0.14))
        for by, bx in fresh:
            d.rectangle((bx * BLOCK, by * BLOCK, bx * BLOCK + BLOCK - 1, by * BLOCK + BLOCK - 1), outline=TEAL, width=2)
        return img
    if CUT_D + PIX_SWAP <= t < CUT_D + PIX_SWAP + PIX_IN:
        u = 1 - ease_out_cubic((t - CUT_D - PIX_SWAP) / PIX_IN)
        return pixelate(frame, 1 + (BLOCK - 1) * u)
    return frame


_cache = {}


# ============================================================ v5 source-space effects (follow the camera)
BANNER_SRC = (214, 284, 498, 356)     # "אתם כן." gold stroke, clip 5 source px
LOGO_SRC = (100, 8, 612, 238)         # AI NATI STUDIOS logo, clip 5 source px


def gold_glint(region, u, strength=120, width=40):
    arr = np.array(region).astype(np.float32)
    gold = ((arr[:, :, 0] > 165) & (arr[:, :, 1] > 110) & (arr[:, :, 2] < 140)).astype(np.float32)
    xx = np.arange(arr.shape[1])[None, :] + 0.45 * np.arange(arr.shape[0])[:, None]
    gx = arr.shape[1] * (1.3 - 1.7 * u)
    band = np.clip(1 - np.abs(xx - gx) / width, 0, 1) ** 1.5
    arr += (gold * band * strength)[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def v5_source_fx(img, t):
    if PULSE0 <= t < PULSE1:
        u = (t - PULSE0) / (PULSE1 - PULSE0)
        s = 1 + 0.12 * math.sin(math.pi * u) ** 1.5
        x0, y0, x1, y1 = BANNER_SRC
        reg = gold_glint(img.crop(BANNER_SRC), u)
        w, h = reg.size
        big = reg.resize((int(w * s), int(h * s)), Image.LANCZOS)
        m = rrect_mask(big.width, big.height, 18).filter(ImageFilter.GaussianBlur(6))
        img = img.copy()
        img.paste(big, (int((x0 + x1) / 2 - big.width / 2), int((y0 + y1) / 2 - big.height / 2)), m)
    if NAME_T <= t < NAME_T + 0.7:
        u = (t - NAME_T) / 0.7
        img = img.copy()
        img.paste(gold_glint(img.crop(LOGO_SRC), u, 130, 55), LOGO_SRC[:2])
    return img


# ============================================================ golden swirl transition (in the language of clip 4's magic)
SWIRL_C = (545, 905)                  # crossing point: her chest, under the matched face
SWIRL_A = 560                         # lobe reach left and right of her


def lemniscate(u, phase):
    th = u * 2 * math.pi + phase
    d = 1 + math.sin(th) ** 2
    x = SWIRL_A * math.cos(th) / d
    y = SWIRL_A * 0.62 * math.sin(th) * math.cos(th) / d
    # slight tilt and perspective so it reads as wrapping around her
    return SWIRL_C[0] + x, SWIRL_C[1] + y - 0.10 * x


def swirl_overlay(frame, t):
    if not (SWIRL[0] <= t < SWIRL[1]):
        return frame
    if t < CUT_E - 0.05:
        e = smooth((t - SWIRL[0]) / (CUT_E - 0.05 - SWIRL[0]))
    elif t < CUT_E + 0.08:
        e = 1.0
    else:
        e = 1 - smooth((t - CUT_E - 0.08) / (SWIRL[1] - CUT_E - 0.08))
    u_t = (t - SWIRL[0]) / (SWIRL[1] - SWIRL[0])
    core = Image.new('L', (W, H), 0)
    cd = ImageDraw.Draw(core)
    head = 0.25 + 1.35 * u_t                       # the ribbons keep travelling round the loop
    length = 0.80 * e + 0.08
    for strand, (ph, width, off) in enumerate(((0.0, 12, 0), (0.22, 8, 16), (0.45, 6, -14), (0.68, 5, 26), (0.9, 4, -24))):
        pts = []
        for k in range(90):
            uu = head - length * (k / 89)
            x, y = lemniscate(uu, ph)
            pts.append((x, y + off))
        for k in range(len(pts) - 1):
            taper = 1 - k / (len(pts) - 1)
            wdt = max(1, int(width * (0.35 + 0.65 * taper)))
            cd.line((pts[k], pts[k + 1]), fill=int(255 * taper), width=wdt)
    # sparkles shed along the ribbon
    rng = np.random.default_rng(int(t * 1000))
    for _ in range(int(230 * e)):
        uu = head - length * rng.uniform(0, 1)
        x, y = lemniscate(uu, rng.uniform(0, 0.7))
        x += rng.normal(0, 18); y += rng.normal(0, 18)
        r = rng.uniform(1, 3.2)
        cd.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(120, 255)))
    c = np.array(core).astype(np.float32) / 255
    g1 = np.array(core.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    g2 = np.array(core.filter(ImageFilter.GaussianBlur(22))).astype(np.float32) / 255
    light = (c[:, :, None] * np.array([255, 246, 214]) + g1[:, :, None] * np.array([255, 205, 95]) * 1.7
             + g2[:, :, None] * np.array([255, 150, 40]) * 2.4) * e
    a = np.array(frame).astype(np.float32)
    res = 255 - (255 - a) * (255 - np.clip(light, 0, 255)) / 255       # screen: light only adds, no white-out
    return Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))


# ============================================================ end card in the cinematic world
F_CTA1 = FONT('rubik-800', 84)
F_CTA2 = FONT('rubik-800', 72)
F_STUDIO = FONT('heebo-700', 60)
F_SERV2 = FONT('heebo-700', 42)
F_HANDLE = FONT('heebo-700', 64)

CTA1_Y, CTA2_Y = 1076, 1180
COMPACT_Y = 978
STUDIO_Y = 1052
SERV2_Y = 1120
SOC_Y = [1212, 1334, 1456]
BADGE = 114

GLYPHS = {n: Image.open(f'{SP}/icons/{n}.png').convert('RGBA') for n in ('instagram', 'facebook', 'tiktok')}


def text_layer(text, font, fill=(255, 255, 255), contour=6, direction='rtl'):
    key = ('tl', text, font.path, font.size, fill, contour, direction)
    if key in _cache:
        return _cache[key]
    tw = int(tlen(text, font, direction)); asc, desc = font.getmetrics()
    M = 34
    im = Image.new('RGBA', (tw + 2 * M, asc + desc + 2 * M), (0, 0, 0, 0))
    c = (M + tw // 2, M + (asc + desc) // 2)
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).text(c, text, font=font, fill=255, anchor='mm', direction=direction, stroke_width=contour + 3, stroke_fill=255)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), (0, 6), sh.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
    ImageDraw.Draw(im).text(c, text, font=font, fill=fill + (255,), anchor='mm', direction=direction,
                            stroke_width=contour, stroke_fill=CONTOUR + (255,))
    _cache[key] = (im, tw)
    return _cache[key]


def line2_layer():
    if 'l2' in _cache:
        return _cache['l2']
    parts = [text_layer(w, F_CTA2, GOLD if c else (255, 255, 255)) for w, c in CTA_LINE2]
    gap = 22
    tw = sum(v for _, v in parts) + gap * (len(parts) - 1)
    M = 34
    H2 = max(p.height for p, _ in parts)
    im = Image.new('RGBA', (tw + 2 * M, H2), (0, 0, 0, 0))
    x = M + tw
    for p, v in parts:
        im.alpha_composite(p, (int(x - v - M), (H2 - p.height) // 2))
        x -= v + gap
    _cache['l2'] = (im, tw)
    return _cache['l2']


def wipe_reveal(spr, u, band=True):
    """Light writes the line from right to left (Hebrew reading direction)."""
    if u >= 1:
        return spr
    w, h = spr.size
    edge = w * (1 - u)
    xs = np.arange(w, dtype=np.float32)
    ramp = np.clip((xs - edge) / 36 + 0.5, 0, 1)
    a = np.array(spr.getchannel('A')).astype(np.float32) * ramp[None, :]
    out = spr.copy()
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    if band and u > 0:
        glow = np.clip(1 - np.abs(xs - edge) / 26, 0, 1)[None, :] * (np.array(spr.getchannel('A')).astype(np.float32) / 255)
        g = Image.new('RGBA', (w, h), GOLD + (0,))
        g.putalpha(Image.fromarray((glow * 230).astype(np.uint8)))
        out.alpha_composite(g)
    return out


def studio_layer(spacing):
    key = ('studio', round(spacing, 1))
    if key in _cache:
        return _cache[key]
    widths = [ImageDraw.Draw(Image.new('L', (1, 1))).textlength(ch, font=F_STUDIO) for ch in STUDIO]
    tw = int(sum(widths) + spacing * (len(STUDIO) - 1))
    asc, desc = F_STUDIO.getmetrics()
    M = 30
    size = (tw + 2 * M, asc + desc + 2 * M)
    mask = Image.new('L', size, 0)
    md = ImageDraw.Draw(mask)
    stroke = Image.new('L', size, 0)
    sd = ImageDraw.Draw(stroke)
    x = M
    for ch, wch in zip(STUDIO, widths):
        md.text((x, M), ch, font=F_STUDIO, fill=255)
        sd.text((x, M), ch, font=F_STUDIO, fill=255, stroke_width=5, stroke_fill=255)
        x += wch + spacing
    grad = np.zeros((size[1], size[0], 3), np.float32)
    ys = np.linspace(0, 1, size[1])[:, None]
    top, bot = np.array([255, 238, 168], np.float32), np.array([222, 148, 38], np.float32)
    grad = (top[None, None, :] * (1 - ys[:, :, None]) + bot[None, None, :] * ys[:, :, None]).repeat(size[0], 1)
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    im.paste(Image.new('RGBA', size, (0, 0, 0, 255)), (0, 5), stroke.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.5)))
    im.paste(Image.new('RGBA', size, CONTOUR + (255,)), (0, 0), stroke)
    gold = Image.fromarray(grad.astype(np.uint8)).convert('RGBA')
    im.paste(gold, (0, 0), mask)
    _cache[key] = (im, tw)
    return _cache[key]


def badge(icon):
    if ('badge', icon) in _cache:
        return _cache[('badge', icon)]
    S = BADGE * 2                     # draw at 2x, downsample for clean edges
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    circle = Image.new('L', (S, S), 0)
    ImageDraw.Draw(circle).ellipse((2, 2, S - 3, S - 3), fill=255)
    if icon == 'instagram':
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
        u = np.clip((xx + (1 - yy)) / 2, 0, 1)
        stops = [(0.0, (254, 218, 117)), (0.3, (250, 126, 30)), (0.55, (214, 41, 118)), (0.8, (150, 47, 191)), (1.0, (79, 91, 213))]
        rgb = np.zeros((S, S, 3), np.float32)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            m = (u >= a) & (u <= b)
            k = ((u - a) / (b - a))[..., None]
            rgb = np.where(m[..., None], np.array(ca) * (1 - k) + np.array(cb) * k, rgb)
        im.paste(Image.fromarray(rgb.astype(np.uint8)), (0, 0), circle)
        g = GLYPHS['instagram'].resize((int(S * 0.56), int(S * 0.56)), Image.LANCZOS)
        im.alpha_composite(g, ((S - g.width) // 2, (S - g.height) // 2))
    elif icon == 'facebook':
        disc = Image.new('L', (S, S), 0)
        ImageDraw.Draw(disc).ellipse((10, 10, S - 11, S - 11), fill=255)
        im.paste(Image.new('RGBA', (S, S), (255, 255, 255, 255)), (0, 0), disc)
        g = GLYPHS['facebook'].resize((S, S), Image.LANCZOS)
        blue = Image.new('RGBA', (S, S), (24, 119, 242, 255))
        im.paste(blue, (0, 0), g.getchannel('A'))
    else:
        im.paste(Image.new('RGBA', (S, S), (18, 16, 22, 255)), (0, 0), circle)
        g = GLYPHS['tiktok'].resize((int(S * 0.54), int(S * 0.54)), Image.LANCZOS)
        ox, oy = (S - g.width) // 2, (S - g.height) // 2
        for col, dx, dy in (((37, 244, 238), -5, -4), ((254, 44, 85), 5, 4), ((255, 255, 255), 0, 0)):
            layer = Image.new('RGBA', g.size, col + (255,))
            layer.putalpha(g.getchannel('A'))
            im.alpha_composite(layer, (ox + dx, oy + dy))
    ring = Image.new('L', (S, S), 0)
    ImageDraw.Draw(ring).ellipse((2, 2, S - 3, S - 3), outline=255, width=5)
    im.paste(Image.new('RGBA', (S, S), (255, 255, 255, 200)), (0, 0), ring)
    sh = Image.new('RGBA', (S + 60, S + 60), (0, 0, 0, 0))
    shm = Image.new('L', sh.size, 0)
    ImageDraw.Draw(shm).ellipse((30, 40, 30 + S, 40 + S), fill=150)
    sh.paste(Image.new('RGBA', sh.size, (0, 0, 0, 255)), (0, 0), shm.filter(ImageFilter.GaussianBlur(12)))
    sh.alpha_composite(im, (30, 30))
    out = sh.resize((sh.width // 2, sh.height // 2), Image.LANCZOS)
    _cache[('badge', icon)] = out
    return out


BRAND_COL = {'instagram': (225, 48, 108), 'facebook': (24, 119, 242), 'tiktok': (37, 244, 238)}


def soft_dot(r):
    key = ('dot', r)
    if key not in _cache:
        S = r * 6
        m = Image.new('L', (S, S), 0)
        ImageDraw.Draw(m).ellipse((S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(r * 0.9))
        _cache[key] = m
    return _cache[key]


_rng = np.random.default_rng(21)
PARTICLES = [dict(x=_rng.uniform(40, 1040), y=_rng.uniform(600, 1950), v=_rng.uniform(28, 75),
                  r=int(_rng.integers(2, 7)), a=_rng.uniform(0.25, 0.75), ph=_rng.uniform(0, 6.28),
                  sw=_rng.uniform(8, 22)) for _ in range(54)]


def warm_light(frame, t):
    """Golden ambience for the end card: a warm glow behind the text and drifting gold dust."""
    k = smooth((t - (CTA1_T - 0.2)) / 0.6)
    if k <= 0:
        return frame
    bump = 0.0
    if t >= FINAL_HIT - 0.05:
        bump = math.exp(-(t - FINAL_HIT) * 2.2) * 0.9 if t >= FINAL_HIT else 0
    if 'glow' not in _cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((xx - 540) / 560) ** 2 + ((yy - 1250) / 420) ** 2))
        _cache['glow'] = g
    g = _cache['glow'] * (0.16 * k + 0.22 * bump)
    light = g[:, :, None] * np.array([255, 182, 78], np.float32)
    dust = Image.new('L', (W, H), 0)
    for p in PARTICLES:
        age = t - (CTA1_T - 0.2)
        y = p['y'] - p['v'] * age
        y = (y - 600) % 1400 + 600
        x = p['x'] + p['sw'] * math.sin(age * 1.3 + p['ph'])
        tw = 0.6 + 0.4 * math.sin(age * 5 + p['ph'] * 3)
        d = soft_dot(p['r'])
        dust.paste(Image.new('L', d.size, int(255 * p['a'] * tw * k)), (int(x - d.width / 2), int(y - d.height / 2)), d)
    dn = np.array(dust).astype(np.float32)[:, :, None] / 255 * np.array([255, 214, 130], np.float32)
    light = light + dn * (1 + bump)
    a = np.array(frame).astype(np.float32)
    res = 255 - (255 - a) * (255 - np.clip(light, 0, 255)) / 255
    return Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))


def fingertip_out(t):
    rect, _ = camera_rect('s5', 'v5', t)
    x0, y0, cw, ch = rect
    return (333 - x0) * W / cw, (640 - y0) * H / ch


def draw_comet(frame, t):
    if not (FINGER_T <= t < CTA1_T + 0.05):
        return
    u = ease_in_out((t - FINGER_T) / (CTA1_T - FINGER_T))
    sx, sy = fingertip_out(t)
    l1, w1 = text_layer(CTA_LINE1, F_CTA1)
    ex, ey = W / 2 + w1 / 2, CTA1_Y
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    for k in range(14):
        v = max(0.0, u - k * 0.035)
        px, py = sx + (ex - sx) * v, sy + (ey - sy) * v - 60 * math.sin(math.pi * v)
        r = 13 - k * 0.8
        if r > 1:
            d.ellipse((px - r, py - r, px + r, py + r), fill=int(255 * (1 - k / 14)))
    glow = layer.filter(ImageFilter.GaussianBlur(10))
    light = np.array(ImageChops.add(layer, glow)).astype(np.float32)[:, :, None] / 255 * np.array([255, 214, 120], np.float32)
    a = np.array(frame).astype(np.float32)
    frame.paste(Image.fromarray(np.clip(255 - (255 - a) * (255 - light) / 255, 0, 255).astype(np.uint8)))


def draw_end(frame, t):
    if t < CUT_E:
        return frame
    frame = warm_light(frame, t)
    draw_comet(frame, t)
    # --- the call to action, written by light, then tucked up as one compact line
    l1, w1 = text_layer(CTA_LINE1, F_CTA1)
    l2, w2 = line2_layer()
    if t >= CTA1_T:
        mu = ease_in_out((t - COMPACT_T) / 0.38) if t >= COMPACT_T else 0.0
        s_c = 860 / (w1 + w2 + 28)
        total = s_c * (w1 + w2) + 28
        c1 = (W / 2 + total / 2 - s_c * w1 / 2, COMPACT_Y)
        c2 = (W / 2 - total / 2 + s_c * w2 / 2, COMPACT_Y + 3)
        for spr, tw0, pos_big, pos_c, t0 in ((l1, w1, (W / 2, CTA1_Y), c1, CTA1_T), (l2, w2, (W / 2, CTA2_Y), c2, CTA2_T)):
            if t < t0:
                continue
            u = clamp((t - t0) / 0.36)
            img = wipe_reveal(spr, ease_out_cubic(u))
            sc = 1 + (s_c - 1) * mu
            cx = pos_big[0] + (pos_c[0] - pos_big[0]) * mu
            cy = pos_big[1] + (pos_c[1] - pos_big[1]) * mu
            place_sprite(frame, img, cx, cy, sc, 1.0)
    # --- studio name: tracked gold letters settle in on the downbeat, the logo above glints
    if t >= NAME_T:
        p = clamp((t - NAME_T) / 0.45)
        spr, tw = studio_layer(8 + 26 * (1 - ease_out_cubic(p)))
        place_sprite(frame, spr, W / 2, STUDIO_Y, 1.0, smooth(p * 1.4))
    # --- services
    if t >= SERV_T:
        parts = [text_layer(s, F_SERV2) for s in SERVICES]
        sep = 44
        total = sum(v for _, v in parts) + sep * (len(parts) - 1)
        x = W / 2 + total / 2
        for i, (spr, v) in enumerate(parts):
            p = clamp((t - SERV_T - i * 0.07) / 0.28)
            if p > 0:
                place_sprite(frame, spr, x - v / 2, SERV2_Y + 16 * (1 - ease_out_cubic(p)), 1.0, smooth(p * 1.5))
            x -= v
            if i < len(parts) - 1:
                pb = clamp((t - SERV_T - i * 0.07 - 0.1) / 0.2)
                if pb > 0:
                    bar = Image.new('RGBA', (5, 44), GOLD + (int(255 * pb),))
                    frame.paste(bar, (int(x - sep / 2 - 2), int(SERV2_Y - 22)), bar)
                x -= sep
    # --- networks: colour badges pop in on the beat, a ring bursts, the handle slides in
    widest = max(text_layer(h, F_HANDLE, contour=5, direction='ltr')[1] for _, h in SOCIALS)
    block = BADGE + 28 + widest
    bx = W / 2 - block / 2
    beat_phase = None
    for i, ((icon, handle), tin) in enumerate(zip(SOCIALS, SOC_TIMES)):
        if t < tin:
            continue
        y = SOC_Y[i]
        p = clamp((t - tin) / 0.30)
        sc = ease_out_back(p, 2.6)
        # gentle breathing on every later beat keeps the card in time with the music
        since = t - tin
        if since > 0.5:
            ph = ((t - MUSIC_FINALE_START - LOOP_E) % 0.5) / 0.5
            sc *= 1 + 0.045 * math.exp(-ph * 6)
        b = badge(icon)
        place_sprite(frame, b, bx + BADGE / 2, y, max(0.01, sc), smooth(p * 2), rot=-28 * (1 - ease_out_cubic(p)))
        rp = clamp((t - tin) / 0.42)
        if 0 < rp < 1:
            r = BADGE / 2 + 46 * ease_out_cubic(rp)
            ring = Image.new('RGBA', (int(2 * r + 12), int(2 * r + 12)), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((6, 6, 6 + 2 * r, 6 + 2 * r), outline=BRAND_COL[icon] + (int(230 * (1 - rp)),),
                                         width=max(1, int(7 * (1 - rp))))
            frame.paste(ring, (int(bx + BADGE / 2 - ring.width / 2), int(y - ring.height / 2)), ring)
        ph = clamp((t - tin - 0.06) / 0.28)
        if ph > 0:
            spr, hw = text_layer(handle, F_HANDLE, contour=5, direction='ltr')
            dx = -40 * (1 - ease_out_cubic(ph))
            place_sprite(frame, spr, bx + BADGE + 28 + hw / 2 + dx, y, 1.0, smooth(ph * 1.6))
    return frame


# ============================================================ main
def segment_frames(keep=None):
    for (clip, t0, t1, fn, cam) in SEGMENTS:
        f0, f1 = int(round(t0 * FPS)), int(round(t1 * FPS))
        ks = [k for k in range(f0, f1) if keep is None or k in keep]
        if not ks:
            continue
        idx = [src_index(src_time(fn, k / FPS, t0)) for k in ks]
        frames = read_frames(clip, min(idx), max(idx))
        for k, i in zip(ks, idx):
            yield k, clip, cam, frames[min(frames.keys(), key=lambda j: abs(j - i))]


def render_frame(k, clip, cam, src):
    t = k / FPS
    if clip == 'v5':
        src = v5_source_fx(src, t)
    rect, shake = camera_rect(cam, clip, t)
    z = base_crop(clip)[0] / rect[2]
    if clip == 'v3' and ERASE_T <= t < S3E_T:
        fr = erase_frame(src, t, rect)
    else:
        fr = crop_resize(src, clip, rect, shake)
    fr = finish(fr, z)
    fr = pixel_transition(fr, t)
    fr = swirl_overlay(fr, t)
    fr = draw_end(fr, t)
    draw_prompts(fr, t)
    draw_dialogue(fr, t)
    return fr


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
    n = 0
    for k, clip, cam, src in segment_frames(keep):
        fr = render_frame(k, clip, cam, src)
        if enc:
            enc.stdin.write(fr.tobytes())
        else:
            fr.save(f'{SP}/build/stills/f{k:04d}.jpg', quality=90)
        n += 1
        if k % 150 == 0:
            print('frame', k, flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
        print('wrote', OUT, n, 'frames')


if __name__ == '__main__':
    main()
