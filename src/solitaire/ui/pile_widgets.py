"""Widgets that render the stock, waste, foundations, and tableau columns."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from solitaire.domain.card import Card, Suit
from solitaire.domain.game_state import TableauColumn
from solitaire.ui.card_widget import CardButton


CARD_WIDTH = CardButton.CARD_WIDTH
CARD_HEIGHT = CardButton.CARD_HEIGHT


class StockButton(QPushButton):
    """Clickable stock/recycle pile with a visible remaining-card count."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("stock-button")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            "QPushButton { background: #123D5C; color: #F4F7FA; "
            "border: 2px solid #B9C7D3; border-radius: 8px; "
            "font-size: 16px; font-weight: 700; }"
            "QPushButton:hover { border: 2px solid #F5C84C; }"
            "QPushButton:disabled { color: #A9B9C5; border-color: #6B7D88; }"
        )

    def set_stock(self, count: int, can_recycle: bool) -> None:
        if count:
            self.setText(f"✦\n\n{count}")
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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("waste-widget")
        self.setMinimumSize(CARD_WIDTH * 3 + 16, CARD_HEIGHT)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(-48)
        self._buttons: list[CardButton] = []

    def set_cards(self, cards: list[Card]) -> None:
        for button in self._buttons:
            self._layout.removeWidget(button)
            button.deleteLater()
        self._buttons.clear()

        visible_cards = cards[-3:]
        for index, card in enumerate(visible_cards):
            is_top = index == len(visible_cards) - 1
            button = CardButton(card, "waste", clickable=is_top)
            button.setAccessibleName(
                f"{card.rank.label} of {card.suit.value}"
                + (", top waste card" if is_top else ", covered waste card")
            )
            self._layout.addWidget(button)
            self._buttons.append(button)

        self._layout.addStretch(1)

    @property
    def card_buttons(self) -> tuple[CardButton, ...]:
        return tuple(self._buttons)


class FoundationSlot(QWidget):
    """Displays one suit foundation and acts as a click-to-place target."""

    selected = pyqtSignal(object)

    def __init__(self, suit: Suit, parent=None) -> None:
        super().__init__(parent)
        self.suit = suit
        self.setObjectName(f"foundation-{suit.code.lower()}")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self._button: QPushButton | CardButton | None = None
        self.set_card(None)

    def set_card(self, card: Card | None) -> None:
        if self._button is not None:
            self._button.deleteLater()
            self._button = None

        if card is None:
            button = QPushButton(self.suit.symbol)
            button.setObjectName(f"empty-foundation-{self.suit.code.lower()}")
            ink = "#C8344B" if self.suit in (Suit.HEARTS, Suit.DIAMONDS) else "#E6EEF4"
            button.setStyleSheet(
                "QPushButton { "
                f"background: rgba(3, 38, 25, 0.18); color: {ink}; "
                "border: 2px dashed rgba(230, 241, 235, 0.55); "
                "border-radius: 8px; font-size: 32px; font-weight: 700; }"
                "QPushButton:hover { border: 2px solid #F5C84C; }"
            )
            button.setAccessibleName(f"Empty {self.suit.value} foundation. Click to place a card.")
        else:
            button = CardButton(card, f"foundation-{self.suit.code.lower()}", clickable=True)
            button.setAccessibleName(f"{card.rank.label} of {card.suit.value} foundation. Click to add a card.")

        button.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        button.clicked.connect(lambda: self.selected.emit(self.suit))
        self._button = button
        button.setParent(self)
        button.setGeometry(0, 0, CARD_WIDTH, CARD_HEIGHT)
        button.show()


class TableauColumnWidget(QWidget):
    """Renders a tableau Stack vertically with clickable face-up cards."""

    card_selected = pyqtSignal(str, str)
    empty_selected = pyqtSignal(str)

    FACE_DOWN_OFFSET = 22
    FACE_UP_OFFSET = 28

    def __init__(self, column_id: str, parent=None) -> None:
        super().__init__(parent)
        self.column_id = column_id
        self.setObjectName(f"tableau-column-{column_id.rsplit('-', 1)[-1]}")
        self.setMinimumWidth(CARD_WIDTH)
        self.setFixedWidth(CARD_WIDTH)
        self.setMinimumHeight(CARD_HEIGHT)
        self._buttons: list[CardButton] = []
        self._is_empty = True

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
        for index, card in enumerate(cards):
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
            button.setGeometry(0, y_position, CARD_WIDTH, CARD_HEIGHT)
            button.show()
            button.raise_()
            self._buttons.append(button)
            y_position += (
                self.FACE_UP_OFFSET if card.face_up else self.FACE_DOWN_OFFSET
            )

        total_height = max(CARD_HEIGHT, y_position - self.FACE_UP_OFFSET)
        self.setFixedHeight(total_height)
        self.update()

    @property
    def card_buttons(self) -> tuple[CardButton, ...]:
        return tuple(self._buttons)

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
        pen = QPen(Qt.GlobalColor.white)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, CARD_WIDTH - 2, CARD_HEIGHT - 2, 8, 8)
        painter.end()
