"""
YouTube Downloader Pro — Custom UI Components

Reusable widgets and dialogs.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Optional, Callable, List, Dict, Any

from config import THEME, COLORS, VIDEO_QUALITIES, AUDIO_QUALITIES, SPEED_LIMITS, SUBTITLE_LANGUAGES


class VideoInfoCard(ttk.Frame):
    """Card widget displaying brief video metadata."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="TFrame")

        self._thumbnail_label = ttk.Label(self, background=THEME["surface"])
        self._thumbnail_label.pack(side="left", padx=(0, 10))

        info_frame = ttk.Frame(self)
        info_frame.pack(side="left", fill="both", expand=True)

        self._title_label = ttk.Label(
            info_frame, text="", font=("Segoe UI", 11, "bold"),
            foreground=THEME["text"], wraplength=400, justify="left",
        )
        self._title_label.pack(anchor="w")

        self._details_label = ttk.Label(
            info_frame, text="", style="Status.TLabel",
        )
        self._details_label.pack(anchor="w", pady=(2, 0))

        self._thumbnail_image = None

    def set_info(
        self,
        title: str = "",
        uploader: str = "",
        duration: str = "",
        filesize: str = "",
    ) -> None:
        """Update the displayed information."""
        self._title_label.config(text=title or "No video selected")
        details = []
        if uploader and uploader != "Unknown":
            details.append(f"👤 {uploader}")
        if duration and duration != "Unknown":
            details.append(f"⏱️ {duration}")
        if filesize and filesize != "Unknown":
            details.append(f"📦 {filesize}")
        self._details_label.config(text="  •  ".join(details) if details else "")

    def set_thumbnail(self, image) -> None:
        """Set the thumbnail image."""
        self._thumbnail_image = image
        self._thumbnail_label.config(image=image)

    def clear(self) -> None:
        """Clear the card contents."""
        self._title_label.config(text="No video selected")
        self._details_label.config(text="")
        self._thumbnail_image = None
        self._thumbnail_label.config(image="")


class DownloadProgressCard(ttk.Frame):
    """Card widget displaying download progress."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style="TFrame")

        # Progress info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", pady=(0, 4))

        self._status_label = ttk.Label(
            info_frame, text="Ready", style="Info.TLabel",
        )
        self._status_label.pack(side="left")

        self._percent_label = ttk.Label(
            info_frame, text="0%", font=("Segoe UI", 10, "bold"),
            foreground=THEME["accent"],
        )
        self._percent_label.pack(side="right")

        # Progress bar
        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            self, variable=self._progress_var, maximum=100,
        )
        self._progress_bar.pack(fill="x", pady=(0, 4))

        # Speed & ETA
        details_frame = ttk.Frame(self)
        details_frame.pack(fill="x")

        self._speed_label = ttk.Label(
            details_frame, text="", style="Status.TLabel",
        )
        self._speed_label.pack(side="left")

        self._eta_label = ttk.Label(
            details_frame, text="", style="Status.TLabel",
        )
        self._eta_label.pack(side="right")

    def update_progress(
        self,
        percent: float = 0,
        status: str = "",
        speed: str = "",
        eta: str = "",
    ) -> None:
        """Update progress information."""
        self._progress_var.set(percent)
        self._percent_label.config(text=f"{percent:.1f}%")
        if status:
            self._status_label.config(text=status)
        self._speed_label.config(text=f"⚡ {speed}" if speed else "")
        self._eta_label.config(text=f"⏳ ETA: {eta}" if eta else "")

    def set_complete(self) -> None:
        """Switch to completed state."""
        self._progress_var.set(100)
        self._percent_label.config(text="100%", foreground=THEME["success"])
        self._status_label.config(text="✅ Completed!", foreground=THEME["success"])
        self._speed_label.config(text="")
        self._eta_label.config(text="")
        self._progress_bar.configure(style="Success.Horizontal.TProgressbar")

    def set_error(self, message: str = "") -> None:
        """Switch to error state."""
        self._status_label.config(text=f"❌ Error: {message}", foreground=THEME["error"])
        self._speed_label.config(text="")
        self._eta_label.config(text="")

    def reset(self) -> None:
        """Reset to initial state."""
        self._progress_var.set(0)
        self._percent_label.config(text="0%", foreground=THEME["accent"])
        self._status_label.config(text="Ready", foreground=THEME["info"])
        self._speed_label.config(text="")
        self._eta_label.config(text="")
        self._progress_bar.configure(style="TProgressbar")


class StyledText(scrolledtext.ScrolledText):
    """Styled text widget with Catppuccin theme."""

    def __init__(self, parent: tk.Widget, **kwargs):
        defaults = {
            "font": ("Cascadia Code", 9),
            "bg": THEME["surface"],
            "fg": THEME["text"],
            "insertbackground": THEME["text"],
            "selectbackground": THEME["accent"],
            "selectforeground": COLORS["crust"],
            "wrap": "word",
            "relief": "flat",
            "borderwidth": 0,
            "padx": 8,
            "pady": 8,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

        # Tag configurations
        self.tag_configure("success", foreground=THEME["success"])
        self.tag_configure("error", foreground=THEME["error"])
        self.tag_configure("warning", foreground=THEME["warning"])
        self.tag_configure("info", foreground=THEME["info"])
        self.tag_configure("accent", foreground=THEME["accent"])
        self.tag_configure("dim", foreground=THEME["text_dim"])


class SettingsDialog(tk.Toplevel):
    """Application settings dialog."""

    def __init__(self, parent: tk.Widget, settings, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self.title("⚙️ Settings")
        self.geometry("500x550")
        self.configure(bg=THEME["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._settings = settings
        self._on_save = on_save

        self._build_ui()
        self._load_current_settings()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="⚙️ Settings", style="Header.TLabel").pack(anchor="w", pady=(0, 15))

        # Download settings
        dl_frame = ttk.LabelFrame(main, text="Download", padding=10)
        dl_frame.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(dl_frame)
        row1.pack(fill="x", pady=(0, 8))
        ttk.Label(row1, text="Default Format:").pack(side="left", padx=(0, 10))
        self._format_var = tk.StringVar()
        ttk.Radiobutton(row1, text="Video (MP4)", variable=self._format_var, value="video").pack(side="left", padx=5)
        ttk.Radiobutton(row1, text="Audio (MP3)", variable=self._format_var, value="audio").pack(side="left", padx=5)

        row2 = ttk.Frame(dl_frame)
        row2.pack(fill="x", pady=(0, 8))
        ttk.Label(row2, text="Video Quality:").pack(side="left", padx=(0, 10))
        self._quality_var = tk.StringVar()
        ttk.Combobox(row2, textvariable=self._quality_var, values=VIDEO_QUALITIES,
                     state="readonly", width=12).pack(side="left")

        row3 = ttk.Frame(dl_frame)
        row3.pack(fill="x", pady=(0, 8))
        ttk.Label(row3, text="Audio Quality:").pack(side="left", padx=(0, 10))
        self._audio_q_var = tk.StringVar()
        ttk.Combobox(row3, textvariable=self._audio_q_var,
                     values=[q[0] for q in AUDIO_QUALITIES],
                     state="readonly", width=20).pack(side="left")

        row4 = ttk.Frame(dl_frame)
        row4.pack(fill="x")
        ttk.Label(row4, text="Speed Limit:").pack(side="left", padx=(0, 10))
        self._speed_var = tk.StringVar()
        ttk.Combobox(row4, textvariable=self._speed_var,
                     values=[s[0] for s in SPEED_LIMITS],
                     state="readonly", width=15).pack(side="left")

        # Subtitle settings
        sub_frame = ttk.LabelFrame(main, text="Subtitles", padding=10)
        sub_frame.pack(fill="x", pady=(0, 10))

        self._sub_enabled = tk.BooleanVar()
        ttk.Checkbutton(sub_frame, text="Download Subtitles", variable=self._sub_enabled).pack(anchor="w")

        sub_row = ttk.Frame(sub_frame)
        sub_row.pack(fill="x", pady=(8, 0))
        ttk.Label(sub_row, text="Language:").pack(side="left", padx=(0, 10))
        self._sub_lang_var = tk.StringVar()
        ttk.Combobox(sub_row, textvariable=self._sub_lang_var,
                     values=[f"{name} ({code})" for name, code in SUBTITLE_LANGUAGES],
                     state="readonly", width=20).pack(side="left")

        self._embed_subs = tk.BooleanVar()
        ttk.Checkbutton(sub_frame, text="Embed subtitles in video", variable=self._embed_subs).pack(anchor="w", pady=(5, 0))

        # General settings
        gen_frame = ttk.LabelFrame(main, text="General", padding=10)
        gen_frame.pack(fill="x", pady=(0, 15))

        self._clipboard_var = tk.BooleanVar()
        ttk.Checkbutton(gen_frame, text="Monitor clipboard for YouTube URLs", variable=self._clipboard_var).pack(anchor="w")

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Save", command=self._save, style="Accent.TButton").pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, style="Ghost.TButton").pack(side="right")

    def _load_current_settings(self) -> None:
        self._format_var.set(self._settings.format)
        self._quality_var.set(self._settings.video_quality)
        self._sub_enabled.set(self._settings.subtitle_enabled)
        self._embed_subs.set(self._settings.embed_subtitles)
        self._clipboard_var.set(self._settings.clipboard_monitor)

        # Audio quality
        for name, code in AUDIO_QUALITIES:
            if code == self._settings.audio_quality:
                self._audio_q_var.set(name)
                break

        # Speed limit
        for name, value in SPEED_LIMITS:
            if value == self._settings.speed_limit:
                self._speed_var.set(name)
                break

        # Subtitle language
        for name, code in SUBTITLE_LANGUAGES:
            if code == self._settings.subtitle_language:
                self._sub_lang_var.set(f"{name} ({code})")
                break

    def _save(self) -> None:
        self._settings.format = self._format_var.get()
        self._settings.video_quality = self._quality_var.get()
        self._settings.subtitle_enabled = self._sub_enabled.get()
        self._settings.embed_subtitles = self._embed_subs.get()
        self._settings.clipboard_monitor = self._clipboard_var.get()

        # Audio quality
        audio_name = self._audio_q_var.get()
        for name, code in AUDIO_QUALITIES:
            if name == audio_name:
                self._settings.audio_quality = code
                break

        # Speed limit
        speed_name = self._speed_var.get()
        for name, value in SPEED_LIMITS:
            if name == speed_name:
                self._settings.speed_limit = value
                break

        # Subtitle language
        lang_str = self._sub_lang_var.get()
        for name, code in SUBTITLE_LANGUAGES:
            if f"{name} ({code})" == lang_str:
                self._settings.subtitle_language = code
                break

        self._settings.save()
        if self._on_save:
            self._on_save()
        self.destroy()


class BatchURLDialog(tk.Toplevel):
    """Dialog for adding multiple URLs at once."""

    def __init__(self, parent: tk.Widget, on_submit: Optional[Callable] = None):
        super().__init__(parent)
        self.title("📋 Batch Add URLs")
        self.geometry("500x400")
        self.configure(bg=THEME["bg"])
        self.transient(parent)
        self.grab_set()

        self._on_submit = on_submit

        main = ttk.Frame(self, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Enter each URL on a new line:",
                  style="TLabel").pack(anchor="w", pady=(0, 8))

        self._text = StyledText(main, height=15)
        self._text.pack(fill="both", expand=True, pady=(0, 10))

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Paste from Clipboard",
                   command=self._paste_clipboard, style="Secondary.TButton").pack(side="left")
        ttk.Button(btn_frame, text="Add All", command=self._submit,
                   style="Accent.TButton").pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy,
                   style="Ghost.TButton").pack(side="right")

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _paste_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
            self._text.insert(tk.END, text)
        except tk.TclError:
            pass

    def _submit(self) -> None:
        text = self._text.get("1.0", tk.END).strip()
        if text and self._on_submit:
            urls = [line.strip() for line in text.splitlines() if line.strip()]
            self._on_submit(urls)
        self.destroy()
