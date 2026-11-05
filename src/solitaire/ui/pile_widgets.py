"""Widgets that render the stock, waste, foundations, and tableau columns."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from solitaire.domain.card import Card, Suit
from solitaire.domain.game_state import TableauColumn
from solitaire.ui.card_widget import CardButton
from solitaire.ui.theme import paint_card_back


CARD_WIDTH = CardButton.CARD_WIDTH
CARD_HEIGHT = CardButton.CARD_HEIGHT


class StockButton(QPushButton):
    """Clickable stock/recycle pile with a visible remaining-card count."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("stock-button")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT + 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._stock_count = 24
        self._can_recycle = False
        self.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1679C5, stop:0.48 #07539A, stop:1 #032C59); "
            "color: #FFFFFF; border: 2px solid #D8ECFF; border-radius: 9px; "
            "font-size: 29px; font-weight: 800; padding: 5px; }"
            "QPushButton:hover { border: 2px solid #FFD65A; }"
            "QPushButton:disabled { color: #A9C1D5; border-color: #6687A5; }"
        )

    def set_stock(self, count: int, can_recycle: bool) -> None:
        self._stock_count = count
        self._can_recycle = can_recycle
        if count:
            self.setText(f"♠\n\n{count}")
            self.setAccessibleName(f"Stock pile, {count} cards. Click to draw.")
            self.setEnabled(True)
        elif can_recycle:
            self.setText("↻\n\nRecycle")
            self.setAccessibleName("Recycle waste into stock and draw.")
            self.setEnabled(True)
        else:
            self.setText("Empty")
            self.setAccessibleName("Stock and waste are empty.")
            self.setEnabled(False)


class WasteWidget(QWidget):
    """Shows up to the three newest waste cards; only the top card is active."""

    card_selected = pyqtSignal(str, str)
    card_drag_started = pyqtSignal(str, str)
    card_drag_finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("waste-widget")
        self.setMinimumSize(CARD_WIDTH + 98, CARD_HEIGHT)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(-67)
        self._buttons: list[CardButton] = []

    def set_cards(self, cards: list[Card]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._buttons.clear()

        visible_cards = cards[-3:]
        for index, card in enumerate(visible_cards):
            is_top = index == len(visible_cards) - 1
            button = CardButton(card, "waste", clickable=is_top)
            button.setAccessibleName(
                f"{card.rank.label} of {card.suit.value}"
                + (", top waste card" if is_top else ", covered waste card")
            )
            if is_top:
                button.activated.connect(self.card_selected.emit)
                button.drag_started.connect(self.card_drag_started.emit)
                button.drag_finished.connect(self.card_drag_finished.emit)
            self._layout.addWidget(button)
            self._buttons.append(button)


    @property
    def card_buttons(self) -> tuple[CardButton, ...]:
        return tuple(self._buttons)


class FoundationSlot(QWidget):
    """Displays one suit foundation and acts as a click-to-place target."""

    selected = pyqtSignal(object)
    card_dropped = pyqtSignal(str, str, str)

    def __init__(self, suit: Suit, parent=None) -> None:
        super().__init__(parent)
        self.suit = suit
        self.setObjectName(f"foundation-{suit.code.lower()}")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self._button: QPushButton | CardButton | None = None
        self._base_button_style = ""
        self._drag_highlighted = False
        self.setAcceptDrops(True)
        self.set_card(None)

    def set_card(self, card: Card | None) -> None:
        if self._button is not None:
            self._button.deleteLater()
            self._button = None

        if card is None:
            button = QPushButton(self.suit.symbol)
            button.setObjectName(f"empty-foundation-{self.suit.code.lower()}")
            ink = "#FF6677" if self.suit in (Suit.HEARTS, Suit.DIAMONDS) else "#A5E8C0"
            button.setStyleSheet(
                "QPushButton { "
                f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(15, 88, 48, 0.76), stop:1 rgba(0, 43, 25, 0.90)); color: {ink}; "
                "border: 2px solid rgba(120, 255, 105, 0.94); "
                "border-radius: 10px; font-size: 40px; font-weight: 800; }"
                "QPushButton:hover { border: 3px solid #FFD65A; background: rgba(13, 93, 48, 0.82); }"
            )
            button.setAccessibleName(f"Empty {self.suit.value} foundation. Click to place a card.")
        else:
            button = CardButton(card, f"foundation-{self.suit.code.lower()}", clickable=True)
            button.setAccessibleName(f"{card.rank.label} of {card.suit.value} foundation. Click to add a card.")

        button.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        button.setAcceptDrops(False)
        button.clicked.connect(lambda: self.selected.emit(self.suit))
        self._button = button
        self._base_button_style = button.styleSheet()
        self._apply_drop_style()
        button.setParent(self)
        button.setGeometry(0, 0, CARD_WIDTH, CARD_HEIGHT)
        button.show()

    def set_drag_highlight(self, highlighted: bool) -> None:
        self._drag_highlighted = highlighted
        self._apply_drop_style()

    def _apply_drop_style(self) -> None:
        if self._button is None:
            return
        highlight_style = (
            " QPushButton { border: 3px solid #FFD65A; }"
            if self._drag_highlighted else ""
        )
        self._button.setStyleSheet(self._base_button_style + highlight_style)

    def dragEnterEvent(self, event) -> None:
        payload = CardButton._drag_payload(event)
        if payload and payload[1] != f"foundation-{self.suit.code.lower()}":
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.set_drag_highlight(False)
        event.accept()

    def dropEvent(self, event) -> None:
        self.set_drag_highlight(False)
        payload = CardButton._drag_payload(event)
        if payload and payload[1] != f"foundation-{self.suit.code.lower()}":
            self.card_dropped.emit(
                payload[0], payload[1], f"foundation-{self.suit.code.lower()}"
            )
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()


class TableauColumnWidget(QWidget):
    """Renders a tableau Stack vertically with clickable face-up cards."""

    card_selected = pyqtSignal(str, str)
    empty_selected = pyqtSignal(str)
    card_dropped = pyqtSignal(str, str, str)
    card_drag_started = pyqtSignal(str, str)
    card_drag_finished = pyqtSignal()

    FACE_DOWN_OFFSET = 27
    FACE_UP_OFFSET = 40

    def __init__(self, column_id: str, parent=None) -> None:
        super().__init__(parent)
        self.column_id = column_id
        self.setObjectName(f"tableau-column-{column_id.rsplit('-', 1)[-1]}")
        self.setMinimumWidth(CARD_WIDTH)
        self.setFixedWidth(CARD_WIDTH)
        self.setMinimumHeight(CARD_HEIGHT)
        self._buttons: list[CardButton] = []
        self._is_empty = True
        self._drag_highlighted = False
        self.setAcceptDrops(True)

    def set_column(
        self,
        column: TableauColumn,
        selected_card_id: str | None = None,
    ) -> None:
        for button in self._buttons:
            button.deleteLater()
        self._buttons.clear()

        cards = column.cards_bottom_to_top()
        self._is_empty = not cards
        if not cards:
            self.setFixedHeight(CARD_HEIGHT)
            self.update()
            return

        selected_index = next(
            (index for index, card in enumerate(cards) if card.card_id == selected_card_id),
            None,
        )
        y_position = 0
        last_top = 0
        for index, card in enumerate(cards):
            last_top = y_position
            in_selected_run = selected_index is not None and index >= selected_index
            button = CardButton(
                card,
                self.column_id,
                clickable=card.face_up,
                highlighted=in_selected_run,
                parent=self,
            )
            if card.face_up:
                button.activated.connect(self.card_selected.emit)
                button.drag_started.connect(self.card_drag_started.emit)
                button.drag_finished.connect(self.card_drag_finished.emit)
            button.drop_requested.connect(self.card_dropped.emit)
            if self._drag_highlighted:
                button.set_drag_highlight(True)
            button.setGeometry(0, y_position, CARD_WIDTH, CARD_HEIGHT)
            button.show()
            button.raise_()
            self._buttons.append(button)
            y_position += (
                self.FACE_UP_OFFSET if card.face_up else self.FACE_DOWN_OFFSET
            )

        total_height = max(CARD_HEIGHT, last_top + CARD_HEIGHT)
        self.setFixedHeight(total_height)
        self.update()

    @property
    def card_buttons(self) -> tuple[CardButton, ...]:
        return tuple(self._buttons)

    def set_drag_highlight(self, highlighted: bool) -> None:
        self._drag_highlighted = highlighted
        for button in self._buttons:
            button.set_drag_highlight(highlighted)

    def dragEnterEvent(self, event) -> None:
        payload = CardButton._drag_payload(event)
        if payload and payload[1] != self.column_id:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.set_drag_highlight(False)
        event.accept()

    def dropEvent(self, event) -> None:
        self.set_drag_highlight(False)
        payload = CardButton._drag_payload(event)
        if payload and payload[1] != self.column_id:
            self.card_dropped.emit(
                payload[0], payload[1], self.column_id
            )
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            return
        event.ignore()

    def mousePressEvent(self, event) -> None:
        if self._is_empty and event.button() is Qt.MouseButton.LeftButton:
            self.empty_selected.emit(self.column_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        if not self._is_empty:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#8AF28B"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, CARD_WIDTH - 2, CARD_HEIGHT - 2, 8, 8)
        painter.end()
