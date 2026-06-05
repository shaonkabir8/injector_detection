"""
Vehicle Detector — FastAPI entry point
Bangladesh Brick Kiln Gate Detection System — 9-Model Pipeline
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

from config import settings
from routers.health    import router as health_router
from routers.detect    import router as detect_router
from routers.queue     import router as queue_router
from routers.feedback  import router as feedback_router
from routers.video     import router as video_router
from routers.audit     import router as audit_router
from modules.job_queue import startup as queue_startup, shutdown as queue_shutdown

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

base_path = settings.base_path.rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await queue_startup()
    logger.info("[startup] Job queue worker started")
    yield
    await queue_shutdown()
    logger.info("[shutdown] Job queue worker stopped")


app = FastAPI(
    title="Brick Kiln Gate — 9-Model Vehicle Detection API",
    description=(
        "**Bangladesh Brick Kiln Gate — 9-Model Detection Pipeline**\n\n"
        "| Model | Role | Method |\n"
        "|---|---|---|\n"
        "| **A** | Image Quality Checker | Laplacian blur + brightness + contrast |\n"
        "| **B** | YOLO Vehicle Detector | YOLOv8n COCO fast pass |\n"
        "| **C** | Second Detector (Fusion) | TTA augmented pass, auto-triggered if B conf<0.55 |\n"
        "| **D** | Vehicle Subtype Classifier | 7-feature scoring matrix on vehicle crop |\n"
        "| **E** | Cargo Area Segmenter | K-means + edge fusion → binary cargo mask |\n"
        "| **F** | Load Classifier | Texture analysis on cargo mask → Empty/Partial/Full |\n"
        "| **G** | Material Classifier | HSV colour-signature → Bricks/Clay/Coal/Sand |\n"
        "| **H** | Plate Detector + OCR | OpenCV geometric locator + EasyOCR |\n"
        "| **I** | Confidence/Review Gate | Aggregate all scores → Pass/Review/Reject |\n\n"
        "**Primary endpoints:**\n\n"
        "- `POST /detect/full` — All 9 models, cache-aware\n"
        "- `POST /detect/async` — Submit job to Redis-backed async queue\n"
        "- `GET  /detect/queue/{job_id}` — Poll async job result\n"
        "- `GET  /detect/stats` — Cache hit-rate + usage counters\n"
    ),
    version="4.0.0",
    docs_url=f"{base_path}/docs",
    redoc_url=f"{base_path}/redoc",
    openapi_url=f"{base_path}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)")
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )


app.include_router(health_router,   prefix=base_path)
app.include_router(detect_router,   prefix=base_path)
app.include_router(queue_router,    prefix=base_path)
app.include_router(feedback_router, prefix=base_path)
app.include_router(video_router,    prefix=base_path)
app.include_router(audit_router,    prefix=base_path)

os.makedirs("feedback_dataset/video_frames", exist_ok=True)
app.mount(f"{base_path}/frames", StaticFiles(directory="feedback_dataset/video_frames"), name="frames")

@app.get("/", include_in_schema=False)
async def root():
    # The detector service is an API only. In local/dev it often runs alongside a
    # separate frontend that lives on a different port.
    return {
        "service": "brickify-detector",
        "ok": True,
        "base_path": base_path,
        "docs": f"{base_path}/docs",
        "healthz": f"{base_path}/healthz",
        "hint": "The web UI is served by the frontend service; this port exposes the detector API only.",
    }


@app.get("/detection", include_in_schema=False)
async def mistaken_ui_path():
    # Common confusion: `/detection` is a frontend SPA route, not an API route.
    # Redirect to the API docs so the user gets something useful.
    return RedirectResponse(url=f"{base_path}/docs", status_code=307)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        access_log=False,
    )
