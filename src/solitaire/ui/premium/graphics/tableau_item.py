"""Tableau column slot graphics item."""

from __future__ import annotations

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.graphics.pile_slots import PileSlotItem
from solitaire.ui.premium.theme import CARD_H, CARD_W


class TableauColumnGraphicsItem(PileSlotItem):
    """Backdrop for one tableau column; cards fan above this slot."""

    def __init__(self, column_id: str, parent=None) -> None:
        super().__init__(column_id, float(CARD_W), float(CARD_H), parent)
        self._empty = True
        self.setZValue(0.5)

    def set_empty(self, empty: bool) -> None:
        if empty != self._empty:
            self._empty = empty
            self.update()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if not self._empty:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.paint_slot_base(painter, self.slot_rect())
        painter.restore()

    def boundingRect(self) -> QRectF:
        return self.slot_rect().adjusted(-10.0, -10.0, 10.0, 10.0)
