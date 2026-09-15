"""Reusable widgets: CapsuleFrame, FlyoutFrame, PillButton, ThicknessSlider, ColorSwatch."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import config, icons


class CapsuleFrame(QWidget):
    """A floating pill/capsule-shaped frame with pure white background and soft border."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)
        r = min(rect.width() / 2.0, 27.0)

        p.setPen(QPen(QColor(config.PILL_BORDER), 1.2))
        p.setBrush(QColor(config.PILL_BG))
        p.drawRoundedRect(rect, r, r)
        p.end()


class FlyoutFrame(QWidget):
    """A sleek, modern white card with smooth rounded corners."""

    RADIUS = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)
        p.setPen(QPen(QColor(config.FLYOUT_BORDER), 1.2))
        p.setBrush(QColor(config.FLYOUT_BG))
        p.drawRoundedRect(rect, self.RADIUS, self.RADIUS)
        p.end()


class RoundedFrame(QWidget):
    """Legacy rounded frame."""
    RADIUS = 12

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
    line.setStyleSheet(f"color:{config.PILL_BORDER};background:{config.PILL_BORDER};border:none;")
    return line


def h_separator(color: str = config.PILL_BORDER) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"color:{color};background:{color};border:none;")
    return line


class PillButton(QAbstractButton):
    """A modern tool button matching the mockup:

    - Active: Outer concentric Royal Blue ring, inner solid Royal Blue squircle,
      crisp white icon, and a small white indicator dot in the bottom-right corner.
    - Inactive: Clean transparent/white background with slate-gray icon (#64748B).
    - Hover: Soft subtle rounded background (#F1F5F9).
    """

    def __init__(self, icon_name: str, tooltip: str = "", size: int = 24,
                 checkable: bool = False, has_flyout: bool = False,
                 color_indicator: QColor | None = None, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._icon_size = size
        self._has_flyout = has_flyout
        self._color_indicator = color_indicator
        self.setCheckable(checkable)
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(config.TB_BTN, config.TB_BTN)

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self.update()

    def set_color_indicator(self, color: QColor | None) -> None:
        self._color_indicator = color
        self.update()

    def set_has_flyout(self, has_flyout: bool) -> None:
        self._has_flyout = has_flyout
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()

        if self.isChecked():
            # Outer concentric ring
            outer_r = QRectF(rect).adjusted(1.5, 1.5, -1.5, -1.5)
            p.setPen(QPen(QColor(config.ACTIVE_BLUE), 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(outer_r, 13, 13)

            # Inner squircle
            inner_r = QRectF(rect).adjusted(4.5, 4.5, -4.5, -4.5)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(config.ACTIVE_BLUE))
            p.drawRoundedRect(inner_r, 9, 9)

            # White icon
            pm = icons.pixmap(self._icon_name, self._icon_size, QColor(config.ICON_ACTIVE))
            x = round((self.width() - self._icon_size) / 2.0)
            y = round((self.height() - self._icon_size) / 2.0)
            p.drawPixmap(x, y, pm)

            # Small white indicator dot in bottom-right corner (matching mockup)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(inner_r.right() - 4.5, inner_r.bottom() - 4.5), 1.8, 1.8)

        else:
            if self.underMouse():
                hover_r = QRectF(rect).adjusted(2.5, 2.5, -2.5, -2.5)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(config.BTN_HOVER))
                p.drawRoundedRect(hover_r, 10, 10)

            # Normal icon
            pm = icons.pixmap(self._icon_name, self._icon_size, QColor(config.ICON_NORMAL))
            x = round((self.width() - self._icon_size) / 2.0)
            y = round((self.height() - self._icon_size) / 2.0)
            p.drawPixmap(x, y, pm)

            # Optional color strip if tool has color indicator and not checked
            if self._color_indicator is not None:
                strip_r = QRectF(rect.left() + 10, rect.bottom() - 5, rect.width() - 20, 2.5)
                p.setPen(Qt.NoPen)
                p.setBrush(self._color_indicator)
                p.drawRoundedRect(strip_r, 1.2, 1.2)

        p.end()


class ThicknessPreview(QWidget):
    """Live preview of stroke thickness and color in a light card container."""

    def __init__(self, thickness: int = config.DEFAULT_PEN_SIZE,
                 color: QColor = QColor(config.DEFAULT_COLOR), parent=None):
        super().__init__(parent)
        self._thickness = thickness
        self._color = QColor(color)
        self._translucent = False
        self.setFixedHeight(38)

    def set_thickness(self, w: int) -> None:
        self._thickness = max(1, int(w))
        self.update()

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.update()

    def set_translucent(self, enabled: bool) -> None:
        self._translucent = bool(enabled)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)

        # Light card container
        p.setPen(QPen(QColor(config.FLYOUT_BORDER), 1.2))
        p.setBrush(QColor(config.FLYOUT_PREVIEW_BG))
        p.drawRoundedRect(r, 12, 12)

        # Stroke line preview
        col = QColor(self._color)
        if self._translucent:
            col.setAlpha(config.HIGHLIGHTER_ALPHA)

        w = min(self._thickness, 22)
        pen = QPen(col, w)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        cy = self.height() / 2.0
        p.drawLine(QPointF(20, cy), QPointF(self.width() - 20, cy))
        p.end()


class ThicknessSlider(QWidget):
    """Modern light slider with dynamic bold-blue tick label highlighting."""

    valueChanged = Signal(int)

    def __init__(self, min_val: int = config.PEN_MIN,
                 max_val: int = config.PEN_MAX,
                 val: int = config.DEFAULT_PEN_SIZE,
                 ticks: tuple[int, ...] | None = None,
                 parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 4, 2, 0)
        lay.setSpacing(6)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(val)
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.setStyleSheet(f"""
            QSlider {{
                height: 24px;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {config.PILL_BORDER};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {config.ACTIVE_BLUE};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #FFFFFF;
                border: 3px solid {config.ACTIVE_BLUE};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #EFF6FF;
            }}
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        lay.addWidget(self.slider)

        # Tick labels row
        self.labels_row = QHBoxLayout()
        self.labels_row.setContentsMargins(6, 0, 6, 0)
        if ticks is None:
            ticks = (1, 5, 9, 13, 17, 21)
        self._ticks = ticks
        self._tick_labels: list[tuple[int, QLabel]] = []

        for i, num in enumerate(ticks):
            is_last = (i == len(ticks) - 1)
            text = f"{num}+" if is_last and max_val > num else str(num)
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{config.FLYOUT_TEXT_MUTED};font-size:9px;background:transparent;")
            self._tick_labels.append((num, lbl))
            self.labels_row.addWidget(lbl, 1, Qt.AlignHCenter)

        lay.addLayout(self.labels_row)
        self._update_tick_highlight(val)

    def _on_value_changed(self, val: int) -> None:
        self._update_tick_highlight(val)
        self.valueChanged.emit(val)

    def _update_tick_highlight(self, val: int) -> None:
        if not self._tick_labels:
            return
        # Find closest tick
        closest_num = min(self._ticks, key=lambda t: abs(t - val))
        for num, lbl in self._tick_labels:
            if num == closest_num:
                lbl.setStyleSheet(f"color:{config.ACTIVE_BLUE};font-weight:bold;font-size:10px;background:transparent;")
            else:
                lbl.setStyleSheet(f"color:{config.FLYOUT_TEXT_MUTED};font-size:9px;background:transparent;")

    def value(self) -> int:
        return self.slider.value()

    def setValue(self, val: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self._update_tick_highlight(val)
        self.slider.blockSignals(False)

    def setRange(self, min_val: int, max_val: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setRange(min_val, max_val)
        self.slider.blockSignals(False)


class ColorSwatch(QAbstractButton):
    """Squircle color swatch with concentric Royal Blue ring and centered checkmark when active."""

    def __init__(self, color: str, size: int = 32, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self._size = size
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(size, size)
        self.setToolTip(color.upper())

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()

        if self.isChecked():
            # Concentric active ring
            outer_r = QRectF(rect).adjusted(1.0, 1.0, -1.0, -1.0)
            p.setPen(QPen(QColor(config.ACTIVE_BLUE), 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(outer_r, 10, 10)

            # Inner squircle
            inner_r = QRectF(rect).adjusted(3.8, 3.8, -3.8, -3.8)
            p.setPen(Qt.NoPen)
            p.setBrush(self.color)
            p.drawRoundedRect(inner_r, 7, 7)

            # Centered checkmark
            cx, cy = self.width() / 2.0, self.height() / 2.0
            path = QPainterPath()
            path.moveTo(cx - 4.5, cy - 0.5)
            path.lineTo(cx - 1.2, cy + 3.0)
            path.lineTo(cx + 4.8, cy - 3.2)
            check_col = QColor("#FFFFFF") if self.color != QColor("#FFFFFF") else QColor(config.ACTIVE_BLUE)
            p.setPen(QPen(check_col, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

        else:
            r = QRectF(rect).adjusted(2.0, 2.0, -2.0, -2.0)
            if self.underMouse():
                p.setPen(QPen(QColor(config.ACTIVE_BLUE), 1.2))
            elif self.color == QColor("#FFFFFF"):
                p.setPen(QPen(QColor(config.PILL_BORDER), 1.2))
            else:
                p.setPen(Qt.NoPen)

            p.setBrush(self.color)
            p.drawRoundedRect(r, 9, 9)

        p.end()


class RainbowSwatch(QAbstractButton):
    """Custom color picker button with rainbow gradient border and crosshair icon."""

    colorPicked = Signal(QColor)

    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self._size = size
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(size, size)
        self.setToolTip("Chọn màu tùy chỉnh...")
        self.clicked.connect(self._open_dialog)

    def _open_dialog(self) -> None:
        col = QColorDialog.getColor(QColor(config.DEFAULT_COLOR), self, "Chọn màu")
        if col.isValid():
            self.colorPicked.emit(col)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(2.0, 2.0, -2.0, -2.0)

        # Rainbow gradient border
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0.0, QColor("#8A2BE2"))  # Purple
        grad.setColorAt(0.35, QColor("#EC4899")) # Magenta
        grad.setColorAt(0.70, QColor("#F59E0B")) # Orange
        grad.setColorAt(1.0, QColor("#FACC15"))  # Yellow

        p.setPen(QPen(QBrush(grad), 2.0))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(r, 9, 9)

        # Centered crosshair icon
        pm = icons.pixmap("crosshair", 16, QColor("#475569"))
        x = int((self.width() - 16) / 2.0)
        y = int((self.height() - 16) / 2.0)
        p.drawPixmap(x, y, pm)

        p.end()


class ToolButton(QToolButton):
    """Legacy tool button for backwards compatibility."""

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


class SizeDot(QAbstractButton):
    """Legacy size dot for backwards compatibility."""

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
        d = max(3, min(self.width_value, self._box - 12))
        c = self._box / 2.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(config.ICON))
        p.drawEllipse(QRectF(c - d / 2, c - d / 2, d, d))
        p.end()
