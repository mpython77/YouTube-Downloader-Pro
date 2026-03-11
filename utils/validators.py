"""
YouTube Downloader Pro — URL Validators

URL validation and sanitization functions.
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Optional

from config import SUPPORTED_DOMAINS


def is_valid_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube URL.

    Args:
        url: URL string to validate.

    Returns:
        True if the URL is a valid YouTube URL.
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        return False

    if not parsed.netloc:
        return False

    # Check domain
    domain = parsed.netloc.lower()
    if not any(domain == d or domain.endswith("." + d) for d in SUPPORTED_DOMAINS):
        return False

    # youtu.be short URL
    if "youtu.be" in domain:
        return len(parsed.path) > 1

    # youtube.com/watch?v=...
    if "/watch" in parsed.path:
        params = parse_qs(parsed.query)
        return "v" in params and len(params["v"][0]) == 11

    # youtube.com/shorts/..., /live/..., /embed/...
    valid_paths = ("/shorts/", "/live/", "/embed/", "/v/", "/playlist")
    if any(parsed.path.startswith(p) for p in valid_paths):
        return True

    return False


def is_playlist_url(url: str) -> bool:
    """Check if the URL is a playlist URL.

    Args:
        url: URL to check.

    Returns:
        True if the URL is a playlist.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # /playlist?list=...
        if "/playlist" in parsed.path and "list" in params:
            return True

        # watch?v=...&list=...
        if "list" in params:
            return True

    except Exception:
        pass

    return False


def extract_video_id(url: str) -> Optional[str]:
    """Extract the video ID from a YouTube URL.

    Args:
        url: YouTube URL.

    Returns:
        Video ID or None.
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)

        # youtu.be/VIDEO_ID
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/")[:11]

        # youtube.com/watch?v=VIDEO_ID
        params = parse_qs(parsed.query)
        if "v" in params:
            return params["v"][0][:11]

        # youtube.com/shorts/VIDEO_ID, /embed/VIDEO_ID
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] in ("shorts", "embed", "v", "live"):
            return path_parts[1][:11]

    except Exception:
        pass

    return None


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize a filename by removing forbidden characters.

    Args:
        filename: Original filename.
        max_length: Maximum allowed length.

    Returns:
        Sanitized filename.
    """
    if not filename:
        return "untitled"

    # Windows forbidden characters
    forbidden = r'<>:"/\\|?*'
    for char in forbidden:
        filename = filename.replace(char, "")

    # Remove control characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

    # Strip leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Enforce maximum length
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip(". ")

    return filename or "untitled"
