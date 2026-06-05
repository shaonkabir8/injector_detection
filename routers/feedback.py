"""
Feedback router — human correction endpoints for training data collection.

POST /detect/feedback
    Submit a corrected detection result.
    Saves image to disk + appends a JSONL record with the diff.

GET  /detect/feedback/stats
    Aggregate statistics (total corrections, breakdown by field, recent 10).

GET  /detect/feedback/export
    Download the full feedback.jsonl dataset file.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from modules.feedback import export_jsonl, get_stats, record_correction, save_image

logger = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])


@router.post(
    "/feedback",
    summary="Submit a human correction for AI training",
    description=(
        "Saves the corrected labels alongside the source image on disk.\n\n"
        "The `corrections` field is a JSON object mapping each corrected field to "
        "`{\"ai\": <predicted_value>, \"corrected\": <ground_truth>}`.\n\n"
        "Supported fields: `plate`, `vehicle_sub_type`, `load_status`, "
        "`material_type`, `gate_decision`.\n\n"
        "Only include fields that actually changed — unchanged fields should be omitted."
    ),
)
async def submit_feedback(
    file:        UploadFile = File(..., description="Original image (required to persist training sample)"),
    filename:    str        = Form(...),
    corrections: str        = Form(..., description="JSON string: {field: {ai, corrected}}"),
    ai_result:   str        = Form("{}",  description="JSON string of the full AI detection result"),
) -> dict:
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty image")

    try:
        corrections_data: dict = json.loads(corrections)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid corrections JSON: {exc}") from exc

    try:
        ai_result_data: dict = json.loads(ai_result) if ai_result else {}
    except json.JSONDecodeError:
        ai_result_data = {}

    if not corrections_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="corrections must contain at least one field")

    image_md5, img_path = save_image(image_bytes)
    record = record_correction(
        image_md5=image_md5,
        filename=filename,
        ai_result=ai_result_data,
        corrections=corrections_data,
    )

    return {
        "success":       True,
        "id":            record["id"],
        "image_md5":     image_md5,
        "image_saved":   str(img_path),
        "fields_saved":  list(corrections_data.keys()),
        "total_corrections": get_stats()["total_corrections"],
    }


@router.get(
    "/feedback/stats",
    summary="Training dataset statistics",
)
async def feedback_stats() -> dict:
    return get_stats()


from modules.feedback import export_dataset_zip, export_jsonl, get_stats, record_correction, save_image


@router.get(
    "/feedback/export",
    summary="Download feedback.jsonl training dataset",
    response_class=Response,
)
async def feedback_export() -> Response:
    data = export_jsonl()
    return Response(
        content=data,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=feedback.jsonl"},
    )


@router.get(
    "/feedback/export-zip",
    summary="Download full training dataset (images + jsonl) as ZIP",
    response_class=Response,
)
async def feedback_export_zip() -> Response:
    data = export_dataset_zip()
    if data is None:
        raise HTTPException(status_code=404, detail="Dataset is empty")
    
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=brickify_training_dataset.zip"},
    )
