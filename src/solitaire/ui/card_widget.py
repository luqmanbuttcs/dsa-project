"""Reusable playing-card widget with click, drag, and drop support."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPainter, QColor, QPen, QFont, QLinearGradient
from PyQt6.QtCore import QMimeData
from PyQt6.QtWidgets import QApplication, QPushButton

from solitaire.domain.card import Card, CardColor
from solitaire.ui.theme import paint_card_back


CARD_MIME_TYPE = "application/x-klondike-card"


class CardButton(QPushButton):
    """A visual card that supports selection and drag-and-drop movement."""

    activated = pyqtSignal(str, str)
    drag_started = pyqtSignal(str, str)
    drag_finished = pyqtSignal()
    drop_requested = pyqtSignal(str, str, str)

    CARD_WIDTH = 108
    CARD_HEIGHT = 150

    def __init__(
        self,
        card: Card,
        pile_id: str,
        *,
        clickable: bool = True,
        highlighted: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.card_id = card.card_id
        self.pile_id = pile_id
        self._card = card
        self._selected_highlight = highlighted
        self._drag_highlight = False
        self._press_position: QPoint | None = None
        self._drag_in_progress = False
        self._suppress_next_click = False
        self._draggable = (
            clickable and (pile_id == "waste" or pile_id.startswith("tableau-"))
        )
        self.setObjectName(f"card-{card.card_id}")
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(
            Qt.CursorShape.OpenHandCursor
            if self._draggable
            else Qt.CursorShape.PointingHandCursor
            if clickable else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus if clickable else Qt.FocusPolicy.NoFocus
        )
        self.setEnabled(clickable)
        self.setAcceptDrops(pile_id.startswith("tableau-"))
        self.setAccessibleName(
            f"{card.rank.label} of {card.suit.value}, "
            f"{'face up' if card.face_up else 'face down'}"
        )
        self.clicked.connect(self._emit_activated)
        self.update_card(card, highlighted=highlighted)

    def update_card(self, card: Card, *, highlighted: bool = False) -> None:
        """Refresh face, color, and selection styling from the domain card."""
        self._card = card
        self._selected_highlight = highlighted
        self._apply_card_style()

    def set_drag_highlight(self, highlighted: bool) -> None:
        """Highlight this card when its tableau column is a legal drop target."""
        self._drag_highlight = highlighted
        self._apply_card_style()

    def _apply_card_style(self) -> None:
        """Keep semantic text for accessibility/tests; render the card face ourselves."""
        card = self._card
        if not card.face_up:
            self.setText("✦\n✦")
        else:
            self.setText(f"{card.rank.label}\n{card.suit.symbol}")
        self.setStyleSheet(
            "QPushButton { background: transparent; color: transparent; "
            "border: none; padding: 0; }"
            "QPushButton:hover { background: transparent; }"
            "QPushButton:disabled { background: transparent; color: transparent; }"
        )
        self.update()

    def paintEvent(self, event) -> None:
        """Paint full-size premium playing cards and ornamental blue card backs."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._card.face_up:
            paint_card_back(
                painter,
                QRectF(self.rect()),
                selected=self._selected_highlight or self._drag_highlight,
                radius=9.0,
            )
            painter.end()
            return

        bounds = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        radius = 9.0
        # Soft, built-in shadow; no external image or graphics dependency.
        shadow = bounds.translated(0, 2)
        shadow_path = __import__("PyQt6.QtGui", fromlist=["QPainterPath"]).QPainterPath()
        shadow_path.addRoundedRect(shadow, radius, radius)
        painter.fillPath(shadow_path, QColor(0, 14, 24, 90))

        card_path = __import__("PyQt6.QtGui", fromlist=["QPainterPath"]).QPainterPath()
        card_path.addRoundedRect(bounds, radius, radius)
        face_gradient = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
        face_gradient.setColorAt(0.0, QColor("#FFFFFF"))
        face_gradient.setColorAt(1.0, QColor("#F1EDE3"))
        painter.fillPath(card_path, face_gradient)
        painter.setPen(QPen(QColor("#D8D5CC"), 1.0))
        painter.drawPath(card_path)

        ink = QColor("#D51E35") if self._card.color is CardColor.RED else QColor("#101923")
        rank_font = QFont("Georgia", 18, QFont.Weight.Bold)
        painter.setFont(rank_font)
        painter.setPen(ink)
        painter.drawText(
            QRectF(bounds.left() + 8, bounds.top() + 5, 34, 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._card.rank.label,
        )
        suit_small = QFont("Segoe UI Symbol", 17, QFont.Weight.Bold)
        painter.setFont(suit_small)
        painter.drawText(
            QRectF(bounds.left() + 8, bounds.top() + 26, 31, 25),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._card.suit.symbol,
        )

        central_font = QFont("Segoe UI Symbol", 67, QFont.Weight.Bold)
        painter.setFont(central_font)
        painter.drawText(
            QRectF(bounds.left() + 17, bounds.top() + 37, bounds.width() - 34, bounds.height() - 48),
            Qt.AlignmentFlag.AlignCenter,
            self._card.suit.symbol,
        )

        # A small mirrored corner index gives the card a traditional casino-deck finish.
        painter.save()
        painter.translate(bounds.right() - 9, bounds.bottom() - 8)
        painter.rotate(180)
        painter.setFont(QFont("Georgia", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, 27, 17), Qt.AlignmentFlag.AlignLeft, self._card.rank.label)
        painter.setFont(QFont("Segoe UI Symbol", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(1, 13, 24, 15), Qt.AlignmentFlag.AlignLeft, self._card.suit.symbol)
        painter.restore()

        if self._selected_highlight or self._drag_highlight:
            painter.setPen(QPen(QColor(255, 199, 55, 85), 7.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(bounds.adjusted(1, 1, -1, -1), radius, radius)
            painter.setPen(QPen(QColor("#FFD65A"), 2.4))
            painter.drawRoundedRect(bounds.adjusted(2, 2, -2, -2), radius, radius)
        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() is Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
            self._suppress_next_click = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            self._draggable
            and self.isEnabled()
            and self._press_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and (event.position().toPoint() - self._press_position).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._start_drag()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._suppress_next_click:
            self._suppress_next_click = False
            self._press_position = None
            self.setDown(False)
            event.accept()
            return
        self._press_position = None
        super().mouseReleaseEvent(event)

    def _start_drag(self) -> None:
        self._drag_in_progress = True
        self._suppress_next_click = True
        self.setDown(False)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.drag_started.emit(self.card_id, self.pile_id)

        mime = QMimeData()
        payload = f"{self.card_id}\t{self.pile_id}".encode("utf-8")
        mime.setData(CARD_MIME_TYPE, QByteArray(payload))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self.rect().center())
        drag.exec(Qt.DropAction.MoveAction)

        self._drag_in_progress = False
        self._press_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_finished.emit()

    @staticmethod
    def _drag_payload(event) -> tuple[str, str] | None:
        mime = event.mimeData()
        if not mime.hasFormat(CARD_MIME_TYPE):
            return None
        try:
            card_id, source_pile = bytes(mime.data(CARD_MIME_TYPE)).decode(
                "utf-8"
            ).split("\t", 1)
        except (UnicodeDecodeError, ValueError):
            return None
        return card_id, source_pile

    def dragEnterEvent(self, event) -> None:
        payload = self._drag_payload(event)
        if payload and payload[1] != self.pile_id:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        # Legal targets remain highlighted for the entire drag session.
        event.accept()

    def dropEvent(self, event) -> None:
        self.set_drag_highlight(False)
        payload = self._drag_payload(event)
        if payload and payload[1] != self.pile_id:
            self.drop_requested.emit(payload[0], payload[1], self.pile_id)
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def _emit_activated(self) -> None:
        self.activated.emit(self.card_id, self.pile_id)
