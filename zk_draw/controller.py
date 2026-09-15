"""Application controller: wires the IPEVO-style toolbar, flyout panel and canvas windows."""

from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config, icons
from .toolbar import MainToolbar
from .tools_panel import ToolFlyoutPanel
from .windows import CanvasWindow

GAP = 8  # px between the toolbar and the flyout panel


class Controller:
    """Owns every window and keeps them in sync."""

    def __init__(self, app: QApplication):
        self.app = app
        self.mode: str = "screen"             # "screen" | "whiteboard"

        # Separate stroke histories for screen vs whiteboard
        self._screen_strokes: list[dict] = []
        self._screen_redo: list[dict] = []
        self._wb_strokes: list[dict] = []
        self._wb_redo: list[dict] = []

        # windows -----------------------------------------------------------
        self.toolbar = MainToolbar()
        self.panel = ToolFlyoutPanel()
        self.screen_win = CanvasWindow("screen")
        self.screen_win.set_chrome_checker(self._is_point_in_chrome)

        # Set the ZK logo as window icon (shows in taskbar)
        self.screen_win.setWindowIcon(QIcon(icons.app_icon(64)))

        self._wire()
        self._install_shortcuts()
        self._build_tray()
        self._place_initial()

    # --- setup --------------------------------------------------------------
    def _wire(self) -> None:
        tb = self.toolbar
        tb.modeChanged.connect(self._on_mode_changed)
        tb.toolChanged.connect(self._on_tool_changed)
        tb.togglePanel.connect(self._on_toggle_panel)
        tb.undoRequested.connect(self._on_undo)
        tb.redoRequested.connect(self._on_redo)
        tb.clearRequested.connect(self._on_clear)
        tb.snapshotRequested.connect(self._on_snapshot)
        tb.collapseToggled.connect(self._on_collapse)
        tb.moved.connect(self._on_toolbar_moved)
        tb.quitRequested.connect(self.quit)

        p = self.panel
        p.colorChanged.connect(self._on_color)
        p.penWidthChanged.connect(self._on_pen_width)
        p.eraserWidthChanged.connect(self._on_eraser_width)
        p.closeRequested.connect(self._hide_panel)

        self.screen_win.historyChanged.connect(self.toolbar.set_history)
        self.screen_win.escapePressed.connect(self._on_escape)
        self.screen_win.interacted.connect(self._raise_ui)

    def _install_shortcuts(self) -> None:
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
        self.tray = QSystemTrayIcon(QIcon(icons.app_icon(64)))
        self.tray.setToolTip(config.APP_NAME)
        menu = QMenu()
        menu.addAction("Vẽ lên màn hình", lambda: self._switch_mode("screen"))
        menu.addAction("Bảng trắng", lambda: self._switch_mode("whiteboard"))
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
        x = screen.left() + 30
        y = screen.top() + 100
        self.toolbar.move(x, y)
        self.toolbar.show()

        # Initialize canvas & tool state (screen mode, pen tool)
        self._activate_pen()
        self.screen_win.show_overlay()
        self.panel.set_tool("pen")
        self.panel.show()
        self._reposition_panel()
        self._bring_ui_to_front()

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
            pass
        elif tb.left() - GAP - w >= screen.left():
            x = tb.left() - GAP - w
        else:
            x = tb.left()
            y = tb.bottom() + GAP

        x = max(screen.left() + 4, min(x, screen.right() - w - 4))
        y = max(screen.top() + 4, min(y, screen.bottom() - h - 4))
        self.panel.move(int(x), int(y))
        self._update_canvas_shape()

    def _is_point_in_chrome(self, gpos: QPoint) -> bool:
        if self.toolbar.frameGeometry().contains(gpos):
            return True
        if self.panel.isVisible() and self.panel.frameGeometry().contains(gpos):
            return True
        return False

    def _update_canvas_shape(self) -> None:
        if not self.screen_win.isVisible():
            return
        if QGuiApplication.platformName() != "xcb":
            return
        from . import native_x11

        if self.screen_win.is_click_through():
            native_x11.update_canvas_input_shape(int(self.screen_win.winId()), True)
        else:
            holes = []
            tb = self.toolbar.frameGeometry()
            holes.append((tb.x(), tb.y(), tb.width(), tb.height()))
            if self.panel.isVisible():
                p = self.panel.frameGeometry()
                holes.append((p.x(), p.y(), p.width(), p.height()))
            native_x11.update_canvas_input_shape(int(self.screen_win.winId()), False, holes)

    def _raise_ui(self) -> None:
        self.screen_win.raise_()
        if self.screen_win.isVisible() and QGuiApplication.platformName() == "xcb":
            from . import native_x11
            # Re-assert always-on-top in case another app stole it
            native_x11.set_window_above(int(self.screen_win.winId()), not self.screen_win.is_whiteboard_active())
            above = []
            if self.panel.isVisible():
                above.append(int(self.panel.winId()))
            above.append(int(self.toolbar.winId()))
            native_x11.restack_above(above, int(self.screen_win.winId()))

        self.toolbar.raise_()
        if self.panel.isVisible():
            self.panel.raise_()
        self._update_canvas_shape()

    def _bring_ui_to_front(self) -> None:
        self._raise_ui()
        self.toolbar.activateWindow()
        QTimer.singleShot(0, self._raise_ui)

    # --- helper: activate pen in current mode --------------------------------
    def _activate_pen(self) -> None:
        """Set canvas to pen tool in the current mode."""
        win = self.screen_win
        if win.is_click_through():
            win.set_click_through(False)
        win.canvas.set_drawing_enabled(True)
        win.canvas.set_tool("pen")
        win.canvas.set_pen_width(self.panel.pen_width())
        win.canvas.set_color(self.panel.color())
        win.canvas.set_translucent(False)

    # --- MODE SWITCHING (the core logic) ------------------------------------
    def _switch_mode(self, new_mode: str) -> None:
        """Switch between screen and whiteboard, saving/restoring strokes."""
        canvas = self.screen_win.canvas

        # Save current mode's strokes
        old_strokes, old_redo = canvas.save_strokes()
        if self.mode == "screen":
            self._screen_strokes = old_strokes
            self._screen_redo = old_redo
        else:
            self._wb_strokes = old_strokes
            self._wb_redo = old_redo

        # Switch
        self.mode = new_mode
        is_wb = (new_mode == "whiteboard")
        self.screen_win.set_whiteboard_active(is_wb)

        # Restore new mode's strokes
        if is_wb:
            canvas.restore_strokes(self._wb_strokes, self._wb_redo)
        else:
            canvas.restore_strokes(self._screen_strokes, self._screen_redo)

        # Activate pen in new mode and show panel
        self._activate_pen()
        self.panel.set_tool("pen")
        self.panel.show()
        self._reposition_panel()
        self._bring_ui_to_front()

    def _on_mode_changed(self, mode: str) -> None:
        """Toolbar emits this when the user clicks a different mode button."""
        self._switch_mode(mode)

    def _on_toggle_panel(self) -> None:
        """Toolbar emits this when the user clicks the already-active mode button."""
        self._activate_pen()
        self.panel.set_tool("pen")
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.panel.show()
            self._reposition_panel()
        self._raise_ui()

    # --- TOOL SWITCHING (pen / eraser / pointer within current mode) ---------
    def _on_tool_changed(self, tool: str) -> None:
        """Toolbar emits this when the user clicks a sub-tool button."""
        win = self.screen_win
        if tool == "pointer":
            win.canvas.set_drawing_enabled(False)
            win.set_click_through(True)
            self.panel.hide()
        elif tool == "eraser":
            if win.is_click_through():
                win.set_click_through(False)
            win.canvas.set_drawing_enabled(True)
            win.canvas.set_tool("eraser")
            win.canvas.set_eraser_width(self.panel.eraser_width())
            win.canvas.set_translucent(False)
            self.panel.set_tool("eraser")
            self.panel.show()
            self._reposition_panel()
        elif tool == "pen":
            self._activate_pen()
            self.panel.set_tool("pen")
            self.panel.show()
            self._reposition_panel()

        self._raise_ui()

    def _on_color(self, color: QColor) -> None:
        self.screen_win.canvas.set_color(color)
        self.toolbar.set_pen_color(color)

    def _on_pen_width(self, w: int) -> None:
        self.screen_win.canvas.set_pen_width(w)

    def _on_eraser_width(self, w: int) -> None:
        self.screen_win.canvas.set_eraser_width(w)

    def _on_clear(self) -> None:
        self.screen_win.canvas.clear()

    def _on_undo(self) -> None:
        self.screen_win.canvas.undo()

    def _on_redo(self) -> None:
        self.screen_win.canvas.redo()

    def _on_snapshot(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        pix = screen.grabWindow(0)
        pics_dir = os.path.expanduser("~/Pictures")
        if not os.path.isdir(pics_dir):
            pics_dir = os.path.expanduser("~")
        filename = f"ZK_Draw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(pics_dir, filename)
        pix.save(path, "PNG")
        QGuiApplication.clipboard().setPixmap(pix)
        if self.tray is not None:
            self.tray.showMessage("Đã chụp màn hình", f"Đã lưu vào {path}",
                                  QSystemTrayIcon.Information, 3000)

    def _on_escape(self) -> None:
        """Escape → switch to pointer mode."""
        self.toolbar._on_pointer_clicked()

    # --- collapse -----------------------------------------------------------
    def _on_toolbar_moved(self) -> None:
        self._reposition_panel()
        self._update_canvas_shape()

    def _hide_panel(self) -> None:
        self.panel.hide()
        self._update_canvas_shape()

    def _on_collapse(self, collapsed: bool) -> None:
        if collapsed:
            self.panel.hide()
        self._reposition_panel()
        self._update_canvas_shape()

    def _show_toolbar(self) -> None:
        if self.toolbar.is_collapsed():
            self.toolbar.set_collapsed(False)
        self.toolbar.show()
        self._ensure_toolbar_on_screen()
        self.toolbar.raise_()
        self.toolbar.activateWindow()

    def _ensure_toolbar_on_screen(self) -> None:
        tb = self.toolbar.frameGeometry()
        screens = QGuiApplication.screens()
        if any(s.availableGeometry().intersects(tb) for s in screens):
            return
        area = QGuiApplication.primaryScreen().availableGeometry()
        self.toolbar.move(area.left() + 30, area.top() + 100)

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._show_toolbar()

    # --- lifecycle ----------------------------------------------------------
    def quit(self) -> None:
        if self.tray is not None:
            self.tray.hide()
        self.app.quit()
