import io
import logging
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

VEHICLE_CLASS_IDS = {2, 3, 5, 7}


def decode_upload(data: bytes) -> np.ndarray:
    """Decode raw image bytes → BGR ndarray (OpenCV format)."""
    try:
        pil_img = Image.open(io.BytesIO(data)).convert("RGB")
        bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return bgr
    except Exception as exc:
        logger.error(f"[image] Failed to decode upload: {exc}")
        raise ValueError(f"Cannot decode image: {exc}") from exc


def crop_region(image: np.ndarray, x1: int, y1: int, x2: int, y2: int, pad: int = 0) -> np.ndarray:
    """Crop a region from image with optional padding, clamped to image bounds."""
    h, w = image.shape[:2]
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return image[y1:y2, x1:x2]


def iou(box_a: list[int], box_b: list[int]) -> float:
    """Compute Intersection-over-Union of two [x1,y1,x2,y2] boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def intersection_over_smaller(box_a: list[int], box_b: list[int]) -> float:
    """Fraction of the smaller box that intersects with box_a."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / area_b if area_b > 0 else 0.0


def resize_for_inference(image: np.ndarray, max_side: int = 1280) -> np.ndarray:
    """Resize image keeping aspect ratio so the largest side ≤ max_side."""
    h, w = image.shape[:2]
    scale = min(max_side / max(h, w), 1.0)
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image
