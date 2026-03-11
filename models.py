"""
YouTube Downloader Pro — Data Models

All data models (dataclass) and status enums.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


class DownloadStatus(enum.Enum):
    """Download status states."""
    PENDING = "pending"
    FETCHING_INFO = "fetching_info"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadFormat(enum.Enum):
    """Download format type."""
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class VideoInfo:
    """YouTube video metadata."""
    url: str
    title: str = "Unknown"
    uploader: str = "Unknown"
    duration: int = 0
    thumbnail_url: str = ""
    filesize_approx: int = 0
    has_subtitles: bool = False
    is_playlist: bool = False
    playlist_title: str = ""
    playlist_count: int = 0
    raw_info: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def duration_str(self) -> str:
        """Return duration as 'MM:SS' or 'HH:MM:SS'."""
        if self.duration <= 0:
            return "Unknown"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def filesize_str(self) -> str:
        """Return file size in human-readable format."""
        return format_bytes(self.filesize_approx)

    @classmethod
    def from_yt_dlp(cls, url: str, info: Dict[str, Any]) -> "VideoInfo":
        """Create VideoInfo from yt-dlp info dictionary."""
        # Calculate file size
        filesize = info.get("filesize") or info.get("filesize_approx") or 0
        if not filesize:
            # Find the best format's size
            formats = info.get("formats", [])
            if formats:
                best = max(formats, key=lambda f: f.get("filesize", 0) or 0)
                filesize = best.get("filesize", 0) or best.get("filesize_approx", 0) or 0

        return cls(
            url=url,
            title=info.get("title", "Unknown"),
            uploader=info.get("uploader", "Unknown"),
            duration=info.get("duration", 0) or 0,
            thumbnail_url=info.get("thumbnail", ""),
            filesize_approx=filesize,
            has_subtitles=bool(info.get("subtitles", {})),
            is_playlist=info.get("_type") == "playlist",
            playlist_title=info.get("playlist_title", "") or "",
            playlist_count=info.get("playlist_count", 0) or 0,
            raw_info=info,
        )


@dataclass
class DownloadItem:
    """A single item in the download queue."""
    video_info: VideoInfo
    format: DownloadFormat = DownloadFormat.VIDEO
    quality: str = "best"
    audio_quality: str = "192"
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    speed: float = 0.0
    eta: int = 0
    filepath: Optional[str] = None
    error_message: str = ""
    added_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None

    @property
    def title(self) -> str:
        return self.video_info.title

    @property
    def url(self) -> str:
        return self.video_info.url

    @property
    def speed_str(self) -> str:
        """Return speed in human-readable format."""
        return f"{format_bytes(self.speed)}/s" if self.speed > 0 else ""

    @property
    def eta_str(self) -> str:
        """Return ETA as 'MM:SS'."""
        if self.eta <= 0:
            return ""
        minutes, seconds = divmod(self.eta, 60)
        return f"{minutes}:{seconds:02d}"

    @property
    def status_icon(self) -> str:
        """Return emoji icon for current status."""
        icons = {
            DownloadStatus.PENDING: "⏳",
            DownloadStatus.FETCHING_INFO: "🔍",
            DownloadStatus.DOWNLOADING: "⬇️",
            DownloadStatus.PAUSED: "⏸️",
            DownloadStatus.CONVERTING: "🔄",
            DownloadStatus.COMPLETED: "✅",
            DownloadStatus.FAILED: "❌",
            DownloadStatus.CANCELLED: "🚫",
        }
        return icons.get(self.status, "❓")

    def to_history_dict(self) -> Dict[str, Any]:
        """Return a dictionary for history storage."""
        return {
            "title": self.title,
            "url": self.url,
            "uploader": self.video_info.uploader,
            "duration": self.video_info.duration,
            "duration_str": self.video_info.duration_str,
            "format": self.format.value,
            "quality": self.quality,
            "filepath": self.filepath,
            "filesize": self.video_info.filesize_approx,
            "filesize_str": self.video_info.filesize_str,
            "added_at": self.added_at,
            "completed_at": self.completed_at,
        }


@dataclass
class DownloadProgress:
    """Progress data from the download hook."""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    eta: int = 0
    percent: float = 0.0
    status: str = ""
    filename: str = ""


def format_bytes(size: int | float) -> str:
    """Convert bytes to human-readable format."""
    if size <= 0:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
