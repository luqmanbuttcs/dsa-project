"""Reusable playing-card widget with click, drag, and drop support."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPainter, QColor, QPen
from PyQt6.QtCore import QMimeData
from PyQt6.QtWidgets import QApplication, QPushButton

from solitaire.domain.card import Card, CardColor


CARD_MIME_TYPE = "application/x-klondike-card"


class CardButton(QPushButton):
    """A visual card that supports selection and drag-and-drop movement."""

    activated = pyqtSignal(str, str)
    drag_started = pyqtSignal(str, str)
    drag_finished = pyqtSignal()
    drop_requested = pyqtSignal(str, str, str)

    CARD_WIDTH = 96
    CARD_HEIGHT = 134

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
        card = self._card
        highlighted = self._selected_highlight or self._drag_highlight
        if not card.face_up:
            border = "#FFD65A" if self._drag_highlight else "#A7D3F5"
            width = "3px" if self._drag_highlight else "2px"
            self.setText("✦\n✦")
            self.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0B68B6, stop:0.48 #064783, stop:1 #032D59); color: #F4FAFF; "
                f"border: {width} solid {border}; border-radius: 9px; "
                "font-size: 22px; font-weight: 800; }"
                "QPushButton:disabled { background: #064783; color: #F4FAFF; }"
            )
            return

        ink = "#D51E35" if card.color is CardColor.RED else "#142332"
        border = "#FFD65A" if highlighted else "#D9E1E5"
        border_width = "3px" if highlighted else "1px"
        self.setText(f"{card.rank.label}\n{card.suit.symbol}")
        self.setStyleSheet(
            "QPushButton { "
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FFFFFF, stop:1 #F4F0E7); color: {ink}; "
            f"border: {border_width} solid {border}; "
            "border-radius: 9px; font-family: Georgia, 'Times New Roman', serif; font-size: 23px; font-weight: 800; "
            "text-align: center; padding: 5px; }"
            "QPushButton:hover { background: #FFFFFF; }"
            f"QPushButton:disabled {{ background: #FFFDF8; color: {ink}; }}"
        )

    def paintEvent(self, event) -> None:
        """Add the fine ornamental frame used by the premium blue card back."""
        super().paintEvent(event)
        if self._card.face_up:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = self.rect().adjusted(5, 5, -5, -5)
        painter.setPen(QPen(QColor("#D8ECFF"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(outer, 7, 7)
        inner = outer.adjusted(5, 5, -5, -5)
        painter.setPen(QPen(QColor("#7CB6EA"), 0.9))
        painter.drawRoundedRect(inner, 5, 5)
        painter.setPen(QPen(QColor("#9BC9F0"), 0.8))
        cx = self.width() // 2
        cy = self.height() // 2
        painter.drawLine(14, 16, self.width() - 14, self.height() - 16)
        painter.drawLine(self.width() - 14, 16, 14, self.height() - 16)
        painter.drawEllipse(cx - 18, cy - 24, 36, 48)
        painter.drawEllipse(cx - 11, cy - 11, 22, 22)
        for y in (18, self.height() - 30):
            for x in (18, self.width() - 30):
                painter.drawEllipse(x, y, 12, 12)
        painter.setPen(QPen(QColor("#FFD65A"), 2.8) if (self._selected_highlight or self._drag_highlight) else QPen(QColor("#FFD65A"), 0))
        if self._selected_highlight or self._drag_highlight:
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 9, 9)
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
