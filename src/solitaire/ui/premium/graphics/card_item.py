"""Premium interactive playing-card graphics item.

Rendering rules (per the approved reference):
- warm ivory surface, rounded corners, refined border, soft drop shadow;
- rank top-left with a small suit symbol, mirrored index bottom-right;
- ONE oversized central suit illustration for Ace through 10;
- bundled SVG court illustrations for Jack, Queen and King;
- bundled royal-blue ornate back for face-down cards;
- gold selection glow and hint glow driven by animatable properties.

Interaction feel (game-feel upgrade):
- hover lifts the card off the felt with a softening shadow;
- selected runs float slightly above the table;
- drags are *manual* (no QDrag): the grabbed run follows the pointer
  one-to-one with a velocity tilt and a floating shadow, so the card
  never lags behind the mouse;
- landing cards pop with a tiny spring.

Identity: one item per real card, keyed by `card.card_id`. Items are
reused across scene refreshes and never mutate game state.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QGraphicsObject

from solitaire.domain.card import Card, Rank
from solitaire.ui.premium import resources
from solitaire.ui.premium.graphics.effects.highlights import paint_card_shadow, paint_glow
from solitaire.ui.premium.theme import CARD_H, CARD_RADIUS, CARD_W

DRAG_THRESHOLD = 12.0
HOVER_LIFT_PX = 4.0
DRAG_LIFT_PX = 10.0
MAX_TILT_DEG = 6.0

IVORY_TOP = "#FDF9EE"
IVORY_BOTTOM = "#EFE4C6"
BORDER = "#C4B58E"
RED = "#C62828"
INK = "#1B1E26"

SELECT_GOLD = QColor(240, 199, 94)
SELECT_MINT = QColor(64, 224, 178)
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
        self._hover_lift = 0.0
        self._drag_lift = 0.0
        self._drag_tilt = 0.0
        self._pop_scale = 0.0
        self._interactive = True
        self.on_clicked = None  # callback(item) wired by the scene
        self.drag_provider = None  # callback(card_id) -> (card_ids, pile) | None
        # Manual-drag hooks, wired by the scene: begin/move/finish.
        self.on_drag_started = None
        self.on_drag_moved = None
        self.on_drag_dropped = None
        self.on_drag_cancelled = None
        self._press_pos: QPoint | None = None
        self._dragging = False
        # One live QPropertyAnimation per float property (see
        # _animate_property): the registry lets a new animation retire the
        # previous writer and lets tests scrub timelines deterministically.
        self._property_animations: dict[str, QPropertyAnimation] = {}
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
            self._hover_lift = 0.0
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

    def get_hover_lift(self) -> float:
        return self._hover_lift

    def set_hover_lift(self, value: float) -> None:
        self._hover_lift = max(0.0, min(1.0, float(value)))
        self.update()

    hover_lift = pyqtProperty(float, get_hover_lift, set_hover_lift)

    def get_drag_lift(self) -> float:
        return self._drag_lift

    def set_drag_lift(self, value: float) -> None:
        self._drag_lift = max(0.0, min(1.0, float(value)))
        self.update()

    drag_lift = pyqtProperty(float, get_drag_lift, set_drag_lift)

    def get_drag_tilt(self) -> float:
        return self._drag_tilt

    def set_drag_tilt(self, value: float) -> None:
        self._drag_tilt = max(-1.0, min(1.0, float(value)))
        self.update()

    drag_tilt = pyqtProperty(float, get_drag_tilt, set_drag_tilt)

    def get_pop_scale(self) -> float:
        return self._pop_scale

    def set_pop_scale(self, value: float) -> None:
        self._pop_scale = max(0.0, min(1.0, float(value)))
        self.update()

    pop_scale = pyqtProperty(float, get_pop_scale, set_pop_scale)

    # --- small self-owned animations (destroyed with the item) --------------
    @staticmethod
    def _scaled_ms(ms: int) -> int:
        """Follow the user's animation-speed multiplier like the manager.

        The lift/hover/tilt/error timelines are owned by the item itself, so
        they must apply the same speed semantics as CardAnimationManager
        (divide by the multiplier) or the Settings control would leave these
        motions at raw speed while everything else speeds up.
        """
        from solitaire.ui.premium.animations.card_animation_manager import (
            CardAnimationManager,
        )

        return CardAnimationManager.instance().duration_for(ms)

    def _animate_property(self, name: str, target: float, ms: int) -> None:
        """Animate one of this item's own float properties.

        The QPropertyAnimation is parented to *this item*, so it can never
        outlive its target — no orphaned animation can write into a dying
        C++ object (the historical exit-134 abort family).

        Exactly one timeline may own a property at a time. Qt >= 6.8 already
        stops a previous QPropertyAnimation on the same target + property
        when a new one starts; retiring it here makes that guarantee
        explicit and version-independent, and ``deleteLater()`` releases the
        retired timeline instead of letting finished animations accumulate
        as children of the item for its whole lifetime. The registry also
        lets tests drive the timeline with ``setCurrentTime()``
        deterministically instead of racing the wall clock (whose coarse
        timer granularity differs per platform).
        """
        previous = self._property_animations.pop(name, None)
        if previous is not None:
            try:
                previous.stop()
                previous.deleteLater()
            except RuntimeError:
                pass  # already destroyed with a dying C++ object
        try:
            animation = QPropertyAnimation(self, name.encode(), self)
            animation.setDuration(self._scaled_ms(ms))
            animation.setStartValue(getattr(self, f"get_{name}")())
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._property_animations[name] = animation
            animation.start()
        except RuntimeError:
            pass  # target destroyed between calls; nothing left to animate

    def animate_hover(self, lifted: bool) -> None:
        if not self._interactive and lifted:
            return
        self._animate_property("hover_lift", 1.0 if lifted else 0.0, 130)

    def animate_drag_lift(self, lifted: bool) -> None:
        self._animate_property("drag_lift", 1.0 if lifted else 0.0, 140)

    def animate_tilt(self, tilt: float, ms: int = 90) -> None:
        self._animate_property("drag_tilt", tilt, ms)

    def animate_error(self) -> None:
        """Coral warning ring that flashes once and fades out."""
        self._animate_property("error_pulse", 1.0, 40)
        QTimer.singleShot(
            60, lambda target=self: target._animate_property("error_pulse", 0.0, 420)
        )

    # --- manual drag session (driven by the scene) ---------------------------
    def begin_drag_session(self) -> None:
        self._dragging = True
        self._press_pos = None
        self.animate_drag_lift(True)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def end_drag_session(self) -> None:
        self._dragging = False
        self.animate_drag_lift(False)
        self.animate_tilt(0.0, 140)
        self.unsetCursor()

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
        # Covers hover/drag lift, pop scale (4%) and the 6-degree drag tilt.
        return QRectF(-16.0, -18.0, CARD_W + 32.0, CARD_H + 34.0)

    def shape(self) -> QPainterPath:
        """Use the visible card face for hit testing, not the shadow bounds.

        ``boundingRect`` deliberately includes a generous shadow/lift margin
        for painting and scene indexing. Using Qt's default shape (the whole
        bounding rectangle) lets an upper card's invisible shadow margin
        steal clicks from the exposed strip of the card below it. That makes
        lower cards in a face-up run difficult to grab reliably.
        """
        path = QPainterPath()
        path.addRoundedRect(self.rect(), CARD_RADIUS, CARD_RADIUS)
        return path

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

        # --- depth transforms: lift, tilt and settle pop --------------------
        lift = self._hover_lift * HOVER_LIFT_PX + self._drag_lift * DRAG_LIFT_PX
        selected_extra = self._highlight * 2.0
        total_lift = lift + selected_extra
        tilt_deg = self._drag_tilt * MAX_TILT_DEG
        scale = 1.0 + 0.05 * self._pop_scale

        shadow_boost = max(self._hover_lift, self._drag_lift)
        if abs(tilt_deg) > 0.05 or scale != 1.0 or total_lift > 0.01:
            center = rect.center()
            painter.translate(center.x(), center.y() - total_lift)
            painter.rotate(tilt_deg)
            painter.scale(scale, scale)
            rect = QRectF(-CARD_W / 2.0, -CARD_H / 2.0, float(CARD_W), float(CARD_H))
        elif total_lift > 0.01:
            painter.translate(0.0, -total_lift)

        if 0.0001 < progress < 0.9999:
            # Mid-flip: squeeze horizontally and switch the face at 50%.
            squeeze = abs(1.0 - 2.0 * progress)
            painter.translate(rect.center())
            painter.scale(max(0.04, squeeze), 1.0)
            painter.translate(-rect.center().x(), -rect.center().y())

        show_back = progress >= 0.5
        paint_card_shadow(painter, rect, CARD_RADIUS, boost=shadow_boost)
        if show_back:
            self._paint_back(painter, rect)
        else:
            self._paint_face(painter, rect)

        if self._highlight > 0.01:
            glow_color = SELECT_MINT if self._dragging else SELECT_GOLD
            paint_glow(painter, rect, CARD_RADIUS, glow_color, self._highlight)
            painter.setPen(QPen(glow_color, 2.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, CARD_RADIUS, CARD_RADIUS)
        if self._hint > 0.01:
            painter.setPen(QPen(HINT_GOLD, 3.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), CARD_RADIUS, CARD_RADIUS)
        if self._error_pulse > 0.01:
            painter.setPen(QPen(QColor(235, 87, 87, int(215 * self._error_pulse)), 3.0))
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
            self.animate_hover(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        self.unsetCursor()
        self.animate_hover(False)
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
        """Begin a manual drag once the press becomes a deliberate move.

        The card itself follows the pointer one-to-one (see the scene's
        drag session) — no QDrag hand-off, so the card can never lag the
        cursor and the run stays visually complete while moving.
        """
        if (
            self._interactive
            and self._press_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and self.on_drag_started is not None
            and not self._dragging
        ):
            distance = (event.pos().toPoint() - self._press_pos).manhattanLength()
            if distance >= DRAG_THRESHOLD:
                self._press_pos = None
                self.on_drag_started(self, event.scenePos())
                if self._dragging:
                    event.accept()
                    return
        if self._dragging and self.on_drag_moved is not None:
            self.on_drag_moved(self, event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._interactive and event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                if self.on_drag_dropped is not None:
                    self.on_drag_dropped(self, event.scenePos())
                event.accept()
                return
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
