"""Writes data/sample_images/marker_depth_<cm>.png for demo uploads."""
import os
import sys
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from neer_kaaval.synthetic import make_marker_image

out = os.path.join(os.path.dirname(__file__), "..", "data", "sample_images")
os.makedirs(out, exist_ok=True)
for d in (0, 15, 30, 55, 80):
    cv2.imwrite(os.path.join(out, f"marker_depth_{d}.png"), make_marker_image(d))
print("done:", sorted(os.listdir(out)))
