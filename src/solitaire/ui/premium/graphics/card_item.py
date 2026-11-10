"""Premium interactive playing-card graphics item.

Rendering rules (per the approved reference):
- warm ivory surface, rounded corners, refined border, soft drop shadow;
- rank top-left with a small suit symbol, mirrored index bottom-right;
- ONE oversized central suit illustration for Ace through 10;
- bundled SVG court illustrations for Jack, Queen and King;
- bundled royal-blue ornate back for face-down cards;
- gold selection glow and hint glow driven by animatable properties.

Identity: one item per real card, keyed by `card.card_id`. Items are
reused across scene refreshes and never mutate game state.
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRectF, Qt, pyqtProperty
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.domain.card import Card, Rank
from solitaire.ui.premium import resources
from solitaire.ui.premium.graphics.effects.highlights import paint_card_shadow, paint_glow
from solitaire.ui.premium.theme import CARD_H, CARD_RADIUS, CARD_W

DRAG_THRESHOLD = 12.0

IVORY_TOP = "#FDF9EE"
IVORY_BOTTOM = "#EFE4C6"
BORDER = "#C4B58E"
RED = "#C62828"
INK = "#1B1E26"

SELECT_GOLD = QColor(240, 199, 94)
HINT_GOLD = QColor(240, 199, 94, 190)


def rank_label(rank: Rank) -> str:
    return rank.label


class CardGraphicsItem(QGraphicsObject):
    """One real playing card in the game scene."""

    def __init__(self, card: Card, parent=None) -> None:
        super().__init__(parent)
        self._card = card
        self._face_up = card.face_up
        self._flip = 0.0 if card.face_up else 1.0
        # flip convention: 0 = fully face-up, 1 = fully face-down
        self._highlight = 0.0
        self._hint = 0.0
        self._error_pulse = 0.0
        self._interactive = True
        self.on_clicked = None  # callback(item) wired by the scene
        self.drag_provider = None  # callback(card_id) -> (card_ids, pile) | None
        self._press_pos: QPoint | None = None
        self.setAcceptHoverEvents(True)
        self.setZValue(10.0)

    # --- identity ----------------------------------------------------------
    @property
    def card_id(self) -> str:
        return self._card.card_id

    @property
    def card(self) -> Card:
        return self._card

    def refresh_card(self, card: Card) -> None:
        """Re-bind to the authoritative Card object and refresh face state."""
        self._card = card
        self.refresh_face(animated=False)

    @property
    def interactive(self) -> bool:
        return self._interactive

    def set_interactive(self, interactive: bool) -> None:
        self._interactive = interactive
        if not interactive:
            self._highlight = 0.0
            self._hint = 0.0
        self.update()
        self.setAcceptHoverEvents(interactive)
        self.unsetCursor()

    # --- animatable properties ---------------------------------------------
    def get_flip(self) -> float:
        return self._flip

    def set_flip(self, value: float) -> None:
        self._flip = max(0.0, min(1.0, float(value)))
        self.update()

    flip = pyqtProperty(float, get_flip, set_flip)

    def get_highlight(self) -> float:
        return self._highlight

    def set_highlight(self, value: float) -> None:
        self._highlight = max(0.0, min(1.0, float(value)))
        self.update()

    highlight = pyqtProperty(float, get_highlight, set_highlight)

    def get_hint(self) -> float:
        return self._hint

    def set_hint(self, value: float) -> None:
        self._hint = max(0.0, min(1.0, float(value)))
        self.update()

    hint = pyqtProperty(float, get_hint, set_hint)

    def get_error_pulse(self) -> float:
        return self._error_pulse

    def set_error_pulse(self, value: float) -> None:
        self._error_pulse = max(0.0, min(1.0, float(value)))
        self.update()

    error_pulse = pyqtProperty(float, get_error_pulse, set_error_pulse)

    def refresh_face(self, *, animated: bool = False) -> None:
        """Sync the painted face with the domain card's face_up flag."""
        target = 0.0 if self._card.face_up else 1.0
        if animated and target != self._flip:
            from solitaire.ui.premium.animations.card_animation_manager import (
                CardAnimationManager,
            )

            CardAnimationManager.instance().animate_flip(self)
        else:
            self._flip = target
            self.update()

    # --- geometry -----------------------------------------------------------
    def boundingRect(self) -> QRectF:
        return QRectF(-10.0, -10.0, CARD_W + 20.0, CARD_H + 20.0)

    def rect(self) -> QRectF:
        return QRectF(0.0, 0.0, float(CARD_W), float(CARD_H))

    # --- painting ------------------------------------------------------------
    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = self.rect()
        progress = self._flip

        if 0.0001 < progress < 0.9999:
            # Mid-flip: squeeze horizontally and switch the face at 50%.
            squeeze = abs(1.0 - 2.0 * progress)
            painter.translate(rect.center())
            painter.scale(max(0.04, squeeze), 1.0)
            painter.translate(-rect.center().x(), -rect.center().y())

        show_back = progress >= 0.5
        paint_card_shadow(painter, rect, CARD_RADIUS)
        if show_back:
            self._paint_back(painter, rect)
        else:
            self._paint_face(painter, rect)

        if self._highlight > 0.01:
            paint_glow(painter, rect, CARD_RADIUS, SELECT_GOLD, self._highlight)
            painter.setPen(QPen(SELECT_GOLD, 2.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)
        if self._hint > 0.01:
            painter.setPen(QPen(HINT_GOLD, 3.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), CARD_RADIUS, CARD_RADIUS)
        if self._error_pulse > 0.01:
            from PyQt6.QtGui import QColor as _QColor

            painter.setPen(QPen(_QColor(224, 85, 85, int(210 * self._error_pulse)), 3.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)

        painter.restore()

    def _paint_back(self, painter: QPainter, rect: QRectF) -> None:
        path = QPainterPath()
        path.addRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)
        painter.save()
        painter.setClipPath(path)
        resources.back_renderer().render(painter, rect)
        painter.restore()
        painter.setPen(QPen(QColor(12, 27, 56, 160), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)

    def _paint_face(self, painter: QPainter, rect: QRectF) -> None:
        # Warm ivory body with a subtle vertical sheen.
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, QColor(IVORY_TOP))
        gradient.setColorAt(1.0, QColor(IVORY_BOTTOM))
        path = QPainterPath()
        path.addRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)
        painter.fillPath(path, gradient)

        painter.setPen(QPen(QColor(BORDER), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)

        ink = RED if self._card.color.value == "red" else INK
        self._paint_corner(painter, rect, ink, mirrored=False)
        self._paint_corner(painter, rect, ink, mirrored=True)
        self._paint_center(painter, rect, ink)

    def _paint_corner(self, painter: QPainter, rect: QRectF, ink: str, *, mirrored: bool) -> None:
        painter.save()
        if mirrored:
            painter.translate(rect.center())
            painter.rotate(180.0)
            painter.translate(-rect.center().x(), -rect.center().y())

        text_rect = QRectF(rect.left() + 5.0, rect.top() + 3.0, 34.0, 26.0)
        font = QFont("Georgia")
        font.setPixelSize(21)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(ink)))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, rank_label(self._card.rank))

        suit_rect = QRectF(rect.left() + 6.0, rect.top() + 27.0, 17.0, 17.0)
        resources.suit_renderer(self._card.suit.value).render(painter, suit_rect)
        painter.restore()

    def _paint_center(self, painter: QPainter, rect: QRectF, ink: str) -> None:
        rank = self._card.rank
        if rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
            court_rect = QRectF(
                rect.left() + 9.0, rect.top() + 26.0, rect.width() - 18.0, rect.height() - 44.0
            )
            resources.court_renderer(rank.name.lower(), self._card.suit.value).render(
                painter, court_rect
            )
            return

        # One oversized central suit illustration for Ace through 10.
        size = 86.0 if rank is Rank.ACE else 72.0
        center_rect = QRectF(
            rect.center().x() - size / 2.0,
            rect.center().y() - size / 2.0 + 2.0,
            size,
            size,
        )
        resources.suit_renderer(self._card.suit.value).render(painter, center_rect)

        if rank is not Rank.ACE:
            # Faint oversized rank numeral behind the suit for readability.
            painter.save()
            font = QFont("Georgia")
            font.setPixelSize(30)
            font.setBold(True)
            painter.setFont(font)
            halo = QColor(ink)
            halo.setAlpha(30)
            painter.setPen(QPen(halo))
            painter.drawText(
                QRectF(rect.left(), rect.top() + 30.0, rect.width(), 40.0),
                Qt.AlignmentFlag.AlignHCenter,
                rank_label(rank),
            )
            painter.restore()

    # --- interaction ---------------------------------------------------------
    def hoverEnterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._interactive:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._interactive and event.button() == Qt.MouseButton.LeftButton:
            # QGraphicsSceneMouseEvent.pos() is the press point in item-local
            # coordinates (scene events have no QMouseEvent.position()).
            self._press_pos = event.pos().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """Start a real QDrag once the press becomes a deliberate drag."""
        if (
            self._interactive
            and self._press_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and self.drag_provider is not None
        ):
            distance = (event.pos().toPoint() - self._press_pos).manhattanLength()
            if distance >= DRAG_THRESHOLD:
                self._press_pos = None
                if self._start_drag():
                    event.accept()
                    return
        super().mouseMoveEvent(event)

    def _start_drag(self) -> bool:
        """Begin a QDrag carrying the selected run; True when one started."""
        payload = self.drag_provider(self.card_id)
        if not payload:
            return False
        from PyQt6.QtGui import QDrag
        from solitaire.ui.premium.controllers.drag_controller import create_payload

        card_ids, source_pile = payload
        drag = QDrag(self)
        drag.setMimeData(create_payload(card_ids, source_pile))
        drag.setHotSpot(QPoint(24, 24))
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        try:
            drag.exec(Qt.DropAction.MoveAction)
        finally:
            self.unsetCursor()
        return True

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._interactive and event.button() == Qt.MouseButton.LeftButton:
            # The accepted press made this item the mouse grabber, so this
            # release belongs to it even when the cursor drifted off the
            # card or the hover state was never updated (offscreen/tests).
            pressed = self._press_pos is not None
            self._press_pos = None
            if pressed and self.on_clicked is not None:
                self.on_clicked(self)
            event.accept()
            return
        super().mouseReleaseEvent(event)
