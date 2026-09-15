"""Custom mouse cursors that preview the current brush size."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPixmap


def make_tool_cursor(tool: str, width: int, color) -> QCursor:
    """A ring the size of the brush with a centre dot (hotspot = centre)."""
    diameter = max(8, min(int(width), 128)) + 8
    screen = QGuiApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    pm = QPixmap(round(diameter * dpr), round(diameter * dpr))
    pm.setDevicePixelRatio(dpr)     # keep the cursor crisp on HiDPI
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    c = diameter / 2.0
    r = max(3.0, width / 2.0)

    if tool == "eraser":
        p.setPen(QPen(QColor("#000000"), 1.4))
        p.setBrush(QColor(255, 255, 255, 180))
        p.drawEllipse(QRectF(c - r, c - r, 2 * r, 2 * r))
        p.setPen(QPen(QColor("#FFFFFF"), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(c - r + 1, c - r + 1, 2 * r - 2, 2 * r - 2))
    else:
        col = QColor(color)
        # outline ring for visibility over any background
        p.setPen(QPen(QColor(255, 255, 255, 220), 1.6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(c - r, c - r, 2 * r, 2 * r))
        p.setPen(QPen(QColor(0, 0, 0, 160), 0.8))
        p.drawEllipse(QRectF(c - r - 0.8, c - r - 0.8, 2 * r + 1.6, 2 * r + 1.6))
        # centre dot in the pen colour
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(QRectF(c - 1.4, c - 1.4, 2.8, 2.8))
    p.end()
    return QCursor(pm, int(c), int(c))
