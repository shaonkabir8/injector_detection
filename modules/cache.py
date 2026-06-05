"""
Redis Cache Module
==================
Transparent Redis cache with automatic fallback to fakeredis (in-memory)
when no REDIS_URL is configured.

In production: set REDIS_URL=redis://host:6379/0
In development: leave REDIS_URL empty — fakeredis starts automatically,
                no Redis server process required.

Public API
──────────
  cache.get_result(mode, image_bytes) → dict | None
  cache.set_result(mode, image_bytes, result_dict)
  cache.increment(key) → int
  cache.get_int(key) → int
  cache.get_stats() → dict
  cache.flush_results() → int   # clear only detection results
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import date
from typing import Any, Optional

from config import settings

logger = logging.getLogger(__name__)

# ── Redis client singleton ────────────────────────────────────────────────────

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    if settings.redis_url:
        try:
            import redis
            _client = redis.from_url(settings.redis_url, decode_responses=True)
            _client.ping()
            logger.info(f"[cache] Connected to Redis at {settings.redis_url}")
        except Exception as exc:
            logger.warning(f"[cache] Redis connection failed ({exc}) — falling back to fakeredis")
            _client = None

    if _client is None:
        try:
            import fakeredis
            _client = fakeredis.FakeRedis(decode_responses=True)
            logger.info("[cache] Using fakeredis (in-memory, no server required)")
        except ImportError:
            logger.error("[cache] Neither redis nor fakeredis available — caching disabled")
            _client = None

    return _client


# ── Key helpers ───────────────────────────────────────────────────────────────

def _image_hash(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()


def _result_key(mode: str, image_hash: str) -> str:
    return f"cache:result:{mode}:{image_hash}"


def _today_key() -> str:
    return f"stats:detections:{date.today().isoformat()}"


# ── Public cache API ──────────────────────────────────────────────────────────

class _Cache:
    def get_result(self, mode: str, image_bytes: bytes) -> Optional[dict]:
        r = _get_client()
        if r is None:
            return None
        try:
            key  = _result_key(mode, _image_hash(image_bytes))
            data = r.get(key)
            if data:
                r.incr("stats:cache_hits")
                logger.info(f"[cache] HIT  {key[:40]}…")
                return json.loads(data)
            r.incr("stats:cache_misses")
            logger.debug(f"[cache] MISS {key[:40]}…")
            return None
        except Exception as exc:
            logger.warning(f"[cache] get_result error: {exc}")
            return None

    def set_result(self, mode: str, image_bytes: bytes, result: dict) -> bool:
        r = _get_client()
        if r is None:
            return False
        try:
            key = _result_key(mode, _image_hash(image_bytes))
            r.setex(key, settings.cache_result_ttl, json.dumps(result))
            logger.info(f"[cache] SET  {key[:40]}… ttl={settings.cache_result_ttl}s")
            return True
        except Exception as exc:
            logger.warning(f"[cache] set_result error: {exc}")
            return False

    def increment(self, key: str) -> int:
        r = _get_client()
        if r is None:
            return 0
        try:
            return int(r.incr(key))
        except Exception:
            return 0

    def get_int(self, key: str, default: int = 0) -> int:
        r = _get_client()
        if r is None:
            return default
        try:
            v = r.get(key)
            return int(v) if v is not None else default
        except Exception:
            return default

    def record_detection(self) -> dict:
        """Increment both all-time and today counters. Returns usage dict."""
        total = self.increment("stats:detections:total")
        today = self.increment(_today_key())
        return {"total": total, "today": today}

    def get_stats(self) -> dict:
        r = _get_client()
        if r is None:
            return {"available": False}
        try:
            hits   = self.get_int("stats:cache_hits")
            misses = self.get_int("stats:cache_misses")
            total  = hits + misses
            return {
                "available": True,
                "backend": "redis" if settings.redis_url else "fakeredis",
                "cache_hits": hits,
                "cache_misses": misses,
                "hit_rate": round(hits / total, 4) if total > 0 else 0.0,
                "detections_total": self.get_int("stats:detections:total"),
                "detections_today": self.get_int(_today_key()),
                "result_ttl_seconds": settings.cache_result_ttl,
                "free_tier_daily_limit": settings.saas_free_daily_limit,
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    # ── Job state (used by job_queue.py) ──────────────────────────────────────

    def set_job(self, job_id: str, data: dict) -> None:
        r = _get_client()
        if r is None:
            return
        try:
            r.setex(f"job:{job_id}", settings.job_ttl, json.dumps(data))
            # Keep a sorted-set index of recent jobs (score = epoch)
            r.zadd("jobs:index", {job_id: time.time()})
            # Trim to last 200 jobs
            r.zremrangebyrank("jobs:index", 0, -201)
        except Exception as exc:
            logger.warning(f"[cache] set_job error: {exc}")

    def get_job(self, job_id: str) -> Optional[dict]:
        r = _get_client()
        if r is None:
            return None
        try:
            data = r.get(f"job:{job_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def list_jobs(self, limit: int = 20) -> list[dict]:
        r = _get_client()
        if r is None:
            return []
        try:
            ids   = r.zrevrange("jobs:index", 0, limit - 1)
            jobs  = []
            for jid in ids:
                raw = r.get(f"job:{jid}")
                if raw:
                    job = json.loads(raw)
                    job["job_id"] = jid
                    jobs.append(job)
            return jobs
        except Exception:
            return []

    def flush_results(self) -> int:
        """Delete all cached detection results. Returns count deleted."""
        r = _get_client()
        if r is None:
            return 0
        try:
            keys = r.keys("cache:result:*")
            if keys:
                return r.delete(*keys)
            return 0
        except Exception:
            return 0


cache = _Cache()
