"""In-memory game state and exact Klondike initial deal."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random
from uuid import uuid4

from solitaire.domain.card import Card, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.operations import OperationTracker, StructureName
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack


class Zone(str, Enum):
    STOCK = "stock"
    WASTE = "waste"
    TABLEAU = "tableau"
    FOUNDATION = "foundation"


class GameStatus(str, Enum):
    READY = "ready"
    PLAYING = "playing"
    WON = "won"


@dataclass(frozen=True, slots=True)
class CardLocation:
    zone: Zone
    pile_id: str
    position: int
    face_up: bool


@dataclass(slots=True)
class TableauColumn:
    """A tableau pile with Stack operations backed by Linked List nodes."""

    column_id: str
    stack: Stack[Card] = field(default_factory=Stack)

    def push(self, card: Card) -> None:
        self.stack.push(card)

    def pop(self) -> Card:
        return self.stack.pop()

    def peek(self) -> Card:
        return self.stack.peek()

    def size(self) -> int:
        return self.stack.size()

    def is_empty(self) -> bool:
        return self.stack.is_empty()

    def cards_bottom_to_top(self) -> list[Card]:
        return self.stack.to_list()


@dataclass(slots=True)
class GameState:
    """Canonical in-memory state for one Klondike game."""

    stock: Queue[Card]
    waste: Stack[Card]
    tableau: dict[str, TableauColumn]
    foundations: dict[Suit, Stack[Card]]
    card_index: dict[str, CardLocation]
    draw_count: int = 1
    status: GameStatus = GameStatus.PLAYING
    move_count: int = 0
    elapsed_seconds: int = 0
    score: int = 0

    def set_draw_count(self, count: int) -> None:
        if count not in (1, 3):
            raise ValueError("Draw count must be either 1 or 3")
        self.draw_count = count

    def cards_in_play(self) -> list[Card]:
        """Return every active card once, in a stable zone traversal order."""
        cards: list[Card] = []
        cards.extend(self.stock.to_list())
        cards.extend(self.waste.to_list())

        for column_id in sorted(self.tableau):
            cards.extend(self.tableau[column_id].cards_bottom_to_top())

        for suit in Suit:
            cards.extend(self.foundations[suit].to_list())

        return cards

    def assert_invariants(self) -> None:
        """Raise AssertionError if cards, piles, links, or index disagree."""
        cards = self.cards_in_play()
        card_ids = [card.card_id for card in cards]

        assert len(cards) == 52, f"Expected 52 cards, found {len(cards)}"
        assert len(set(card_ids)) == 52, "A card is missing or appears in multiple piles"
        assert set(self.card_index) == set(card_ids), "Dictionary keys do not match cards in piles"

        expected_locations: dict[str, CardLocation] = {}

        for position, card in enumerate(self.stock.to_list()):
            expected_locations[card.card_id] = CardLocation(
                Zone.STOCK, "stock", position, card.face_up
            )

        for position, card in enumerate(self.waste.to_list()):
            expected_locations[card.card_id] = CardLocation(
                Zone.WASTE, "waste", position, card.face_up
            )

        for column_id, column in self.tableau.items():
            assert column.stack.linked_list.validate(), f"Invalid links in {column_id}"
            for position, card in enumerate(column.cards_bottom_to_top()):
                expected_locations[card.card_id] = CardLocation(
                    Zone.TABLEAU, column_id, position, card.face_up
                )

        for suit, pile in self.foundations.items():
            for position, card in enumerate(pile.to_list()):
                expected_locations[card.card_id] = CardLocation(
                    Zone.FOUNDATION, f"foundation-{suit.code.lower()}", position, card.face_up
                )

        assert self.card_index == expected_locations, "Card dictionary is out of sync with piles"


def create_new_game(\n    rng: Random | None = None,\n    draw_count: int = 1,\n    tracker: OperationTracker | None = None,\n) -> GameState:
    """Create, shuffle, deal, and index a fresh 52-card Klondike game."""
    if draw_count not in (1, 3):
        raise ValueError("Draw count must be either 1 or 3")

    tracker = tracker or OperationTracker()
    action_id = f"setup-{uuid4().hex[:8]}"

    deck = DeckFactory.create_standard_deck()
    tracker.record(
        StructureName.ARRAY_LIST, "CREATE_DECK", action_id=action_id,
        card_ids=tuple(card.card_id for card in deck),
        details={"size": len(deck)},
    )
    DeckFactory.shuffle(deck, rng)
    tracker.record(
        StructureName.ARRAY_LIST, "SHUFFLE", action_id=action_id,
        card_ids=tuple(card.card_id for card in deck),
        details={"algorithm": "randomized in-place shuffle"},
    )

    tableau: dict[str, TableauColumn] = {}

    for column_number in range(1, 8):
        column_id = f"tableau-{column_number}"
        column = TableauColumn(column_id=column_id)

        for card_position in range(column_number):
            card = deck.pop()
            tracker.record(
                StructureName.ARRAY_LIST, "POP_FOR_DEAL", action_id=action_id,
                card_ids=(card.card_id,),
                details={"destination": column_id, "position": card_position},
            )
            card.turn_face_down()
            if card_position == column_number - 1:
                card.turn_face_up()
            column.push(card)
            tracker.record(
                StructureName.STACK, "PUSH", action_id=action_id,
                pile_id=column_id, card_ids=(card.card_id,),
            )
            tracker.record(
                StructureName.LINKED_LIST, "APPEND_NODE", action_id=action_id,
                pile_id=column_id, card_ids=(card.card_id,),
            )

        tableau[column_id] = column

    stock: Queue[Card] = Queue()
    for card in deck:
        card.turn_face_down()
        stock.enqueue(card)
        tracker.record(
            StructureName.QUEUE, "ENQUEUE", action_id=action_id,
            pile_id="stock", card_ids=(card.card_id,),
        )

    # The temporary deck list has completed its job. The 24 stock cards
    # now live only in the Queue.
    deck.clear()
    tracker.record(
        StructureName.ARRAY_LIST, "CLEAR_AFTER_DEAL", action_id=action_id,
        details={"reason": "active cards now belong to their piles"},
    )

    waste: Stack[Card] = Stack()
    foundations = {suit: Stack[Card]() for suit in Suit}

    card_index: dict[str, CardLocation] = {}

    for position, card in enumerate(stock.to_list()):
        card_index[card.card_id] = CardLocation(
            Zone.STOCK, "stock", position, card.face_up
        )
        tracker.record(
            StructureName.DICTIONARY, "INSERT", action_id=action_id,
            pile_id="stock", card_ids=(card.card_id,),
            details={"zone": Zone.STOCK.value, "position": position, "face_up": card.face_up},
        )

    for position, card in enumerate(waste.to_list()):
        card_index[card.card_id] = CardLocation(
            Zone.WASTE, "waste", position, card.face_up
        )

    for column_id, column in tableau.items():
        for position, card in enumerate(column.cards_bottom_to_top()):
            card_index[card.card_id] = CardLocation(
                Zone.TABLEAU, column_id, position, card.face_up
            )
            tracker.record(
                StructureName.DICTIONARY, "INSERT", action_id=action_id,
                pile_id=column_id, card_ids=(card.card_id,),
                details={"zone": Zone.TABLEAU.value, "position": position, "face_up": card.face_up},
            )

    for suit, pile in foundations.items():
        for position, card in enumerate(pile.to_list()):
            card_index[card.card_id] = CardLocation(
                Zone.FOUNDATION, f"foundation-{suit.code.lower()}", position, card.face_up
            )

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=card_index,
        draw_count=draw_count,
    )
    state.assert_invariants()
    tracker.record(
        StructureName.GAME, "INITIAL_DEAL_COMPLETE", action_id=action_id,
        details={"tableau_cards": 28, "stock_cards": 24, "face_up_tableau_cards": 7},
    )
    return state
