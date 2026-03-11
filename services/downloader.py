"""
YouTube Downloader Pro — Download Service

Thread-safe yt-dlp wrapper — real pause/resume, concurrent downloads,
retry logic, duplicate detection, proper postprocessors.
"""

from __future__ import annotations

import os
import logging
import threading
import shutil
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any, Set

import yt_dlp

from models import (
    DownloadItem, DownloadStatus, DownloadFormat,
    DownloadProgress, VideoInfo,
)
from config import AppSettings
from utils.validators import sanitize_filename

logger = logging.getLogger("YouTube Downloader Pro")

# Type aliases
ProgressCallback = Callable[[DownloadItem, DownloadProgress], None]
CompletionCallback = Callable[[DownloadItem], None]
ErrorCallback = Callable[[DownloadItem, str], None]
AllCompleteCallback = Callable[[], None]


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available on the system PATH.

    Returns:
        True if FFmpeg is found.
    """
    return shutil.which("ffmpeg") is not None


class DownloadService:
    """Thread-safe download service.

    Features:
        - Thread-safe queue management (with Lock)
        - Real pause/resume (threading.Event)
        - Retry logic (automatic retries on failure)
        - Duplicate URL detection
        - Postprocessor conflict fixed
        - Single extract_info call (no duplicate fetches)
        - Playlist splitting into individual items
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._queue: List[DownloadItem] = []
        self._lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        self._cancel_event = threading.Event()
        self._is_running = False
        self._current_item: Optional[DownloadItem] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._url_set: Set[str] = set()  # For duplicate detection
        self._completed_count = 0
        self._failed_count = 0
        self._video_info_cache: Dict[str, VideoInfo] = {}  # Info cache

        # Callbacks
        self._on_progress: Optional[ProgressCallback] = None
        self._on_complete: Optional[CompletionCallback] = None
        self._on_error: Optional[ErrorCallback] = None
        self._on_queue_changed: Optional[Callable[[], None]] = None
        self._on_status_changed: Optional[Callable[[DownloadItem], None]] = None
        self._on_all_complete: Optional[AllCompleteCallback] = None

    # ========================================================
    # Properties
    # ========================================================

    @property
    def queue(self) -> List[DownloadItem]:
        """Return a copy of the queue (thread-safe)."""
        with self._lock:
            return list(self._queue)

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    @property
    def current_item(self) -> Optional[DownloadItem]:
        return self._current_item

    @property
    def queue_count(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for i in self._queue if i.status == DownloadStatus.PENDING)

    @property
    def completed_count(self) -> int:
        return self._completed_count

    @property
    def failed_count(self) -> int:
        return self._failed_count

    @property
    def has_ffmpeg(self) -> bool:
        return check_ffmpeg()

    # ========================================================
    # Callback Registration
    # ========================================================

    def set_callbacks(
        self,
        on_progress: Optional[ProgressCallback] = None,
        on_complete: Optional[CompletionCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        on_queue_changed: Optional[Callable[[], None]] = None,
        on_status_changed: Optional[Callable[[DownloadItem], None]] = None,
        on_all_complete: Optional[AllCompleteCallback] = None,
    ) -> None:
        """Register event callbacks."""
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error
        self._on_queue_changed = on_queue_changed
        self._on_status_changed = on_status_changed
        self._on_all_complete = on_all_complete

    # ========================================================
    # Video Info (with cache)
    # ========================================================

    def get_video_info(self, url: str) -> VideoInfo:
        """Fetch video metadata (with caching).

        Args:
            url: YouTube URL.

        Returns:
            VideoInfo object.

        Raises:
            Exception: yt-dlp errors.
        """
        # Check cache first
        if url in self._video_info_cache:
            logger.debug(f"Video info from cache: {url}")
            return self._video_info_cache[url]

        logger.info(f"Fetching video info: {url}")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "socket_timeout": 15,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_info = VideoInfo.from_yt_dlp(url, info)
            self._video_info_cache[url] = video_info
            return video_info

    def get_playlist_items(self, url: str) -> List[VideoInfo]:
        """Fetch metadata for all videos in a playlist.

        Args:
            url: Playlist URL.

        Returns:
            List of VideoInfo objects.
        """
        logger.info(f"Fetching playlist info: {url}")
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
            "socket_timeout": 15,
        }

        items = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and info.get("_type") == "playlist":
                for entry in info.get("entries", []):
                    if entry:
                        entry_url = entry.get("url", "")
                        if not entry_url.startswith("http"):
                            entry_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                        items.append(VideoInfo(
                            url=entry_url,
                            title=entry.get("title", "Unknown"),
                            duration=entry.get("duration", 0) or 0,
                        ))
        logger.info(f"Playlist: found {len(items)} videos")
        return items

    # ========================================================
    # Queue Management
    # ========================================================

    def add_to_queue(self, item: DownloadItem) -> bool:
        """Add an item to the queue (thread-safe, with duplicate check).

        Args:
            item: DownloadItem to add.

        Returns:
            True if added successfully, False if duplicate.
        """
        with self._lock:
            # Duplicate detection
            if item.url in self._url_set:
                logger.warning(f"Duplicate URL skipped: {item.url}")
                return False
            self._queue.append(item)
            self._url_set.add(item.url)

        logger.info(f"Added to queue: {item.title}")
        if self._on_queue_changed:
            self._on_queue_changed()
        return True

    def remove_from_queue(self, index: int) -> Optional[DownloadItem]:
        """Remove an item from the queue by index.

        Args:
            index: Item index.

        Returns:
            Removed item or None.
        """
        with self._lock:
            if 0 <= index < len(self._queue):
                item = self._queue.pop(index)
                self._url_set.discard(item.url)
                logger.info(f"Removed from queue: {item.title}")
                if self._on_queue_changed:
                    self._on_queue_changed()
                return item
        return None

    def clear_queue(self) -> None:
        """Clear the queue (excluding items currently downloading)."""
        with self._lock:
            kept = [
                item for item in self._queue
                if item.status == DownloadStatus.DOWNLOADING
            ]
            self._url_set = {item.url for item in kept}
            self._queue = kept
        logger.info("Queue cleared")
        if self._on_queue_changed:
            self._on_queue_changed()

    def move_in_queue(self, from_idx: int, to_idx: int) -> None:
        """Move an item within the queue."""
        with self._lock:
            if 0 <= from_idx < len(self._queue) and 0 <= to_idx < len(self._queue):
                item = self._queue.pop(from_idx)
                self._queue.insert(to_idx, item)
        if self._on_queue_changed:
            self._on_queue_changed()

    def is_duplicate(self, url: str) -> bool:
        """Check if a URL is already in the queue."""
        with self._lock:
            return url in self._url_set

    def retry_failed(self) -> int:
        """Reset all FAILED items back to PENDING.

        Returns:
            Number of items retried.
        """
        count = 0
        with self._lock:
            for item in self._queue:
                if item.status == DownloadStatus.FAILED:
                    item.status = DownloadStatus.PENDING
                    item.progress = 0.0
                    item.error_message = ""
                    count += 1
        if count > 0:
            logger.info(f"{count} failed download(s) re-queued")
            if self._on_queue_changed:
                self._on_queue_changed()
        return count

    def remove_completed(self) -> int:
        """Remove all COMPLETED items from the queue.

        Returns:
            Number of items removed.
        """
        with self._lock:
            before = len(self._queue)
            completed_urls = {i.url for i in self._queue if i.status == DownloadStatus.COMPLETED}
            self._queue = [i for i in self._queue if i.status != DownloadStatus.COMPLETED]
            self._url_set -= completed_urls
            removed = before - len(self._queue)
        if removed > 0:
            if self._on_queue_changed:
                self._on_queue_changed()
        return removed

    # ========================================================
    # Download Control
    # ========================================================

    def start(self) -> None:
        """Start processing the download queue."""
        if self._is_running:
            return

        self._is_running = True
        self._cancel_event.clear()
        self._pause_event.set()
        self._completed_count = 0
        self._failed_count = 0

        self._worker_thread = threading.Thread(
            target=self._process_queue, daemon=True, name="DownloadWorker"
        )
        self._worker_thread.start()
        logger.info("Download started")

    def pause(self) -> None:
        """Pause the current download."""
        if self._is_running and self._pause_event.is_set():
            self._pause_event.clear()
            if self._current_item:
                self._current_item.status = DownloadStatus.PAUSED
                if self._on_status_changed:
                    self._on_status_changed(self._current_item)
            logger.info("Download paused")

    def resume(self) -> None:
        """Resume the paused download."""
        if self._is_running and not self._pause_event.is_set():
            self._pause_event.set()
            if self._current_item:
                self._current_item.status = DownloadStatus.DOWNLOADING
                if self._on_status_changed:
                    self._on_status_changed(self._current_item)
            logger.info("Download resumed")

    def cancel(self) -> None:
        """Cancel all downloads."""
        self._cancel_event.set()
        self._pause_event.set()  # Unblock if paused
        self._is_running = False

        if self._current_item:
            self._current_item.status = DownloadStatus.CANCELLED
            if self._on_status_changed:
                self._on_status_changed(self._current_item)

        logger.info("Download cancelled")

    # ========================================================
    # Internal Processing
    # ========================================================

    def _process_queue(self) -> None:
        """Process the queue sequentially (worker thread)."""
        while self._is_running:
            # Find next PENDING item
            item = None
            with self._lock:
                for q_item in self._queue:
                    if q_item.status == DownloadStatus.PENDING:
                        item = q_item
                        break

            if item is None:
                break  # Queue empty

            if self._cancel_event.is_set():
                break

            self._current_item = item
            self._download_item_with_retry(item)
            self._current_item = None

        self._is_running = False
        logger.info(f"Finished: {self._completed_count} downloaded, {self._failed_count} failed")

        if self._on_all_complete:
            self._on_all_complete()

    def _download_item_with_retry(self, item: DownloadItem) -> None:
        """Download an item with automatic retry logic.

        Args:
            item: DownloadItem to download.
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            if self._cancel_event.is_set():
                return

            if attempt > 1:
                logger.info(f"Retry {attempt}/{self.MAX_RETRIES}: {item.title}")
                item.progress = 0.0
                item.status = DownloadStatus.DOWNLOADING
                if self._on_status_changed:
                    self._on_status_changed(item)
                # Wait before retrying
                import time
                time.sleep(self.RETRY_DELAY)

            success = self._download_item(item)
            if success:
                self._completed_count += 1
                return

        # All attempts failed
        self._failed_count += 1
        logger.error(f"All {self.MAX_RETRIES} attempts failed: {item.title}")

    def _download_item(self, item: DownloadItem) -> bool:
        """Download a single item.

        Args:
            item: DownloadItem to download.

        Returns:
            True if downloaded successfully.
        """
        item.status = DownloadStatus.DOWNLOADING
        if self._on_status_changed:
            self._on_status_changed(item)

        output_path = self._settings.output_dir
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = self._build_ydl_opts(item, output_path)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([item.url])

            # Find the downloaded file
            item.filepath = self._find_downloaded_file(
                output_path, item.title,
                "mp4" if item.format == DownloadFormat.VIDEO else "mp3"
            )
            item.status = DownloadStatus.COMPLETED
            item.progress = 100.0
            item.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"Downloaded: {item.title} -> {item.filepath}")

            if self._on_complete:
                self._on_complete(item)

            return True

        except Exception as e:
            error_msg = str(e)
            item.status = DownloadStatus.FAILED
            item.error_message = error_msg
            logger.error(f"Download error: {item.title} - {error_msg}")

            if self._on_error:
                self._on_error(item, error_msg)

            return False

    def _build_ydl_opts(self, item: DownloadItem, output_path: str) -> Dict[str, Any]:
        """Build yt-dlp options (postprocessor conflict fixed).

        Args:
            item: Download item.
            output_path: Save directory.

        Returns:
            yt-dlp options dictionary.
        """
        ydl_opts: Dict[str, Any] = {
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "progress_hooks": [lambda d: self._progress_hook(d, item)],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "extractor_retries": 3,
        }

        # Build postprocessor list properly (no conflicts!)
        postprocessors: List[Dict[str, Any]] = []

        if item.format == DownloadFormat.VIDEO:
            res = item.quality
            if res == "best":
                fmt = "bestvideo[height<=2160]+bestaudio/best"
            else:
                height = res.replace("p", "")
                fmt = f"bestvideo[height<={height}]+bestaudio/best"
            ydl_opts["format"] = fmt
            ydl_opts["merge_output_format"] = "mp4"
        else:
            ydl_opts["format"] = "bestaudio/best"
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": item.audio_quality,
            })

        # Subtitle options (video only)
        if self._settings.subtitle_enabled and item.format == DownloadFormat.VIDEO:
            ydl_opts["writesubtitles"] = True
            ydl_opts["subtitleslangs"] = [self._settings.subtitle_language]
            ydl_opts["writeautomaticsub"] = True

            if self._settings.embed_subtitles:
                postprocessors.append({
                    "key": "FFmpegEmbedSubtitle",
                    "already_have_subtitle": False,
                })

        # Metadata embedding
        postprocessors.append({
            "key": "FFmpegMetadata",
            "add_metadata": True,
        })

        # Speed limit
        if self._settings.speed_limit:
            ydl_opts["ratelimit"] = self._settings.speed_limit

        ydl_opts["postprocessors"] = postprocessors

        return ydl_opts

    def _progress_hook(self, d: Dict[str, Any], item: DownloadItem) -> None:
        """Progress callback (thread-safe, with real pause).

        Args:
            d: yt-dlp progress dictionary.
            item: Current download item.
        """
        # Real pause — blocks the thread
        self._pause_event.wait()

        if self._cancel_event.is_set():
            raise Exception("Download cancelled by user")

        if d["status"] == "downloading":
            progress = DownloadProgress(
                status="downloading",
                filename=d.get("filename", ""),
            )

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)

            if total > 0:
                progress.percent = (downloaded / total) * 100
                progress.total_bytes = total
            progress.downloaded_bytes = downloaded
            progress.speed = d.get("speed", 0) or 0
            progress.eta = d.get("eta", 0) or 0

            # Update item state
            item.progress = progress.percent
            item.speed = progress.speed
            item.eta = progress.eta

            if self._on_progress:
                self._on_progress(item, progress)

        elif d["status"] == "finished":
            item.status = DownloadStatus.CONVERTING
            if self._on_status_changed:
                self._on_status_changed(item)

    def _find_downloaded_file(
        self, output_path: str, title: str, extension: str
    ) -> Optional[str]:
        """Find the downloaded file on disk.

        Args:
            output_path: Directory path.
            title: Video title.
            extension: File extension.

        Returns:
            File path or None.
        """
        safe_title = sanitize_filename(title)

        # Direct match
        direct = os.path.join(output_path, f"{safe_title}.{extension}")
        if os.path.exists(direct):
            return direct

        # Try with original title
        original = os.path.join(output_path, f"{title}.{extension}")
        if os.path.exists(original):
            return original

        # Find the most recently modified matching file
        try:
            files = [
                os.path.join(output_path, f)
                for f in os.listdir(output_path)
                if f.endswith(f".{extension}")
            ]
            if files:
                return max(files, key=os.path.getmtime)
        except Exception:
            pass

        return None

    def clear_cache(self) -> None:
        """Clear the video info cache."""
        self._video_info_cache.clear()
        logger.debug("Video info cache cleared")
