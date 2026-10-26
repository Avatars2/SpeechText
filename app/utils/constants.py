import os

# ── Left Sidebar (Dark Navy) ───────────────────────────────────────────────
SIDEBAR_BG          = "#0B132B"   # Deep Midnight Navy
SIDEBAR_HOVER       = "#16234D"   # Hover state for nav items
SIDEBAR_ACTIVE_BG   = "#2563EB"   # Active blue pill (#2563EB)
SIDEBAR_TEXT        = "#FFFFFF"   # White text
SIDEBAR_MUTED       = "#94A3B8"   # Slate 400
SIDEBAR_BORDER      = "#1E293B"   # Subtle divider line
SIDEBAR_WIDTH       = 240         # Fixed width for sidebar

# ── Main Content Canvas ────────────────────────────────────────────────────
BG                  = "#F4F7FB"   # Soft Slate/Blue clean background
SURFACE             = "#FFFFFF"   # Pure white container cards
SURFACE_ALT         = "#F8FAFC"   # Text inputs & preview boxes
BORDER              = "#E2E8F0"   # Card outline & dividers
BORDER_FOCUS        = "#93C5FD"   # Focused border (Soft Blue)

# ── Brand & Accent Colors ──────────────────────────────────────────────────
PRIMARY_BLUE        = "#2563EB"   # Active button / Hero badge
PRIMARY_BLUE_HOVER  = "#1D4ED8"   # Blue hover
PRIMARY_BLUE_LIGHT  = "#EFF6FF"   # Light blue tint

ACCENT_STT          = "#2563EB"   # Primary Indigo / Blue
ACCENT_STT_HOVER    = "#1D4ED8"   # Hover state
ACCENT_STT_LIGHT    = "#EFF6FF"   # Light tint background
ACCENT_STT_PULSE    = "#BFDBFE"   # Pulse ring for recording

ACCENT_TTS          = "#059669"   # Emerald Green
ACCENT_TTS_HOVER    = "#047857"   # Darker Green
ACCENT_TTS_LIGHT    = "#ECFDF5"   # Light mint tint background

ACCENT_TRANS        = "#6366F1"   # Translation Purple/Indigo
ACCENT_TRANS_LIGHT  = "#EEF2FF"   # Light purple tint

# ── Semantic Colors ────────────────────────────────────────────────────────
SUCCESS             = "#10B981"   # Mint green status
SUCCESS_BG          = "#ECFDF5"   # Mint bg
SUCCESS_TEXT        = "#047857"   # Mint text
DANGER              = "#EF4444"   # Red danger
DANGER_HOVER        = "#DC2626"
WARNING             = "#F59E0B"   # Amber warning
INFO                = "#3B82F6"   # Info blue

# ── Typography & Text Colors ───────────────────────────────────────────────
TEXT_DARK           = "#0F172A"   # Headings / Primary (Slate 900)
TEXT_BODY           = "#334155"   # Content / Controls (Slate 700)
TEXT_MUTED          = "#64748B"   # Secondary / Subtitles (Slate 500)
TEXT_LIGHT          = "#FFFFFF"   # White text for active cards

FONT_FAMILY         = "Segoe UI"

# ── Window Settings ────────────────────────────────────────────────────────
WIN_WIDTH           = 1320
WIN_HEIGHT          = 840
WIN_MIN_WIDTH       = 1120
WIN_MIN_HEIGHT      = 720
WIN_TITLE           = "Speech & Text Converter"

# ── Storage Paths ──────────────────────────────────────────────────────────
DEFAULT_EXPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "exports"))
HISTORY_FILE_PATH   = os.path.join(DEFAULT_EXPORTS_DIR, "history.json")
