"""Vector icons drawn with QPainter so the app ships with no image assets.

Every icon is rendered crisply at the requested size (device-pixel aware) and
returned as a QIcon or QPixmap.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

from . import config


def _new_pixmap(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.setDevicePixelRatio(1.0)
    pm.fill(Qt.transparent)
    return pm


def _painter(pm: QPixmap) -> QPainter:
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    return p


def _stroke_pen(color: QColor, w: float) -> QPen:
    pen = QPen(color, w)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


# --- individual glyphs (drawn on a 0..S box) --------------------------------

def _draw_pen(p: QPainter, s: float, c: QColor) -> None:
    # A pen/marker pointing to the bottom-left.
    p.save()
    body = QPolygonF([
        QPointF(0.66 * s, 0.14 * s),
        QPointF(0.86 * s, 0.34 * s),
        QPointF(0.40 * s, 0.80 * s),
        QPointF(0.20 * s, 0.60 * s),
    ])
    p.setPen(_stroke_pen(c, max(1.4, s * 0.055)))
    p.setBrush(QBrush(c))
    # nib triangle
    nib = QPolygonF([
        QPointF(0.20 * s, 0.60 * s),
        QPointF(0.40 * s, 0.80 * s),
        QPointF(0.15 * s, 0.85 * s),
    ])
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(body)
    p.setBrush(QBrush(c))
    p.drawPolygon(nib)
    # cap line near top
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(0.60 * s, 0.28 * s), QPointF(0.72 * s, 0.40 * s))
    p.restore()


def _draw_whiteboard(p: QPainter, s: float, c: QColor) -> None:
    p.setPen(_stroke_pen(c, max(1.4, s * 0.06)))
    p.setBrush(Qt.NoBrush)
    r = QRectF(0.14 * s, 0.20 * s, 0.72 * s, 0.52 * s)
    p.drawRoundedRect(r, s * 0.05, s * 0.05)
    # stand
    p.drawLine(QPointF(0.5 * s, 0.72 * s), QPointF(0.5 * s, 0.84 * s))
    p.drawLine(QPointF(0.36 * s, 0.86 * s), QPointF(0.64 * s, 0.86 * s))
    # a scribble line inside
    path = QPainterPath(QPointF(0.26 * s, 0.52 * s))
    path.cubicTo(QPointF(0.38 * s, 0.34 * s),
                 QPointF(0.52 * s, 0.60 * s),
                 QPointF(0.72 * s, 0.38 * s))
    thin = _stroke_pen(c, max(1.2, s * 0.045))
    p.setPen(thin)
    p.drawPath(path)


def _draw_eraser(p: QPainter, s: float, c: QColor) -> None:
    p.save()
    p.translate(0.5 * s, 0.5 * s)
    p.rotate(-40)
    p.translate(-0.5 * s, -0.5 * s)
    p.setPen(_stroke_pen(c, max(1.4, s * 0.06)))
    p.setBrush(Qt.NoBrush)
    body = QRectF(0.24 * s, 0.30 * s, 0.52 * s, 0.40 * s)
    p.drawRoundedRect(body, s * 0.05, s * 0.05)
    # split line (rubber tip)
    y = 0.55 * s
    p.drawLine(QPointF(0.24 * s, y), QPointF(0.76 * s, y))
    p.restore()


def _draw_trash(p: QPainter, s: float, c: QColor) -> None:
    p.setPen(_stroke_pen(c, max(1.4, s * 0.06)))
    p.setBrush(Qt.NoBrush)
    # lid
    p.drawLine(QPointF(0.22 * s, 0.28 * s), QPointF(0.78 * s, 0.28 * s))
    p.drawLine(QPointF(0.40 * s, 0.28 * s), QPointF(0.42 * s, 0.20 * s))
    p.drawLine(QPointF(0.42 * s, 0.20 * s), QPointF(0.58 * s, 0.20 * s))
    p.drawLine(QPointF(0.58 * s, 0.20 * s), QPointF(0.60 * s, 0.28 * s))
    # can
    can = QPainterPath(QPointF(0.28 * s, 0.30 * s))
    can.lineTo(0.32 * s, 0.80 * s)
    can.lineTo(0.68 * s, 0.80 * s)
    can.lineTo(0.72 * s, 0.30 * s)
    p.drawPath(can)
    # ribs
    for x in (0.42, 0.5, 0.58):
        p.drawLine(QPointF(x * s, 0.40 * s), QPointF(x * s, 0.70 * s))


def _draw_undo(p: QPainter, s: float, c: QColor, mirror: bool = False) -> None:
    p.save()
    if mirror:
        p.translate(s, 0)
        p.scale(-1, 1)
    p.setPen(_stroke_pen(c, max(1.7, s * 0.085)))
    p.setBrush(Qt.NoBrush)
    cx, cy, r = 0.52 * s, 0.54 * s, 0.24 * s
    rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
    start, span = -20.0, 250.0          # degrees, CCW (Qt convention)
    path = QPainterPath()
    path.arcMoveTo(rect, start)
    path.arcTo(rect, start, span)
    p.drawPath(path)
    # arrowhead at the end of the arc, aligned to the tangent
    end = math.radians(start + span)
    ex = cx + r * math.cos(end)
    ey = cy - r * math.sin(end)         # Qt y-axis points down
    tx, ty = math.sin(end), math.cos(end)   # CCW tangent (y flipped)
    nx, ny = -ty, tx
    a = 0.15 * s
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(c))
    p.drawPolygon(QPolygonF([
        QPointF(ex + tx * a, ey + ty * a),
        QPointF(ex + nx * a * 0.6, ey + ny * a * 0.6),
        QPointF(ex - nx * a * 0.6, ey - ny * a * 0.6),
    ]))
    p.restore()


def _draw_chevron(p: QPainter, s: float, c: QColor, direction: str) -> None:
    p.setPen(_stroke_pen(c, max(1.6, s * 0.09)))
    p.setBrush(Qt.NoBrush)
    cx, cy = 0.5 * s, 0.5 * s
    d = 0.16 * s
    if direction == "down":
        pts = [QPointF(cx - d, cy - d * 0.6), QPointF(cx, cy + d * 0.6),
               QPointF(cx + d, cy - d * 0.6)]
    elif direction == "up":
        pts = [QPointF(cx - d, cy + d * 0.6), QPointF(cx, cy - d * 0.6),
               QPointF(cx + d, cy + d * 0.6)]
    elif direction == "left":
        pts = [QPointF(cx + d * 0.6, cy - d), QPointF(cx - d * 0.6, cy),
               QPointF(cx + d * 0.6, cy + d)]
    else:  # right
        pts = [QPointF(cx - d * 0.6, cy - d), QPointF(cx + d * 0.6, cy),
               QPointF(cx - d * 0.6, cy + d)]
    p.drawPolyline(QPolygonF(pts))


def _draw_cursor(p: QPainter, s: float, c: QColor) -> None:
    # Classic arrow pointer -> "use computer normally".
    p.setPen(_stroke_pen(c, max(1.2, s * 0.05)))
    p.setBrush(QBrush(c))
    arrow = QPolygonF([
        QPointF(0.30 * s, 0.22 * s),
        QPointF(0.30 * s, 0.74 * s),
        QPointF(0.43 * s, 0.61 * s),
        QPointF(0.52 * s, 0.80 * s),
        QPointF(0.60 * s, 0.76 * s),
        QPointF(0.51 * s, 0.57 * s),
        QPointF(0.68 * s, 0.55 * s),
    ])
    p.drawPolygon(arrow)


def _draw_close(p: QPainter, s: float, c: QColor) -> None:
    p.setPen(_stroke_pen(c, max(1.6, s * 0.08)))
    p.drawLine(QPointF(0.32 * s, 0.32 * s), QPointF(0.68 * s, 0.68 * s))
    p.drawLine(QPointF(0.68 * s, 0.32 * s), QPointF(0.32 * s, 0.68 * s))


_GLYPHS = {
    "pen": _draw_pen,
    "whiteboard": _draw_whiteboard,
    "eraser": _draw_eraser,
    "trash": _draw_trash,
    "undo": lambda p, s, c: _draw_undo(p, s, c, mirror=False),
    "redo": lambda p, s, c: _draw_undo(p, s, c, mirror=True),
    "chev-down": lambda p, s, c: _draw_chevron(p, s, c, "down"),
    "chev-up": lambda p, s, c: _draw_chevron(p, s, c, "up"),
    "chev-left": lambda p, s, c: _draw_chevron(p, s, c, "left"),
    "chev-right": lambda p, s, c: _draw_chevron(p, s, c, "right"),
    "cursor": _draw_cursor,
    "close": _draw_close,
}


def pixmap(name: str, size: int = 24, color: str | QColor = config.ICON) -> QPixmap:
    """Render *name* as a QPixmap of *size* px in *color*."""
    c = QColor(color) if not isinstance(color, QColor) else color
    pm = _new_pixmap(size)
    p = _painter(pm)
    glyph = _GLYPHS.get(name)
    if glyph is not None:
        glyph(p, float(size), c)
    p.end()
    return pm


def icon(name: str, size: int = 24, color: str | QColor = config.ICON) -> QIcon:
    return QIcon(pixmap(name, size, color))


def app_icon(size: int = 256) -> QPixmap:
    """The application / launcher icon: rounded accent tile + white pen."""
    s = float(size)
    pm = _new_pixmap(size)
    p = _painter(pm)
    # rounded gradient-ish tile
    from PySide6.QtGui import QLinearGradient
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0.0, QColor("#3B8CFF"))
    grad.setColorAt(1.0, QColor(config.ACCENT))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    r = QRectF(s * 0.06, s * 0.06, s * 0.88, s * 0.88)
    p.drawRoundedRect(r, s * 0.22, s * 0.22)
    # white pen glyph, centred
    p.save()
    p.translate(s * 0.14, s * 0.14)
    _draw_pen(p, s * 0.72, QColor("#FFFFFF"))
    p.restore()
    p.end()
    return pm
