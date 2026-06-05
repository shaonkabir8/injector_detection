"""
Model H — Plate Detector + OCR
================================

Two-stage pipeline:
  1. OpenCV geometric locator
       grayscale → bilateral filter → Canny → contours →
       4-corner polygon filter (aspect ratio, area, solidity)
  2. EasyOCR on each candidate crop

Multi-vehicle support
─────────────────────
`detect_plate_in_region(image, vehicle_bbox)` focuses the search on a single
vehicle's bounding box (expanded by REGION_PAD_FRACTION to catch plates that
sit just below or outside the tight detection box).  This ensures that in a
multi-vehicle scene each vehicle's plate is found independently, rather than
all vehicles sharing the same (wrong) plate reading.

Fallback: if no geometric candidates are found inside the expanded region,
OCR runs on the full region crop.

Post-processing:
  - Filter to strings with ≥4 consecutive alphanumeric chars
  - OCR substitutions: O→0, I→1, S→5, B→8, Z→2 (Bangladesh plate convention)
  - normalized_plate = stripped, substituted, uppercased

Falls back gracefully if EasyOCR is not installed.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import cv2
import numpy as np

from schemas.detection import BoundingBox, PlateDetection
from config import settings

logger = logging.getLogger(__name__)

_ocr_reader = None
_ocr_attempted = False

_PLATE_PATTERN = re.compile(r"[A-Z0-9]{4,}", re.IGNORECASE)

# How much to expand each vehicle bbox side when searching for its plate
REGION_PAD_FRACTION: float = 0.18


# ── OCR reader singleton ───────────────────────────────────────────────────────

def _get_reader():
    global _ocr_reader, _ocr_attempted
    if _ocr_attempted:
        return _ocr_reader
    _ocr_attempted = True
    try:
        import easyocr
        logger.info("[plate] Initialising EasyOCR (first call is slow)…")
        _ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("[plate] EasyOCR ready")
    except Exception as exc:
        logger.error(f"[plate] EasyOCR init failed: {exc}")
        _ocr_reader = None
    return _ocr_reader


# ── Geometric plate candidate finder ──────────────────────────────────────────

def _find_plate_candidates(image: np.ndarray) -> list[tuple[np.ndarray, list[int]]]:
    """
    Return list of (cropped_image, [x1,y1,x2,y2]) for plate candidate regions.
    Coordinates are relative to `image` (which may already be a vehicle crop).
    """
    h, w = image.shape[:2]
    gray     = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    edges    = cv2.Canny(filtered, 30, 200)

    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:100]

    candidates: list[tuple[np.ndarray, list[int]]] = []

    for contour in contours:
        peri  = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

        if len(approx) != 4:
            continue

        x, y, bw, bh = cv2.boundingRect(approx)

        if bw < settings.plate_min_width or bh < settings.plate_min_height:
            continue

        aspect = bw / bh
        if not (settings.plate_aspect_ratio_min <= aspect <= settings.plate_aspect_ratio_max):
            continue

        area      = cv2.contourArea(contour)
        rect_area = bw * bh
        if rect_area == 0 or area / rect_area < 0.5:
            continue

        x1 = max(0, x - 2);  y1 = max(0, y - 2)
        x2 = min(w, x + bw + 2);  y2 = min(h, y + bh + 2)
        crop = image[y1:y2, x1:x2]
        candidates.append((crop, [x1, y1, x2, y2]))

    return candidates


def _enhance_for_ocr(crop: np.ndarray) -> np.ndarray:
    scale = max(1.0, 100.0 / crop.shape[0])
    if scale > 1.0:
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _is_valid_plate(text: str) -> bool:
    cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
    return len(cleaned) >= 4


_OCR_SUBS = str.maketrans("OISBZoisbz", "0151280182")


def _normalize(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text).upper().translate(_OCR_SUBS)


# ── Core OCR runner (on a cropped region) ─────────────────────────────────────

def _run_ocr_on_region(
    region: np.ndarray,
    offset_x: int = 0,
    offset_y: int = 0,
) -> PlateDetection:
    """
    Run plate detection on `region`.
    Returns PlateDetection with bbox coordinates offset by (offset_x, offset_y)
    to translate back to full-image space.
    """
    reader = _get_reader()

    candidates = _find_plate_candidates(region)
    if not candidates:
        logger.debug("[plate] No geometric candidates — running OCR on full region")
        candidates = [(region, [0, 0, region.shape[1], region.shape[0]])]

    best_text  = ""
    best_conf  = 0.0
    best_bbox: Optional[list[int]] = None
    all_texts: list[str] = []

    for crop, local_bbox in candidates:
        if reader is None:
            break

        enhanced = _enhance_for_ocr(crop)

        try:
            results = reader.readtext(
                enhanced,
                detail=1,
                paragraph=False,
                min_size=10,
                text_threshold=settings.plate_min_confidence,
                low_text=0.3,
                link_threshold=0.4,
            )
        except Exception as exc:
            logger.warning(f"[plate] OCR error: {exc}")
            continue

        for (_pts, text, conf) in results:
            text = text.strip()
            if not _is_valid_plate(text):
                continue
            all_texts.append(text)
            if conf > best_conf:
                best_conf = conf
                best_text = text
                best_bbox = local_bbox

    if best_text:
        logger.info(f"[plate] '{best_text}' conf={best_conf:.2f}")
    else:
        logger.info("[plate] No valid plate text found")

    full_bbox = None
    if best_bbox is not None:
        full_bbox = BoundingBox(
            x1=best_bbox[0] + offset_x,
            y1=best_bbox[1] + offset_y,
            x2=best_bbox[2] + offset_x,
            y2=best_bbox[3] + offset_y,
        )

    return PlateDetection(
        plate_text=best_text,
        normalized_plate=_normalize(best_text),
        confidence=round(best_conf, 4),
        bbox=full_bbox,
        candidates=list(dict.fromkeys(all_texts)),
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_plate(image: np.ndarray) -> PlateDetection:
    """
    Run plate detection on the full image (used by /detect/plate endpoint).
    """
    return _run_ocr_on_region(image, offset_x=0, offset_y=0)


def detect_plate_for_vehicle(
    image: np.ndarray,
    vehicle_bbox: BoundingBox,
) -> PlateDetection:
    """
    Run plate detection focused on a single vehicle's bounding box region.

    The search region is expanded by REGION_PAD_FRACTION on each side to
    catch plates that sit just below or outside the tight YOLO detection box.
    Returned PlateDetection.bbox coordinates are in full-image space.

    This is the correct function to call in a multi-vehicle pipeline so that
    each vehicle's plate is found independently.
    """
    img_h, img_w = image.shape[:2]

    pad_x = int(vehicle_bbox.width  * REGION_PAD_FRACTION)
    pad_y = int(vehicle_bbox.height * REGION_PAD_FRACTION)

    x1 = max(0, vehicle_bbox.x1 - pad_x)
    y1 = max(0, vehicle_bbox.y1 - pad_y)
    x2 = min(img_w, vehicle_bbox.x2 + pad_x)
    y2 = min(img_h, vehicle_bbox.y2 + pad_y)

    region = image[y1:y2, x1:x2]

    if region.size == 0 or region.shape[0] < 20 or region.shape[1] < 20:
        logger.warning("[plate] Vehicle region too small — falling back to full image")
        return detect_plate(image)

    logger.debug(
        f"[plate] Searching in vehicle region "
        f"[{x1},{y1}→{x2},{y2}] (padded by {pad_x}px×{pad_y}px)"
    )

    return _run_ocr_on_region(region, offset_x=x1, offset_y=y1)
