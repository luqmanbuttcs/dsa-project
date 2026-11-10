"""Shared behaviour for pile slot graphics items."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.ui.premium.graphics.effects.highlights import paint_glow


def paint_status_chip(
    painter: QPainter,
    rect: QRectF,
    label: str,
    detail: str,
    *,
    accent: QColor | None = None,
) -> None:
    """Paint a compact premium game-status chip centred in `rect`.

    Renders `LABEL  •  DETAIL` on one line — the label in gold, the bullet
    and detail in ivory — inside a deep navy pill with a luminous accent
    dot. Used for the Stock/Waste captions that live in the scene's
    reserved caption band.
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pill = QPainterPath()
    pill.addRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
    painter.fillPath(pill, QColor(8, 18, 32, 238))
    painter.setPen(QPen(QColor(36, 57, 90), 1.0))
    painter.drawPath(pill)

    # Luminous accent dot inside the left cap of the pill.
    dot_color = accent if accent is not None else QColor(240, 199, 94)
    dot_center = QPointF(rect.left() + rect.height() / 2.0, rect.center().y())
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(dot_color)
    painter.drawEllipse(dot_center, 3.0, 3.0)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(dot_color.red(), dot_color.green(), dot_color.blue(), 90), 1.0))
    painter.drawEllipse(dot_center, 5.2, 5.2)

    font = QFont("DejaVu Sans")
    font.setPixelSize(11)
    font.setBold(True)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.7)
    painter.setFont(font)
    metrics = QFontMetricsF(font)
    bullet = " • "
    total = metrics.horizontalAdvance(label) + metrics.horizontalAdvance(bullet) + metrics.horizontalAdvance(detail)
    # Centre the text in the area right of the accent dot, never over it.
    area_left = dot_center.x() + 9.0
    area_right = rect.right() - 12.0
    left = (area_left + area_right) / 2.0 - total / 2.0
    baseline = rect.center().y() + metrics.ascent() / 2.0 - metrics.descent() / 3.0

    painter.setPen(QPen(QColor("#E8C766")))
    painter.drawText(QPointF(left, baseline), label)
    left += metrics.horizontalAdvance(label)
    painter.setPen(QPen(QColor(159, 176, 198)))
    painter.drawText(QPointF(left, baseline), bullet)
    left += metrics.horizontalAdvance(bullet)
    painter.setPen(QPen(QColor("#F2EEE2")))
    painter.drawText(QPointF(left, baseline), detail)
    painter.restore()


class PileSlotItem(QGraphicsObject):
    """Base class for stock, waste, foundation and tableau slot decorations.

    Provides:
    - a target rect (logical coordinates),
    - an animatable `legal_glow` property for gold destination highlighting,
    - a click callback hook (slots forward clicks to the scene/controller).
    """

    SLOT_FILL = QColor(6, 34, 17, 150)
    SLOT_BORDER = QColor(226, 198, 116, 150)

    def __init__(self, pile_id: str, width: float, height: float, parent=None) -> None:
        super().__init__(parent)
        self._pile_id = pile_id
        self._width = width
        self._height = height
        self._legal_glow = 0.0
        self.on_clicked = None  # callback(item) wired by the scene
        self.setAcceptHoverEvents(True)
        self.setZValue(2.0)

    @property
    def pile_id(self) -> str:
        return self._pile_id

    def slot_rect(self) -> QRectF:
        return QRectF(0.0, 0.0, self._width, self._height)

    def boundingRect(self) -> QRectF:
        return self.slot_rect().adjusted(-8.0, -8.0, 8.0, 8.0)

    # --- animatable legal-target glow ---------------------------------------
    def get_legal_glow(self) -> float:
        return self._legal_glow

    def set_legal_glow(self, value: float) -> None:
        self._legal_glow = max(0.0, min(1.0, float(value)))
        self.update()

    legal_glow = pyqtProperty(float, get_legal_glow, set_legal_glow)

    def set_legal_target(self, legal: bool) -> None:
        target = 1.0 if legal else 0.0
        if abs(target - self._legal_glow) < 0.01:
            if target != self._legal_glow:
                self._legal_glow = target
                self.update()
            return
        from solitaire.ui.premium.animations.card_animation_manager import (
            CardAnimationManager,
        )

        CardAnimationManager.instance().animate_property(self, "legal_glow", target, 180)

    # --- interaction ---------------------------------------------------------
    def hoverEnterEvent(self, event) -> None:  # noqa: N802
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, "_pressed", False):
            # The accepted press grabbed the mouse; this release is ours even
            # if hover state says otherwise (cursor drift / offscreen tests).
            self._pressed = False
            if self.on_clicked is not None:
                self.on_clicked(self)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # --- shared painting helpers ----------------------------------------------
    def paint_slot_base(self, painter: QPainter, rect: QRectF, radius: float = 10.0) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, self.SLOT_FILL)
        painter.setPen(QPen(self.SLOT_BORDER, 1.2))
        painter.drawPath(path)
        if self._legal_glow > 0.01:
            paint_glow(painter, rect, radius, QColor(240, 199, 94), self._legal_glow)
        painter.restore()
