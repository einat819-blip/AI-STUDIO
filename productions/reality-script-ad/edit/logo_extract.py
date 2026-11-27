"""Extract the AI NATI STUDIOS logo from clip 5 (temporal median, colour keys, cleanup)."""
import numpy as np, subprocess, cv2, sys
from PIL import Image, ImageFilter
SRC, OUT = sys.argv[1], sys.argv[2]
w, h = 704, 1248
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', 'trim=start_frame=60:end_frame=120,setpts=PTS-STARTPTS',
                    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
x0, y0, x1, y1 = 90, 0, 640, 252
med = np.median(fr[:, y0:y1, x0:x1], axis=0)
R, G, B = med[..., 0], med[..., 1], med[..., 2]; lum = med.mean(2)
sky = (B > R + 18) & (B > G + 6)
curtain = (R > 1.45 * G) & (R > 1.25 * B) & (R > 30)
gold = (R > 110) & (G > 75) & (R > B + 18) & ~sky & ~curtain
white = (lum > 160) & ~sky & ~curtain


def comps(mask, min_area):
    m8 = (mask * 255).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m8)
    out = np.zeros_like(m8)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > min_area:
            out[lab == i] = 255
    return out


core = np.maximum(comps(gold, 120), comps(white, 10))
body = cv2.morphologyEx(core, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27)))
body = cv2.erode(body, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
dark = ((lum < 95) & (np.abs(R - B) < 26) & (np.abs(G - B) < 26) & ~sky & ~curtain).astype(np.uint8) * 255
near = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
clapper = np.zeros_like(core); clapper[:118, :] = 255          # the clapperboard keeps its black stripes
dark_keep = cv2.bitwise_and(dark, cv2.bitwise_and(body, np.maximum(near, cv2.bitwise_and(body, clapper))))
m = np.maximum(core, dark_keep)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
# drop stray stars: small bright specks well outside the logo body
far = cv2.dilate(body, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
m = cv2.bitwise_and(m, far)
m[200:, :60] = 0                      # loose sliver of film strip under the logo
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
clean = np.zeros_like(m)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 18:
        clean[lab == i] = 255
alpha = Image.fromarray(clean).filter(ImageFilter.GaussianBlur(0.8))
rgba = Image.fromarray(np.clip(med, 0, 255).astype(np.uint8)).convert('RGBA')
rgba.putalpha(alpha)
rgba = rgba.crop(rgba.getbbox())
rgba.save(OUT)
print('logo', rgba.size)
