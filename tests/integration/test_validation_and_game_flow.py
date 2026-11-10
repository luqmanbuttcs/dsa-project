"""Integration coverage for Klondike rules, flips, victory, and game flow."""

from __future__ import annotations

from random import Random

import pytest

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.game_engine import GameEngine, InvalidMoveError
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    GameStatus,
    TableauColumn,
    Zone,
    create_new_game,
)
from solitaire.domain.rules import MoveError
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack


def build_tableau_state(
    source_run_ids: tuple[str, ...],
    destination_card_id: str,
    *,
    hidden_card_id: str = "D-6",
) -> GameState:
    """Build a deterministic, invariant-valid game state for move tests."""
    ids = (*source_run_ids, destination_card_id, hidden_card_id)
    if len(set(ids)) != len(ids):
        raise ValueError("Fixture card IDs must be unique")

    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    hidden = cards.pop(hidden_card_id)
    destination_card = cards.pop(destination_card_id)
    moving_cards = [cards.pop(card_id) for card_id in source_run_ids]

    hidden.turn_face_down()
    destination_card.turn_face_up()
    for card in moving_cards:
        card.turn_face_up()

    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    tableau["tableau-1"].push(hidden)
    for card in moving_cards:
        tableau["tableau-1"].push(card)
    tableau["tableau-2"].push(destination_card)

    stock = Queue()
    for card in cards.values():
        card.turn_face_down()
        stock.enqueue(card)

    waste = Stack()
    foundations = {suit: Stack() for suit in Suit}
    index = {}
    for position, card in enumerate(stock.to_list()):
        index[card.card_id] = CardLocation(
            Zone.STOCK, "stock", position, card.face_up
        )
    for column_id, column in tableau.items():
        for position, card in enumerate(column.cards_bottom_to_top()):
            index[card.card_id] = CardLocation(
                Zone.TABLEAU, column_id, position, card.face_up
            )

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )
    state.assert_invariants()
    return state


def build_four_king_endgame() -> GameState:
    """Create a valid deterministic endgame: four King cards remain in tableau."""
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    stock = Queue()
    waste = Stack()
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    foundations = {suit: Stack() for suit in Suit}

    for suit in Suit:
        for rank in Rank:
            card = cards.pop(f"{suit.code}-{rank.label}")
            card.turn_face_up()
            if rank is Rank.KING:
                column_id = f"tableau-{list(Suit).index(suit) + 1}"
                tableau[column_id].push(card)
            else:
                foundations[suit].push(card)

    index = {}
    for suit, pile in foundations.items():
        pile_id = f"foundation-{suit.code.lower()}"
        for position, card in enumerate(pile.to_list()):
            index[card.card_id] = CardLocation(
                Zone.FOUNDATION, pile_id, position, card.face_up
            )
    for column_id, column in tableau.items():
        for position, card in enumerate(column.cards_bottom_to_top()):
            index[card.card_id] = CardLocation(
                Zone.TABLEAU, column_id, position, card.face_up
            )

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
        status=GameStatus.PLAYING,
    )
    state.assert_invariants()
    return state


def test_new_game_initialization_has_correct_zones_and_visibility():
    state = create_new_game(Random(4101))

    assert len(state.cards_in_play()) == 52
    assert state.stock.size() == 24
    assert state.waste.is_empty()
    assert sum(column.size() for column in state.tableau.values()) == 28
    assert len(state.tableau) == 7

    for number in range(1, 8):
        column = state.tableau[f"tableau-{number}"]
        cards = column.cards_bottom_to_top()
        assert len(cards) == number
        assert all(not card.face_up for card in cards[:-1])
        assert cards[-1].face_up

    assert all(pile.is_empty() for pile in state.foundations.values())
    state.assert_invariants()


def test_legal_tableau_move_checks_alternating_color_and_sequential_rank():
    state = build_tableau_state(
        source_run_ids=("H-8", "C-7"),
        destination_card_id="S-9",
        hidden_card_id="D-6",
    )
    engine = GameEngine(state)

    moved = engine.move_tableau_to_tableau(
        "tableau-1", "H-8", "tableau-2"
    )

    assert [card.card_id for card in moved] == ["H-8", "C-7"]
    assert [
        card.card_id
        for card in state.tableau["tableau-2"].cards_bottom_to_top()
    ][-2:] == ["H-8", "C-7"]
    state.assert_invariants()


@pytest.mark.parametrize(
    ("source_run_ids", "destination_card_id", "selected_card_id", "reason"),
    [
        (("H-8",), "D-9", "H-8", MoveError.SAME_TABLEAU_COLOR),
        (("H-8",), "C-10", "H-8", MoveError.WRONG_TABLEAU_RANK),
        (("H-8", "D-7"), "C-9", "H-8", MoveError.SAME_TABLEAU_COLOR),
        (("H-8",), "C-9", "D-6", MoveError.CARD_FACE_DOWN),
    ],
)
def test_illegal_tableau_moves_are_rejected_without_state_mutation(
    source_run_ids, destination_card_id, selected_card_id, reason
):
    state = build_tableau_state(
        source_run_ids=source_run_ids,
        destination_card_id=destination_card_id,
        hidden_card_id="D-6",
    )
    engine = GameEngine(state)
    before_source = [
        card.card_id
        for card in state.tableau["tableau-1"].cards_bottom_to_top()
    ]
    before_destination = [
        card.card_id
        for card in state.tableau["tableau-2"].cards_bottom_to_top()
    ]
    before_index = dict(state.card_index)
    before_move_count = state.move_count

    with pytest.raises(InvalidMoveError) as error:
        engine.move_tableau_to_tableau(
            "tableau-1", selected_card_id, "tableau-2"
        )

    assert error.value.result.reason is reason
    assert [
        card.card_id
        for card in state.tableau["tableau-1"].cards_bottom_to_top()
    ] == before_source
    assert [
        card.card_id
        for card in state.tableau["tableau-2"].cards_bottom_to_top()
    ] == before_destination
    assert state.card_index == before_index
    assert state.move_count == before_move_count
    assert not engine.can_undo
    assert engine.tracker.events[-1].operation == "MOVE_REJECTED"
    state.assert_invariants()


def test_moving_tableau_card_flips_newly_exposed_card_and_updates_index():
    state = build_tableau_state(
        source_run_ids=("H-8",),
        destination_card_id="C-9",
        hidden_card_id="D-6",
    )
    engine = GameEngine(state)
    newly_exposed = state.tableau["tableau-1"].cards_bottom_to_top()[0]
    assert not newly_exposed.face_up

    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")

    assert newly_exposed.face_up
    location = state.card_index[newly_exposed.card_id]
    assert location.zone is Zone.TABLEAU
    assert location.pile_id == "tableau-1"
    assert location.position == 0
    assert location.face_up

    flips = [
        event for event in engine.tracker.events
        if event.operation == "CARD_FLIPPED"
        and newly_exposed.card_id in event.card_ids
    ]
    assert len(flips) == 1
    state.assert_invariants()


def test_foundation_accepts_only_same_suit_next_rank_through_engine():
    state = build_tableau_state(
        source_run_ids=("H-A",),
        destination_card_id="C-9",
        hidden_card_id="H-2",
    )
    engine = GameEngine(state)

    ace = engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)
    assert ace.card_id == "H-A"
    assert state.tableau["tableau-1"].peek().card_id == "H-2"
    assert state.tableau["tableau-1"].peek().face_up

    two = engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)
    assert two.card_id == "H-2"
    assert [
        card.card_id for card in state.foundations[Suit.HEARTS].to_list()
    ] == ["H-A", "H-2"]
    state.assert_invariants()


def test_fourth_king_completes_game_and_undo_redo_restore_win_state():
    state = build_four_king_endgame()
    engine = GameEngine(state)

    for index, suit in enumerate(Suit, start=1):
        moved = engine.move_tableau_to_foundation(f"tableau-{index}", suit)
        assert moved.rank is Rank.KING
        if suit is not list(Suit)[-1]:
            assert state.status is GameStatus.PLAYING
            assert not engine.has_won()

    assert state.status is GameStatus.WON
    assert engine.has_won()
    assert sum(pile.size() for pile in state.foundations.values()) == 52
    assert all(column.is_empty() for column in state.tableau.values())
    state.assert_invariants()

    assert engine.undo()
    assert state.status is GameStatus.PLAYING
    assert not engine.has_won()
    assert state.tableau["tableau-4"].peek().card_id == "S-K"
    state.assert_invariants()

    assert engine.redo()
    assert state.status is GameStatus.WON
    assert engine.has_won()
    state.assert_invariants()


def test_initialized_engine_obeys_game_status_after_win():
    state = build_four_king_endgame()
    engine = GameEngine(state)
    for index, suit in enumerate(Suit, start=1):
        engine.move_tableau_to_foundation(f"tableau-{index}", suit)

    assert state.status is GameStatus.WON
    with pytest.raises(RuntimeError, match="not currently playable"):
        engine.draw_from_stock()
    state.assert_invariants()



@pytest.mark.parametrize("seed", [5101, 5102, 5103, 5104, 5105])
def test_random_legal_hint_sequences_preserve_all_cards_and_dictionary(seed):
    """Exercise many valid actions without ever losing or duplicating a card."""
    rng = Random(seed)
    state = create_new_game(rng)
    engine = GameEngine(state)
    engine.set_draw_count(rng.choice((1, 3)))

    successful_actions = 0
    for _ in range(80):
        hints = engine.find_hints()
        if not hints:
            break

        hint = rng.choice(hints)
        if hint.action_type == "DRAW_STOCK":
            engine.draw_from_stock()
        elif hint.action_type == "WASTE_TO_TABLEAU":
            engine.move_waste_to_tableau(hint.destination_pile)
        elif hint.action_type == "WASTE_TO_FOUNDATION":
            suit = next(
                suit for suit in Suit
                if hint.destination_pile == f"foundation-{suit.code.lower()}"
            )
            engine.move_waste_to_foundation(suit)
        elif hint.action_type == "TABLEAU_TO_FOUNDATION":
            suit = next(
                suit for suit in Suit
                if hint.destination_pile == f"foundation-{suit.code.lower()}"
            )
            engine.move_tableau_to_foundation(hint.source_pile, suit)
        elif hint.action_type == "TABLEAU_TO_TABLEAU":
            engine.move_tableau_to_tableau(
                hint.source_pile,
                hint.card_ids[0],
                hint.destination_pile,
            )
        else:
            pytest.fail(f"Unknown hint action type: {hint.action_type}")

        successful_actions += 1
        state.assert_invariants()
        cards = state.cards_in_play()
        assert len(cards) == 52
        assert len({card.card_id for card in cards}) == 52
        assert set(state.card_index) == {card.card_id for card in cards}

        if state.status is GameStatus.WON:
            break

    assert successful_actions > 0
    state.assert_invariants()
