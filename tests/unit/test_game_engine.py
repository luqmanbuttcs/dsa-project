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
    source_run_ids: tuple[str, ...] = ("H-8",),
) -> GameState:
    """Build a deterministic tableau move fixture with hidden source cards."""
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    source_run = [cards.pop(card_id) for card_id in source_run_ids]
    destination_card = cards.pop(destination_card_id)

    counts = [5, 5, 4, 4, 4, 3, 3]
    if len(source_run) > counts[0]:
        raise ValueError("Source run is larger than its tableau column")
    tableau = {}

    for column_number, count in enumerate(counts, start=1):
        column_id = f"tableau-{column_number}"
        column = TableauColumn(column_id=column_id)
        hidden_count = count - len(source_run) if column_number == 1 else count - 1

        for _ in range(hidden_count):
            card = cards.pop(next(iter(cards)))
            card.turn_face_down()
            column.push(card)

        if column_number == 1:
            for card in source_run:
                card.turn_face_up()
                column.push(card)
        elif column_number == 2:
            destination_card.turn_face_up()
            column.push(destination_card)
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
    state = arranged_move_state(source_run_ids=("H-A",))
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
    action_events = engine.tracker.events_for_action(engine.move_history[-1].action_id)
    assert sum(
        event.structure is StructureName.STACK and event.operation == "POP"
        for event in action_events
    ) == 1
    assert sum(
        event.structure is StructureName.STACK and event.operation == "PUSH"
        for event in action_events
    ) == 1
    assert sum(
        event.structure is StructureName.LINKED_LIST
        and event.operation == "REMOVE_TOP_NODE"
        for event in action_events
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
    action_events = engine.tracker.events_for_action(engine.move_history[-1].action_id)
    assert sum(
        event.structure is StructureName.STACK and event.operation == "POP"
        for event in action_events
    ) == 1
    assert sum(
        event.structure is StructureName.LINKED_LIST
        and event.operation == "APPEND_NODE"
        for event in action_events
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
    action_events = engine.tracker.events_for_action(engine.move_history[-1].action_id)
    assert any(event.operation == "GAME_WON" for event in action_events)
    state.assert_invariants()

    assert engine.undo()
    assert state.status is GameStatus.PLAYING
    assert tableau["tableau-1"].peek().card_id == "H-K"
    assert engine.redo()
    assert state.status is GameStatus.WON
    state.assert_invariants()



def test_victory_requires_four_complete_ordered_foundations():
    from solitaire.domain.card import Rank
    from solitaire.domain.game_state import GameStatus

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
            card = cards[f"{suit.code}-{rank.label}"]
            card.turn_face_up()
            foundations[suit].push(card)

    index = {}
    for suit, pile in foundations.items():
        for position, card in enumerate(pile.to_list()):
            index[card.card_id] = CardLocation(
                Zone.FOUNDATION,
                f"foundation-{suit.code.lower()}",
                position,
                card.face_up,
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

    engine = GameEngine(state)
    assert engine.has_won()
    engine._update_win_status("test-complete")
    assert state.status is GameStatus.WON


def test_victory_is_false_when_foundation_order_is_corrupted():
    from solitaire.domain.card import Rank

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
            card = cards[f"{suit.code}-{rank.label}"]
            card.turn_face_up()
            foundations[suit].push(card)

    # Swap the first two Hearts in a deliberately invalid test state.
    hearts = foundations[Suit.HEARTS].to_list()
    hearts[0], hearts[1] = hearts[1], hearts[0]
    foundations[Suit.HEARTS].clear()
    for card in hearts:
        foundations[Suit.HEARTS].push(card)

    index = {}
    for suit, pile in foundations.items():
        for position, card in enumerate(pile.to_list()):
            index[card.card_id] = CardLocation(
                Zone.FOUNDATION,
                f"foundation-{suit.code.lower()}",
                position,
                card.face_up,
            )

    state = GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )
    engine = GameEngine(state)

    assert not engine.has_won()
    try:
        state.assert_invariants()
    except AssertionError:
        pass
    else:
        raise AssertionError("Expected corrupted foundation ordering to fail invariants")



def test_tableau_move_transfers_entire_face_up_sequence_in_original_order():
    state = arranged_move_state(
        destination_card_id="H-10",
        source_run_ids=("C-9", "H-8"),
    )
    engine = GameEngine(state)

    source = state.tableau["tableau-1"]
    destination = state.tableau["tableau-2"]
    source_hidden_card = source.cards_bottom_to_top()[-3]

    moved = engine.move_tableau_to_tableau(
        "tableau-1", "C-9", "tableau-2"
    )

    assert [card.card_id for card in moved] == ["C-9", "H-8"]
    assert [card.card_id for card in destination.cards_bottom_to_top()[-2:]] == [
        "C-9", "H-8"
    ]
    assert source.peek() is source_hidden_card
    assert source.peek().face_up
    assert state.card_index["C-9"].pile_id == "tableau-2"
    assert state.card_index["H-8"].pile_id == "tableau-2"
    state.assert_invariants()



def test_foundation_stack_accepts_ace_then_two_and_keeps_lifo_top():
    from solitaire.domain.card import Rank

    deck = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    ace = deck.pop("H-A")
    two = deck.pop("H-2")
    ace.turn_face_up()
    two.turn_face_up()

    stock = Queue()
    for card in deck.values():
        card.turn_face_down()
        stock.enqueue(card)

    waste = Stack()
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    tableau["tableau-1"].push(two)
    foundations = {suit: Stack() for suit in Suit}
    foundations[Suit.HEARTS].push(ace)

    index = {}
    for position, card in enumerate(stock.to_list()):
        index[card.card_id] = CardLocation(
            Zone.STOCK, "stock", position, card.face_up
        )
    index[ace.card_id] = CardLocation(
        Zone.FOUNDATION, "foundation-h", 0, ace.face_up
    )
    index[two.card_id] = CardLocation(
        Zone.TABLEAU, "tableau-1", 0, two.face_up
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

    pile = state.foundations[Suit.HEARTS]
    assert moved is two
    assert pile.to_list() == [ace, two]
    assert pile.peek() is two
    assert pile.linked_list.validate()
    assert state.card_index["H-2"].zone is Zone.FOUNDATION
    assert state.card_index["H-2"].position == 1
    state.assert_invariants()



def test_undo_redo_restores_tableau_move_card_flip_and_dictionary():
    state = arranged_move_state()
    engine = GameEngine(state)
    source = state.tableau["tableau-1"]
    destination = state.tableau["tableau-2"]
    original_source_ids = [card.card_id for card in source.cards_bottom_to_top()]
    original_destination_ids = [
        card.card_id for card in destination.cards_bottom_to_top()
    ]
    original_index = dict(state.card_index)
    exposed_card = source.cards_bottom_to_top()[-2]

    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")
    assert engine.can_undo
    assert not engine.can_redo
    assert exposed_card.face_up

    assert engine.undo()
    assert [card.card_id for card in source.cards_bottom_to_top()] == original_source_ids
    assert [
        card.card_id for card in destination.cards_bottom_to_top()
    ] == original_destination_ids
    assert not exposed_card.face_up
    assert state.card_index == original_index
    assert state.move_count == 0
    assert engine.move_history == []
    assert not engine.can_undo
    assert engine.can_redo
    assert engine.tracker.events[-1].context == "UNDO"
    assert engine.tracker.events[-1].operation == "UNDO_COMPLETE"
    state.assert_invariants()

    assert engine.redo()
    assert source.peek() is exposed_card
    assert exposed_card.face_up
    assert destination.peek().card_id == "H-8"
    assert state.move_count == 1
    assert len(engine.move_history) == 1
    assert engine.can_undo
    assert not engine.can_redo
    assert engine.tracker.events[-1].context == "REDO"
    assert engine.tracker.events[-1].operation == "REDO_COMPLETE"
    state.assert_invariants()


def test_undo_redo_restores_draw_three_queue_order_and_face_states():
    state = create_new_game(Random(901), draw_count=3)
    engine = GameEngine(state)
    original_stock_ids = [card.card_id for card in state.stock.to_list()]
    original_index = dict(state.card_index)

    drawn = engine.draw_from_stock()
    after_draw_stock_ids = [card.card_id for card in state.stock.to_list()]
    after_draw_waste_ids = [card.card_id for card in state.waste.to_list()]
    after_draw_index = dict(state.card_index)

    assert len(drawn) == 3
    assert engine.undo()
    assert [card.card_id for card in state.stock.to_list()] == original_stock_ids
    assert state.waste.is_empty()
    assert state.card_index == original_index
    assert all(not card.face_up for card in state.stock.to_list())
    assert state.move_count == 0
    state.assert_invariants()

    assert engine.redo()
    assert [card.card_id for card in state.stock.to_list()] == after_draw_stock_ids
    assert [card.card_id for card in state.waste.to_list()] == after_draw_waste_ids
    assert state.card_index == after_draw_index
    assert all(card.face_up for card in state.waste.to_list())
    assert state.move_count == 1
    state.assert_invariants()


def test_undo_redo_restores_stock_recycle_as_one_atomic_action():
    state = create_new_game(Random(902), draw_count=3)
    engine = GameEngine(state)

    while not state.stock.is_empty():
        engine.draw_from_stock()

    original_waste_ids = [card.card_id for card in state.waste.to_list()]
    original_index = dict(state.card_index)
    assert state.stock.is_empty()
    assert len(original_waste_ids) == 24

    engine.draw_from_stock(1)
    after_stock_ids = [card.card_id for card in state.stock.to_list()]
    after_waste_ids = [card.card_id for card in state.waste.to_list()]
    after_index = dict(state.card_index)

    assert engine.undo()
    assert state.stock.is_empty()
    assert [card.card_id for card in state.waste.to_list()] == original_waste_ids
    assert state.card_index == original_index
    assert all(card.face_up for card in state.waste.to_list())
    state.assert_invariants()

    assert engine.redo()
    assert [card.card_id for card in state.stock.to_list()] == after_stock_ids
    assert [card.card_id for card in state.waste.to_list()] == after_waste_ids
    assert state.card_index == after_index
    state.assert_invariants()


def test_undo_redo_restores_tableau_to_foundation_and_exposed_card():
    state = arranged_move_state(source_run_ids=("H-A",))
    engine = GameEngine(state)
    source = state.tableau["tableau-1"]
    original_source_ids = [card.card_id for card in source.cards_bottom_to_top()]
    exposed_card = source.cards_bottom_to_top()[-2]

    engine.move_tableau_to_foundation("tableau-1", Suit.HEARTS)
    assert state.foundations[Suit.HEARTS].peek().card_id == "H-A"
    assert exposed_card.face_up

    assert engine.undo()
    assert [card.card_id for card in source.cards_bottom_to_top()] == original_source_ids
    assert state.foundations[Suit.HEARTS].is_empty()
    assert not exposed_card.face_up
    assert state.card_index["H-A"].zone is Zone.TABLEAU
    state.assert_invariants()

    assert engine.redo()
    assert source.peek() is exposed_card
    assert exposed_card.face_up
    assert state.foundations[Suit.HEARTS].peek().card_id == "H-A"
    assert state.card_index["H-A"].zone is Zone.FOUNDATION
    state.assert_invariants()


def test_new_successful_action_after_undo_clears_redo_history():
    state = arranged_move_state()
    engine = GameEngine(state)

    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")
    assert engine.undo()
    assert engine.can_redo

    engine.draw_from_stock(1)

    assert not engine.can_redo
    assert engine.can_undo
    assert state.move_count == 1
    state.assert_invariants()


def test_empty_undo_and_redo_return_false_without_mutating_state():
    state = create_new_game(Random(903))
    engine = GameEngine(state)
    original_index = dict(state.card_index)
    original_stock_ids = [card.card_id for card in state.stock.to_list()]

    assert not engine.undo()
    assert not engine.redo()
    assert state.card_index == original_index
    assert [card.card_id for card in state.stock.to_list()] == original_stock_ids
    assert state.move_count == 0
    state.assert_invariants()
