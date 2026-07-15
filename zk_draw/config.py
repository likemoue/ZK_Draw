"""Central configuration: palette, sizes, theme colors."""

APP_NAME = "ZK_Draw"

# Preset colours shown as swatches in the tools panel.
PALETTE = [
    "#FF3B30",  # red
    "#FF9500",  # orange
    "#FFCC00",  # yellow
    "#34C759",  # green
    "#00C7BE",  # teal
    "#007AFF",  # blue
    "#5856D6",  # indigo
    "#AF52DE",  # purple
    "#FF2D55",  # pink
    "#8E8E93",  # gray
    "#000000",  # black
    "#FFFFFF",  # white
]

# Available pen stroke widths (px) and eraser widths (px).
PEN_SIZES = [2, 4, 8, 16]
ERASER_SIZES = [24, 48, 96]

DEFAULT_COLOR = "#FF3B30"
DEFAULT_PEN_SIZE = 4
DEFAULT_ERASER_SIZE = 48

# --- Theme -----------------------------------------------------------------
ACCENT = "#2D7DF6"          # highlight / selected state
ACCENT_SOFT = "#1B4C99"
PANEL_BG = "#22242B"        # toolbar / panel background
PANEL_BG2 = "#2C2F38"       # button background
PANEL_HOVER = "#3A3E4A"
PANEL_BORDER = "#40444F"
TEXT = "#F2F3F5"
TEXT_DIM = "#9AA0AB"
ICON = "#E6E8EC"

WHITEBOARD_BG = "#FFFFFF"   # whiteboard background colour

# Toolbar geometry
TB_BTN = 46                 # main toolbar button size (px)
TB_MARGIN = 8
