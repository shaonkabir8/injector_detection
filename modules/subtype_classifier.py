"""
Model D — Vehicle Subtype Classifier
=====================================

Refines the broad COCO vehicle class into a specific brick-kiln sub-type
using a **7-feature scoring matrix** computed from the vehicle crop.

This goes beyond the pure geometry rules in the YOLO stage (Model B) by
analysing the crop's internal texture and gradient patterns — features that
distinguish, e.g., a tractor from a short truck even when their bounding
boxes have the same aspect ratio.

Features
--------
  1. aspect_ratio          — bbox width / height  (fast: low → Tractor/Trolley)
  2. size_fraction         — bbox area / image area  (large → Truck-Large)
  3. height_fraction       — bbox height / image height  (tall → Truck-Large dump)
  4. edge_density          — Canny edges / total crop pixels
                             Tractors (complex cab + tyres) > Flat trucks
  5. horiz_gradient_ratio  — mean(|Sobel_x|) / (mean(|Sobel_x|) + mean(|Sobel_y|))
                             Trucks have strong horizontal lines (flat bed, side panels)
                             → ratio > 0.55
  6. top_half_edge_ratio   — edge_density(top 40%) / edge_density(bottom 40%)
                             Tractors have complex cab at top → ratio > 1.2
  7. color_uniformity      — 1 − (LAB std-dev / 60)  capped 0–1
                             Metallic empty trucks are uniform; loaded trucks vary

Scoring
-------
For each candidate sub-type a compatibility score (0–1) is computed by
measuring how well each feature falls inside the expected range.  The
candidate with the highest total score wins.

Expected feature ranges (calibrated for side-view factory gate cameras,
Bangladesh brick kiln vehicles):

  Sub-type      AR        SZ      HFrac   EdgeD   HGrad   TopHalf  ColorU
  Tractor       0.8–1.8   any     any     .08–.30  <.55    >1.1     any
  Trolley       1.0–3.5   any     any     .02–.18  >.50    <1.1     any
  Truck-Large   2.5–7.0   >.06    any     .03–.15  >.55    <1.0     any
  Truck-Medium  1.6–3.5   >.03    any     .03–.15  >.55    <1.0     any
  Truck-Small   1.0–2.4   <.10    any     .03–.18  any     any      any

COCO class constraint: class 5 can only be Trolley or Bus; class 7 can be
all five primary types; class 2 can only be Van/Car (non-primary).
"""
from __future__ import annotations

import logging

import cv2
import numpy as np

from schemas.detection import VehicleSubType, PRIMARY_SUBTYPES, BoundingBox

logger = logging.getLogger(__name__)

# ── Feature extraction ────────────────────────────────────────────────────────

def _extract_features(
    image: np.ndarray,
    bbox: BoundingBox,
    img_h: int,
    img_w: int,
) -> dict[str, float]:
    """
    Extract 7 discriminative features from the vehicle crop.

    Returns dict with keys matching the feature names above.
    """
    bw = bbox.width
    bh = bbox.height
    if bh == 0 or bw == 0:
        return {}

    # Geometry features
    aspect_ratio   = bw / bh
    size_fraction  = (bw * bh) / max(1, img_w * img_h)
    height_fraction = bh / max(1, img_h)

    # Crop the vehicle
    x1 = max(0, bbox.x1);  x2 = min(img_w, bbox.x2)
    y1 = max(0, bbox.y1);  y2 = min(img_h, bbox.y2)
    crop = image[y1:y2, x1:x2]

    if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
        return {
            "aspect_ratio":       round(aspect_ratio, 3),
            "size_fraction":      round(size_fraction, 4),
            "height_fraction":    round(height_fraction, 3),
            "edge_density":       0.0,
            "horiz_gradient_ratio": 0.5,
            "top_half_edge_ratio":  1.0,
            "color_uniformity":   0.5,
        }

    gray    = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Feature 4: Overall edge density
    edges = cv2.Canny(blurred, 40, 120)
    edge_density = float(np.sum(edges > 0)) / max(1, edges.size)

    # Feature 5: Horizontal vs vertical gradient dominance
    sobel_x = np.abs(cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3))
    sobel_y = np.abs(cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3))
    sx_mean = float(np.mean(sobel_x))
    sy_mean = float(np.mean(sobel_y))
    total_grad = sx_mean + sy_mean + 1e-6
    horiz_gradient_ratio = sx_mean / total_grad  # high → horizontal dominant

    # Feature 6: Edge density ratio top 40% vs bottom 40%
    ch = edges.shape[0]
    top_edge    = float(np.sum(edges[:int(ch * 0.4)] > 0)) / max(1, int(ch * 0.4) * edges.shape[1])
    bottom_edge = float(np.sum(edges[int(ch * 0.6):] > 0)) / max(1, int(ch * 0.4) * edges.shape[1])
    top_half_edge_ratio = top_edge / max(1e-6, bottom_edge)

    # Feature 7: Color uniformity (1 - normalised LAB std-dev)
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    lab_std = float(np.std(lab.reshape(-1, 3), axis=0).mean())
    color_uniformity = round(max(0.0, 1.0 - lab_std / 60.0), 3)

    return {
        "aspect_ratio":         round(aspect_ratio, 3),
        "size_fraction":        round(size_fraction, 4),
        "height_fraction":      round(height_fraction, 3),
        "edge_density":         round(edge_density, 4),
        "horiz_gradient_ratio": round(horiz_gradient_ratio, 3),
        "top_half_edge_ratio":  round(top_half_edge_ratio, 3),
        "color_uniformity":     round(color_uniformity, 3),
    }


# ── Scoring matrix ────────────────────────────────────────────────────────────

def _range_score(value: float, lo: float, hi: float) -> float:
    """1.0 if value is inside [lo, hi], decays linearly to 0 outside."""
    if lo <= value <= hi:
        return 1.0
    span = hi - lo
    if value < lo:
        return max(0.0, 1.0 - (lo - value) / max(1e-6, span * 0.5))
    return max(0.0, 1.0 - (value - hi) / max(1e-6, span * 0.5))


# (lo, hi, weight)  — weight reflects how discriminative this feature is
_PROFILES: dict[VehicleSubType, list[tuple[str, float, float, float]]] = {
    VehicleSubType.TRACTOR: [
        ("aspect_ratio",         0.8,  1.8,  2.0),
        ("edge_density",         0.07, 0.30, 1.5),  # complex tractor silhouette
        ("horiz_gradient_ratio", 0.0,  0.54, 1.0),  # NOT horizontally dominant
        ("top_half_edge_ratio",  1.05, 3.00, 1.5),  # cab structure in top half
        ("size_fraction",        0.01, 0.25, 0.5),
    ],
    VehicleSubType.TROLLEY: [
        ("aspect_ratio",         1.0,  3.5,  1.5),
        ("edge_density",         0.02, 0.18, 1.0),
        ("horiz_gradient_ratio", 0.50, 1.00, 1.5),  # horizontal rails/slats
        ("top_half_edge_ratio",  0.00, 1.10, 1.0),  # flat top profile
        ("size_fraction",        0.01, 0.35, 0.5),
    ],
    VehicleSubType.TRUCK_LARGE: [
        ("aspect_ratio",         2.5,  8.0,  2.0),
        ("size_fraction",        0.06, 1.00, 2.0),
        ("horiz_gradient_ratio", 0.55, 1.00, 1.5),
        ("top_half_edge_ratio",  0.00, 1.05, 1.0),
        ("edge_density",         0.02, 0.16, 0.5),
    ],
    VehicleSubType.TRUCK_MEDIUM: [
        ("aspect_ratio",         1.6,  3.8,  2.0),
        ("size_fraction",        0.03, 0.25, 1.5),
        ("horiz_gradient_ratio", 0.52, 1.00, 1.5),
        ("top_half_edge_ratio",  0.00, 1.10, 1.0),
        ("edge_density",         0.02, 0.16, 0.5),
    ],
    VehicleSubType.TRUCK_SMALL: [
        ("aspect_ratio",         1.0,  2.5,  2.0),
        ("size_fraction",        0.00, 0.12, 1.5),
        ("horiz_gradient_ratio", 0.48, 1.00, 1.0),
        ("top_half_edge_ratio",  0.00, 1.20, 1.0),
        ("edge_density",         0.03, 0.20, 0.5),
    ],
}

# Which sub-types are legal for each COCO class
_CLASS_ALLOWED: dict[int, list[VehicleSubType]] = {
    7: [VehicleSubType.TRUCK_LARGE, VehicleSubType.TRUCK_MEDIUM,
        VehicleSubType.TRUCK_SMALL, VehicleSubType.TRACTOR],
    5: [VehicleSubType.TROLLEY],
    2: [],   # non-primary (Car/Van)
    3: [],   # non-primary (Motorcycle)
}


def classify_subtype(
    image: np.ndarray,
    bbox: BoundingBox,
    coco_class_id: int,
    geometry_subtype: VehicleSubType,
) -> tuple[VehicleSubType, float, dict[str, float]]:
    """
    Classify vehicle sub-type using a 7-feature scoring matrix.

    Args:
        image           : full BGR frame
        bbox            : YOLO bounding box
        coco_class_id   : COCO class (2/3/5/7)
        geometry_subtype: sub-type from the fast geometry rules (Model B fallback)

    Returns:
        (sub_type, confidence, feature_dict)
    """
    allowed = _CLASS_ALLOWED.get(coco_class_id, [])
    if not allowed:
        # Non-primary class — geometry fallback, confidence 0
        return geometry_subtype, 0.0, {}

    img_h, img_w = image.shape[:2]
    features = _extract_features(image, bbox, img_h, img_w)

    if not features:
        return geometry_subtype, 0.3, {}

    # Score each allowed sub-type
    candidate_scores: dict[VehicleSubType, float] = {}
    for sub_type in allowed:
        profile = _PROFILES.get(sub_type, [])
        total_weight = sum(w for _, _, _, w in profile)
        weighted_score = sum(
            _range_score(features[feat], lo, hi) * w
            for feat, lo, hi, w in profile
            if feat in features
        )
        candidate_scores[sub_type] = weighted_score / max(1e-6, total_weight)

    # Winner
    winner = max(candidate_scores, key=lambda k: candidate_scores[k])
    best_score  = candidate_scores[winner]
    scores_list = sorted(candidate_scores.values(), reverse=True)
    second      = scores_list[1] if len(scores_list) > 1 else 0.0

    # Confidence: how much better than second place
    raw_conf = best_score * (1.0 - second / max(1e-6, best_score) * 0.5)
    confidence = round(min(0.95, max(0.10, raw_conf)), 4)

    logger.info(
        f"[subtype/D] class={coco_class_id} winner={winner.value} "
        f"conf={confidence:.3f} scores={{{', '.join(f'{k.value}: {v:.2f}' for k, v in candidate_scores.items())}}}"
    )

    return winner, confidence, {k: round(v, 3) for k, v in features.items()}
