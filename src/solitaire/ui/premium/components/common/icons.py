"""Vector icon factory: every icon is painted with QPainter, no downloads."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

GOLD = QColor("#E8C766")
IVORY = QColor("#F2EEE2")
DARK = QColor("#241A02")


def icon_pixmap(name: str, size: int = 22, color: QColor | None = None) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    _PAINTERS[name](painter, QRectF(1, 1, size - 2, size - 2), color or GOLD)
    painter.end()
    return pixmap


def make_icon(name: str, size: int = 22, color: QColor | None = None) -> QIcon:
    return QIcon(icon_pixmap(name, size, color))


def _stopwatch(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    circle = QRectF(r.left() + 1, r.top() + 4, r.width() - 2, r.height() - 6)
    p.drawEllipse(circle)
    p.drawLine(QPointF(r.center().x(), r.top() + 1), QPointF(r.center().x() + 5, r.top() + 1))
    p.drawLine(QPointF(r.center().x(), circle.top()), QPointF(r.center().x(), circle.center().y() - 2))
    p.drawLine(QPointF(circle.center().x(), circle.center().y() - 3), QPointF(circle.center().x() + 5, circle.center().y() - 5))


def _moves(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    center = r.center()
    d = r.width() * 0.34
    for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d)):
        p.drawLine(center, center + QPointF(dx, dy))
        arrow = QPolygonF([
            center + QPointF(dx * 1.28, dy * 1.28),
            center + QPointF(dx * 0.9 + dy * 0.32, dy * 0.9 + dx * 0.32),
            center + QPointF(dx * 0.9 - dy * 0.32, dy * 0.9 - dx * 0.32),
        ])
        p.setBrush(c)
        p.drawPolygon(arrow)


def _trophy(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cup = QRectF(r.left() + r.width() * 0.22, r.top(), r.width() * 0.56, r.height() * 0.5)
    p.drawRoundedRect(cup, 4, 4)
    p.drawArc(QRectF(r.left(), r.top() + r.height() * 0.08, r.width() * 0.24, r.height() * 0.3), 90 * 16, -160 * 16)
    p.drawArc(QRectF(r.right() - r.width() * 0.24, r.top() + r.height() * 0.08, r.width() * 0.24, r.height() * 0.3), 90 * 16, 160 * 16)
    p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.5), QPointF(r.center().x(), r.bottom() - r.height() * 0.18))
    p.drawLine(QPointF(r.left() + r.width() * 0.3, r.bottom() - r.height() * 0.12), QPointF(r.right() - r.width() * 0.3, r.bottom() - r.height() * 0.12))


def _bulb(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    bulb = QRectF(r.left() + r.width() * 0.25, r.top(), r.width() * 0.5, r.height() * 0.62)
    p.drawEllipse(bulb)
    p.drawPolyline(QPolygonF([
        QPointF(r.center().x() - 4, r.bottom() - r.height() * 0.22),
        QPointF(r.center().x() + 4, r.bottom() - r.height() * 0.22),
        QPointF(r.center().x() + 3, r.bottom() - r.height() * 0.05),
        QPointF(r.center().x() - 3, r.bottom() - r.height() * 0.05),
        QPointF(r.center().x() - 4, r.bottom() - r.height() * 0.22),
    ]))


def _arrow(p: QPainter, r: QRectF, c: QColor, flip: bool) -> None:
    pen = QPen(c, 2.4)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path_y = r.center().y()
    start = QPointF(r.left() + 2, path_y)
    end = QPointF(r.right() - 6, path_y)
    if flip:
        start, end = end, start
    p.drawLine(start, end)
    head = QPolygonF([
        end + QPointF(6, 0) if not flip else end + QPointF(-6, 0),
        end + QPointF(-2, -5) if not flip else end + QPointF(2, -5),
        end + QPointF(-2, 5) if not flip else end + QPointF(2, 5),
    ])
    p.setBrush(c)
    p.drawPolygon(head)


def _undo(p: QPainter, r: QRectF, c: QColor) -> None:
    _arrow(p, r, c, flip=True)


def _redo(p: QPainter, r: QRectF, c: QColor) -> None:
    _arrow(p, r, c, flip=False)


def _gear(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    center = r.center()
    radius = r.width() * 0.32
    p.drawEllipse(center, radius, radius)
    p.drawEllipse(center, radius * 0.42, radius * 0.42)
    for index in range(8):
        angle = math.pi / 4 * index
        inner = center + QPointF(radius * 1.0 * math.cos(angle), radius * 1.0 * math.sin(angle))
        outer = center + QPointF(radius * 1.45 * math.cos(angle), radius * 1.45 * math.sin(angle))
        p.drawLine(inner, outer)


def _spade(p: QPainter, r: QRectF, c: QColor) -> None:
    path = QPainterPath()
    center_x = r.center().x()
    path.moveTo(center_x, r.top() + 2)
    path.cubicTo(r.right(), r.center().y() - 2, r.right() - 2, r.bottom() - 6, center_x + 5, r.bottom() - 10)
    path.cubicTo(center_x + 2, r.bottom() - 4, center_x - 2, r.bottom() - 4, center_x - 5, r.bottom() - 10)
    path.cubicTo(r.left() + 2, r.bottom() - 6, r.left(), r.center().y() - 2, center_x, r.top() + 2)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(c)
    p.drawPath(path)


def _flask(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(r.center().x() - 3, r.top()), QPointF(r.center().x() + 3, r.top()))
    p.drawLine(QPointF(r.center().x() - 3, r.top()), QPointF(r.center().x() - 3, r.center().y()))
    p.drawLine(QPointF(r.center().x() + 3, r.top()), QPointF(r.center().x() + 3, r.center().y()))
    path = QPainterPath()
    path.moveTo(r.center().x() - 3, r.center().y())
    path.lineTo(r.left() + 2, r.bottom() - 2)
    path.lineTo(r.right() - 2, r.bottom() - 2)
    path.lineTo(r.center().x() + 3, r.center().y())
    p.drawPath(path)


def _cap(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    top = QPolygonF([
        QPointF(r.center().x(), r.top()),
        QPointF(r.right(), r.center().y()),
        QPointF(r.center().x(), r.center().y() + 2),
        QPointF(r.left(), r.center().y()),
    ])
    p.drawPolygon(top)
    p.drawArc(QRectF(r.left() + 2, r.center().y(), r.width() - 4, r.height() * 0.5), 180 * 16, -180 * 16)


def _chart(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.4)
    p.setPen(pen)
    base = r.bottom() - 2
    p.drawLine(QPointF(r.left() + 1, r.top() + 1), QPointF(r.left() + 1, base))
    p.drawLine(QPointF(r.left() + 1, base), QPointF(r.right() - 1, base))
    for index, height in enumerate((0.4, 0.7, 0.55, 0.9)):
        x = r.left() + 4 + index * (r.width() - 8) / 4.4
        p.drawLine(QPointF(x, base), QPointF(x, base - r.height() * height))


def _check(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.6)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolyline(QPolygonF([
        QPointF(r.left() + 2, r.center().y() + 1),
        QPointF(r.center().x() - 1, r.bottom() - 3),
        QPointF(r.right() - 2, r.top() + 3),
    ]))


def _warning(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolygon(QPolygonF([
        QPointF(r.center().x(), r.top() + 1),
        QPointF(r.right(), r.bottom() - 1),
        QPointF(r.left(), r.bottom() - 1),
    ]))
    p.drawLine(QPointF(r.center().x(), r.center().y() - 1), QPointF(r.center().x(), r.center().y() + 4))
    p.drawPoint(QPointF(r.center().x(), r.bottom() - 4))


def _info(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(r.left() + 1, r.top() + 1, r.width() - 2, r.height() - 2))
    p.drawLine(QPointF(r.center().x(), r.center().y()), QPointF(r.center().x(), r.bottom() - 5))
    p.drawPoint(QPointF(r.center().x(), r.top() + 6))


def _list_icon(p: QPainter, r: QRectF, c: QColor) -> None:
    pen = QPen(c, 2.0)
    p.setPen(pen)
    for index in range(3):
        y = r.top() + 3 + index * (r.height() - 6) / 2.4
        p.drawLine(QPointF(r.left() + 1, y), QPointF(r.left() + 5, y))
        p.drawLine(QPointF(r.left() + 9, y), QPointF(r.right() - 1, y))


_PAINTERS = {
    "stopwatch": _stopwatch,
    "moves": _moves,
    "trophy": _trophy,
    "bulb": _bulb,
    "undo": _undo,
    "redo": _redo,
    "gear": _gear,
    "spade": _spade,
    "flask": _flask,
    "cap": _cap,
    "chart": _chart,
    "check": _check,
    "warning": _warning,
    "info": _info,
    "list": _list_icon,
}
