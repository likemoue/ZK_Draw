"""Global QSS stylesheet."""

from . import config


def stylesheet() -> str:
    return f"""
    QToolTip {{
        background: {config.PANEL_BG2};
        color: {config.TEXT};
        border: 1px solid {config.PANEL_BORDER};
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
    }}
    QToolButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 4px;
    }}
    QToolButton:hover {{
        background: {config.PANEL_HOVER};
        border: 1px solid {config.PANEL_BORDER};
    }}
    QToolButton:pressed {{
        background: {config.PANEL_BG2};
    }}
    QToolButton:checked {{
        background: {config.ACCENT_SOFT};
        border: 1px solid {config.ACCENT};
    }}
    QToolButton:disabled {{
        opacity: 0.4;
    }}
    QMenu {{
        background: {config.PANEL_BG};
        color: {config.TEXT};
        border: 1px solid {config.PANEL_BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 18px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {config.ACCENT_SOFT};
    }}
    QLabel {{ background: transparent; }}
    """
