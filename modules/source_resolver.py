"""
Source resolver — detects URL type (YouTube, stream, video file, or unknown).
"""
from __future__ import annotations

import urllib.parse


def detect_source_type(url: str) -> str:
    """
    Returns 'youtube', 'stream', 'video_file', or 'unknown'.
    """
    u = url.strip().lower()
    parsed = urllib.parse.urlparse(u)

    # 1. YouTube check
    domain = parsed.hostname or ""
    if any(d in domain for d in ("youtube.com", "youtu.be", "youtube-nocookie.com")):
        return "youtube"

    # 2. Stream check
    if u.startswith(("rtsp://", "rtsps://", "rtmp://", "rtmps://")):
        return "stream"
    path = parsed.path or ""
    if path.endswith((".m3u8", ".mjpg", ".mjpeg")):
        return "stream"

    # 3. Video file check
    if path.endswith((".mp4", ".mov", ".webm", ".mkv", ".avi")):
        return "video_file"

    return "unknown"
