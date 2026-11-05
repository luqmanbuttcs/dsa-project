"""Klondike game actions using the custom data structures."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from itertools import count
from typing import Iterable

from solitaire.domain.card import Card, Suit
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    GameStatus,
    Zone,
)
from solitaire.domain.operations import OperationTracker, StructureName
from solitaire.domain.rules import MoveError, RuleValidator, ValidationResult
from solitaire.structures.stack import Stack


class InvalidMoveError(ValueError):
    """Raised when a requested move violates Klondike rules."""

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        message = result.reason.value if result.reason else "Invalid move."
        super().__init__(message)


class NoCardsAvailableError(RuntimeError):
    """Raised when neither stock nor recyclable waste contains a card."""


@dataclass(frozen=True, slots=True)
class MoveEvent:
    action_id: str
    action_type: str
    description: str
    card_ids: tuple[str, ...]
    source_pile: str | None
    destination_pile: str | None
    move_number: int


@dataclass(frozen=True, slots=True)
class GameSnapshot:
    """Immutable logical snapshot used to reverse or reapply one player action."""

    stock_ids: tuple[str, ...]
    waste_ids: tuple[str, ...]
    tableau_ids: tuple[tuple[str, tuple[str, ...]], ...]
    foundation_ids: tuple[tuple[Suit, tuple[str, ...]], ...]
    face_states: tuple[tuple[str, bool], ...]
    draw_count: int
    status: GameStatus
    move_count: int
    elapsed_seconds: int
    score: int
    move_history: tuple[MoveEvent, ...]


def _undoable(method):
    """Save the exact pre-action state after a public game action succeeds."""

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        before = self._capture_snapshot()
        previous_history_size = len(self.move_history)
        result = method(self, *args, **kwargs)

        # Failed/invalid actions do not append a MoveEvent and therefore do
        # not become undo entries.
        if len(self.move_history) > previous_history_size:
            self._store_undo_snapshot(before, self.move_history[-1].action_id)
        return result

    return wrapped


class GameEngine:
    """Coordinates rule validation, real structure calls, and card indexing."""

    _action_counter = count(1)

    def __init__(
        self,
        state: GameState,
        tracker: OperationTracker | None = None,
    ) -> None:
        self.state = state
        self.tracker = tracker or OperationTracker()
        self.move_history: list[MoveEvent] = []
        self.undo_stack: Stack[GameSnapshot] = Stack()
        self.redo_stack: Stack[GameSnapshot] = Stack()
        self._active_action_id: str | None = None
        self._context = "PLAY"

    @property
    def can_undo(self) -> bool:
        """Whether at least one successful player action can be undone."""
        return not self.undo_stack.is_empty()

    @property
    def can_redo(self) -> bool:
        """Whether an undone player action can be reapplied."""
        return not self.redo_stack.is_empty()

    @_undoable
    def draw_from_stock(self, count_cards: int | None = None) -> list[Card]:
        """Draw one or three cards from the FIFO stock queue into waste."""
        self._ensure_playing()
        draw_count = count_cards if count_cards is not None else self.state.draw_count
        if draw_count not in (1, 3):
            raise ValueError("A stock draw must request one or three cards")

        action_id = self._begin_action()
        source_ids: list[str] = []
        drawn: list[Card] = []

        if self.state.stock.is_empty():
            if self.state.waste.is_empty():
                self._active_action_id = None
                raise NoCardsAvailableError("The stock and waste piles are empty.")
            self._recycle_waste(action_id)

        while len(drawn) < draw_count and not self.state.stock.is_empty():
            card = self.state.stock.dequeue()
            self._record(
                StructureName.QUEUE,
                "DEQUEUE",
                action_id=action_id,
                pile_id="stock",
                card_ids=(card.card_id,),
                details={"fifo_position": "front"},
            )

            card.turn_face_up()
            self.state.waste.push(card)
            self._record(
                StructureName.STACK,
                "PUSH",
                action_id=action_id,
                pile_id="waste",
                card_ids=(card.card_id,),
                details={"role": "waste pile"},
            )
            drawn.append(card)
            source_ids.append(card.card_id)

        self.state.move_count += 1
        self._refresh_card_index(action_id)
        self._append_move(
            action_id,
            "DRAW",
            f"Drew {len(drawn)} card(s) from Stock",
            tuple(source_ids),
            "stock",
            "waste",
        )
        self.state.assert_invariants()
        self._active_action_id = None
        return drawn

    @_undoable
    def move_tableau_to_tableau(
        self,
        source_column_id: str,
        card_id: str,
        destination_column_id: str,
    ) -> list[Card]:
        """Move a face-up tableau suffix using the Linked List and Stack APIs."""
        self._ensure_playing()
        if source_column_id == destination_column_id:
            raise InvalidMoveError(ValidationResult.reject(MoveError.SAME_COLUMN))

        source = self._get_tableau(source_column_id)
        destination = self._get_tableau(destination_column_id)
        source_cards = source.cards_bottom_to_top()

        selected_index = next(
            (index for index, card in enumerate(source_cards) if card.card_id == card_id),
            None,
        )
        if selected_index is None:
            raise InvalidMoveError(ValidationResult.reject(MoveError.CARD_NOT_FOUND))

        run = source_cards[selected_index:]
        if destination.is_empty():
            destination_top = None
        else:
            destination_top = destination.peek()

        result = RuleValidator.validate_tableau_run(run, destination_top)
        if not result.allowed:
            self._record_rejection(source_column_id, destination_column_id, card_id, result)
            raise InvalidMoveError(result)

        action_id = self._begin_action()
        detached = source.detach_run_from(selected_index)
        self._record(
            StructureName.STACK,
            "DETACH_RUN",
            action_id=action_id,
            pile_id=source_column_id,
            card_ids=tuple(card.card_id for card in run),
        )
        self._record(
            StructureName.LINKED_LIST,
            "DETACH_RUN",
            action_id=action_id,
            pile_id=source_column_id,
            card_ids=tuple(card.card_id for card in run),
            details={"node_links": "source boundaries relinked"},
        )

        destination.attach_run(detached)
        self._record(
            StructureName.STACK,
            "ATTACH_RUN",
            action_id=action_id,
            pile_id=destination_column_id,
            card_ids=tuple(card.card_id for card in run),
        )
        self._record(
            StructureName.LINKED_LIST,
            "ATTACH_RUN",
            action_id=action_id,
            pile_id=destination_column_id,
            card_ids=tuple(card.card_id for card in run),
            details={"node_links": "run attached after destination tail"},
        )

        self._flip_exposed_card(source, action_id)
        self.state.move_count += 1
        self._refresh_card_index(action_id)
        self._append_move(
            action_id,
            "TABLEAU_TO_TABLEAU",
            f"Moved {run[0]} from {source_column_id} to {destination_column_id}",
            tuple(card.card_id for card in run),
            source_column_id,
            destination_column_id,
        )
        self.state.assert_invariants()
        self._active_action_id = None
        return run

    @_undoable
    def move_waste_to_tableau(
        self,
        destination_column_id: str,
    ) -> Card:
        self._ensure_playing()
        if self.state.waste.is_empty():
            raise InvalidMoveError(ValidationResult.reject(MoveError.CARD_NOT_FOUND))

        card = self.state.waste.peek()
        destination = self._get_tableau(destination_column_id)
        destination_top = None if destination.is_empty() else destination.peek()
        result = RuleValidator.validate_tableau_run([card], destination_top)
        if not result.allowed:
            self._record_rejection("waste", destination_column_id, card.card_id, result)
            raise InvalidMoveError(result)

        action_id = self._begin_action()
        moved = self.state.waste.pop()
        self._record(
            StructureName.STACK, "POP", action_id=action_id,
            pile_id="waste", card_ids=(moved.card_id,)
        )
        destination.push(moved)
        self._record(
            StructureName.STACK, "PUSH", action_id=action_id,
            pile_id=destination_column_id, card_ids=(moved.card_id,)
        )
        self._record(
            StructureName.LINKED_LIST, "APPEND_NODE", action_id=action_id,
            pile_id=destination_column_id, card_ids=(moved.card_id,),
        )

        self.state.move_count += 1
        self._refresh_card_index(action_id)
        self._append_move(
            action_id, "WASTE_TO_TABLEAU",
            f"Moved {moved} from Waste to {destination_column_id}",
            (moved.card_id,), "waste", destination_column_id
        )
        self.state.assert_invariants()
        self._active_action_id = None
        return moved

    @_undoable
    def move_tableau_to_foundation(
        self,
        source_column_id: str,
        foundation_suit: Suit,
    ) -> Card:
        self._ensure_playing()
        source = self._get_tableau(source_column_id)
        if source.is_empty():
            raise InvalidMoveError(ValidationResult.reject(MoveError.CARD_NOT_FOUND))

        card = source.peek()
        foundation = self.state.foundations[foundation_suit]
        foundation_top = None if foundation.is_empty() else foundation.peek()
        result = RuleValidator.validate_foundation(card, foundation_suit, foundation_top)

        if not result.allowed:
            self._record_rejection(
                source_column_id,
                f"foundation-{foundation_suit.code.lower()}",
                card.card_id,
                result,
            )
            raise InvalidMoveError(result)

        action_id = self._begin_action()
        moved = source.pop()
        self._record(
            StructureName.STACK, "POP", action_id=action_id,
            pile_id=source_column_id, card_ids=(moved.card_id,)
        )
        self._record(
            StructureName.LINKED_LIST, "REMOVE_TOP_NODE", action_id=action_id,
            pile_id=source_column_id, card_ids=(moved.card_id,),
        )
        foundation.push(moved)
        self._record(
            StructureName.STACK, "PUSH", action_id=action_id,
            pile_id=f"foundation-{foundation_suit.code.lower()}",
            card_ids=(moved.card_id,)
        )

        self._flip_exposed_card(source, action_id)
        self.state.move_count += 1
        self._refresh_card_index(action_id)
        destination_id = f"foundation-{foundation_suit.code.lower()}"
        self._append_move(
            action_id, "TABLEAU_TO_FOUNDATION",
            f"Moved {moved} to {destination_id}",
            (moved.card_id,), source_column_id, destination_id
        )
        self._update_win_status(action_id)
        self.state.assert_invariants()
        self._active_action_id = None
        return moved

    @_undoable
    def move_waste_to_foundation(self, foundation_suit: Suit) -> Card:
        self._ensure_playing()
        if self.state.waste.is_empty():
            raise InvalidMoveError(ValidationResult.reject(MoveError.CARD_NOT_FOUND))

        card = self.state.waste.peek()
        foundation = self.state.foundations[foundation_suit]
        foundation_top = None if foundation.is_empty() else foundation.peek()
        result = RuleValidator.validate_foundation(card, foundation_suit, foundation_top)

        if not result.allowed:
            self._record_rejection(
                "waste", f"foundation-{foundation_suit.code.lower()}",
                card.card_id, result
            )
            raise InvalidMoveError(result)

        action_id = self._begin_action()
        moved = self.state.waste.pop()
        self._record(
            StructureName.STACK, "POP", action_id=action_id,
            pile_id="waste", card_ids=(moved.card_id,)
        )
        foundation.push(moved)
        destination_id = f"foundation-{foundation_suit.code.lower()}"
        self._record(
            StructureName.STACK, "PUSH", action_id=action_id,
            pile_id=destination_id, card_ids=(moved.card_id,)
        )

        self.state.move_count += 1
        self._refresh_card_index(action_id)
        self._append_move(
            action_id, "WASTE_TO_FOUNDATION",
            f"Moved {moved} from Waste to {destination_id}",
            (moved.card_id,), "waste", destination_id
        )
        self._update_win_status(action_id)
        self.state.assert_invariants()
        self._active_action_id = None
        return moved

    def set_draw_count(self, count_cards: int) -> None:
        self.state.set_draw_count(count_cards)

    def has_won(self) -> bool:
        """Return True only when all 52 cards form four complete suit foundations."""
        if not self.state.stock.is_empty() or not self.state.waste.is_empty():
            return False
        if any(not column.is_empty() for column in self.state.tableau.values()):
            return False

        for suit, pile in self.state.foundations.items():
            cards = pile.to_list()
            if len(cards) != 13:
                return False
            if any(card.suit is not suit or not card.face_up for card in cards):
                return False
            if [int(card.rank) for card in cards] != list(range(1, 14)):
                return False

        return True

    def valid_tableau_destinations(
        self,
        source_column_id: str,
        card_id: str,
    ) -> list[str]:
        """Return legal destination columns for the selected face-up run."""
        source = self._get_tableau(source_column_id)
        cards = source.cards_bottom_to_top()
        index = next((i for i, card in enumerate(cards) if card.card_id == card_id), None)
        if index is None:
            return []

        run = cards[index:]
        destinations: list[str] = []
        for column_id, column in self.state.tableau.items():
            if column_id == source_column_id:
                continue
            top = None if column.is_empty() else column.peek()
            if RuleValidator.validate_tableau_run(run, top).allowed:
                destinations.append(column_id)
        return destinations

    def undo(self) -> bool:
        """Restore the state immediately before the most recent successful action.

        The operation tracker is intentionally append-only: restoring a state
        performs real Stack/Queue/Linked List operations and records them with
        the UNDO context instead of deleting the original play events.
        """
        if self.undo_stack.is_empty():
            return False

        action_id = self._begin_action()
        current = self._capture_snapshot()
        previous = self._pop_history_snapshot(
            self.undo_stack, action_id, context="UNDO", pile_id="undo-history"
        )
        self._push_history_snapshot(
            self.redo_stack, current, action_id,
            context="UNDO", pile_id="redo-history"
        )
        self._restore_snapshot(previous, action_id, context="UNDO")
        self._record(
            StructureName.GAME,
            "UNDO_COMPLETE",
            action_id=action_id,
            context="UNDO",
            details={"restored_move_count": self.state.move_count},
        )
        self._active_action_id = None
        return True

    def redo(self) -> bool:
        """Reapply the most recently undone successful action."""
        if self.redo_stack.is_empty():
            return False

        action_id = self._begin_action()
        current = self._capture_snapshot()
        next_state = self._pop_history_snapshot(
            self.redo_stack, action_id, context="REDO", pile_id="redo-history"
        )
        self._push_history_snapshot(
            self.undo_stack, current, action_id,
            context="REDO", pile_id="undo-history"
        )
        self._restore_snapshot(next_state, action_id, context="REDO")
        self._record(
            StructureName.GAME,
            "REDO_COMPLETE",
            action_id=action_id,
            context="REDO",
            details={"restored_move_count": self.state.move_count},
        )
        self._active_action_id = None
        return True

    def _capture_snapshot(self) -> GameSnapshot:
        """Capture pile order and mutable card/game metadata without copying cards."""
        cards = {card.card_id: card for card in self.state.cards_in_play()}
        return GameSnapshot(
            stock_ids=tuple(card.card_id for card in self.state.stock.to_list()),
            waste_ids=tuple(card.card_id for card in self.state.waste.to_list()),
            tableau_ids=tuple(
                (column_id, tuple(card.card_id for card in column.cards_bottom_to_top()))
                for column_id, column in self.state.tableau.items()
            ),
            foundation_ids=tuple(
                (suit, tuple(card.card_id for card in self.state.foundations[suit].to_list()))
                for suit in Suit
            ),
            face_states=tuple(
                (card_id, cards[card_id].face_up) for card_id in sorted(cards)
            ),
            draw_count=self.state.draw_count,
            status=self.state.status,
            move_count=self.state.move_count,
            elapsed_seconds=self.state.elapsed_seconds,
            score=self.state.score,
            move_history=tuple(self.move_history),
        )

    def _store_undo_snapshot(self, snapshot: GameSnapshot, action_id: str) -> None:
        """Push a pre-action snapshot and invalidate the redo branch."""
        # History maintenance is a real Stack operation, but it is a separate
        # internal action and must not inflate the player's move-level trace.
        history_action_id = f"{action_id}-history"
        self._push_history_snapshot(
            self.undo_stack, snapshot, history_action_id,
            context="HISTORY", pile_id="undo-history"
        )
        while not self.redo_stack.is_empty():
            self._pop_history_snapshot(
                self.redo_stack, history_action_id,
                context="HISTORY", pile_id="redo-history"
            )

    def _push_history_snapshot(
        self,
        history_stack: Stack[GameSnapshot],
        snapshot: GameSnapshot,
        action_id: str,
        *,
        context: str,
        pile_id: str,
    ) -> None:
        history_stack.push(snapshot)
        self._record(
            StructureName.STACK, "PUSH", action_id=action_id,
            pile_id=pile_id, context=context,
            details={"role": "undo/redo history"},
        )
        self._record(
            StructureName.LINKED_LIST, "APPEND_NODE", action_id=action_id,
            pile_id=pile_id, context=context,
            details={"role": "Stack backing node"},
        )

    def _pop_history_snapshot(
        self,
        history_stack: Stack[GameSnapshot],
        action_id: str,
        *,
        context: str,
        pile_id: str,
    ) -> GameSnapshot:
        snapshot = history_stack.pop()
        self._record(
            StructureName.STACK, "POP", action_id=action_id,
            pile_id=pile_id, context=context,
            details={"role": "undo/redo history"},
        )
        self._record(
            StructureName.LINKED_LIST, "REMOVE_TOP_NODE", action_id=action_id,
            pile_id=pile_id, context=context,
            details={"role": "Stack backing node"},
        )
        return snapshot

    def _restore_snapshot(
        self,
        snapshot: GameSnapshot,
        action_id: str,
        *,
        context: str,
    ) -> None:
        """Rebuild every zone from a snapshot using the project's custom ADTs."""
        cards_by_id = {card.card_id: card for card in self.state.cards_in_play()}
        snapshot_card_ids = {card_id for card_id, _ in snapshot.face_states}
        if snapshot_card_ids != set(cards_by_id):
            raise AssertionError("Undo snapshot does not contain the current 52-card deck")

        # Empty all zones through their public Stack/Queue operations.
        while not self.state.stock.is_empty():
            card = self.state.stock.dequeue()
            self._record(
                StructureName.QUEUE, "DEQUEUE", action_id=action_id,
                pile_id="stock", card_ids=(card.card_id,), context=context,
                details={"purpose": "state restoration"},
            )

        while not self.state.waste.is_empty():
            card = self.state.waste.pop()
            self._record(
                StructureName.STACK, "POP", action_id=action_id,
                pile_id="waste", card_ids=(card.card_id,), context=context,
                details={"purpose": "state restoration"},
            )

        for column_id, column in self.state.tableau.items():
            while not column.is_empty():
                card = column.pop()
                self._record(
                    StructureName.STACK, "POP", action_id=action_id,
                    pile_id=column_id, card_ids=(card.card_id,), context=context,
                    details={"purpose": "state restoration"},
                )
                self._record(
                    StructureName.LINKED_LIST, "REMOVE_TOP_NODE",
                    action_id=action_id, pile_id=column_id,
                    card_ids=(card.card_id,), context=context,
                    details={"purpose": "state restoration"},
                )

        for suit, pile in self.state.foundations.items():
            pile_id = f"foundation-{suit.code.lower()}"
            while not pile.is_empty():
                card = pile.pop()
                self._record(
                    StructureName.STACK, "POP", action_id=action_id,
                    pile_id=pile_id, card_ids=(card.card_id,), context=context,
                    details={"purpose": "state restoration"},
                )

        # Face state is part of the snapshot, not an incidental side effect.
        for card_id, face_up in snapshot.face_states:
            card = cards_by_id[card_id]
            if card.face_up != face_up:
                if face_up:
                    card.turn_face_up()
                else:
                    card.turn_face_down()
                self._record(
                    StructureName.GAME, "CARD_FLIPPED",
                    action_id=action_id, pile_id=None,
                    card_ids=(card_id,), context=context,
                    details={"face_up": face_up, "reason": "state restoration"},
                )

        for card_id in snapshot.stock_ids:
            card = cards_by_id[card_id]
            self.state.stock.enqueue(card)
            self._record(
                StructureName.QUEUE, "ENQUEUE", action_id=action_id,
                pile_id="stock", card_ids=(card_id,), context=context,
                details={"purpose": "state restoration", "fifo_position": "rear"},
            )

        for card_id in snapshot.waste_ids:
            card = cards_by_id[card_id]
            self.state.waste.push(card)
            self._record(
                StructureName.STACK, "PUSH", action_id=action_id,
                pile_id="waste", card_ids=(card_id,), context=context,
                details={"purpose": "state restoration"},
            )

        for column_id, card_ids in snapshot.tableau_ids:
            column = self.state.tableau[column_id]
            for card_id in card_ids:
                card = cards_by_id[card_id]
                column.push(card)
                self._record(
                    StructureName.STACK, "PUSH", action_id=action_id,
                    pile_id=column_id, card_ids=(card_id,), context=context,
                    details={"purpose": "state restoration"},
                )
                self._record(
                    StructureName.LINKED_LIST, "APPEND_NODE",
                    action_id=action_id, pile_id=column_id,
                    card_ids=(card_id,), context=context,
                    details={"purpose": "state restoration"},
                )

        for suit, card_ids in snapshot.foundation_ids:
            pile = self.state.foundations[suit]
            pile_id = f"foundation-{suit.code.lower()}"
            for card_id in card_ids:
                card = cards_by_id[card_id]
                pile.push(card)
                self._record(
                    StructureName.STACK, "PUSH", action_id=action_id,
                    pile_id=pile_id, card_ids=(card_id,), context=context,
                    details={"purpose": "state restoration"},
                )

        self.state.draw_count = snapshot.draw_count
        self.state.status = snapshot.status
        self.state.move_count = snapshot.move_count
        self.state.elapsed_seconds = snapshot.elapsed_seconds
        self.state.score = snapshot.score
        self.move_history = list(snapshot.move_history)
        self._refresh_card_index(action_id, context=context)
        self.state.assert_invariants()

    def _recycle_waste(self, action_id: str) -> None:
        """Recycle waste top-to-bottom so the next draw uses the former top."""
        recycled: list[str] = []
        while not self.state.waste.is_empty():
            card = self.state.waste.pop()
            self._record(
                StructureName.STACK, "POP", action_id=action_id,
                pile_id="waste", card_ids=(card.card_id,),
                details={"purpose": "stock recycle"}
            )
            card.turn_face_down()
            self.state.stock.enqueue(card)
            self._record(
                StructureName.QUEUE, "ENQUEUE", action_id=action_id,
                pile_id="stock", card_ids=(card.card_id,),
                details={"fifo_position": "rear", "purpose": "stock recycle"}
            )
            recycled.append(card.card_id)

        self._refresh_card_index(action_id)
        self._record(
            StructureName.GAME, "WASTE_RECYCLED",
            action_id=action_id, pile_id="stock",
            card_ids=tuple(recycled),
            details={"recycled_count": len(recycled)}
        )

    def _flip_exposed_card(self, column, action_id: str) -> None:
        if column.is_empty():
            return
        exposed = column.peek()
        if not exposed.face_up:
            exposed.turn_face_up()
            self._record(
                StructureName.GAME, "CARD_FLIPPED",
                action_id=action_id,
                pile_id=column.column_id,
                card_ids=(exposed.card_id,),
            )

    def _refresh_card_index(self, action_id: str, *, context: str = "PLAY") -> None:
        expected: dict[str, CardLocation] = {}

        for position, card in enumerate(self.state.stock.to_list()):
            expected[card.card_id] = CardLocation(
                Zone.STOCK, "stock", position, card.face_up
            )

        for position, card in enumerate(self.state.waste.to_list()):
            expected[card.card_id] = CardLocation(
                Zone.WASTE, "waste", position, card.face_up
            )

        for column_id, column in self.state.tableau.items():
            for position, card in enumerate(column.cards_bottom_to_top()):
                expected[card.card_id] = CardLocation(
                    Zone.TABLEAU, column_id, position, card.face_up
                )

        for suit, pile in self.state.foundations.items():
            pile_id = f"foundation-{suit.code.lower()}"
            for position, card in enumerate(pile.to_list()):
                expected[card.card_id] = CardLocation(
                    Zone.FOUNDATION, pile_id, position, card.face_up
                )

        for card_id, location in expected.items():
            old_location = self.state.card_index.get(card_id)
            if old_location != location:
                self.state.card_index[card_id] = location
                self._record(
                    StructureName.DICTIONARY,
                    "INSERT" if old_location is None else "UPDATE",
                    action_id=action_id,
                    pile_id=location.pile_id,
                    card_ids=(card_id,),
                    context=context,
                    details={
                        "zone": location.zone.value,
                        "position": location.position,
                        "face_up": location.face_up,
                    },
                )

        # Removing an index key would mean a card was lost, so fail loudly.
        if set(expected) != set(self.state.card_index):
            raise AssertionError("Card dictionary contains missing or stale card entries")

    def _update_win_status(self, action_id: str) -> None:
        if self.has_won():
            self.state.status = GameStatus.WON
            self._record(
                StructureName.GAME, "GAME_WON",
                action_id=action_id,
                details={"foundation_cards": 52},
            )

    def _record_rejection(
        self,
        source: str,
        destination: str,
        card_id: str,
        result: ValidationResult,
    ) -> None:
        action_id = self._begin_action()
        self._record(
            StructureName.GAME,
            "MOVE_REJECTED",
            action_id=action_id,
            card_ids=(card_id,),
            outcome="REJECTED",
            details={
                "source": source,
                "destination": destination,
                "reason": result.reason.value if result.reason else "Invalid move",
            },
        )
        self._active_action_id = None

    def _append_move(
        self,
        action_id: str,
        action_type: str,
        description: str,
        card_ids: tuple[str, ...],
        source: str | None,
        destination: str | None,
    ) -> None:
        self.move_history.append(
            MoveEvent(
                action_id=action_id,
                action_type=action_type,
                description=description,
                card_ids=card_ids,
                source_pile=source,
                destination_pile=destination,
                move_number=self.state.move_count,
            )
        )

    def _begin_action(self) -> str:
        action_id = f"action-{next(self._action_counter)}"
        self._active_action_id = action_id
        return action_id

    def _record(
        self,
        structure: StructureName,
        operation: str,
        *,
        action_id: str,
        pile_id: str | None = None,
        card_ids: Iterable[str] = (),
        context: str = "PLAY",
        outcome: str = "SUCCESS",
        details: dict | None = None,
    ) -> None:
        self.tracker.record(
            structure,
            operation,
            action_id=action_id,
            pile_id=pile_id,
            card_ids=tuple(card_ids),
            context=context,
            outcome=outcome,
            details=details,
        )

    def _get_tableau(self, column_id: str):
        try:
            return self.state.tableau[column_id]
        except KeyError as error:
            raise ValueError(f"Unknown tableau column: {column_id}") from error

    def _ensure_playing(self) -> None:
        if self.state.status is not GameStatus.PLAYING:
            raise RuntimeError("The game is not currently playable")
