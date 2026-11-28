# -*- coding: utf-8 -*-
"""Lift a static lower-third graphic out of a clip so it can be re-placed
higher in the frame (social-media safe area).

mask(): alpha of the graphic inside rect, from its coloured fill/outline:
  pixels of the graphic's accent colours -> closed -> holes filled
  (dark panels enclosed by an accent outline become part of the graphic).
"""
import cv2
import numpy as np


def graphic_mask(img, rect, accents, close=15, keep_n=None):
    x0, y0, x1, y1 = rect
    blk = np.ascontiguousarray(img[y0:y1, x0:x1])
    hsv = cv2.cvtColor(blk, cv2.COLOR_RGB2HSV)
    m = np.zeros(blk.shape[:2], np.uint8)
    for a in accents:
        h0, h1 = a.get("h", (0, 180))
        sel = (hsv[..., 0] >= h0) & (hsv[..., 0] <= h1)
        sel &= hsv[..., 1] >= a.get("s_min", 0)
        sel &= hsv[..., 1] <= a.get("s_max", 255)
        sel &= hsv[..., 2] >= a.get("v_min", 0)
        m |= sel.astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    # fill holes: everything not reachable from the rect border is inside the graphic
    inv = (1 - m).astype(np.uint8)
    ff = inv.copy()
    h, w = ff.shape
    flood = np.zeros((h + 2, w + 2), np.uint8)
    for x in range(w):
        for y in (0, h - 1):
            if ff[y, x] == 1:
                cv2.floodFill(ff, flood, (x, y), 2)
    for y in range(h):
        for x in (0, w - 1):
            if ff[y, x] == 1:
                cv2.floodFill(ff, flood, (x, y), 2)
    filled = ((m == 1) | (ff == 1)).astype(np.uint8)
    # keep only big components (the panels), drop specks
    n, lab, stats, _ = cv2.connectedComponentsWithStats(filled, 8)
    keep = np.zeros_like(filled)
    order = sorted(range(1, n), key=lambda k: -stats[k, cv2.CC_STAT_AREA])
    if keep_n:
        order = order[:keep_n]
    for k in order:
        if stats[k, cv2.CC_STAT_AREA] > 0.02 * h * w:
            keep[lab == k] = 1
    alpha = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8)
    return alpha
