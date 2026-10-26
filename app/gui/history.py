import os
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import font as tkfont
from typing import Optional

from app.core.history_manager import HistoryManager
from app.utils.constants import (
    BG, SURFACE, SURFACE_ALT, BORDER,
    PRIMARY_BLUE, PRIMARY_BLUE_HOVER,
    SUCCESS, SUCCESS_BG, SUCCESS_TEXT,
    DANGER, DANGER_HOVER,
    TEXT_DARK, TEXT_BODY, TEXT_MUTED, TEXT_LIGHT,
    FONT_FAMILY,
)


class HistoryView(tk.Frame):
    """
    Dedicated view displaying conversion and translation history in a structured table,
    with interactive row selection to inspect full original and translated text.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)

        self._f_title    = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
        self._f_sub      = tkfont.Font(family=FONT_FAMILY, size=9)
        self._f_sec_h    = tkfont.Font(family=FONT_FAMILY, size=11, weight="bold")
        self._f_lbl      = tkfont.Font(family=FONT_FAMILY, size=8, weight="bold")
        self._f_btn      = tkfont.Font(family=FONT_FAMILY, size=9, weight="bold")
        self._f_body     = tkfont.Font(family=FONT_FAMILY, size=9)
        self._f_text     = tkfont.Font(family=FONT_FAMILY, size=10)
        self._f_text_hi  = tkfont.Font(family="Nirmala UI", size=10)
        self._f_badge    = tkfont.Font(family=FONT_FAMILY, size=8, weight="bold")

        self._items_by_iid: dict[str, dict] = {}
        self._selected_item: Optional[dict] = None

        self._init_styles()
        self._build_ui()
        self.refresh()

    def _init_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview row styling
        style.configure(
            "History.Treeview",
            background=SURFACE,
            foreground=TEXT_DARK,
            rowheight=32,
            fieldbackground=SURFACE,
            font=(FONT_FAMILY, 9),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "History.Treeview",
            background=[("selected", PRIMARY_BLUE)],
            foreground=[("selected", "#FFFFFF")],
        )

        # Treeview heading styling
        style.configure(
            "History.Treeview.Heading",
            background=SURFACE_ALT,
            foreground=TEXT_DARK,
            font=(FONT_FAMILY, 9, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "History.Treeview.Heading",
            background=[("active", "#E2E8F0")],
        )

    def _build_ui(self):
        # ── 1. Top Header Bar ──────────────────────────────────────────────
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(16, 12))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text="🕒 Conversion & Translation History",
            font=self._f_title,
            bg=BG,
            fg=TEXT_DARK,
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Review all conversions. Click any record in the table to inspect original and translated text.",
            font=self._f_sub,
            bg=BG,
            fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        btn_clear = tk.Button(
            header,
            text="🗑️  Clear All History",
            font=self._f_btn,
            bg=SURFACE,
            fg=DANGER,
            activebackground=SURFACE_ALT,
            relief="flat",
            bd=1,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._clear_history,
        )
        btn_clear.pack(side="right")

        # ── 2. Main Content Split Workspace ────────────────────────────────
        workspace = tk.Frame(self, bg=BG)
        workspace.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        workspace.rowconfigure(0, weight=5)  # Table row
        workspace.rowconfigure(1, weight=6)  # Details card row
        workspace.columnconfigure(0, weight=1)

        # ── Upper Card: History Table ──────────────────────────────────────
        table_card = tk.Frame(workspace, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        table_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # Table header info
        table_top = tk.Frame(table_card, bg=SURFACE)
        table_top.pack(fill="x", padx=16, pady=(10, 6))

        tk.Label(
            table_top,
            text="History Records",
            font=self._f_sec_h,
            bg=SURFACE,
            fg=TEXT_DARK,
        ).pack(side="left")

        self._lbl_record_count = tk.Label(
            table_top,
            text="0 entries",
            font=self._f_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
        )
        self._lbl_record_count.pack(side="right")

        # Treeview Table Container
        tree_container = tk.Frame(table_card, bg=SURFACE)
        tree_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        columns = ("mode", "languages", "datetime", "preview")
        self._tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            style="History.Treeview",
            selectmode="browse",
        )

        self._tree.heading("mode", text="Type / Mode", anchor="w")
        self._tree.heading("languages", text="Language to Language", anchor="w")
        self._tree.heading("datetime", text="Date & Time", anchor="w")
        self._tree.heading("preview", text="Text Preview", anchor="w")

        self._tree.column("mode", width=150, minwidth=130, stretch=False, anchor="w")
        self._tree.column("languages", width=230, minwidth=170, stretch=False, anchor="w")
        self._tree.column("datetime", width=170, minwidth=140, stretch=False, anchor="w")
        self._tree.column("preview", width=300, minwidth=180, stretch=True, anchor="w")

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)

        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self._tree.tag_configure("even", background="#FFFFFF")
        self._tree.tag_configure("odd", background="#F8FAFC")

        self._tree.bind("<<TreeviewSelect>>", self._on_row_selected)
        self._tree.bind("<ButtonRelease-1>", self._on_row_selected)

        # ── Lower Card: Selected Item Text Details ─────────────────────────
        self._details_card = tk.Frame(workspace, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        self._details_card.grid(row=1, column=0, sticky="nsew")

        self._build_details_panel(self._details_card)

    def _build_details_panel(self, parent):
        inner = tk.Frame(parent, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        # Header of Details Card
        detail_header = tk.Frame(inner, bg=SURFACE)
        detail_header.pack(fill="x", pady=(0, 10))

        tk.Label(
            detail_header,
            text="Selected Record Text",
            font=self._f_sec_h,
            bg=SURFACE,
            fg=TEXT_DARK,
        ).pack(side="left")

        # Badges row on right side of header
        self._badge_box = tk.Frame(detail_header, bg=SURFACE)
        self._badge_box.pack(side="right")

        self._lbl_badge_mode = tk.Label(
            self._badge_box,
            text="Speech to Text",
            font=self._f_badge,
            bg="#EFF6FF",
            fg=PRIMARY_BLUE,
            padx=8,
            pady=3,
        )
        self._lbl_badge_mode.pack(side="left", padx=(0, 6))

        self._lbl_badge_lang = tk.Label(
            self._badge_box,
            text="English → Hindi",
            font=self._f_badge,
            bg="#F1F5F9",
            fg=TEXT_BODY,
            padx=8,
            pady=3,
        )
        self._lbl_badge_lang.pack(side="left", padx=(0, 6))

        self._lbl_badge_date = tk.Label(
            self._badge_box,
            text="",
            font=self._f_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
        )
        self._lbl_badge_date.pack(side="left")

        # Placeholder label when no item selected
        self._lbl_no_selection = tk.Label(
            inner,
            text="👆 Click any row in the table above to view original and translated text",
            font=self._f_sub,
            bg=SURFACE,
            fg=TEXT_MUTED,
        )

        # Dual Text Columns container
        self._text_container = tk.Frame(inner, bg=SURFACE)
        self._text_container.pack(fill="both", expand=True)
        self._text_container.columnconfigure(0, weight=1, uniform="hist_cols")
        self._text_container.columnconfigure(1, weight=1, uniform="hist_cols")
        self._text_container.rowconfigure(0, weight=1)

        # ── Column 0: Original Text ────────────────────────────────────────
        col0 = tk.Frame(self._text_container, bg=SURFACE)
        col0.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        c0_top = tk.Frame(col0, bg=SURFACE)
        c0_top.pack(fill="x", pady=(0, 4))

        self._lbl_orig_title = tk.Label(
            c0_top,
            text="Original Text",
            font=self._f_lbl,
            bg=SURFACE,
            fg=TEXT_BODY,
        )
        self._lbl_orig_title.pack(side="left")

        self._btn_copy_orig = tk.Button(
            c0_top,
            text="📋 Copy",
            font=self._f_badge,
            bg=SURFACE,
            fg=TEXT_MUTED,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._copy_original,
        )
        self._btn_copy_orig.pack(side="right")

        box0 = tk.Frame(col0, bg=SURFACE_ALT, highlightbackground=BORDER, highlightthickness=1)
        box0.pack(fill="both", expand=True)

        self._txt_orig = tk.Text(
            box0,
            font=self._f_text,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
        )
        scroll0 = ttk.Scrollbar(box0, orient="vertical", command=self._txt_orig.yview)
        self._txt_orig.configure(yscrollcommand=scroll0.set)
        self._txt_orig.pack(side="left", fill="both", expand=True)
        scroll0.pack(side="right", fill="y")

        # ── Column 1: Translated Text ──────────────────────────────────────
        col1 = tk.Frame(self._text_container, bg=SURFACE)
        col1.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        c1_top = tk.Frame(col1, bg=SURFACE)
        c1_top.pack(fill="x", pady=(0, 4))

        self._lbl_trans_title = tk.Label(
            c1_top,
            text="Translated Text",
            font=self._f_lbl,
            bg=SURFACE,
            fg=SUCCESS_TEXT,
        )
        self._lbl_trans_title.pack(side="left")

        self._btn_copy_trans = tk.Button(
            c1_top,
            text="📋 Copy",
            font=self._f_badge,
            bg=SURFACE,
            fg=TEXT_MUTED,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._copy_translated,
        )
        self._btn_copy_trans.pack(side="right")

        box1 = tk.Frame(col1, bg=SURFACE_ALT, highlightbackground=BORDER, highlightthickness=1)
        box1.pack(fill="both", expand=True)

        self._txt_trans = tk.Text(
            box1,
            font=self._f_text_hi,
            bg=SURFACE_ALT,
            fg=TEXT_DARK,
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
        )
        scroll1 = ttk.Scrollbar(box1, orient="vertical", command=self._txt_trans.yview)
        self._txt_trans.configure(yscrollcommand=scroll1.set)
        self._txt_trans.pack(side="left", fill="both", expand=True)
        scroll1.pack(side="right", fill="y")

    # ── Refresh & Table Population ─────────────────────────────────────────

    def refresh(self):
        """Reloads history records and repopulates the Treeview table."""
        # Clear existing rows
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._items_by_iid.clear()

        items = HistoryManager.load_history()
        self._lbl_record_count.config(text=f"{len(items)} entries")

        if not items:
            self._badge_box.pack_forget()
            self._text_container.pack_forget()
            self._lbl_no_selection.config(text="No conversion history yet.\nStart converting speech or text on the Home dashboard!")
            self._lbl_no_selection.pack(expand=True, pady=40)
            return

        self._lbl_no_selection.pack_forget()
        self._badge_box.pack(side="right")
        self._text_container.pack(fill="both", expand=True)

        for idx, item in enumerate(items):
            iid = f"row_{idx}"
            self._items_by_iid[iid] = item

            # Format Mode / Type: explicitly 'Speech to Text' or 'Text to Speech'
            raw_type = item.get("type", "")
            if "Speech" in raw_type:
                mode_str = "Speech to Text"
            else:
                mode_str = "Text to Speech"

            # Format Language Pair: e.g. English -> Hindi
            s_lang = item.get("source_lang", "English")
            t_lang = item.get("target_lang", "Hindi")
            # Clean up display (take short name if long)
            s_short = s_lang.split("(")[0].strip() if s_lang else "English"
            t_short = t_lang.split("(")[0].strip() if t_lang else "Hindi"
            lang_str = f"{s_short}  →  {t_short}"

            # Format Date & Time
            d = item.get("date", "")
            t = item.get("time", "")
            date_time_str = f"{d}, {t}".strip(", ")

            # Format Preview
            src_text = (item.get("source_text") or item.get("title") or "").replace("\n", " ").strip()
            preview_str = src_text[:70] + ("..." if len(src_text) > 70 else "")

            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert(
                "",
                "end",
                iid=iid,
                values=(mode_str, lang_str, date_time_str, preview_str),
                tags=(tag,),
            )

        # Automatically select the first item
        first_iid = "row_0"
        if first_iid in self._items_by_iid:
            self._tree.selection_set(first_iid)
            self._tree.focus(first_iid)
            self._display_item(self._items_by_iid[first_iid])

    # ── Interactive Row Selection ──────────────────────────────────────────

    def _on_row_selected(self, event=None):
        selected_ids = self._tree.selection()
        if not selected_ids:
            return
        iid = selected_ids[0]
        item = self._items_by_iid.get(iid)
        if item:
            self._display_item(item)

    def _display_item(self, item: dict):
        self._selected_item = item

        # Mode label
        raw_type = item.get("type", "")
        if "Speech" in raw_type:
            mode_str = "🎙️  Speech to Text"
            self._lbl_badge_mode.config(text=mode_str, bg="#EFF6FF", fg=PRIMARY_BLUE)
        else:
            mode_str = "📄  Text to Speech"
            self._lbl_badge_mode.config(text=mode_str, bg="#F5F3FF", fg="#7C3AED")

        # Languages
        s_lang = item.get("source_lang", "English")
        t_lang = item.get("target_lang", "Hindi")
        self._lbl_badge_lang.config(text=f"🌐  {s_lang}  →  {t_lang}")

        # Date & Time
        d = item.get("date", "")
        t = item.get("time", "")
        self._lbl_badge_date.config(text=f"📅 {d} at {t}")

        # Update text labels
        s_short = s_lang.split("(")[0].strip() if s_lang else "Original"
        t_short = t_lang.split("(")[0].strip() if t_lang else "Translated"
        self._lbl_orig_title.config(text=f"Original Text ({s_short})")
        self._lbl_trans_title.config(text=f"Translated Text ({t_short})")

        # Populate text areas
        src_text = item.get("source_text") or item.get("title") or ""
        trans_text = item.get("translated_text") or ""

        self._txt_orig.config(state="normal")
        self._txt_orig.delete("1.0", "end")
        self._txt_orig.insert("1.0", src_text)

        self._txt_trans.config(state="normal")
        self._txt_trans.delete("1.0", "end")
        self._txt_trans.insert("1.0", trans_text)

    # ── Copy Actions ───────────────────────────────────────────────────────

    def _copy_original(self):
        text = self._txt_orig.get("1.0", "end-1c").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._btn_copy_orig.config(text="✓ Copied!", fg=SUCCESS)
        self.after(1500, lambda: self._btn_copy_orig.config(text="📋 Copy", fg=TEXT_MUTED))

    def _copy_translated(self):
        text = self._txt_trans.get("1.0", "end-1c").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._btn_copy_trans.config(text="✓ Copied!", fg=SUCCESS)
        self.after(1500, lambda: self._btn_copy_trans.config(text="📋 Copy", fg=TEXT_MUTED))

    # ── Clear History ──────────────────────────────────────────────────────

    def _clear_history(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all conversion history?"):
            HistoryManager.clear_all()
            self.refresh()
