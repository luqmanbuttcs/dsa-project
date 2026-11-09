"""Foundation slot graphics item: suit placeholder with soft glow."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
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

        path = QPainterPath()
        path.addRoundedRect(rect, 10.0, 10.0)
        painter.fillPath(path, QColor(10, 64, 33, 170))
        painter.setPen(QColor(120, 220, 150, 170))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Large faint suit symbol.
        suit_rect = QRectF(
            rect.center().x() - 26, rect.center().y() - 26, 52, 52
        )
        painter.setOpacity(0.34)
        resources.suit_renderer(self._suit.value).render(painter, suit_rect)
        painter.setOpacity(1.0)

        if self._legal_glow > 0.01:
            from solitaire.ui.premium.graphics.effects.highlights import paint_glow

            paint_glow(painter, rect, 10.0, QColor(240, 199, 94), self._legal_glow)
        painter.restore()
