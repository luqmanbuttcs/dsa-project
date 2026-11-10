"""Foundation slot graphics item: suit placeholder with soft glow."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.domain.card import Suit
from solitaire.ui.premium import resources
from solitaire.ui.premium.graphics.pile_slots import PileSlotItem
from solitaire.ui.premium.theme import CARD_H, CARD_W


class FoundationGraphicsItem(PileSlotItem):
    """One suit foundation placeholder; the top card renders above it."""

    def __init__(self, suit: Suit, parent=None) -> None:
        super().__init__(f"foundation-{suit.code.lower()}", float(CARD_W), float(CARD_H), parent)
        self._suit = suit
        self._occupied = False
        self.setZValue(1.0)

    @property
    def suit(self) -> Suit:
        return self._suit

    def set_occupied(self, occupied: bool) -> None:
        if occupied != self._occupied:
            self._occupied = occupied
            self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self._occupied:
            # The real card covers the slot; keep only the legal-glow ring.
            if self._legal_glow > 0.01:
                from solitaire.ui.premium.graphics.effects.highlights import paint_glow

                paint_glow(painter, self.slot_rect(), 10.0, QColor(240, 199, 94), self._legal_glow)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.slot_rect()

        # Recessed dark-green well with a gold dressage frame.
        path = QPainterPath()
        path.addRoundedRect(rect, 10.0, 10.0)
        painter.fillPath(path, QColor(6, 44, 21, 210))
        painter.setPen(QPen(QColor(212, 175, 55, 205), 1.7))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.setPen(QPen(QColor(240, 199, 94, 90), 0.9))
        painter.drawPath(_rounded(rect.adjusted(3.2, 3.2, -3.2, -3.2), 7.5))

        # Inner contact shadow along the top edge for physical depth.
        top_shadow = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + 20.0))
        top_shadow.setColorAt(0.0, QColor(0, 0, 0, 90))
        top_shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setClipPath(path)
        painter.fillPath(path, top_shadow)
        painter.setClipping(False)

        # Large suit symbol in full heraldic colour with an embossed twin.
        pip_center = rect.center()
        pip_rect = QRectF(pip_center.x() - 27, pip_center.y() - 27, 54, 54)
        shadow_rect = pip_rect.translated(1.6, 2.2)
        painter.setOpacity(0.35)
        resources.suit_renderer(self._suit.value).render(painter, shadow_rect)
        painter.setOpacity(1.0)
        painter.setOpacity(0.62)
        resources.suit_renderer(self._suit.value).render(painter, pip_rect)
        painter.setOpacity(1.0)

        if self._legal_glow > 0.01:
            from solitaire.ui.premium.graphics.effects.highlights import paint_glow

            paint_glow(painter, rect, 10.0, QColor(240, 199, 94), self._legal_glow)
        painter.restore()


def _rounded(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path
