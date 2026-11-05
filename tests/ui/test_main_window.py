"""Offscreen smoke tests for the interactive PyQt6 game board."""

from __future__ import annotations

import os
from random import Random

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.game_engine import GameEngine
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    TableauColumn,
    Zone,
    create_new_game,
)
from solitaire.structures.queue import Queue
from solitaire.structures.stack import Stack
from solitaire.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def build_waste_ace_state() -> GameState:
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    ace = cards.pop("H-A")
    ace.turn_face_up()

    stock = Queue()
    waste = Stack()
    waste.push(ace)
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    foundations = {suit: Stack() for suit in Suit}

    for card in cards.values():
        card.turn_face_down()
        stock.enqueue(card)

    index = {
        card.card_id: CardLocation(
            Zone.STOCK, "stock", position, card.face_up
        )
        for position, card in enumerate(stock.to_list())
    }
    index[ace.card_id] = CardLocation(Zone.WASTE, "waste", 0, True)

    return GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )


def build_tableau_move_state() -> GameState:
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    hidden = cards.pop("C-7")
    moving = cards.pop("H-8")
    destination_top = cards.pop("C-9")
    hidden.turn_face_down()
    moving.turn_face_up()
    destination_top.turn_face_up()

    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    tableau["tableau-1"].push(hidden)
    tableau["tableau-1"].push(moving)
    tableau["tableau-2"].push(destination_top)

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

    return GameState(
        stock=stock,
        waste=waste,
        tableau=tableau,
        foundations=foundations,
        card_index=index,
    )


def test_window_renders_stock_waste_four_foundations_and_seven_tableau_columns(app):
    engine = GameEngine(create_new_game(Random(1201)))
    window = MainWindow(engine)

    assert window.windowTitle().startswith("Klondike Solitaire")
    assert window.stock_button.objectName() == "stock-button"
    assert engine.state.stock.size() == 24
    assert len(window.foundation_widgets) == 4
    assert len(window.tableau_widgets) == 7

    for number in range(1, 8):
        column = engine.state.tableau[f"tableau-{number}"]
        widget = window.tableau_widgets[f"tableau-{number}"]
        assert column.size() == number
        assert len(widget.card_buttons) == number

    assert all(engine.state.foundations[suit].is_empty() for suit in Suit)
    assert not window.undo_button.isEnabled()
    assert not window.redo_button.isEnabled()
    window.close()


def test_stock_draw_undo_and_redo_buttons_are_connected(app):
    engine = GameEngine(create_new_game(Random(1202)))
    window = MainWindow(engine)

    window.stock_button.click()
    assert engine.state.stock.size() == 23
    assert engine.state.waste.size() == 1
    assert engine.state.move_count == 1
    assert window.undo_button.isEnabled()

    window.undo_button.click()
    assert engine.state.stock.size() == 24
    assert engine.state.waste.is_empty()
    assert window.redo_button.isEnabled()

    window.redo_button.click()
    assert engine.state.stock.size() == 23
    assert engine.state.waste.size() == 1
    assert engine.state.move_count == 1
    window.close()


def test_draw_mode_combo_selects_draw_three(app):
    engine = GameEngine(create_new_game(Random(1203)))
    window = MainWindow(engine)

    window.draw_mode_combo.setCurrentIndex(window.draw_mode_combo.findData(3))
    assert engine.state.draw_count == 3

    window.stock_button.click()
    assert engine.state.stock.size() == 21
    assert engine.state.waste.size() == 3
    assert len(window.waste_widget.card_buttons) == 3
    window.close()


def test_waste_selection_and_foundation_target_perform_real_game_move(app):
    engine = GameEngine(build_waste_ace_state())
    window = MainWindow(engine)

    top_waste_card = window.waste_widget.card_buttons[-1]
    top_waste_card.click()
    assert window.selected_card_id == "H-A"

    hearts_foundation = window.foundation_widgets[Suit.HEARTS]
    hearts_foundation._button.click()

    assert engine.state.waste.is_empty()
    assert engine.state.foundations[Suit.HEARTS].peek().card_id == "H-A"
    assert engine.state.move_count == 1

    window.undo_button.click()
    assert engine.state.foundations[Suit.HEARTS].is_empty()
    assert engine.state.waste.peek().card_id == "H-A"
    window.close()


def test_tableau_card_clicks_select_and_move_face_up_card(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)

    source_widget = window.tableau_widgets["tableau-1"]
    destination_widget = window.tableau_widgets["tableau-2"]
    source_card = next(
        button for button in source_widget.card_buttons if button.card_id == "H-8"
    )
    destination_card = next(
        button for button in destination_widget.card_buttons if button.card_id == "C-9"
    )

    source_card.click()
    assert window.selected_card_id == "H-8"

    # Selection refreshes the card widgets so the destination highlight state
    # is current; query the refreshed board rather than a stale widget object.
    destination_card = next(
        button
        for button in window.tableau_widgets["tableau-2"].card_buttons
        if button.card_id == "C-9"
    )
    destination_card.click()

    source = engine.state.tableau["tableau-1"]
    destination = engine.state.tableau["tableau-2"]
    assert source.peek().card_id == "C-7"
    assert source.peek().face_up
    assert destination.peek().card_id == "H-8"
    assert engine.state.card_index["H-8"].pile_id == "tableau-2"
    assert window.selected_card_id is None
    engine.state.assert_invariants()
    window.close()


def test_new_game_reinitializes_all_piles_and_history(app):
    engine = GameEngine(create_new_game(Random(1204)))
    window = MainWindow(engine)
    window.stock_button.click()
    assert engine.can_undo

    window.new_game_button.click()
    assert window.engine is not engine
    assert window.engine.state.stock.size() == 24
    assert window.engine.state.waste.is_empty()
    assert all(
        window.engine.state.tableau[f"tableau-{number}"].size() == number
        for number in range(1, 8)
    )
    assert not window.engine.can_undo
    assert window.moves_label.text() == "MOVES  0"
    window.close()



def test_hint_button_selects_the_source_for_a_legal_move(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)

    window.hint_button.click()

    assert window.selected_card_id == "H-8"
    assert window._selected_pile_id == "tableau-1"
    assert "Hint 1/1" in window.status_label.text()
    assert "Tableau 2" in window.status_label.text()
    window.close()


def test_score_label_and_timer_track_actions_and_survive_undo(app, monkeypatch):
    import solitaire.ui.main_window as main_window_module

    clock = [100.0]
    monkeypatch.setattr(main_window_module, "monotonic", lambda: clock[0])
    engine = GameEngine(build_waste_ace_state())
    window = MainWindow(engine)

    assert window.timer_label.text() == "TIME  00:00"
    assert window.score_label.text() == "SCORE  0"

    window.waste_widget.card_buttons[-1].click()
    window.foundation_widgets[Suit.HEARTS]._button.click()
    assert engine.state.score == 10
    assert window.score_label.text() == "SCORE  10"

    clock[0] = 105.0
    window._update_clock_display()
    assert engine.state.elapsed_seconds == 5
    assert window.timer_label.text() == "TIME  00:05"

    window.undo_button.click()
    clock[0] = 108.0
    window._update_clock_display()
    assert engine.state.score == 0
    assert engine.state.elapsed_seconds == 8
    assert window.timer_label.text() == "TIME  00:08"

    window.new_game_button.click()
    assert window.engine.state.score == 0
    assert window.engine.state.elapsed_seconds == 0
    assert window.timer_label.text() == "TIME  00:00"
    window.close()
