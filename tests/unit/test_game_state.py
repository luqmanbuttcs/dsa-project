from random import Random

import pytest

from solitaire.domain.card import Suit
from solitaire.domain.game_state import GameStatus, Zone, create_new_game


def test_initial_game_has_correct_zone_counts():
    state = create_new_game(Random(2026))

    assert state.stock.size() == 24
    assert state.waste.size() == 0
    assert len(state.tableau) == 7
    assert sum(column.size() for column in state.tableau.values()) == 28
    assert all(pile.size() == 0 for pile in state.foundations.values())
    assert len(state.card_index) == 52
    assert state.status is GameStatus.PLAYING
    state.assert_invariants()


def test_tableau_columns_have_expected_sizes_and_face_states():
    state = create_new_game(Random(17))

    for column_number in range(1, 8):
        column = state.tableau[f"tableau-{column_number}"]
        cards = column.cards_bottom_to_top()

        assert len(cards) == column_number
        assert sum(card.face_up for card in cards) == 1
        assert cards[-1].face_up
        assert all(not card.face_up for card in cards[:-1])


def test_initial_dictionary_entries_match_each_zone():
    state = create_new_game(Random(5))

    assert all(
        entry.zone is Zone.STOCK and entry.pile_id == "stock"
        for card_id, entry in state.card_index.items()
        if card_id in {card.card_id for card in state.stock.to_list()}
    )

    for column_id, column in state.tableau.items():
        for position, card in enumerate(column.cards_bottom_to_top()):
            entry = state.card_index[card.card_id]
            assert entry.zone is Zone.TABLEAU
            assert entry.pile_id == column_id
            assert entry.position == position
            assert entry.face_up is card.face_up


def test_initial_state_has_all_four_empty_foundations():
    state = create_new_game(Random(5))

    assert set(state.foundations) == set(Suit)
    assert all(pile.is_empty() for pile in state.foundations.values())


def test_draw_mode_accepts_only_one_or_three():
    state = create_new_game(Random(8))

    state.set_draw_count(3)
    assert state.draw_count == 3

    with pytest.raises(ValueError):
        state.set_draw_count(2)


def test_card_conservation_invariant_detects_duplicate():
    state = create_new_game(Random(8))
    duplicate = state.tableau["tableau-1"].peek()
    state.tableau["tableau-2"].push(duplicate)

    with pytest.raises(AssertionError):
        state.assert_invariants()


def test_initial_deal_records_all_five_required_data_structures():
    from solitaire.domain.operations import OperationTracker, StructureName

    tracker = OperationTracker()
    state = create_new_game(Random(2027), tracker=tracker)

    assert tracker.count(StructureName.ARRAY_LIST) > 0
    assert tracker.count(StructureName.STACK) == 28
    assert tracker.count(StructureName.QUEUE) == 24
    assert tracker.count(StructureName.LINKED_LIST) == 28
    assert tracker.count(StructureName.DICTIONARY) == 52
    state.assert_invariants()
