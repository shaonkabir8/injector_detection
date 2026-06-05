"""
URL safety gate — blocks private/internal IPs and local file access.
"""
from __future__ import annotations

import ipaddress
import socket
import urllib.parse


def is_url_safe(url: str) -> tuple[bool, str]:
    """
    Checks if a URL is safe to fetch (public IP, http/https/rtsp/rtmp).
    Returns (is_safe, error_reason).
    """
    u = url.strip().lower()
    parsed = urllib.parse.urlparse(u)

    scheme = parsed.scheme
    if scheme not in ("http", "https", "rtsp", "rtsps", "rtmp", "rtmps"):
        return False, f"Unsupported scheme '{scheme}'"

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid hostname"

    # Block obvious localnames
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False, "Localhost access blocked"

    # Try resolving IP to check against private ranges
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            return False, f"Access to private IP ({ip}) blocked"
    except Exception as exc:
        # If DNS fails, let caller handle or fail``
        pass

    return True, ""
