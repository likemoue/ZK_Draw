"""The main floating toolbar: ZK_Draw handle, draw, whiteboard, collapse."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from . import config, icons
from .widgets import RoundedFrame, ToolButton, h_separator


class DragHandle(QWidget):
    """The 'ZK_Draw' title bar. Dragging it moves the whole toolbar window."""

    moved = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedHeight(30)
        self._press_global: QPoint | None = None
        self._win_start: QPoint | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 6, 2)
        lay.setSpacing(4)
        self.title = QLabel(config.APP_NAME)
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        self.title.setFont(f)
        self.title.setStyleSheet(
            f"color:{config.TEXT};background:transparent;")
        lay.addWidget(self.title, 1, Qt.AlignCenter)

    def paintEvent(self, event) -> None:
        # subtle grip dots behind the title for affordance
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(config.PANEL_BORDER))
        y = 6
        for i in range(2):
            for x in range(self.width() // 2 - 12, self.width() // 2 + 13, 6):
                p.drawEllipse(QPoint(x, y + i * 5), 1, 1)
        p.end()

    # dragging ---------------------------------------------------------------
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
        """Keep the toolbar fully on the screen under the cursor so it can
        never be dragged out of reach."""
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


class MainToolbar(RoundedFrame):
    drawRequested = Signal()
    whiteboardRequested = Signal()
    collapseToggled = Signal(bool)   # True -> collapsed
    moved = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint
                            | Qt.Tool
                            | Qt.NoDropShadowWindowHint)
        self._collapsed = False
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.header = DragHandle()
        self.header.moved.connect(self.moved)
        self.header.quitRequested.connect(self.quitRequested)
        root.addWidget(self.header)

        root.addWidget(h_separator())

        # collapsible body: the two main actions
        self.body = QWidget()
        self.body.setStyleSheet("background:transparent;")
        body_lay = QVBoxLayout(self.body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(6)

        self.btn_draw = ToolButton("pen", "Vẽ lên màn hình", 30,
                                   checkable=True)
        self.btn_draw.setFixedSize(config.TB_BTN, config.TB_BTN)
        self.btn_draw.clicked.connect(self.drawRequested)

        self.btn_board = ToolButton("whiteboard", "Bảng trắng", 30,
                                    checkable=True)
        self.btn_board.setFixedSize(config.TB_BTN, config.TB_BTN)
        self.btn_board.clicked.connect(self.whiteboardRequested)

        body_lay.addWidget(self.btn_draw, 0, Qt.AlignHCenter)
        body_lay.addWidget(self.btn_board, 0, Qt.AlignHCenter)
        root.addWidget(self.body)

        root.addWidget(h_separator())

        # collapse / expand arrow (always visible)
        self.btn_collapse = ToolButton("chev-up", "Thu nhỏ", 22)
        self.btn_collapse.setFixedSize(config.TB_BTN, 28)
        self.btn_collapse.clicked.connect(self._toggle_collapse)
        root.addWidget(self.btn_collapse, 0, Qt.AlignHCenter)

    # --- state --------------------------------------------------------------
    def set_draw_active(self, active: bool) -> None:
        self.btn_draw.setChecked(active)

    def set_whiteboard_active(self, active: bool) -> None:
        self.btn_board.setChecked(active)

    def _toggle_collapse(self) -> None:
        self.set_collapsed(not self._collapsed)
        self.collapseToggled.emit(self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.body.setVisible(not collapsed)
        self.btn_collapse.set_icon_name("chev-down" if collapsed else "chev-up")
        self.btn_collapse.setToolTip("Mở rộng" if collapsed else "Thu nhỏ")
        # let the layout shrink to fit
        self.adjustSize()

    def is_collapsed(self) -> bool:
        return self._collapsed
