# -*- coding: utf-8 -*-
"""V5_APPROVED, square 1:1 (1080x1080) for Facebook.

Same edit as edit_v5.py: narration, music, SFX, timing, scene order and caption
text are inherited unchanged. Only the framing changes: each shot is reframed
from the source clip (one uniform scale, no stretching) so faces, billboards,
the map and "אשכול ✗" stay in the square. Captions sit low in the frame, with
per-line positions where they would cover text printed in the picture.
"""
import copy
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("edit_v5", os.path.join(os.path.dirname(os.path.abspath(__file__)), "edit_v5.py"))
_v5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v5)
globals().update({k: copy.deepcopy(v) for k, v in vars(_v5).items() if k.isupper()})

W, H = 1080, 1080

# per-segment square framing (overrides the 9:16 zoom/centre)
SQ = {
    "1":   dict(cy=0.30),
    "2":   dict(cy=0.36),
    "3":   dict(zoom=1.0, cx=0.60, cy=0.45, zoom_to=1.30, cx_to=0.70, cy_to=0.42),
    "4":   dict(cy=0.38, zoom=1.0, zoom_to=1.10),
    "5a":  dict(cy=0.38),
    "5b":  dict(zoom=1.18, cx=0.47, cy=0.32),
    "6a":  dict(cy=0.36),
    "6b":  dict(zoom=1.25, cx=0.50, cy=0.27),
    "7":   dict(cy=0.36),
    "8":   dict(cy=0.45),
    "9":   dict(cy=0.36),
    "10":  dict(zoom=1.0, cx=0.62, cy=0.362, zoom_to=1.30, cx_to=0.611, cy_to=0.577, zoom_t0=1.35, zoom_t1=1.85),
    "11a": dict(cy=0.40),
    "11b": dict(cy=0.16),
    "11c": dict(cy=0.30),
    "11d": dict(cy=0.40),
    "11e": dict(cy=0.16),
    "12a": dict(cy=0.36),
    "12b": dict(cy=0.36),
    "12c": dict(cy=0.36),
    "13a": dict(cy=0.30),
    "13b": dict(zoom=1.0, cx=0.5, cy=0.28),
    "13c": dict(zoom=1.0, cx=0.5, cy=0.30),
}
SEGMENTS = [dict(s, **SQ.get(s["id"], {})) for s in SEGMENTS]

CAPTIONS["margin_v"] = 80
# lines whose 9:16 position override must be reset for the square
VO = [(seg, off, txt, hl, {k: v for k, v in opt.items() if k != "marginv"}) for seg, off, txt, hl, opt in VO]
# square-specific caption heights (distance from the bottom), by VO line index
SQ_MARGINV = {
    15: 340, 16: 340,   # shot 8: above the map, "אשכול ✗" stays clear
}
SQ_TOP = {
    17: 40,             # shot 9: over her hair; eyes, mouth and the hand pointing at herself stay clear
    18: 110,            # shot 10 wide: over his hair; face, map and red zone stay clear
}
for _i, _mv in SQ_MARGINV.items():
    VO[_i][4]["marginv"] = _mv
for _i, _mv in SQ_TOP.items():
    VO[_i][4].update(top=True, marginv=_mv)

LOGO = dict(width=190, x=854, y=30, opacity=0.92)
ENDCARD_V4 = dict(ENDCARD_V4, brush_y=540, logo_y=470, tagline_y=708, bg_y0=760)
FINAL_CRF = 14   # visually lossless; keeps the file easy to download (<~85 MB)
