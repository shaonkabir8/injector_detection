"""
Event Emitter — Detector → Redis Queue
=======================================

Python detector calls emit_detection_event() after the full 9-model pipeline
completes. This module pushes a structured event to Redis so Node workers can
consume and decide ALLOW / DENY / REVIEW.

Design rules:
  - NON-BLOCKING: push and exit, never await Node response here
  - DEDUPLICATION: same plate within DEDUP_WINDOW_SECONDS is silently dropped
  - TENANT-AWARE: every event carries tenant_id from camera config
  - FALLBACK: if Redis is down, log the event and continue (do NOT crash detector)

Queue key: "securityos_detection_events" (BullMQ-compatible list)
Dedup key:  "securityos:dedup:{tenant_id}:{plate_normalized}" (TTL = DEDUP_WINDOW)

Event shape (matches Node worker expectation):
{
  "event_id":      "<uuid>",
  "tenant_id":     "<string>",
  "camera_id":     "<string>",
  "timestamp":     "<ISO-8601 UTC>",
  "plate":         "<raw OCR text>",
  "plate_norm":    "<normalized plate>",
  "sub_type":      "<vehicle sub-type>",
  "load_status":   "<Empty|Partial|Full>",
  "material":      "<Bricks|Coal|Sand|Raw Clay|Empty|Unknown>",
  "gate_decision": "<Pass|Review|Reject>",
  "overall_score": <float 0-1>,
  "confidence":    <float 0-1>,
  "source":        "detector"
}
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Seconds within which a duplicate plate from the same tenant is suppressed
DEDUP_WINDOW_SECONDS: int = 3

# Redis key for the BullMQ-compatible detection event list
QUEUE_KEY = "securityos_detection_events"

_redis_client = None


def _get_redis() -> Optional[Any]:
    """
    Return a Redis client using the same connection as the cache module.
    Avoids opening a second connection pool.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        from modules.cache import _get_client  # reuse existing singleton
        _redis_client = _get_client()
    except Exception as exc:
        logger.warning(f"[emitter] Could not acquire Redis client: {exc}")
        _redis_client = None

    return _redis_client


def _normalize_plate(plate: str) -> str:
    """Strip spaces, uppercase — same as plate_detector but minimal dep."""
    import re
    return re.sub(r"[^A-Z0-9]", "", plate.upper())


def _dedup_key(tenant_id: str, plate_norm: str) -> str:
    return f"securityos:dedup:{tenant_id}:{plate_norm}"


def _is_duplicate(r: Any, tenant_id: str, plate_norm: str) -> bool:
    """
    Returns True if this plate was already emitted within DEDUP_WINDOW_SECONDS.
    Sets the dedup key with TTL if this is a fresh event.
    Skips dedup if plate is empty (no-plate events always pass through).
    """
    if not plate_norm:
        return False
    key = _dedup_key(tenant_id, plate_norm)
    try:
        existing = r.get(key)
        if existing:
            logger.info(
                f"[emitter] DEDUP: plate='{plate_norm}' tenant={tenant_id} "
                f"— suppressed (within {DEDUP_WINDOW_SECONDS}s window)"
            )
            return True
        r.setex(key, DEDUP_WINDOW_SECONDS, "1")
        return False
    except Exception as exc:
        logger.warning(f"[emitter] Dedup check failed: {exc} — allowing event through")
        return False


def emit_detection_event(
    *,
    tenant_id: str,
    camera_id: str,
    plate_text: str,
    plate_norm: str,
    sub_type: str,
    load_status: str,
    material: str,
    gate_decision: str,
    overall_score: float,
    vehicle_confidence: float,
    actual_percent: Optional[int] = None,
    expected_percent: Optional[int] = None,
) -> bool:
    """
    Build and push one detection event to the Redis queue.

    Args:
        tenant_id          : Kiln/tenant identifier (from camera config)
        camera_id          : Camera identifier (e.g. "CAM-GATE-01")
        plate_text         : Raw OCR plate text
        plate_norm         : Normalized plate (uppercase, no spaces)
        sub_type           : Vehicle sub-type string
        load_status        : "Empty" | "Partial" | "Full"
        material           : Material type string
        gate_decision      : "Pass" | "Review" | "Reject"
        overall_score      : Confidence gate overall score (0–1)
        vehicle_confidence : YOLO vehicle detection confidence (0–1)
        actual_percent     : AI Estimated Capacity % (0-120)
        expected_percent   : Expected Capacity %

    Returns:
        True if event was pushed, False if dropped (dedup) or Redis unavailable.
    """
    r = _get_redis()

    if r is None:
        logger.error(
            f"[emitter] Redis unavailable — event NOT queued "
            f"plate='{plate_norm}' tenant={tenant_id}"
        )
        return False

    # Deduplication check
    if _is_duplicate(r, tenant_id, plate_norm):
        return False

    event: dict[str, Any] = {
        "event_id":      str(uuid.uuid4()),
        "tenant_id":     tenant_id,
        "camera_id":     camera_id,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "plate":         plate_text,
        "plate_norm":    plate_norm,
        "sub_type":      sub_type,
        "load_status":   load_status,
        "material":      material,
        "gate_decision": gate_decision,
        "overall_score": round(overall_score, 4),
        "confidence":    round(vehicle_confidence, 4),
        "source":        "detector",
    }
    
    if actual_percent is not None:
        event["actual_percent"] = actual_percent
    if expected_percent is not None:
        event["expected_percent"] = expected_percent

    try:
        # RPUSH so Node worker LPOPs from the left → FIFO order
        r.rpush(QUEUE_KEY, json.dumps(event, ensure_ascii=False))
        logger.info(
            f"[emitter] Pushed event_id={event['event_id'][:8]}… "
            f"plate='{plate_norm}' tenant={tenant_id} gate={gate_decision}"
        )
        return True
    except Exception as exc:
        logger.error(f"[emitter] Failed to push event to Redis: {exc}")
        return False


def emit_from_vehicle_result(
    vehicle_result: Any,
    *,
    tenant_id: str,
    camera_id: str,
) -> bool:
    """
    Convenience wrapper — extracts all fields from a VehicleResult object
    (as returned by detect.py _process_vehicle) and calls emit_detection_event.

    Usage in detect.py full pipeline:
        from modules.event_emitter import emit_from_vehicle_result
        emit_from_vehicle_result(vr, tenant_id=tenant_id, camera_id=camera_id)
    """
    try:
        plate_text = ""
        plate_norm = ""
        if vehicle_result.plate:
            plate_text = vehicle_result.plate.plate_text or ""
            plate_norm = vehicle_result.plate.normalized_plate or ""

        sub_type = ""
        vehicle_confidence = 0.0
        if vehicle_result.vehicle:
            sub_type = vehicle_result.vehicle.vehicle_sub_type.value
            vehicle_confidence = vehicle_result.vehicle.confidence

        load_status = "Unknown"
        actual_percent = None
        expected_percent = None
        if vehicle_result.load:
            load_status = vehicle_result.load.load_status.value
            actual_percent = vehicle_result.load.actual_percent
            expected_percent = vehicle_result.load.expected_percent

        material = "Unknown"
        if vehicle_result.material:
            material = vehicle_result.material.material_type.value

        gate_decision = "Reject"
        overall_score = 0.0
        if vehicle_result.gate:
            gate_decision = vehicle_result.gate.decision.value
            overall_score = vehicle_result.gate.overall_score

        return emit_detection_event(
            tenant_id=tenant_id,
            camera_id=camera_id,
            plate_text=plate_text,
            plate_norm=plate_norm,
            sub_type=sub_type,
            load_status=load_status,
            material=material,
            gate_decision=gate_decision,
            overall_score=overall_score,
            vehicle_confidence=vehicle_confidence,
            actual_percent=actual_percent,
            expected_percent=expected_percent,
        )

    except Exception as exc:
        logger.error(f"[emitter] emit_from_vehicle_result failed: {exc}")
        return False
