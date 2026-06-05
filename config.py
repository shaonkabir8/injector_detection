import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = int(os.environ.get("PORT", 5000))
    log_level: str = "info"
    base_path: str = os.environ.get("BASE_PATH", "/detect")

    yolo_model: str = "yolov8n.pt"
    yolo_confidence: float = 0.25
    yolo_iou: float = 0.45

    plate_min_confidence: float = 0.2
    plate_min_width: int = 50
    plate_min_height: int = 15
    plate_aspect_ratio_min: float = 1.5
    plate_aspect_ratio_max: float = 8.0

    load_iou_threshold: float = 0.10
    load_min_item_confidence: float = 0.20

    load_visual_empty_threshold: float = 0.05
    load_visual_full_threshold: float = 0.40
    load_visual_edge_weight: float = 0.45
    load_visual_color_weight: float = 0.40
    load_visual_blob_weight: float = 0.15
    load_visual_edge_max: float = 0.22
    load_visual_color_max: float = 55.0
    load_visual_blob_max: float = 8.0
    load_visual_skip_bottom: float = 0.22
    load_visual_skip_top: float = 0.05

    max_image_bytes: int = 20 * 1024 * 1024

    # ── Redis ────────────────────────────────────────────────────────────────
    # Set REDIS_URL in production (e.g. redis://localhost:6379/0)
    # If unset, fakeredis (in-memory) is used automatically — no server needed.
    redis_url: str = os.environ.get("REDIS_URL", "")

    # Cache TTL for detection results (seconds)
    cache_result_ttl: int = int(os.environ.get("CACHE_TTL", 900))   # 15 min

    # Job queue TTL (seconds) — how long to keep completed/failed jobs
    job_ttl: int = int(os.environ.get("JOB_TTL", 3600))             # 1 hour

    # SaaS daily detection limit per tier
    saas_free_daily_limit: int = int(os.environ.get("SAAS_FREE_DAILY_LIMIT", 100))

    # ── YouTube Live Resolver ────────────────────────────────────────────────
    youtube_resolver_enabled: bool = True
    yt_dlp_timeout_seconds: int = 20
    stream_resolve_cache_ttl: int = 600
    video_source_require_api_key: bool = False


settings = Settings()

