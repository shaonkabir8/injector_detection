"""
Detection router — 9-model pipeline, multi-vehicle aware.

Every primary vehicle detected in the image gets its own independent run of:
  Model E (cargo segmenter)
  Model F (load classifier on that vehicle's cargo mask)
  Model G (material classifier on that vehicle's cargo mask)
  Model H (plate OCR restricted to that vehicle's bbox region)
  Model I (confidence gate for that vehicle)

This means a single photo with 3 trucks returns 3 complete VehicleResult
objects, each with independent load/material/plate/gate fields.

Endpoints
─────────
  POST /detect/vehicle    → Models A + B/C + D
  POST /detect/load       → Models E + F  (best vehicle only)
  POST /detect/material   → Models E + G  (best vehicle only)
  POST /detect/plate      → Model H  (full image)
  POST /detect/full       → All 9 models, all vehicles
  POST /detect/validate   → All 9 models + Module 4 registry, all vehicles

  GET  /detect/registry
  POST /detect/registry/reload
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from config import settings
from modules.cache              import cache
from modules.quality_checker    import check_image_quality
from modules.vehicle_detector   import detect_vehicles, run_raw_yolo
from modules.cargo_segmenter    import segment_cargo
from modules.load_detector      import detect_load
from modules.materials_detector import classify_material
from modules.plate_detector     import detect_plate, detect_plate_for_vehicle
from modules.vehicle_validator  import validate_vehicle, reload_registry, _load_registry
from modules.confidence_gate    import evaluate_gate
from schemas.detection import (
    FullDetectionResponse,
    ImageQualityResult,
    VehicleDetection,
    VehicleOnlyResponse,
    VehicleResult,
    LoadOnlyResponse,
    MaterialOnlyResponse,
    PlateOnlyResponse,
    VehicleValidationResponse,
)
from utils.image import decode_upload, resize_for_inference

import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter(tags=["detection"])


# ── Image helper ───────────────────────────────────────────────────────────────

def _read_image(data: bytes) -> np.ndarray:
    if len(data) > settings.max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.max_image_bytes // (1024 * 1024)} MB limit",
        )
    try:
        image = decode_upload(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return resize_for_inference(image, max_side=1280)


# ── Per-vehicle pipeline (Models E → F → G → H → I) ──────────────────────────

def _process_vehicle(
    image: np.ndarray,
    vehicle: VehicleDetection,
    raw_detections: list[dict],
    model_available: bool,
    image_quality: ImageQualityResult,
    include_validation: bool = False,
    expected_plate: Optional[str] = None,
) -> VehicleResult:
    """
    Run Models E, F, G, H, I independently for a single vehicle.

    Args:
        image             : Full BGR frame
        vehicle           : VehicleDetection from Models B/C/D
        raw_detections    : run_raw_yolo() output (all classes)
        model_available   : Whether YOLO is loaded
        image_quality     : Model A result (used by gate)
        include_validation: If True, also run Module 4 fleet validation
        expected_plate    : Override OCR plate for registry lookup

    Returns:
        VehicleResult with all per-vehicle fields populated
    """
    # Model E — cargo segmenter
    cargo_mask, cargo_seg = None, None
    if vehicle.bbox is not None:
        cargo_mask, cargo_seg = segment_cargo(image, vehicle.bbox)

    # Model F — load classifier (uses Model E mask)
    load_result = detect_load(
        raw_detections, vehicle, model_available,
        image=image,
        cargo_mask=cargo_mask,
    )

    # Model G — material classifier (uses Model E mask)
    material_result = None
    if vehicle.bbox is not None:
        material_result = classify_material(image, vehicle.bbox, cargo_mask)

    # Model H — plate detector restricted to this vehicle's region
    if vehicle.bbox is not None:
        plate_result = detect_plate_for_vehicle(image, vehicle.bbox)
    else:
        plate_result = detect_plate(image)

    # Module 4 — fleet registry validation (optional)
    validation = None
    if include_validation:
        validation = validate_vehicle(
            detected_vehicle=vehicle,
            detected_plate=plate_result,
            expected_plate=expected_plate,
        )

    # Model I — confidence gate for this vehicle
    gate = evaluate_gate(image_quality, vehicle, load_result, material_result, plate_result)

    logger.info(
        f"[pipeline] bbox=[{vehicle.bbox.x1},{vehicle.bbox.y1}→"
        f"{vehicle.bbox.x2},{vehicle.bbox.y2}] "
        f"sub={vehicle.vehicle_sub_type.value} "
        f"load={load_result.load_status.value} "
        f"material={material_result.material_type.value if material_result else 'none'} "
        f"plate='{plate_result.plate_text}' "
        f"gate={gate.decision.value}"
    )

    return VehicleResult(
        vehicle=vehicle,
        cargo_segmentation=cargo_seg,
        load=load_result,
        material=material_result,
        plate=plate_result,
        validation=validation,
        gate=gate,
    )


# ── Module 1 — Vehicle Detector ───────────────────────────────────────────────

@router.post(
    "/vehicle",
    response_model=VehicleOnlyResponse,
    summary="Model A + B/C + D — Vehicle Detector",
    description=(
        "**Model A** — Image quality check\n\n"
        "**Model B** — YOLOv8n fast detection pass\n\n"
        "**Model C** — TTA fusion (auto-triggered when B confidence < 0.55)\n\n"
        "**Model D** — 7-feature subtype classifier on each vehicle crop\n\n"
        "Returns ALL primary vehicles found in the image.\n"
        "`total_vehicles` = count of primary kiln vehicles detected."
    ),
)
async def detect_vehicle_only(file: UploadFile = File(...)) -> VehicleOnlyResponse:
    data = await file.read()
    image = _read_image(data)
    quality = check_image_quality(image)
    best_vehicle, all_vehicles, model_available = detect_vehicles(image)
    return VehicleOnlyResponse(
        success=True,
        model_available=model_available,
        image_quality=quality,
        vehicle=best_vehicle,
        all_vehicles=all_vehicles,
        total_vehicles=len(all_vehicles),
    )


# ── Module 2 — Load Detector ──────────────────────────────────────────────────

@router.post(
    "/load",
    response_model=LoadOnlyResponse,
    summary="Model E + F — Cargo Segmenter + Load Classifier",
    description=(
        "Runs on the highest-confidence primary vehicle in the frame.\n\n"
        "**Model E** — K-means + edge cargo segmentation\n\n"
        "**Model F** — Texture analysis on segmented cargo mask\n\n"
        "| Status | visual_score |\n"
        "|---|---|\n"
        "| Empty | < 5% |\n"
        "| Partial | 5% – 40% |\n"
        "| Full | ≥ 40% |"
    ),
)
async def detect_load_only(file: UploadFile = File(...)) -> LoadOnlyResponse:
    data = await file.read()
    image = _read_image(data)
    best_vehicle, _, model_available = detect_vehicles(image)
    raw_detections, _ = run_raw_yolo(image) if model_available else ([], False)

    cargo_mask, cargo_seg = None, None
    if best_vehicle and best_vehicle.bbox:
        cargo_mask, cargo_seg = segment_cargo(image, best_vehicle.bbox)

    load_result = detect_load(
        raw_detections, best_vehicle, model_available,
        image=image, cargo_mask=cargo_mask,
    )
    return LoadOnlyResponse(
        success=True,
        model_available=model_available,
        cargo_segmentation=cargo_seg,
        load=load_result,
    )


# ── Module 3 — Materials Detector ─────────────────────────────────────────────

@router.post(
    "/material",
    response_model=MaterialOnlyResponse,
    summary="Model E + G — Cargo Segmenter + Material Classifier",
    description=(
        "Runs on the highest-confidence primary vehicle in the frame.\n\n"
        "**Model E** — binary cargo mask\n\n"
        "**Model G** — HSV colour-signature on masked cargo pixels\n\n"
        "| Material | Signal |\n"
        "|---|---|\n"
        "| Bricks | Red-orange H=0–18° |\n"
        "| Raw Clay | Brownish-grey, low S |\n"
        "| Coal | Very dark V<55 |\n"
        "| Sand | Yellow-tan H=14–34° |"
    ),
)
async def detect_material_only(file: UploadFile = File(...)) -> MaterialOnlyResponse:
    data = await file.read()
    image = _read_image(data)
    best_vehicle, _, model_available = detect_vehicles(image)

    cargo_mask, cargo_seg = None, None
    material_result = None
    if best_vehicle and best_vehicle.bbox:
        cargo_mask, cargo_seg = segment_cargo(image, best_vehicle.bbox)
        material_result = classify_material(image, best_vehicle.bbox, cargo_mask)

    return MaterialOnlyResponse(
        success=True,
        model_available=model_available,
        cargo_segmentation=cargo_seg,
        material=material_result,
    )


# ── Module 5 — OCR Detector ───────────────────────────────────────────────────

@router.post(
    "/plate",
    response_model=PlateOnlyResponse,
    summary="Model H — Plate Detector + OCR (full image)",
    description=(
        "Runs plate detection on the entire image.\n\n"
        "For per-vehicle plate detection in multi-vehicle scenes, "
        "use `/detect/full` which calls `detect_plate_for_vehicle()` per vehicle.\n\n"
        "Bangladesh plate format: `DISTRICT-SERIES-CLASS-NUMBER`"
    ),
)
async def detect_plate_only(file: UploadFile = File(...)) -> PlateOnlyResponse:
    data = await file.read()
    image = _read_image(data)
    return PlateOnlyResponse(success=True, plate=detect_plate(image))


# ── Full Pipeline — All 9 Models, All Vehicles ────────────────────────────────

@router.post(
    "/full",
    response_model=FullDetectionResponse,
    summary="Full 9-model pipeline — all vehicles (cache-aware)",
    description=(
        "Runs all 9 models on every primary vehicle found in the image.\n\n"
        "Results are cached in Redis by image MD5 hash (15 min TTL). "
        "Identical images return instantly from cache without re-running the pipeline.\n\n"
        "| Model | Role |\n"
        "|---|---|\n"
        "| A | Image Quality Checker (once per image) |\n"
        "| B | YOLO Vehicle Detector |\n"
        "| C | TTA Fusion (auto, when B confidence < 0.55) |\n"
        "| D | Vehicle Subtype Classifier (per vehicle) |\n"
        "| E | Cargo Area Segmenter (per vehicle) |\n"
        "| F | Load Classifier on cargo mask (per vehicle) |\n"
        "| G | Material Classifier on cargo mask (per vehicle) |\n"
        "| H | Plate OCR restricted to vehicle bbox (per vehicle) |\n"
        "| I | Confidence Gate (per vehicle) |\n\n"
        "`vehicles` array contains one full result per primary vehicle.\n"
        "Top-level fields mirror `vehicles[0]` for backward compatibility."
    ),
)
async def detect_full(file: UploadFile = File(...)) -> FullDetectionResponse:
    data = await file.read()

    # ── Cache check ────────────────────────────────────────────────────────────
    cached = cache.get_result("full", data)
    if cached:
        logger.info("[full] Cache hit — returning cached result")
        return FullDetectionResponse(**cached)

    image = _read_image(data)

    # Model A — once per image
    quality = check_image_quality(image)

    # Models B + C + D — detect ALL primary vehicles
    _, all_vehicles, model_available = detect_vehicles(image)
    raw_detections, _ = run_raw_yolo(image) if model_available else ([], False)

    if not all_vehicles:
        logger.info("[full] No primary vehicles detected")
        result = FullDetectionResponse(
            success=True,
            model_available=model_available,
            image_quality=quality,
            vehicles=[],
            total_vehicles=0,
        )
        cache.set_result("full", data, result.model_dump())
        cache.record_detection()
        return result

    # Models E → F → G → H → I per vehicle
    vehicle_results: list[VehicleResult] = []
    for v in all_vehicles:
        vr = _process_vehicle(
            image, v, raw_detections, model_available, quality,
            include_validation=False,
        )
        vehicle_results.append(vr)

    logger.info(
        f"[full] {len(vehicle_results)} primary vehicle(s) processed "
        f"quality={quality.quality.value}"
    )

    # Top-level fields = first (highest confidence) vehicle
    first = vehicle_results[0]
    result = FullDetectionResponse(
        success=True,
        model_available=model_available,
        image_quality=quality,
        vehicles=vehicle_results,
        total_vehicles=len(vehicle_results),
        vehicle=first.vehicle,
        cargo_segmentation=first.cargo_segmentation,
        load=first.load,
        material=first.material,
        plate=first.plate,
        gate=first.gate,
    )
    cache.set_result("full", data, result.model_dump())
    cache.record_detection()
    return result


# ── Module 4 — Match Details Detector + Full Pipeline ─────────────────────────

@router.post(
    "/validate",
    response_model=VehicleValidationResponse,
    summary="Full pipeline + Module 4 fleet validation — all vehicles",
    description=(
        "Runs all 9 models on every primary vehicle, then validates each "
        "vehicle's plate against the fleet registry.\n\n"
        "`vehicles[N].validation` contains the registry result for vehicle N.\n\n"
        "`vehicles[N].gate.decision` gives the final PASS/REVIEW/REJECT verdict "
        "for that specific vehicle.\n\n"
        "Pass `expected_plate` to override OCR for all vehicles in this image "
        "(useful when a pre-booked plate is known in advance)."
    ),
)
async def detect_and_validate(
    file: UploadFile = File(...),
    expected_plate: Optional[str] = Form(
        None,
        description="Pre-known plate — overrides OCR for registry lookup on all vehicles",
    ),
) -> VehicleValidationResponse:
    data = await file.read()

    # ── Cache check ────────────────────────────────────────────────────────────
    cache_key = f"validate:{expected_plate or ''}"
    cached = cache.get_result(cache_key, data)
    if cached:
        logger.info("[validate] Cache HIT — returning cached result")
        return VehicleValidationResponse(**cached)

    image = _read_image(data)

    quality = check_image_quality(image)
    _, all_vehicles, model_available = detect_vehicles(image)
    raw_detections, _ = run_raw_yolo(image) if model_available else ([], False)

    if not all_vehicles:
        result = VehicleValidationResponse(
            success=True,
            model_available=model_available,
            image_quality=quality,
            vehicles=[],
            total_vehicles=0,
        )
        cache.set_result(cache_key, data, result.model_dump())
        cache.record_detection()
        return result

    vehicle_results: list[VehicleResult] = []
    for v in all_vehicles:
        vr = _process_vehicle(
            image, v, raw_detections, model_available, quality,
            include_validation=True,
            expected_plate=expected_plate,
        )
        vehicle_results.append(vr)

    logger.info(
        f"[validate] {len(vehicle_results)} vehicle(s) — "
        f"authorized: {sum(1 for vr in vehicle_results if vr.validation and vr.validation.authorized)}"
    )

    first = vehicle_results[0]
    result = VehicleValidationResponse(
        success=True,
        model_available=model_available,
        image_quality=quality,
        vehicles=vehicle_results,
        total_vehicles=len(vehicle_results),
        vehicle=first.vehicle,
        cargo_segmentation=first.cargo_segmentation,
        load=first.load,
        material=first.material,
        plate=first.plate,
        validation=first.validation,
        gate=first.gate,
    )
    cache.set_result(cache_key, data, result.model_dump())
    cache.record_detection()
    return result


# ── Registry ───────────────────────────────────────────────────────────────────

@router.get(
    "/registry",
    summary="List registered fleet vehicles",
)
async def list_registry():
    entries = _load_registry()
    return {"total": len(entries), "vehicles": [e.model_dump() for e in entries]}


@router.post(
    "/registry/reload",
    summary="Hot-reload fleet registry",
)
async def registry_reload():
    count = reload_registry()
    return {"success": True, "loaded": count}
