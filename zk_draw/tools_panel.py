"""The floating drawing-tools panel (pen, colours, sizes, eraser, undo/redo).

It is shown whenever screen-draw or whiteboard mode is active and moves
together with the main toolbar.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from . import config
from .widgets import ColorSwatch, RoundedFrame, SizeDot, ToolButton, v_separator


class ToolsPanel(RoundedFrame):
    # mode is one of "pen", "eraser", "none" (none = use computer normally)
    modeChanged = Signal(str)
    colorChanged = Signal(QColor)
    penWidthChanged = Signal(int)
    eraserWidthChanged = Signal(int)
    clearRequested = Signal()
    undoRequested = Signal()
    redoRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint
                            | Qt.Tool
                            | Qt.NoDropShadowWindowHint)
        self._mode = "pen"
        self._build()
        self._select_defaults()

    # --- construction -------------------------------------------------------
    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        # -- tools: pen + eraser (mutually exclusive, both can toggle to none)
        self.btn_pen = ToolButton("pen", "Bút vẽ (nhấn lại để dùng máy tính)",
                                   26, checkable=True)
        self.btn_eraser = ToolButton("eraser", "Tẩy (chọn cỡ bên phải)",
                                     26, checkable=True)
        self.btn_pen.clicked.connect(lambda: self._toggle_tool("pen"))
        self.btn_eraser.clicked.connect(lambda: self._toggle_tool("eraser"))
        tools = QHBoxLayout()
        tools.setSpacing(2)
        tools.addWidget(self.btn_pen)
        tools.addWidget(self.btn_eraser)
        root.addLayout(tools)

        root.addWidget(v_separator())

        # -- pen sizes
        self.pen_size_group = QButtonGroup(self)
        self.pen_size_group.setExclusive(True)
        pen_sizes = QHBoxLayout()
        pen_sizes.setSpacing(2)
        for w in config.PEN_SIZES:
            dot = SizeDot(w, "pen")
            self.pen_size_group.addButton(dot, w)
            dot.clicked.connect(lambda _=False, val=w: self._on_pen_width(val))
            pen_sizes.addWidget(dot)
        root.addLayout(pen_sizes)

        root.addWidget(v_separator())

        # -- colour swatches (2 rows)
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)
        colors = QGridLayout()
        colors.setHorizontalSpacing(2)
        colors.setVerticalSpacing(2)
        per_row = (len(config.PALETTE) + 1) // 2
        for i, hexc in enumerate(config.PALETTE):
            sw = ColorSwatch(hexc)
            self.color_group.addButton(sw, i)
            sw.clicked.connect(lambda _=False, c=hexc: self._on_color(c))
            colors.addWidget(sw, i // per_row, i % per_row)
        root.addLayout(colors)

        root.addWidget(v_separator())

        # -- eraser sizes
        self.eraser_size_group = QButtonGroup(self)
        self.eraser_size_group.setExclusive(True)
        er = QVBoxLayout()
        er.setSpacing(1)
        er_label = QLabel("Tẩy")
        er_label.setAlignment(Qt.AlignHCenter)
        er_label.setStyleSheet(
            f"color:{config.TEXT_DIM};font-size:10px;background:transparent;")
        er_row = QHBoxLayout()
        er_row.setSpacing(2)
        for w in config.ERASER_SIZES:
            dot = SizeDot(w, "eraser", box=30)
            self.eraser_size_group.addButton(dot, w)
            dot.clicked.connect(
                lambda _=False, val=w: self._on_eraser_width(val))
            er_row.addWidget(dot)
        er.addWidget(er_label)
        er.addLayout(er_row)
        root.addLayout(er)

        root.addWidget(v_separator())

        # -- clear / undo / redo
        self.btn_clear = ToolButton("trash", "Xóa hết", 24)
        self.btn_undo = ToolButton("undo", "Hoàn tác (Ctrl+Z)", 24)
        self.btn_redo = ToolButton("redo", "Làm lại (Ctrl+Y)", 24)
        self.btn_clear.clicked.connect(self.clearRequested)
        self.btn_undo.clicked.connect(self.undoRequested)
        self.btn_redo.clicked.connect(self.redoRequested)
        actions = QHBoxLayout()
        actions.setSpacing(2)
        actions.addWidget(self.btn_clear)
        actions.addWidget(self.btn_undo)
        actions.addWidget(self.btn_redo)
        root.addLayout(actions)

        self.btn_undo.setEnabled(False)
        self.btn_redo.setEnabled(False)

    def _select_defaults(self) -> None:
        # default colour + pen size checked
        for btn in self.color_group.buttons():
            if btn.color == QColor(config.DEFAULT_COLOR):
                btn.setChecked(True)
                break
        b = self.pen_size_group.button(config.DEFAULT_PEN_SIZE)
        if b:
            b.setChecked(True)
        b = self.eraser_size_group.button(config.DEFAULT_ERASER_SIZE)
        if b:
            b.setChecked(True)
        self.btn_pen.setChecked(True)

    # --- interaction --------------------------------------------------------
    def _toggle_tool(self, tool: str) -> None:
        if self._mode == tool:
            self.set_mode("none")
        else:
            self.set_mode(tool)

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.btn_pen.setChecked(mode == "pen")
        self.btn_eraser.setChecked(mode == "eraser")
        self.modeChanged.emit(mode)

    def mode(self) -> str:
        return self._mode

    def _on_color(self, hexc: str) -> None:
        self.colorChanged.emit(QColor(hexc))
        # choosing a colour means we want to draw with the pen
        if self._mode != "pen":
            self.set_mode("pen")

    def _on_pen_width(self, w: int) -> None:
        self.penWidthChanged.emit(w)
        if self._mode != "pen":
            self.set_mode("pen")

    def _on_eraser_width(self, w: int) -> None:
        self.eraserWidthChanged.emit(w)
        self.set_mode("eraser")

    def set_history(self, can_undo: bool, can_redo: bool) -> None:
        self.btn_undo.setEnabled(can_undo)
        self.btn_redo.setEnabled(can_redo)
