from random import Random

import pytest

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.game_engine import GameEngine, InvalidMoveError
from solitaire.domain.game_state import CardLocation, GameState, TableauColumn, Zone, create_new_game
from solitaire.domain.operations import OperationTracker, StructureName
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack


def arranged_move_state(
    destination_card_id: str = "C-9",
    source_card_id: str = "H-8",
) -> GameState:
    """Build a deterministic 8H tableau move with a hidden source card."""
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    source_card = cards.pop(source_card_id)
    destination_card = cards.pop(destination_card_id)

    counts = [5, 5, 4, 4, 4, 3, 3]
    tableau = {}

    for column_number, count in enumerate(counts, start=1):
        column_id = f"tableau-{column_number}"
        column = TableauColumn(column_id=column_id)

        for _ in range(count - 1):
            card = cards.pop(next(iter(cards)))
            card.turn_face_down()
            column.push(card)

        if column_number == 1:
            top = source_card
        elif column_number == 2:
            top = destination_card
        else:
            top = cards.pop(next(iter(cards)))

        top.turn_face_up()
        column.push(top)
        tableau[column_id] = column

    stock = Queue()
    for card in cards.values():
        card.turn_face_down()
        stock.enqueue(card)

    assert stock.size() == 24

    waste = Stack()
    foundations = {suit: Stack() for suit in Suit}
    index = {}

    for position, card in enumerate(stock.to_list()):
        index[card.card_id] = CardLocation(Zone.STOCK, "stock", position, card.face_up)

    for column_id, column in tableau.items():
        for position, card in enumerate(column.cards_bottom_to_top()):
            index[card.card_id] = CardLocation(
                Zone.TABLEAU, column_id, position, card.face_up
            )

    return GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )


def test_draw_three_uses_queue_fifo_and_pushes_to_waste():
    tracker = OperationTracker()
    state = create_new_game(Random(101), draw_count=3, tracker=tracker)
    expected = state.stock.to_list()[:3]
    engine = GameEngine(state, tracker)

    drawn = engine.draw_from_stock()
    action_id = engine.move_history[-1].action_id
    action_events = tracker.events_for_action(action_id)

    assert drawn == expected
    assert state.stock.size() == 21
    assert state.waste.size() == 3
    assert state.waste.peek() is expected[-1]

    assert sum(
        event.structure is StructureName.QUEUE and event.operation == "DEQUEUE"
        for event in action_events
    ) == 3
    assert sum(
        event.structure is StructureName.STACK and event.operation == "PUSH"
        for event in action_events
    ) == 3

    for card in expected:
        location = state.card_index[card.card_id]
        assert location.zone is Zone.WASTE
        assert location.pile_id == "waste"
        assert location.face_up

    state.assert_invariants()


def test_draw_mode_can_be_set_to_one_or_three():
    state = create_new_game(Random(55))
    engine = GameEngine(state)

    engine.set_draw_count(3)
    assert state.draw_count == 3

    engine.set_draw_count(1)
    assert state.draw_count == 1


def test_empty_stock_recycles_waste_in_reverse_stack_order():
    state = create_new_game(Random(44), draw_count=3)
    engine = GameEngine(state)

    while not state.stock.is_empty():
        engine.draw_from_stock()

    previous_waste_top = state.waste.peek()
    assert state.stock.is_empty()
    assert state.waste.size() == 24

    drawn = engine.draw_from_stock(1)

    assert drawn == [previous_waste_top]
    assert state.stock.size() == 23
    assert state.waste.size() == 1
    state.assert_invariants()


def test_move_tableau_run_uses_linked_list_and_updates_dictionary():
    state = arranged_move_state()
    engine = GameEngine(state)

    source = state.tableau["tableau-1"]
    destination = state.tableau["tableau-2"]
    exposed_card = source.cards_bottom_to_top()[-2]

    moved = engine.move_tableau_to_tableau(
        "tableau-1", "H-8", "tableau-2"
    )

    assert [card.card_id for card in moved] == ["H-8"]
    assert destination.peek().card_id == "H-8"
    assert source.peek() is exposed_card
    assert source.peek().face_up

    moved_location = state.card_index["H-8"]
    assert moved_location.zone is Zone.TABLEAU
    assert moved_location.pile_id == "tableau-2"
    assert moved_location.face_up

    exposed_location = state.card_index[exposed_card.card_id]
    assert exposed_location.face_up
    assert engine.tracker.count_operation(
        StructureName.LINKED_LIST, "DETACH_RUN"
    ) == 1
    assert engine.tracker.count_operation(
        StructureName.LINKED_LIST, "ATTACH_RUN"
    ) == 1
    assert engine.tracker.count_operation(
        StructureName.GAME, "CARD_FLIPPED"
    ) == 1
    state.assert_invariants()


def test_invalid_tableau_move_does_not_mutate_piles():
    state = arranged_move_state(destination_card_id="D-9")
    engine = GameEngine(state)

    before_source = state.tableau["tableau-1"].cards_bottom_to_top()
    before_destination = state.tableau["tableau-2"].cards_bottom_to_top()
    before_index = dict(state.card_index)
    before_move_count = state.move_count

    # 8♥ cannot be placed on 9♦ because both cards are red.
    with pytest.raises(InvalidMoveError):
        engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")

    assert state.tableau["tableau-1"].cards_bottom_to_top() == before_source
    assert state.tableau["tableau-2"].cards_bottom_to_top() == before_destination
    assert state.card_index == before_index
    assert state.move_count == before_move_count
    assert engine.tracker.events[-1].outcome == "REJECTED"
    state.assert_invariants()



def move_card_from_stock_to_waste(state: GameState, card_id: str) -> Card:
    """Test helper that relocates one stock card to waste and reindexes."""
    stock_cards = state.stock.to_list()
    selected = next(card for card in stock_cards if card.card_id == card_id)

    state.stock = Queue()
    for card in stock_cards:
        if card.card_id != card_id:
            state.stock.enqueue(card)

    selected.turn_face_up()
    state.waste.push(selected)

    for position, card in enumerate(state.stock.to_list()):
        state.card_index[card.card_id] = CardLocation(
            Zone.STOCK, "stock", position, card.face_up
        )
    for position, card in enumerate(state.waste.to_list()):
        state.card_index[card.card_id] = CardLocation(
            Zone.WASTE, "waste", position, card.face_up
        )
    return selected


def test_tableau_to_foundation_uses_stacks_and_updates_dictionary():
    state = arranged_move_state(source_card_id="H-A")
    engine = GameEngine(state)
    source = state.tableau["tableau-1"]
    newly_exposed = source.cards_bottom_to_top()[-2]

    moved = engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)

    assert moved.card_id == "H-A"
    assert state.foundations[Suit.HEARTS].peek() is moved
    assert source.peek() is newly_exposed
    assert newly_exposed.face_up
    assert state.card_index["H-A"].zone is Zone.FOUNDATION
    assert state.card_index["H-A"].pile_id == "foundation-h"
    assert state.card_index[newly_exposed.card_id].face_up
    assert engine.tracker.count_operation(StructureName.STACK, "POP") == 1
    assert engine.tracker.count_operation(StructureName.STACK, "PUSH") == 1
    assert engine.tracker.count_operation(
        StructureName.LINKED_LIST, "REMOVE_TOP_NODE"
    ) == 1
    state.assert_invariants()


def test_waste_to_tableau_uses_stack_and_linked_list():
    state = arranged_move_state(destination_card_id="D-9")
    selected = move_card_from_stock_to_waste(state, "C-8")
    engine = GameEngine(state)

    moved = engine.move_waste_to_tableau("tableau-2")

    assert moved is selected
    assert state.tableau["tableau-2"].peek() is selected
    assert state.waste.is_empty()
    location = state.card_index[selected.card_id]
    assert location.zone is Zone.TABLEAU
    assert location.pile_id == "tableau-2"
    assert engine.tracker.count_operation(
        StructureName.STACK, "POP"
    ) == 1
    assert engine.tracker.count_operation(
        StructureName.LINKED_LIST, "APPEND_NODE"
    ) == 1
    state.assert_invariants()


def test_waste_to_foundation_moves_ace_using_stacks():
    state = arranged_move_state()
    selected = move_card_from_stock_to_waste(state, "S-A")
    engine = GameEngine(state)

    moved = engine.move_waste_to_foundation(Suit.SPADES)

    assert moved is selected
    assert state.waste.is_empty()
    assert state.foundations[Suit.SPADES].peek() is selected
    assert state.card_index[selected.card_id].zone is Zone.FOUNDATION
    state.assert_invariants()


def test_last_foundation_card_triggers_win_detection():
    from solitaire.domain.card import Rank
    from solitaire.domain.game_state import GameStatus

    full_deck = DeckFactory.create_standard_deck()
    cards = {card.card_id: card for card in full_deck}
    stock = Queue()
    waste = Stack()
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    foundations = {suit: Stack() for suit in Suit}

    for suit in Suit:
        for rank in Rank:
            card = cards[f"{suit.code}-{rank.label}"]
            card.turn_face_up()
            if suit is Suit.HEARTS and rank is Rank.KING:
                tableau["tableau-1"].push(card)
            else:
                foundations[suit].push(card)

    index = {}
    for suit, pile in foundations.items():
        pile_id = f"foundation-{suit.code.lower()}"
        for position, card in enumerate(pile.to_list()):
            index[card.card_id] = CardLocation(
                Zone.FOUNDATION, pile_id, position, card.face_up
            )

    king = tableau["tableau-1"].peek()
    index[king.card_id] = CardLocation(
        Zone.TABLEAU, "tableau-1", 0, king.face_up
    )

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )
    state.assert_invariants()
    engine = GameEngine(state)

    moved = engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)

    assert moved.card_id == "H-K"
    assert state.status is GameStatus.WON
    assert engine.has_won()
    assert sum(pile.size() for pile in state.foundations.values()) == 52
    assert engine.tracker.events[-1].operation == "GAME_WON"
    state.assert_invariants()
