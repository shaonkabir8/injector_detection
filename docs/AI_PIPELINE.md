# Brickify Detector AI Pipeline

Canonical location: `docs/pipelines/AI_PIPELINE.md`. The detector service and model chain are **unchanged** by monorepo layout refactors; this document describes behavior and file layout under `detector/`.

## Purpose

`detector/` is the Python FastAPI AI service for Brickify SecurityOS. It receives gate camera images, videos, or stream URLs and returns vehicle, load, material, plate, validation, and final gate decision results.

Main goal: help a brick kiln guard decide quickly whether a vehicle should pass, be reviewed, or be rejected, without depending on paid cloud AI.

## Current Shape

The service is mounted under `BASE_PATH`, default `/detect`.

Core files:

- `detector/main.py` - FastAPI app, router wiring, queue startup/shutdown, CORS, logging.
- `detector/routers/detect.py` - image detection endpoints and full pipeline orchestration.
- `detector/routers/queue.py` - async image jobs, queue status, cache stats.
- `detector/routers/video.py` - uploaded video, remote video URL, and live stream processing.
- `detector/routers/feedback.py` - human correction capture for future training.
- `detector/modules/cache.py` - Redis cache with fakeredis fallback.
- `detector/modules/job_queue.py` - in-process asyncio worker queue.
- `detector/modules/video_processor.py` - frame sampling and best-frame selection.
- `detector/schemas/detection.py` - public response models.

## Pipeline

Current full image pipeline is a 9-model chain:

| Stage | Code | Role | Method |
|---|---|---|---|
| A | `quality_checker.py` | Image quality | Blur, brightness, contrast, overexposure |
| B | `vehicle_detector.py` | Vehicle detection | YOLOv8n COCO vehicle classes |
| C | `vehicle_detector.py` | Fusion pass | TTA only when confidence is low |
| D | `subtype_classifier.py` | Kiln vehicle subtype | Feature scoring on vehicle crop |
| E | `cargo_segmenter.py` | Cargo zone segmentation | K-means plus edge fusion |
| F | `load_detector.py` | Empty/partial/full | Texture, color variance, blobs, COCO override |
| G | `materials_detector.py` | Cargo material | HSV signature for bricks/clay/coal/sand |
| H | `plate_detector.py` | Plate detection/OCR | OpenCV geometry plus EasyOCR |
| I | `confidence_gate.py` | Final decision | Weighted score and review flags |

Flow:

1. Upload bytes are size-checked.
2. Image is decoded and resized to max side 1280.
3. Image quality is checked once.
4. YOLO detects broad vehicle classes.
5. Low-confidence detections trigger TTA fusion.
6. Vehicle subtypes are refined and non-kiln vehicles are filtered.
7. Each primary vehicle gets independent cargo, load, material, plate, validation, and gate results.
8. Result is cached by image hash.
9. Top-level response mirrors the first vehicle for backward compatibility, while `vehicles[]` holds multi-vehicle results.

## Public Endpoints

Image endpoints:

- `POST /detect/vehicle` - quality plus vehicle detection.
- `POST /detect/load` - cargo segmentation plus load result for best vehicle.
- `POST /detect/material` - cargo segmentation plus material result for best vehicle.
- `POST /detect/plate` - plate OCR over full image.
- `POST /detect/full` - full 9-stage pipeline for all primary vehicles.
- `POST /detect/validate` - full pipeline plus local fleet registry validation.
- `GET /detect/registry` - list fleet registry.
- `POST /detect/registry/reload` - hot reload local registry.

Async/cache endpoints:

- `POST /detect/async` - queue a full or validate job.
- `GET /detect/queue/{job_id}` - poll job result.
- `GET /detect/queue` - recent jobs.
- `GET /detect/stats` - cache and usage stats.
- `POST /detect/cache/flush` - clear cached detection results.

Video endpoints:

- `POST /detect/video` - upload video and process sampled frames.
- `POST /detect/video-url` - download and process direct HTTP/HTTPS video.
- `POST /detect/stream` - sample frames from live stream URLs.

Feedback endpoints:

- `POST /detect/feedback` - save corrected labels and source image.
- `GET /detect/feedback/stats` - feedback dataset summary.
- `GET /detect/feedback/export` - download JSONL corrections.

## Current Strengths

- Zero-cost core: local YOLOv8n, OpenCV heuristics, EasyOCR, Redis/fakeredis.
- Good offline/dev fallback: fakeredis works without a Redis server.
- Multi-vehicle aware: `vehicles[]` can represent several trucks in one frame.
- Cache-aware: repeated images avoid repeat inference.
- Async path exists: guards can submit and poll instead of blocking UI.
- Feedback loop exists: corrected labels are already persisted for future training.
- Video/stream support exists: can mine real kiln footage for better samples.
- Response schemas are stable and explicit through Pydantic.

## Current Risks

- The async queue is in-process. It is simple and free, but jobs disappear if the process restarts when fakeredis is used.
- CPU-bound inference can still saturate one server under load.
- `fakeredis` is memory-only and not production durable.
- `POST /detect/video-url` and `/detect/stream` accept external URLs. This needs stronger SSRF protection before public production use.
- `/detect/cache/flush` has no auth guard.
- CORS is open to all origins.
- OCR can be slow and brittle on dusty, angled, low-light Bangladeshi plates.
- Thresholds are hard-coded or env-configured but not yet calibrated from measured kiln data.
- No visible model/version metadata is returned in detection responses.
- No structured request ID is included for tracing a gate event across frontend, server, and detector.

## Zero-Cost Production Plan

### Phase 1 - Make It Safe

Do first. Cheap. Big gain.

- Add an API key middleware for detector admin endpoints:
  - Protect `/detect/cache/flush`.
  - Protect `/detect/feedback/export`.
  - Protect registry reload.
- Restrict CORS by env:
  - `DETECTOR_ALLOWED_ORIGINS=http://localhost:5173,https://your-pwa-domain`.
- Add request IDs:
  - Accept `X-Request-ID`.
  - Generate one if missing.
  - Return it in all responses.
  - Log it in every module.
- Add structured JSON logging for production:
  - request id
  - endpoint
  - latency
  - image size
  - vehicle count
  - decision
  - cache hit/miss
- Add body/file guards:
  - Keep image max at 20 MB.
  - Keep video max at 200 MB or lower for low-RAM machines.
  - Reject unknown MIME types early.
- Harden URL inputs:
  - Block localhost, private IPs, link-local IPs, metadata IPs, and file URLs.
  - Allow only `http` and `https` for video URL.
  - Put stream support behind admin/internal network only.

### Phase 2 - Make It Smooth For Guards

Goal: fewer confusing results, better field UX.

- Return Bangla-friendly recommendation keys alongside English enum values:
  - `capture_hint_bn`
  - `decision_bn`
  - `reason_bn`
- Convert quality flags into guard actions:
  - `BLURRY` -> "ছবি ঝাপসা, আবার তুলুন"
  - `DARK` -> "আলো কম, ফ্ল্যাশ/লাইট দিন"
  - `OVEREXPOSED` -> "আলো বেশি, ক্যামেরা একটু ঘুরান"
  - `NO_PLATE` -> "নাম্বার প্লেট পরিষ্কার নয়"
- Add `next_action`:
  - `PROCEED`
  - `RECAPTURE`
  - `MANUAL_REVIEW`
  - `SCAN_QR`
- Add `debug_level` query or env flag:
  - Normal guard UI gets only useful fields.
  - Admin/debug mode gets module scores and flags.
- Add confidence bands:
  - `high`, `medium`, `low`
  - Easier for UI than raw float everywhere.

### Phase 3 - Make It Faster

Free speed wins before buying hardware.

- Use endpoint-specific short paths:
  - Keep `/vehicle`, `/plate`, `/load`, `/material` for UI steps that do not need full pipeline.
  - Use `/full` only after capture is accepted.
- Skip expensive work when early result is unusable:
  - If image quality is `REJECT`, return early unless `force=true`.
  - If no primary vehicle, skip cargo/material/plate.
- Add OCR short-circuit:
  - Run plate OCR only on vehicle crop.
  - Skip OCR if bbox is too small or quality too poor.
  - Cache OCR by cropped plate hash when bbox exists.
- Tune image resize:
  - Use max side 960 for quick preview.
  - Use 1280 only for final validation/OCR.
- Keep YOLO model loaded at startup:
  - Warm model once during lifespan startup.
  - Avoid first-request latency surprise.
- Add simple concurrency limit:
  - One or two inference jobs per CPU-only machine.
  - Return queue position for overload.

### Phase 4 - Scale On One Machine

Still zero-cost. No cloud needed.

- Use real Redis in production:
  - `REDIS_URL=redis://localhost:6379/0`
  - Keeps cache/jobs across worker processes.
- Run multiple Uvicorn workers only if memory allows:
  - CPU-only small VPS: start with 1 worker.
  - Better box: 2 workers.
  - Do not over-fork if each worker loads YOLO and OCR models.
- Split process roles:
  - API process handles upload, validation, polling.
  - Worker process handles inference jobs.
  - Same Redis, no Celery needed at first.
- Use file-based queue recovery if Redis unavailable:
  - Append queued jobs to disk.
  - Mark done/failed.
  - Requeue pending jobs on startup.
- Add cache namespaces:
  - `vehicle:{hash}`
  - `full:{hash}`
  - `validate:{expected_plate}:{hash}`
  - `plate_crop:{hash}`

### Phase 5 - Improve Accuracy Without Paid Services

Use real kiln data already captured by feedback/video.

- Build a weekly review set:
  - 50 good images
  - 50 bad images
  - 50 plates
  - 50 loaded/unloaded vehicle crops
- Track accuracy manually in CSV/JSONL:
  - vehicle subtype accuracy
  - plate exact match
  - plate partial match
  - load class accuracy
  - material class accuracy
  - gate decision accuracy
- Calibrate thresholds from local samples:
  - quality blur thresholds
  - cargo fill thresholds
  - load visual thresholds
  - confidence gate weights
- Add per-kiln camera profiles:
  - `camera_id`
  - side angle
  - day/night
  - expected vehicle lane position
  - tuned crop fractions
- Fine-tune YOLO only when enough labels exist:
  - Start with 300-500 labeled kiln vehicle images.
  - Use existing feedback/video frames.
  - Train locally on free GPU options only when available, or on a borrowed machine.
- Keep heuristics as fallback:
  - Fine-tuned model can fail.
  - Current OpenCV/load/material logic remains useful.

## Production Readiness Checklist

Minimum for first production pilot:

- `REDIS_URL` set to local Redis.
- `DETECTOR_API_KEY` required for admin endpoints.
- CORS restricted.
- Request ID logging enabled.
- `/detect/healthz` monitored.
- Model warmup at startup.
- Cache stats visible.
- Queue depth visible.
- Upload limits enforced.
- Private URL/IP blocking for video URL and stream endpoints.
- Feedback capture enabled.
- Daily backup of `feedback_dataset/`.
- Daily backup of `vehicles.json` if still using local registry.

Nice next:

- Dockerfile with pinned Python version.
- `systemd` service for detector.
- Log rotation.
- `/detect/readyz` endpoint that checks model load and Redis.
- `/detect/version` endpoint with model name, code version, config snapshot.
- Lightweight smoke test script using one known image.

## Recommended Environment

Development:

```bash
BASE_PATH=/detect
PORT=5000
LOG_LEVEL=info
REDIS_URL=
CACHE_TTL=900
JOB_TTL=3600
```

Production pilot on one machine:

```bash
BASE_PATH=/detect
PORT=5000
LOG_LEVEL=info
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=900
JOB_TTL=86400
DETECTOR_API_KEY=change-this
DETECTOR_ALLOWED_ORIGINS=https://your-frontend-domain
```

## Target Architecture

Simple production shape:

```text
Guard PWA
  |
  | /api/*
  v
Node server
  |
  | /detect/full or /detect/async
  v
Python detector API
  |
  +-- Redis cache/jobs
  +-- YOLO/OpenCV/EasyOCR local inference
  +-- feedback_dataset JSONL/images
```

Scaled one-machine shape:

```text
Nginx
  |
  +-- frontend static/PWA
  +-- Node API
  +-- detector API
          |
          +-- Redis
          +-- one or more detector workers
          +-- local feedback dataset
```

## API Response Improvements

Add these fields without breaking current clients:

```json
{
  "request_id": "uuid",
  "pipeline_version": "4.0.0",
  "model_versions": {
    "vehicle": "yolov8n.pt",
    "ocr": "easyocr",
    "load": "opencv-heuristic-v1",
    "material": "hsv-signature-v1"
  },
  "next_action": "MANUAL_REVIEW",
  "decision_bn": "রিভিউ দরকার",
  "capture_hint_bn": "নাম্বার প্লেট পরিষ্কার করে আবার ছবি তুলুন"
}
```

This keeps the frontend stable while making guard UX smoother.

## Best Next Implementation Steps

Do in this order:

1. Add detector API key middleware for admin routes.
2. Add request ID middleware and structured logs.
3. Add `next_action` and Bangla hint fields to response schemas.
4. Add model warmup and `/detect/readyz`.
5. Harden `/video-url` and `/stream` against private/internal URLs.
6. Add Redis-required production mode:
   - dev can use fakeredis
   - production should warn or fail if Redis is missing
7. Add a smoke test script with one sample image.
8. Add weekly feedback export and accuracy report script.

## Caveman Summary

Pipeline good. Bones strong.

Need helmet:

- auth
- CORS
- request IDs
- Redis in prod
- URL hardening

Need smoother guard path:

- Bangla hints
- next action
- less debug noise
- faster reject/recapture

Need scale:

- cache hard
- queue hard
- limit concurrency
- split API and worker later

Need better brain:

- collect feedback
- measure accuracy
- tune thresholds
- fine-tune only after enough real kiln data
