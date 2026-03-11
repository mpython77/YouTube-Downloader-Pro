"""
Tests for services/downloader.py — Download service tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock

from config import AppSettings
from models import DownloadItem, DownloadFormat, DownloadStatus, VideoInfo
from services.downloader import DownloadService, check_ffmpeg


@pytest.fixture
def settings():
    """Test settings."""
    return AppSettings(
        output_dir=os.path.join(os.path.expanduser("~"), "Downloads"),
        format="video",
        video_quality="1080p",
        subtitle_enabled=False,
        speed_limit=None,
    )


@pytest.fixture
def service(settings):
    """Create a DownloadService instance."""
    return DownloadService(settings)


@pytest.fixture
def sample_item():
    """Create a sample DownloadItem."""
    info = VideoInfo(url="https://youtube.com/watch?v=test123456", title="Test Video")
    return DownloadItem(video_info=info, format=DownloadFormat.VIDEO, quality="1080p")


class TestFFmpegCheck:
    """FFmpeg availability tests."""

    def test_check_ffmpeg_returns_bool(self):
        result = check_ffmpeg()
        assert isinstance(result, bool)


class TestDownloadServiceQueue:
    """Queue management tests."""

    def test_initial_state(self, service):
        assert service.queue_count == 0
        assert service.is_running is False
        assert service.is_paused is False
        assert service.current_item is None
        assert service.completed_count == 0
        assert service.failed_count == 0
        assert service.pending_count == 0

    def test_add_to_queue(self, service, sample_item):
        result = service.add_to_queue(sample_item)
        assert result is True
        assert service.queue_count == 1
        assert service.queue[0].title == "Test Video"

    def test_add_duplicate_to_queue(self, service, sample_item):
        """Duplicate URLs should not be added."""
        result1 = service.add_to_queue(sample_item)
        assert result1 is True

        # Same URL
        info2 = VideoInfo(url="https://youtube.com/watch?v=test123456", title="Test Video Dup")
        item2 = DownloadItem(video_info=info2)
        result2 = service.add_to_queue(item2)
        assert result2 is False
        assert service.queue_count == 1  # Only 1

    def test_is_duplicate(self, service, sample_item):
        assert service.is_duplicate(sample_item.url) is False
        service.add_to_queue(sample_item)
        assert service.is_duplicate(sample_item.url) is True

    def test_add_multiple_different_urls(self, service):
        for i in range(5):
            info = VideoInfo(url=f"https://youtube.com/watch?v=unique{i}", title=f"Video {i}")
            item = DownloadItem(video_info=info)
            service.add_to_queue(item)
        assert service.queue_count == 5

    def test_remove_from_queue(self, service, sample_item):
        service.add_to_queue(sample_item)
        removed = service.remove_from_queue(0)
        assert removed is not None
        assert removed.title == "Test Video"
        assert service.queue_count == 0
        # Verify URL set is also updated
        assert service.is_duplicate(sample_item.url) is False

    def test_remove_invalid_index(self, service):
        assert service.remove_from_queue(99) is None

    def test_clear_queue(self, service, sample_item):
        service.add_to_queue(sample_item)
        service.clear_queue()
        assert service.queue_count == 0
        assert service.is_duplicate(sample_item.url) is False

    def test_move_in_queue(self, service):
        for i in range(3):
            info = VideoInfo(url=f"https://youtube.com/watch?v=move{i}", title=f"Video {i}")
            service.add_to_queue(DownloadItem(video_info=info))

        service.move_in_queue(0, 2)
        assert service.queue[2].title == "Video 0"

    def test_retry_failed(self, service):
        """Failed items should be reset to PENDING."""
        info1 = VideoInfo(url="https://youtube.com/watch?v=fail1", title="Failed 1")
        item1 = DownloadItem(video_info=info1)
        item1.status = DownloadStatus.FAILED
        item1.error_message = "Network error"

        info2 = VideoInfo(url="https://youtube.com/watch?v=ok1", title="OK 1")
        item2 = DownloadItem(video_info=info2)

        service._queue = [item1, item2]
        service._url_set = {item1.url, item2.url}

        count = service.retry_failed()
        assert count == 1
        assert item1.status == DownloadStatus.PENDING
        assert item1.progress == 0.0
        assert item1.error_message == ""
        assert item2.status == DownloadStatus.PENDING  # Unchanged

    def test_remove_completed(self, service):
        """Completed items should be removed from queue."""
        info1 = VideoInfo(url="https://youtube.com/watch?v=done1", title="Done 1")
        item1 = DownloadItem(video_info=info1)
        item1.status = DownloadStatus.COMPLETED

        info2 = VideoInfo(url="https://youtube.com/watch?v=pend1", title="Pending 1")
        item2 = DownloadItem(video_info=info2)

        service._queue = [item1, item2]
        service._url_set = {item1.url, item2.url}

        removed = service.remove_completed()
        assert removed == 1
        assert service.queue_count == 1
        assert service.queue[0].title == "Pending 1"
        assert service.is_duplicate("https://youtube.com/watch?v=done1") is False

    def test_pending_count(self, service):
        info1 = VideoInfo(url="https://youtube.com/watch?v=p1", title="P1")
        item1 = DownloadItem(video_info=info1)
        info2 = VideoInfo(url="https://youtube.com/watch?v=p2", title="P2")
        item2 = DownloadItem(video_info=info2)
        item2.status = DownloadStatus.COMPLETED

        service._queue = [item1, item2]
        assert service.pending_count == 1

    def test_has_ffmpeg_property(self, service):
        result = service.has_ffmpeg
        assert isinstance(result, bool)


class TestBuildYdlOpts:
    """yt-dlp options building tests."""

    def test_video_opts(self, service, sample_item):
        opts = service._build_ydl_opts(sample_item, "/tmp/test")
        assert "format" in opts
        assert "1080" in opts["format"]
        assert opts["merge_output_format"] == "mp4"
        assert opts["retries"] == 5
        assert opts["socket_timeout"] == 30

    def test_audio_opts(self, service):
        info = VideoInfo(url="test", title="Audio Test")
        item = DownloadItem(video_info=info, format=DownloadFormat.AUDIO, audio_quality="320")
        opts = service._build_ydl_opts(item, "/tmp/test")

        assert opts["format"] == "bestaudio/best"
        assert "postprocessors" in opts
        pp_keys = [p["key"] for p in opts["postprocessors"]]
        assert "FFmpegExtractAudio" in pp_keys

    def test_metadata_postprocessor_always_added(self, service, sample_item):
        """FFmpegMetadata should always be included."""
        opts = service._build_ydl_opts(sample_item, "/tmp/test")
        pp_keys = [p["key"] for p in opts["postprocessors"]]
        assert "FFmpegMetadata" in pp_keys

    def test_video_best_quality(self, service):
        info = VideoInfo(url="test", title="Best Quality")
        item = DownloadItem(video_info=info, format=DownloadFormat.VIDEO, quality="best")
        opts = service._build_ydl_opts(item, "/tmp/test")
        assert "2160" in opts["format"]

    def test_subtitle_opts(self, settings):
        settings.subtitle_enabled = True
        settings.subtitle_language = "en"
        settings.embed_subtitles = True
        service = DownloadService(settings)

        info = VideoInfo(url="test", title="Sub Test")
        item = DownloadItem(video_info=info, format=DownloadFormat.VIDEO)
        opts = service._build_ydl_opts(item, "/tmp/test")

        assert opts["writesubtitles"] is True
        assert opts["subtitleslangs"] == ["en"]
        pp_keys = [p["key"] for p in opts["postprocessors"]]
        assert "FFmpegEmbedSubtitle" in pp_keys

    def test_subtitle_with_audio_no_conflict(self, settings):
        """BUG FIX: Subtitle postprocessor must not conflict with audio."""
        settings.subtitle_enabled = True
        settings.embed_subtitles = True
        service = DownloadService(settings)

        info = VideoInfo(url="test", title="Conflict Test")
        item = DownloadItem(video_info=info, format=DownloadFormat.AUDIO)
        opts = service._build_ydl_opts(item, "/tmp/test")

        pp_keys = [p["key"] for p in opts["postprocessors"]]
        assert "FFmpegExtractAudio" in pp_keys
        assert "FFmpegEmbedSubtitle" not in pp_keys

    def test_speed_limit(self, settings):
        settings.speed_limit = 5 * 1024 * 1024
        service = DownloadService(settings)

        info = VideoInfo(url="test", title="Speed Test")
        item = DownloadItem(video_info=info)
        opts = service._build_ydl_opts(item, "/tmp/test")

        assert opts["ratelimit"] == 5 * 1024 * 1024

    def test_no_speed_limit(self, service, sample_item):
        opts = service._build_ydl_opts(sample_item, "/tmp/test")
        assert "ratelimit" not in opts

    def test_yt_dlp_retry_options(self, service, sample_item):
        """Verify yt-dlp retry settings are configured."""
        opts = service._build_ydl_opts(sample_item, "/tmp/test")
        assert opts["retries"] == 5
        assert opts["fragment_retries"] == 5
        assert opts["extractor_retries"] == 3


class TestPauseResume:
    """Pause/Resume mechanism tests."""

    def test_initial_not_paused(self, service):
        assert service.is_paused is False

    def test_pause_when_not_running(self, service):
        service.pause()
        assert service.is_paused is False

    def test_cancel(self, service):
        service.cancel()
        assert service.is_running is False


class TestCallbacks:
    """Callback registration tests."""

    def test_set_callbacks(self, service):
        on_progress = MagicMock()
        on_complete = MagicMock()
        on_error = MagicMock()
        on_all_complete = MagicMock()

        service.set_callbacks(
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
            on_all_complete=on_all_complete,
        )

        assert service._on_progress == on_progress
        assert service._on_complete == on_complete
        assert service._on_error == on_error
        assert service._on_all_complete == on_all_complete

    def test_queue_changed_callback(self, service, sample_item):
        callback = MagicMock()
        service.set_callbacks(on_queue_changed=callback)

        service.add_to_queue(sample_item)
        callback.assert_called_once()


class TestCache:
    """Video info cache tests."""

    def test_clear_cache(self, service):
        service._video_info_cache["test_url"] = VideoInfo(url="test")
        assert len(service._video_info_cache) == 1

        service.clear_cache()
        assert len(service._video_info_cache) == 0
