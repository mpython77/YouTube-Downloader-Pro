"""
YouTube Downloader Pro — Thumbnail Service

Asynchronous thumbnail loading with in-memory caching.
Retrieves thumbnail URL from VideoInfo (no duplicate extract_info calls).
"""

from __future__ import annotations

import logging
import threading
from io import BytesIO
from typing import Optional, Dict, Callable, Tuple

import requests
from PIL import Image, ImageTk

logger = logging.getLogger("YouTube Downloader Pro")

ThumbnailCallback = Callable[[str, ImageTk.PhotoImage], None]


class ThumbnailService:
    """Thumbnail loading and in-memory cache.

    Avoids downloading the same URL twice.
    """

    def __init__(self, size: Tuple[int, int] = (160, 90)):
        """
        Args:
            size: Thumbnail dimensions (width, height).
        """
        self._cache: Dict[str, ImageTk.PhotoImage] = {}
        self._lock = threading.Lock()
        self._size = size

    def get_thumbnail(
        self,
        url: str,
        thumbnail_url: str,
        callback: ThumbnailCallback,
    ) -> None:
        """Load a thumbnail asynchronously.

        If cached, the callback is invoked immediately.
        Otherwise, it is downloaded in a background thread.

        Args:
            url: Video URL (used as cache key).
            thumbnail_url: Thumbnail image URL.
            callback: Function called when loaded (url, image).
        """
        # Check cache
        with self._lock:
            if url in self._cache:
                callback(url, self._cache[url])
                return

        if not thumbnail_url:
            return

        thread = threading.Thread(
            target=self._load_async,
            args=(url, thumbnail_url, callback),
            daemon=True,
            name=f"Thumbnail-{url[:30]}",
        )
        thread.start()

    def _load_async(
        self,
        url: str,
        thumbnail_url: str,
        callback: ThumbnailCallback,
    ) -> None:
        """Download a thumbnail in a background thread."""
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()

            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img = img.resize(self._size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            with self._lock:
                self._cache[url] = photo

            callback(url, photo)
            logger.debug(f"Thumbnail loaded: {url}")

        except requests.RequestException as e:
            logger.warning(f"Thumbnail network error: {e}")
        except Exception as e:
            logger.error(f"Thumbnail error: {e}")

    def clear_cache(self) -> None:
        """Clear the thumbnail cache."""
        with self._lock:
            self._cache.clear()
        logger.debug("Thumbnail cache cleared")

    @property
    def cache_size(self) -> int:
        """Number of cached thumbnails."""
        with self._lock:
            return len(self._cache)
