"""
Model B — YOLO Vehicle Detector
Model C — Second Detector (TTA Fusion)
Model D — Vehicle Subtype Classifier

Pipeline
────────
  Stage 1 (Model B): YOLOv8n fast pass — detect vehicle bounding boxes.
      Only 4 COCO classes kept: 2 (Car/Van), 3 (Motorcycle), 5 (Bus/Trolley), 7 (Truck/Tractor)
      Non-primary sub-types (Car, Van, Bus, Motorcycle) are discarded.

  Stage 2 (Model C): Fusion via TTA (Test-Time Augmentation).
      Triggered only when Model B best confidence < FUSION_THRESHOLD (0.55).
      Calls YOLOv8n with augment=True (multi-scale + flip internally).
      If augmented pass yields higher max confidence, its detections replace Model B.

  Stage 3 (Model D): Subtype Classifier.
      For each vehicle crop, extracts 7 discriminative features and scores
      against known brick-kiln sub-type profiles.
      Replaces the pure geometry sub-type with a more robust classification.

Returns
────────
  (best_vehicle, all_primary_vehicles, model_available)
  Only PRIMARY vehicles (Trolley, Tractor, Truck-*) are returned.
  Non-primary detections are discarded and logged at DEBUG level.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from schemas.detection import (
    BoundingBox,
    PRIMARY_SUBTYPES,
    VehicleDetection,
    VehicleSubType,
)
from modules.subtype_classifier import classify_subtype
from config import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VEHICLE_CLASS_MAP: dict[int, str] = {
    2: "Car/Van",
    3: "Motorcycle",
    5: "Bus/Trolley",
    7: "Truck/Tractor",
}
VEHICLE_CLASS_IDS = set(VEHICLE_CLASS_MAP.keys())

# Geometry fallback sub-type (used before Model D overrides it)
# Class 5 at a brick kiln → almost always Trolley
_GEOMETRY_CLASS5_DEFAULT = VehicleSubType.TROLLEY

# Model C activation threshold: if best confidence < this, run TTA pass
FUSION_THRESHOLD: float = 0.55

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

_model_instance: Optional[object] = None


# ── Model loading ─────────────────────────────────────────────────────────────

def _get_model():
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    try:
        from ultralytics import YOLO
        candidates = [
            MODEL_DIR / settings.yolo_model,
            Path(__file__).parent.parent / settings.yolo_model,
            settings.yolo_model,
        ]
        path = next(
            (str(p) for p in candidates if isinstance(p, Path) and p.exists()),
            settings.yolo_model,
        )
        logger.info(f"[vehicle/B] Loading model: {path}")
        _model_instance = YOLO(path)
        logger.info("[vehicle/B] Model ready")
    except Exception as exc:
        logger.error(f"[vehicle/B] Model load failed: {exc}")
        _model_instance = None
    return _model_instance


# ── Geometry fallback sub-type (fast, no crop analysis) ───────────────────────

def _geometry_subtype(cls_id: int, aspect: float, size_frac: float, height_frac: float) -> VehicleSubType:
    """
    Fast geometry-only sub-type used as a fallback before Model D runs,
    and for non-primary classes.
    """
    if cls_id == 7:
        if aspect <= 1.6:
            return VehicleSubType.TRACTOR
        if aspect >= 3.5 or size_frac >= 0.28:
            return VehicleSubType.TRUCK_LARGE
        if height_frac >= 0.40 and size_frac >= 0.08:
            return VehicleSubType.TRUCK_LARGE
        if aspect >= 2.2 or size_frac >= 0.10:
            return VehicleSubType.TRUCK_MEDIUM
        return VehicleSubType.TRUCK_SMALL
    if cls_id == 5:
        return VehicleSubType.TROLLEY if aspect <= 3.0 else VehicleSubType.BUS
    if cls_id == 2:
        return VehicleSubType.VAN if aspect >= 1.9 else VehicleSubType.CAR
    if cls_id == 3:
        return VehicleSubType.MOTORCYCLE
    return VehicleSubType.UNKNOWN


# ── YOLO inference helper ─────────────────────────────────────────────────────

def _run_yolo(model, image: np.ndarray, augment: bool = False):
    """Run YOLO and return the raw results[0] object."""
    return model(
        image,
        verbose=False,
        conf=settings.yolo_confidence,
        iou=settings.yolo_iou,
        augment=augment,
    )[0]


def _max_conf(results) -> float:
    if results.boxes is None or len(results.boxes) == 0:
        return 0.0
    return max(float(b.conf[0]) for b in results.boxes)


# ── Main detection function ───────────────────────────────────────────────────

def detect_vehicles(
    image: np.ndarray,
) -> tuple[Optional[VehicleDetection], list[VehicleDetection], bool]:
    """
    Run Model B → Model C (conditional) → Model D for each detection.

    Returns:
        (best_primary_vehicle, all_primary_vehicles, model_available)
    """
    model = _get_model()
    if model is None:
        return None, [], False

    img_h, img_w = image.shape[:2]

    # ── Model B: fast YOLO pass ───────────────────────────────────────────────
    try:
        results = _run_yolo(model, image, augment=False)
    except Exception as exc:
        logger.error(f"[vehicle/B] Inference error: {exc}")
        return None, [], True

    fusion_used = False

    # ── Model C: TTA fusion on low-confidence detections ─────────────────────
    if _max_conf(results) < FUSION_THRESHOLD:
        try:
            aug_results = _run_yolo(model, image, augment=True)
            if _max_conf(aug_results) > _max_conf(results):
                logger.info(
                    f"[vehicle/C] TTA improved confidence: "
                    f"{_max_conf(results):.2f} → {_max_conf(aug_results):.2f}"
                )
                results = aug_results
                fusion_used = True
            else:
                logger.info("[vehicle/C] TTA did not improve — keeping Model B results")
        except Exception as exc:
            logger.warning(f"[vehicle/C] TTA failed: {exc}")

    # ── Build detection objects + Model D subtype classification ─────────────
    all_detections: list[VehicleDetection] = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        if cls_id not in VEHICLE_CLASS_IDS:
            continue

        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        bw = x2 - x1
        bh = y2 - y1

        aspect      = round(bw / bh, 3) if bh > 0 else 0.0
        size_frac   = round((bw * bh) / max(1, img_w * img_h), 4)
        height_frac = round(bh / max(1, img_h), 3)

        # Geometry fallback sub-type
        geo_sub = _geometry_subtype(cls_id, aspect, size_frac, height_frac)

        # Model D: feature-based subtype refinement (primary classes only)
        bbox = BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
        if geo_sub in PRIMARY_SUBTYPES or cls_id == 7 or cls_id == 5:
            sub_type, subtype_conf, feat_dict = classify_subtype(
                image, bbox, cls_id, geo_sub
            )
        else:
            sub_type, subtype_conf, feat_dict = geo_sub, 0.0, {}

        is_primary = sub_type in PRIMARY_SUBTYPES

        all_detections.append(
            VehicleDetection(
                vehicle_type=VEHICLE_CLASS_MAP[cls_id],
                vehicle_sub_type=sub_type,
                is_primary_vehicle=is_primary,
                confidence=round(conf, 4),
                fusion_used=fusion_used,
                subtype_confidence=subtype_conf,
                subtype_features=feat_dict,
                bbox=bbox,
                class_id=cls_id,
                aspect_ratio=aspect,
                size_fraction=size_frac,
            )
        )

    all_detections.sort(key=lambda d: d.confidence, reverse=True)

    # Only primary vehicles are surfaced
    primary = [d for d in all_detections if d.is_primary_vehicle]
    non_primary = [d for d in all_detections if not d.is_primary_vehicle]

    for d in non_primary:
        logger.debug(
            f"[vehicle] Non-kiln discarded: {d.vehicle_sub_type.value} "
            f"(conf={d.confidence:.2f})"
        )

    best = primary[0] if primary else None

    if best:
        logger.info(
            f"[vehicle] Best: {best.vehicle_sub_type.value} "
            f"det_conf={best.confidence:.2f} "
            f"sub_conf={best.subtype_confidence:.2f} "
            f"fusion={best.fusion_used}"
        )
    else:
        logger.info(
            f"[vehicle] No primary vehicle detected "
            f"(total_hits={len(all_detections)} fusion_used={fusion_used})"
        )

    return best, primary, True


# ── Raw YOLO (used by load and plate modules) ─────────────────────────────────

def run_raw_yolo(image: np.ndarray) -> tuple[list[dict], bool]:
    """Return all YOLO detections (all classes) as raw dicts."""
    model = _get_model()
    if model is None:
        return [], False
    try:
        results = model(
            image,
            verbose=False,
            conf=max(settings.yolo_confidence * 0.5, 0.10),
            iou=settings.yolo_iou,
        )[0]
    except Exception as exc:
        logger.error(f"[vehicle/raw] Inference error: {exc}")
        return [], True

    names: dict[int, str] = results.names
    return [
        {
            "class_id": int(box.cls[0]),
            "label":    names.get(int(box.cls[0]), str(int(box.cls[0]))),
            "confidence": round(float(box.conf[0]), 4),
            "bbox":     list(map(int, box.xyxy[0])),
        }
        for box in results.boxes
    ], True
