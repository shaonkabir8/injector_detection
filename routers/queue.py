"""
Async Queue + Stats Router
===========================
Endpoints for submitting background detection jobs, polling status,
inspecting cache statistics, and retrieving usage data.

Endpoints
─────────
  POST /detect/async              → Submit full-pipeline job to queue
  GET  /detect/queue/{job_id}     → Poll job status / fetch result
  GET  /detect/queue              → List recent jobs
  GET  /detect/stats              → Cache hit-rate + usage counters
  POST /detect/cache/flush        → Flush all cached results (admin)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from modules.cache import cache
from modules.job_queue import enqueue, get_job, list_jobs, queue_depth
from utils.image import decode_upload, resize_for_inference
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["queue"])


# ── Submit async job ──────────────────────────────────────────────────────────

@router.post(
    "/async",
    summary="Submit full-pipeline detection job (async)",
    description=(
        "Queues a full 9-model detection job and returns a `job_id` immediately.\n\n"
        "Poll `GET /detect/queue/{job_id}` until `status == 'done'`.\n\n"
        "Results are also cached in Redis — identical images return the cached "
        "result without re-running the pipeline."
    ),
)
async def submit_async_job(
    file: UploadFile = File(...),
    mode: str = Form("full", description="'full' or 'validate'"),
    expected_plate: Optional[str] = Form(None),
) -> dict:
    from utils.image import decode_upload, resize_for_inference

    data = await file.read()

    if len(data) > settings.max_image_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.max_image_bytes // (1024 * 1024)} MB limit",
        )

    if mode not in ("full", "validate"):
        raise HTTPException(status_code=400, detail="mode must be 'full' or 'validate'")

    # Check cache before queuing
    cached = cache.get_result(mode, data)
    if cached:
        logger.info(f"[queue/async] Cache hit for mode={mode} — skipping queue")
        return {
            "job_id":       None,
            "status":       "done",
            "from_cache":   True,
            "mode":         mode,
            "queue_depth":  queue_depth(),
            "result":       cached,
        }

    # Build the sync callable that the worker will run
    def _run():
        import numpy as np
        from routers.detect import _read_image, _process_vehicle
        from modules.quality_checker    import check_image_quality
        from modules.vehicle_detector   import detect_vehicles, run_raw_yolo
        from modules.plate_detector     import detect_plate
        from schemas.detection          import FullDetectionResponse, VehicleValidationResponse

        image = _read_image(data)
        quality = check_image_quality(image)
        _, all_vehicles, model_available = detect_vehicles(image)
        raw_detections, _ = run_raw_yolo(image) if model_available else ([], False)

        vehicle_results = []
        for v in all_vehicles:
            vr = _process_vehicle(
                image, v, raw_detections, model_available, quality,
                include_validation=(mode == "validate"),
                expected_plate=expected_plate,
            )
            vehicle_results.append(vr)

        first = vehicle_results[0] if vehicle_results else None

        if mode == "validate":
            resp = VehicleValidationResponse(
                success=True,
                model_available=model_available,
                image_quality=quality,
                vehicles=vehicle_results,
                total_vehicles=len(vehicle_results),
                vehicle=first.vehicle if first else None,
                load=first.load if first else None,
                plate=first.plate if first else None,
                validation=first.validation if first else None,
                gate=first.gate if first else None,
            )
        else:
            resp = FullDetectionResponse(
                success=True,
                model_available=model_available,
                image_quality=quality,
                vehicles=vehicle_results,
                total_vehicles=len(vehicle_results),
                vehicle=first.vehicle if first else None,
                load=first.load if first else None,
                plate=first.plate if first else None,
                gate=first.gate if first else None,
            )

        result_dict = resp.model_dump()
        cache.set_result(mode, data, result_dict)
        cache.record_detection()
        return result_dict

    job_id = await enqueue(
        mode=mode,
        fn=_run,
        image_filename=file.filename or "upload",
    )

    return {
        "job_id":      job_id,
        "status":      "queued",
        "from_cache":  False,
        "mode":        mode,
        "queue_depth": queue_depth(),
        "result":      None,
    }


# ── Poll job status ───────────────────────────────────────────────────────────

@router.get(
    "/queue/{job_id}",
    summary="Poll async job status",
    description=(
        "Returns the current status of a queued job.\n\n"
        "| `status` | Meaning |\n"
        "|---|---|\n"
        "| `queued` | Waiting for worker |\n"
        "| `processing` | Worker is running the pipeline |\n"
        "| `done` | Complete — `result` field is populated |\n"
        "| `failed` | Error — `error` field has the message |"
    ),
)
async def poll_job(job_id: str) -> dict:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    job["job_id"] = job_id
    return job


# ── List recent jobs ──────────────────────────────────────────────────────────

@router.get(
    "/queue",
    summary="List recent async jobs",
)
async def list_recent_jobs(limit: int = 20) -> dict:
    jobs = list_jobs(min(limit, 50))
    return {
        "queue_depth": queue_depth(),
        "total":       len(jobs),
        "jobs":        jobs,
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="Cache + usage statistics",
    description=(
        "Returns Redis cache hit/miss counts, total detection count, today's "
        "detection count, and SaaS tier information."
    ),
)
async def get_stats() -> dict:
    stats = cache.get_stats()
    stats["queue_depth"] = queue_depth()
    return stats


# ── Cache management ──────────────────────────────────────────────────────────

@router.post(
    "/cache/flush",
    summary="Flush all cached detection results",
)
async def flush_cache() -> dict:
    count = cache.flush_results()
    return {"success": True, "flushed": count}
