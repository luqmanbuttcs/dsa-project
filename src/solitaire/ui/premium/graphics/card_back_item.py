"""Reusable card-back graphics used by the stock pile and effects.

The ornate royal-blue back ships as a bundled SVG asset; this item wraps it
with rounded clipping, a soft shadow and depth layers for stacked decks.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QPainterPath
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium import resources
from solitaire.ui.premium.graphics.effects.highlights import paint_card_shadow
from solitaire.ui.premium.theme import CARD_H, CARD_RADIUS, CARD_W


def paint_back_layers(
    painter: QPainter,
    rect: QRectF,
    layers: int,
    offset_step: float = 2.2,
) -> None:
    """Paint `layers` offset card backs to suggest a thick deck."""
    if layers <= 0:
        return
    renderer = resources.back_renderer()
    for index in range(layers - 1, -1, -1):
        shifted = rect.translated(-index * offset_step, -index * offset_step)
        path = QPainterPath()
        path.addRoundedRect(shifted, CARD_RADIUS, CARD_RADIUS)
        painter.save()
        painter.setClipPath(path)
        renderer.render(painter, shifted)
        painter.restore()


class CardBackItem(QGraphicsObject):
    """A standalone face-down card item (used by decorative compositions)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setZValue(1.0)

    def boundingRect(self) -> QRectF:
        return QRectF(-8, -8, CARD_W + 16, CARD_H + 16)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        rect = QRectF(0, 0, CARD_W, CARD_H)
        paint_card_shadow(painter, rect, CARD_RADIUS)
        paint_back_layers(painter, rect, layers=1)
