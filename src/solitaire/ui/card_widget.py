"""Reusable card button widget for the Klondike board."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton

from solitaire.domain.card import Card, CardColor


class CardButton(QPushButton):
    """A visual card that reports its card ID and source pile when activated."""

    activated = pyqtSignal(str, str)

    CARD_WIDTH = 80
    CARD_HEIGHT = 112

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
        self.setObjectName(f"card-{card.card_id}")
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if clickable else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus if clickable else Qt.FocusPolicy.NoFocus)
        self.setEnabled(clickable)
        self.setAccessibleName(
            f"{card.rank.label} of {card.suit.value}, "
            f"{'face up' if card.face_up else 'face down'}"
        )
        self.clicked.connect(self._emit_activated)
        self.update_card(card, highlighted=highlighted)

    def update_card(self, card: Card, *, highlighted: bool = False) -> None:
        """Refresh face, color, and selection styling from the domain card."""
        if not card.face_up:
            self.setText("✦\n✦")
            self.setStyleSheet(
                "QPushButton { background: #123D5C; color: #E8F1F8; "
                "border: 2px solid #AFC1D0; border-radius: 8px; "
                "font-size: 22px; font-weight: 700; }"
                "QPushButton:disabled { background: #123D5C; color: #D8E3EC; }"
            )
            return

        ink = "#C8344B" if card.color is CardColor.RED else "#172B3A"
        border = "#F5C84C" if highlighted else "#D5DFE5"
        border_width = "3px" if highlighted else "1px"
        self.setText(f"{card.rank.label}\n{card.suit.symbol}")
        self.setStyleSheet(
            "QPushButton { "
            f"background: #FFFDF8; color: {ink}; "
            f"border: {border_width} solid {border}; "
            "border-radius: 8px; font-size: 20px; font-weight: 800; "
            "text-align: center; padding: 5px; }"
            "QPushButton:hover { background: #F4F0E6; }"
            "QPushButton:disabled { background: #FFFDF8; color: " + ink + "; }"
        )

    def _emit_activated(self) -> None:
        self.activated.emit(self.card_id, self.pile_id)
