import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
from urllib.parse import urlparse
import time
import webbrowser
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json
from datetime import datetime
import platform
import subprocess

class ImprovedYouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("850x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e2e")
        
        self.url = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="Ready to download")
        self.format_var = tk.StringVar(value="video")
        self.resolution_var = tk.StringVar(value="best")
        self.speed_limit_var = tk.StringVar(value="None")
        self.subtitle_var = tk.BooleanVar(value=False)
        self.subtitle_lang_var = tk.StringVar(value="en")
        self.embed_subs_var = tk.BooleanVar(value=True)
        self.download_queue = []
        self.download_history = []
        self.is_downloading = False
        self.is_paused = False
        self.thumbnail = None
        self.current_download = None
        self.last_file = None
        
        self.setup_styles()
        self.setup_gui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Return>", lambda e: self.add_to_queue())

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        self.colors = {
            "bg": "#1e1e2e",
            "accent": "#cba6f7",
            "secondary": "#89b4fa",
            "text": "#cdd6f4",
            "warning": "#f38ba8",
            "success": "#a6e3a1",
            "surface": "#313244"
        }
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground=self.colors["accent"])
        
        style.configure("Accent.TButton", font=("Segoe UI", 10), 
                       background=self.colors["accent"], foreground="#11111b", padding=6)
        style.map("Accent.TButton", background=[("active", self.colors["secondary"])])
        
        style.configure("Danger.TButton", font=("Segoe UI", 10), 
                       background=self.colors["warning"], foreground="#11111b", padding=6)
        style.map("Danger.TButton", background=[("active", "#eb6f92")])
        
        style.configure("Info.TButton", font=("Segoe UI", 9), 
                       background=self.colors["secondary"], foreground="#11111b", padding=4)
        
        style.configure("TProgressbar", thickness=25, 
                       troughcolor=self.colors["surface"], 
                       background=self.colors["accent"])
        
        style.configure("TCombobox", fieldbackground=self.colors["surface"], 
                       foreground=self.colors["text"], font=("Segoe UI", 10))
        style.map("TCombobox", fieldbackground=[("readonly", self.colors["surface"])])
        
        style.configure("TEntry", fieldbackground=self.colors["surface"], 
                       foreground=self.colors["text"], font=("Segoe UI", 11))
        
        style.configure("TCheckbutton", background=self.colors["bg"], 
                       foreground=self.colors["text"], font=("Segoe UI", 10))
        
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["surface"], 
                       foreground=self.colors["text"], padding=[10, 4])
        style.map("TNotebook.Tab", background=[("selected", self.colors["accent"])],
                 foreground=[("selected", "#11111b")])
        
        style.configure("TLabelframe", background=self.colors["bg"], foreground=self.colors["accent"])
        style.configure("TLabelframe.Label", background=self.colors["bg"], foreground=self.colors["accent"])

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(header_frame, text="🎬 YouTube Downloader Pro", style="Header.TLabel").pack(side="left")
        ttk.Button(header_frame, text="?", style="Info.TButton", command=self.show_help).pack(side="right")

        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(url_frame, text="YouTube URL:").pack(side="left", padx=(0, 10))
        ttk.Entry(url_frame, textvariable=self.url, width=50).pack(side="left", padx=(0, 10), fill="x", expand=True)
        ttk.Button(url_frame, text="Add", command=self.add_to_queue, style="Accent.TButton").pack(side="left", padx=(0, 10))
        self.thumbnail_label = ttk.Label(url_frame, background=self.colors["surface"])
        self.thumbnail_label.pack(side="right")

        options_frame = ttk.LabelFrame(main_frame, text="Download Settings", padding=10)
        options_frame.pack(fill="x", pady=(0, 15))

        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill="x", pady=(0, 10))
        
        left_options = ttk.Frame(format_frame)
        left_options.pack(side="left", fill="x", expand=True)
        
        format_row = ttk.Frame(left_options)
        format_row.pack(fill="x", pady=(0, 10))
        ttk.Label(format_row, text="Format:").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(format_row, text="Video (MP4)", variable=self.format_var, 
                       value="video", command=self.toggle_resolution).pack(side="left", padx=10)
        ttk.Radiobutton(format_row, text="Audio (MP3)", variable=self.format_var, 
                       value="audio", command=self.toggle_resolution).pack(side="left", padx=10)
        
        res_row = ttk.Frame(left_options)
        res_row.pack(fill="x")
        ttk.Label(res_row, text="Quality:").pack(side="left", padx=(0, 10))
        self.res_combo = ttk.Combobox(res_row, textvariable=self.resolution_var, 
                                     values=["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"], 
                                     state="readonly", width=10)
        self.res_combo.pack(side="left", padx=(0, 15))
        
        right_options = ttk.Frame(format_frame)
        right_options.pack(side="right", fill="x", expand=True)
        
        sub_cb_frame = ttk.Frame(right_options)
        sub_cb_frame.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(sub_cb_frame, text="Download Subtitles", 
                       variable=self.subtitle_var, 
                       command=self.toggle_subtitle_options).pack(side="left")
        
        self.sub_options_frame = ttk.Frame(right_options)
        self.sub_options_frame.pack(fill="x")
        
        ttk.Label(self.sub_options_frame, text="Language:").pack(side="left", padx=(0, 5))
        ttk.Combobox(self.sub_options_frame, textvariable=self.subtitle_lang_var, 
                    values=["en", "ru", "uz", "es", "fr", "de", "auto"], 
                    state="readonly", width=8).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(self.sub_options_frame, text="Embed subtitles in video", 
                       variable=self.embed_subs_var).pack(side="left")
        
        self.toggle_subtitle_options()
        
        speed_frame = ttk.Frame(options_frame)
        speed_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(speed_frame, text="Speed Limit:").pack(side="left", padx=(0, 10))
        ttk.Combobox(speed_frame, textvariable=self.speed_limit_var, 
                    values=["None", "500K", "1M", "2M", "5M", "10M"], 
                    state="readonly", width=10).pack(side="left")

        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(output_frame, text="Save to:").pack(side="left", padx=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_dir).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.select_output_dir, 
                  style="Accent.TButton").pack(side="left")

        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill="both", expand=True, pady=(0, 15))

        queue_frame = ttk.Frame(tab_control)
        tab_control.add(queue_frame, text="Queue")
        self.queue_text = scrolledtext.ScrolledText(queue_frame, height=8, font=("Segoe UI", 9), 
                                                  bg=self.colors["surface"], fg=self.colors["text"], 
                                                  wrap="word", relief="flat")
        self.queue_text.pack(fill="both", expand=True, padx=5, pady=5)

        history_frame = ttk.Frame(tab_control)
        tab_control.add(history_frame, text="History")
        self.history_text = scrolledtext.ScrolledText(history_frame, height=8, font=("Segoe UI", 9), 
                                                     bg=self.colors["surface"], fg=self.colors["text"], 
                                                     wrap="word", relief="flat")
        self.history_text.pack(fill="both", expand=True, padx=5, pady=5)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill="x")
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(status_frame, textvariable=self.status, wraplength=810, 
                foreground=self.colors["text"]).pack(anchor="w")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side="left", fill="x")
        
        self.start_btn = ttk.Button(left_buttons, text="Start Download", 
                                  command=self.start_downloads, style="Accent.TButton")
        self.start_btn.pack(side="left", padx=(0, 5))
        
        self.pause_btn = ttk.Button(left_buttons, text="Pause", 
                                  command=self.toggle_pause, style="Accent.TButton", 
                                  state="disabled")
        self.pause_btn.pack(side="left", padx=5)
        
        ttk.Button(left_buttons, text="Clear Queue", 
                 command=self.clear_queue, style="Accent.TButton").pack(side="left", padx=5)
        
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side="right", fill="x")
        
        ttk.Button(right_buttons, text="Open Last File", 
                 command=self.open_last_file, style="Accent.TButton").pack(side="right", padx=5)
        
        ttk.Button(right_buttons, text="Open Folder", 
                 command=lambda: self.open_folder(self.output_dir.get()), 
                 style="Accent.TButton").pack(side="right", padx=5)
        
        ttk.Button(right_buttons, text="Export List", 
                 command=self.export_playlist, style="Accent.TButton").pack(side="right", padx=(0, 5))

    def toggle_resolution(self):
        self.res_combo.config(state="readonly" if self.format_var.get() == "video" else "disabled")

    def toggle_subtitle_options(self):
        for child in self.sub_options_frame.winfo_children():
            child.configure(state="normal" if self.subtitle_var.get() else "disabled")

    def select_output_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.output_dir.get(), 
                                         title="Select Save Location")
        if dir_path:
            self.output_dir.set(dir_path)
            self.status.set(f"Save location: {dir_path}")

    def add_to_queue(self):
        url = self.url.get().strip()
        if not url or not self.validate_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return
        
        self.status.set(f"Getting video info...")
        
        threading.Thread(target=self._process_add_to_queue, args=(url,), daemon=True).start()

    def _process_add_to_queue(self, url):
        try:
            info = self.get_video_info(url)
            title = info.get('title', 'Unknown')
            
            self.root.after(0, lambda: self._update_queue(url, info, title))
        except Exception as e:
            self.root.after(0, lambda: self.status.set(f"Error: {str(e)}"))

    def _update_queue(self, url, info, title):
        self.download_queue.append({'url': url, 'info': info})
        self.queue_text.insert(tk.END, f"{title} ({url})\n")
        self.status.set(f"Added: {title}")
        self.url.set("")
        self.show_thumbnail(url)

    def clear_queue(self):
        self.download_queue.clear()
        self.queue_text.delete(1.0, tk.END)
        self.progress.set(0)
        self.status.set("Queue cleared")
        self.thumbnail_label.config(image="")

    def validate_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc and 
                  ("youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc))

    def show_thumbnail(self, url):
        threading.Thread(target=self._load_thumbnail, args=(url,), daemon=True).start()

    def _load_thumbnail(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                thumb_url = info.get('thumbnail', '')
                if thumb_url:
                    response = requests.get(thumb_url)
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data).resize((120, 90), Image.LANCZOS)
                    thumb = ImageTk.PhotoImage(img)
                    
                    self.root.after(0, lambda: self._set_thumbnail(thumb))
        except Exception as e:
            self.root.after(0, lambda: self.status.set(f"Error loading thumbnail: {str(e)}"))

    def _set_thumbnail(self, thumb):
        self.thumbnail = thumb
        self.thumbnail_label.config(image=self.thumbnail)

    def download_progress_hook(self, d):
        if self.is_paused:
            return
            
        if d['status'] == 'downloading':
            title = d.get('info_dict', {}).get('title', 'Unknown')
            
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                speed = d.get('speed', 0)
                speed_str = f"{speed/1024/1024:.1f} MB/s" if speed else "Unknown"
                eta = d.get('eta', 0)
                eta_str = f"{eta//60}:{eta%60:02d}" if eta else "Unknown"
                
                self.root.after(0, lambda: self._update_progress(percent, title, speed_str, eta_str))
            elif 'downloaded_bytes' in d:
                bytes_str = f"{d['downloaded_bytes']/1024/1024:.1f} MB"
                self.root.after(0, lambda: self.status.set(f"Downloading: {bytes_str} - {title}"))
                
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self._download_finished())

    def _update_progress(self, percent, title, speed_str, eta_str):
        self.progress.set(percent)
        self.status.set(f"Downloading: {percent:.1f}% - {title} - Speed: {speed_str} - ETA: {eta_str}")

    def _download_finished(self):
        self.progress.set(100)
        self.status.set("Download complete, converting...")

    def get_video_info(self, url):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'url': url,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filepath': None,
                'has_subtitles': bool(info.get('subtitles', {}))
            }

    def download(self, url_info):
        url = url_info['url']
        info = url_info['info']
        output_path = self.output_dir.get()
        os.makedirs(output_path, exist_ok=True)
        
        title = info['title']
        self.root.after(0, lambda: self.status.set(f"Downloading: {title}"))

        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.download_progress_hook],
            'quiet': True,
            'noplaylist': False,
            'ignoreerrors': True,
        }

        if self.format_var.get() == "video":
            res = self.resolution_var.get()
            format_str = "bestvideo[height<=2160]+bestaudio/best" if res == "best" else f"bestvideo[height<={res[:-1]}]+bestaudio/best"
            ydl_opts.update({'format': format_str, 'merge_output_format': 'mp4'})
        else:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio', 
                    'preferredcodec': 'mp3', 
                    'preferredquality': '192'
                }],
            })
        
        speed = self.speed_limit_var.get()
        if speed != "None":
            multiplier = 1024 * 1024 if speed.endswith('M') else 1024
            ydl_opts['ratelimit'] = int(speed[:-1]) * multiplier
        
        if self.subtitle_var.get() and self.format_var.get() == "video":
            ydl_opts.update({
                'writesubtitles': True,
                'subtitleslangs': [self.subtitle_lang_var.get()],
                'writeautomaticsub': True,
            })
            
            if self.embed_subs_var.get():
                ydl_opts.update({
                    'embedsubtitles': True,
                    'postprocessors': [{
                        'key': 'FFmpegEmbedSubtitle',
                        'already_have_subtitle': False,
                    }],
                })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            file_ext = 'mp4' if self.format_var.get() == 'video' else 'mp3'
            possible_filename = os.path.join(output_path, f"{title}.{file_ext}")
            
            if not os.path.exists(possible_filename):
                for file in os.listdir(output_path):
                    if file.endswith(f".{file_ext}") and title.split()[0] in file:
                        possible_filename = os.path.join(output_path, file)
                        break
            
            info['filepath'] = possible_filename
            
            self.root.after(0, lambda: self._update_history(info, url, title))
            self.last_file = possible_filename
            return info
            
        except Exception as e:
            self.root.after(0, lambda: self.status.set(f"Download error: {str(e)}"))
            return None

    def _update_history(self, info, url, title):
        self.download_history.append(info)
        self.history_text.insert(tk.END, f"{info['timestamp']} - {title} ({url})\n")

    def start_downloads(self):
        if not self.download_queue or self.is_downloading:
            return
        self.is_downloading = True
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        for url_info in self.download_queue[:]:
            if not self.is_downloading:
                break
                
            self.root.after(0, lambda: self.progress.set(0))
            self.current_download = url_info
            
            result = self.download(url_info)
            if result:
                self.download_queue.pop(0)
                self.root.after(0, lambda: self.queue_text.delete(1.0, "2.0"))
                self.root.after(0, lambda: self.status.set(f"Downloaded: {result['title']}"))
            else:
                break
                
            if self.is_paused:
                self.root.after(0, lambda: self.status.set("Paused"))
                while self.is_paused and self.is_downloading:
                    time.sleep(0.5)
                    
            time.sleep(1)
        
        self.is_downloading = False
        self.is_paused = False
        self.current_download = None
        
        self.root.after(0, lambda: self._downloads_complete())

    def _downloads_complete(self):
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        
        if not self.download_queue:
            self.status.set("All downloads completed!")
            if messagebox.askyesno("Success", "Downloads completed! Open the folder?"):
                self.open_folder(self.output_dir.get())

    def toggle_pause(self):
        if not self.is_downloading:
            return
        self.is_paused = not self.is_paused
        self.pause_btn.config(text="Resume" if self.is_paused else "Pause")
        
        if self.is_paused:
            self.status.set("Download paused")
        else:
            self.status.set("Download resumed")

    def open_last_file(self):
        if self.last_file and os.path.exists(self.last_file):
            webbrowser.open(f"file://{self.last_file}")
        else:
            messagebox.showinfo("Info", "No file has been downloaded yet")

    def export_playlist(self):
        if not self.download_history:
            messagebox.showinfo("Info", "No data to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", 
            filetypes=[("JSON", "*.json")],
            title="Save List"
        )
        
        if file_path:
            export_data = []
            for item in self.download_history:
                export_data.append({
                    'title': item['title'],
                    'url': item['url'],
                    'uploader': item['uploader'],
                    'duration': item['duration'],
                    'timestamp': item['timestamp'],
                    'filepath': item['filepath'],
                })
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
                
            self.status.set(f"List saved: {file_path}")

    def open_folder(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Error", "Folder does not exist")
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Error opening folder: {str(e)}")

    def show_help(self):
        help_text = """🎬 YouTube Downloader Pro

Usage:
1. Enter YouTube video URL
2. Select format (video or audio)
3. Select quality for videos
4. Configure subtitle options if needed
5. Click "Add" to add to queue
6. Click "Start Download" to begin

Subtitle Options:
- Check "Download Subtitles"
- Select desired language
- "Embed subtitles in video" - embeds subtitles into the video file

Other Features:
- Pause/Resume downloads
- Set download speed limits
- Queue multiple videos
- View download history
- Export download list
"""
        messagebox.showinfo("About", help_text)

    def on_closing(self):
        if self.is_downloading and not messagebox.askokcancel(
            "Exit", "Download in progress. Do you want to exit?"
        ):
            return
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImprovedYouTubeDownloader(root)
    root.mainloop()
