"""The drawing surface.

The canvas keeps a list of *strokes* (vector data) as the single source of
truth so undo / redo / clear are all exact and cheap.  For speed the current
committed image is cached in a QImage; while a stroke is in progress it is
painted incrementally onto that cache.  A full replay only happens on
undo / redo / clear / resize, which are rare.

Stroke schema (plain dict)::

    {"tool": "pen" | "eraser" | "clear",
     "color": QColor,      # pen only
     "width": int,         # pen / eraser
     "points": [QPointF]}  # pen / eraser
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QTabletEvent,
)
from PySide6.QtWidgets import QWidget

from . import config


class Canvas(QWidget):
    """A transparent drawing widget. Put it on a translucent or white window."""

    # Emitted whenever the undo / redo availability may have changed.
    historyChanged = Signal(bool, bool)  # (can_undo, can_redo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StaticContents, True)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._image = self._make_image(1, 1)

        self._strokes: list[dict] = []
        self._redo: list[dict] = []

        self._tool = "pen"
        self._color = QColor(config.DEFAULT_COLOR)
        self._pen_width = config.DEFAULT_PEN_SIZE
        self._eraser_width = config.DEFAULT_ERASER_SIZE

        self._drawing = False
        self._enabled = True
        self._active: dict | None = None
        self._last: QPointF | None = None

        self._apply_cursor()

    # --- public API ---------------------------------------------------------
    def set_drawing_enabled(self, enabled: bool) -> None:
        """When disabled the canvas ignores input (arrow cursor)."""
        self._enabled = enabled
        if not enabled and self._drawing:
            self._finish()
        self._apply_cursor()

    def is_drawing_enabled(self) -> bool:
        return self._enabled

    def set_tool(self, tool: str) -> None:
        if tool not in ("pen", "eraser"):
            return
        self._tool = tool
        self._apply_cursor()

    def tool(self) -> str:
        return self._tool

    def set_color(self, color) -> None:
        self._color = QColor(color)
        if self._tool == "eraser":
            # picking a colour implies switching back to the pen
            self.set_tool("pen")

    def color(self) -> QColor:
        return QColor(self._color)

    def set_pen_width(self, w: int) -> None:
        self._pen_width = int(w)
        self._apply_cursor()

    def set_eraser_width(self, w: int) -> None:
        self._eraser_width = int(w)
        self._apply_cursor()

    def current_width(self) -> int:
        return self._pen_width if self._tool == "pen" else self._eraser_width

    def can_undo(self) -> bool:
        return bool(self._strokes)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> None:
        if not self._strokes:
            return
        self._redo.append(self._strokes.pop())
        self._rebuild()
        self._emit_history()

    def redo(self) -> None:
        if not self._redo:
            return
        self._strokes.append(self._redo.pop())
        self._rebuild()
        self._emit_history()

    def clear(self) -> None:
        # Clear is undoable: it is recorded as a stroke marker. Skip when
        # there is nothing to clear (empty, or already ends with a clear).
        if not self._strokes or self._strokes[-1].get("tool") == "clear":
            return
        self._strokes.append({"tool": "clear"})
        self._redo.clear()
        self._image.fill(Qt.transparent)
        self.update()
        self._emit_history()

    def is_empty(self) -> bool:
        return not self._strokes

    # --- geometry -----------------------------------------------------------
    def _make_image(self, w: int, h: int) -> QImage:
        """Allocate the backing image at physical resolution so ink stays
        crisp on HiDPI / fractionally-scaled displays."""
        dpr = self.devicePixelRatioF()
        img = QImage(max(1, round(w * dpr)), max(1, round(h * dpr)),
                     QImage.Format_ARGB32_Premultiplied)
        img.setDevicePixelRatio(dpr)
        img.fill(Qt.transparent)
        return img

    def showEvent(self, event) -> None:
        # If the real screen's devicePixelRatio differs from what the image
        # was allocated with (window created before it knew its screen),
        # reallocate at the correct physical resolution.
        if abs(self._image.devicePixelRatio() - self.devicePixelRatioF()) > 0.01:
            self._image = self._make_image(self.width(), self.height())
            self._rebuild()
        super().showEvent(event)

    def resizeEvent(self, event) -> None:
        self._image = self._make_image(self.width(), self.height())
        self._rebuild()
        # keep the portion of an in-progress stroke drawn before the resize
        if self._active is not None:
            p = QPainter(self._image)
            p.setRenderHint(QPainter.Antialiasing, True)
            self._paint_stroke(p, self._active)
            p.end()
        super().resizeEvent(event)

    # --- painting -----------------------------------------------------------
    def paintEvent(self, event) -> None:
        # The image carries a devicePixelRatio, so drawing it at logical (0,0)
        # renders it at the widget's size while keeping physical resolution.
        p = QPainter(self)
        p.setClipRect(event.rect())
        p.drawImage(0, 0, self._image)
        p.end()

    # --- mouse --------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._enabled or event.button() != Qt.LeftButton:
            return
        self._begin(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drawing and (event.buttons() & Qt.LeftButton):
            self._extend(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._drawing:
            self._extend(event.position())
            self._finish()

    # Graphics-tablet / stylus support (Wacom, IPEVO doc-cam pens, etc.)
    def tabletEvent(self, event: QTabletEvent) -> None:
        if not self._enabled:
            event.ignore()
            return
        etype = event.type()
        pos = event.position()
        if etype == QTabletEvent.TabletPress:
            self._begin(pos)
        elif etype == QTabletEvent.TabletMove and self._drawing:
            self._extend(pos)
        elif etype == QTabletEvent.TabletRelease and self._drawing:
            self._extend(pos)
            self._finish()
        event.accept()

    # --- stroke lifecycle ---------------------------------------------------
    def _begin(self, pos: QPointF) -> None:
        self._drawing = True
        width = self._pen_width if self._tool == "pen" else self._eraser_width
        self._active = {
            "tool": self._tool,
            "color": QColor(self._color),
            "width": int(width),
            "points": [QPointF(pos)],
        }
        self._last = QPointF(pos)
        # a single click should leave a dot
        self._paint_segment(self._active, pos, pos)
        self.update()

    def _extend(self, pos: QPointF) -> None:
        if not self._active or self._last is None:
            return
        self._active["points"].append(QPointF(pos))
        self._paint_segment(self._active, self._last, pos)
        # repaint the affected band only
        w = self._active["width"]
        x1, y1 = self._last.x(), self._last.y()
        x2, y2 = pos.x(), pos.y()
        left = min(x1, x2) - w
        top = min(y1, y2) - w
        self.update(int(left), int(top), int(abs(x2 - x1) + 2 * w),
                    int(abs(y2 - y1) + 2 * w))
        self._last = QPointF(pos)

    def _finish(self) -> None:
        if self._active is not None:
            self._strokes.append(self._active)
            self._redo.clear()
            self._emit_history()
        self._active = None
        self._drawing = False
        self._last = None

    # --- rendering helpers --------------------------------------------------
    def _paint_segment(self, stroke: dict, a: QPointF, b: QPointF) -> None:
        p = QPainter(self._image)
        p.setRenderHint(QPainter.Antialiasing, True)
        self._configure(p, stroke)
        if a == b:
            # dot: fill only (no stroking pen) so the live radius matches replay
            r = max(0.5, stroke["width"] / 2.0)
            p.setPen(Qt.NoPen)
            p.drawEllipse(a, r, r)
        else:
            p.drawLine(a, b)
        p.end()

    def _configure(self, p: QPainter, stroke: dict) -> None:
        if stroke["tool"] == "eraser":
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.black, stroke["width"])
            brush_color = Qt.black
        else:
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(stroke["color"], stroke["width"])
            brush_color = stroke["color"]
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(brush_color)

    def _paint_stroke(self, p: QPainter, stroke: dict) -> None:
        pts = stroke["points"]
        if not pts:
            return
        self._configure(p, stroke)
        if len(pts) == 1:
            r = max(0.5, stroke["width"] / 2.0)
            p.setPen(Qt.NoPen)
            p.drawEllipse(pts[0], r, r)
            return
        path = QPainterPath(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def _rebuild(self) -> None:
        """Replay committed strokes onto a fresh image.

        Strokes before the last ``clear`` marker are invisible (the clear
        wipes them), so rendering starts just after that marker — the marker
        itself stays in the list so the clear remains undoable.
        """
        self._image.fill(Qt.transparent)
        start = 0
        for i in range(len(self._strokes) - 1, -1, -1):
            if self._strokes[i].get("tool") == "clear":
                start = i + 1
                break
        p = QPainter(self._image)
        p.setRenderHint(QPainter.Antialiasing, True)
        for stroke in self._strokes[start:]:
            if stroke.get("tool") == "clear":
                continue
            self._paint_stroke(p, stroke)
        p.end()
        self.update()

    # --- misc ---------------------------------------------------------------
    def _emit_history(self) -> None:
        self.historyChanged.emit(self.can_undo(), self.can_redo())

    def _apply_cursor(self) -> None:
        if not self._enabled:
            self.setCursor(Qt.ArrowCursor)
            return
        from .cursors import make_tool_cursor
        self.setCursor(make_tool_cursor(self._tool, self.current_width(),
                                        self._color))
