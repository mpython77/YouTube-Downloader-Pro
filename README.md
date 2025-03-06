# YouTube Downloader Pro

A feature-rich, GUI-based YouTube downloader built with Python, Tkinter, and yt_dlp. This application allows users to download YouTube videos and audio files with customizable options such as format, quality, subtitles, and speed limits. It supports queuing multiple downloads, viewing download history, and exporting download lists.

## Features
- **Download Formats:** Choose between video (MP4) or audio (MP3) formats.
- **Video Quality:** Select resolutions (Best, 2160p, 1440p, 1080p, 720p, 480p, 360p).
- **Subtitles:** Download subtitles in multiple languages and optionally embed them into the video.
- **Speed Limiting:** Control download speed (e.g., 500K, 1M, 2M, 5M, 10M).
- **Queue Management:** Add multiple URLs to a download queue and process them sequentially.
- **Download History:** Track completed downloads with timestamps and file paths.
- **Thumbnail Preview:** Displays video thumbnails when URLs are added.
- **Export List:** Save download history as a JSON file.
- **Cross-Platform:** Works on Windows, macOS, and Linux.
- **Modern UI:** A sleek, dark-themed interface with progress bars and status updates.

## Prerequisites
Before running the application, ensure you have the following installed:

### Required Software:
- **Python 3.7 or higher**
- **FFmpeg** (required for audio extraction and subtitle embedding):
  - Install on Windows: Download from the FFmpeg website and add it to `PATH`.
  - Install on macOS: `brew install ffmpeg`
  - Install on Linux: `sudo apt install ffmpeg` (Ubuntu/Debian) or the equivalent for your distro.

### Required Python Packages:
Install dependencies via pip:
```bash
pip install yt-dlp tkinter pillow requests
```

## Installation
Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-downloader-pro.git
cd youtube-downloader-pro
```
Install dependencies:
```bash
pip install -r requirements.txt
```
*(Ensure `requirements.txt` contains yt-dlp, pillow, and requests if not already present.)*

Run the application:
```bash
python youtube_downloader_pro.py
```

## Usage
1. Launch the application:
   ```bash
   python youtube_downloader_pro.py
   ```
2. Enter a YouTube URL in the input field.
3. Choose your download settings:
   - **Format:** Video (MP4) or Audio (MP3)
   - **Quality:** Select resolution for videos
   - **Subtitles:** Enable and choose language (optional embedding)
   - **Speed Limit:** Set a download speed cap (optional)
4. Click **"Add"** to queue the video.
5. Click **"Start Download"** to begin downloading.
6. Monitor progress via the progress bar and status updates.
7. Additional features:
   - Pause/Resume downloads
   - Clear the queue
   - Open the last downloaded file or folder
   - Export the download history

## Screenshots
*(Add screenshots here if available, such as the main window, queue tab, etc.)*
![image](https://github.com/user-attachments/assets/2db61f18-6cf7-415a-8bd1-28bae174c632)

## Code Structure
- **ImprovedYouTubeDownloader Class:** Main application logic with GUI setup and download functionality.
- **GUI Components:** Uses Tkinter with custom styles for a modern look.
- **Download Handling:** Leverages yt_dlp for downloading and threading for non-blocking operations.
- **File Management:** Handles output directories, file paths, and history tracking.



## License
This project is licensed under the **GPL-3.0 ** - see the `LICENSE` file for details.

## Acknowledgments
- **yt-dlp** for YouTube downloading capabilities.
- **Tkinter** for the GUI framework.
- **Pillow** for image processing.

