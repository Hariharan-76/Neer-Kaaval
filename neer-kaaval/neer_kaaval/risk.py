"""Fuse citizen depth readings with rainfall + reservoir data into a ward risk level.
Weights and thresholds are heuristics for the prototype and must be calibrated with
local authority data before real use."""
from statistics import median


def consensus_depth(readings, min_conf=0.5):
    """readings: list of (depth_cm, confidence). Returns (depth or None, n_used)."""
    good = [d for d, c in readings if c >= min_conf]
    if not good:
        return None, 0
    med = median(good)
    mad = median(abs(d - med) for d in good)
    tol = max(10.0, 3 * mad)
    kept = [d for d in good if abs(d - med) <= tol]
    return float(median(kept)), len(kept)


def risk_score(depth_cm, rainfall_mm_3h, reservoir_pct):
    comps = {
        "depth": (min(depth_cm / 50.0, 1.0) if depth_cm is not None else None, 0.60),
        "rain": (min(max(rainfall_mm_3h, 0) / 50.0, 1.0), 0.25),
        "reservoir": (min(max(reservoir_pct - 70, 0) / 30.0, 1.0), 0.15),
    }
    used = {k: v for k, v in comps.items() if v[0] is not None}
    wsum = sum(w for _, w in used.values())
    score = sum(v * w for v, w in used.values()) / wsum
    level = "HIGH" if score >= 0.6 else "MEDIUM" if score >= 0.33 else "LOW"
    if depth_cm is not None:  # measured water always wins over forecasts
        if depth_cm >= 50:
            level = "HIGH"
        elif depth_cm >= 30 and level == "LOW":
            level = "MEDIUM"
    return round(score, 2), level
