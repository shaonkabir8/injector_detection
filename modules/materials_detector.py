"""
Model G — Material Classifier
===============================

Identifies what material is loaded in the vehicle's open-top cargo zone
using HSV colour-signature analysis.

When a cargo mask from Model E is available, only the masked (cargo) pixels
are analysed — this significantly reduces false signals from the empty bed
floor, cab side panel, or background bleeding into the bbox.

Supported materials (Bangladesh brick kiln context)
────────────────────────────────────────────────────
  Bricks    — Fired red/orange bricks (primary outbound cargo)
  Raw Clay  — Wet/dry clay for brick production (primary inbound cargo)
  Coal      — Dark fuel coal used in kiln furnaces
  Sand      — Yellow-tan construction sand
  Mixed     — Two materials at similar coverage
  Empty     — No material above coverage threshold
  Unknown   — Segmentation failed

HSV colour ranges (OpenCV: H 0–180, S 0–255, V 0–255)
────────────────────────────────────────────────────────
  Bricks    H=0–18 + H=165–180   S=80–255   V=60–210  (red-orange fired clay)
  Raw Clay  H=8–25               S=10–90    V=25–145   (brownish-grey wet/dry)
  Coal      V < 55 (any hue)                           (very dark black lumps)
  Sand      H=14–34              S=25–130   V=140–240  (yellow-tan dry sand)

Classification logic
─────────────────────
  max(all_scores) < MATERIAL_MIN_COVERAGE              → Empty
  top − second < MIXED_GAP and second ≥ MIN_COVERAGE   → Mixed
  else                                                  → top-scoring material
"""
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from schemas.detection import BoundingBox, MaterialDetectionResult, MaterialType
from config import settings

logger = logging.getLogger(__name__)

MATERIAL_MIN_COVERAGE: float = 0.07   # minimum fraction of cargo zone to count
MIXED_GAP_THRESHOLD:   float = 0.08   # top-second gap below which → Mixed


# ── Cargo zone extraction ──────────────────────────────────────────────────────

def _cargo_zone(image: np.ndarray, bbox: BoundingBox) -> Optional[np.ndarray]:
    img_h, img_w = image.shape[:2]
    x1 = max(0, bbox.x1);  x2 = min(img_w, bbox.x2)
    y1 = max(0, bbox.y1);  y2 = min(img_h, bbox.y2)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
        return None
    ch = crop.shape[0]
    zone_y1 = int(ch * settings.load_visual_skip_top)
    zone_y2 = int(ch * (1.0 - settings.load_visual_skip_bottom))
    zone = crop[zone_y1:zone_y2, :]
    return zone if zone.size > 0 and zone.shape[0] >= 5 else None


# ── HSV scoring ────────────────────────────────────────────────────────────────

def _coverage(mask: np.ndarray, total_px: int) -> float:
    return float(np.sum(mask > 0)) / max(1, total_px)


def _score_materials(
    hsv: np.ndarray,
    cargo_mask: Optional[np.ndarray] = None,
) -> dict[str, float]:
    """
    Compute per-material coverage ratio.
    If cargo_mask is provided (bool, same shape as zone), only masked pixels count.
    """
    if cargo_mask is not None and cargo_mask.shape == hsv.shape[:2]:
        total = int(cargo_mask.sum())
    else:
        cargo_mask = None
        total = hsv.shape[0] * hsv.shape[1]

    def _masked_coverage(mask2d: np.ndarray) -> float:
        if cargo_mask is not None:
            return float(np.sum(mask2d & cargo_mask)) / max(1, total)
        return _coverage(mask2d, total)

    # Bricks — red/orange (wraps around H=0)
    b1 = cv2.inRange(hsv, np.array([0,   80,  60]), np.array([18, 255, 210]))
    b2 = cv2.inRange(hsv, np.array([165, 80,  60]), np.array([180, 255, 210]))
    brick_mask = (b1 | b2).astype(bool)

    # Raw Clay — brownish, low saturation
    clay_mask = cv2.inRange(
        hsv, np.array([8, 10, 25]), np.array([25, 90, 145])
    ).astype(bool)

    # Coal — very dark pixels
    v_channel = hsv[:, :, 2]
    coal_mask = (v_channel < 55)

    # Sand — yellow-tan
    sand_mask = cv2.inRange(
        hsv, np.array([14, 25, 140]), np.array([34, 130, 240])
    ).astype(bool)

    return {
        "Bricks":   round(_masked_coverage(brick_mask), 4),
        "Raw Clay": round(_masked_coverage(clay_mask),  4),
        "Coal":     round(_masked_coverage(coal_mask),  4),
        "Sand":     round(_masked_coverage(sand_mask),  4),
    }


# ── Public API ─────────────────────────────────────────────────────────────────

_MATERIAL_MAP: dict[str, MaterialType] = {
    "Bricks":   MaterialType.BRICKS,
    "Raw Clay": MaterialType.RAW_CLAY,
    "Coal":     MaterialType.COAL,
    "Sand":     MaterialType.SAND,
}


def classify_material(
    image: np.ndarray,
    vehicle_bbox: BoundingBox,
    cargo_mask: Optional[np.ndarray] = None,
) -> MaterialDetectionResult:
    """
    Classify cargo material using HSV colour-signature analysis.

    Args:
        image        : Full BGR frame
        vehicle_bbox : Vehicle bounding box
        cargo_mask   : Optional bool ndarray from Model E (cargo-zone shape)

    Returns:
        MaterialDetectionResult
    """
    _unknown = MaterialDetectionResult(
        material_type=MaterialType.UNKNOWN,
        confidence=0.0, coverage_ratio=0.0,
        segmented=False, all_scores={},
    )

    zone = _cargo_zone(image, vehicle_bbox)
    if zone is None:
        logger.warning("[material/G] Could not extract cargo zone")
        return _unknown

    hsv = cv2.cvtColor(zone, cv2.COLOR_BGR2HSV)

    # Validate mask shape
    used_mask = cargo_mask is not None and cargo_mask.shape == zone.shape[:2]
    scores = _score_materials(hsv, cargo_mask if used_mask else None)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_name,  top_score  = sorted_scores[0]
    sec_name,  sec_score  = sorted_scores[1]

    logger.info(
        f"[material/G] scores={scores} mask={'yes' if used_mask else 'no'} "
        f"top={top_name}({top_score:.3f}) sec={sec_name}({sec_score:.3f})"
    )

    if top_score < MATERIAL_MIN_COVERAGE:
        return MaterialDetectionResult(
            material_type=MaterialType.EMPTY,
            confidence=round(max(0.5, 1.0 - top_score / max(1e-6, MATERIAL_MIN_COVERAGE)), 4),
            coverage_ratio=top_score,
            segmented=used_mask,
            all_scores=scores,
        )

    if (top_score - sec_score) < MIXED_GAP_THRESHOLD and sec_score >= MATERIAL_MIN_COVERAGE:
        return MaterialDetectionResult(
            material_type=MaterialType.MIXED,
            confidence=round((top_score + sec_score) / 2.0, 4),
            coverage_ratio=round(top_score + sec_score, 4),
            segmented=used_mask,
            all_scores=scores,
        )

    return MaterialDetectionResult(
        material_type=_MATERIAL_MAP.get(top_name, MaterialType.UNKNOWN),
        confidence=round(min(1.0, top_score * 3.0), 4),
        coverage_ratio=top_score,
        segmented=used_mask,
        all_scores=scores,
    )
