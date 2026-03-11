"""
Tests for services/history.py — History service tests.
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path
from services.history import HistoryService


@pytest.fixture
def temp_history_file():
    """Create a temporary history file."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)  # Start with a clean slate
    yield Path(path)
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def history_service(temp_history_file):
    """Create a HistoryService instance."""
    return HistoryService(history_file=temp_history_file)


class TestHistoryService:
    """HistoryService tests."""

    def test_initial_empty(self, history_service):
        assert history_service.count == 0
        assert history_service.items == []

    def test_add_entry(self, history_service):
        entry = {"title": "Test Video", "url": "https://youtube.com/watch?v=test"}
        history_service.add(entry)
        assert history_service.count == 1
        assert history_service.items[0]["title"] == "Test Video"

    def test_add_multiple(self, history_service):
        for i in range(5):
            history_service.add({"title": f"Video {i}", "url": f"url_{i}"})
        assert history_service.count == 5

    def test_remove_entry(self, history_service):
        history_service.add({"title": "Video 1"})
        history_service.add({"title": "Video 2"})
        removed = history_service.remove(0)
        assert removed["title"] == "Video 1"
        assert history_service.count == 1

    def test_remove_invalid_index(self, history_service):
        assert history_service.remove(99) is None
        assert history_service.remove(-1) is None

    def test_clear(self, history_service):
        history_service.add({"title": "Test"})
        history_service.add({"title": "Test2"})
        history_service.clear()
        assert history_service.count == 0

    def test_search(self, history_service):
        history_service.add({"title": "Python Tutorial", "url": "url1", "uploader": "Channel1"})
        history_service.add({"title": "JavaScript Guide", "url": "url2", "uploader": "Channel2"})
        history_service.add({"title": "Python Advanced", "url": "url3", "uploader": "Channel1"})

        results = history_service.search("Python")
        assert len(results) == 2

        results = history_service.search("Channel1")
        assert len(results) == 2

        results = history_service.search("nonexistent")
        assert len(results) == 0

    def test_search_case_insensitive(self, history_service):
        history_service.add({"title": "UPPERCASE VIDEO", "url": "url1", "uploader": ""})
        results = history_service.search("uppercase")
        assert len(results) == 1

    def test_persistence(self, temp_history_file):
        """Verify history is persisted and reloaded from file."""
        # First service
        service1 = HistoryService(history_file=temp_history_file)
        service1.add({"title": "Persistent Video", "url": "test_url"})
        assert service1.count == 1

        # Second service (should load previous history)
        service2 = HistoryService(history_file=temp_history_file)
        assert service2.count == 1
        assert service2.items[0]["title"] == "Persistent Video"

    def test_export_json(self, history_service, tmp_path):
        history_service.add({"title": "Export Test", "url": "url1"})
        export_path = str(tmp_path / "export.json")
        result = history_service.export_json(export_path)

        assert result is True
        assert os.path.exists(export_path)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Export Test"

    def test_export_csv(self, history_service, tmp_path):
        history_service.add({
            "title": "CSV Test", "url": "url1", "uploader": "Test",
            "duration_str": "3:00", "format": "video", "quality": "1080p",
            "filesize_str": "100 MB", "added_at": "2024-01-01", "completed_at": "2024-01-01",
            "filepath": "/test/path",
        })
        export_path = str(tmp_path / "export.csv")
        result = history_service.export_csv(export_path)

        assert result is True
        assert os.path.exists(export_path)

    def test_stats(self, history_service):
        history_service.add({"title": "V1", "format": "video", "filesize": 1024 * 1024})
        history_service.add({"title": "V2", "format": "video", "filesize": 2 * 1024 * 1024})
        history_service.add({"title": "A1", "format": "audio", "filesize": 512 * 1024})

        stats = history_service.get_stats()
        assert stats["total_downloads"] == 3
        assert stats["video_downloads"] == 2
        assert stats["audio_downloads"] == 1
        assert stats["total_size"] > 0
        assert "MB" in stats["total_size_str"]

    def test_corrupted_file(self, temp_history_file):
        """Verify corrupted file does not cause errors."""
        with open(temp_history_file, "w") as f:
            f.write("invalid json{{{")

        service = HistoryService(history_file=temp_history_file)
        assert service.count == 0  # Should work gracefully
