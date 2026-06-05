"""
YouTube resolver — uses yt-dlp to extract direct HLS stream URLs from YouTube Live/Watch pages.
"""
from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache for resolved stream URLs
_yt_cache: dict[str, tuple[str, float]] = {}


@dataclass
class ResolvedSource:
    source_type:  str
    original_url: str
    resolved_url: str
    expires_at:   float


def resolve_youtube_live(url: str) -> ResolvedSource:
    """
    Resolves a YouTube URL to a direct HLS (.m3u8) or playable stream URL using yt-dlp.
    Caches the result in memory for stream_resolve_cache_ttl seconds.
    """
    url_clean = url.strip()
    now = time.time()

    # Check cache
    if url_clean in _yt_cache:
        cached_url, exp = _yt_cache[url_clean]
        if now < exp:
            logger.info(f"[youtube] cache hit for '{url_clean[:60]}'")
            return ResolvedSource(
                source_type="youtube_live",
                original_url=url_clean,
                resolved_url=cached_url,
                expires_at=exp,
            )
        else:
            del _yt_cache[url_clean]

    if not settings.youtube_resolver_enabled:
        raise ValueError("YouTube resolver is disabled in configuration")

    logger.info(f"[youtube] resolving direct stream URL for '{url_clean[:60]}'")

    # yt-dlp command to get best m3u8 or direct stream URL
    cmd = [
        "yt-dlp",
        "--get-url",
        "--format", "best[protocol^=m3u8]/best",
        "--no-playlist",
        "--no-warnings",
        url_clean,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.yt_dlp_timeout_seconds,
            check=True,
        )
        resolved_url = proc.stdout.strip()
        if not resolved_url:
            raise ValueError("yt-dlp returned empty URL")
    except subprocess.TimeoutExpired as exc:
        logger.error(f"[youtube] yt-dlp timed out after {settings.yt_dlp_timeout_seconds}s")
        raise ValueError("YouTube stream resolution timed out") from exc
    except subprocess.CalledProcessError as exc:
        logger.error(f"[youtube] yt-dlp failed: {exc.stderr.strip()}")
        raise ValueError(f"Could not resolve YouTube stream: {exc.stderr.strip()}") from exc
    except Exception as exc:
        logger.error(f"[youtube] unexpected error: {exc}")
        raise ValueError(f"YouTube stream resolution failed: {exc}") from exc

    ttl = settings.stream_resolve_cache_ttl
    expires_at = now + ttl
    _yt_cache[url_clean] = (resolved_url, expires_at)

    logger.info(f"[youtube] successfully resolved stream URL (TTL {ttl}s)")
    return ResolvedSource(
        source_type="youtube_live",
        original_url=url_clean,
        resolved_url=resolved_url,
        expires_at=expires_at,
    )
