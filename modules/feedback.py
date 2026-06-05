"""
Feedback / correction store for human-in-the-loop training data collection.

Each submitted correction is appended as one JSON line to:
    feedback_dataset/feedback.jsonl

The accompanying image is saved to:
    feedback_dataset/images/{YYYY-MM-DD}/{md5}.jpg

This gives a ready-to-use labelled dataset that maps each image to ground-truth
corrections across: plate OCR, vehicle sub-type, load status, material type,
and gate decision.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DATASET_DIR   = Path("feedback_dataset")
IMAGES_DIR    = DATASET_DIR / "images"
FEEDBACK_FILE = DATASET_DIR / "feedback.jsonl"

_CORRECTABLE_FIELDS = {"plate", "vehicle_sub_type", "load_status", "material_type", "gate_decision"}


def _ensure_dirs() -> None:
    DATASET_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def save_image(image_bytes: bytes, md5: Optional[str] = None) -> tuple[str, Path]:
    """Write image bytes to disk; return (md5, path)."""
    _ensure_dirs()
    if md5 is None:
        md5 = _md5(image_bytes)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = IMAGES_DIR / date_str
    day_dir.mkdir(exist_ok=True)
    img_path = day_dir / f"{md5}.jpg"
    if not img_path.exists():
        img_path.write_bytes(image_bytes)
    return md5, img_path


def record_correction(
    *,
    image_md5: str,
    filename: str,
    ai_result: dict[str, Any],
    corrections: dict[str, Any],
) -> dict[str, Any]:
    """
    Append one correction record to feedback.jsonl.

    corrections is a dict of field -> {ai: <value>, corrected: <value>}.
    Only fields that actually changed should be included.

    Returns the persisted record.
    """
    _ensure_dirs()

    record = {
        "id":          str(uuid.uuid4()),
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "image_md5":   image_md5,
        "filename":    filename,
        "corrections": corrections,
        "ai_result":   ai_result,
    }

    with FEEDBACK_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    fields_changed = list(corrections.keys())
    logger.info(f"[feedback] {filename} | fields changed: {fields_changed}")
    return record


def get_stats() -> dict[str, Any]:
    """Return aggregate statistics from feedback.jsonl."""
    if not FEEDBACK_FILE.exists():
        return {
            "total_corrections": 0,
            "corrections_by_field": {},
            "recent": [],
        }

    records: list[dict] = []
    with FEEDBACK_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    by_field: dict[str, int] = {}
    for rec in records:
        for field in rec.get("corrections", {}):
            by_field[field] = by_field.get(field, 0) + 1

    recent = [
        {
            "id":        r["id"],
            "timestamp": r["timestamp"],
            "filename":  r["filename"],
            "fields":    list(r.get("corrections", {}).keys()),
        }
        for r in records[-10:]
    ]
    recent.reverse()

    return {
        "total_corrections":    len(records),
        "corrections_by_field": by_field,
        "recent":               recent,
    }


def export_jsonl() -> bytes:
    """Return the raw JSONL bytes for download."""
    if not FEEDBACK_FILE.exists():
        return b""
    return FEEDBACK_FILE.read_bytes()


def export_dataset_zip() -> Optional[bytes]:
    """
    Create a ZIP in memory containing all images and the feedback.jsonl.
    Returns bytes or None if empty.
    """
    import io
    import zipfile

    if not DATASET_DIR.exists():
        return None

    # We use io.BytesIO to create a zip file in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add feedback.jsonl if it exists
        if FEEDBACK_FILE.exists():
            zf.write(FEEDBACK_FILE, arcname="feedback.jsonl")

        # Add all images recursively
        if IMAGES_DIR.exists():
            for root, _, files in os.walk(IMAGES_DIR):
                for file in files:
                    file_path = Path(root) / file
                    # Calculate relative path from DATASET_DIR for the zip
                    # We want the zip to look like images/YYYY-MM-DD/abc.jpg
                    rel_path = file_path.relative_to(DATASET_DIR)
                    zf.write(file_path, arcname=str(rel_path))

    return buf.getvalue()
