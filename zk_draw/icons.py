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
    # Stylus / pen matching mockup precisely: slanted 45 deg, barrel + nib + tip line
    p.save()
    p.setRenderHint(QPainter.Antialiasing, True)
    p.translate(0.5 * s, 0.5 * s)
    p.rotate(-45)
    p.translate(-0.5 * s, -0.5 * s)

    stroke = max(1.5, s * 0.07)
    p.setPen(_stroke_pen(c, stroke))
    p.setBrush(Qt.NoBrush)

    # Pen barrel (rounded top)
    body = QRectF(0.38 * s, 0.16 * s, 0.24 * s, 0.44 * s)
    p.drawRoundedRect(body, 0.06 * s, 0.06 * s)

    # Nib cone converging to point
    p.drawLine(QPointF(0.38 * s, 0.60 * s), QPointF(0.50 * s, 0.80 * s))
    p.drawLine(QPointF(0.62 * s, 0.60 * s), QPointF(0.50 * s, 0.80 * s))

    # Nib tip line
    p.drawLine(QPointF(0.42 * s, 0.68 * s), QPointF(0.58 * s, 0.68 * s))
    p.restore()


def _draw_whiteboard(p: QPainter, s: float, c: QColor) -> None:
    # Desktop monitor with stock chart zigzag line inside (matching mockup)
    p.save()
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(_stroke_pen(c, max(1.5, s * 0.065)))
    p.setBrush(Qt.NoBrush)

    # Screen
    r = QRectF(0.16 * s, 0.18 * s, 0.68 * s, 0.48 * s)
    p.drawRoundedRect(r, 0.07 * s, 0.07 * s)

    # Stand neck & base
    p.drawLine(QPointF(0.50 * s, 0.66 * s), QPointF(0.50 * s, 0.80 * s))
    p.drawLine(QPointF(0.36 * s, 0.80 * s), QPointF(0.64 * s, 0.80 * s))

    # Stock chart zigzag line inside screen
    chart = QPolygonF([
        QPointF(0.24 * s, 0.48 * s),
        QPointF(0.35 * s, 0.48 * s),
        QPointF(0.45 * s, 0.32 * s),
        QPointF(0.55 * s, 0.54 * s),
        QPointF(0.65 * s, 0.38 * s),
        QPointF(0.76 * s, 0.38 * s),
    ])
    p.drawPolyline(chart)
    p.restore()


def _draw_eraser(p: QPainter, s: float, c: QColor) -> None:
    p.save()
    p.translate(0.5 * s, 0.5 * s)
    p.rotate(-40)
    p.translate(-0.5 * s, -0.5 * s)
    p.setPen(_stroke_pen(c, max(1.5, s * 0.065)))
    p.setBrush(Qt.NoBrush)
    body = QRectF(0.24 * s, 0.30 * s, 0.52 * s, 0.40 * s)
    p.drawRoundedRect(body, s * 0.06, s * 0.06)
    # split line (rubber tip)
    y = 0.54 * s
    p.drawLine(QPointF(0.24 * s, y), QPointF(0.76 * s, y))
    p.restore()


def _draw_trash(p: QPainter, s: float, c: QColor) -> None:
    p.setPen(_stroke_pen(c, max(1.5, s * 0.065)))
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
    # Clean curved undo/redo arrow matching mockup
    p.save()
    if mirror:
        p.translate(s, 0)
        p.scale(-1, 1)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = _stroke_pen(c, max(1.6, s * 0.075))
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    # Arc sweeping over the top
    path = QPainterPath()
    path.moveTo(0.72 * s, 0.66 * s)
    path.cubicTo(0.72 * s, 0.36 * s, 0.56 * s, 0.32 * s, 0.32 * s, 0.44 * s)
    p.drawPath(path)

    # Arrowhead pointing left/down
    arrow = QPolygonF([
        QPointF(0.34 * s, 0.28 * s),
        QPointF(0.20 * s, 0.44 * s),
        QPointF(0.36 * s, 0.58 * s),
    ])
    p.drawPolyline(arrow)
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
    # Classic mouse arrow pointer — universally recognizable
    p.save()
    p.setRenderHint(QPainter.Antialiasing, True)
    stroke = max(1.4, s * 0.06)

    # Main arrow body (filled white/light with colored outline)
    arrow = QPainterPath()
    arrow.moveTo(0.22 * s, 0.14 * s)   # top-left tip
    arrow.lineTo(0.22 * s, 0.78 * s)   # straight down
    arrow.lineTo(0.38 * s, 0.64 * s)   # inner notch
    arrow.lineTo(0.56 * s, 0.86 * s)   # lower-right tail
    arrow.lineTo(0.64 * s, 0.80 * s)   # tail edge
    arrow.lineTo(0.46 * s, 0.58 * s)   # back from tail
    arrow.lineTo(0.66 * s, 0.52 * s)   # right wing
    arrow.closeSubpath()

    # Fill with white/translucent so it looks like a real cursor
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFFFFF"))
    p.drawPath(arrow)

    # Outline with the icon color
    p.setPen(_stroke_pen(c, stroke))
    p.setBrush(Qt.NoBrush)
    p.drawPath(arrow)
    p.restore()


def _draw_crosshair(p: QPainter, s: float, c: QColor) -> None:
    p.save()
    cx, cy = 0.5 * s, 0.5 * s
    r = 0.25 * s
    pen_dash = _stroke_pen(c, max(1.2, s * 0.055))
    pen_dash.setStyle(Qt.DotLine)
    p.setPen(pen_dash)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), r, r)
    pen_solid = _stroke_pen(c, max(1.4, s * 0.065))
    p.setPen(pen_solid)
    d = 0.12 * s
    p.drawLine(QPointF(cx - d, cy), QPointF(cx + d, cy))
    p.drawLine(QPointF(cx, cy - d), QPointF(cx, cy + d))
    p.restore()


def _draw_screen_pen(p: QPainter, s: float, c: QColor) -> None:
    # Live screen annotation: squiggle curve on the left, pen on the right
    p.save()
    # Left squiggle line
    path = QPainterPath(QPointF(0.18 * s, 0.30 * s))
    path.cubicTo(QPointF(0.38 * s, 0.24 * s),
                 QPointF(0.12 * s, 0.50 * s),
                 QPointF(0.34 * s, 0.62 * s))
    path.cubicTo(QPointF(0.44 * s, 0.68 * s),
                 QPointF(0.20 * s, 0.82 * s),
                 QPointF(0.38 * s, 0.78 * s))
    p.setPen(_stroke_pen(c, max(1.8, s * 0.08)))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)

    # Right pen
    p.translate(0.18 * s, -0.05 * s)
    _draw_pen(p, s * 0.82, c)
    p.restore()


def _draw_camera(p: QPainter, s: float, c: QColor) -> None:
    # Camera / snapshot icon
    p.save()
    p.setPen(_stroke_pen(c, max(1.4, s * 0.06)))
    p.setBrush(Qt.NoBrush)
    # Body
    body = QRectF(0.16 * s, 0.34 * s, 0.68 * s, 0.48 * s)
    p.drawRoundedRect(body, s * 0.08, s * 0.08)
    # Top flash / prism
    roof = QPainterPath(QPointF(0.34 * s, 0.34 * s))
    roof.lineTo(QPointF(0.40 * s, 0.22 * s))
    roof.lineTo(QPointF(0.60 * s, 0.22 * s))
    roof.lineTo(QPointF(0.66 * s, 0.34 * s))
    p.drawPath(roof)
    # Center lens
    lens_r = 0.14 * s
    p.drawEllipse(QPointF(0.50 * s, 0.58 * s), lens_r, lens_r)
    # Small dot
    p.setBrush(QBrush(c))
    p.drawEllipse(QPointF(0.70 * s, 0.42 * s), 0.035 * s, 0.035 * s)
    p.restore()


def _draw_highlighter(p: QPainter, s: float, c: QColor) -> None:
    # Highlighter / marker icon with chisel tip
    p.save()
    p.translate(0.5 * s, 0.5 * s)
    p.rotate(-45)
    p.translate(-0.5 * s, -0.5 * s)
    p.setPen(_stroke_pen(c, max(1.4, s * 0.06)))
    p.setBrush(Qt.NoBrush)
    # Barrel
    barrel = QRectF(0.36 * s, 0.30 * s, 0.28 * s, 0.46 * s)
    p.drawRoundedRect(barrel, s * 0.04, s * 0.04)
    # Chisel tip
    tip = QPolygonF([
        QPointF(0.38 * s, 0.30 * s),
        QPointF(0.44 * s, 0.16 * s),
        QPointF(0.60 * s, 0.22 * s),
        QPointF(0.56 * s, 0.30 * s),
    ])
    p.setBrush(QBrush(c))
    p.drawPolygon(tip)
    p.restore()


def _draw_rainbow(p: QPainter, s: float, c: QColor) -> None:
    # 4-quadrant rainbow preview
    p.save()
    r = QRectF(0.12 * s, 0.12 * s, 0.76 * s, 0.76 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FF3B30"))
    p.drawPie(r, 0 * 16, 90 * 16)
    p.setBrush(QColor("#FFCC00"))
    p.drawPie(r, 90 * 16, 90 * 16)
    p.setBrush(QColor("#34C759"))
    p.drawPie(r, 180 * 16, 90 * 16)
    p.setBrush(QColor("#007AFF"))
    p.drawPie(r, 270 * 16, 90 * 16)
    p.restore()


def _draw_close(p: QPainter, s: float, c: QColor) -> None:
    p.setPen(_stroke_pen(c, max(1.6, s * 0.08)))
    p.drawLine(QPointF(0.32 * s, 0.32 * s), QPointF(0.68 * s, 0.68 * s))
    p.drawLine(QPointF(0.68 * s, 0.32 * s), QPointF(0.32 * s, 0.68 * s))


_GLYPHS = {
    "pen": _draw_pen,
    "screen-pen": _draw_screen_pen,
    "whiteboard": _draw_whiteboard,
    "highlighter": _draw_highlighter,
    "camera": _draw_camera,
    "rainbow": _draw_rainbow,
    "eraser": _draw_eraser,
    "trash": _draw_trash,
    "undo": lambda p, s, c: _draw_undo(p, s, c, mirror=False),
    "redo": lambda p, s, c: _draw_undo(p, s, c, mirror=True),
    "chev-down": lambda p, s, c: _draw_chevron(p, s, c, "down"),
    "chev-up": lambda p, s, c: _draw_chevron(p, s, c, "up"),
    "chev-left": lambda p, s, c: _draw_chevron(p, s, c, "left"),
    "chev-right": lambda p, s, c: _draw_chevron(p, s, c, "right"),
    "cursor": _draw_cursor,
    "crosshair": _draw_crosshair,
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
    """The application / launcher icon: uses the custom SVG from assets."""
    import os

    # 1. Try SVG icon (best quality at any size)
    svg_path = os.path.join(config.ASSETS_DIR, "zk-draw-icon.svg")
    if os.path.exists(svg_path):
        try:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtCore import QSize as _QSize
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                pm = QPixmap(_QSize(size, size))
                pm.fill(Qt.transparent)
                p = QPainter(pm)
                renderer.render(p)
                p.end()
                return pm
        except ImportError:
            pass

    # 2. Fallback: PNG logo
    logo_path = os.path.join(config.ASSETS_DIR, "logo", "mark-light-bg.png")
    if os.path.exists(logo_path):
        pm = QPixmap(logo_path)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # 3. Fallback: programmatic icon
    s = float(size)
    pm = _new_pixmap(size)
    p = _painter(pm)
    from PySide6.QtGui import QLinearGradient
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0.0, QColor("#3B8CFF"))
    grad.setColorAt(1.0, QColor(config.ACCENT))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    r = QRectF(s * 0.06, s * 0.06, s * 0.88, s * 0.88)
    p.drawRoundedRect(r, s * 0.22, s * 0.22)
    p.save()
    p.translate(s * 0.14, s * 0.14)
    _draw_pen(p, s * 0.72, QColor("#FFFFFF"))
    p.restore()
    p.end()
    return pm

