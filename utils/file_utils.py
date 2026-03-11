"""
YouTube Downloader Pro — File Utilities

File operations: open files, open folders, format sizes.
"""

import os
import platform
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("YouTube Downloader Pro")


def open_file(filepath: str) -> bool:
    """Open a file with the system default application (cross-platform).

    Args:
        filepath: Path to the file to open.

    Returns:
        True if opened successfully.
    """
    if not filepath or not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return False

    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
        logger.info(f"File opened: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error opening file: {e}")
        return False


def open_folder(folder_path: str, select_file: Optional[str] = None) -> bool:
    """Open a folder in the system file manager (cross-platform).

    Args:
        folder_path: Path to the folder to open.
        select_file: Optional — a file to highlight in the folder.

    Returns:
        True if opened successfully.
    """
    if not folder_path or not os.path.exists(folder_path):
        logger.warning(f"Folder not found: {folder_path}")
        return False

    try:
        system = platform.system()
        if system == "Windows":
            if select_file and os.path.exists(select_file):
                subprocess.Popen(["explorer", "/select,", select_file])
            else:
                os.startfile(folder_path)
        elif system == "Darwin":
            if select_file and os.path.exists(select_file):
                subprocess.Popen(["open", "-R", select_file])
            else:
                subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])
        logger.info(f"Folder opened: {folder_path}")
        return True
    except Exception as e:
        logger.error(f"Error opening folder: {e}")
        return False


def get_unique_filepath(directory: str, filename: str, extension: str) -> str:
    """Generate a unique file path by appending a number if needed.

    Args:
        directory: Directory path.
        filename: File name (without extension).
        extension: File extension (without dot, e.g. 'mp4').

    Returns:
        Unique file path.
    """
    filepath = os.path.join(directory, f"{filename}.{extension}")

    if not os.path.exists(filepath):
        return filepath

    counter = 1
    while True:
        filepath = os.path.join(directory, f"{filename} ({counter}).{extension}")
        if not os.path.exists(filepath):
            return filepath
        counter += 1


def format_bytes(size: int | float) -> str:
    """Convert bytes to human-readable format.

    Args:
        size: Number of bytes.

    Returns:
        Formatted string, e.g. '1.5 GB'.
    """
    if size <= 0:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def ensure_dir(path: str) -> str:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        The created/existing directory path.
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return path
