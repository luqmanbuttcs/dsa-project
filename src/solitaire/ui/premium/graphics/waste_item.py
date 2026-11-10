"""Waste slot graphics item."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.graphics.effects.highlights import paint_rounded_panel
from solitaire.ui.premium.graphics.pile_slots import PileSlotItem
from solitaire.ui.premium.theme import CARD_H, CARD_W


class WasteGraphicsItem(PileSlotItem):
    """Slot decoration for the waste pile; real cards fan above it."""

    def __init__(self, parent=None) -> None:
        super().__init__("waste", float(CARD_W), float(CARD_H), parent)
        self.setZValue(1.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.paint_slot_base(painter, self.slot_rect())
        chip = QRectF(
            self.slot_rect().left() - 6,
            self.slot_rect().bottom() + 10,
            self.slot_rect().width() + 12,
            26,
        )
        paint_rounded_panel(painter, chip, 10, QColor(8, 18, 32, 235), QColor(36, 57, 90), 1.0)
        font = QFont("DejaVu Sans")
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#F2EEE2"))
        painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, "Waste")
        painter.restore()

    def boundingRect(self) -> QRectF:
        base = self.slot_rect()
        return QRectF(base.left() - 14, base.top() - 8, base.width() + 28, base.height() + 52)
