from datetime import datetime
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Callable, Optional

from app.core.audio_recorder import AudioRecorder
from app.core.document import DocumentHandler
from app.core.history_manager import HistoryManager
from app.core.languages import (
    DEFAULT_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_dropdown_options,
    get_language,
    get_language_by_display_name,
)
from app.core.speech_to_text import SpeechToTextEngine
from app.core.text_to_speech import TextToSpeechEngine
from app.core.translator import TranslatorEngine
from app.utils.constants import (
    BG, SURFACE, SURFACE_ALT, BORDER, BORDER_FOCUS,
    PRIMARY_BLUE, PRIMARY_BLUE_HOVER, PRIMARY_BLUE_LIGHT,
    ACCENT_STT, ACCENT_STT_HOVER, ACCENT_STT_LIGHT, ACCENT_STT_PULSE,
    ACCENT_TTS, ACCENT_TTS_HOVER, ACCENT_TTS_LIGHT,
    SUCCESS, SUCCESS_BG, SUCCESS_TEXT,
    DANGER, DANGER_HOVER, WARNING, INFO,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, TEXT_LIGHT,
    FONT_FAMILY, DEFAULT_EXPORTS_DIR,
)


class DashboardView(tk.Frame):
    """
    Modern unified dual-column dashboard with integrated speech recognition,
    language translation (English, Hindi, Gujarati), and speech playback.
    """

    def __init__(
        self,
        parent,
        status_callback: Optional[Callable[[str, str], None]] = None,
        navigate_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=BG, **kwargs)
        self._status_callback = status_callback
        self._navigate_callback = navigate_callback

        # Core Engines
        self._recorder = AudioRecorder()
        self._stt_engine = SpeechToTextEngine()
        self._tts_engine = TextToSpeechEngine()
        self._translator = TranslatorEngine()

        # Application State
        self._current_mode = "stt"          # "stt" or "tts"
        self._active_tab = "original"       # "original" or "translation"
        self._is_recording = False
        self._recording_start_time = 0.0
        self._recording_timer_id = None
        self._pulse_state = 0
        self._last_recorded_wav: Optional[bytes] = None
        self._selected_audio_file: str = ""

        # Language Selection State
        self._source_lang_code = "en"
        self._target_lang_code = "hi"

        # Theme State
        self._dark_mode = False
        self._currently_playing: Optional[str] = None

        # Typography
        self._init_fonts()

        # Build GUI
        self._build_ui()
        self._bind_shortcuts()

        # Update initial status
        self._notify_status_update()

    def _init_fonts(self):
        self._f_title    = tkfont.Font(family=FONT_FAMILY, size=18, weight="bold")
        self._f_sub      = tkfont.Font(family=FONT_FAMILY, size=9)
        self._f_card_h   = tkfont.Font(family=FONT_FAMILY, size=11, weight="bold")
        self._f_card_sub = tkfont.Font(family=FONT_FAMILY, size=8)
        self._f_sec_h    = tkfont.Font(family=FONT_FAMILY, size=11, weight="bold")
        self._f_lbl      = tkfont.Font(family=FONT_FAMILY, size=8, weight="bold")
        self._f_btn      = tkfont.Font(family=FONT_FAMILY, size=9, weight="bold")
        self._f_btn_lg   = tkfont.Font(family=FONT_FAMILY, size=10, weight="bold")
        self._f_text     = tkfont.Font(family=FONT_FAMILY, size=10)
        self._f_text_hi  = tkfont.Font(family="Nirmala UI", size=10)
        self._f_counter  = tkfont.Font(family=FONT_FAMILY, size=8)

    def _set_status(self, text: str, state: str = "ready"):
        if self._status_callback:
            self._status_callback(text, state)

    def _notify_status_update(self):
        s_lang = get_language(self._source_lang_code)
        t_lang = get_language(self._target_lang_code)
        mode_str = "Speech to Text" if self._current_mode == "stt" else "Text to Speech"
        msg = f"Ready"
        self._set_status(msg, "ready")

    def _bind_shortcuts(self):
        self.bind_all("<space>", self._on_space_pressed)

    def _on_space_pressed(self, event):
        focused = self.focus_get()
        # Do not intercept space if user is typing in a text widget
        if isinstance(focused, (tk.Text, tk.Entry, ttk.Combobox)):
            return
        if self._current_mode == "stt":
            self._toggle_recording()

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # Mode Switcher Row (Speech to Text vs Text to Speech)
        self._build_mode_switcher(self)

        # Dual Column Workspace
        workspace = tk.Frame(self, bg=BG)
        workspace.pack(fill="both", expand=True, padx=24, pady=(10, 16))
        workspace.columnconfigure(0, weight=5, uniform="dash_cols")
        workspace.columnconfigure(1, weight=6, uniform="dash_cols")
        workspace.rowconfigure(0, weight=1)

        # Left Column: Input / Recording / Controls
        self._left_container = tk.Frame(workspace, bg=BG)
        self._left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_left_panel(self._left_container)

        # Right Column: Dual Output Text & Playback Controls
        self._right_container = tk.Frame(workspace, bg=BG)
        self._right_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_right_panel(self._right_container)

    # ── 1. Top Header ──────────────────────────────────────────────────────

    def _build_header(self, parent):
        header_frame = tk.Frame(parent, bg=BG)
        header_frame.pack(fill="x", padx=24, pady=(16, 10))

        # Left Title & Subtitle
        left_box = tk.Frame(header_frame, bg=BG)
        left_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            left_box,
            text="Speech & Text Converter",
            font=self._f_title,
            bg=BG,
            fg=TEXT_DARK,
        ).pack(anchor="w")

        tk.Label(
            left_box,
            text="Convert voice to text, text to speech and translate between languages — all in one place.",
            font=self._f_sub,
            bg=BG,
            fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

    # ── 2. Mode Switcher Cards (STT vs TTS) ────────────────────────────────

    def _build_mode_switcher(self, parent):
        mode_row = tk.Frame(parent, bg=BG)
        mode_row.pack(fill="x", padx=24, pady=(16, 8))
        mode_row.columnconfigure(0, weight=1)
        mode_row.columnconfigure(1, weight=1)

        # Mode Card 1: Speech to Text
        self._card_stt = tk.Frame(
            mode_row,
            bg=PRIMARY_BLUE,
            highlightthickness=0,
            cursor="hand2",
        )
        self._card_stt.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=8)
        self._card_stt.bind("<Button-1>", lambda e: self._select_mode("stt"))

        inner_stt = tk.Frame(self._card_stt, bg=PRIMARY_BLUE, cursor="hand2")
        inner_stt.pack(fill="x", padx=16, pady=4)
        inner_stt.bind("<Button-1>", lambda e: self._select_mode("stt"))

        # Mic Icon Circle
        self._icon_stt_box = tk.Frame(inner_stt, bg="#3B82F6", width=36, height=36, cursor="hand2")
        self._icon_stt_box.pack(side="left", padx=(0, 12))
        self._icon_stt_box.pack_propagate(False)
        self._icon_stt_box.bind("<Button-1>", lambda e: self._select_mode("stt"))

        self._lbl_stt_icon = tk.Label(
            self._icon_stt_box,
            text="🎙️",
            font=tkfont.Font(size=13),
            bg="#3B82F6",
            fg=TEXT_LIGHT,
            cursor="hand2",
        )
        self._lbl_stt_icon.place(relx=0.5, rely=0.5, anchor="center")
        self._lbl_stt_icon.bind("<Button-1>", lambda e: self._select_mode("stt"))

        text_stt = tk.Frame(inner_stt, bg=PRIMARY_BLUE, cursor="hand2")
        text_stt.pack(side="left")
        text_stt.bind("<Button-1>", lambda e: self._select_mode("stt"))

        self._lbl_stt_title = tk.Label(
            text_stt,
            text="Speech to Text",
            font=self._f_card_h,
            bg=PRIMARY_BLUE,
            fg=TEXT_LIGHT,
            cursor="hand2",
        )
        self._lbl_stt_title.pack(anchor="w")
        self._lbl_stt_title.bind("<Button-1>", lambda e: self._select_mode("stt"))

        self._lbl_stt_sub = tk.Label(
            text_stt,
            text="Convert your voice to text",
            font=self._f_card_sub,
            bg=PRIMARY_BLUE,
            fg="#BFDBFE",
            cursor="hand2",
        )
        self._lbl_stt_sub.pack(anchor="w")
        self._lbl_stt_sub.bind("<Button-1>", lambda e: self._select_mode("stt"))

        # Mode Card 2: Text to Speech
        self._card_tts = tk.Frame(
            mode_row,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
            cursor="hand2",
        )
        self._card_tts.grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=8)
        self._card_tts.bind("<Button-1>", lambda e: self._select_mode("tts"))

        inner_tts = tk.Frame(self._card_tts, bg=SURFACE, cursor="hand2")
        inner_tts.pack(fill="x", padx=16, pady=4)
        inner_tts.bind("<Button-1>", lambda e: self._select_mode("tts"))

        self._icon_tts_box = tk.Frame(inner_tts, bg="#EFF6FF", width=36, height=36, cursor="hand2")
        self._icon_tts_box.pack(side="left", padx=(0, 12))
        self._icon_tts_box.pack_propagate(False)
        self._icon_tts_box.bind("<Button-1>", lambda e: self._select_mode("tts"))

        self._lbl_tts_icon = tk.Label(
            self._icon_tts_box,
            text="📄",
            font=tkfont.Font(size=13),
            bg="#EFF6FF",
            fg=PRIMARY_BLUE,
            cursor="hand2",
        )
        self._lbl_tts_icon.place(relx=0.5, rely=0.5, anchor="center")
        self._lbl_tts_icon.bind("<Button-1>", lambda e: self._select_mode("tts"))

        text_tts = tk.Frame(inner_tts, bg=SURFACE, cursor="hand2")
        text_tts.pack(side="left")
        text_tts.bind("<Button-1>", lambda e: self._select_mode("tts"))

        self._lbl_tts_title = tk.Label(
            text_tts,
            text="Text to Speech",
            font=self._f_card_h,
            bg=SURFACE,
            fg=TEXT_DARK,
            cursor="hand2",
        )
        self._lbl_tts_title.pack(anchor="w")
        self._lbl_tts_title.bind("<Button-1>", lambda e: self._select_mode("tts"))

        self._lbl_tts_sub = tk.Label(
            text_tts,
            text="Convert text to natural voice",
            font=self._f_card_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
            cursor="hand2",
        )
        self._lbl_tts_sub.pack(anchor="w")
        self._lbl_tts_sub.bind("<Button-1>", lambda e: self._select_mode("tts"))

    def _select_mode(self, mode: str):
        if self._current_mode == mode:
            return
        self._stop_any_playback()
        self._current_mode = mode

        if mode == "stt":
            # Active STT
            self._card_stt.config(bg=PRIMARY_BLUE, highlightthickness=0)
            self._card_stt.winfo_children()[0].config(bg=PRIMARY_BLUE)
            self._icon_stt_box.config(bg="#3B82F6")
            self._lbl_stt_icon.config(bg="#3B82F6", fg=TEXT_LIGHT)
            self._lbl_stt_title.config(bg=PRIMARY_BLUE, fg=TEXT_LIGHT)
            self._lbl_stt_sub.config(bg=PRIMARY_BLUE, fg="#BFDBFE")

            # Inactive TTS
            self._card_tts.config(bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            self._card_tts.winfo_children()[0].config(bg=SURFACE)
            self._icon_tts_box.config(bg="#EFF6FF")
            self._lbl_tts_icon.config(bg="#EFF6FF", fg=PRIMARY_BLUE)
            self._lbl_tts_title.config(bg=SURFACE, fg=TEXT_DARK)
            self._lbl_tts_sub.config(bg=SURFACE, fg=TEXT_MUTED)

            self._mode_header_title.config(text="Speech to Text")
            self._mode_header_sub.config(text="Speak naturally and get accurate text with translation.")
            self._mode_header_icon.config(text="🎙️")
            self._tts_controls_frame.pack_forget()
            self._stt_controls_frame.pack(fill="both", expand=True)

            if hasattr(self, "_lbl_orig_header"):
                self._lbl_orig_header.config(text=f"Transcribed Text ({get_language(self._source_lang_code).display_name.split()[0]})")
            self._set_status("Switched to Speech to Text mode", "ready")
        else:
            # Active TTS
            self._card_tts.config(bg=PRIMARY_BLUE, highlightthickness=0)
            self._card_tts.winfo_children()[0].config(bg=PRIMARY_BLUE)
            self._icon_tts_box.config(bg="#3B82F6")
            self._lbl_tts_icon.config(bg="#3B82F6", fg=TEXT_LIGHT)
            self._lbl_tts_title.config(bg=PRIMARY_BLUE, fg=TEXT_LIGHT)
            self._lbl_tts_sub.config(bg=PRIMARY_BLUE, fg="#BFDBFE")

            # Inactive STT
            self._card_stt.config(bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            self._card_stt.winfo_children()[0].config(bg=SURFACE)
            self._icon_stt_box.config(bg="#EFF6FF")
            self._lbl_stt_icon.config(bg="#EFF6FF", fg=PRIMARY_BLUE)
            self._lbl_stt_title.config(bg=SURFACE, fg=TEXT_DARK)
            self._lbl_stt_sub.config(bg=SURFACE, fg=TEXT_MUTED)

            self._mode_header_title.config(text="Text to Speech")
            self._mode_header_sub.config(text="Enter or import text, select voice, and generate natural speech.")
            self._mode_header_icon.config(text="📄")
            self._stt_controls_frame.pack_forget()
            self._tts_controls_frame.pack(fill="both", expand=True)

            if hasattr(self, "_lbl_orig_header"):
                self._lbl_orig_header.config(text=f"Original Text ({get_language(self._source_lang_code).display_name.split()[0]})")
            self._set_status("Switched to Text to Speech mode", "ready")

    # ── 3. Left Panel (Input / Recording / Controls) ──────────────────────

    def _build_left_panel(self, parent):
        card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Header for the active mode
        h_box = tk.Frame(inner, bg=SURFACE)
        h_box.pack(fill="x", pady=(0, 14))

        icon_frame = tk.Frame(h_box, bg="#EFF6FF", width=38, height=38)
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)

        self._mode_header_icon = tk.Label(icon_frame, text="🎙️", font=tkfont.Font(size=14), bg="#EFF6FF", fg=PRIMARY_BLUE)
        self._mode_header_icon.place(relx=0.5, rely=0.5, anchor="center")

        title_box = tk.Frame(h_box, bg=SURFACE)
        title_box.pack(side="left")

        self._mode_header_title = tk.Label(title_box, text="Speech to Text", font=self._f_sec_h, bg=SURFACE, fg=TEXT_DARK)
        self._mode_header_title.pack(anchor="w")

        self._mode_header_sub = tk.Label(
            title_box,
            text="Speak naturally and get accurate text with translation.",
            font=self._f_card_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
        )
        self._mode_header_sub.pack(anchor="w")

        # Language Selectors Row: Input Language [▼] ⇄ Translate To [▼]
        lang_row = tk.Frame(inner, bg=SURFACE)
        lang_row.pack(fill="x", pady=(0, 16))

        # Input Language
        col_src = tk.Frame(lang_row, bg=SURFACE)
        col_src.pack(side="left", fill="x", expand=True)

        tk.Label(col_src, text="Input Language", font=self._f_lbl, bg=SURFACE, fg=TEXT_BODY).pack(anchor="w")

        options = get_dropdown_options()
        self._cb_input_lang = ttk.Combobox(col_src, values=options, state="readonly", font=self._f_text)
        self._cb_input_lang.current(0)  # English
        self._cb_input_lang.pack(fill="x", pady=(4, 0))
        self._cb_input_lang.bind("<<ComboboxSelected>>", self._on_input_lang_changed)

        # Swap Button ⇄
        btn_swap = tk.Button(
            lang_row,
            text="⇄",
            font=tkfont.Font(size=14, weight="bold"),
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            width=3,
            command=self._swap_languages,
        )
        btn_swap.pack(side="left", padx=8, pady=(16, 0))

        # Target Language
        col_tgt = tk.Frame(lang_row, bg=SURFACE)
        col_tgt.pack(side="left", fill="x", expand=True)

        tk.Label(col_tgt, text="Translate To", font=self._f_lbl, bg=SURFACE, fg=TEXT_BODY).pack(anchor="w")

        self._cb_target_lang = ttk.Combobox(col_tgt, values=options, state="readonly", font=self._f_text)
        self._cb_target_lang.current(1)  # Hindi
        self._cb_target_lang.pack(fill="x", pady=(4, 0))
        self._cb_target_lang.bind("<<ComboboxSelected>>", self._on_target_lang_changed)

        # Container for STT specific controls
        self._stt_controls_frame = tk.Frame(inner, bg=SURFACE)
        self._stt_controls_frame.pack(fill="both", expand=True)
        self._build_stt_controls(self._stt_controls_frame)

        # Container for TTS specific controls (initially hidden)
        self._tts_controls_frame = tk.Frame(inner, bg=SURFACE)
        self._build_tts_controls(self._tts_controls_frame)

    def _build_stt_controls(self, parent):
        # Central Recording Area matching mockup
        rec_box = tk.Frame(parent, bg=SURFACE_ALT, highlightbackground=BORDER, highlightthickness=1)
        rec_box.pack(fill="x", pady=(0, 16), ipady=12)

        # Circular concentric mic ring
        self._pulse_ring = tk.Frame(rec_box, bg="#EFF6FF", width=86, height=86)
        self._pulse_ring.pack(pady=(12, 6))
        self._pulse_ring.pack_propagate(False)

        self._inner_pulse = tk.Frame(self._pulse_ring, bg="#DBEAFE", width=70, height=70)
        self._inner_pulse.place(relx=0.5, rely=0.5, anchor="center")
        self._inner_pulse.pack_propagate(False)

        self._btn_circle_mic = tk.Button(
            self._inner_pulse,
            text="🎙️",
            font=tkfont.Font(size=20),
            bg=PRIMARY_BLUE,
            fg=TEXT_LIGHT,
            activebackground=PRIMARY_BLUE_HOVER,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=3,
            command=self._toggle_recording,
        )
        self._btn_circle_mic.place(relx=0.5, rely=0.5, anchor="center")

        self._lbl_rec_prompt = tk.Label(
            rec_box,
            text="Click to Start Recording",
            font=self._f_card_h,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
        )
        self._lbl_rec_prompt.pack()

        self._lbl_rec_sub = tk.Label(
            rec_box,
            text="Or press Space to start/stop",
            font=self._f_card_sub,
            bg=SURFACE_ALT,
            fg=TEXT_MUTED,
        )
        self._lbl_rec_sub.pack(pady=(2, 8))

        # Divider with "OR"
        div_frame = tk.Frame(parent, bg=SURFACE)
        div_frame.pack(fill="x", pady=(0, 14))

        tk.Frame(div_frame, bg=BORDER, height=1).place(relx=0, rely=0.5, relwidth=1)
        or_badge = tk.Label(div_frame, text="  OR  ", font=self._f_lbl, bg=SURFACE, fg=TEXT_MUTED)
        or_badge.pack()

        # Secondary buttons row: Upload Audio and Clear
        sec_row = tk.Frame(parent, bg=SURFACE)
        sec_row.pack(fill="x", pady=(0, 16))
        sec_row.columnconfigure(0, weight=1)
        sec_row.columnconfigure(1, weight=1)

        # Upload Audio
        btn_upload = tk.Button(
            sec_row,
            text="⇪  Upload Audio",
            font=self._f_btn,
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            pady=10,
            command=self._on_upload_audio,
        )
        btn_upload.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # Clear
        btn_clear = tk.Button(
            sec_row,
            text="🗑️  Clear",
            font=self._f_btn,
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            pady=10,
            command=self._on_clear_stt,
        )
        btn_clear.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Big Primary Action Button: Convert & Translate Text
        self._btn_main_record = tk.Button(
            parent,
            text="🔄  Convert & Translate Text",
            font=self._f_btn_lg,
            bg=PRIMARY_BLUE,
            fg=TEXT_LIGHT,
            activebackground=PRIMARY_BLUE_HOVER,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=12,
            command=self._on_convert_stt,
        )
        self._btn_main_record.pack(fill="x")

    def _build_tts_controls(self, parent):
        """Controls for Text to Speech mode."""
        tk.Label(parent, text="Enter Text to Speak / Translate", font=self._f_lbl, bg=SURFACE, fg=TEXT_BODY).pack(anchor="w")

        self._tts_input_text = tk.Text(
            parent,
            height=7,
            font=self._f_text,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
            bd=1,
            relief="solid",
            highlightthickness=0,
            padx=10,
            pady=8,
            wrap="word",
        )
        self._tts_input_text.pack(fill="x", pady=(4, 10))

        # Action buttons for TTS input: Import PDF, Clear
        btn_bar = tk.Frame(parent, bg=SURFACE)
        btn_bar.pack(fill="x", pady=(0, 14))

        tk.Button(
            btn_bar,
            text="📄 Import PDF",
            font=self._f_btn,
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._on_import_doc,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_bar,
            text="🗑️ Clear",
            font=self._f_btn,
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._on_clear_tts_input,
        ).pack(side="left")

        # Primary TTS generate button
        self._btn_main_tts = tk.Button(
            parent,
            text="🔊  Convert & Translate Speech",
            font=self._f_btn_lg,
            bg=PRIMARY_BLUE,
            fg=TEXT_LIGHT,
            activebackground=PRIMARY_BLUE_HOVER,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=12,
            command=self._on_tts_convert,
        )
        self._btn_main_tts.pack(fill="x", pady=(10, 0))

    # ── 4. Right Panel (Dual Output Text & Playback) ──────────────────────

    def _build_right_panel(self, parent):
        card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # ── Output Box 1: Transcribed / Original Text ──────────────────────
        self._out1_header = tk.Frame(inner, bg=SURFACE)
        self._out1_header.pack(fill="x", pady=(0, 4))

        self._lbl_orig_header = tk.Label(
            self._out1_header,
            text="Transcribed Text (English)",
            font=self._f_lbl,
            bg=SURFACE,
            fg=TEXT_BODY,
        )
        self._lbl_orig_header.pack(side="left")

        self._btn_copy_orig = tk.Button(
            self._out1_header,
            text="📋 Copy",
            font=self._f_card_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: self._copy_text(self._txt_original, self._btn_copy_orig),
        )
        self._btn_copy_orig.pack(side="right")

        # Original Text Container
        box1 = tk.Frame(inner, bg=SURFACE_ALT, highlightbackground=BORDER, highlightthickness=1)
        box1.pack(fill="both", expand=True, pady=(0, 10))

        self._txt_original = tk.Text(
            box1,
            height=4,
            font=self._f_text,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
        )
        self._txt_original.pack(fill="both", expand=True)
        self._txt_original.bind("<KeyRelease>", lambda e: self._update_counters())

        cnt_frame1 = tk.Frame(box1, bg=SURFACE_ALT)
        cnt_frame1.pack(fill="x", padx=8, pady=(0, 4))

        self._lbl_counter_orig = tk.Label(
            cnt_frame1,
            text="0/5000",
            font=self._f_counter,
            bg=SURFACE_ALT,
            fg=TEXT_MUTED,
        )
        self._lbl_counter_orig.pack(side="right")

        # ── Output Box 2: Translated Text (Target) ─────────────────────────
        out2_header = tk.Frame(inner, bg=SURFACE)
        out2_header.pack(fill="x", pady=(0, 4))

        self._lbl_trans_header = tk.Label(
            out2_header,
            text="Translated Text (Hindi)",
            font=self._f_lbl,
            bg=SURFACE,
            fg=SUCCESS_TEXT,
        )
        self._lbl_trans_header.pack(side="left")

        self._btn_copy_trans = tk.Button(
            out2_header,
            text="📋 Copy",
            font=self._f_card_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: self._copy_text(self._txt_translated, self._btn_copy_trans),
        )
        self._btn_copy_trans.pack(side="right")

        # Translated Text Container
        box2 = tk.Frame(inner, bg=SURFACE_ALT, highlightbackground=BORDER, highlightthickness=1)
        box2.pack(fill="both", expand=True, pady=(0, 14))

        self._txt_translated = tk.Text(
            box2,
            height=4,
            font=self._f_text_hi,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
        )
        self._txt_translated.pack(fill="both", expand=True)
        self._txt_translated.bind("<KeyRelease>", lambda e: self._update_counters())

        cnt_frame2 = tk.Frame(box2, bg=SURFACE_ALT)
        cnt_frame2.pack(fill="x", padx=8, pady=(0, 4))

        self._lbl_counter_trans = tk.Label(
            cnt_frame2,
            text="0/5000",
            font=self._f_counter,
            bg=SURFACE_ALT,
            fg=TEXT_MUTED,
        )
        self._lbl_counter_trans.pack(side="right")

        # ── Action Buttons Row: Play Original, Play Translation, Download ───
        action_row = tk.Frame(inner, bg=SURFACE)
        action_row.pack(fill="x")
        action_row.columnconfigure(0, weight=1)
        action_row.columnconfigure(1, weight=1)
        action_row.columnconfigure(2, weight=1)

        # Play Original (Speaker Icon, Soft Blue)
        self._btn_play_orig = tk.Button(
            action_row,
            text="🔊  Play Original",
            font=self._f_btn,
            bg="#EFF6FF",
            fg=PRIMARY_BLUE,
            relief="flat",
            bd=1,
            cursor="hand2",
            pady=9,
            command=self._on_play_original,
        )
        self._btn_play_orig.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        # Play Translation (Speaker Icon, Mint Green)
        self._btn_play_trans = tk.Button(
            action_row,
            text="🔊  Play Translation",
            font=self._f_btn,
            bg=SUCCESS_BG,
            fg=SUCCESS_TEXT,
            relief="flat",
            bd=1,
            cursor="hand2",
            pady=9,
            command=self._on_play_translation,
        )
        self._btn_play_trans.grid(row=0, column=1, sticky="ew", padx=4)

        # Download (Download Icon)
        self._btn_download = tk.Button(
            action_row,
            text="⤓  Download",
            font=self._f_btn,
            bg=SURFACE_ALT,
            fg=TEXT_BODY,
            relief="flat",
            bd=1,
            cursor="hand2",
            pady=9,
            command=self._on_download_menu,
        )
        self._btn_download.grid(row=0, column=2, sticky="ew", padx=(4, 0))

    # ── Language Synchronization & Dropdowns ───────────────────────────────

    def _on_input_lang_changed(self, event=None):
        selected = self._cb_input_lang.get()
        lang = get_language_by_display_name(selected)
        self._source_lang_code = lang.code
        prefix = "Transcribed Text" if self._current_mode == "stt" else "Original Text"
        self._lbl_orig_header.config(text=f"{prefix} ({lang.display_name.split()[0]})")
        self._notify_status_update()
        self._trigger_live_translation()

    def _on_target_lang_changed(self, event=None):
        selected = self._cb_target_lang.get()
        lang = get_language_by_display_name(selected)
        self._target_lang_code = lang.code
        self._lbl_trans_header.config(text=f"Translated Text ({lang.display_name.split()[0]})")
        self._notify_status_update()
        self._trigger_live_translation()

    def _swap_languages(self):
        # Swap source and target languages
        src_idx = self._cb_input_lang.current()
        tgt_idx = self._cb_target_lang.current()

        self._cb_input_lang.current(tgt_idx)
        self._cb_target_lang.current(src_idx)

        # Also swap text in both textboxes
        t1 = self._txt_original.get("1.0", "end-1c")
        t2 = self._txt_translated.get("1.0", "end-1c")

        self._txt_original.delete("1.0", "end")
        self._txt_original.insert("1.0", t2)

        self._txt_translated.delete("1.0", "end")
        self._txt_translated.insert("1.0", t1)

        self._on_input_lang_changed()
        self._on_target_lang_changed()
        self._update_counters()

    def _update_counters(self):
        c1 = len(self._txt_original.get("1.0", "end-1c"))
        c2 = len(self._txt_translated.get("1.0", "end-1c"))
        self._lbl_counter_orig.config(text=f"{c1}/5000")
        self._lbl_counter_trans.config(text=f"{c2}/5000")

    def _copy_text(self, text_widget: tk.Text, btn_widget: tk.Button):
        content = text_widget.get("1.0", "end-1c").strip()
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        orig_text = btn_widget.cget("text")
        btn_widget.config(text="✓ Copied!", fg=SUCCESS)
        self.after(1500, lambda: btn_widget.config(text=orig_text, fg=TEXT_MUTED))

    # ── Speech Recognition & Recording ─────────────────────────────────────

    def _toggle_recording(self):
        if not self._is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self._stop_any_playback()
        self._selected_audio_file = ""
        self._last_recorded_wav = None
        try:
            self._recorder.start_recording()
            self._is_recording = True
            self._recording_start_time = time.time()

            self._btn_circle_mic.config(bg=DANGER, activebackground=DANGER_HOVER)
            self._btn_main_record.config(text="⏹  Stop & Convert (00:00)", bg=DANGER, activebackground=DANGER_HOVER)
            self._lbl_rec_prompt.config(text="Recording in progress...", fg=DANGER)
            self._lbl_rec_sub.config(text="Click mic again to stop • Or Space", fg=TEXT_MUTED)

            self._set_status("Listening to microphone... Speak clearly.", "busy")
            self._update_recording_timer()
        except Exception as e:
            messagebox.showerror("Recording Error", f"Could not access microphone: {e}")
            self._set_status(f"Microphone error: {e}", "error")

    def _update_recording_timer(self):
        if not self._is_recording:
            return

        elapsed = int(time.time() - self._recording_start_time)
        mins, secs = divmod(elapsed, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        self._btn_main_record.config(text=f"⏹  Stop & Convert ({time_str})")
        self._lbl_rec_prompt.config(text=f"Recording... {time_str}")

        # Pulse animation on outer ring
        self._pulse_state = (self._pulse_state + 1) % 3
        pulse_colors = ["#EFF6FF", "#DBEAFE", "#BFDBFE"]
        self._pulse_ring.config(bg=pulse_colors[self._pulse_state])

        self._recording_timer_id = self.after(300, self._update_recording_timer)

    def _stop_recording(self):
        if not self._is_recording:
            return
        self._is_recording = False
        if self._recording_timer_id:
            self.after_cancel(self._recording_timer_id)
            self._recording_timer_id = None

        self._btn_circle_mic.config(bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER)
        self._btn_main_record.config(text="🔄  Convert & Translate Text", bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER, state="normal")
        self._pulse_ring.config(bg="#EFF6FF")

        try:
            wav_bytes = self._recorder.stop_recording()
            self._last_recorded_wav = wav_bytes

            if not wav_bytes or len(wav_bytes) < 1500:
                self._lbl_rec_prompt.config(text="Click to Start Recording", fg=TEXT_DARK)
                self._lbl_rec_sub.config(text="Recording was too short. Speak and click mic again.", fg=TEXT_MUTED)
                self._set_status("Recording too short. Speak and try again.", "ready")
                self._last_recorded_wav = None
                return

            elapsed = int(time.time() - self._recording_start_time)
            mins, secs = divmod(elapsed, 60)
            time_str = f"{mins:02d}:{secs:02d}"

            self._lbl_rec_prompt.config(text=f"Recording Saved ({time_str})", fg=SUCCESS_TEXT)
            self._lbl_rec_sub.config(text="Click 'Convert & Translate Text' below to process", fg=TEXT_MUTED)
            self._set_status("Recording saved. Click 'Convert & Translate Text' to process.", "ready")
        except Exception as e:
            self._last_recorded_wav = None
            self._lbl_rec_prompt.config(text="Click to Start Recording", fg=TEXT_DARK)
            self._lbl_rec_sub.config(text="Or press Space to start/stop", fg=TEXT_MUTED)
            self._set_status(f"Recording error: {e}", "ready")

    def _on_upload_audio(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Supported Audio", "*.wav;*.mp3;*.m4a;*.aac;*.flac;*.ogg"),
                ("WAV Files", "*.wav"),
                ("MP3 Files", "*.mp3"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return

        if self._is_recording:
            self._stop_recording()

        self._selected_audio_file = file_path
        self._last_recorded_wav = None
        filename = os.path.basename(file_path)
        self._lbl_rec_prompt.config(text=f"📁 {filename}", fg=PRIMARY_BLUE)
        self._lbl_rec_sub.config(text="Audio file loaded • Click 'Convert & Translate Text' below", fg=TEXT_MUTED)
        self._btn_main_record.config(text="🔄  Convert & Translate Text", bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER, state="normal")
        self._set_status(f"Loaded '{filename}'. Click 'Convert & Translate Text' to process.", "ready")

    def _on_convert_stt(self):
        """Processes the recorded voice or uploaded audio file to convert and translate."""
        # 1. If currently recording, stop and capture audio
        if self._is_recording:
            self._is_recording = False
            if self._recording_timer_id:
                self.after_cancel(self._recording_timer_id)
                self._recording_timer_id = None
            self._btn_circle_mic.config(bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER)
            self._pulse_ring.config(bg="#EFF6FF")
            try:
                self._last_recorded_wav = self._recorder.stop_recording()
            except Exception:
                self._last_recorded_wav = None

        # 2. Check if we have an uploaded audio file
        if self._selected_audio_file and os.path.exists(self._selected_audio_file):
            file_path = self._selected_audio_file
            filename = os.path.basename(file_path)
            lang = get_language(self._source_lang_code)

            self._btn_main_record.config(text="⏳  Converting & Translating...", state="disabled")
            self._set_status(f"Transcribing '{filename}' in {lang.display_name}...", "busy")

            def _file_worker():
                try:
                    transcript = self._stt_engine.transcribe_file(file_path, lang.code)
                    self.after(0, lambda t=transcript, fn=filename: self._on_transcription_complete(t, fn))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda msg=err_msg: self._on_transcription_error(msg))

            threading.Thread(target=_file_worker, daemon=True).start()
            return

        # 3. Check if we have recorded voice bytes
        if self._last_recorded_wav and len(self._last_recorded_wav) >= 1500:
            wav_bytes = self._last_recorded_wav
            lang = get_language(self._source_lang_code)

            self._btn_main_record.config(text="⏳  Converting & Translating...", state="disabled")
            self._set_status(f"Transcribing voice recording in {lang.display_name}...", "busy")

            def _rec_worker():
                try:
                    transcript = self._stt_engine.transcribe_wav_bytes(wav_bytes, lang.code)
                    self.after(0, lambda t=transcript: self._on_transcription_complete(t, "Microphone"))
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda msg=err_msg: self._on_transcription_error(msg))

            threading.Thread(target=_rec_worker, daemon=True).start()
            return

        # 4. Neither audio file nor recording available
        messagebox.showinfo(
            "No Audio Available",
            "Please record speech (click microphone) or upload an audio file first,\nthen click 'Convert & Translate Text'.",
        )
        self._set_status("Please record speech or upload an audio file first.", "ready")

    def _on_clear_stt(self):
        self._stop_any_playback()
        if self._is_recording:
            self._is_recording = False
            if self._recording_timer_id:
                self.after_cancel(self._recording_timer_id)
                self._recording_timer_id = None
            try:
                self._recorder.stop_recording()
            except Exception:
                pass
        self._selected_audio_file = ""
        self._last_recorded_wav = None
        self._btn_circle_mic.config(bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER)
        self._lbl_rec_prompt.config(text="Click to Start Recording", fg=TEXT_DARK)
        self._lbl_rec_sub.config(text="Or press Space to start/stop", fg=TEXT_MUTED)
        self._pulse_ring.config(bg="#EFF6FF")
        self._btn_main_record.config(text="🔄  Convert & Translate Text", bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER, state="normal")
        self._set_status("Audio file and recording cleared", "ready")

    def _on_transcription_complete(self, transcript: str, source_label: str = "Microphone"):
        self._btn_main_record.config(text="🔄  Convert & Translate Text", bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER, state="normal")
        self._txt_original.delete("1.0", "end")
        self._txt_original.insert("1.0", transcript)
        self._update_counters()

        self._set_status("Transcription complete. Translating...", "busy")
        self._trigger_live_translation()

    def _on_transcription_error(self, err_msg: str):
        self._btn_main_record.config(text="🔄  Convert & Translate Text", bg=PRIMARY_BLUE, activebackground=PRIMARY_BLUE_HOVER, state="normal")
        messagebox.showwarning("Recognition Notice", f"{err_msg}")
        self._set_status("Ready", "ready")

    # ── Translation Workflow ───────────────────────────────────────────────

    def _trigger_live_translation(self):
        text_to_translate = self._txt_original.get("1.0", "end-1c").strip()
        if not text_to_translate:
            self._txt_translated.delete("1.0", "end")
            self._update_counters()
            self._set_status("Ready", "ready")
            return

        src = self._source_lang_code
        tgt = self._target_lang_code

        def _worker():
            try:
                translated = self._translator.translate(text_to_translate, src, tgt)
                self.after(0, lambda t=translated: self._on_translation_success(t))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda msg=err_msg: self._on_translation_failure(msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_translation_success(self, translated_text: str):
        self._txt_translated.delete("1.0", "end")
        self._txt_translated.insert("1.0", translated_text)
        self._update_counters()
        self._set_status("Ready", "ready")

        # Save to history automatically
        orig = self._txt_original.get("1.0", "end-1c").strip()
        s_lang = get_language(self._source_lang_code).display_name
        t_lang = get_language(self._target_lang_code).display_name
        HistoryManager.add_entry(
            conv_type="Speech to Text" if self._current_mode == "stt" else "Text to Speech",
            title=orig[:40] if orig else "Translation Session",
            format_tag="PDF/AUDIO",
            source_text=orig,
            translated_text=translated_text,
            source_lang=s_lang,
            target_lang=t_lang,
        )

    def _on_translation_failure(self, err_msg: str):
        self._set_status(f"Translation notice: {err_msg}", "ready")

    # ── Text to Speech Mode Workflows ──────────────────────────────────────

    def _on_import_doc(self):
        file_path = filedialog.askopenfilename(
            title="Import PDF Document",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not file_path:
            return
        try:
            content = DocumentHandler.import_text_from_file(file_path)
            self._tts_input_text.delete("1.0", "end")
            self._tts_input_text.insert("1.0", content)
            self._set_status(f"Imported PDF '{os.path.basename(file_path)}'", "ready")
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not read PDF document: {e}")

    def _on_clear_tts_input(self):
        self._tts_input_text.delete("1.0", "end")

    def _on_tts_convert(self):
        input_text = self._tts_input_text.get("1.0", "end-1c").strip()
        if not input_text:
            messagebox.showinfo("Empty Text", "Please enter some text to speak and translate.")
            return

        self._txt_original.delete("1.0", "end")
        self._txt_original.insert("1.0", input_text)
        self._update_counters()

        self._set_status("Translating and generating speech...", "busy")
        self._trigger_live_translation()

    # ── Audio Playback ─────────────────────────────────────────────────────

    def _stop_any_playback(self):
        """Immediately stop any active speech playback and reset button states."""
        self._tts_engine.stop_speech()
        self._currently_playing = None
        if hasattr(self, "_btn_play_orig"):
            self._btn_play_orig.config(text="🔊  Play Original")
        if hasattr(self, "_btn_play_trans"):
            self._btn_play_trans.config(text="🔊  Play Translation")

    def _on_play_original(self):
        if self._currently_playing == "original":
            self._stop_any_playback()
            self._set_status("Playback stopped", "ready")
            return

        text = self._txt_original.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Playback", "No original text available to play.")
            return

        self._stop_any_playback()
        self._currently_playing = "original"

        lang = get_language(self._source_lang_code)
        self._set_status(f"Playing original audio in {lang.display_name}...", "busy")
        self._btn_play_orig.config(text="⏹ Stop Playing")

        def _on_done():
            self._currently_playing = None
            self.after(0, lambda: self._btn_play_orig.config(text="🔊  Play Original"))
            self.after(0, lambda: self._set_status("Ready", "ready"))

        self._tts_engine.play_speech(
            text=text,
            lang_code=lang.code,
            on_finished=_on_done,
        )

    def _on_play_translation(self):
        if self._currently_playing == "translation":
            self._stop_any_playback()
            self._set_status("Playback stopped", "ready")
            return

        text = self._txt_translated.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Playback", "No translated text available to play.")
            return

        self._stop_any_playback()
        self._currently_playing = "translation"

        lang = get_language(self._target_lang_code)
        self._set_status(f"Playing translated audio in {lang.display_name}...", "busy")
        self._btn_play_trans.config(text="⏹ Stop Playing")

        def _on_done():
            self._currently_playing = None
            self.after(0, lambda: self._btn_play_trans.config(text="🔊  Play Translation"))
            self.after(0, lambda: self._set_status("Ready", "ready"))

        self._tts_engine.play_speech(
            text=text,
            lang_code=lang.code,
            on_finished=_on_done,
        )

    # ── Downloads & Exports ────────────────────────────────────────────────

    def _on_download_menu(self):
        # 4 comprehensive download options:
        # 1. Original Text as PDF
        # 2. Original Text as Audio
        # 3. Translation Text as PDF
        # 4. Translation Audio File
        menu = tk.Menu(self, tearoff=0, font=self._f_btn)
        menu.add_command(label="📄 Download Original PDF", command=self._export_original_pdf)
        menu.add_command(label="🎵 Download Original Audio", command=self._export_original_audio_mp3)
        menu.add_command(label="📄 Download Translation PDF", command=self._export_translation_pdf)
        menu.add_command(label="🎵 Download Translation Audio", command=self._export_translation_audio_mp3)

        # Place menu under the download button
        x = self._btn_download.winfo_rootx()
        y = self._btn_download.winfo_rooty() + self._btn_download.winfo_height()
        menu.post(x, y)

    def _export_original_audio_mp3(self):
        text = self._txt_original.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Export Notice", "No original text available to export as audio.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = os.path.join(DEFAULT_EXPORTS_DIR, f"original_speech_{ts}.mp3")

        save_path = filedialog.asksaveasfilename(
            title="Save Original Audio File",
            initialfile=os.path.basename(default_file),
            initialdir=DEFAULT_EXPORTS_DIR,
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3")],
        )
        if not save_path:
            return

        lang = get_language(self._source_lang_code)
        try:
            self._tts_engine.save_speech_file(text, lang.code, save_path)
            messagebox.showinfo("Export Successful", f"Original audio successfully saved to:\n{save_path}")
            self._set_status(f"Exported original audio to {os.path.basename(save_path)}", "ready")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save audio file: {e}")

    def _export_original_pdf(self):
        orig = self._txt_original.get("1.0", "end-1c").strip()
        if not orig:
            messagebox.showwarning("Export Notice", "No original text available to export as PDF.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = os.path.join(DEFAULT_EXPORTS_DIR, f"original_text_{ts}.pdf")

        save_path = filedialog.asksaveasfilename(
            title="Save Original Text PDF",
            initialfile=os.path.basename(default_file),
            initialdir=DEFAULT_EXPORTS_DIR,
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
        )
        if not save_path:
            return

        s_lang = get_language(self._source_lang_code).display_name
        try:
            DocumentHandler.export_to_pdf(orig, save_path, title=f"SpeechText Original Text ({s_lang})")
            messagebox.showinfo("Export Successful", f"Original text PDF successfully saved to:\n{save_path}")
            self._set_status(f"Exported PDF to {os.path.basename(save_path)}", "ready")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export PDF: {e}")

    def _export_translation_audio_mp3(self):
        text = self._txt_translated.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Export Notice", "No translated text available to export as audio.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = os.path.join(DEFAULT_EXPORTS_DIR, f"translation_speech_{ts}.mp3")

        save_path = filedialog.asksaveasfilename(
            title="Save Translation Audio File",
            initialfile=os.path.basename(default_file),
            initialdir=DEFAULT_EXPORTS_DIR,
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3")],
        )
        if not save_path:
            return

        lang = get_language(self._target_lang_code)
        try:
            self._tts_engine.save_speech_file(text, lang.code, save_path)
            messagebox.showinfo("Export Successful", f"Translation audio successfully saved to:\n{save_path}")
            self._set_status(f"Exported translation audio to {os.path.basename(save_path)}", "ready")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save audio file: {e}")

    def _export_translation_pdf(self):
        trans = self._txt_translated.get("1.0", "end-1c").strip()
        if not trans:
            messagebox.showwarning("Export Notice", "No translated text available to export as PDF.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = os.path.join(DEFAULT_EXPORTS_DIR, f"translation_{ts}.pdf")

        save_path = filedialog.asksaveasfilename(
            title="Save Translation PDF",
            initialfile=os.path.basename(default_file),
            initialdir=DEFAULT_EXPORTS_DIR,
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
        )
        if not save_path:
            return

        t_lang = get_language(self._target_lang_code).display_name

        try:
            DocumentHandler.export_translation_pdf(trans, t_lang, save_path)
            messagebox.showinfo("Export Successful", f"Translation PDF successfully saved to:\n{save_path}")
            self._set_status(f"Exported PDF to {os.path.basename(save_path)}", "ready")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export PDF: {e}")

    def refresh_recent_activity(self):
        """Hook for app window navigation."""
        pass
