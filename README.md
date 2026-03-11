# 🎬 YouTube Downloader Pro v2.0

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-103%20passed-brightgreen.svg)](tests/)

A professional YouTube downloader built with Python, Tkinter, and yt-dlp. Features a beautiful Catppuccin Mocha-themed UI, thread-safe downloads, retry logic, persistent history, and a modular MVC architecture.

---

## ✨ Features

### Core
- 🎬 **Video Download** — MP4 (360p to 4K)
- 🎵 **Audio Download** — MP3 (96–320 kbps)
- 📋 **Playlist Support** — auto-detection & batch download
- 📝 **Subtitle Download** — 11 languages, auto-subtitles, embedding

### Smart Queue
- 🔄 **Retry Logic** — automatic 3-attempt retry with delay
- 🚫 **Duplicate Detection** — prevents adding the same URL twice
- ⏸️ **Real Pause/Resume** — thread-based, doesn't restart
- 🗂️ **Context Menu** — right-click to retry, remove, reorder
- ✅ **Remove Completed** / 🔄 **Retry Failed** buttons

### Performance
- 💾 **Video Info Cache** — no redundant yt-dlp calls
- 🖼️ **Thumbnail Cache** — in-memory async loading
- ⚡ **Speed Limiting** — 500KB/s to 20MB/s
- 🔧 **FFmpeg Integration** — status indicator in header

### UI & UX
- 🎨 **Catppuccin Mocha** dark theme
- 📊 **Session Counters** — completed/failed/pending
- ⏱️ **Download Timer** — total elapsed time
- ⌨️ **Keyboard Shortcuts** — F5, Escape, Ctrl+V, Ctrl+B, etc.
- 📋 **Clipboard Monitor** — auto-detect YouTube URLs
- 📜 **Persistent History** — JSON/CSV export

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Add URL to queue |
| `F5` | Start download |
| `Escape` | Cancel download |
| `Ctrl+V` | Paste URL from clipboard |
| `Ctrl+B` | Batch add URLs |
| `Ctrl+S` | Open settings |
| `Ctrl+O` | Change save location |
| `Ctrl+Q` | Quit |
| `F1` | Show help |
| `Delete` | Clear queue |
| Right Click | Context menu (queue) |

---

## 📁 Project Structure

```
YouTube-Downloader-Pro/
├── main.py                  # Entry point
├── config.py                # Settings, theme, logging
├── models.py                # Dataclass models + enums
├── services/
│   ├── downloader.py        # Thread-safe yt-dlp wrapper
│   ├── thumbnail.py         # Async thumbnail + cache
│   └── history.py           # Persistent JSON history
├── ui/
│   ├── styles.py            # Catppuccin Mocha theme
│   ├── components.py        # Reusable widgets + dialogs
│   └── main_window.py       # Main GUI (MVC)
├── utils/
│   ├── validators.py        # URL validation
│   └── file_utils.py        # Cross-platform file ops
├── tests/                   # 103 unit tests
│   ├── test_models.py
│   ├── test_validators.py
│   ├── test_history.py
│   ├── test_downloader.py
│   └── test_app.py
├── requirements.txt
├── LICENSE                  # MIT — no restrictions
└── README.md
```

---

## 🚀 Getting Started

### Requirements
- Python 3.10+
- FFmpeg (optional, required for audio & subtitles)

### Installation

```bash
git clone https://github.com/mpython77/YouTube-Downloader-Pro.git
cd YouTube-Downloader-Pro
pip install -r requirements.txt
python main.py
```

### Running Tests

```bash
python -m pytest tests/ -v
```

---

## 📜 License

MIT License — free for personal and commercial use. See [LICENSE](LICENSE) for details.

---

## 📋 Changelog

### v2.0.0 (2026-03-11)
- Modular MVC architecture (16 files)
- Retry logic (3 attempts + delay)
- Duplicate URL detection
- FFmpeg check & indicator
- Video info caching
- Context menu in queue
- Session counters & timer
- Keyboard shortcuts dialog
- Auto-retry prompt on failure
- 103 unit tests (100% passed)
- Full English codebase
- MIT License
