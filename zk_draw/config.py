import os

APP_NAME = "ZK_Draw"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_MARK_PATH = os.path.join(ASSETS_DIR, "logo", "mark-light-bg.png")

# 12 preset colours matching modern UI palette:
# Row 1: Royal Blue (#2563EB), Red (#EF4444), Orange (#F59E0B), Yellow (#FACC15)
# Row 2: White (#FFFFFF), Black/Dark Slate (#0F172A), Brown (#854D0E), Lime (#84CC16)
# Row 3: Cyan (#06B6D4), Magenta (#EC4899), Sky Blue (#38BDF8), Purple (#8A2BE2)
PALETTE = [
    "#2563EB",  # Royal Blue
    "#EF4444",  # Red
    "#F59E0B",  # Orange
    "#FACC15",  # Yellow
    "#FFFFFF",  # White
    "#0F172A",  # Dark Slate / Black
    "#854D0E",  # Brown
    "#84CC16",  # Lime Green
    "#06B6D4",  # Cyan
    "#EC4899",  # Magenta
    "#38BDF8",  # Sky Blue
    "#8A2BE2",  # Purple
]

# Slider ranges for pen and eraser
PEN_MIN = 1
PEN_MAX = 25
DEFAULT_PEN_SIZE = 8

ERASER_MIN = 6
ERASER_MAX = 60
DEFAULT_ERASER_SIZE = 24

HIGHLIGHTER_ALPHA = 120
DEFAULT_HIGHLIGHTER_SIZE = 22

DEFAULT_COLOR = "#2563EB"

# --- Modern Light Theme (Clean White Pill & Modern Card) --------------------
# Main toolbar pill
PILL_BG = "#FFFFFF"
PILL_BORDER = "#E2E8F0"
PILL_HEADER_TEXT = "#475569"
BTN_BG = "#FFFFFF"
BTN_HOVER = "#F1F5F9"
BTN_PRESSED = "#E2E8F0"
ACTIVE_BLUE = "#2563EB"
ACTIVE_BLUE_LIGHT = "#EFF6FF"
ACTIVE_CYAN = "#2563EB"
ICON_NORMAL = "#64748B"
ICON_ACTIVE = "#FFFFFF"
ICON_DARK = "#475569"
ICON_LIGHT = "#FFFFFF"

# Modern Light flyout panel
FLYOUT_BG = "#FFFFFF"
FLYOUT_BORDER = "#E2E8F0"
FLYOUT_PREVIEW_BG = "#F8FAFC"
FLYOUT_TEXT = "#475569"
FLYOUT_TEXT_DARK = "#1E293B"
FLYOUT_TEXT_MUTED = "#94A3B8"

# Legacy aliases for compatibility
ACCENT = ACTIVE_BLUE
ACCENT_SOFT = ACTIVE_BLUE_LIGHT
PANEL_BG = FLYOUT_BG
PANEL_BG2 = "#F8FAFC"
PANEL_HOVER = BTN_HOVER
PANEL_BORDER = FLYOUT_BORDER
TEXT = FLYOUT_TEXT
TEXT_DIM = FLYOUT_TEXT_MUTED
ICON = ICON_NORMAL

WHITEBOARD_BG = "#FFFFFF"
WHITEBOARD_DOT = "#CBD5E1"
WHITEBOARD_DOT_SPACING = 24

# Geometry
TB_WIDTH = 54
TB_BTN = 40

