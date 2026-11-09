"""Click-to-select and click-to-move orchestration.

The selection controller stores the currently selected card/run and derives
the legal destinations from the engine (via the game controller). Clicking
a second card either moves the selection (when the rules allow) or moves
the selection marker. QGraphicsItems report clicks here; they never touch
game state themselves.
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class SelectionController(QObject):
    """Tracks the selected card and resolves click-to-move requests."""

    selection_changed = pyqtSignal()

    def __init__(self, game_controller) -> None:
        super().__init__(game_controller)
        self._game = game_controller
        self.source_pile: str | None = None
        self.card_id: str | None = None

    @property
    def has_selection(self) -> bool:
        return self.source_pile is not None

    def legal_destinations(self) -> list[str]:
        if not self.has_selection:
            return []
        return self._game.legal_destinations(self.source_pile, self.card_id)

    def is_selected(self, card_id: str) -> bool:
        return self.card_id == card_id

    def click_card(self, pile_id: str, card_id: str, *, face_up: bool, top_of_pile: bool) -> None:
        """Handle one click on a card in `pile_id`."""
        if not face_up or not top_of_pile:
            self.clear()
            return

        if self.has_selection:
            if self.source_pile != pile_id or self.card_id != card_id:
                # Interpret as a move attempt onto the pile holding this card.
                source, moving = self.source_pile, self.card_id
                if pile_id in self.legal_destinations():
                    self._game.try_move(source, moving, pile_id)
                self.clear()
                return

        if pile_id == "stock":
            self.clear()
            return
        if pile_id == "waste" and not top_of_pile:
            self.clear()
            return

        self.source_pile = pile_id
        self.card_id = card_id
        self.selection_changed.emit()

    def click_pile(self, pile_id: str) -> None:
        """Handle one click on an empty pile slot (drop-by-click)."""
        if self.has_selection and pile_id in self.legal_destinations():
            self._game.try_move(self.source_pile, self.card_id, pile_id)
        self.clear()

    def request_move_to(self, pile_id: str) -> bool:
        """Attempt the current selection's move to `pile_id` (drop resolution)."""
        if not self.has_selection:
            return False
        moved = pile_id in self.legal_destinations() and self._game.try_move(
            self.source_pile, self.card_id, pile_id
        )
        self.clear()
        return moved

    def clear(self) -> None:
        if self.source_pile is None and self.card_id is None:
            return
        self.source_pile = None
        self.card_id = None
        self.selection_changed.emit()
