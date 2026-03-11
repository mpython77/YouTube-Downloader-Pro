"""
YouTube Downloader Pro — UI Styles

Catppuccin Mocha theme and all ttk styles.
"""

from tkinter import ttk

from config import THEME, COLORS


def setup_styles() -> ttk.Style:
    """Configure all ttk styles.

    Returns:
        Configured ttk.Style object.
    """
    style = ttk.Style()
    style.theme_use("clam")

    # ========================================================
    # Base Styles
    # ========================================================

    style.configure("TFrame", background=THEME["bg"])

    style.configure(
        "TLabel",
        background=THEME["bg"],
        foreground=THEME["text"],
        font=("Segoe UI", 10),
    )

    style.configure(
        "Header.TLabel",
        font=("Segoe UI", 22, "bold"),
        foreground=THEME["accent"],
        background=THEME["bg"],
    )

    style.configure(
        "SubHeader.TLabel",
        font=("Segoe UI", 12, "bold"),
        foreground=THEME["secondary"],
        background=THEME["bg"],
    )

    style.configure(
        "Status.TLabel",
        font=("Segoe UI", 9),
        foreground=THEME["text_dim"],
        background=THEME["bg"],
    )

    style.configure(
        "Success.TLabel",
        foreground=THEME["success"],
        background=THEME["bg"],
        font=("Segoe UI", 10, "bold"),
    )

    style.configure(
        "Error.TLabel",
        foreground=THEME["error"],
        background=THEME["bg"],
        font=("Segoe UI", 10),
    )

    style.configure(
        "Warning.TLabel",
        foreground=THEME["warning"],
        background=THEME["bg"],
        font=("Segoe UI", 10),
    )

    style.configure(
        "Info.TLabel",
        foreground=THEME["info"],
        background=THEME["bg"],
        font=("Segoe UI", 10),
    )

    # ========================================================
    # Buttons
    # ========================================================

    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        background=THEME["accent"],
        foreground=COLORS["crust"],
        padding=(12, 6),
        borderwidth=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", THEME["accent_hover"]), ("disabled", THEME["surface"])],
        foreground=[("disabled", THEME["text_dim"])],
    )

    style.configure(
        "Secondary.TButton",
        font=("Segoe UI", 10),
        background=THEME["secondary"],
        foreground=COLORS["crust"],
        padding=(10, 5),
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", COLORS["sapphire"]), ("disabled", THEME["surface"])],
    )

    style.configure(
        "Danger.TButton",
        font=("Segoe UI", 10),
        background=THEME["error"],
        foreground=COLORS["crust"],
        padding=(10, 5),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", COLORS["maroon"])],
    )

    style.configure(
        "Success.TButton",
        font=("Segoe UI", 10, "bold"),
        background=THEME["success"],
        foreground=COLORS["crust"],
        padding=(12, 6),
        borderwidth=0,
    )
    style.map(
        "Success.TButton",
        background=[("active", COLORS["teal"]), ("disabled", THEME["surface"])],
    )

    style.configure(
        "Ghost.TButton",
        font=("Segoe UI", 9),
        background=THEME["bg"],
        foreground=THEME["text_dim"],
        padding=(8, 4),
        borderwidth=0,
    )
    style.map(
        "Ghost.TButton",
        background=[("active", THEME["surface"])],
        foreground=[("active", THEME["text"])],
    )

    # ========================================================
    # Progress Bar
    # ========================================================

    style.configure(
        "TProgressbar",
        thickness=28,
        troughcolor=THEME["surface"],
        background=THEME["accent"],
        borderwidth=0,
    )

    style.configure(
        "Success.Horizontal.TProgressbar",
        background=THEME["success"],
        troughcolor=THEME["surface"],
    )

    # ========================================================
    # Entry & Combobox
    # ========================================================

    style.configure(
        "TEntry",
        fieldbackground=THEME["surface"],
        foreground=THEME["text"],
        insertcolor=THEME["text"],
        font=("Segoe UI", 11),
        borderwidth=1,
        relief="flat",
    )

    style.configure(
        "TCombobox",
        fieldbackground=THEME["surface"],
        foreground=THEME["text"],
        font=("Segoe UI", 10),
        borderwidth=1,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", THEME["surface"])],
        foreground=[("readonly", THEME["text"])],
    )

    # ========================================================
    # Checkbutton & Radiobutton
    # ========================================================

    style.configure(
        "TCheckbutton",
        background=THEME["bg"],
        foreground=THEME["text"],
        font=("Segoe UI", 10),
    )
    style.map(
        "TCheckbutton",
        background=[("active", THEME["bg"])],
    )

    style.configure(
        "TRadiobutton",
        background=THEME["bg"],
        foreground=THEME["text"],
        font=("Segoe UI", 10),
    )
    style.map(
        "TRadiobutton",
        background=[("active", THEME["bg"])],
    )

    # ========================================================
    # Notebook (Tabs)
    # ========================================================

    style.configure(
        "TNotebook",
        background=THEME["bg"],
        borderwidth=0,
    )

    style.configure(
        "TNotebook.Tab",
        background=THEME["surface"],
        foreground=THEME["text"],
        padding=[14, 6],
        font=("Segoe UI", 10),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", THEME["accent"])],
        foreground=[("selected", COLORS["crust"])],
    )

    # ========================================================
    # LabelFrame
    # ========================================================

    style.configure(
        "TLabelframe",
        background=THEME["bg"],
        foreground=THEME["accent"],
        borderwidth=1,
        relief="groove",
    )
    style.configure(
        "TLabelframe.Label",
        background=THEME["bg"],
        foreground=THEME["accent"],
        font=("Segoe UI", 10, "bold"),
    )

    # ========================================================
    # Separator
    # ========================================================

    style.configure(
        "TSeparator",
        background=THEME["surface"],
    )

    return style
