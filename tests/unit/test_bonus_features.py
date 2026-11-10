"""Tests for optional hints, scoring, and undo-safe performance tracking."""

from __future__ import annotations

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.game_engine import GameEngine
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    TableauColumn,
    Zone,
)
from solitaire.domain.operations import OperationTracker
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack


def build_state(
    tableau_layout: dict[str, list[tuple[str, bool]]] | None = None,
    waste_ids: tuple[str, ...] = (),
) -> GameState:
    """Build a full 52-card state; tableau lists are ordered bottom-to-top."""
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }

    for column_id, entries in (tableau_layout or {}).items():
        for card_id, face_up in entries:
            card = cards.pop(card_id)
            card.turn_face_up() if face_up else card.turn_face_down()
            tableau[column_id].push(card)

    waste = Stack()
    for card_id in waste_ids:
        card = cards.pop(card_id)
        card.turn_face_up()
        waste.push(card)

    stock = Queue()
    for card in cards.values():
        card.turn_face_down()
        stock.enqueue(card)

    foundations = {suit: Stack() for suit in Suit}
    card_index: dict[str, CardLocation] = {}

    for position, card in enumerate(stock.to_list()):
        card_index[card.card_id] = CardLocation(
            Zone.STOCK, "stock", position, card.face_up
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

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=card_index,
    )
    state.assert_invariants()
    return state


def test_hint_enumeration_returns_legal_moves_without_mutating_state():
    state = build_state(
        {
            "tableau-1": [("D-6", False), ("H-8", True)],
            "tableau-2": [("C-9", True)],
        }
    )
    tracker = OperationTracker()
    engine = GameEngine(state, tracker)
    before_tableau = {
        key: tuple(card.card_id for card in column.cards_bottom_to_top())
        for key, column in state.tableau.items()
    }
    before_index = dict(state.card_index)
    before_events = tuple(tracker.events)
    before_history = tuple(engine.move_history)

    hints = engine.find_hints()

    assert len(hints) == 1
    assert hints[0].action_type == "TABLEAU_TO_TABLEAU"
    assert hints[0].card_ids == ("H-8",)
    assert hints[0].source_pile == "tableau-1"
    assert hints[0].destination_pile == "tableau-2"
    assert "Tableau 1" in hints[0].description
    assert "Tableau 2" in hints[0].description
    assert {
        key: tuple(card.card_id for card in column.cards_bottom_to_top())
        for key, column in state.tableau.items()
    } == before_tableau
    assert state.card_index == before_index
    assert tuple(tracker.events) == before_events
    assert tuple(engine.move_history) == before_history
    assert state.move_count == 0
    state.assert_invariants()


def test_foundation_hint_is_prioritized_over_tableau_rearrangement():
    state = build_state(
        {"tableau-1": [("S-K", True)]},
        waste_ids=("H-A",),
    )
    engine = GameEngine(state)

    hints = engine.find_hints()

    assert hints
    assert hints[0].action_type == "WASTE_TO_FOUNDATION"
    assert hints[0].card_ids == ("H-A",)
    assert hints[0].destination_pile == "foundation-h"
    assert any(hint.action_type == "TABLEAU_TO_TABLEAU" for hint in hints)


def test_hint_falls_back_to_stock_draw_when_no_visible_move_exists():
    state = build_state(
        {
            "tableau-1": [("C-2", True)],
            "tableau-2": [("H-4", True)],
            "tableau-3": [("S-6", True)],
            "tableau-4": [("D-8", True)],
            "tableau-5": [("C-10", True)],
            "tableau-6": [("H-Q", True)],
            "tableau-7": [("S-Q", True)],
        }
    )
    engine = GameEngine(state)

    hints = engine.find_hints()

    assert len(hints) == 1
    assert hints[0].action_type == "DRAW_STOCK"
    assert hints[0].source_pile == "stock"
    assert "Stock" in hints[0].description


def test_scoring_and_undo_redo_restore_score_without_rewinding_timer():
    state = build_state(
        {"tableau-1": [("D-6", False), ("H-A", True)]}
    )
    engine = GameEngine(state)
    state.elapsed_seconds = 31

    engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)

    assert state.score == 15  # +10 foundation, +5 newly exposed card
    assert state.elapsed_seconds == 31
    assert state.tableau["tableau-1"].peek().face_up

    state.elapsed_seconds = 37
    assert engine.undo()
    assert state.score == 0
    assert state.elapsed_seconds == 37
    assert not state.tableau["tableau-1"].cards_bottom_to_top()[0].face_up

    assert engine.redo()
    assert state.score == 15
    assert state.elapsed_seconds == 37
    state.assert_invariants()


def test_waste_to_tableau_scores_five_but_tableau_rearrangement_and_draw_do_not():
    waste_state = build_state(
        {"tableau-1": [("C-9", True)]},
        waste_ids=("H-8",),
    )
    waste_engine = GameEngine(waste_state)
    waste_engine.move_waste_to_tableau("tableau-1")
    assert waste_state.score == 5

    tableau_state = build_state(
        {
            "tableau-1": [("H-8", True)],
            "tableau-2": [("C-9", True)],
        }
    )
    tableau_engine = GameEngine(tableau_state)
    tableau_engine.move_tableau_to_tableau(
        "tableau-1", "H-8", "tableau-2"
    )
    assert tableau_state.score == 0

    tableau_engine.draw_from_stock()
    assert tableau_state.score == 0
