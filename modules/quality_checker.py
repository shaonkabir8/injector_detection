"""
Model A — Image Quality Checker
================================

Assesses incoming images before they enter the detection pipeline.
Poor-quality images produce unreliable detections — rejecting or flagging
them early avoids false positives and wasted inference time.

Checks
------
  Blur (sharpness)
    Laplacian operator variance on the grayscale image.
    Sharp images → high variance (>300).  Blurry → low (<80).

  Brightness
    Mean pixel intensity (grayscale, 0–255) normalised to 0–1.
    Good range: 0.15 – 0.85.

  Contrast
    Std-dev of grayscale pixels / 128.  Low std-dev = washed-out image.

  Overexposure
    Fraction of pixels with V > 240 in HSV.  >30% = overexposed.

Quality decision
----------------
  GOOD    — no flags raised → PROCEED
  WARN    — 1 flag raised → PROCEED_WITH_CAUTION (results may be degraded)
  REJECT  — blur < 30 (completely unreadable) OR ≥3 flags raised
"""
from __future__ import annotations

import cv2
import numpy as np

from schemas.detection import ImageQuality, ImageQualityResult


# ── Thresholds ────────────────────────────────────────────────────────────────
BLUR_REJECT   = 30.0    # Laplacian var — below this = completely unreadable
BLUR_WARN     = 80.0    # Laplacian var — below this = flag BLURRY
BLUR_NORM     = 500.0   # Normalisation cap for blur_score output

BRIGHT_MIN    = 0.12    # Mean brightness below this → DARK
BRIGHT_MAX    = 0.92    # Mean brightness above this → OVEREXPOSED

CONTRAST_MIN  = 0.10    # Std-dev / 128 below this → LOW_CONTRAST
OVEREXP_MAX   = 0.30    # Fraction of V>240 above this → OVEREXPOSED


def check_image_quality(image: np.ndarray) -> ImageQualityResult:
    """
    Run all quality checks on a BGR ndarray and return an ImageQualityResult.

    Args:
        image: BGR uint8 ndarray (already resized to inference size by the router)

    Returns:
        ImageQualityResult with quality enum, per-metric scores, flags, and recommendation
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ── Blur (Laplacian variance) ─────────────────────────────────────────────
    lap_var   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = round(min(1.0, lap_var / BLUR_NORM), 4)

    # ── Brightness (mean of grayscale) ────────────────────────────────────────
    brightness = round(float(np.mean(gray)) / 255.0, 4)

    # ── Contrast (std-dev of grayscale, normalised by 128) ───────────────────
    contrast = round(min(1.0, float(np.std(gray)) / 128.0), 4)

    # ── Overexposure (fraction of HSV V-channel > 240) ───────────────────────
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    overexposed_frac = round(float(np.sum(v_channel > 240)) / max(1, v_channel.size), 4)

    # ── Flag collection ───────────────────────────────────────────────────────
    flags: list[str] = []

    if lap_var < BLUR_WARN:
        flags.append("BLURRY")
    if brightness < BRIGHT_MIN:
        flags.append("DARK")
    if brightness > BRIGHT_MAX:
        flags.append("OVEREXPOSED")
    if contrast < CONTRAST_MIN:
        flags.append("LOW_CONTRAST")
    if overexposed_frac > OVEREXP_MAX:
        if "OVEREXPOSED" not in flags:
            flags.append("OVEREXPOSED")

    # ── Quality decision ──────────────────────────────────────────────────────
    if lap_var < BLUR_REJECT or len(flags) >= 3:
        quality = ImageQuality.REJECT
        recommendation = "REJECT"
    elif len(flags) == 0:
        quality = ImageQuality.GOOD
        recommendation = "PROCEED"
    else:
        quality = ImageQuality.WARN
        recommendation = "PROCEED_WITH_CAUTION"

    return ImageQualityResult(
        quality=quality,
        blur_score=blur_score,
        brightness_score=brightness,
        contrast_score=contrast,
        overexposed_fraction=overexposed_frac,
        flags=flags,
        recommendation=recommendation,
    )
