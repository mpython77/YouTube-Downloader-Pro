"""
Tests for models.py — Data model tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models import (
    DownloadStatus, DownloadFormat, VideoInfo, DownloadItem,
    DownloadProgress, format_bytes,
)


class TestDownloadStatus:
    """DownloadStatus enum tests."""

    def test_all_statuses_exist(self):
        assert DownloadStatus.PENDING.value == "pending"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.PAUSED.value == "paused"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.CANCELLED.value == "cancelled"
        assert DownloadStatus.FETCHING_INFO.value == "fetching_info"
        assert DownloadStatus.CONVERTING.value == "converting"

    def test_status_count(self):
        assert len(DownloadStatus) == 8


class TestDownloadFormat:
    """DownloadFormat enum tests."""

    def test_video_format(self):
        assert DownloadFormat.VIDEO.value == "video"

    def test_audio_format(self):
        assert DownloadFormat.AUDIO.value == "audio"


class TestVideoInfo:
    """VideoInfo model tests."""

    def test_default_values(self):
        info = VideoInfo(url="https://youtube.com/watch?v=test123456")
        assert info.title == "Unknown"
        assert info.uploader == "Unknown"
        assert info.duration == 0
        assert info.filesize_approx == 0
        assert info.has_subtitles is False
        assert info.is_playlist is False

    def test_duration_str_seconds(self):
        info = VideoInfo(url="test", duration=45)
        assert info.duration_str == "0:45"

    def test_duration_str_minutes(self):
        info = VideoInfo(url="test", duration=185)
        assert info.duration_str == "3:05"

    def test_duration_str_hours(self):
        info = VideoInfo(url="test", duration=3661)
        assert info.duration_str == "1:01:01"

    def test_duration_str_zero(self):
        info = VideoInfo(url="test", duration=0)
        assert info.duration_str == "Unknown"

    def test_from_yt_dlp(self):
        raw = {
            "title": "Test Video",
            "uploader": "Test User",
            "duration": 120,
            "thumbnail": "https://img.youtube.com/vi/test/0.jpg",
            "subtitles": {"en": []},
            "filesize": 1024000,
        }
        info = VideoInfo.from_yt_dlp("https://youtube.com/watch?v=test", raw)
        assert info.title == "Test Video"
        assert info.uploader == "Test User"
        assert info.duration == 120
        assert info.has_subtitles is True
        assert info.filesize_approx == 1024000


class TestDownloadItem:
    """DownloadItem model tests."""

    def test_default_item(self):
        info = VideoInfo(url="https://youtube.com/watch?v=test123456", title="Test")
        item = DownloadItem(video_info=info)
        assert item.title == "Test"
        assert item.url == "https://youtube.com/watch?v=test123456"
        assert item.status == DownloadStatus.PENDING
        assert item.progress == 0.0
        assert item.filepath is None

    def test_status_icon(self):
        info = VideoInfo(url="test")
        item = DownloadItem(video_info=info)

        item.status = DownloadStatus.PENDING
        assert item.status_icon == "⏳"

        item.status = DownloadStatus.COMPLETED
        assert item.status_icon == "✅"

        item.status = DownloadStatus.FAILED
        assert item.status_icon == "❌"

    def test_speed_str(self):
        info = VideoInfo(url="test")
        item = DownloadItem(video_info=info)

        item.speed = 0
        assert item.speed_str == ""

        item.speed = 1024 * 1024 * 2.5
        assert "MB" in item.speed_str

    def test_eta_str(self):
        info = VideoInfo(url="test")
        item = DownloadItem(video_info=info)

        item.eta = 0
        assert item.eta_str == ""

        item.eta = 125
        assert item.eta_str == "2:05"

    def test_to_history_dict(self):
        info = VideoInfo(url="https://youtube.com/watch?v=test", title="My Video", uploader="Author")
        item = DownloadItem(video_info=info, format=DownloadFormat.VIDEO, quality="1080p")
        d = item.to_history_dict()

        assert d["title"] == "My Video"
        assert d["url"] == "https://youtube.com/watch?v=test"
        assert d["uploader"] == "Author"
        assert d["format"] == "video"
        assert d["quality"] == "1080p"


class TestFormatBytes:
    """format_bytes function tests."""

    def test_zero(self):
        assert format_bytes(0) == "Unknown"

    def test_negative(self):
        assert format_bytes(-100) == "Unknown"

    def test_bytes(self):
        assert format_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        result = format_bytes(1536)
        assert "KB" in result

    def test_megabytes(self):
        result = format_bytes(5 * 1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = format_bytes(2.5 * 1024 * 1024 * 1024)
        assert "GB" in result
