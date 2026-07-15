"""Full-screen canvas windows: transparent screen overlay and whiteboard."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from . import config
from .canvas import Canvas
from .native_x11 import set_input_passthrough


class CanvasWindow(QWidget):
    """A frameless, always-on-top window covering the whole virtual desktop.

    mode = "screen"      -> translucent background (annotate the live desktop)
    mode = "whiteboard"  -> solid white background
    """

    # forwarded from the inner canvas
    historyChanged = Signal(bool, bool)
    # emitted when the user presses Esc while drawing
    escapePressed = Signal()

    def __init__(self, mode: str = "screen", parent=None):
        super().__init__(parent)
        self.mode = mode
        self._click_through = False

        flags = (Qt.FramelessWindowHint
                 | Qt.WindowStaysOnTopHint
                 | Qt.Tool
                 | Qt.NoDropShadowWindowHint)
        self.setWindowFlags(flags)
        self.setWindowTitle(f"{config.APP_NAME} - {mode}")

        if mode == "screen":
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        else:
            self.setAutoFillBackground(True)

        self.canvas = Canvas(self)
        self.canvas.historyChanged.connect(self.historyChanged)

        self._place_full_screen()

    # --- geometry -----------------------------------------------------------
    def _place_full_screen(self) -> None:
        geo = QGuiApplication.primaryScreen().geometry()
        # cover the union of every screen so multi-monitor works too
        for scr in QGuiApplication.screens():
            geo = geo.united(scr.geometry())
        self.setGeometry(geo)
        self.canvas.setGeometry(0, 0, geo.width(), geo.height())

    def resizeEvent(self, event) -> None:
        self.canvas.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    # --- background ---------------------------------------------------------
    def paintEvent(self, event) -> None:
        if self.mode == "whiteboard":
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(config.WHITEBOARD_BG))
            p.end()

    # --- click-through (pass input to the desktop below) --------------------
    def set_click_through(self, enabled: bool) -> None:
        """When enabled the overlay stays visible but no longer eats mouse
        events, so the user can operate the computer normally.

        Prefers the native XShape path (no flash); falls back to toggling
        Qt.WindowTransparentForInput (re-creates the window) if unavailable.
        """
        if enabled == self._click_through and self.isVisible():
            return
        self._click_through = enabled

        native_ok = False
        # winId() is only a real X11 Window under the xcb platform plugin.
        # Under the Wayland plugin it is a Wayland surface handle, so the
        # native path must not run there (it would target a garbage XID).
        if self.isVisible() and QGuiApplication.platformName() == "xcb":
            native_ok = set_input_passthrough(int(self.winId()), enabled)

        if not native_ok:
            self.setWindowFlag(Qt.WindowTransparentForInput, enabled)
            # setWindowFlag re-creates the native window -> re-show to apply.
            self.show()
        elif not enabled:
            # returned to interactive: make sure we can take keyboard focus
            self.activateWindow()

    def is_click_through(self) -> bool:
        return self._click_through

    # --- lifecycle ----------------------------------------------------------
    def show_overlay(self) -> None:
        self._place_full_screen()
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.escapePressed.emit()
        else:
            super().keyPressEvent(event)
