"""
YouTube Downloader Pro — Configuration Module

All application settings, constants, and color palette.
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path

# ============================================================
# App Info
# ============================================================
APP_NAME = "YouTube Downloader Pro"
APP_VERSION = "2.0.0"
APP_ICON = "🎬"

# ============================================================
# Paths
# ============================================================
APP_DATA_DIR = Path(os.path.expanduser("~")) / ".ytdownloader_pro"
SETTINGS_FILE = APP_DATA_DIR / "settings.json"
HISTORY_FILE = APP_DATA_DIR / "download_history.json"
LOG_FILE = APP_DATA_DIR / "app.log"
THUMBNAIL_CACHE_DIR = APP_DATA_DIR / "thumbnails"

# ============================================================
# Catppuccin Mocha Color Palette
# ============================================================
COLORS: Dict[str, str] = {
    "rosewater": "#f5e0dc",
    "flamingo": "#f2cdcd",
    "pink": "#f5c2e7",
    "mauve": "#cba6f7",
    "red": "#f38ba8",
    "maroon": "#eba0ac",
    "peach": "#fab387",
    "yellow": "#f9e2af",
    "green": "#a6e3a1",
    "teal": "#94e2d5",
    "sky": "#89dceb",
    "sapphire": "#74c7ec",
    "blue": "#89b4fa",
    "lavender": "#b4befe",
    "text": "#cdd6f4",
    "subtext1": "#bac2de",
    "subtext0": "#a6adc8",
    "overlay2": "#9399b2",
    "overlay1": "#7f849c",
    "overlay0": "#6c7086",
    "surface2": "#585b70",
    "surface1": "#45475a",
    "surface0": "#313244",
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
}

# Semantic colors
THEME = {
    "bg": COLORS["base"],
    "bg_dark": COLORS["mantle"],
    "bg_darker": COLORS["crust"],
    "surface": COLORS["surface0"],
    "surface_hover": COLORS["surface1"],
    "accent": COLORS["mauve"],
    "accent_hover": COLORS["lavender"],
    "secondary": COLORS["blue"],
    "text": COLORS["text"],
    "text_dim": COLORS["subtext0"],
    "success": COLORS["green"],
    "warning": COLORS["yellow"],
    "error": COLORS["red"],
    "info": COLORS["sky"],
}

# ============================================================
# Download Options
# ============================================================
VIDEO_QUALITIES = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]

AUDIO_QUALITIES = [
    ("320 kbps (Best)", "320"),
    ("256 kbps", "256"),
    ("192 kbps (Default)", "192"),
    ("128 kbps", "128"),
    ("96 kbps", "96"),
]

SPEED_LIMITS = [
    ("No Limit", None),
    ("500 KB/s", 500 * 1024),
    ("1 MB/s", 1 * 1024 * 1024),
    ("2 MB/s", 2 * 1024 * 1024),
    ("5 MB/s", 5 * 1024 * 1024),
    ("10 MB/s", 10 * 1024 * 1024),
    ("20 MB/s", 20 * 1024 * 1024),
]

SUBTITLE_LANGUAGES = [
    ("English", "en"),
    ("Russian", "ru"),
    ("Uzbek", "uz"),
    ("Spanish", "es"),
    ("French", "fr"),
    ("German", "de"),
    ("Turkish", "tr"),
    ("Arabic", "ar"),
    ("Chinese", "zh"),
    ("Japanese", "ja"),
    ("Korean", "ko"),
    ("Auto-detect", "auto"),
]

SUPPORTED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
]

# ============================================================
# Logging Setup
# ============================================================
def setup_logging() -> logging.Logger:
    """Configure the logging system."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ============================================================
# Settings Persistence
# ============================================================
@dataclass
class AppSettings:
    """Application settings — saved/loaded as JSON."""
    output_dir: str = field(default_factory=lambda: os.path.expanduser("~/Downloads"))
    format: str = "video"
    video_quality: str = "best"
    audio_quality: str = "192"
    speed_limit: Optional[int] = None
    subtitle_enabled: bool = False
    subtitle_language: str = "en"
    embed_subtitles: bool = True
    clipboard_monitor: bool = True
    auto_download: bool = False
    max_concurrent: int = 1
    window_width: int = 900
    window_height: int = 750

    def save(self) -> None:
        """Save settings to file."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from file, return defaults on error."""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return cls()
