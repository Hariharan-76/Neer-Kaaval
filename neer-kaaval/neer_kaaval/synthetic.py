"""Generate synthetic marker photos with a known water depth (for demo + tests)."""
import cv2
import numpy as np


def make_marker_image(depth_cm, n_bands=10, band_cm=10, px_per_cm=4, seed=0):
    rng = np.random.default_rng(seed)
    W, H = 360, 640
    img = np.full((H, W, 3), 205, np.uint8)
    bw = band_cm * px_per_cm
    top = 80
    x0 = (W - bw) // 2
    for i in range(n_bands):
        color = (30, 30, 200) if i % 2 == 0 else (200, 60, 30)  # BGR red, blue
        cv2.rectangle(img, (x0, top + i * bw), (x0 + bw, top + (i + 1) * bw), color, -1)
    ground = top + n_bands * bw
    water_y = int(ground - depth_cm * px_per_cm)
    if depth_cm > 0:
        img[water_y:, :] = (60, 100, 140)  # brown flood water
    img = img.astype(np.float32) + rng.normal(0, 6, img.shape)
    img = cv2.GaussianBlur(np.clip(img, 0, 255).astype(np.uint8), (3, 3), 0)
    return img
