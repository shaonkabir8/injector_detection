"""
Async Job Queue
===============
In-process asyncio job queue backed by the Redis cache module for state
persistence.  No external broker (Celery/RQ) required.

Job lifecycle:
  queued  →  processing  →  done
                         →  failed

How it works:
  - FastAPI startup registers a background worker coroutine.
  - POST /detect/async pushes a job onto the asyncio.Queue.
  - The worker coroutine picks it up, runs the detection in a thread pool
    (so it doesn't block the event loop), and writes the result to Redis.
  - Clients poll GET /detect/queue/{job_id} until status == "done" | "failed".

Thread safety: asyncio.Queue is not thread-safe across threads; all queue
operations happen on the main event-loop thread via enqueue().
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Optional

from modules.cache import cache

logger = logging.getLogger(__name__)

_queue: asyncio.Queue = asyncio.Queue()
_worker_task: Optional[asyncio.Task] = None


# ── Public API ────────────────────────────────────────────────────────────────

async def enqueue(
    mode: str,
    fn: Callable,
    *args: Any,
    image_filename: str = "unknown",
) -> str:
    """
    Add a detection job to the queue.

    Args:
        mode           : Detection mode label (e.g. "full", "validate")
        fn             : Callable that performs the detection (runs in threadpool)
        *args          : Arguments forwarded to fn
        image_filename : For display in the queue panel

    Returns:
        job_id (UUID string)
    """
    job_id = str(uuid.uuid4())
    job_record = {
        "status":    "queued",
        "mode":      mode,
        "filename":  image_filename,
        "created":   time.time(),
        "started":   None,
        "finished":  None,
        "result":    None,
        "error":     None,
        "queue_pos": _queue.qsize() + 1,
    }
    cache.set_job(job_id, job_record)
    await _queue.put((job_id, fn, args, job_record))
    logger.info(f"[queue] Enqueued job {job_id[:8]}… mode={mode} file={image_filename}")
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    """Return job status dict, or None if not found."""
    return cache.get_job(job_id)


def list_jobs(limit: int = 20) -> list[dict]:
    """Return the most recent `limit` jobs, newest first."""
    return cache.list_jobs(limit)


def queue_depth() -> int:
    return _queue.qsize()


# ── Background worker ─────────────────────────────────────────────────────────

async def _worker() -> None:
    logger.info("[queue] Worker started — waiting for jobs")
    while True:
        try:
            job_id, fn, args, record = await _queue.get()

            # Mark as processing
            record.update({"status": "processing", "started": time.time(), "queue_pos": 0})
            cache.set_job(job_id, record)
            logger.info(f"[queue] Processing {job_id[:8]}… mode={record['mode']}")

            try:
                # Run CPU-bound detection in a thread pool
                result = await asyncio.get_event_loop().run_in_executor(None, fn, *args)
                record.update({
                    "status":   "done",
                    "finished": time.time(),
                    "result":   result,
                    "error":    None,
                })
                logger.info(
                    f"[queue] Done    {job_id[:8]}… "
                    f"elapsed={record['finished'] - record['started']:.1f}s"
                )
            except Exception as exc:
                record.update({
                    "status":   "failed",
                    "finished": time.time(),
                    "error":    str(exc),
                })
                logger.error(f"[queue] Failed  {job_id[:8]}… {exc}")

            cache.set_job(job_id, record)
            _queue.task_done()

        except asyncio.CancelledError:
            logger.info("[queue] Worker cancelled")
            break
        except Exception as exc:
            logger.error(f"[queue] Worker loop error: {exc}")
            await asyncio.sleep(1)


async def startup() -> None:
    """Call from FastAPI lifespan or startup event."""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker())
        logger.info("[queue] Background worker task created")


async def shutdown() -> None:
    """Call from FastAPI shutdown event."""
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
    logger.info("[queue] Worker stopped")
