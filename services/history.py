"""
YouTube Downloader Pro — History Service

Persistent download history — saved and loaded from a JSON file.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import HISTORY_FILE, APP_DATA_DIR

logger = logging.getLogger("YouTube Downloader Pro")


class HistoryService:
    """Manage download history with JSON file persistence.

    Previous history is loaded on startup.
    Updated after each download completes.
    """

    def __init__(self, history_file: Optional[Path] = None):
        """
        Args:
            history_file: Path to the history file (default: config.HISTORY_FILE).
        """
        self._history_file = history_file or HISTORY_FILE
        self._history: List[Dict[str, Any]] = []
        self._load()

    # ========================================================
    # Properties
    # ========================================================

    @property
    def items(self) -> List[Dict[str, Any]]:
        """All history entries (copy)."""
        return list(self._history)

    @property
    def count(self) -> int:
        """Number of history entries."""
        return len(self._history)

    # ========================================================
    # CRUD
    # ========================================================

    def add(self, entry: Dict[str, Any]) -> None:
        """Add a new entry to history and save to file.

        Args:
            entry: Download information dictionary.
        """
        self._history.append(entry)
        self._save()
        logger.info(f"Added to history: {entry.get('title', 'Unknown')}")

    def remove(self, index: int) -> Optional[Dict[str, Any]]:
        """Remove an entry from history by index.

        Args:
            index: Entry index.

        Returns:
            Removed entry or None.
        """
        if 0 <= index < len(self._history):
            item = self._history.pop(index)
            self._save()
            logger.info(f"Removed from history: {item.get('title', 'Unknown')}")
            return item
        return None

    def clear(self) -> None:
        """Clear all history entries."""
        self._history.clear()
        self._save()
        logger.info("History cleared")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search history by title, URL, or uploader.

        Args:
            query: Search term (case-insensitive).

        Returns:
            List of matching entries.
        """
        query_lower = query.lower()
        return [
            item for item in self._history
            if query_lower in item.get("title", "").lower()
            or query_lower in item.get("url", "").lower()
            or query_lower in item.get("uploader", "").lower()
        ]

    # ========================================================
    # Export
    # ========================================================

    def export_json(self, filepath: str) -> bool:
        """Export history to a JSON file.

        Args:
            filepath: Output file path.

        Returns:
            True if exported successfully.
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
            logger.info(f"History exported to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False

    def export_csv(self, filepath: str) -> bool:
        """Export history to a CSV file.

        Args:
            filepath: Output file path.

        Returns:
            True if exported successfully.
        """
        try:
            import csv
            if not self._history:
                return False

            fieldnames = ["title", "url", "uploader", "duration_str",
                          "format", "quality", "filesize_str",
                          "added_at", "completed_at", "filepath"]

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(self._history)

            logger.info(f"History exported to CSV: {filepath}")
            return True
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            return False

    # ========================================================
    # Statistics
    # ========================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics.

        Returns:
            Statistics dictionary.
        """
        total = len(self._history)
        videos = sum(1 for h in self._history if h.get("format") == "video")
        audios = sum(1 for h in self._history if h.get("format") == "audio")
        total_size = sum(h.get("filesize", 0) for h in self._history)

        return {
            "total_downloads": total,
            "video_downloads": videos,
            "audio_downloads": audios,
            "total_size": total_size,
            "total_size_str": self._format_bytes(total_size),
        }

    # ========================================================
    # Internal
    # ========================================================

    def _load(self) -> None:
        """Load history from file."""
        if self._history_file.exists():
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._history = data
                    logger.info(f"History loaded: {len(self._history)} entries")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error reading history file: {e}")
                self._history = []

    def _save(self) -> None:
        """Save history to file."""
        try:
            APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string."""
        if size <= 0:
            return "0 B"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
