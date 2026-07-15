"""Small reusable widgets: icon buttons, colour swatches, size dots."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QFrame, QToolButton, QWidget

from . import config, icons


class RoundedFrame(QWidget):
    """A frameless translucent widget painting a rounded dark background.

    Used as the visual shell for the toolbar and the tools panel.
    """

    RADIUS = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(config.PANEL_BORDER), 1))
        p.setBrush(QColor(config.PANEL_BG))
        p.drawRoundedRect(rect, self.RADIUS, self.RADIUS)
        p.end()


def v_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFixedWidth(1)
    line.setStyleSheet(f"color:{config.PANEL_BORDER};"
                       f"background:{config.PANEL_BORDER};border:none;")
    return line


def h_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"color:{config.PANEL_BORDER};"
                       f"background:{config.PANEL_BORDER};border:none;")
    return line


class ToolButton(QToolButton):
    """An icon button with hover / checked styling driven by QSS."""

    def __init__(self, name: str, tooltip: str = "", size: int = 24,
                 checkable: bool = False, parent=None):
        super().__init__(parent)
        self._icon_name = name
        self._icon_px = size
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAutoRaise(True)
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        self.setIcon(icons.icon(self._icon_name, self._icon_px, config.ICON))
        self.setIconSize(QSize(self._icon_px, self._icon_px))

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self._refresh_icon()


class ColorSwatch(QAbstractButton):
    """A rounded colour square; shows a ring when selected."""

    def __init__(self, color: str, size: int = 22, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self._size = size
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(size + 8, size + 8)
        self.setToolTip(color)

    def sizeHint(self) -> QSize:
        return QSize(self._size + 8, self._size + 8)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(4, 4, -4, -4)
        # selection / hover ring
        if self.isChecked():
            p.setPen(QPen(QColor(config.ACCENT), 2.4))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        elif self.underMouse():
            p.setPen(QPen(QColor(config.PANEL_BORDER), 1.4))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        # the colour itself
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        if self.color.lightnessF() > 0.9:
            p.setPen(QPen(QColor(config.PANEL_BORDER), 1))
        p.setBrush(self.color)
        p.drawRoundedRect(r, 4, 4)
        p.end()


class SizeDot(QAbstractButton):
    """A dot whose diameter maps to a stroke width; checkable in a group."""

    def __init__(self, width: int, kind: str = "pen", box: int = 30, parent=None):
        super().__init__(parent)
        self.width_value = width
        self.kind = kind
        self._box = box
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(box, box)
        self.setToolTip(f"{width}px")

    def sizeHint(self) -> QSize:
        return QSize(self._box, self._box)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        if self.isChecked():
            p.setPen(QPen(QColor(config.ACCENT), 2))
            p.setBrush(QColor(config.ACCENT_SOFT))
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        elif self.underMouse():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(config.PANEL_HOVER))
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        # preview dot, clamped to the box
        d = max(3, min(self.width_value, self._box - 12))
        c = self._box / 2.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(config.ICON))
        p.drawEllipse(c - d / 2, c - d / 2, d, d)
        p.end()
