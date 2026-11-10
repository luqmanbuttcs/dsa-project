"""Stock slot graphics item: ornate layered deck, recycle cue, status chip."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen

from solitaire.ui.premium.graphics.pile_slots import PileSlotItem, paint_status_chip
from solitaire.ui.premium.theme import CARD_H, CARD_W

# Status chip geometry, in item coordinates. The scene reserves a caption
# band below the top pile row exactly this tall, so the chip can never be
# covered by tableau cards (see game_board_scene.LABEL_BAND).
CHIP_WIDTH = CARD_W + 34.0
CHIP_HEIGHT = 30.0
CHIP_GAP_ABOVE = 12.0


class StockGraphicsItem(PileSlotItem):
    """Decorates the stock slot; the real face-down cards sit above it."""

    def __init__(self, parent=None) -> None:
        super().__init__("stock", float(CARD_W), float(CARD_H), parent)
        self._count = 0
        self._can_recycle = False
        self.setZValue(1.0)

    def set_state(self, count: int, can_recycle: bool) -> None:
        changed = (count, can_recycle) != (self._count, self._can_recycle)
        self._count = count
        self._can_recycle = can_recycle
        if changed:
            self.update()

    @property
    def chip_text(self) -> str:
        """Human-readable status rendered inside the caption chip."""
        if self._count == 0 and self._can_recycle:
            return "STOCK • RECYCLE"
        noun = "CARD" if self._count == 1 else "CARDS"
        return f"STOCK • {self._count} {noun}"

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
        rect = self.slot_rect()

        if self._count == 0 and not self._can_recycle:
            self.paint_slot_base(painter, rect)

        if self._count == 0 and self._can_recycle:
            # Recycling cue: gold circular arrow on an emerald slot.
            self.paint_slot_base(painter, rect)
            painter.setPen(QPen(QColor(240, 199, 94), 3.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            center = rect.center()
            arc_rect = QRectF(
                center.x() - 26, center.y() - 26, 52, 52
            )
            painter.drawArc(arc_rect, 40 * 16, 280 * 16)
            painter.setBrush(QColor(240, 199, 94))
            painter.setPen(Qt.PenStyle.NoPen)
            arrow = QPainterPath()
            arrow.moveTo(center.x() + 30, center.y() - 2)
            arrow.lineTo(center.x() + 16, center.y() - 12)
            arrow.lineTo(center.x() + 16, center.y() + 8)
            arrow.closeSubpath()
            painter.drawPath(arrow)

        # Premium status chip with the genuine dynamic count.
        paint_status_chip(painter, self.chip_rect(), "STOCK", self._chip_detail())
        painter.restore()

    def _chip_detail(self) -> str:
        if self._count == 0 and self._can_recycle:
            return "RECYCLE"
        return f"{self._count} {'CARD' if self._count == 1 else 'CARDS'}"

    def boundingRect(self) -> QRectF:
        slot = self.slot_rect()
        chip = self.chip_rect()
        left = min(slot.left(), chip.left())
        top = min(slot.top(), chip.top())
        right = max(slot.right(), chip.right())
        bottom = max(slot.bottom(), chip.bottom())
        return QRectF(left - 8.0, top - 8.0, right - left + 16.0, bottom - top + 16.0)
