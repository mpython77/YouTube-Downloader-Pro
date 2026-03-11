"""
YouTube Downloader Pro — Main Window

Main GUI window — UI logic only.
Works with Services and Models.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List

from config import (
    APP_NAME, APP_VERSION, APP_ICON, THEME, COLORS,
    VIDEO_QUALITIES, SPEED_LIMITS, SUBTITLE_LANGUAGES,
    AppSettings,
)
from models import (
    DownloadItem, DownloadStatus, DownloadFormat,
    DownloadProgress, VideoInfo,
)
from services.downloader import DownloadService, check_ffmpeg
from services.thumbnail import ThumbnailService
from services.history import HistoryService
from ui.styles import setup_styles
from ui.components import (
    VideoInfoCard, DownloadProgressCard, StyledText,
    SettingsDialog, BatchURLDialog,
)
from utils.validators import is_valid_youtube_url, is_playlist_url
from utils.file_utils import open_file, open_folder

logger = logging.getLogger(APP_NAME)


class MainWindow:
    """Main application window.

    Follows the MVC pattern — only UI logic.
    All business logic is delegated to services.
    """

    def __init__(self, root: tk.Tk, settings: AppSettings):
        self.root = root
        self.settings = settings

        # Services
        self.download_service = DownloadService(settings)
        self.thumbnail_service = ThumbnailService()
        self.history_service = HistoryService()

        # State
        self._url_var = tk.StringVar()
        self._output_dir_var = tk.StringVar(value=settings.output_dir)
        self._format_var = tk.StringVar(value=settings.format)
        self._quality_var = tk.StringVar(value=settings.video_quality)
        self._status_var = tk.StringVar(value="Ready to download")
        self._speed_limit_var = tk.StringVar(value="No Limit")
        self._subtitle_var = tk.BooleanVar(value=settings.subtitle_enabled)
        self._subtitle_lang_var = tk.StringVar(value=settings.subtitle_language)
        self._embed_subs_var = tk.BooleanVar(value=settings.embed_subtitles)
        self._clipboard_last = ""
        self._current_thumbnail = None
        self._download_start_time = None

        # Setup
        self._configure_window()
        setup_styles()
        self._build_menu()
        self._build_ui()
        self._setup_callbacks()
        self._setup_bindings()
        self._load_history()

        # FFmpeg check
        self._check_ffmpeg_on_start()

        # Clipboard monitoring
        if settings.clipboard_monitor:
            self._monitor_clipboard()

    # ========================================================
    # Window Setup
    # ========================================================

    def _configure_window(self) -> None:
        """Configure window properties."""
        self.root.title(f"{APP_ICON} {APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{self.settings.window_width}x{self.settings.window_height}")
        self.root.minsize(750, 600)
        self.root.configure(bg=THEME["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _check_ffmpeg_on_start(self) -> None:
        """Check FFmpeg availability and warn if missing."""
        if not check_ffmpeg():
            self._status_var.set("⚠️ FFmpeg not found! Audio and subtitle features may not work.")
            logger.warning("FFmpeg not found — please add to PATH")

    def _build_menu(self) -> None:
        """Build the menu bar."""
        menubar = tk.Menu(self.root, bg=THEME["surface"], fg=THEME["text"],
                         activebackground=THEME["accent"], activeforeground=COLORS["crust"],
                         borderwidth=0)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=THEME["surface"], fg=THEME["text"],
                           activebackground=THEME["accent"], activeforeground=COLORS["crust"])
        file_menu.add_command(label="📂 Change Save Location", command=self._select_output_dir,
                             accelerator="Ctrl+O")
        file_menu.add_command(label="📋 Batch Add URLs", command=self._show_batch_dialog,
                             accelerator="Ctrl+B")
        file_menu.add_separator()
        file_menu.add_command(label="📤 Export History (JSON)", command=self._export_json)
        file_menu.add_command(label="📊 Export History (CSV)", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self._on_closing, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=THEME["surface"], fg=THEME["text"],
                           activebackground=THEME["accent"], activeforeground=COLORS["crust"])
        edit_menu.add_command(label="📋 Paste URL", command=self._paste_url, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="🔄 Retry Failed", command=self._retry_failed)
        edit_menu.add_command(label="✅ Remove Completed", command=self._remove_completed)
        edit_menu.add_command(label="🗑️ Clear Queue", command=self._clear_queue, accelerator="Del")
        edit_menu.add_command(label="🧹 Clear History", command=self._clear_history)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=THEME["surface"], fg=THEME["text"],
                            activebackground=THEME["accent"], activeforeground=COLORS["crust"])
        tools_menu.add_command(label="⚙️ Settings", command=self._show_settings, accelerator="Ctrl+S")
        tools_menu.add_command(label="📊 Statistics", command=self._show_statistics)
        tools_menu.add_separator()
        tools_menu.add_command(label="🔍 Check FFmpeg", command=self._check_ffmpeg_dialog)
        tools_menu.add_command(label="🗑️ Clear Cache", command=self._clear_cache)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=THEME["surface"], fg=THEME["text"],
                           activebackground=THEME["accent"], activeforeground=COLORS["crust"])
        help_menu.add_command(label="📖 Help", command=self._show_help, accelerator="F1")
        help_menu.add_command(label="⌨️ Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ========================================================
    # UI Building
    # ========================================================

    def _build_ui(self) -> None:
        """Build the complete user interface."""
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        # Header
        self._build_header(main)

        # URL Input
        self._build_url_input(main)

        # Video Info Card
        self.video_card = VideoInfoCard(main)
        self.video_card.pack(fill="x", pady=(0, 12))

        # Download Settings
        self._build_settings_panel(main)

        # Output directory
        self._build_output_dir(main)

        # Tabs (Queue + History)
        self._build_tabs(main)

        # Progress
        self.progress_card = DownloadProgressCard(main)
        self.progress_card.pack(fill="x", pady=(0, 8))

        # Status bar
        self._build_status_bar(main)

        # Buttons
        self._build_buttons(main)

    def _build_header(self, parent: ttk.Frame) -> None:
        """Build the header section."""
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 15))

        ttk.Label(
            header, text=f"{APP_ICON} {APP_NAME}",
            style="Header.TLabel",
        ).pack(side="left")

        ttk.Label(
            header, text=f"v{APP_VERSION}",
            style="Status.TLabel",
        ).pack(side="left", padx=(8, 0), anchor="s", pady=(0, 4))

        # FFmpeg indicator
        ffmpeg_text = "✅ FFmpeg" if check_ffmpeg() else "⚠️ No FFmpeg"
        ffmpeg_style = "Success.TLabel" if check_ffmpeg() else "Error.TLabel"
        ttk.Label(header, text=ffmpeg_text, style=ffmpeg_style).pack(
            side="left", padx=(15, 0), anchor="s", pady=(0, 4))

        # Right side buttons
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="⚙️", command=self._show_settings,
                   style="Ghost.TButton", width=3).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="?", command=self._show_help,
                   style="Ghost.TButton", width=3).pack(side="right", padx=2)

    def _build_url_input(self, parent: ttk.Frame) -> None:
        """Build the URL input section."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="YouTube URL:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        self._url_entry = ttk.Entry(frame, textvariable=self._url_var, font=("Segoe UI", 11))
        self._url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(frame, text="➕ Add", command=self._add_to_queue,
                   style="Accent.TButton").pack(side="left", padx=(0, 4))
        ttk.Button(frame, text="📋", command=self._paste_url,
                   style="Ghost.TButton", width=3).pack(side="left", padx=(0, 4))
        ttk.Button(frame, text="📋+", command=self._show_batch_dialog,
                   style="Ghost.TButton", width=4).pack(side="left")

    def _build_settings_panel(self, parent: ttk.Frame) -> None:
        """Build the download settings panel."""
        settings_frame = ttk.LabelFrame(parent, text="Download Settings", padding=8)
        settings_frame.pack(fill="x", pady=(0, 10))

        # Row 1: Format + Quality
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=(0, 8))

        left = ttk.Frame(row1)
        left.pack(side="left", fill="x", expand=True)

        ttk.Label(left, text="Format:").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(left, text="🎬 Video (MP4)", variable=self._format_var,
                        value="video", command=self._on_format_change).pack(side="left", padx=5)
        ttk.Radiobutton(left, text="🎵 Audio (MP3)", variable=self._format_var,
                        value="audio", command=self._on_format_change).pack(side="left", padx=5)

        right = ttk.Frame(row1)
        right.pack(side="right")

        ttk.Label(right, text="Quality:").pack(side="left", padx=(0, 8))
        self._quality_combo = ttk.Combobox(
            right, textvariable=self._quality_var,
            values=VIDEO_QUALITIES, state="readonly", width=10,
        )
        self._quality_combo.pack(side="left")

        # Row 2: Subtitles + Speed
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x")

        left2 = ttk.Frame(row2)
        left2.pack(side="left", fill="x", expand=True)

        ttk.Checkbutton(left2, text="📝 Subtitles", variable=self._subtitle_var,
                        command=self._on_subtitle_toggle).pack(side="left")

        self._sub_lang_combo = ttk.Combobox(
            left2, textvariable=self._subtitle_lang_var,
            values=[f"{name}" for name, code in SUBTITLE_LANGUAGES],
            state="disabled", width=12,
        )
        self._sub_lang_combo.pack(side="left", padx=(8, 5))

        self._embed_check = ttk.Checkbutton(
            left2, text="Embed", variable=self._embed_subs_var, state="disabled",
        )
        self._embed_check.pack(side="left", padx=5)

        right2 = ttk.Frame(row2)
        right2.pack(side="right")

        ttk.Label(right2, text="Speed:").pack(side="left", padx=(0, 8))
        ttk.Combobox(
            right2, textvariable=self._speed_limit_var,
            values=[s[0] for s in SPEED_LIMITS], state="readonly", width=12,
        ).pack(side="left")

    def _build_output_dir(self, parent: ttk.Frame) -> None:
        """Build the output directory selector."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="💾 Save to:").pack(side="left", padx=(0, 8))
        ttk.Entry(frame, textvariable=self._output_dir_var, font=("Segoe UI", 10)).pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(frame, text="Browse", command=self._select_output_dir,
                   style="Secondary.TButton").pack(side="left")

    def _build_tabs(self, parent: ttk.Frame) -> None:
        """Build Queue and History tabs."""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Queue tab
        queue_frame = ttk.Frame(notebook)
        notebook.add(queue_frame, text="📥 Queue (0)")
        self._queue_notebook = notebook

        self.queue_text = StyledText(queue_frame, height=6)
        self.queue_text.pack(fill="both", expand=True, padx=3, pady=3)

        # Context menu for queue
        self._queue_context_menu = tk.Menu(
            self.queue_text, tearoff=0, bg=THEME["surface"], fg=THEME["text"],
            activebackground=THEME["accent"], activeforeground=COLORS["crust"],
        )
        self._queue_context_menu.add_command(label="🔄 Retry Failed", command=self._retry_failed)
        self._queue_context_menu.add_command(label="✅ Remove Completed", command=self._remove_completed)
        self._queue_context_menu.add_separator()
        self._queue_context_menu.add_command(label="⬆️ Move Up", command=lambda: self._move_queue_item(-1))
        self._queue_context_menu.add_command(label="⬇️ Move Down", command=lambda: self._move_queue_item(1))
        self._queue_context_menu.add_separator()
        self._queue_context_menu.add_command(label="🗑️ Remove", command=self._remove_selected_from_queue)
        self._queue_context_menu.add_command(label="🗑️ Clear All", command=self._clear_queue)

        self.queue_text.bind("<Button-3>", self._show_queue_context_menu)

        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text=f"📜 History ({self.history_service.count})")

        self.history_text = StyledText(history_frame, height=6)
        self.history_text.pack(fill="both", expand=True, padx=3, pady=3)

    def _build_status_bar(self, parent: ttk.Frame) -> None:
        """Build the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(status_frame, textvariable=self._status_var,
                  style="Status.TLabel", wraplength=650).pack(side="left")

        # Queue counter
        self._counter_label = ttk.Label(
            status_frame, text="", style="Status.TLabel",
        )
        self._counter_label.pack(side="right")

    def _build_buttons(self, parent: ttk.Frame) -> None:
        """Build the control buttons."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x")

        # Left buttons
        left = ttk.Frame(frame)
        left.pack(side="left")

        self._start_btn = ttk.Button(
            left, text="▶️ Start Download",
            command=self._start_downloads, style="Success.TButton",
        )
        self._start_btn.pack(side="left", padx=(0, 5))

        self._pause_btn = ttk.Button(
            left, text="⏸️ Pause",
            command=self._toggle_pause, style="Accent.TButton", state="disabled",
        )
        self._pause_btn.pack(side="left", padx=5)

        ttk.Button(
            left, text="⏹️ Cancel",
            command=self._cancel_downloads, style="Danger.TButton",
        ).pack(side="left", padx=5)

        self._retry_btn = ttk.Button(
            left, text="🔄 Retry", command=self._retry_failed,
            style="Accent.TButton",
        )
        self._retry_btn.pack(side="left", padx=5)

        # Right buttons
        right = ttk.Frame(frame)
        right.pack(side="right")

        ttk.Button(
            right, text="📂 Open Folder",
            command=lambda: open_folder(self._output_dir_var.get()),
            style="Secondary.TButton",
        ).pack(side="right", padx=5)

        self._open_last_btn = ttk.Button(
            right, text="🎬 Open Last File",
            command=self._open_last_file, style="Secondary.TButton",
        )
        self._open_last_btn.pack(side="right", padx=5)

    # ========================================================
    # Callbacks Setup
    # ========================================================

    def _setup_callbacks(self) -> None:
        """Register download service callbacks."""
        self.download_service.set_callbacks(
            on_progress=self._on_download_progress,
            on_complete=self._on_download_complete,
            on_error=self._on_download_error,
            on_queue_changed=self._update_queue_display,
            on_status_changed=self._on_status_changed,
            on_all_complete=self._on_all_downloads_complete,
        )

    def _setup_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        self.root.bind("<Return>", lambda e: self._add_to_queue())
        self.root.bind("<Control-v>", lambda e: self._paste_url())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<Delete>", lambda e: self._clear_queue())
        self.root.bind("<Control-b>", lambda e: self._show_batch_dialog())
        self.root.bind("<Control-s>", lambda e: self._show_settings())
        self.root.bind("<Control-o>", lambda e: self._select_output_dir())
        self.root.bind("<F1>", lambda e: self._show_help())
        self.root.bind("<F5>", lambda e: self._start_downloads())
        self.root.bind("<Escape>", lambda e: self._cancel_downloads())

    # ========================================================
    # Context Menu
    # ========================================================

    def _show_queue_context_menu(self, event) -> None:
        """Show right-click context menu in the queue."""
        try:
            self._queue_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._queue_context_menu.grab_release()

    def _get_queue_selected_index(self) -> int:
        """Get the selected line index in the queue text widget."""
        try:
            pos = self.queue_text.index(tk.INSERT)
            line = int(pos.split(".")[0]) - 1
            return line
        except Exception:
            return -1

    def _remove_selected_from_queue(self) -> None:
        """Remove the selected item from the queue."""
        idx = self._get_queue_selected_index()
        if idx >= 0:
            removed = self.download_service.remove_from_queue(idx)
            if removed:
                self._status_var.set(f"🗑️ Removed: {removed.title}")
                self._update_queue_display()

    def _move_queue_item(self, direction: int) -> None:
        """Move a queue item up or down."""
        idx = self._get_queue_selected_index()
        new_idx = idx + direction
        if idx >= 0:
            self.download_service.move_in_queue(idx, new_idx)
            self._update_queue_display()

    # ========================================================
    # Actions
    # ========================================================

    def _add_to_queue(self) -> None:
        """Add a URL to the download queue."""
        url = self._url_var.get().strip()
        if not url:
            return

        if not is_valid_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return

        # Check for duplicates
        if self.download_service.is_duplicate(url):
            messagebox.showwarning("Duplicate", "This URL is already in the queue!")
            return

        self._status_var.set("🔍 Getting video info...")
        self._url_var.set("")

        # Check if playlist
        if is_playlist_url(url):
            threading.Thread(
                target=self._process_playlist, args=(url,), daemon=True,
            ).start()
        else:
            threading.Thread(
                target=self._process_single_url, args=(url,), daemon=True,
            ).start()

    def _process_single_url(self, url: str) -> None:
        """Process a single URL (background thread)."""
        try:
            info = self.download_service.get_video_info(url)
            item = DownloadItem(
                video_info=info,
                format=DownloadFormat(self._format_var.get()),
                quality=self._quality_var.get(),
            )
            added = self.download_service.add_to_queue(item)

            if added:
                self.root.after(0, lambda i=info: self._on_url_added(i))
            else:
                self.root.after(0, lambda: self._status_var.set("⚠️ Duplicate URL — skipped"))

        except Exception as e:
            self.root.after(0, lambda: self._status_var.set(f"❌ Error: {str(e)}"))

    def _process_playlist(self, url: str) -> None:
        """Process a playlist URL (background thread)."""
        try:
            items = self.download_service.get_playlist_items(url)
            count = 0
            skipped = 0
            for video_info in items:
                item = DownloadItem(
                    video_info=video_info,
                    format=DownloadFormat(self._format_var.get()),
                    quality=self._quality_var.get(),
                )
                if self.download_service.add_to_queue(item):
                    count += 1
                else:
                    skipped += 1

            msg = f"✅ Playlist: {count} videos added"
            if skipped > 0:
                msg += f" ({skipped} duplicates skipped)"
            self.root.after(0, lambda: self._status_var.set(msg))
            self.root.after(0, self._update_queue_display)

        except Exception as e:
            self.root.after(0, lambda: self._status_var.set(f"❌ Playlist error: {str(e)}"))

    def _on_url_added(self, info: VideoInfo) -> None:
        """Called when a URL is successfully added (main thread)."""
        self._status_var.set(f"✅ Added: {info.title}")
        self._update_queue_display()

        # Video card
        self.video_card.set_info(
            title=info.title,
            uploader=info.uploader,
            duration=info.duration_str,
            filesize=info.filesize_str,
        )

        # Thumbnail
        if info.thumbnail_url:
            self.thumbnail_service.get_thumbnail(
                info.url, info.thumbnail_url,
                lambda url, img: self.root.after(0, lambda: self.video_card.set_thumbnail(img)),
            )

    def _start_downloads(self) -> None:
        """Start downloading."""
        if self.download_service.queue_count == 0:
            messagebox.showinfo("Info", "Queue is empty! Add some URLs first.")
            return

        if self.download_service.is_running:
            return

        # Update settings
        self.settings.output_dir = self._output_dir_var.get()

        # Speed limit
        speed_name = self._speed_limit_var.get()
        for name, value in SPEED_LIMITS:
            if name == speed_name:
                self.settings.speed_limit = value
                break

        # Subtitle settings
        self.settings.subtitle_enabled = self._subtitle_var.get()
        self.settings.embed_subtitles = self._embed_subs_var.get()
        lang_name = self._subtitle_lang_var.get()
        for name, code in SUBTITLE_LANGUAGES:
            if name == lang_name:
                self.settings.subtitle_language = code
                break

        self._download_start_time = __import__("time").time()
        self.download_service.start()
        self._start_btn.config(state="disabled")
        self._pause_btn.config(state="normal")
        self._status_var.set("⬇️ Downloading...")

    def _toggle_pause(self) -> None:
        """Toggle pause/resume."""
        if self.download_service.is_paused:
            self.download_service.resume()
            self._pause_btn.config(text="⏸️ Pause")
            self._status_var.set("▶️ Download resumed")
        else:
            self.download_service.pause()
            self._pause_btn.config(text="▶️ Resume")
            self._status_var.set("⏸️ Download paused")

    def _cancel_downloads(self) -> None:
        """Cancel all downloads."""
        if self.download_service.is_running:
            if messagebox.askyesno("Cancel", "Cancel all downloads?"):
                self.download_service.cancel()
                self._reset_download_ui()
                self._status_var.set("🚫 Downloads cancelled")

    def _retry_failed(self) -> None:
        """Retry failed downloads."""
        count = self.download_service.retry_failed()
        if count > 0:
            self._status_var.set(f"🔄 {count} download(s) re-queued")
            self._update_queue_display()
        else:
            self._status_var.set("No failed downloads to retry")

    def _remove_completed(self) -> None:
        """Remove completed items from queue."""
        count = self.download_service.remove_completed()
        if count > 0:
            self._status_var.set(f"✅ {count} completed item(s) removed")
            self._update_queue_display()

    def _clear_queue(self) -> None:
        """Clear the download queue."""
        self.download_service.clear_queue()
        self.queue_text.delete("1.0", tk.END)
        self.video_card.clear()
        self.progress_card.reset()
        self._status_var.set("Queue cleared")

    def _clear_history(self) -> None:
        """Clear download history."""
        if messagebox.askyesno("Clear History", "Clear all download history?"):
            self.history_service.clear()
            self.history_text.delete("1.0", tk.END)
            self._update_tab_labels()
            self._status_var.set("History cleared")

    def _clear_cache(self) -> None:
        """Clear all caches."""
        self.download_service.clear_cache()
        self.thumbnail_service.clear_cache()
        self._status_var.set("🗑️ Cache cleared")

    def _reset_download_ui(self) -> None:
        """Reset download UI to initial state."""
        self._start_btn.config(state="normal")
        self._pause_btn.config(state="disabled", text="⏸️ Pause")
        self.progress_card.reset()

    # ========================================================
    # Download Callbacks (background thread -> main thread)
    # ========================================================

    def _on_download_progress(self, item: DownloadItem, progress: DownloadProgress) -> None:
        """Progress callback (called from background thread)."""
        self.root.after(0, lambda p=progress, i=item: self._update_progress_ui(i, p))

    def _update_progress_ui(self, item: DownloadItem, progress: DownloadProgress) -> None:
        """Update progress UI (main thread)."""
        self.progress_card.update_progress(
            percent=progress.percent,
            status=f"⬇️ {item.title}",
            speed=item.speed_str,
            eta=item.eta_str,
        )
        self._update_counter()

    def _on_download_complete(self, item: DownloadItem) -> None:
        """Called when a download completes (background thread)."""
        self.history_service.add(item.to_history_dict())
        self.root.after(0, lambda i=item: self._on_complete_ui(i))

    def _on_complete_ui(self, item: DownloadItem) -> None:
        """Update UI when download completes (main thread)."""
        self.progress_card.set_complete()
        self._status_var.set(f"✅ Downloaded: {item.title}")
        self.history_text.insert(tk.END,
            f"{item.completed_at} — {item.title} ({item.video_info.filesize_str})\n", "success")
        self.history_text.see(tk.END)
        self._update_queue_display()
        self._update_tab_labels()
        self._update_counter()

    def _on_download_error(self, item: DownloadItem, error: str) -> None:
        """Called on download error (background thread)."""
        self.root.after(0, lambda e=error, i=item: self._on_error_ui(i, e))

    def _on_error_ui(self, item: DownloadItem, error: str) -> None:
        """Update UI on error (main thread)."""
        self.progress_card.set_error(error[:80])
        self._status_var.set(f"❌ Error: {item.title}")
        self._update_queue_display()
        self._update_counter()

    def _on_status_changed(self, item: DownloadItem) -> None:
        """Status change callback."""
        self.root.after(0, self._update_queue_display)

    def _on_all_downloads_complete(self) -> None:
        """Called when all downloads are finished (background thread)."""
        self.root.after(0, self._all_downloads_complete_ui)

    def _all_downloads_complete_ui(self) -> None:
        """Handle completion of all downloads (main thread)."""
        self._reset_download_ui()

        # Calculate elapsed time
        elapsed = ""
        if self._download_start_time:
            import time
            secs = int(time.time() - self._download_start_time)
            mins, secs = divmod(secs, 60)
            elapsed = f" ({mins}m {secs}s)" if mins > 0 else f" ({secs}s)"

        completed = self.download_service.completed_count
        failed = self.download_service.failed_count

        summary = f"🎉 Done: {completed} downloaded"
        if failed > 0:
            summary += f", {failed} failed"
        summary += elapsed

        self._status_var.set(summary)

        if completed > 0 and failed == 0:
            if messagebox.askyesno("Success", f"All {completed} downloads completed!{elapsed}\nOpen folder?"):
                open_folder(self._output_dir_var.get())
        elif failed > 0:
            if messagebox.askyesno("Partial", f"{completed} downloaded, {failed} failed.\nRetry failed downloads?"):
                self._retry_failed()
                self._start_downloads()

    # ========================================================
    # UI Updates
    # ========================================================

    def _update_queue_display(self) -> None:
        """Refresh the queue display."""
        self.queue_text.delete("1.0", tk.END)
        for item in self.download_service.queue:
            icon = item.status_icon
            progress_str = f" [{item.progress:.0f}%]" if item.progress > 0 else ""

            # Color by status
            if item.status == DownloadStatus.DOWNLOADING:
                tag = "info"
            elif item.status == DownloadStatus.COMPLETED:
                tag = "success"
            elif item.status == DownloadStatus.FAILED:
                tag = "error"
            elif item.status == DownloadStatus.PAUSED:
                tag = "warning"
            else:
                tag = "dim"

            error_str = f" — {item.error_message[:50]}" if item.error_message else ""
            self.queue_text.insert(
                tk.END,
                f"{icon} {item.title}{progress_str}{error_str}\n",
                tag,
            )
        self._update_tab_labels()
        self._update_counter()

    def _update_tab_labels(self) -> None:
        """Update tab header labels."""
        try:
            self._queue_notebook.tab(0, text=f"📥 Queue ({self.download_service.queue_count})")
            self._queue_notebook.tab(1, text=f"📜 History ({self.history_service.count})")
        except Exception:
            pass

    def _update_counter(self) -> None:
        """Update the counter label."""
        pending = self.download_service.pending_count
        total = self.download_service.queue_count
        completed = self.download_service.completed_count
        failed = self.download_service.failed_count

        parts = []
        if total > 0:
            parts.append(f"📥 {total}")
        if completed > 0:
            parts.append(f"✅ {completed}")
        if failed > 0:
            parts.append(f"❌ {failed}")
        if pending > 0:
            parts.append(f"⏳ {pending}")

        self._counter_label.config(text="  ".join(parts))

    def _load_history(self) -> None:
        """Load and display previous history."""
        for item in self.history_service.items:
            completed = item.get("completed_at", "")
            title = item.get("title", "Unknown")
            size = item.get("filesize_str", "")
            self.history_text.insert(tk.END, f"{completed} — {title} ({size})\n", "dim")
        self._update_tab_labels()

    # ========================================================
    # Helpers
    # ========================================================

    def _select_output_dir(self) -> None:
        """Select save directory."""
        path = filedialog.askdirectory(
            initialdir=self._output_dir_var.get(),
            title="Select Save Location",
        )
        if path:
            self._output_dir_var.set(path)
            self.settings.output_dir = path
            self.settings.save()
            self._status_var.set(f"📂 Save location: {path}")

    def _paste_url(self) -> None:
        """Paste URL from clipboard."""
        try:
            text = self.root.clipboard_get().strip()
            if text:
                self._url_var.set(text)
                # Auto-focus if valid URL
                if is_valid_youtube_url(text):
                    self._url_entry.focus_set()
        except tk.TclError:
            pass

    def _on_format_change(self) -> None:
        """Update quality combo when format changes."""
        if self._format_var.get() == "audio":
            self._quality_combo.config(state="disabled")
        else:
            self._quality_combo.config(state="readonly")

    def _on_subtitle_toggle(self) -> None:
        """Handle subtitle checkbox toggle."""
        state = "readonly" if self._subtitle_var.get() else "disabled"
        self._sub_lang_combo.config(state=state)
        self._embed_check.config(
            state="normal" if self._subtitle_var.get() else "disabled"
        )

    def _open_last_file(self) -> None:
        """Open the most recently downloaded file."""
        if self.history_service.count > 0:
            last = self.history_service.items[-1]
            filepath = last.get("filepath")
            if filepath and open_file(filepath):
                return
        messagebox.showinfo("Info", "No downloaded file found")

    def _monitor_clipboard(self) -> None:
        """Monitor clipboard for YouTube URLs."""
        try:
            current = self.root.clipboard_get().strip()
            if current != self._clipboard_last and is_valid_youtube_url(current):
                self._clipboard_last = current
                self._url_var.set(current)
                self._status_var.set("📋 YouTube URL detected in clipboard!")
        except (tk.TclError, Exception):
            pass

        self.root.after(2000, self._monitor_clipboard)

    # ========================================================
    # Dialogs
    # ========================================================

    def _show_settings(self) -> None:
        SettingsDialog(self.root, self.settings, on_save=self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        self._format_var.set(self.settings.format)
        self._quality_var.set(self.settings.video_quality)
        self._subtitle_var.set(self.settings.subtitle_enabled)
        self._embed_subs_var.set(self.settings.embed_subtitles)
        self._status_var.set("⚙️ Settings saved")

    def _show_batch_dialog(self) -> None:
        BatchURLDialog(self.root, on_submit=self._on_batch_submit)

    def _on_batch_submit(self, urls: List[str]) -> None:
        valid_count = 0
        for url in urls:
            if is_valid_youtube_url(url):
                threading.Thread(
                    target=self._process_single_url, args=(url,), daemon=True,
                ).start()
                valid_count += 1
        self._status_var.set(f"📋 {valid_count}/{len(urls)} URLs processing...")

    def _show_statistics(self) -> None:
        stats = self.history_service.get_stats()
        text = (
            f"📊 Download Statistics\n\n"
            f"📥 Total Downloads: {stats['total_downloads']}\n"
            f"🎬 Videos: {stats['video_downloads']}\n"
            f"🎵 Audio: {stats['audio_downloads']}\n"
            f"💾 Total Size: {stats['total_size_str']}\n"
            f"\n--- Current Session ---\n"
            f"✅ Completed: {self.download_service.completed_count}\n"
            f"❌ Failed: {self.download_service.failed_count}\n"
            f"📥 In Queue: {self.download_service.queue_count}\n"
        )
        messagebox.showinfo("Statistics", text)

    def _check_ffmpeg_dialog(self) -> None:
        if check_ffmpeg():
            messagebox.showinfo("FFmpeg", "✅ FFmpeg found!\nAudio and subtitle features are available.")
        else:
            messagebox.showwarning("FFmpeg", (
                "⚠️ FFmpeg not found!\n\n"
                "FFmpeg is required for audio downloads and subtitle embedding.\n\n"
                "Installation:\n"
                "• Windows: https://ffmpeg.org/download.html\n"
                "• macOS: brew install ffmpeg\n"
                "• Linux: sudo apt install ffmpeg"
            ))

    def _show_help(self) -> None:
        help_text = f"""{APP_ICON} {APP_NAME} v{APP_VERSION}

Usage:
1. Enter YouTube URL (or paste with Ctrl+V)
2. Select format (Video/Audio) and quality
3. Click "Add" to queue the video
4. Click "Start Download" to begin (F5)

Features:
• Video & Audio download (MP4/MP3)
• Playlist support (auto-detect)
• Batch URL import (Ctrl+B)
• Clipboard monitoring (auto-paste)
• Subtitle download & embedding
• Speed limiting
• Download queue with retry
• Persistent history (JSON/CSV export)
• Right-click context menu in queue
• FFmpeg status indicator
• Duplicate URL prevention
"""
        messagebox.showinfo("Help", help_text)

    def _show_shortcuts(self) -> None:
        shortcuts = """⌨️ Keyboard Shortcuts:

Enter     — Add URL to queue
Ctrl+V    — Paste URL from clipboard
Ctrl+B    — Batch add URLs
Ctrl+S    — Open Settings
Ctrl+O    — Change save location
Ctrl+Q    — Quit application
F1        — Show Help
F5        — Start Download
Escape    — Cancel Download
Delete    — Clear Queue

Mouse:
Right Click — Context menu (Queue tab)
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _show_about(self) -> None:
        messagebox.showinfo("About", (
            f"{APP_ICON} {APP_NAME}\n"
            f"Version {APP_VERSION}\n\n"
            f"Built with Python, Tkinter & yt-dlp\n"
            f"Catppuccin Mocha Theme\n\n"
            f"Features:\n"
            f"• Retry logic (3 attempts)\n"
            f"• Thread-safe downloads\n"
            f"• Persistent history\n"
            f"• FFmpeg integration\n\n"
            f"MIT License — © 2024-2026 mpython77"
        ))

    def _export_json(self) -> None:
        if self.history_service.count == 0:
            messagebox.showinfo("Info", "No history to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")], title="Export History")
        if path and self.history_service.export_json(path):
            self._status_var.set(f"📤 Exported: {path}")

    def _export_csv(self) -> None:
        if self.history_service.count == 0:
            messagebox.showinfo("Info", "No history to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Export History")
        if path and self.history_service.export_csv(path):
            self._status_var.set(f"📤 Exported: {path}")

    def _on_closing(self) -> None:
        """Handle application close."""
        if self.download_service.is_running:
            if not messagebox.askokcancel("Exit", "Download in progress. Exit anyway?"):
                return

        # Save window dimensions
        self.settings.window_width = self.root.winfo_width()
        self.settings.window_height = self.root.winfo_height()
        self.settings.save()

        self.download_service.cancel()
        self.root.destroy()
