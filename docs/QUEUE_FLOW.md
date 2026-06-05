# Queue flow

Two BullMQ-related pipelines coexist with a **Python-only** async queue inside the detector.

## 1. Video upload (async)

**Path:** server → BullMQ → worker → detector HTTP → Postgres

1. Client uploads video; server writes a `video_jobs` row (`QUEUED`) and enqueues on the **`video-processing`** queue (`server/src/infrastructure/queue/video-processing-queue.ts`).
2. **`video-processing-worker.ts`** consumes the job, POSTs multipart form data to `DETECTOR_URL` `/detect/video`, then updates the same job row (`DONE` / `FAILED`) with the JSON result.

**Producer:** `enqueueVideoJob` in `video-processing-queue.ts`.  
**Consumer:** `startVideoWorker` in `workers/video-processing-worker.ts`.

**Requires `REDIS_URL`:** If unset, the video worker does not start and `POST .../upload/video` returns **503** with `VIDEO_QUEUE_UNAVAILABLE` (same ergonomics as the live detection queue). Local dev: `REDIS_URL=redis://localhost:6379`. Docker Compose sets `REDIS_URL=redis://redis:6379` for `server` and `detector`.

## 2. Live detection events (Redis / BullMQ)

**Path:** detector → Redis → worker → decision engine → audit (Postgres) → Socket.IO

1. After the full detector pipeline, Python may push a structured JSON event to the list key **`securityos:detection_events`** (`detector/modules/event_emitter.py`).
2. **`redis-detection-events-worker.ts`** consumes jobs, runs **`decisionEngine.evaluate`**, appends **`auditLog`** (Postgres), and emits **`gate-event`** on Socket.IO to `tenant:{tenant_id}`.

**Requires `REDIS_URL` on the Node side:** If unset, the worker does not start (no Redis connection for this queue).

**Producer:** Python `emit_detection_event` / `emit_from_vehicle_result`.  
**Consumer:** `startDetectionWorker` in `workers/redis-detection-events-worker.ts` (shutdown: `stopDetectionWorker` in `server/src/index.ts`).

## 3. In-process HTTP detection queue (dev / hybrid)

**Path:** `POST /api/.../events/detection` → in-memory queue → timer worker → decision → hybrid audit

- **`in-process-detection-worker.ts`** polls `detection-queue.ts` on an interval; this is separate from BullMQ and Redis.
- Started from **`app.ts`** alongside the video worker (same as before the `workers/` folder move).

## 4. Detector internal async (`/detect/async`)

- Implemented in **`detector/modules/job_queue.py`** (asyncio queue + thread pool). **Not** BullMQ; no change when reorganizing Node workers.

## Startup note

The HTTP server starts **both** the in-process detection timer and the BullMQ video worker when `app` loads, and starts **again** the Redis detection worker and video worker when the HTTP listener comes up in `index.ts` — behavior preserved from the pre-refactor layout (including duplicate video worker registration).

## Code map

| Concern | Location |
|---------|----------|
| Video job enqueue | `server/src/infrastructure/queue/video-processing-queue.ts` |
| Video consumer | `server/src/workers/video-processing-worker.ts` |
| Live event Redis connection + queue stats helper | `server/src/infrastructure/queue/detection-events-queue.ts` |
| Live event consumer | `server/src/workers/redis-detection-events-worker.ts` |
| In-process consumer | `server/src/workers/in-process-detection-worker.ts` |
