"""
YouTube Downloader Pro — Entry Point

Application startup: logging, settings, main window.
"""

import tkinter as tk
from config import APP_NAME, setup_logging, AppSettings
from ui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    logger = setup_logging()
    logger.info(f"Starting {APP_NAME}")

    settings = AppSettings.load()

    root = tk.Tk()
    app = MainWindow(root, settings)
    root.mainloop()


if __name__ == "__main__":
    main()
