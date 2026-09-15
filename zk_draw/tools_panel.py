"""The modern Flyout Panel (COLORS grid, live HEX badge, THICKNESS preview, and independent sliders).

Pixel-perfect implementation matching the user's mockup design.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from . import config
from .widgets import (
    ColorSwatch,
    FlyoutFrame,
    RainbowSwatch,
    ThicknessPreview,
    ThicknessSlider,
)


class ColorHexBadge(QWidget):
    """Badge showing a filled color dot and uppercase hex code (e.g. ● #2563EB)."""

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        self.dot = QWidget()
        self.dot.setFixedSize(8, 8)
        self.dot.paintEvent = self._paint_dot

        self.lbl = QLabel(self._color.name().upper())
        self.lbl.setStyleSheet(f"color:{config.FLYOUT_TEXT_DARK};font-weight:bold;font-size:11px;background:transparent;")
        lay.addWidget(self.dot, 0, Qt.AlignVCenter)
        lay.addWidget(self.lbl, 0, Qt.AlignVCenter)

    def _paint_dot(self, event) -> None:
        p = QPainter(self.dot)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(self._color)
        p.drawEllipse(0, 0, 8, 8)
        p.end()

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.lbl.setText(self._color.name().upper())
        self.dot.update()


class PxBadge(QLabel):
    """Pill badge showing thickness like '8 px' with soft blue background."""

    def __init__(self, px: int, parent=None):
        super().__init__(f"{px} px", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background: {config.ACTIVE_BLUE_LIGHT};
                color: {config.ACTIVE_BLUE};
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #DBEAFE;
                border-radius: 6px;
                padding: 2px 8px;
            }}
        """)

    def set_px(self, px: int) -> None:
        self.setText(f"{px} px")


class ToolFlyoutPanel(FlyoutFrame):
    """Modern light card beside the toolbar for Colors and Thickness."""

    colorChanged = Signal(QColor)
    thicknessChanged = Signal(int)
    penWidthChanged = Signal(int)
    eraserWidthChanged = Signal(int)
    translucentChanged = Signal(bool)
    closeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint
                            | Qt.X11BypassWindowManagerHint
                            | Qt.Tool
                            | Qt.NoDropShadowWindowHint)
        self._current_tool = "pen"
        self._color = QColor(config.DEFAULT_COLOR)
        self._pen_width = config.DEFAULT_PEN_SIZE        # 5
        self._eraser_width = config.DEFAULT_ERASER_SIZE  # 24
        self._translucent = False

        self._build()
        self._select_defaults()

    def _build(self) -> None:
        self.setFixedWidth(244)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # -- Section: COLORS (shown for Pen only) ----------------------------
        self.color_section = QWidget()
        self.color_section.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(self.color_section)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(8)

        # Header 1: "COLORS" + Live HEX badge
        h1 = QHBoxLayout()
        h1.setContentsMargins(0, 0, 0, 0)
        lbl_colors = QLabel("COLORS")
        lbl_colors.setStyleSheet(f"color:{config.FLYOUT_TEXT};font-weight:bold;font-size:11px;background:transparent;")
        h1.addWidget(lbl_colors, 0, Qt.AlignVCenter)
        h1.addStretch()

        self.color_badge = ColorHexBadge(self._color)
        h1.addWidget(self.color_badge, 0, Qt.AlignVCenter)
        c_lay.addLayout(h1)

        # 4 columns grid: 11 preset swatches + 1 rainbow picker
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, hexc in enumerate(config.PALETTE[:11]):
            sw = ColorSwatch(hexc, size=32)
            self.color_group.addButton(sw, i)
            sw.clicked.connect(lambda _=False, c=hexc: self._on_color(QColor(c)))
            grid.addWidget(sw, i // 4, i % 4)

        self.rainbow_swatch = RainbowSwatch(size=32)
        self.rainbow_swatch.colorPicked.connect(self._on_custom_color)
        grid.addWidget(self.rainbow_swatch, 2, 3)
        c_lay.addLayout(grid)

        root.addWidget(self.color_section)

        # -- Section: THICKNESS / SIZE ---------------------------------------
        self.thick_section = QWidget()
        self.thick_section.setStyleSheet("background:transparent;")
        t_lay = QVBoxLayout(self.thick_section)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(8)

        # Header 2: "THICKNESS" + Live PX badge
        h2 = QHBoxLayout()
        h2.setContentsMargins(0, 0, 0, 0)
        self.lbl_thick = QLabel("THICKNESS")
        self.lbl_thick.setStyleSheet(f"color:{config.FLYOUT_TEXT};font-weight:bold;font-size:11px;background:transparent;")
        h2.addWidget(self.lbl_thick, 0, Qt.AlignVCenter)
        h2.addStretch()

        self.px_badge = PxBadge(self._pen_width)
        h2.addWidget(self.px_badge, 0, Qt.AlignVCenter)
        t_lay.addLayout(h2)

        # Live preview box
        self.preview = ThicknessPreview(self._pen_width, self._color)
        t_lay.addWidget(self.preview)

        # 1. Independent Pen Slider (Range 1 to 25, default 5)
        self.pen_slider = ThicknessSlider(
            config.PEN_MIN, config.PEN_MAX, self._pen_width,
            ticks=(1, 5, 9, 13, 17, 21)
        )
        self.pen_slider.valueChanged.connect(self._on_pen_slider_moved)
        t_lay.addWidget(self.pen_slider)

        # 2. Independent Eraser Slider (Range 6 to 60, default 24)
        self.eraser_slider = ThicknessSlider(
            config.ERASER_MIN, config.ERASER_MAX, self._eraser_width,
            ticks=(6, 15, 25, 35, 45, 60)
        )
        self.eraser_slider.valueChanged.connect(self._on_eraser_slider_moved)
        self.eraser_slider.hide()
        t_lay.addWidget(self.eraser_slider)

        root.addWidget(self.thick_section)

    def _select_defaults(self) -> None:
        for btn in self.color_group.buttons():
            if btn.color == QColor(config.DEFAULT_COLOR):
                btn.setChecked(True)
                break

    # --- tool & property switching ------------------------------------------
    def set_tool(self, tool: str) -> None:
        """Switch flyout layout and slider according to current tool (pen vs eraser)."""
        self._current_tool = tool
        if tool == "eraser":
            self.color_section.hide()
            self.lbl_thick.setText("ERASER SIZE")
            self.px_badge.set_px(self._eraser_width)
            self.pen_slider.hide()
            self.eraser_slider.show()
            self.preview.set_color(QColor("#2563EB"))
            self.preview.set_thickness(self._eraser_width)
        else:  # pen
            self.color_section.show()
            self.lbl_thick.setText("THICKNESS")
            self.px_badge.set_px(self._pen_width)
            self.eraser_slider.hide()
            self.pen_slider.show()
            self.preview.set_color(self._color)
            self.preview.set_thickness(self._pen_width)
        self.adjustSize()

    def current_tool(self) -> str:
        return self._current_tool

    def _on_pen_slider_moved(self, val: int) -> None:
        self._pen_width = val
        self.px_badge.set_px(val)
        self.preview.set_thickness(val)
        self.penWidthChanged.emit(val)
        self.thicknessChanged.emit(val)

    def _on_eraser_slider_moved(self, val: int) -> None:
        self._eraser_width = val
        self.px_badge.set_px(val)
        self.preview.set_thickness(val)
        self.eraserWidthChanged.emit(val)
        self.thicknessChanged.emit(val)

    def _on_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.color_badge.set_color(self._color)
        if self._current_tool != "eraser":
            self.preview.set_color(self._color)
        self.colorChanged.emit(self._color)

    def _on_custom_color(self, color: QColor) -> None:
        self._on_color(color)
        checked = self.color_group.checkedButton()
        if checked:
            self.color_group.setExclusive(False)
            checked.setChecked(False)
            self.color_group.setExclusive(True)

    def _on_translucent(self, enabled: bool) -> None:
        self._translucent = enabled
        self.preview.set_translucent(enabled)
        self.translucentChanged.emit(enabled)

    def color(self) -> QColor:
        return QColor(self._color)

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.color_badge.set_color(self._color)
        if self._current_tool != "eraser":
            self.preview.set_color(self._color)

    def pen_width(self) -> int:
        return self._pen_width

    def set_pen_width(self, w: int) -> None:
        self._pen_width = int(w)
        self.px_badge.set_px(self._pen_width)
        self.pen_slider.setValue(self._pen_width)
        if self._current_tool != "eraser":
            self.preview.set_thickness(self._pen_width)

    def eraser_width(self) -> int:
        return self._eraser_width

    def set_eraser_width(self, w: int) -> None:
        self._eraser_width = int(w)
        self.px_badge.set_px(self._eraser_width)
        self.eraser_slider.setValue(self._eraser_width)
        if self._current_tool == "eraser":
            self.preview.set_thickness(self._eraser_width)

    def set_translucent(self, enabled: bool) -> None:
        pass


# Backwards compatibility alias
ToolsPanel = ToolFlyoutPanel
