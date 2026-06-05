"""
Model E — Cargo Area Segmenter
================================

Segments the cargo-bearing region inside the vehicle's bounding box to
produce a binary cargo mask.  Downstream modules (Load Classifier F and
Material Classifier G) analyse only the masked pixels for higher accuracy.

The vehicle bbox crops are from a side-on gate camera.  The vehicle floor,
axles, and chassis are excluded using the same top/bottom crop fractions as
the load detector.  The remaining "cargo zone" is then segmented into
foreground (cargo) vs background (empty bed, walls, sky).

Algorithm — K-means + Edge Fusion
──────────────────────────────────
  1. Extract cargo zone crop (skip top 5%, bottom 22%).
  2. Compute a per-pixel "complexity" feature:
       feature = 0.60 × normalised_gradient_magnitude
               + 0.40 × normalised_pixel_intensity
     Gradient captures irregular cargo shapes; intensity separates bright
     cargo from dark metallic bed.
  3. K-means (k=2) on this 1D feature — two clusters: "simple" and "complex".
  4. The "complex" cluster is assumed to be cargo.
  5. Coal exception: coal is dark AND complex → captured by gradient channel.
  6. Morphological cleanup (closing + opening) removes noise.
  7. cargo_fill_ratio = fraction of cargo-zone pixels in the cargo cluster.

Output
──────
  CargoSegmentation — cargo_fill_ratio, cargo_present, segment_confidence
  cargo_mask (ndarray, bool, cargo-zone size) — passed to downstream modules

The mask is NOT included in the JSON response (only the summary metrics are).
Use the internal API `segment_cargo(image, bbox)` which returns both.
"""
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from schemas.detection import BoundingBox, CargoSegmentation
from config import settings

logger = logging.getLogger(__name__)

CARGO_MIN_FILL: float = 0.06    # below this → cargo_present = False
MORPH_KERNEL_SIZE: int = 7


def segment_cargo(
    image: np.ndarray,
    vehicle_bbox: BoundingBox,
) -> tuple[Optional[np.ndarray], CargoSegmentation]:
    """
    Segment the cargo area and return (cargo_mask, CargoSegmentation).

    cargo_mask shape = (zone_height, zone_width), dtype=bool.
    None if segmentation fails (vehicle crop too small).
    """
    img_h, img_w = image.shape[:2]
    x1 = max(0, vehicle_bbox.x1)
    y1 = max(0, vehicle_bbox.y1)
    x2 = min(img_w, vehicle_bbox.x2)
    y2 = min(img_h, vehicle_bbox.y2)

    crop = image[y1:y2, x1:x2]
    if crop.size == 0 or crop.shape[0] < 12 or crop.shape[1] < 12:
        return None, _unknown_seg()

    ch, cw = crop.shape[:2]
    zone_y1 = int(ch * settings.load_visual_skip_top)
    zone_y2 = int(ch * (1.0 - settings.load_visual_skip_bottom))
    zone = crop[zone_y1:zone_y2, :]

    if zone.size == 0 or zone.shape[0] < 5 or zone.shape[1] < 5:
        return None, _unknown_seg()

    zh, zw = zone.shape[:2]

    # ── Per-pixel complexity feature ─────────────────────────────────────────
    gray    = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Gradient magnitude (Sobel)
    gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx**2 + gy**2)

    # Normalise both channels to 0–1
    grad_norm = grad_mag / max(1.0, float(grad_mag.max()))
    bright_norm = gray / 255.0

    feature = (0.60 * grad_norm + 0.40 * bright_norm).reshape(-1, 1).astype(np.float32)

    # ── K-means (k=2) ────────────────────────────────────────────────────────
    try:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
        _, labels, centers = cv2.kmeans(
            feature, 2, None, criteria,
            attempts=3,
            flags=cv2.KMEANS_PP_CENTERS,
        )
    except Exception as exc:
        logger.warning(f"[cargo/E] K-means failed: {exc}")
        return None, _unknown_seg()

    labels = labels.reshape(zh, zw)
    centers = centers.flatten()

    # The cluster with HIGHER feature value is the "cargo" cluster
    cargo_label = int(np.argmax(centers))
    raw_mask = (labels == cargo_label).astype(np.uint8) * 255

    # ── Morphological cleanup ─────────────────────────────────────────────────
    kernel = np.ones((MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE), np.uint8)
    cleaned = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN,  kernel)

    cargo_mask = cleaned.astype(bool)
    fill_ratio = round(float(cargo_mask.sum()) / max(1, cargo_mask.size), 4)
    cargo_present = fill_ratio >= CARGO_MIN_FILL

    # Confidence: how well separated are the two clusters?
    separation = round(abs(float(centers[0]) - float(centers[1])), 3)
    seg_confidence = round(min(1.0, separation / 0.30), 4)   # saturates at 0.30 separation

    logger.info(
        f"[cargo/E] fill={fill_ratio:.2%} present={cargo_present} "
        f"separation={separation:.3f} conf={seg_confidence:.3f}"
    )

    return cargo_mask, CargoSegmentation(
        cargo_fill_ratio=fill_ratio,
        cargo_present=cargo_present,
        segment_confidence=seg_confidence,
        method="kmeans+edge",
    )


def _unknown_seg() -> CargoSegmentation:
    return CargoSegmentation(
        cargo_fill_ratio=0.0,
        cargo_present=False,
        segment_confidence=0.0,
        method="failed",
    )
