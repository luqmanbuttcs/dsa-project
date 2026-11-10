"""Stock slot graphics item: ornate layered deck, count label, recycle cue."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.graphics.effects.highlights import paint_rounded_panel
from solitaire.ui.premium.graphics.pile_slots import PileSlotItem
from solitaire.ui.premium.theme import CARD_H, CARD_W


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

        # "Stock" caption chip with the remaining-card count.
        chip = QRectF(rect.left() - 14, rect.bottom() + 10, rect.width() + 28, 40)
        paint_rounded_panel(painter, chip, 12, QColor(8, 18, 32, 235), QColor(36, 57, 90), 1.0)
        title_font = QFont("DejaVu Sans")
        title_font.setPixelSize(13)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor("#F2EEE2")))
        painter.drawText(
            QRectF(chip.left(), chip.top() + 5, chip.width(), 18),
            Qt.AlignmentFlag.AlignHCenter,
            "Stock",
        )
        count_font = QFont("DejaVu Sans")
        count_font.setPixelSize(12)
        painter.setFont(count_font)
        painter.setPen(QPen(QColor("#E8C766")))
        painter.drawText(
            QRectF(chip.left(), chip.top() + 20, chip.width(), 16),
            Qt.AlignmentFlag.AlignHCenter,
            f"({self._count} cards)",
        )
        painter.restore()

    def boundingRect(self) -> QRectF:
        return QRectF(-22.0, -8.0, CARD_W + 44.0, CARD_H + 66.0)
