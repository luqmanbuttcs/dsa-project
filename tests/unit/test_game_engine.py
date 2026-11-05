from random import Random

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.game_engine import GameEngine, InvalidMoveError
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    GameStatus,
    TableauColumn,
    Zone,
    create_new_game,
)
from solitaire.domain.operations import OperationTracker, StructureName
from solitaire.domain.deck import DeckFactory
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack


def arranged_move_state() -> GameState:
    """Build a deterministic legal 8H-on-9C move with a hidden card to reveal."""
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    eight_hearts = cards.pop("H-8")
    nine_clubs = cards.pop("C-9")

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
            top = eight_hearts
        elif column_number == 2:
            top = nine_clubs
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
    state = create_new_game(Random(101), tracker=tracker)
    expected = state.stock.to_list()[:3]
    engine = GameEngine(state, tracker)

    drawn = engine.draw_from_stock()

    assert drawn == expected
    assert state.stock.size() == 21
    assert state.waste.size() == 3
    assert state.waste.peek() is expected[-1]
    assert tracker.count_operation(StructureName.QUEUE, "DEQUEUE") == 3
    assert tracker.count_operation(StructureName.STACK, "PUSH") == 3

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
    state = arranged_move_state()
    engine = GameEngine(state)

    before_source = state.tableau["tableau-1"].cards_bottom_to_top()
    before_destination = state.tableau["tableau-2"].cards_bottom_to_top()
    before_index = dict(state.card_index)

    # 8♥ on 9♣ is legal, so use a same-color 9♦ destination instead.
    original_destination = state.tableau["tableau-2"]
    replacement = TableauColumn("tableau-2")
    old_cards = original_destination.cards_bottom_to_top()
    for card in old_cards[:-1]:
        replacement.push(card)
    nine_diamonds = Card(Suit.DIAMONDS, Rank.NINE, face_up=True)
    # Replace the card object in the same slot while keeping the deck at 52:
    # swap it with the old 9♣ and update the stock/index locations.
    nine_clubs = original_destination.pop()
    replacement.push(nine_diamonds)
    state.tableau["tableau-2"] = replacement
    state.stock.enqueue(nine_clubs)
    state.card_index.pop(nine_clubs.card_id)
    state.card_index[nine_diamonds.card_id] = CardLocation(
        Zone.TABLEAU, "tableau-2", replacement.size() - 1, True
    )
    # A duplicate 9D may already exist, so the invariant is not used for this
    # deliberately invalid-move fixture; the rule must reject before mutation.
    with pytest.raises(InvalidMoveError):
        engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")

    assert state.tableau["tableau-1"].cards_bottom_to_top() == before_source
    assert state.move_count == 0
