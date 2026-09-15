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
    # emitted when the user starts interacting (so the chrome can re-raise)
    interacted = Signal()

    def __init__(self, mode: str = "screen", parent=None):
        super().__init__(parent)
        self.mode = mode
        self._click_through = False
        self._whiteboard_active = False

        flags = (Qt.FramelessWindowHint
                 | Qt.Tool
                 | Qt.NoDropShadowWindowHint)
        # Only the transparent screen overlay must float above other apps.
        # The opaque whiteboard is a normal-layer window so the toolbar/tools
        # panel (which ARE always-on-top) reliably stay visible above it.
        if mode == "screen":
            flags |= Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint
        self.setWindowFlags(flags)
        self.setWindowTitle(f"{config.APP_NAME} - {mode}")

        if mode == "screen":
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        else:
            self.setAutoFillBackground(True)

        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._chrome_checker = None

        self.canvas = Canvas(self)
        self.canvas.historyChanged.connect(self.historyChanged)
        self.canvas.interacted.connect(self.interacted)

        # Pre-render dot grid pattern for whiteboard
        spacing = getattr(config, "WHITEBOARD_DOT_SPACING", 24)
        from PySide6.QtGui import QPixmap, QBrush
        dot_pm = QPixmap(spacing, spacing)
        dot_pm.fill(Qt.transparent)
        dp = QPainter(dot_pm)
        dp.setRenderHint(QPainter.Antialiasing, True)
        dp.setPen(Qt.NoPen)
        dp.setBrush(QColor(getattr(config, "WHITEBOARD_DOT", "#CBD5E1")))
        dp.drawEllipse(spacing // 2 - 1, spacing // 2 - 1, 2, 2)
        dp.end()
        self._dot_brush = QBrush(dot_pm)

        self._place_full_screen()

    def set_chrome_checker(self, checker) -> None:
        self._chrome_checker = checker

    def is_point_in_chrome(self, gpos) -> bool:
        if self._chrome_checker:
            return self._chrome_checker(gpos)
        return False

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
    def set_whiteboard_active(self, active: bool) -> None:
        """Display white backdrop beneath the live annotation layer."""
        self._whiteboard_active = bool(active)
        if self.isVisible() and QGuiApplication.platformName() == "xcb":
            from . import native_x11
            # When whiteboard is active, canvas is solid opaque white: keep it in
            # the Normal window layer so the toolbar/panel (Above layer) never get occluded.
            native_x11.set_window_above(int(self.winId()), not self._whiteboard_active)
        self.update()

    def is_whiteboard_active(self) -> bool:
        return self._whiteboard_active

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        if self._whiteboard_active or self.mode == "whiteboard":
            p.fillRect(self.rect(), QColor(config.WHITEBOARD_BG))
            p.fillRect(self.rect(), self._dot_brush)
        elif self.mode == "screen":
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(self.rect(), Qt.transparent)
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
        if QGuiApplication.platformName() == "xcb":
            from . import native_x11
            native_x11.set_window_above(int(self.winId()), not self._whiteboard_active)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.escapePressed.emit()
        else:
            super().keyPressEvent(event)
