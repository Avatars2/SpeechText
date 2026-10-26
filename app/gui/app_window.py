import tkinter as tk
from tkinter import font as tkfont

from app.gui.dashboard import DashboardView
from app.gui.history import HistoryView
from app.utils.constants import (
    BG, SURFACE, SURFACE_ALT, BORDER,
    PRIMARY_BLUE, PRIMARY_BLUE_HOVER,
    SUCCESS, WARNING, DANGER,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, TEXT_LIGHT,
    FONT_FAMILY,
    WIN_WIDTH, WIN_HEIGHT, WIN_MIN_WIDTH, WIN_MIN_HEIGHT, WIN_TITLE,
)


class AppWindow(tk.Tk):
    """
    Root application window with top-right navigation (Home / History)
    and full-width dual-column workspace.
    """

    def __init__(self):
        super().__init__()

        self.title(WIN_TITLE)
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(WIN_MIN_WIDTH, WIN_MIN_HEIGHT)
        self.configure(bg=BG)

        self._center_window()

        self._f_status = tkfont.Font(family=FONT_FAMILY, size=8)

        self._current_tab = "home"
        self._views: dict[str, tk.Frame] = {}

        self._build_layout()
        self._on_navigate("home")

    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - WIN_WIDTH) // 2)
        y = max(0, (sh - WIN_HEIGHT) // 2 - 20)
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+{x}+{y}")

    def _build_layout(self):
        # ── 1. Top Navigation Bar (Logo on left, Home & History on top right) ─
        self._build_top_navbar()

        # ── 2. Bottom Status Bar ───────────────────────────────────────────
        self._build_statusbar()

        # ── 3. Central Content Box for Views ───────────────────────────────
        self._content_box = tk.Frame(self, bg=BG)
        self._content_box.pack(fill="both", expand=True)
        self._content_box.columnconfigure(0, weight=1)
        self._content_box.rowconfigure(0, weight=1)

        # Instantiate Views
        self._dashboard_view = DashboardView(
            self._content_box,
            status_callback=self._update_status,
            navigate_callback=self._on_navigate,
        )
        self._history_view = HistoryView(self._content_box)

        self._views["home"] = self._dashboard_view
        self._views["history"] = self._history_view

        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def _build_top_navbar(self):
        """Builds the top navigation bar with branding on left and Home/History buttons on right."""
        self._top_navbar = tk.Frame(self, bg=SURFACE, height=60)
        self._top_navbar.pack(side="top", fill="x")
        self._top_navbar.pack_propagate(False)

        # Subtle separator line
        tk.Frame(self, bg=BORDER, height=1).pack(side="top", fill="x")

        inner = tk.Frame(self._top_navbar, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=24)

        # ── Left: App Brand & Icon ─────────────────────────────────────────
        brand_box = tk.Frame(inner, bg=SURFACE)
        brand_box.pack(side="left", fill="y")

        logo_box = tk.Frame(brand_box, bg=PRIMARY_BLUE, width=38, height=38)
        logo_box.pack(side="left", pady=11)
        logo_box.pack_propagate(False)

        tk.Label(
            logo_box,
            text="🎙️",
            font=tkfont.Font(size=14),
            bg=PRIMARY_BLUE,
            fg="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_box = tk.Frame(brand_box, bg=SURFACE)
        title_box.pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            title_box,
            text="Speech & Text Converter",
            font=tkfont.Font(family=FONT_FAMILY, size=13, weight="bold"),
            bg=SURFACE,
            fg=TEXT_DARK,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Voice to text, text to speech and language translation",
            font=tkfont.Font(family=FONT_FAMILY, size=8),
            bg=SURFACE,
            fg=TEXT_MUTED,
        ).pack(anchor="w")

        # ── Right: Home & History Navigation Tabs ──────────────────────────
        nav_box = tk.Frame(inner, bg=SURFACE)
        nav_box.pack(side="right", fill="y")

        self._nav_btn_home = tk.Button(
            nav_box,
            text="🏠  Home",
            font=tkfont.Font(family=FONT_FAMILY, size=9, weight="bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=6,
            command=lambda: self._on_navigate("home"),
        )
        self._nav_btn_home.pack(side="left", padx=(0, 8), pady=13)

        self._nav_btn_history = tk.Button(
            nav_box,
            text="🕒  History",
            font=tkfont.Font(family=FONT_FAMILY, size=9, weight="bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=6,
            command=lambda: self._on_navigate("history"),
        )
        self._nav_btn_history.pack(side="left", pady=13)

    def _update_nav_styles(self, active_tab: str):
        """Highlights the active tab and styles the inactive tab."""
        if active_tab == "home":
            self._nav_btn_home.config(
                bg=PRIMARY_BLUE,
                fg="#FFFFFF",
                activebackground=PRIMARY_BLUE_HOVER,
                activeforeground="#FFFFFF",
            )
            self._nav_btn_history.config(
                bg=SURFACE_ALT,
                fg=TEXT_BODY,
                activebackground="#E2E8F0",
                activeforeground=TEXT_DARK,
            )
        else:
            self._nav_btn_home.config(
                bg=SURFACE_ALT,
                fg=TEXT_BODY,
                activebackground="#E2E8F0",
                activeforeground=TEXT_DARK,
            )
            self._nav_btn_history.config(
                bg=PRIMARY_BLUE,
                fg="#FFFFFF",
                activebackground=PRIMARY_BLUE_HOVER,
                activeforeground="#FFFFFF",
            )

    def _build_statusbar(self):
        statusbar = tk.Frame(self, bg=SURFACE, height=30)
        statusbar.pack(side="bottom", fill="x")
        statusbar.pack_propagate(False)

        tk.Frame(statusbar, bg=BORDER, height=1).pack(fill="x", side="top")

        inner = tk.Frame(statusbar, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=24)

        # Left status dot and message
        left_box = tk.Frame(inner, bg=SURFACE)
        left_box.pack(side="left")

        self._status_dot = tk.Label(left_box, text="●", font=tkfont.Font(size=9), bg=SURFACE, fg=SUCCESS)
        self._status_dot.pack(side="left", padx=(0, 6))

        self._status_text_var = tk.StringVar(value="Ready")
        tk.Label(left_box, textvariable=self._status_text_var, font=self._f_status, bg=SURFACE, fg=TEXT_MUTED).pack(side="left")

        # Right badges
        right_box = tk.Frame(inner, bg=SURFACE)
        right_box.pack(side="right")

        # 1. Language pair badge
        self._status_lang_var = tk.StringVar(value="🌐  English  ↔  Hindi")
        tk.Label(
            right_box,
            textvariable=self._status_lang_var,
            font=self._f_status,
            bg=SURFACE,
            fg=TEXT_MUTED,
        ).pack(side="left", padx=(0, 20))

        # 2. Current Mode badge
        self._status_mode_var = tk.StringVar(value="🎙️  Speech to Text")
        tk.Label(
            right_box,
            textvariable=self._status_mode_var,
            font=self._f_status,
            bg=SURFACE,
            fg=TEXT_MUTED,
        ).pack(side="left", padx=(0, 20))

        # 3. Translation Indicator badge
        tk.Label(
            right_box,
            text="文A  Translation",
            font=self._f_status,
            bg=SURFACE,
            fg=TEXT_MUTED,
        ).pack(side="right")

    def _on_navigate(self, tab_id: str):
        if tab_id not in self._views:
            return

        self._current_tab = tab_id
        self._update_nav_styles(tab_id)
        self._views[tab_id].tkraise()

        if tab_id == "history":
            self._history_view.refresh()
            self._update_status("Viewing conversion history", "ready")
        else:
            self._dashboard_view.refresh_recent_activity()
            self._update_status("Ready", "ready")

    def _update_status(self, message: str, state: str = "ready"):
        self._status_text_var.set(message)
        if state in ("ready", "success"):
            self._status_dot.config(fg=SUCCESS)
        elif state == "busy":
            self._status_dot.config(fg=WARNING)
        elif state == "error":
            self._status_dot.config(fg=DANGER)
        else:
            self._status_dot.config(fg=TEXT_MUTED)

        # Synchronize dynamic language badge if dashboard exists
        if hasattr(self, "_dashboard_view"):
            try:
                s = self._dashboard_view._source_lang_code
                t = self._dashboard_view._target_lang_code
                s_name = "English" if "en" in s else ("Hindi" if "hi" in s else "Gujarati")
                t_name = "English" if "en" in t else ("Hindi" if "hi" in t else "Gujarati")
                self._status_lang_var.set(f"🌐  {s_name}  ↔  {t_name}")

                mode_name = "Speech to Text" if self._dashboard_view._current_mode == "stt" else "Text to Speech"
                icon = "🎙️" if self._dashboard_view._current_mode == "stt" else "📄"
                self._status_mode_var.set(f"{icon}  {mode_name}")
            except Exception:
                pass
