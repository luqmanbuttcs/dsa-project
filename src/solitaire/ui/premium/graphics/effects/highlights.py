"""Reusable painter effects: glow strokes and soft shadows."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen


def paint_glow(
    painter: QPainter,
    rect: QRectF,
    radius: float,
    color: QColor,
    intensity: float = 1.0,
    layers: int = 3,
) -> None:
    """Paint a soft multi-stroke glow around a rounded rectangle."""
    if intensity <= 0.01:
        return
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    for index in range(layers, 0, -1):
        spread = index * 2.4
        alpha = int(70 * intensity / index)
        pen_color = QColor(color)
        pen_color.setAlpha(alpha)
        painter.setPen(QPen(pen_color, 2.2))
        expanded = rect.adjusted(-spread, -spread, spread, spread)
        glow_path = QPainterPath()
        glow_path.addRoundedRect(expanded, radius + spread, radius + spread)
        painter.drawPath(glow_path)
    painter.restore()


def paint_card_shadow(painter: QPainter, rect: QRectF, radius: float, boost: float = 0.0) -> None:
    """Two-layer soft shadow beneath a card or slot.

    `boost` (0..1) deepens and offsets the shadow for hover/drag elevation,
    making the card read as physically lifted off the felt.
    """
    painter.save()
    spread = 1.0 + 0.9 * boost
    for offset, alpha in ((5.0, 46), (2.5, 60)):
        shadow = QColor(0, 0, 0, min(255, int(alpha * (1.0 + 0.8 * boost))))
        shadow_rect = rect.translated(offset * 0.6 * spread, offset * spread)
        path = QPainterPath()
        path.addRoundedRect(shadow_rect, radius, radius)
        painter.fillPath(path, shadow)
    painter.restore()


def paint_rounded_panel(
    painter: QPainter,
    rect: QRectF,
    radius: float,
    fill: QColor,
    border: QColor,
    border_width: float = 1.2,
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.fillPath(path, fill)
    painter.setPen(QPen(border, border_width))
    painter.drawPath(path)
    painter.restore()
