"""GameController: the single boundary between the premium UI and the
existing GameEngine.

The controller never re-implements game rules. Every mutation is delegated
to `GameEngine`, which validates, executes, records real OperationTracker
events and raises on invalid input. The controller only:

1. forwards player intent (draw / move / undo / redo / hint / new game),
2. translates engine results into Qt signals and presentation data,
3. owns presentation-only concerns (the elapsed-time clock, feedback text).

If a move is invalid the engine raises `InvalidMoveError` before mutating
anything, the controller emits an error feedback signal, and the game state
stays untouched.
"""

from __future__ import annotations

import random
from typing import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from solitaire.domain.card import Card, Suit
from solitaire.domain.game_engine import GameEngine, InvalidMoveError, NoCardsAvailableError
from solitaire.domain.game_state import GameState, GameStatus, Zone, create_new_game
from solitaire.domain.operations import OperationTracker, StructureName
from solitaire.domain.rules import MoveError, ValidationResult

PILE_LABELS = {
    "stock": "Stock",
    "waste": "Waste",
}

FEEDBACK_SUCCESS = "success"
FEEDBACK_ERROR = "error"
FEEDBACK_INFO = "info"
FEEDBACK_VICTORY = "victory"


def pretty_pile(pile_id: str) -> str:
    """Human label for a pile identifier ('tableau-6' -> 'Column 6')."""
    if pile_id.startswith("tableau-"):
        return f"Column {pile_id.rsplit('-', 1)[1]}"
    if pile_id.startswith("foundation-"):
        code = pile_id.rsplit("-", 1)[1].upper()
        names = {"H": "Hearts", "D": "Diamonds", "C": "Clubs", "S": "Spades"}
        return f"{names.get(code, code)} Foundation"
    return PILE_LABELS.get(pile_id, pile_id)


def describe_move(event) -> str:
    """Compact readable notation for a move-history event.

    Replaces raw pile identifiers ('tableau-4', 'foundation-s') with the
    player-facing labels used by the Move Log, so every panel in the UI
    speaks the same notation ('Column 4', 'Spades Foundation').
    """
    description = event.description
    for pile_id in (getattr(event, "source_pile", None), getattr(event, "destination_pile", None)):
        if pile_id:
            description = description.replace(pile_id, pretty_pile(pile_id))
    return description


def foundation_suit_for(pile_id: str) -> Suit:
    """Map 'foundation-h' to Suit.HEARTS."""
    code = pile_id.rsplit("-", 1)[1].upper()
    for suit in Suit:
        if suit.code == code:
            return suit
    raise ValueError(f"unknown foundation pile: {pile_id}")


def _missing_card_error() -> InvalidMoveError:
    return InvalidMoveError(ValidationResult.reject(MoveError.CARD_NOT_FOUND))


class GameController(QObject):
    """Qt boundary in front of the untouched domain layer."""

    state_changed = pyqtSignal(str)
    operations_changed = pyqtSignal()
    move_logged = pyqtSignal(object)
    feedback = pyqtSignal(str, str, str)
    game_won = pyqtSignal()
    tick = pyqtSignal(int)

    def __init__(self, parent: QObject | None = None, seed: int | None = None) -> None:
        super().__init__(parent)
        self._seed = seed
        self._tracker = OperationTracker()
        self._engine: GameEngine | None = None
        self._state: GameState | None = None
        self._elapsed_seconds = 0
        self._clock_running = False

        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._on_clock_tick)

        self.new_game(draw_count=1, announce=False)

    # --- properties -------------------------------------------------------
    @property
    def engine(self) -> GameEngine:
        return self._engine  # type: ignore[return-value]

    @property
    def state(self) -> GameState:
        return self._state  # type: ignore[return-value]

    @property
    def tracker(self) -> OperationTracker:
        return self._tracker

    @property
    def can_undo(self) -> bool:
        return self._engine.can_undo

    @property
    def can_redo(self) -> bool:
        return self._engine.can_redo

    @property
    def draw_mode(self) -> int:
        return self._state.draw_count

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed_seconds

    @property
    def is_won(self) -> bool:
        return self._state.status is GameStatus.WON

    # --- lifecycle --------------------------------------------------------
    def new_game(self, draw_count: int = 1, announce: bool = True) -> None:
        rng = random.Random(self._seed) if self._seed is not None else None
        self._tracker.clear()
        self._state = create_new_game(rng=rng, draw_count=draw_count, tracker=self._tracker)
        self._engine = GameEngine(self._state, self._tracker)
        self._elapsed_seconds = 0
        self._clock.stop()
        self._clock_running = False
        self.operations_changed.emit()
        self.state_changed.emit("new-game")
        if announce:
            self.feedback.emit(
                "New Game",
                f"A fresh deck is on the table. Draw {draw_count} mode.",
                FEEDBACK_INFO,
            )

    def set_draw_mode(self, count: int) -> None:
        if count == self._state.draw_count:
            return
        self._engine.set_draw_count(count)
        self.feedback.emit(
            "Settings",
            f"Draw {count} mode enabled.",
            FEEDBACK_INFO,
        )
        self.state_changed.emit("draw-mode")

    # --- clock ------------------------------------------------------------
    def _on_clock_tick(self) -> None:
        if self._state.status is GameStatus.PLAYING:
            self._elapsed_seconds += 1
            self.tick.emit(self._elapsed_seconds)

    def _ensure_clock(self) -> None:
        if not self._clock_running:
            self._clock.start()
            self._clock_running = True

    # --- player actions ---------------------------------------------------
    def draw_from_stock(self) -> None:
        try:
            drawn = self._engine.draw_from_stock()
        except NoCardsAvailableError as error:
            # Invalid action: the game clock must NOT start.
            self.feedback.emit("No Cards Left", str(error), FEEDBACK_ERROR)
            return
        except InvalidMoveError as error:  # pragma: no cover - defensive
            self.feedback.emit("Invalid Draw", str(error), FEEDBACK_ERROR)
            return

        self._ensure_clock()
        noun = "card" if len(drawn) == 1 else "cards"
        self.feedback.emit(
            "Stock Draw",
            f"Drew {len(drawn)} {noun} from the Stock to the Waste.",
            FEEDBACK_SUCCESS,
        )
        self._after_action(announce_move=True)

    def try_move(self, source_pile: str, card_id: str | None, destination_pile: str) -> bool:
        """Resolve one player move request through the engine.

        Returns True when the engine executed the move. On invalid moves the
        engine raises before mutating, and False is returned after showing
        the rule-based reason.
        """
        if source_pile == destination_pile:
            self.feedback.emit(
                "Invalid Move", "Source and destination are the same pile.", FEEDBACK_ERROR
            )
            return False

        # Resolve pile IDs against the live state before dispatching. A Waste
        # or Stock target is not a Tableau column; prefix-only routing used
        # to send "waste" into move_tableau_to_tableau(), which raised an
        # uncaught ValueError from GameEngine._get_tableau().
        tableau_piles = self._state.tableau
        foundation_suits = {
            f"foundation-{suit.code.lower()}": suit
            for suit in self._state.foundations
        }

        if source_pile != "waste" and source_pile not in tableau_piles:
            self.feedback.emit(
                "Invalid Move",
                "The selected source is not a movable Waste or Tableau pile.",
                FEEDBACK_ERROR,
            )
            return False

        if destination_pile not in tableau_piles and destination_pile not in foundation_suits:
            self.feedback.emit(
                "Invalid Move",
                "Choose a Tableau column or Foundation as the destination.",
                FEEDBACK_ERROR,
            )
            return False

        try:
            if source_pile == "waste":
                if destination_pile in foundation_suits:
                    self._engine.move_waste_to_foundation(foundation_suits[destination_pile])
                else:
                    self._engine.move_waste_to_tableau(destination_pile)
            else:
                if card_id is None:
                    raise _missing_card_error()
                if destination_pile in foundation_suits:
                    self._engine.move_tableau_to_foundation(
                        source_pile, foundation_suits[destination_pile]
                    )
                else:
                    self._engine.move_tableau_to_tableau(
                        source_pile, card_id, destination_pile
                    )
        except InvalidMoveError as error:
            # Invalid action: the engine rejected before mutating and the
            # game clock must NOT start on a rejected move.
            reason = error.result.reason.value if error.result.reason else "Invalid move."
            self.feedback.emit("Invalid Move", reason, FEEDBACK_ERROR)
            self.operations_changed.emit()
            return False
        except RuntimeError as error:
            self.feedback.emit("Game Over", str(error), FEEDBACK_INFO)
            return False

        self._ensure_clock()
        self._after_action(announce_move=True)
        return True

    def undo(self) -> None:
        if self._engine.undo():
            self.feedback.emit("Undo", "The last action was reverted.", FEEDBACK_INFO)
            self._after_action(announce_move=False)
        else:
            self.feedback.emit("Undo", "There is nothing to undo.", FEEDBACK_INFO)

    def redo(self) -> None:
        if self._engine.redo():
            self.feedback.emit("Redo", "The undone action was reapplied.", FEEDBACK_INFO)
            self._after_action(announce_move=False)
        else:
            self.feedback.emit("Redo", "There is nothing to redo.", FEEDBACK_INFO)

    def hint(self) -> None:
        hints = self._engine.find_hints()
        if not hints:
            self.feedback.emit(
                "Hint", "No legal moves remain. Try undoing or starting a new game.",
                FEEDBACK_INFO,
            )
            return
        best = hints[0]
        self.feedback.emit("Hint", best.description, FEEDBACK_INFO)

    def hint_move(self):
        """Return the highest-priority MoveHint or None (for glow effects)."""
        hints = self._engine.find_hints()
        return hints[0] if hints else None

    # --- validation helpers (read-only, no state changes) ------------------
    def legal_destinations(self, source_pile: str, card_id: str | None) -> list[str]:
        """Piles that currently accept the selected card/run, per the rules."""
        if source_pile == "waste":
            if self._state.waste.is_empty():
                return []
            card = self._state.waste.peek()
            return self._legal_targets_for_cards([card])
        if source_pile.startswith("tableau-"):
            if card_id is None:
                return []
            return [
                *self._engine.valid_tableau_destinations(source_pile, card_id),
                *self._legal_foundation_for_column_top(source_pile, card_id),
            ]
        return []

    def _legal_targets_for_cards(self, run: list[Card]) -> list[str]:
        targets: list[str] = []
        for column_id, column in self._state.tableau.items():
            top = None if column.is_empty() else column.peek()
            from solitaire.domain.rules import RuleValidator

            if RuleValidator.validate_tableau_run(run, top).allowed:
                targets.append(column_id)
        for suit, foundation in self._state.foundations.items():
            if len(run) != 1:
                continue
            top = None if foundation.is_empty() else foundation.peek()
            from solitaire.domain.rules import RuleValidator

            if RuleValidator.validate_foundation(run[0], suit, top).allowed:
                targets.append(f"foundation-{suit.code.lower()}")
        return targets

    def _legal_foundation_for_column_top(self, column_id: str, card_id: str) -> list[str]:
        column = self._state.tableau[column_id]
        if column.is_empty():
            return []
        top = column.peek()
        if top.card_id != card_id:
            return []
        targets: list[str] = []
        for suit, foundation in self._state.foundations.items():
            foundation_top = None if foundation.is_empty() else foundation.peek()
            from solitaire.domain.rules import RuleValidator

            if RuleValidator.validate_foundation(top, suit, foundation_top).allowed:
                targets.append(f"foundation-{suit.code.lower()}")
        return targets

    # --- presentation data -------------------------------------------------
    def metrics(self) -> dict[str, str]:
        minutes, seconds = divmod(self._elapsed_seconds, 60)
        return {
            "time": f"{minutes:02d}:{seconds:02d}",
            "moves": str(self._state.move_count),
            "score": str(self._state.score),
        }

    def foundation_progress(self) -> tuple[int, int]:
        total = sum(pile.size() for pile in self._state.foundations.values())
        return total, 52

    # --- internals ----------------------------------------------------------
    def _after_action(self, *, announce_move: bool) -> None:
        # Only genuine player actions append a log row. Undo/redo TRUNCATE or
        # re-extend the engine history, so re-emitting `history[-1]` here
        # would duplicate an earlier player move in the Move Log.
        if announce_move:
            history = self._engine.move_history
            if history:
                self.move_logged.emit(history[-1])
        self.operations_changed.emit()
        self.state_changed.emit("action")
        if self._state.status is GameStatus.WON:
            self._clock.stop()
            minutes, seconds = divmod(self._elapsed_seconds, 60)
            self.feedback.emit(
                "Victory!",
                (
                    "All four foundations are complete. "
                    f"Score {self._state.score} in {self._state.move_count} moves "
                    f"({minutes:02d}:{seconds:02d})."
                ),
                FEEDBACK_VICTORY,
            )
            self.game_won.emit()
