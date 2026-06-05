"""
Video processor — extracts frames from uploaded files OR live stream URLs,
quality-filters, detects vehicles, runs the full 9-model pipeline,
deduplicates across frames, annotates thumbnails, and saves training data.

Supported stream protocols (via OpenCV VideoCapture):
  RTSP   — rtsp://user:pass@192.168.1.100:554/stream1
  HLS    — http://host/stream.m3u8
  MJPEG  — http://host/mjpg/video.mjpg
  RTMP   — rtmp://host/live/stream

Pipeline (shared by both file and stream sources)
──────────────────────────────────────────────────
1. Frame capture at `sample_fps`
2. Model A  — quality gate (rejects blurry / dark / overexposed frames)
3. Models B+C+D — vehicle detection; skip frames with no primary vehicle
4. Models E→I   — full pipeline per vehicle on surviving frames
5. Deduplicate  — one identity per plate (or subtype + 3-second window)
6. Best frame per identity = highest Model-I overall_score
7. Annotate thumbnails server-side with coloured bboxes
8. Save vehicle frames as labelled training data
"""
from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from modules.quality_checker import check_image_quality
from modules.vehicle_detector import detect_vehicles, run_raw_yolo
from schemas.detection import FullDetectionResponse, ImageQualityResult, VehicleResult
from modules.motion_detector import global_motion_detector

VIDEO_FRAMES_DIR = Path("feedback_dataset/video_frames")

logger = logging.getLogger(__name__)

# ── Annotation colour palettes (BGR for OpenCV) ──────────────────────────────
_VEHICLE_BGR = [
    (233, 165,  14),
    (247,  85, 168),
    ( 22, 115, 249),
    (166, 184,  20),
    (153,  72, 236),
    ( 22, 204, 132),
]
_GATE_BGR: dict[str, tuple[int, int, int]] = {
    "Pass":   ( 94, 197,  34),
    "Review": ( 11, 158, 245),
    "Reject": ( 68,  68, 239),
}

_ALLOWED_SCHEMES = ("rtsp://", "rtsps://", "rtmp://", "rtmps://",
                    "http://", "https://")


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class FrameData:
    frame_number: int
    timestamp_ms: float
    image:        np.ndarray


@dataclass
class FrameResult:
    frame:              FrameData
    result:             FullDetectionResponse
    overall_score:      float
    is_best_frame:      bool          = False
    thumbnail_b64:      str           = ""
    frame_path:         str           = ""
    vehicle_identities: list[str]     = field(default_factory=list)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _thumbnail_b64(image: np.ndarray, width: int = 400) -> str:
    h, w = image.shape[:2]
    new_h = max(1, int(h * width / w))
    thumb = cv2.resize(image, (width, new_h))
    _, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def _annotate(image: np.ndarray, result: FullDetectionResponse) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[:2]
    scale      = min(w, h) / 800.0
    font_scale = max(0.35, 0.5 * scale)
    thickness  = max(1, int(1.5 * scale))
    font       = cv2.FONT_HERSHEY_SIMPLEX

    for i, vr in enumerate(result.vehicles or []):
        gate_dec = vr.gate.decision if vr.gate else None
        color: tuple[int, int, int] = (
            _GATE_BGR.get(gate_dec, _VEHICLE_BGR[i % len(_VEHICLE_BGR)])
            if gate_dec else _VEHICLE_BGR[i % len(_VEHICLE_BGR)]
        )
        if vr.vehicle and vr.vehicle.bbox:
            bx = vr.vehicle.bbox
            cv2.rectangle(out, (bx.x1, bx.y1), (bx.x2, bx.y2), color, thickness + 1)
            labels = [
                f"#{i + 1} {vr.vehicle.vehicle_sub_type} {vr.vehicle.confidence * 100:.0f}%",
                (f"{vr.plate.normalized_plate} [{gate_dec.upper()}]"
                 if vr.plate and vr.plate.normalized_plate and gate_dec else
                 vr.plate.normalized_plate if vr.plate and vr.plate.normalized_plate else ""),
            ]
            for label, base_y in zip(labels, [bx.y1, bx.y2]):
                if not label:
                    continue
                (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)
                ly = max(th + 4, base_y) if base_y == bx.y1 else base_y
                cv2.rectangle(out, (bx.x1, ly - th - 3), (bx.x1 + tw + 6, ly + 2), color, -1)
                cv2.putText(out, label, (bx.x1 + 3, ly - 1),
                            font, font_scale, (0, 0, 0), 1, cv2.LINE_AA)
        if vr.plate and vr.plate.bbox:
            pb = vr.plate.bbox
            cv2.rectangle(out, (pb.x1, pb.y1), (pb.x2, pb.y2),
                          (11, 158, 245), max(1, thickness - 1))
    return out


def _vehicle_identity(vr: VehicleResult, time_bucket: int) -> str:
    if vr.plate and vr.plate.normalized_plate and vr.plate.confidence > 0.55:
        return f"plate:{vr.plate.normalized_plate}"
    return f"type:{vr.vehicle.vehicle_sub_type}:t{time_bucket}"


def _fmt_ts(ms: float) -> str:
    s = ms / 1000.0
    return f"{int(s // 60)}:{s % 60:05.2f}"


# ── Session-based training data save ─────────────────────────────────────────

def _new_session_dir(source: str) -> Path:
    """
    Create and return a new session directory:
      feedback_dataset/video_frames/{YYYY-MM-DD}/{source}_{short_uuid}/
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    short_id = uuid.uuid4().hex[:8]
    session_dir = VIDEO_FRAMES_DIR / date_str / f"{source}_{short_id}"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def save_indexed_frame(
    session_dir: Path,
    frame_number: int,
    image: np.ndarray,
    timestamp_ms: float,
    detection: dict[str, Any],
) -> None:
    """
    Save one frame as   frame_{frame_number:06d}.jpg
    and append one JSON line to  labels.jsonl  in the same session directory.

    File layout:
        feedback_dataset/video_frames/
          {YYYY-MM-DD}/
            {source}_{uuid8}/
              frame_000000.jpg
              frame_000015.jpg
              frame_000030.jpg
              ...
              labels.jsonl       ← one JSON object per saved frame, in order
              session.json       ← written once when the session finishes
    """
    fname = f"frame_{frame_number:06d}.jpg"
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 92])
    (session_dir / fname).write_bytes(buf.tobytes())

    label_line = json.dumps({
        "frame_number":  frame_number,
        "timestamp_ms":  round(timestamp_ms, 1),
        "timestamp":     _fmt_ts(timestamp_ms),
        "filename":      fname,
        "detection":     detection,
    }, ensure_ascii=False)
    with open(session_dir / "labels.jsonl", "a", encoding="utf-8") as f:
        f.write(label_line + "\n")


def write_session_manifest(
    session_dir: Path,
    *,
    source: str,
    url: str | None,
    video_fps: float,
    duration_ms: float,
    sampled_frames: int,
    vehicle_frames: int,
    unique_vehicle_count: int,
    processing_time_seconds: float,
) -> None:
    manifest = {
        "source":                  source,
        "stream_url":              url,
        "created_utc":             datetime.now(timezone.utc).isoformat(),
        "video_fps":               video_fps,
        "duration_ms":             duration_ms,
        "sampled_frames":          sampled_frames,
        "vehicle_frames":          vehicle_frames,
        "unique_vehicle_count":    unique_vehicle_count,
        "processing_time_seconds": processing_time_seconds,
    }
    (session_dir / "session.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── Frame capture — file ──────────────────────────────────────────────────────

def extract_frames(
    video_bytes: bytes,
    sample_fps:  float = 2.0,
    max_frames:  int   = 100,
) -> tuple[list[FrameData], float, float, float]:
    """
    Write video bytes to a temp file, open with VideoCapture,
    and return (frames, video_fps, duration_ms, total_video_frames).
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        tmp.write(video_bytes)
        tmp.flush()
        tmp.close()

        cap = cv2.VideoCapture(tmp.name)
        if not cap.isOpened():
            raise ValueError("Cannot open video — unsupported format or corrupt file")

        video_fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_f     = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_ms = (total_f / video_fps) * 1000.0
        interval    = max(1, int(round(video_fps / max(0.1, sample_fps))))

        frames: list[FrameData] = []
        idx = 0
        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % interval == 0:
                frames.append(FrameData(idx, (idx / video_fps) * 1000.0, frame))
            idx += 1

        cap.release()
        return frames, video_fps, duration_ms, float(max(total_f, idx))
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── Frame capture — live stream ───────────────────────────────────────────────

def capture_stream_frames(
    url:             str,
    sample_fps:      float = 2.0,
    max_frames:      int   = 60,
    connect_timeout: float = 12.0,
) -> tuple[list[FrameData], float, float, float]:
    """
    Open a live stream URL (RTSP/HLS/MJPEG/RTMP) with VideoCapture,
    capture up to `max_frames` sampled frames, then close.

    Returns (frames, stream_fps, duration_ms, total_raw_frames_read).

    Raises ValueError if the stream cannot be opened within `connect_timeout`.
    """
    # Validate scheme to prevent SSRF via unexpected protocols
    url_lower = url.strip()
    if not any(url_lower.startswith(s) for s in _ALLOWED_SCHEMES):
        raise ValueError(
            f"Unsupported stream URL scheme. Allowed: RTSP, RTSPS, RTMP, RTMPS, HTTP, HTTPS"
        )

    cap_holder: list[cv2.VideoCapture | None] = [None]
    open_error: list[str] = []

    def _open():
        try:
            cap = cv2.VideoCapture(url_lower)
            cap_holder[0] = cap
        except Exception as exc:
            open_error.append(str(exc))

    t = threading.Thread(target=_open, daemon=True)
    t.start()
    t.join(timeout=connect_timeout)

    cap = cap_holder[0]
    if cap is None or not cap.isOpened():
        if cap:
            cap.release()
        reason = open_error[0] if open_error else "connection timed out or refused"
        raise ValueError(f"Cannot open stream '{url_lower[:80]}': {reason}")

    # Prefer cap FPS; many streams report 0 — default to 25
    stream_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    # For streams that report an unrealistic FPS, clamp it
    if stream_fps > 120 or stream_fps < 1:
        stream_fps = 25.0

    # We grab every N-th frame to hit ~sample_fps
    interval = max(1, int(round(stream_fps / max(0.1, sample_fps))))

    frames: list[FrameData] = []
    idx = 0
    while len(frames) < max_frames:
        # grab() is faster than read() for frames we'll discard
        if idx % interval != 0:
            ok = cap.grab()
            if not ok:
                break
            idx += 1
            continue

        ret, frame = cap.retrieve() if cap.grab() else (False, None)
        if not ret or frame is None:
            # Fall back to full read
            ret2, frame2 = cap.read()
            if not ret2 or frame2 is None:
                break
            frame = frame2

        ts_ms = (idx / stream_fps) * 1000.0
        frames.append(FrameData(idx, ts_ms, frame))
        idx += 1

    cap.release()

    total_f     = float(idx)
    duration_ms = (idx / stream_fps) * 1000.0
    return frames, stream_fps, duration_ms, total_f


# ── Shared ML pipeline ────────────────────────────────────────────────────────

def _run_pipeline_on_frames(
    frames:          list[FrameData],
    video_fps:       float,
    duration_ms:     float,
    total_f:         float,
    max_best_frames: int,
    save_training:   bool,
    t0:              float,
    source:          str         = "file",   # "file" | "stream"
    stream_url:      str | None  = None,
) -> dict[str, Any]:
    """
    Runs stages 2-8 of the pipeline on a pre-extracted frame list.
    Shared by process_video() and process_stream().

    When save_training=True every vehicle-containing frame is written to:
        feedback_dataset/video_frames/{YYYY-MM-DD}/{source}_{uuid8}/
            frame_{frame_number:06d}.jpg   ← indexed by original frame number
            labels.jsonl                   ← one JSON line per frame, in order
            session.json                   ← session metadata written at the end
    """
    from routers.detect import _process_vehicle  # avoid circular imports

    # Create the training session directory once, up front
    session_dir: Path | None = None
    if save_training:
        session_dir = _new_session_dir(source)
        logger.info(f"[video] training session → {session_dir}")

    # ── 1.5. Motion detection filter ───────────────────────────────────────────
    motion_pass: list[FrameData] = []
    for fd in frames:
        # Use stream_url as source ID, or 'file' for uploaded videos
        source_id = stream_url if stream_url else f"file_{id(frames)}"
        has_motion, score, meta = global_motion_detector.detect(source_id, fd.image)
        if has_motion:
            motion_pass.append(fd)
            
    logger.info(f"[video] motion={len(motion_pass)}/{len(frames)}")

    # ── 2. Quality gate ────────────────────────────────────────────────────────
    quality_pass: list[tuple[FrameData, ImageQualityResult]] = []
    for fd in motion_pass:
        q = check_image_quality(fd.image)
        if q.quality.value != "Reject":
            quality_pass.append((fd, q))

    # ── 3. Vehicle detection filter ────────────────────────────────────────────
    VehicleFrame = tuple[FrameData, ImageQualityResult, list, bool]
    vehicle_frames_list: list[VehicleFrame] = []
    for fd, quality in quality_pass:
        _, all_v, model_avail = detect_vehicles(fd.image)
        primary = [v for v in all_v if v.is_primary_vehicle]
        if primary:
            vehicle_frames_list.append((fd, quality, primary, model_avail))

    logger.info(
        f"[video] quality={len(quality_pass)}/{len(frames)}  "
        f"vehicle={len(vehicle_frames_list)}/{len(quality_pass)}"
    )

    # ── 4. Full pipeline + indexed save ───────────────────────────────────────
    frame_results: list[FrameResult] = []
    training_saved = 0

    for fd, quality, primary_vehicles, model_avail in vehicle_frames_list:
        raw_dets, _ = run_raw_yolo(fd.image) if model_avail else ([], False)
        vr_list: list[VehicleResult] = []
        for v in primary_vehicles:
            vr = _process_vehicle(fd.image, v, raw_dets, model_avail, quality)
            vr_list.append(vr)

        first = vr_list[0]
        full_result = FullDetectionResponse(
            success=True,
            model_available=model_avail,
            image_quality=quality,
            vehicles=vr_list,
            total_vehicles=len(vr_list),
            vehicle=first.vehicle,
            cargo_segmentation=first.cargo_segmentation,
            load=first.load,
            material=first.material,
            plate=first.plate,
            gate=first.gate,
        )

        scores = [vr.gate.overall_score for vr in vr_list if vr.gate]
        overall_score = (sum(scores) / len(scores)) if scores else first.vehicle.confidence

        time_bucket = fd.frame_number // max(1, int(video_fps * 3))
        identities = [_vehicle_identity(vr, time_bucket) for vr in vr_list]

        frame_results.append(FrameResult(
            frame=fd,
            result=full_result,
            overall_score=overall_score,
            vehicle_identities=identities,
            frame_path=str(session_dir.relative_to(VIDEO_FRAMES_DIR) / f"frame_{fd.frame_number:06d}.jpg") if session_dir else ""
        ))

        # ── Indexed save: frame_NNNNNN.jpg + labels.jsonl line ────────────────
        if session_dir is not None:
            # Compact detection summary stored in labels.jsonl
            detection_summary = {
                "vehicle_count":  len(vr_list),
                "vehicles": [
                    {
                        "sub_type":   vr.vehicle.vehicle_sub_type,
                        "confidence": round(vr.vehicle.confidence, 4),
                        "plate":      vr.plate.normalized_plate if vr.plate else None,
                        "plate_conf": round(vr.plate.confidence, 4) if vr.plate else None,
                        "load":       vr.load.load_status if vr.load else None,
                        "material":   vr.material.material_type if vr.material else None,
                        "gate":       vr.gate.decision if vr.gate else None,
                        "score":      round(overall_score, 4),
                    }
                    for vr in vr_list
                ],
            }
            save_indexed_frame(
                session_dir,
                fd.frame_number,
                fd.image,
                fd.timestamp_ms,
                detection_summary,
            )
            training_saved += 1

    # ── 5. Deduplicate + best frame per identity ──────────────────────────────
    best_per_id: dict[str, FrameResult] = {}
    for fr in frame_results:
        for ident in fr.vehicle_identities:
            if ident not in best_per_id or fr.overall_score > best_per_id[ident].overall_score:
                best_per_id[ident] = fr

    best_ids = {id(fr) for fr in best_per_id.values()}
    for fr in frame_results:
        fr.is_best_frame = id(fr) in best_ids

    seen: dict[int, FrameResult] = {id(fr): fr for fr in best_per_id.values()}
    if len(seen) < max_best_frames:
        for fr in sorted(frame_results, key=lambda f: f.overall_score, reverse=True):
            if id(fr) not in seen:
                seen[id(fr)] = fr
            if len(seen) >= max_best_frames:
                break

    top_frames = sorted(seen.values(), key=lambda f: f.frame.timestamp_ms)

    # ── 6. Annotate thumbnails ────────────────────────────────────────────────
    for fr in top_frames:
        ann = _annotate(fr.frame.image, fr.result)
        fr.thumbnail_b64 = _thumbnail_b64(ann)

    elapsed = time.perf_counter() - t0

    # ── 7. Write session manifest ─────────────────────────────────────────────
    if session_dir is not None:
        try:
            write_session_manifest(
                session_dir,
                source=source,
                url=stream_url,
                video_fps=video_fps,
                duration_ms=duration_ms,
                sampled_frames=len(frames),
                vehicle_frames=training_saved,
                unique_vehicle_count=len(best_per_id),
                processing_time_seconds=round(elapsed, 2),
            )
        except Exception as exc:
            logger.warning(f"[video] could not write session manifest: {exc}")

    return {
        "success":                 True,
        "video_fps":               round(video_fps, 2),
        "duration_ms":             round(duration_ms, 1),
        "total_frames":            int(total_f),
        "sampled_frames":          len(frames),
        "quality_passed":          len(quality_pass),
        "vehicle_frames":          len(vehicle_frames_list),
        "best_frames": [
            {
                "frame_number":       fr.frame.frame_number,
                "timestamp_ms":       fr.frame.timestamp_ms,
                "timestamp_label":    _fmt_ts(fr.frame.timestamp_ms),
                "thumbnail":          fr.thumbnail_b64,
                "frame_path":         fr.frame_path,
                "overall_score":      round(fr.overall_score, 4),
                "is_best_frame":      fr.is_best_frame,
                "vehicle_count":      fr.result.total_vehicles,
                "vehicle_identities": fr.vehicle_identities,
                "result":             fr.result.model_dump(),
            }
            for fr in top_frames
        ],
        "unique_vehicle_count":    len(best_per_id),
        "training_samples_saved":  training_saved,
        "training_session_dir":    str(session_dir) if session_dir else None,
        "processing_time_seconds": round(elapsed, 2),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def process_video(
    video_bytes:     bytes,
    *,
    sample_fps:      float = 2.0,
    max_frames:      int   = 100,
    max_best_frames: int   = 12,
    save_training:   bool  = True,
) -> dict[str, Any]:
    """Process an uploaded video file through the full 9-model pipeline."""
    t0 = time.perf_counter()
    frames, video_fps, duration_ms, total_f = extract_frames(
        video_bytes, sample_fps=sample_fps, max_frames=max_frames
    )
    logger.info(f"[video:file] {len(frames)} frames sampled from {duration_ms / 1000:.1f}s")
    return _run_pipeline_on_frames(
        frames, video_fps, duration_ms, total_f,
        max_best_frames, save_training, t0,
        source="file", stream_url=None,
    )


def process_stream(
    url:             str,
    *,
    sample_fps:      float = 2.0,
    max_frames:      int   = 60,
    max_best_frames: int   = 12,
    save_training:   bool  = True,
    connect_timeout: float = 12.0,
) -> dict[str, Any]:
    """
    Open a live stream URL and run the full 9-model pipeline on captured frames.
    Blocks until `max_frames` have been captured or the stream ends.
    """
    t0 = time.perf_counter()
    frames, stream_fps, duration_ms, total_f = capture_stream_frames(
        url, sample_fps=sample_fps, max_frames=max_frames,
        connect_timeout=connect_timeout,
    )
    logger.info(
        f"[video:stream] {len(frames)} frames captured from '{url[:60]}'"
        f" @ {stream_fps:.1f} fps"
    )
    result = _run_pipeline_on_frames(
        frames, stream_fps, duration_ms, total_f,
        max_best_frames, save_training, t0,
        source="stream", stream_url=url,
    )
    result["stream_url"] = url
    return result
