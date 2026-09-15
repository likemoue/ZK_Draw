"""The main floating vertical capsule toolbar — IPEVO-style.

Two mutually exclusive main modes:
    1. Screen Drawing  (screen-pen icon) — draw on the live desktop
    2. Whiteboard       (whiteboard icon) — draw on a solid white board

Sub-tools (work within the active mode):
    3. Eraser
    4. Pointer / Cursor (click-through)
    5. Undo, Redo, Trash, Camera
    6. Collapse chevron
"""

import os

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import config, icons
from .widgets import CapsuleFrame, PillButton, h_separator


class DragHandle(QWidget):
    """The rounded top capsule cap with ZK Logo; drag to move toolbar."""

    moved = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedHeight(38)
        self._press_global: QPoint | None = None
        self._win_start: QPoint | None = None
        self.setToolTip("ZK_Draw (Giữ chuột để di chuyển, chuột phải để thoát)")

        self._logo: QPixmap | None = None
        logo_path = getattr(config, "LOGO_MARK_PATH", "")
        if logo_path and os.path.exists(logo_path):
            pm = QPixmap(logo_path)
            if not pm.isNull():
                self._logo = pm

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if self._logo is not None:
            target_w, target_h = 28, 28
            scaled = self._logo.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = int((self.width() - scaled.width()) / 2.0)
            y = int((self.height() - scaled.height()) / 2.0 + 2)
            p.drawPixmap(x, y, scaled)
        else:
            f = QFont()
            f.setPointSize(8)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(config.PILL_HEADER_TEXT))
            r = self.rect().adjusted(0, 4, 0, 0)
            p.drawText(r, Qt.AlignCenter, "ZK")
        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self._press_global = event.globalPosition().toPoint()
            self._win_start = self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is not None:
            gpos = event.globalPosition().toPoint()
            target = self._win_start + (gpos - self._press_global)
            self.window().move(self._clamp(target, gpos))
            self.moved.emit()

    def _clamp(self, target: QPoint, gpos: QPoint) -> QPoint:
        scr = QGuiApplication.screenAt(gpos) or QGuiApplication.primaryScreen()
        area = scr.availableGeometry()
        win = self.window()
        x = max(area.left(), min(target.x(), area.right() - win.width() + 1))
        y = max(area.top(), min(target.y(), area.bottom() - win.height() + 1))
        return QPoint(x, y)

    def mouseReleaseEvent(self, event) -> None:
        self.setCursor(Qt.OpenHandCursor)
        self._press_global = None
        self._win_start = None

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        act_quit = menu.addAction("Thoát ZK_Draw")
        chosen = menu.exec(event.globalPos())
        if chosen == act_quit:
            self.quitRequested.emit()


class MainToolbar(CapsuleFrame):
    """The vertical capsule toolbar — IPEVO style.

    Signals:
        modeChanged(str)   — "screen" or "whiteboard"
        toolChanged(str)   — "pen", "eraser", "pointer"
        undoRequested, redoRequested, clearRequested, snapshotRequested
        collapseToggled(bool), moved, quitRequested
    """

    modeChanged = Signal(str)            # "screen" | "whiteboard"
    toolChanged = Signal(str)            # "pen" | "eraser" | "pointer"
    togglePanel = Signal()               # toggle flyout panel visibility
    undoRequested = Signal()
    redoRequested = Signal()
    clearRequested = Signal()
    snapshotRequested = Signal()
    collapseToggled = Signal(bool)       # True -> collapsed
    moved = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint
                            | Qt.X11BypassWindowManagerHint
                            | Qt.Tool
                            | Qt.NoDropShadowWindowHint)
        self._collapsed = False
        self._mode = "screen"       # current mode
        self._tool = "pen"          # current sub-tool
        self._pen_color = QColor(config.DEFAULT_COLOR)
        self.setFixedWidth(config.TB_WIDTH)
        self._build()

    def _build(self) -> None:
        self.root_lay = QVBoxLayout(self)
        self.root_lay.setContentsMargins(6, 6, 6, 8)
        self.root_lay.setSpacing(4)

        # 1. Top Drag Handle with ZK logo
        self.header = DragHandle()
        self.header.moved.connect(self.moved)
        self.header.quitRequested.connect(self.quitRequested)
        self.root_lay.addWidget(self.header)

        # Divider under logo
        self.sep_logo = h_separator()
        self.root_lay.addWidget(self.sep_logo)

        # Direct container for all tools
        self.tools_container = QWidget()
        self.tools_container.setStyleSheet("background:transparent;")
        t_lay = QVBoxLayout(self.tools_container)
        t_lay.setContentsMargins(0, 0, 0, 0)
        t_lay.setSpacing(4)

        # ── MODE GROUP (exclusive: screen OR whiteboard) ───────────────
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        # A. Screen Drawing
        self.btn_screen = PillButton("screen-pen", "Vẽ lên màn hình",
                                     22, checkable=True,
                                     color_indicator=self._pen_color)
        self.mode_group.addButton(self.btn_screen)
        self.btn_screen.clicked.connect(lambda: self._on_mode_clicked("screen"))
        t_lay.addWidget(self.btn_screen, 0, Qt.AlignHCenter)

        # B. Whiteboard
        self.btn_whiteboard = PillButton("whiteboard", "Bảng trắng",
                                         22, checkable=True)
        self.mode_group.addButton(self.btn_whiteboard)
        self.btn_whiteboard.clicked.connect(lambda: self._on_mode_clicked("whiteboard"))
        t_lay.addWidget(self.btn_whiteboard, 0, Qt.AlignHCenter)

        t_lay.addWidget(h_separator())

        # ── SUB-TOOLS ─────────────────────────────────────────────────
        # C. Eraser
        self.btn_eraser = PillButton("eraser", "Cục tẩy (nhấn để chỉnh cỡ)",
                                     20, checkable=True, has_flyout=True)
        self.btn_eraser.clicked.connect(self._on_eraser_clicked)
        t_lay.addWidget(self.btn_eraser, 0, Qt.AlignHCenter)

        # D. Pointer (Cursor)
        self.btn_pointer = PillButton("cursor", "Thao tác chuột bình thường",
                                      20, checkable=True)
        self.btn_pointer.clicked.connect(self._on_pointer_clicked)
        t_lay.addWidget(self.btn_pointer, 0, Qt.AlignHCenter)

        t_lay.addWidget(h_separator())

        # ── ACTION BUTTONS ────────────────────────────────────────────
        self.btn_undo = PillButton("undo", "Hoàn tác (Ctrl+Z)", 20)
        self.btn_undo.clicked.connect(self.undoRequested)
        t_lay.addWidget(self.btn_undo, 0, Qt.AlignHCenter)

        self.btn_redo = PillButton("redo", "Làm lại (Ctrl+Y)", 20)
        self.btn_redo.clicked.connect(self.redoRequested)
        t_lay.addWidget(self.btn_redo, 0, Qt.AlignHCenter)

        self.btn_trash = PillButton("trash", "Xóa toàn bộ (Delete)", 20)
        self.btn_trash.clicked.connect(self.clearRequested)
        t_lay.addWidget(self.btn_trash, 0, Qt.AlignHCenter)

        self.btn_camera = PillButton("camera", "Chụp ảnh màn hình", 22)
        self.btn_camera.clicked.connect(self.snapshotRequested)
        t_lay.addWidget(self.btn_camera, 0, Qt.AlignHCenter)

        self.root_lay.addWidget(self.tools_container)

        # Separator bottom
        self.sep_bottom = h_separator()
        self.root_lay.addWidget(self.sep_bottom)

        # Collapse Chevron
        self.btn_collapse = PillButton("chev-up", "Thu nhỏ", 18)
        self.btn_collapse.setFixedHeight(24)
        self.btn_collapse.clicked.connect(self._toggle_collapse)
        self.root_lay.addWidget(self.btn_collapse, 0, Qt.AlignHCenter)

        # Default state: Screen Drawing active
        self.btn_screen.setChecked(True)

    # --- mode click handlers ------------------------------------------------
    def _on_mode_clicked(self, mode: str) -> None:
        """User clicked Screen or Whiteboard mode button."""
        # Uncheck sub-tool buttons
        self.btn_eraser.setChecked(False)
        self.btn_pointer.setChecked(False)

        if mode != self._mode:
            # Switching to a different mode
            self._mode = mode
            self._tool = "pen"
            self.modeChanged.emit(mode)
        else:
            # Clicked the already-active mode → toggle COLORS panel
            self._tool = "pen"
            self.togglePanel.emit()

    def _on_eraser_clicked(self) -> None:
        """Toggle eraser sub-tool within the current mode."""
        if self._tool == "eraser":
            # Already eraser → go back to pen
            self.btn_eraser.setChecked(False)
            self._tool = "pen"
            # Re-highlight the mode button
            if self._mode == "screen":
                self.btn_screen.setChecked(True)
            else:
                self.btn_whiteboard.setChecked(True)
            self.toolChanged.emit("pen")
        else:
            self._tool = "eraser"
            # Uncheck mode buttons visually, check eraser
            self.mode_group.setExclusive(False)
            self.btn_screen.setChecked(False)
            self.btn_whiteboard.setChecked(False)
            self.mode_group.setExclusive(True)
            self.btn_eraser.setChecked(True)
            self.btn_pointer.setChecked(False)
            self.toolChanged.emit("eraser")

    def _on_pointer_clicked(self) -> None:
        """Toggle pointer sub-tool (click-through)."""
        if self._tool == "pointer":
            # Already pointer → go back to pen
            self.btn_pointer.setChecked(False)
            self._tool = "pen"
            if self._mode == "screen":
                self.btn_screen.setChecked(True)
            else:
                self.btn_whiteboard.setChecked(True)
            self.toolChanged.emit("pen")
        else:
            self._tool = "pointer"
            self.mode_group.setExclusive(False)
            self.btn_screen.setChecked(False)
            self.btn_whiteboard.setChecked(False)
            self.mode_group.setExclusive(True)
            self.btn_eraser.setChecked(False)
            self.btn_pointer.setChecked(True)
            self.toolChanged.emit("pointer")

    # --- public API ---------------------------------------------------------
    def current_mode(self) -> str:
        return self._mode

    def current_tool(self) -> str:
        return self._tool

    def set_mode(self, mode: str) -> None:
        """Programmatically set the mode without emitting signals."""
        self._mode = mode
        if mode == "screen":
            self.btn_screen.setChecked(True)
        else:
            self.btn_whiteboard.setChecked(True)
        self.btn_eraser.setChecked(False)
        self.btn_pointer.setChecked(False)
        self._tool = "pen"

    def set_pen_color(self, color: QColor) -> None:
        self._pen_color = QColor(color)
        self.btn_screen.set_color_indicator(self._pen_color)

    def set_history(self, can_undo: bool, can_redo: bool) -> None:
        self.btn_undo.setEnabled(can_undo)
        self.btn_redo.setEnabled(can_redo)

    def _toggle_collapse(self) -> None:
        self.set_collapsed(not self._collapsed)
        self.collapseToggled.emit(self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.sep_logo.setVisible(not collapsed)
        self.tools_container.setVisible(not collapsed)
        self.sep_bottom.setVisible(not collapsed)
        self.btn_collapse.set_icon_name("chev-down" if collapsed else "chev-up")
        self.btn_collapse.setToolTip("Mở rộng" if collapsed else "Thu nhỏ")

        if collapsed:
            self.setFixedHeight(75)
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.adjustSize()

    def is_collapsed(self) -> bool:
        return self._collapsed
