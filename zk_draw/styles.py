"""Global QSS stylesheet."""

from . import config


def stylesheet() -> str:
    return f"""
    QToolTip {{
        background: #1E2024;
        color: #F0F2F5;
        border: 1px solid #444750;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
    }}
    QMenu {{
        background: {config.FLYOUT_BG};
        color: {config.FLYOUT_TEXT};
        border: 1px solid {config.FLYOUT_BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 18px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {config.ACTIVE_CYAN};
        color: #FFFFFF;
    }}
    QLabel {{ background: transparent; }}
    """

