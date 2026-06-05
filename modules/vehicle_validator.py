"""
Vehicle Registry Validator
==========================

Validates a detected vehicle (plate + type) against a registered fleet database.

Registry loading order:
  1. VEHICLE_REGISTRY env var → path to a custom JSON file
  2. vehicles.json in the service directory (default)
  3. Empty registry (all vehicles flagged as unauthorized)

Registry JSON format:
  [
    {
      "plate": "MH12AB1234",
      "vehicle_type": "Truck",
      "sub_type": "Semi-Truck",
      "owner": "Rajesh Logistics",
      "department": "Inbound",
      "authorized": true,
      "notes": "Daily delivery"
    },
    ...
  ]

Plate matching uses fuzzy normalisation to tolerate common OCR errors:
  O ↔ 0,  I ↔ 1,  S ↔ 5,  B ↔ 8,  Z ↔ 2

similarity = (matching chars) / (max of the two lengths)
"""
from __future__ import annotations

import json
import logging
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from schemas.detection import (
    LoadDetectionResult,
    PlateDetection,
    RegisteredVehicle,
    ValidationResult,
    VehicleDetection,
)

logger = logging.getLogger(__name__)

_REGISTRY_DIR = Path(__file__).parent.parent
_DEFAULT_REGISTRY = _REGISTRY_DIR / "vehicles.json"

_PLATE_NORMALISE = str.maketrans("OISBZoisbz", "0151280182")
_MIN_SIMILARITY = 0.75   # 75 % character match to accept a plate as matched

_registry: Optional[list[RegisteredVehicle]] = None
_registry_loaded = False


def _load_registry() -> list[RegisteredVehicle]:
    global _registry, _registry_loaded
    if _registry_loaded:
        return _registry or []

    _registry_loaded = True
    path_str = os.environ.get("VEHICLE_REGISTRY", str(_DEFAULT_REGISTRY))
    path = Path(path_str)

    if not path.exists():
        logger.warning(f"[validator] Registry not found at {path}. All vehicles will be unauthorized.")
        _registry = []
        return _registry

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _registry = [RegisteredVehicle(**entry) for entry in data]
        logger.info(f"[validator] Loaded {len(_registry)} entries from {path}")
    except Exception as exc:
        logger.error(f"[validator] Failed to load registry: {exc}")
        _registry = []

    return _registry


def _normalize_plate(plate: str) -> str:
    """Strip non-alphanumeric chars, apply OCR-error substitutions, uppercase."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", plate)
    return cleaned.translate(_PLATE_NORMALISE).upper()


def _plate_similarity(a: str, b: str) -> float:
    na, nb = _normalize_plate(a), _normalize_plate(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _type_matches(detected: VehicleDetection, registered: RegisteredVehicle) -> bool:
    """
    Check whether the detected vehicle type is consistent with the registered type.
    Uses both the broad category and the sub-type.
    """
    det_broad = detected.vehicle_type.lower()
    det_sub = detected.vehicle_sub_type.value.lower()
    reg_type = registered.vehicle_type.lower()
    reg_sub = registered.sub_type.lower()

    # Direct broad match
    if reg_type and reg_type in det_broad:
        return True
    if reg_type and det_broad in reg_type:
        return True

    # Sub-type match
    if reg_sub and reg_sub in det_sub:
        return True

    # Common synonym mappings — updated for new sub-type names
    synonyms: dict[str, list[str]] = {
        "truck": [
            "truck-large", "truck-medium", "truck-small",
            "truck/tractor", "truck/pickup/tractor/trolley",
        ],
        "truck-large": ["truck-large", "truck/tractor"],
        "truck-medium": ["truck-medium", "truck/tractor"],
        "truck-small": ["truck-small", "truck/tractor"],
        "tractor": ["tractor", "truck/tractor", "truck/pickup/tractor/trolley"],
        "trolley": ["trolley", "bus/trolley"],
        "van": ["van", "car/van"],
        "car": ["car", "car/van"],
        "bus": ["bus", "bus/trolley"],
        "motorcycle": ["motorcycle"],
    }
    for canonical, aliases in synonyms.items():
        if reg_type == canonical or reg_sub == canonical:
            if any(alias in det_broad or alias in det_sub for alias in aliases):
                return True

    return False


def validate_vehicle(
    detected_vehicle: Optional[VehicleDetection],
    detected_plate: Optional[PlateDetection],
    expected_plate: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a detected vehicle against the fleet registry.

    Args:
        detected_vehicle : Best YOLO vehicle detection (may be None)
        detected_plate   : OCR plate result (may be None or empty)
        expected_plate   : Plate string known in advance (optional override)

    Returns:
        ValidationResult with authorization status and match details
    """
    registry = _load_registry()

    # Decide which plate text to use
    ocr_text = detected_plate.plate_text if detected_plate else ""
    query_plate = expected_plate or ocr_text

    if not query_plate:
        return ValidationResult(
            authorized=False,
            plate_matched=False,
            type_matched=False,
            detected_plate="",
            expected_plate=expected_plate,
            registered_vehicle=None,
            plate_similarity=0.0,
            reason="No plate text detected or provided",
        )

    # Find best matching registry entry
    best_entry: Optional[RegisteredVehicle] = None
    best_sim = 0.0

    for entry in registry:
        sim = _plate_similarity(query_plate, entry.plate)
        if sim > best_sim:
            best_sim = sim
            best_entry = entry

    plate_matched = best_sim >= _MIN_SIMILARITY
    type_matched = False
    authorized = False
    reason_parts: list[str] = []

    if not plate_matched:
        reason_parts.append(f"Plate '{query_plate}' not found in registry (best match: {best_sim:.0%})")
        authorized = False
    else:
        assert best_entry is not None

        if not best_entry.authorized:
            reason_parts.append(f"Vehicle {best_entry.plate} is marked unauthorized")
            authorized = False
        else:
            authorized = True

        if detected_vehicle is not None:
            type_matched = _type_matches(detected_vehicle, best_entry)
            if not type_matched:
                reason_parts.append(
                    f"Type mismatch: registered '{best_entry.vehicle_type}' "
                    f"but detected '{detected_vehicle.vehicle_sub_type.value}'"
                )
                # Type mismatch downgrades authorization — log but keep authorized
                # (may be a legitimate vehicle change; flag for human review)
                if authorized:
                    reason_parts.append("Flagged for manual review due to type mismatch")
        else:
            reason_parts.append("No vehicle detected in image")

    if not reason_parts:
        reason_parts.append(
            f"Authorized: {best_entry.plate} ({best_entry.vehicle_type}) — {best_entry.owner}"
        )

    logger.info(
        f"[validator] plate='{query_plate}' matched={plate_matched} "
        f"sim={best_sim:.2f} authorized={authorized} type_ok={type_matched}"
    )

    return ValidationResult(
        authorized=authorized,
        plate_matched=plate_matched,
        type_matched=type_matched,
        detected_plate=ocr_text,
        expected_plate=expected_plate,
        registered_vehicle=best_entry,
        plate_similarity=round(best_sim, 4),
        reason=" | ".join(reason_parts),
    )


def reload_registry() -> int:
    """Force-reload the registry from disk. Returns count of entries."""
    global _registry, _registry_loaded
    _registry = None
    _registry_loaded = False
    entries = _load_registry()
    return len(entries)
