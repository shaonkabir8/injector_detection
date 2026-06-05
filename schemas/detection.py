from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

_no_model_ns = ConfigDict(protected_namespaces=())


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class ImageQuality(str, Enum):
    GOOD   = "Good"
    WARN   = "Warn"
    REJECT = "Reject"


class LoadStatus(str, Enum):
    EMPTY   = "Empty"
    PARTIAL = "Partial"
    FULL    = "Full"
    UNKNOWN = "Unknown"


class VehicleSubType(str, Enum):
    # PRIMARY — brick kiln vehicles
    TRUCK_LARGE  = "Truck-Large"
    TRUCK_MEDIUM = "Truck-Medium"
    TRUCK_SMALL  = "Truck-Small"
    TRACTOR      = "Tractor"
    TROLLEY      = "Trolley"
    # NON-PRIMARY
    VAN        = "Van"
    CAR        = "Car"
    MOTORCYCLE = "Motorcycle"
    BUS        = "Bus"
    UNKNOWN    = "Unknown"


class MaterialType(str, Enum):
    BRICKS   = "Bricks"
    RAW_CLAY = "Raw Clay"
    COAL     = "Coal"
    SAND     = "Sand"
    MIXED    = "Mixed"
    EMPTY    = "Empty"
    UNKNOWN  = "Unknown"


class GateDecision(str, Enum):
    PASS   = "Pass"
    REVIEW = "Review"
    REJECT = "Reject"


PRIMARY_SUBTYPES: frozenset[VehicleSubType] = frozenset({
    VehicleSubType.TRUCK_LARGE,
    VehicleSubType.TRUCK_MEDIUM,
    VehicleSubType.TRUCK_SMALL,
    VehicleSubType.TRACTOR,
    VehicleSubType.TROLLEY,
})


# ═══════════════════════════════════════════════════════════════════════════════
# Model A — Image Quality
# ═══════════════════════════════════════════════════════════════════════════════

class ImageQualityResult(BaseModel):
    quality: ImageQuality
    blur_score: float = Field(..., ge=0.0, le=1.0)
    brightness_score: float = Field(..., ge=0.0, le=1.0)
    contrast_score: float = Field(..., ge=0.0, le=1.0)
    overexposed_fraction: float = Field(..., ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)
    recommendation: str


# ═══════════════════════════════════════════════════════════════════════════════
# Model B/C/D — Vehicle Detection
# ═══════════════════════════════════════════════════════════════════════════════

class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        return self.width * self.height


class VehicleDetection(BaseModel):
    """Output of Model B (YOLO) + Model C (fusion) + Model D (subtype classifier)."""
    vehicle_type: str = Field(...,
        description="Broad COCO category: Car/Van, Bus/Trolley, Truck/Tractor")
    vehicle_sub_type: VehicleSubType = Field(VehicleSubType.UNKNOWN)
    is_primary_vehicle: bool = Field(False,
        description="True = brick kiln vehicle")
    confidence: float = Field(..., ge=0.0, le=1.0,
        description="YOLO bounding-box detection confidence")
    fusion_used: bool = Field(False,
        description="True when Model C TTA pass improved detection")
    subtype_confidence: float = Field(0.0, ge=0.0, le=1.0,
        description="Model D subtype classification confidence")
    subtype_features: dict[str, float] = Field(default_factory=dict)
    bbox: Optional[BoundingBox] = None
    class_id: int
    aspect_ratio: Optional[float] = None
    size_fraction: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Model E — Cargo Segmenter
# ═══════════════════════════════════════════════════════════════════════════════

class CargoSegmentation(BaseModel):
    cargo_fill_ratio: float = Field(..., ge=0.0, le=1.0)
    cargo_present: bool
    segment_confidence: float = Field(..., ge=0.0, le=1.0)
    method: str = "kmeans+edge"


# ═══════════════════════════════════════════════════════════════════════════════
# Model F — Load Classifier
# ═══════════════════════════════════════════════════════════════════════════════

class LoadItem(BaseModel):
    label: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None


class LoadDetectionResult(BaseModel):
    load_status: LoadStatus
    is_loaded: bool
    load_confidence: float = Field(..., ge=0.0, le=1.0)
    coverage_ratio: float = Field(..., ge=0.0, le=1.0)
    actual_percent: Optional[int] = None
    expected_percent: Optional[int] = None
    segmented: bool = Field(False,
        description="True when Model E cargo mask was used")
    load_items: list[LoadItem] = Field(default_factory=list)
    item_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# Model G — Material Classifier
# ═══════════════════════════════════════════════════════════════════════════════

class MaterialDetectionResult(BaseModel):
    material_type: MaterialType
    confidence: float = Field(..., ge=0.0, le=1.0)
    coverage_ratio: float = Field(..., ge=0.0, le=1.0)
    segmented: bool = Field(False,
        description="True when Model E cargo mask was used")
    all_scores: dict[str, float] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Model H — Plate Detector + OCR
# ═══════════════════════════════════════════════════════════════════════════════

class PlateDetection(BaseModel):
    plate_text: str
    normalized_plate: str = Field("",
        description="Uppercase, OCR corrections applied")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None
    candidates: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Model I — Confidence Gate
# ═══════════════════════════════════════════════════════════════════════════════

class ConfidenceGateResult(BaseModel):
    decision: GateDecision
    overall_score: float = Field(..., ge=0.0, le=1.0)
    module_scores: dict[str, float] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    reason: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Fleet Registry / Validation (Module 4)
# ═══════════════════════════════════════════════════════════════════════════════

class RegisteredVehicle(BaseModel):
    plate: str
    vehicle_type: str
    sub_type: str = ""
    owner: str = ""
    department: str = ""
    authorized: bool = True
    notes: str = ""


class ValidationResult(BaseModel):
    authorized: bool
    plate_matched: bool
    type_matched: bool
    detected_plate: str
    expected_plate: Optional[str] = None
    registered_vehicle: Optional[RegisteredVehicle] = None
    plate_similarity: float = Field(0.0, ge=0.0, le=1.0)
    reason: str


# ═══════════════════════════════════════════════════════════════════════════════
# VehicleResult — complete per-vehicle output (multi-vehicle support)
# ═══════════════════════════════════════════════════════════════════════════════

class VehicleResult(BaseModel):
    """
    Full pipeline result for a SINGLE vehicle within the image.

    Every primary vehicle detected in the frame gets its own VehicleResult.
    Models E → F → G → H → I all run independently per vehicle so that
    load, material, plate and gate decisions are vehicle-specific — not shared
    across multiple vehicles in the same photo.
    """
    model_config = _no_model_ns

    # Model B/C/D
    vehicle: VehicleDetection

    # Model E
    cargo_segmentation: Optional[CargoSegmentation] = None

    # Model F — analysed only on this vehicle's cargo mask
    load: Optional[LoadDetectionResult] = None

    # Model G — analysed only on this vehicle's cargo mask
    material: Optional[MaterialDetectionResult] = None

    # Model H — plate search restricted to this vehicle's bbox region
    plate: Optional[PlateDetection] = None

    # Module 4 — fleet registry validation for this vehicle's plate
    validation: Optional[ValidationResult] = None

    # Model I — gate decision for this vehicle only
    gate: Optional[ConfidenceGateResult] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Compound API Responses
# ═══════════════════════════════════════════════════════════════════════════════

class FullDetectionResponse(BaseModel):
    """
    Full 9-model pipeline response — multi-vehicle aware.

    `vehicles` contains one VehicleResult per primary vehicle found in the frame,
    each with its own load/material/plate/gate results.

    Top-level fields (vehicle, load, material, plate, gate) mirror vehicles[0]
    for single-vehicle backward compatibility.
    """
    model_config = _no_model_ns

    success: bool = True
    model_available: bool

    # Model A — one quality check per image
    image_quality: Optional[ImageQualityResult] = None

    # All primary vehicles, each with full pipeline results
    vehicles: list[VehicleResult] = Field(
        default_factory=list,
        description="Per-vehicle results — one entry per primary kiln vehicle detected",
    )
    total_vehicles: int = Field(0,
        description="Number of primary brick kiln vehicles found in this image")

    # Convenience top-level fields = vehicles[0] (backward compat)
    vehicle: Optional[VehicleDetection] = Field(None,
        description="Best / first vehicle (same as vehicles[0].vehicle)")
    cargo_segmentation: Optional[CargoSegmentation] = None
    load: Optional[LoadDetectionResult] = None
    material: Optional[MaterialDetectionResult] = None
    plate: Optional[PlateDetection] = None
    gate: Optional[ConfidenceGateResult] = None

    error: Optional[str] = None


class VehicleOnlyResponse(BaseModel):
    model_config = _no_model_ns
    success: bool = True
    model_available: bool
    image_quality: Optional[ImageQualityResult] = None
    vehicle: Optional[VehicleDetection] = None
    all_vehicles: list[VehicleDetection] = Field(default_factory=list)
    total_vehicles: int = 0
    error: Optional[str] = None


class LoadOnlyResponse(BaseModel):
    model_config = _no_model_ns
    success: bool = True
    model_available: bool
    cargo_segmentation: Optional[CargoSegmentation] = None
    load: Optional[LoadDetectionResult] = None
    error: Optional[str] = None


class MaterialOnlyResponse(BaseModel):
    model_config = _no_model_ns
    success: bool = True
    model_available: bool
    cargo_segmentation: Optional[CargoSegmentation] = None
    material: Optional[MaterialDetectionResult] = None
    error: Optional[str] = None


class PlateOnlyResponse(BaseModel):
    success: bool = True
    plate: Optional[PlateDetection] = None
    error: Optional[str] = None


class VehicleValidationResponse(BaseModel):
    """
    Full 9-model pipeline + fleet validation — multi-vehicle aware.

    `vehicles` contains one VehicleResult (with validation) per primary vehicle.
    """
    model_config = _no_model_ns

    success: bool = True
    model_available: bool

    image_quality: Optional[ImageQualityResult] = None

    vehicles: list[VehicleResult] = Field(
        default_factory=list,
        description="Per-vehicle results including fleet validation",
    )
    total_vehicles: int = 0

    # Top-level = vehicles[0] for backward compat
    vehicle: Optional[VehicleDetection] = None
    cargo_segmentation: Optional[CargoSegmentation] = None
    load: Optional[LoadDetectionResult] = None
    material: Optional[MaterialDetectionResult] = None
    plate: Optional[PlateDetection] = None
    validation: Optional[ValidationResult] = None
    gate: Optional[ConfidenceGateResult] = None

    error: Optional[str] = None
