"""
Model F — Load Classifier
==========================

Determines how loaded a vehicle is: Empty / Partial / Full.

Primary method — Visual Texture Analysis
─────────────────────────────────────────
Analyses edge density, LAB colour variance, and blob count inside the cargo
zone.  When a cargo mask from Model E is available, only the masked pixels
are analysed (more accurate than the full cargo zone).

Three visual metrics combined into visual_score (0–1):
  edge_density   — Canny edges / total cargo pixels
  color_variance — mean std-dev of L*A*B* channels
  blob_count     — connected components in dilated edge map

Classification thresholds (config.py):
  visual_score < 0.05           → EMPTY   (0–5%)
  0.05 ≤ visual_score < 0.40   → PARTIAL (5–40%)
  visual_score ≥ 0.40          → FULL    (≥40%)

Secondary method — COCO Override
──────────────────────────────────
COCO object detection (from run_raw_yolo) provides a supplementary signal.
It can only UPGRADE the visual result, never downgrade it.
For brick kiln cargo (bricks, clay, coal) COCO will rarely fire —
the visual method is the primary signal for all industrial cargo.
"""
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from schemas.detection import (
    BoundingBox,
    LoadDetectionResult,
    LoadItem,
    LoadStatus,
    VehicleDetection,
)
from utils.image import intersection_over_smaller
from config import settings

logger = logging.getLogger(__name__)

VEHICLE_CLASS_IDS = {2, 3, 5, 7}
PERSON_CLASS_IDS  = {0, 1}

_CATEGORY_LABEL: dict[int, str] = {
    24: "container/bag", 26: "container/bag", 28: "container/bag",
    25: "sport/misc",    27: "sport/misc",    32: "sport/misc",
    39: "beverage/food", 40: "beverage/food", 41: "beverage/food",
    45: "beverage/food", 46: "beverage/food", 47: "beverage/food",
    48: "beverage/food", 49: "beverage/food", 50: "beverage/food",
    56: "furniture",     57: "furniture",     58: "furniture",
    62: "equipment",     63: "equipment",     64: "equipment",
    65: "equipment",     66: "equipment",     67: "equipment",
    76: "equipment",     77: "equipment",     78: "equipment",
}
_EXCLUDED_IDS = VEHICLE_CLASS_IDS | PERSON_CLASS_IDS


# ── Visual Analysis ────────────────────────────────────────────────────────────

def _analyze_cargo_visuals(
    image: np.ndarray,
    vehicle_bbox: BoundingBox,
    cargo_mask: Optional[np.ndarray] = None,
) -> tuple[float, float, int, float, bool]:
    """
    Analyse visual complexity of the cargo zone.

    If cargo_mask (bool ndarray, same shape as cargo zone) is provided,
    analysis runs only on masked pixels (Model E output).

    Returns:
        (edge_density, color_variance, blob_count, visual_score, used_mask)
    """
    img_h, img_w = image.shape[:2]
    x1 = max(0, vehicle_bbox.x1);  x2 = min(img_w, vehicle_bbox.x2)
    y1 = max(0, vehicle_bbox.y1);  y2 = min(img_h, vehicle_bbox.y2)

    crop = image[y1:y2, x1:x2]
    if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
        return 0.0, 0.0, 0, 0.0, False

    ch, cw = crop.shape[:2]
    zone_y1 = int(ch * settings.load_visual_skip_top)
    zone_y2 = int(ch * (1.0 - settings.load_visual_skip_bottom))
    zone = crop[zone_y1:zone_y2, :]

    if zone.size == 0 or zone.shape[0] < 5:
        return 0.0, 0.0, 0, 0.0, False

    used_mask = False

    # Apply cargo mask from Model E if shape matches
    if cargo_mask is not None and cargo_mask.shape == zone.shape[:2]:
        mask3 = np.stack([cargo_mask] * 3, axis=-1)
        zone = np.where(mask3, zone, np.zeros_like(zone))
        valid_pixels = int(cargo_mask.sum())
        used_mask = True
    else:
        valid_pixels = zone.shape[0] * zone.shape[1]

    if valid_pixels < 50:
        return 0.0, 0.0, 0, 0.0, used_mask

    # ── Edge density ──────────────────────────────────────────────────────────
    gray    = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges   = cv2.Canny(blurred, 40, 120)
    edge_density = float(np.sum(edges > 0)) / max(1, valid_pixels)

    # ── Colour variance (L*A*B*) ──────────────────────────────────────────────
    lab = cv2.cvtColor(zone, cv2.COLOR_BGR2LAB)
    if used_mask:
        lab_pixels = lab[cargo_mask]
    else:
        lab_pixels = lab.reshape(-1, 3)
    color_variance = float(np.std(lab_pixels, axis=0).mean()) if len(lab_pixels) > 0 else 0.0

    # ── Blob count ────────────────────────────────────────────────────────────
    kernel  = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    num_labels, _labels, stats, _ = cv2.connectedComponentsWithStats(dilated)
    min_blob_px = max(80, valid_pixels // 300)
    blob_count  = sum(
        1 for i in range(1, num_labels)
        if stats[i, cv2.CC_STAT_AREA] > min_blob_px
    )

    # ── Composite visual_score ────────────────────────────────────────────────
    edge_comp  = min(1.0, edge_density   / max(1e-6, settings.load_visual_edge_max))
    color_comp = min(1.0, color_variance / max(1e-6, settings.load_visual_color_max))
    blob_comp  = min(1.0, blob_count     / max(1e-6, settings.load_visual_blob_max))

    visual_score = round(min(1.0,
        settings.load_visual_edge_weight  * edge_comp
        + settings.load_visual_color_weight * color_comp
        + settings.load_visual_blob_weight  * blob_comp
    ), 4)

    return round(edge_density, 4), round(color_variance, 2), blob_count, visual_score, used_mask


def _visual_to_status(visual_score: float) -> tuple[LoadStatus, bool, float]:
    """Map visual_score to LoadStatus + confidence."""
    if visual_score < settings.load_visual_empty_threshold:
        return LoadStatus.EMPTY, False, round(max(0.5, 1.0 - visual_score * 8), 4)
    if visual_score >= settings.load_visual_full_threshold:
        conf = round(0.5 + visual_score * 0.5, 4)
        return LoadStatus.FULL, True, min(1.0, conf)
    span = settings.load_visual_full_threshold - settings.load_visual_empty_threshold
    pos  = (visual_score - settings.load_visual_empty_threshold) / max(1e-6, span)
    conf = round(0.35 + pos * 0.45, 4)
    return LoadStatus.PARTIAL, True, min(1.0, conf)


# ── COCO override ──────────────────────────────────────────────────────────────

def _coco_items_and_coverage(
    raw_detections: list[dict],
    vehicle_box: list[int],
    vehicle_area: int,
) -> tuple[list[LoadItem], float]:
    load_items: list[LoadItem] = []
    covered_px = 0
    for det in raw_detections:
        cls_id = det["class_id"]
        conf   = det["confidence"]
        if cls_id in _EXCLUDED_IDS or conf < settings.load_min_item_confidence:
            continue
        det_box = det["bbox"]
        if intersection_over_smaller(vehicle_box, det_box) < settings.load_iou_threshold:
            continue
        x1, y1, x2, y2 = det_box
        ix1 = max(vehicle_box[0], x1);  iy1 = max(vehicle_box[1], y1)
        ix2 = min(vehicle_box[2], x2);  iy2 = min(vehicle_box[3], y2)
        covered_px += max(0, (ix2 - ix1) * (iy2 - iy1))
        category = _CATEGORY_LABEL.get(cls_id, "cargo")
        load_items.append(LoadItem(
            label=det["label"], category=category, confidence=round(conf, 4),
            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
        ))
    load_items.sort(key=lambda i: i.confidence, reverse=True)
    coco_coverage = round(min(1.0, covered_px / max(1, vehicle_area)), 4)
    return load_items, coco_coverage


def _coco_to_status(load_items: list[LoadItem], coco_coverage: float) -> Optional[tuple[LoadStatus, float]]:
    if not load_items or coco_coverage < 0.01:
        return None
    if coco_coverage >= 0.40 or len(load_items) >= 5:
        return LoadStatus.FULL, round(min(1.0, 0.5 + coco_coverage * 0.5), 4)
    return LoadStatus.PARTIAL, round(min(1.0, 0.30 + coco_coverage * 0.70), 4)


# ── Public API ─────────────────────────────────────────────────────────────────

_STATUS_RANK = {LoadStatus.EMPTY: 0, LoadStatus.PARTIAL: 1, LoadStatus.FULL: 2, LoadStatus.UNKNOWN: -1}


def detect_load(
    raw_detections: list[dict],
    primary_vehicle: Optional[VehicleDetection],
    model_available: bool,
    image: Optional[np.ndarray] = None,
    cargo_mask: Optional[np.ndarray] = None,
) -> LoadDetectionResult:
    """
    Compute load status using visual texture + COCO override.

    Args:
        raw_detections  : All detections from run_raw_yolo()
        primary_vehicle : Best vehicle detection (may be None)
        model_available : Whether YOLO model is loaded
        image           : BGR ndarray (required for visual analysis)
        cargo_mask      : Optional bool mask from Model E (improves accuracy)
    """
    _unknown = LoadDetectionResult(
        load_status=LoadStatus.UNKNOWN,
        is_loaded=False, load_confidence=0.0, coverage_ratio=0.0,
        segmented=False, load_items=[], item_count=0,
    )
    if not model_available or primary_vehicle is None or primary_vehicle.bbox is None:
        return _unknown

    v = primary_vehicle.bbox
    vehicle_box = [v.x1, v.y1, v.x2, v.y2]
    vehicle_area = max(1, v.width * v.height)

    # ── Signal 1: Visual texture (Model F primary) ────────────────────────────
    visual_status, vis_loaded, visual_confidence = LoadStatus.EMPTY, False, 0.5
    visual_score  = 0.0
    used_mask     = False

    if image is not None:
        edge_density, color_variance, blob_count, visual_score, used_mask = \
            _analyze_cargo_visuals(image, v, cargo_mask)
        visual_status, vis_loaded, visual_confidence = _visual_to_status(visual_score)
        logger.info(
            f"[load/F] score={visual_score:.3f} → {visual_status.value} "
            f"(edge={edge_density:.3f} color={color_variance:.1f} blobs={blob_count} "
            f"mask={'yes' if used_mask else 'no'})"
        )
    else:
        logger.warning("[load/F] No image provided — visual analysis skipped")

    # ── Signal 2: COCO override ───────────────────────────────────────────────
    load_items, coco_coverage = _coco_items_and_coverage(raw_detections, vehicle_box, vehicle_area)
    coco_result = _coco_to_status(load_items, coco_coverage)

    # ── Fusion: max of both signals ───────────────────────────────────────────
    if coco_result is not None:
        coco_status, coco_confidence = coco_result
        if _STATUS_RANK[coco_status] > _STATUS_RANK[visual_status]:
            logger.info(
                f"[load/F] COCO upgrade: {visual_status.value} → {coco_status.value} "
                f"(items={len(load_items)} coverage={coco_coverage:.2%})"
            )
            final_status     = coco_status
            final_confidence = round(max(visual_confidence, coco_confidence), 4)
        else:
            final_status     = visual_status
            final_confidence = visual_confidence
    else:
        final_status     = visual_status
        final_confidence = visual_confidence

    coverage_ratio = round(max(visual_score, coco_coverage), 4)
    is_loaded      = final_status in (LoadStatus.PARTIAL, LoadStatus.FULL)

    # ── AI Capacity Estimation Engine (3-Camera Simulated logic) ──
    # height_score proxy = visual_score (side camera proxy)
    # area_score proxy = coco_coverage (top camera proxy)
    volume_score = (visual_score * 0.6) + (coco_coverage * 0.4)
    
    # max_volume proxy ~ 0.8 for a full load
    capacity = int((volume_score / 0.8) * 100)
    actual_percent = min(120, capacity) # Cap at 120%
    expected_percent = 100 # Assuming full load is expected by default, overridden by API

    logger.info(
        f"[load/F] FINAL status={final_status.value} coverage={coverage_ratio:.2%} "
        f"conf={final_confidence:.2f} coco_items={len(load_items)} volume={volume_score:.2f} actual_pct={actual_percent}%"
    )

    return LoadDetectionResult(
        load_status=final_status,
        is_loaded=is_loaded,
        load_confidence=final_confidence,
        coverage_ratio=coverage_ratio,
        actual_percent=actual_percent,
        expected_percent=expected_percent,
        segmented=used_mask,
        load_items=load_items,
        item_count=len(load_items),
    )
