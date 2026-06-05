"""
Model I — Confidence / Review Gate
====================================

The final stage of the pipeline.  Aggregates confidence signals from all
upstream modules and issues one of three gate decisions:

  PASS    — Every module produced a confident result.
            The detection can be acted upon automatically.

  REVIEW  — One or more modules produced a borderline result.
            Flag for human review before granting/denying entry.

  REJECT  — The image is unreadable OR no primary vehicle was detected.
            Re-capture image or escalate.

Scoring
────────
Each module contributes a score (0–1) and may raise flags:

  Module A — image_quality  : blur_score (poor image → BLURRY flag)
  Module B/C — vehicle       : detection confidence (low → LOW_VEHICLE_CONF)
  Module D — subtype         : subtype_confidence (low → LOW_SUBTYPE_CONF)
  Module F — load            : load_confidence (low → LOW_LOAD_CONF)
  Module G — material        : material confidence (low → LOW_MATERIAL_CONF)
  Module H — plate           : OCR confidence (no text → NO_PLATE, low → LOW_PLATE_CONF)

overall_score = weighted mean of available module scores:
  image_quality  0.15
  vehicle        0.30
  subtype        0.20
  load           0.15
  material       0.10
  plate          0.10

Decision rules (applied in order):
  1. REJECT if image_quality == REJECT
  2. REJECT if no primary vehicle detected (vehicle is None)
  3. REJECT if overall_score < 0.25
  4. REVIEW if any "critical" flag: LOW_VEHICLE_CONF, NO_PLATE, BLURRY
  5. REVIEW if ≥ 2 "warning" flags
  6. PASS   otherwise
"""
from __future__ import annotations

import logging
from typing import Optional

from schemas.detection import (
    ConfidenceGateResult,
    GateDecision,
    ImageQuality,
    ImageQualityResult,
    LoadDetectionResult,
    MaterialDetectionResult,
    PlateDetection,
    VehicleDetection,
)

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
VEHICLE_CONF_WARN    = 0.45   # below this → LOW_VEHICLE_CONF flag
SUBTYPE_CONF_WARN    = 0.40   # below this → LOW_SUBTYPE_CONF flag
LOAD_CONF_WARN       = 0.38   # below this → LOW_LOAD_CONF flag
MATERIAL_CONF_WARN   = 0.35   # below this → LOW_MATERIAL_CONF flag
PLATE_CONF_WARN      = 0.38   # below this → LOW_PLATE_CONF flag

OVERALL_REJECT_THRESHOLD = 0.25

# Module weights for overall_score
WEIGHTS = {
    "image_quality": 0.15,
    "vehicle":       0.30,
    "subtype":       0.20,
    "load":          0.15,
    "material":      0.10,
    "plate":         0.10,
}

CRITICAL_FLAGS = {"LOW_VEHICLE_CONF", "NO_PLATE", "BLURRY", "IMAGE_QUALITY_FAILED"}


def _reason(decision: GateDecision, flags: list[str]) -> str:
    if decision == GateDecision.PASS:
        return "All modules confident — proceed automatically."
    if decision == GateDecision.REJECT:
        if "IMAGE_QUALITY_FAILED" in flags:
            return "Image quality too poor for reliable detection. Re-capture required."
        if "NO_VEHICLE" in flags:
            return "No brick kiln vehicle detected in the image."
        return "Detection quality too low. Re-capture or escalate."
    # REVIEW
    flag_str = ", ".join(flags)
    return f"Low confidence in: {flag_str}. Human review recommended."


def evaluate_gate(
    image_quality: Optional[ImageQualityResult],
    vehicle: Optional[VehicleDetection],
    load: Optional[LoadDetectionResult],
    material: Optional[MaterialDetectionResult],
    plate: Optional[PlateDetection],
) -> ConfidenceGateResult:
    """
    Aggregate all module outputs and return a gate decision.

    Args:
        image_quality : Model A output
        vehicle       : Model B/C/D combined output
        load          : Model F output
        material      : Model G output
        plate         : Model H output

    Returns:
        ConfidenceGateResult
    """
    flags: list[str] = []
    module_scores: dict[str, float] = {}

    # ── Model A: Image Quality ────────────────────────────────────────────────
    if image_quality is not None:
        module_scores["image_quality"] = image_quality.blur_score
        if image_quality.quality == ImageQuality.REJECT:
            flags.append("IMAGE_QUALITY_FAILED")
        elif "BLURRY" in image_quality.flags:
            flags.append("BLURRY")
    else:
        module_scores["image_quality"] = 0.5   # unknown

    # ── Model B/C/D: Vehicle ──────────────────────────────────────────────────
    if vehicle is None:
        flags.append("NO_VEHICLE")
        module_scores["vehicle"] = 0.0
        module_scores["subtype"] = 0.0
    else:
        module_scores["vehicle"] = vehicle.confidence
        module_scores["subtype"] = vehicle.subtype_confidence
        if vehicle.confidence < VEHICLE_CONF_WARN:
            flags.append("LOW_VEHICLE_CONF")
        if vehicle.subtype_confidence < SUBTYPE_CONF_WARN and vehicle.subtype_confidence > 0:
            flags.append("LOW_SUBTYPE_CONF")

    # ── Model F: Load ─────────────────────────────────────────────────────────
    if load is not None:
        module_scores["load"] = load.load_confidence
        if load.load_confidence < LOAD_CONF_WARN:
            flags.append("LOW_LOAD_CONF")
    else:
        module_scores["load"] = 0.0

    # ── Model G: Material ─────────────────────────────────────────────────────
    if material is not None:
        module_scores["material"] = material.confidence
        if material.confidence < MATERIAL_CONF_WARN:
            flags.append("LOW_MATERIAL_CONF")
    else:
        module_scores["material"] = 0.0

    # ── Model H: Plate ────────────────────────────────────────────────────────
    if plate is not None:
        if plate.plate_text == "":
            flags.append("NO_PLATE")
            module_scores["plate"] = 0.0
        else:
            module_scores["plate"] = plate.confidence
            if plate.confidence < PLATE_CONF_WARN:
                flags.append("LOW_PLATE_CONF")
    else:
        module_scores["plate"] = 0.0
        flags.append("NO_PLATE")

    # ── Overall score ─────────────────────────────────────────────────────────
    total_weight = sum(WEIGHTS[k] for k in module_scores)
    overall = sum(
        module_scores[k] * WEIGHTS[k]
        for k in module_scores
    ) / max(1e-6, total_weight)
    overall = round(overall, 4)

    # ── Decision ──────────────────────────────────────────────────────────────
    if "IMAGE_QUALITY_FAILED" in flags or "NO_VEHICLE" in flags:
        decision = GateDecision.REJECT
    elif overall < OVERALL_REJECT_THRESHOLD:
        decision = GateDecision.REJECT
    elif any(f in CRITICAL_FLAGS for f in flags):
        decision = GateDecision.REVIEW
    elif sum(1 for f in flags if f not in CRITICAL_FLAGS) >= 2:
        decision = GateDecision.REVIEW
    else:
        decision = GateDecision.PASS

    logger.info(
        f"[gate/I] decision={decision.value} overall={overall:.3f} flags={flags}"
    )

    return ConfidenceGateResult(
        decision=decision,
        overall_score=overall,
        module_scores={k: round(v, 4) for k, v in module_scores.items()},
        flags=flags,
        reason=_reason(decision, flags),
    )
