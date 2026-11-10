"""Waste slot graphics item with a dynamic status chip."""

from __future__ import annotations

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QPainter

from solitaire.ui.premium.graphics.pile_slots import PileSlotItem, paint_status_chip
from solitaire.ui.premium.theme import CARD_H, CARD_W

# Matches the Stock chip so both captions read as one system.
CHIP_WIDTH = CARD_W + 34.0
CHIP_HEIGHT = 30.0
CHIP_GAP_ABOVE = 12.0

MINT_ACCENT = QColor(64, 224, 178)


class WasteGraphicsItem(PileSlotItem):
    """Slot decoration for the waste pile; real cards fan above it."""

    def __init__(self, parent=None) -> None:
        super().__init__("waste", float(CARD_W), float(CARD_H), parent)
        self._count = 0
        self.setZValue(1.0)

    def set_state(self, count: int) -> None:
        """Track the genuine waste population for the caption chip."""
        if count != self._count:
            self._count = count
            self.update()

    @property
    def chip_text(self) -> str:
        noun = "CARD" if self._count == 1 else "CARDS"
        return f"WASTE • {self._count} {noun}"

    def chip_rect(self) -> QRectF:
        """Chip rect in item-local coordinates (reserved caption band)."""
        slot = self.slot_rect()
        return QRectF(
            slot.center().x() - CHIP_WIDTH / 2.0,
            slot.bottom() + CHIP_GAP_ABOVE,
            CHIP_WIDTH,
            CHIP_HEIGHT,
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.paint_slot_base(painter, self.slot_rect())
        paint_status_chip(
            painter, self.chip_rect(), "WASTE", self._chip_detail(), accent=MINT_ACCENT
        )
        painter.restore()

    def _chip_detail(self) -> str:
        return f"{self._count} {'CARD' if self._count == 1 else 'CARDS'}"

    def boundingRect(self) -> QRectF:
        slot = self.slot_rect()
        chip = self.chip_rect()
        left = min(slot.left(), chip.left())
        top = min(slot.top(), chip.top())
        right = max(slot.right(), chip.right())
        bottom = max(slot.bottom(), chip.bottom())
        return QRectF(left - 8.0, top - 8.0, right - left + 16.0, bottom - top + 16.0)
