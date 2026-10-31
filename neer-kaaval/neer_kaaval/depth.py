"""Estimate flood depth from a photo of a Neer Kaaval depth marker.

Marker design: a vertical strip of N equal, square bands (default 10 x 10 cm = 100 cm)
alternating red / blue, red band at the TOP, ground level at the bottom. Water hides
the lower bands, so depth = marker height - visible height.
"""
from dataclasses import dataclass
import cv2
import numpy as np


class MarkerNotFound(Exception):
    """No marker pattern detected (or the marker is fully submerged / out of frame)."""


@dataclass
class DepthResult:
    depth_cm: float
    confidence: float      # 0..1, how consistent the band pattern looked
    bands_visible: float


def _color_masks(bgr):
    h, s, v = cv2.split(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))
    saturated = (s > 120) & (v > 70)
    red = saturated & ((h <= 8) | (h >= 172))
    blue = saturated & (h >= 100) & (h <= 130)
    return red, blue


def _runs(classes, max_gap=3):
    """Run-length encode row classes (0 none, 1 red, 2 blue), bridging tiny gaps."""
    cl = list(classes)
    i = 0
    while i < len(cl):
        if cl[i] == 0:
            j = i
            while j < len(cl) and cl[j] == 0:
                j += 1
            if 0 < i and j < len(cl) and cl[i - 1] == cl[j] and (j - i) <= max_gap:
                for k in range(i, j):
                    cl[k] = cl[i - 1]
            i = j
        else:
            i += 1
    runs, cur, n = [], None, 0
    for c in cl:
        if c == cur:
            n += 1
        else:
            if cur not in (None, 0) and n >= 3:
                runs.append(n)
            cur, n = c, 1
    if cur not in (None, 0) and n >= 3:
        runs.append(n)
    return runs


def estimate_depth(bgr, marker_height_cm=100.0, n_bands=10):
    band_cm = marker_height_cm / n_bands
    red, blue = _color_masks(bgr)
    mask = ((red | blue).astype(np.uint8)) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n <= 1:
        raise MarkerNotFound("no marker pattern found")
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[idx]
    if area < 200 or h < w:
        raise MarkerNotFound("pattern too small or not vertical")
    classes = []
    for row in range(y, y + h):
        rc, bc = red[row, x:x + w].sum(), blue[row, x:x + w].sum()
        classes.append(1 if (rc > 0.5 * w and rc >= bc) else 2 if (bc > 0.5 * w) else 0)
    runs = _runs(classes)
    if not runs:
        raise MarkerNotFound("no band rows found")
    k = len(runs)
    band_px = float(np.median(runs[:-1])) if k >= 2 else float(w)  # bands are square
    n_eff = (k - 1) + min(runs[-1] / band_px, 1.0)
    depth = float(np.clip(marker_height_cm - n_eff * band_cm, 0.0, marker_height_cm))
    consistency = 1.0 - min(1.0, float(np.std(runs[:-1])) / band_px) if k >= 3 else 0.6
    confidence = 0.5 * consistency + 0.5 * (1.0 if k >= 2 else 0.6)
    if y <= 1:  # touching the top edge -> marker probably cropped
        confidence *= 0.5
    return DepthResult(round(depth, 1), round(confidence, 2), round(n_eff, 2))
