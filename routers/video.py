"""
Video detection router.

POST /detect/video
    Upload a video file — extract best frames, run full 9-model pipeline,
    return annotated thumbnails + detection results.

POST /detect/video-url
    Provide an HTTP/HTTPS URL to a video file — server downloads it then
    runs the same pipeline as a file upload.  Great for training batches.

POST /detect/stream
    Paste a live stream URL (RTSP / HLS / MJPEG / RTMP) — capture frames
    in real time, run the same pipeline, return identical results.
    Frames are auto-saved as labelled training data.
"""
from __future__ import annotations

import asyncio
import logging

import requests as req_lib

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from modules.video_processor import process_video, process_stream

logger = logging.getLogger(__name__)
router = APIRouter(tags=["video"])

MAX_VIDEO_BYTES  = 200 * 1024 * 1024   # 200 MB
STREAM_TIMEOUT_S = 120                  # hard cap for stream processing


# ── /detect/video — file upload ───────────────────────────────────────────────

@router.post(
    "/video",
    summary="Video vehicle detection — upload a file",
    description=(
        "Upload a video (MP4, AVI, MOV, WebM, MKV) and get back the most informative "
        "frames with annotated thumbnails and full detection results.\n\n"
        "Pipeline per sampled frame:\n"
        "1. **Model A** — quality gate\n"
        "2. **Models B+C+D** — primary vehicle detection\n"
        "3. **Models E→I** — full pipeline on frames with vehicles\n"
        "4. Deduplication — best frame per unique vehicle\n"
        "5. Thumbnails annotated server-side"
    ),
)
async def detect_video(
    file:            UploadFile = File(...,  description="Video file (MP4/AVI/MOV/WebM/MKV)"),
    sample_fps:      float      = Form(2.0,  description="Frames per second to sample (0.5–4.0)"),
    max_frames:      int        = Form(100,  description="Max frames to extract (10–200)"),
    max_best_frames: int        = Form(12,   description="Max best frames to return (5–30)"),
    save_training:   bool       = Form(True, description="Auto-save vehicle frames as training data"),
) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Empty file")
    if len(data) > MAX_VIDEO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video exceeds {MAX_VIDEO_BYTES // (1024 * 1024)} MB limit",
        )

    sample_fps      = max(0.5, min(4.0,  sample_fps))
    max_frames      = max(10,  min(200,  max_frames))
    max_best_frames = max(5,   min(30,   max_best_frames))

    logger.info(f"[video:file] {len(data) // 1024} KB  fps={sample_fps}  max={max_frames}")
    try:
        result = await asyncio.to_thread(
            process_video, data,
            sample_fps=sample_fps, max_frames=max_frames,
            max_best_frames=max_best_frames, save_training=save_training,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc

    logger.info(
        f"[video:file] done — {result['vehicle_frames']} vehicle frames  "
        f"{result['unique_vehicle_count']} unique  {result['processing_time_seconds']}s"
    )
    return result


# ── /detect/video-url — remote file download ─────────────────────────────────

_URL_DOWNLOAD_TIMEOUT_S = 180   # max time to download + process

_ALLOWED_SCHEMES = {"http", "https"}
_VIDEO_CONTENT_TYPES = {
    "video/mp4", "video/avi", "video/quicktime",
    "video/webm", "video/x-matroska", "video/x-msvideo",
    "application/octet-stream",   # many servers serve video as this
}


def _download_video(url: str, max_bytes: int) -> bytes:
    """Streaming download of a remote video file with size guard."""
    try:
        head = req_lib.head(url, timeout=10, allow_redirects=True)
        cl = int(head.headers.get("content-length", 0))
        if cl and cl > max_bytes:
            raise ValueError(
                f"Remote file is {cl // (1024 * 1024)} MB — exceeds {max_bytes // (1024 * 1024)} MB limit"
            )
    except req_lib.RequestException:
        pass   # some servers don't respond to HEAD; proceed with GET

    resp = req_lib.get(url, stream=True, timeout=60, allow_redirects=True)
    resp.raise_for_status()

    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(chunk_size=65_536):
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(
                f"Download exceeded {max_bytes // (1024 * 1024)} MB limit after {total // (1024 * 1024)} MB"
            )

    return b"".join(chunks)


@router.post(
    "/video-url",
    summary="Video vehicle detection — fetch from URL",
    description=(
        "Provide an HTTP/HTTPS URL to a video file (MP4, AVI, MOV, WebM, MKV). "
        "The server downloads the file then runs the same full 9-model pipeline "
        "as a file upload.\n\n"
        "**Use cases:**\n"
        "- Footage hosted on NAS / NVR web interfaces\n"
        "- Dropbox (`?dl=1`), Google Drive export links\n"
        "- Any direct HTTP/HTTPS URL that resolves to a video file\n\n"
        "YouTube watch pages are **not** supported — use direct download links only. "
        "Max download size is 200 MB."
    ),
)
async def detect_video_url(
    url:             str   = Form(...,   description="HTTP/HTTPS URL to a video file"),
    sample_fps:      float = Form(2.0,   description="Frames per second to sample (0.5–4.0)"),
    max_frames:      int   = Form(100,   description="Max frames to extract (10–200)"),
    max_best_frames: int   = Form(12,    description="Max best frames to return (5–30)"),
    save_training:   bool  = Form(True,  description="Auto-save vehicle frames as training data"),
) -> dict:
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="URL is required")

    from urllib.parse import urlparse
    scheme = urlparse(url).scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported URL scheme '{scheme}'. Only http:// and https:// are allowed.",
        )

    sample_fps      = max(0.5, min(4.0,  sample_fps))
    max_frames      = max(10,  min(200,  max_frames))
    max_best_frames = max(5,   min(30,   max_best_frames))

    logger.info(f"[video:url] downloading '{url[:80]}'  fps={sample_fps}  max={max_frames}")

    def _download_and_process() -> dict:
        data = _download_video(url, MAX_VIDEO_BYTES)
        logger.info(f"[video:url] downloaded {len(data) // 1024} KB from '{url[:60]}'")
        return process_video(
            data,
            sample_fps=sample_fps,
            max_frames=max_frames,
            max_best_frames=max_best_frames,
            save_training=save_training,
        )

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_download_and_process),
            timeout=_URL_DOWNLOAD_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Download + processing timed out after {_URL_DOWNLOAD_TIMEOUT_S}s.",
        )
    except req_lib.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not download video: HTTP {exc.response.status_code} from remote server",
        ) from exc
    except (req_lib.ConnectionError, req_lib.Timeout) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not reach URL: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc

    result["source_url"] = url
    logger.info(
        f"[video:url] done — {result['vehicle_frames']} vehicle frames  "
        f"{result['unique_vehicle_count']} unique  {result['processing_time_seconds']}s"
    )
    return result


# ── /detect/stream — live URL ─────────────────────────────────────────────────

@router.post(
    "/stream",
    summary="Live stream vehicle detection — RTSP / HLS / MJPEG / RTMP",
    description=(
        "Paste a live stream URL to capture frames and run the full 9-model "
        "detection pipeline in real time.\n\n"
        "**Supported protocols:**\n"
        "- `rtsp://user:pass@192.168.1.100:554/stream1` — IP/DVR cameras\n"
        "- `http://host/stream.m3u8` — HLS streams\n"
        "- `http://host/mjpg/video.mjpg` — MJPEG streams\n"
        "- `rtmp://host/live/stream` — RTMP feeds\n\n"
        "The server opens the stream, captures `max_frames` sampled frames, "
        "runs the pipeline, and closes the connection.\n\n"
        "**Recommended gate-camera settings:**\n"
        "- `sample_fps=2`, `max_frames=60` (≈ 30 s of footage)\n"
        "- `max_best_frames=12`\n\n"
        "Detected vehicle frames are auto-saved as training data."
    ),
)
async def detect_stream(
    url:             str   = Form(...,   description="Live stream URL (RTSP/HLS/MJPEG/RTMP)"),
    sample_fps:      float = Form(2.0,   description="Frames per second to capture (0.5–4.0)"),
    max_frames:      int   = Form(60,    description="Max frames to capture (10–150)"),
    max_best_frames: int   = Form(12,    description="Max best frames to return (5–30)"),
    save_training:   bool  = Form(True,  description="Auto-save vehicle frames as training data"),
    connect_timeout: float = Form(12.0,  description="Stream connect timeout in seconds (5–30)"),
) -> dict:
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Stream URL is required")

    sample_fps      = max(0.5, min(4.0,  sample_fps))
    max_frames      = max(10,  min(150,  max_frames))
    max_best_frames = max(5,   min(30,   max_best_frames))
    connect_timeout = max(5.0, min(30.0, connect_timeout))

    logger.info(
        f"[video:stream] url='{url[:80]}'  fps={sample_fps}  "
        f"max={max_frames}  timeout={connect_timeout}s"
    )

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                process_stream, url,
                sample_fps=sample_fps, max_frames=max_frames,
                max_best_frames=max_best_frames, save_training=save_training,
                connect_timeout=connect_timeout,
            ),
            timeout=STREAM_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Stream processing timed out after {STREAM_TIMEOUT_S}s. "
                   "Try reducing max_frames or check the stream URL.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc

    logger.info(
        f"[video:stream] done — {result['vehicle_frames']} vehicle frames  "
        f"{result['unique_vehicle_count']} unique  {result['processing_time_seconds']}s"
    )
    return result


# ── /detect/video-source — universal intake (YouTube Live, Stream, File URL) ──

from modules.source_resolver import detect_source_type
from modules.url_safety import is_url_safe
from modules.youtube_resolver import resolve_youtube_live


@router.post(
    "/video-source",
    summary="Universal video source detection (YouTube Live, Stream, File URL)",
    description=(
        "Paste any video URL (YouTube Live stream, RTSP/HLS stream, or direct MP4/MKV file URL). "
        "The server automatically detects the source type, resolves YouTube Live to direct HLS, "
        "verifies URL safety against SSRF, captures frames, runs the full AI pipeline, "
        "and returns decision results."
    ),
)
async def detect_video_source(
    url:             str   = Form(...,   description="YouTube Live URL, Stream URL, or File URL"),
    sample_fps:      float = Form(2.0,   description="Frames per second to capture (0.5–4.0)"),
    max_frames:      int   = Form(60,    description="Max frames to capture/sample (10–150)"),
    max_best_frames: int   = Form(12,    description="Max best frames to return (5–30)"),
    save_training:   bool  = Form(True,  description="Auto-save vehicle frames as training data"),
    connect_timeout: float = Form(15.0,  description="Stream connect timeout in seconds (5–30)"),
) -> dict:
    url_clean = url.strip()
    if not url_clean:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="URL is required")

    # Safety check
    safe, reason = is_url_safe(url_clean)
    if not safe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"URL blocked: {reason}")

    source_type = detect_source_type(url_clean)
    logger.info(f"[video:source] detected type '{source_type}' for '{url_clean[:80]}'")

    if source_type == "youtube":
        try:
            resolved = await asyncio.to_thread(resolve_youtube_live, url_clean)
            logger.info(f"[video:source] resolved YouTube Live -> HLS: {resolved.resolved_url[:80]}")
            # Feed direct HLS into stream processor
            res = await detect_stream(
                url=resolved.resolved_url,
                sample_fps=sample_fps,
                max_frames=max_frames,
                max_best_frames=max_best_frames,
                save_training=save_training,
                connect_timeout=connect_timeout,
            )
            res["source_type"] = "youtube_live"
            res["source_resolved"] = True
            res["original_url"] = url_clean
            return res
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    elif source_type == "stream":
        res = await detect_stream(
            url=url_clean,
            sample_fps=sample_fps,
            max_frames=max_frames,
            max_best_frames=max_best_frames,
            save_training=save_training,
            connect_timeout=connect_timeout,
        )
        res["source_type"] = "stream"
        res["source_resolved"] = True
        res["original_url"] = url_clean
        return res

    elif source_type == "video_file":
        res = await detect_video_url(
            url=url_clean,
            sample_fps=sample_fps,
            max_frames=max_frames,
            max_best_frames=max_best_frames,
            save_training=save_training,
        )
        res["source_type"] = "video_file"
        res["source_resolved"] = True
        res["original_url"] = url_clean
        return res

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown or unsupported video source URL format. Provide YouTube Live, RTSP/HLS stream, or direct video file URL.",
        )

