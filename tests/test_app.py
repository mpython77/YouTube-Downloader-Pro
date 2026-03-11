"""
Tests for app startup — GUI window creation test.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tkinter as tk
from config import AppSettings


class TestAppStartup:
    """Application startup tests."""

    def test_tkinter_available(self):
        """Check that Tkinter is available."""
        root = tk.Tk()
        root.withdraw()
        assert root is not None
        root.destroy()

    def test_settings_load(self):
        """Check that settings load correctly."""
        settings = AppSettings.load()
        assert settings.output_dir is not None
        assert settings.format in ("video", "audio")
        assert settings.video_quality in ("best", "2160p", "1440p", "1080p", "720p", "480p", "360p")

    def test_settings_save_load_cycle(self, tmp_path):
        """Check settings save and reload cycle."""
        import config
        original_file = config.SETTINGS_FILE

        # Use temporary file
        config.SETTINGS_FILE = tmp_path / "test_settings.json"

        settings = AppSettings(output_dir="/tmp/test", format="audio", video_quality="720p")
        settings.save()

        loaded = AppSettings.load()
        assert loaded.output_dir == "/tmp/test"
        assert loaded.format == "audio"
        assert loaded.video_quality == "720p"

        # Restore original value
        config.SETTINGS_FILE = original_file

    def test_main_window_creates(self):
        """Check that MainWindow creates without errors."""
        root = tk.Tk()
        root.withdraw()

        try:
            from ui.main_window import MainWindow
            settings = AppSettings()
            app = MainWindow(root, settings)
            assert app is not None
            assert app.root == root

            # Update to process any pending events
            root.update_idletasks()

        finally:
            root.destroy()

    def test_imports_work(self):
        """Check that all modules import successfully."""
        import config
        import models
        from services.downloader import DownloadService
        from services.thumbnail import ThumbnailService
        from services.history import HistoryService
        from ui.styles import setup_styles
        from ui.components import VideoInfoCard, DownloadProgressCard
        from utils.validators import is_valid_youtube_url
        from utils.file_utils import open_file, open_folder, format_bytes

        assert True  # If we reach here, all imports worked
