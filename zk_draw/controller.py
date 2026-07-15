"""Application controller: wires the toolbar, tools panel and canvas windows."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config, icons
from .toolbar import MainToolbar
from .tools_panel import ToolsPanel
from .windows import CanvasWindow

GAP = 10  # px between the toolbar and the tools panel


class Controller:
    """Owns every window and keeps them in sync."""

    def __init__(self, app: QApplication):
        self.app = app
        self.mode: str | None = None          # None | "screen" | "whiteboard"

        # windows -----------------------------------------------------------
        self.toolbar = MainToolbar()
        self.panel = ToolsPanel()
        self.screen_win = CanvasWindow("screen")
        self.board_win = CanvasWindow("whiteboard")
        self.panel.hide()

        self._wire()
        self._install_shortcuts()
        self._build_tray()
        self._place_initial()

    # --- setup --------------------------------------------------------------
    def _wire(self) -> None:
        tb = self.toolbar
        tb.drawRequested.connect(self._on_draw_clicked)
        tb.whiteboardRequested.connect(self._on_board_clicked)
        tb.collapseToggled.connect(self._on_collapse)
        tb.moved.connect(self._reposition_panel)
        tb.quitRequested.connect(self.quit)

        p = self.panel
        p.modeChanged.connect(self._on_mode_changed)
        p.colorChanged.connect(self._on_color)
        p.penWidthChanged.connect(self._on_pen_width)
        p.eraserWidthChanged.connect(self._on_eraser_width)
        p.clearRequested.connect(self._on_clear)
        p.undoRequested.connect(self._on_undo)
        p.redoRequested.connect(self._on_redo)

        for win in (self.screen_win, self.board_win):
            win.historyChanged.connect(self.panel.set_history)
            win.escapePressed.connect(self._on_escape)

    def _install_shortcuts(self) -> None:
        # One application-wide set, routed to whichever canvas is active. This
        # works no matter which of our windows currently holds keyboard focus
        # (overlay, whiteboard, toolbar or tools panel).
        self._shortcut("Ctrl+Z", self._on_undo)
        self._shortcut("Ctrl+Y", self._on_redo)
        self._shortcut("Ctrl+Shift+Z", self._on_redo)
        self._shortcut("Delete", self._on_clear)
        self._shortcut("Escape", self._on_escape)

    def _shortcut(self, seq: str, slot) -> None:
        sc = QShortcut(QKeySequence(seq), self.toolbar)
        sc.setContext(Qt.ApplicationShortcut)
        sc.activated.connect(slot)

    def _build_tray(self) -> None:
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(icons.icon("pen", 32, config.ACCENT))
        self.tray.setToolTip(config.APP_NAME)
        menu = QMenu()
        menu.addAction("Vẽ lên màn hình", self._on_draw_clicked)
        menu.addAction("Bảng trắng", self._on_board_clicked)
        menu.addSeparator()
        menu.addAction("Hiện thanh công cụ", self._show_toolbar)
        menu.addSeparator()
        menu.addAction("Thoát", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _place_initial(self) -> None:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.toolbar.adjustSize()
        x = screen.left() + 40
        y = screen.top() + 120
        self.toolbar.move(x, y)
        self.toolbar.show()
        self._reposition_panel()

    # --- window layout ------------------------------------------------------
    def _reposition_panel(self) -> None:
        if not self.panel.isVisible():
            return
        tb = self.toolbar.frameGeometry()
        self.panel.adjustSize()
        w = self.panel.width()
        h = self.panel.height()
        screen = QGuiApplication.primaryScreen().availableGeometry()

        x = tb.right() + GAP
        y = tb.top()
        if x + w <= screen.right():
            pass                                   # fits to the right
        elif tb.left() - GAP - w >= screen.left():
            x = tb.left() - GAP - w                # fits to the left
        else:
            # not enough room either side -> drop it below the toolbar
            x = tb.left()
            y = tb.bottom() + GAP

        x = max(screen.left() + 4, min(x, screen.right() - w - 4))
        y = max(screen.top() + 4, min(y, screen.bottom() - h - 4))
        self.panel.move(int(x), int(y))

    def _raise_ui(self) -> None:
        """Keep the interactive chrome above the full-screen canvas."""
        if self.panel.isVisible():
            self.panel.raise_()
        self.toolbar.raise_()

    # --- main actions -------------------------------------------------------
    def _active_win(self) -> CanvasWindow | None:
        if self.mode == "screen":
            return self.screen_win
        if self.mode == "whiteboard":
            return self.board_win
        return None

    def _on_draw_clicked(self) -> None:
        self._activate("screen" if self.mode != "screen" else None)

    def _on_board_clicked(self) -> None:
        self._activate("whiteboard" if self.mode != "whiteboard" else None)

    def _activate(self, mode: str | None) -> None:
        # tear down the previous mode
        if self.mode == "screen" and mode != "screen":
            self.screen_win.hide()
        if self.mode == "whiteboard" and mode != "whiteboard":
            self.board_win.hide()

        self.mode = mode
        self.toolbar.set_draw_active(mode == "screen")
        self.toolbar.set_whiteboard_active(mode == "whiteboard")

        if mode is None:
            self.panel.hide()
            return

        win = self._active_win()
        # start every session with the pen active
        self.panel.set_mode("pen")
        self._apply_mode_to_canvas(win, "pen")
        win.show_overlay()
        self.panel.show()
        # reflect this canvas's own undo/redo availability
        self.panel.set_history(win.canvas.can_undo(), win.canvas.can_redo())
        self._reposition_panel()
        self._raise_ui()
        win.canvas.setFocus()

    # --- tools panel handlers ----------------------------------------------
    def _on_mode_changed(self, mode: str) -> None:
        win = self._active_win()
        if win is None:
            return
        self._apply_mode_to_canvas(win, mode)
        self._raise_ui()

    def _apply_mode_to_canvas(self, win: CanvasWindow, mode: str) -> None:
        if mode == "none":
            win.canvas.set_drawing_enabled(False)
            if win.mode == "screen":
                win.set_click_through(True)
                self._raise_ui()
        else:  # pen or eraser
            if win.mode == "screen" and win.is_click_through():
                win.set_click_through(False)
                self._raise_ui()
            win.canvas.set_drawing_enabled(True)
            win.canvas.set_tool(mode)
            win.canvas.setFocus()

    def _on_color(self, color) -> None:
        win = self._active_win()
        if win:
            win.canvas.set_color(color)

    def _on_pen_width(self, w: int) -> None:
        win = self._active_win()
        if win:
            win.canvas.set_pen_width(w)

    def _on_eraser_width(self, w: int) -> None:
        win = self._active_win()
        if win:
            win.canvas.set_eraser_width(w)

    def _on_clear(self) -> None:
        win = self._active_win()
        if win:
            win.canvas.clear()

    def _on_undo(self) -> None:
        win = self._active_win()
        if win:
            win.canvas.undo()

    def _on_redo(self) -> None:
        win = self._active_win()
        if win:
            win.canvas.redo()

    def _on_escape(self) -> None:
        # Esc -> "use the computer normally"
        if self.mode is not None:
            self.panel.set_mode("none")

    # --- collapse -----------------------------------------------------------
    def _on_collapse(self, collapsed: bool) -> None:
        if collapsed:
            # minimise everything: leave only the compact handle
            self._activate(None)
        self._reposition_panel()

    def _show_toolbar(self) -> None:
        if self.toolbar.is_collapsed():
            self.toolbar.set_collapsed(False)
        self.toolbar.show()
        self._ensure_toolbar_on_screen()
        self.toolbar.raise_()
        self.toolbar.activateWindow()

    def _ensure_toolbar_on_screen(self) -> None:
        """Pull the toolbar back into view if it ended up off-screen."""
        tb = self.toolbar.frameGeometry()
        screens = QGuiApplication.screens()
        if any(s.availableGeometry().intersects(tb) for s in screens):
            return
        area = QGuiApplication.primaryScreen().availableGeometry()
        self.toolbar.move(area.left() + 40, area.top() + 120)

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._show_toolbar()

    # --- lifecycle ----------------------------------------------------------
    def quit(self) -> None:
        if self.tray is not None:
            self.tray.hide()
        self.app.quit()
