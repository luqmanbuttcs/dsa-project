"""Offscreen smoke tests for the interactive PyQt6 game board."""

from __future__ import annotations

import os
from random import Random

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QByteArray, QMimeData, QPointF, Qt
from PyQt6.QtGui import QDropEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from solitaire.domain.card import Card, Rank, Suit
from solitaire.domain.deck import DeckFactory
from solitaire.domain.game_engine import GameEngine
from solitaire.domain.operations import StructureName
from solitaire.domain.game_state import (
    CardLocation,
    GameState,
    GameStatus,
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


def build_tableau_move_state(destination_card_id: str = "C-9") -> GameState:
    cards = {card.card_id: card for card in DeckFactory.create_standard_deck()}
    hidden = cards.pop("C-7")
    moving = cards.pop("H-8")
    destination_top = cards.pop(destination_card_id)
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


def test_new_game_reinitializes_all_piles_and_history(app, monkeypatch):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
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

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window.new_game_button.click()
    assert window.engine.state.score == 0
    assert window.engine.state.elapsed_seconds == 0
    assert window.timer_label.text() == "TIME  00:00"
    window.close()



def _make_drop_event(
    card_id: str, source_pile: str
) -> tuple[QDropEvent, QMimeData]:
    mime = QMimeData()
    mime.setData(
        "application/x-klondike-card",
        QByteArray(f"{card_id}\t{source_pile}".encode("utf-8")),
    )
    event = QDropEvent(
        QPointF(12, 12),
        Qt.DropAction.MoveAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # QDropEvent stores a borrowed QMimeData pointer; retain the wrapper too.
    return event, mime

def test_tableau_drop_event_moves_card_through_game_engine(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    event, mime = _make_drop_event("H-8", "tableau-1")
    window.tableau_widgets["tableau-2"].dropEvent(event)

    assert event.isAccepted()
    assert engine.state.tableau["tableau-1"].peek().card_id == "C-7"
    assert engine.state.tableau["tableau-2"].peek().card_id == "H-8"
    assert engine.state.move_count == 1
    assert window.status_label.text() == "Card dropped successfully."
    engine.state.assert_invariants()
    window.close()


def test_foundation_drop_event_moves_waste_card_through_engine(app):
    engine = GameEngine(build_waste_ace_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    event, mime = _make_drop_event("H-A", "waste")
    window.foundation_widgets[Suit.HEARTS].dropEvent(event)

    assert event.isAccepted()
    assert engine.state.waste.is_empty()
    assert engine.state.foundations[Suit.HEARTS].peek().card_id == "H-A"
    assert engine.state.score == 10
    engine.state.assert_invariants()
    window.close()


def test_drag_preview_highlights_only_currently_legal_destinations(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)

    window._start_drag_preview("H-8", "tableau-1")

    assert window._drag_destinations == {"tableau-2"}
    assert window.tableau_widgets["tableau-2"]._drag_highlighted
    assert not window.tableau_widgets["tableau-1"]._drag_highlighted
    assert not window.foundation_widgets[Suit.HEARTS]._drag_highlighted

    window._clear_drag_preview()
    assert not any(
        widget._drag_highlighted for widget in window.tableau_widgets.values()
    )
    window.close()


def test_dsa_monitor_shows_real_operations_and_current_structure_state(app):
    engine = GameEngine(create_new_game(Random(4501)))
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    assert window.dsa_monitor_dock.isVisible()
    assert window.dsa_monitor.count_table.rowCount() == 5
    assert "24 | F:" in window.dsa_monitor.count_table.item(2, 1).text()
    assert "52 / 52 entries" == window.dsa_monitor.count_table.item(4, 1).text()

    window.stock_button.click()
    assert "Queue" in window.dsa_monitor.latest_operation.text()
    assert "Queue: DEQUEUE ×1" in window.dsa_monitor.latest_operation.text()
    assert window.dsa_monitor.operation_history.count() > 0
    assert any(
        "Queue · DEQUEUE" in window.dsa_monitor.operation_history.item(index).text()
        for index in range(window.dsa_monitor.operation_history.count())
    )

    queue_details = window.dsa_monitor.detail_views[
        StructureName.QUEUE
    ].toPlainText()
    assert "Front / next to draw" in queue_details
    assert "STOCK QUEUE" in queue_details
    window.close()


def test_card_move_and_flip_animations_complete_and_restore_target_widgets(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    visuals, flip_visual = window._capture_move_visuals("H-8", "tableau-1")
    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")
    window._refresh_board()
    window._animate_transitions(visuals, flip_visual)
    QTest.qWait(420)

    moved_button = window._find_card_button("H-8")
    flipped_button = window._find_card_button("C-7")
    assert moved_button is not None and moved_button.isVisible()
    assert flipped_button is not None and flipped_button.isVisible()
    assert not window._active_animations
    assert flipped_button.text() == "7\n♣"
    window.close()


def test_reduced_motion_skips_card_animation(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()
    window.reduce_motion_check.setChecked(True)

    visuals, flip_visual = window._capture_move_visuals("H-8", "tableau-1")
    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")
    window._refresh_board()
    window._animate_transitions(visuals, flip_visual)
    QTest.qWait(250)

    assert not window._active_animations
    assert window._find_card_button("H-8").isVisible()
    assert window._find_card_button("C-7").isVisible()
    window.close()


def test_keyboard_shortcuts_are_installed(app):
    window = MainWindow(GameEngine(create_new_game(Random(4502))))
    shortcuts = {action.shortcut().toString() for action in window._shortcut_actions}
    assert {"Ctrl+Z", "Ctrl+Y", "Ctrl+N", "H", "Space"} <= shortcuts
    window.close()



def test_window_resizes_to_design_minimum_without_hiding_scrollable_board(app):
    window = MainWindow(GameEngine(create_new_game(Random(4503))))
    window.resize(1280, 800)
    window.show()
    app.processEvents()

    assert window.minimumWidth() == 1280
    assert window.minimumHeight() == 800
    assert window.width() >= 1280
    assert window.height() >= 800
    scroll = window.findChild(__import__(
        "PyQt6.QtWidgets", fromlist=["QScrollArea"]
    ).QScrollArea, "tableau-scroll-area")
    assert scroll is not None
    assert scroll.horizontalScrollBarPolicy() is Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert window.dsa_monitor_dock.isVisible()
    window.dsa_monitor_button.click()
    assert not window.dsa_monitor_dock.isVisible()
    window.dsa_monitor_button.click()
    assert window.dsa_monitor_dock.isVisible()
    window.close()


def test_new_game_confirmation_can_be_cancelled_without_losing_current_game(
    app, monkeypatch
):
    engine = GameEngine(create_new_game(Random(4504)))
    window = MainWindow(engine)
    window.stock_button.click()
    assert engine.state.move_count == 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    window.new_game_button.click()

    assert window.engine is engine
    assert engine.state.stock.size() == 23
    assert engine.state.waste.size() == 1
    assert engine.state.move_count == 1
    window.close()



def test_invalid_drag_drop_is_consumed_but_does_not_mutate_the_game(app):
    engine = GameEngine(build_tableau_move_state("D-9"))
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    before_source = tuple(
        card.card_id
        for card in engine.state.tableau["tableau-1"].cards_bottom_to_top()
    )
    before_destination = tuple(
        card.card_id
        for card in engine.state.tableau["tableau-2"].cards_bottom_to_top()
    )
    before_index = dict(engine.state.card_index)
    event, mime = _make_drop_event("H-8", "tableau-1")

    window.tableau_widgets["tableau-2"].dropEvent(event)

    assert event.isAccepted()
    assert tuple(
        card.card_id
        for card in engine.state.tableau["tableau-1"].cards_bottom_to_top()
    ) == before_source
    assert tuple(
        card.card_id
        for card in engine.state.tableau["tableau-2"].cards_bottom_to_top()
    ) == before_destination
    assert engine.state.card_index == before_index
    assert engine.state.move_count == 0
    assert not engine.can_undo
    assert "alternate red and black" in window.status_label.text()
    engine.state.assert_invariants()
    window.close()


def test_undo_redo_animate_visible_card_moves(app):
    engine = GameEngine(build_tableau_move_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    engine.move_tableau_to_tableau("tableau-1", "H-8", "tableau-2")
    window._refresh_board()
    window._undo()
    QTest.qWait(300)

    moved_back = window._find_card_button("H-8")
    assert moved_back is not None and moved_back.isVisible()
    assert engine.state.tableau["tableau-1"].peek().card_id == "H-8"

    window._redo()
    QTest.qWait(300)
    moved_forward = window._find_card_button("H-8")
    assert moved_forward is not None and moved_forward.isVisible()
    assert engine.state.tableau["tableau-2"].peek().card_id == "H-8"
    assert not window._active_animations
    window.close()


def test_restart_confirmation_also_protects_an_undone_game_with_redo_available(
    app, monkeypatch
):
    engine = GameEngine(create_new_game(Random(4505)))
    window = MainWindow(engine)
    window.stock_button.click()
    window.undo_button.click()
    assert not engine.can_undo
    assert engine.can_redo

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    window.new_game_button.click()

    assert window.engine is engine
    assert engine.can_redo
    assert engine.state.stock.size() == 24
    assert engine.state.waste.is_empty()
    window.close()


def test_dsa_history_rows_include_ordered_utc_timestamps(app):
    window = MainWindow(GameEngine(create_new_game(Random(4506))))
    window.stock_button.click()

    rows = [
        window.dsa_monitor.operation_history.item(index).text()
        for index in range(window.dsa_monitor.operation_history.count())
    ]
    queue_row = next(row for row in rows if "Queue · DEQUEUE" in row)
    assert queue_row.startswith("#")
    assert " UTC " in queue_row
    assert "PLAY" in queue_row
    window.close()



def build_four_king_endgame_state() -> GameState:
    cards = {
        card.card_id: card for card in DeckFactory.create_standard_deck()
    }
    stock = Queue()
    waste = Stack()
    tableau = {
        f"tableau-{number}": TableauColumn(f"tableau-{number}")
        for number in range(1, 8)
    }
    foundations = {suit: Stack() for suit in Suit}

    for index, suit in enumerate(Suit, start=1):
        for rank in Rank:
            card = cards.pop(f"{suit.code}-{rank.label}")
            card.turn_face_up()
            if rank is Rank.KING:
                tableau[f"tableau-{index}"].push(card)
            else:
                foundations[suit].push(card)

    card_index = {}
    for suit, pile in foundations.items():
        pile_id = f"foundation-{suit.code.lower()}"
        for position, card in enumerate(pile.to_list()):
            card_index[card.card_id] = CardLocation(
                Zone.FOUNDATION, pile_id, position, card.face_up
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
        status=GameStatus.PLAYING,
    )
    state.assert_invariants()
    return state


def test_nonblocking_victory_panel_appears_and_undo_hides_it(app):
    engine = GameEngine(build_four_king_endgame_state())
    window = MainWindow(engine)
    window.show()
    app.processEvents()
    assert not window.victory_panel.isVisible()

    for index, suit in enumerate(Suit, start=1):
        engine.move_tableau_to_foundation(f"tableau-{index}", suit)

    window._refresh_board()
    assert engine.state.status is GameStatus.WON
    assert window.victory_panel.isVisible()
    assert "All 52 cards are home" in window.victory_label.text()
    assert "Score: 40" in window.victory_label.text()

    assert engine.undo()
    window._refresh_board()
    assert engine.state.status is GameStatus.PLAYING
    assert not window.victory_panel.isVisible()
    window.close()


def test_reference_style_dashboard_exposes_live_structures_stats_and_modes(app):
    engine = GameEngine(create_new_game(Random(4510)))
    window = MainWindow(engine)
    window.show()
    app.processEvents()

    panel = window.dsa_monitor
    assert len(panel.structure_cards) == 5
    assert panel.main_tabs.tabText(0).endswith("DSA Monitor")
    assert panel.main_tabs.tabText(1).endswith("Game Stats")
    assert panel.game_stats_labels["stock"].text() == "24 cards"
    assert panel.game_stats_labels["foundations"].text() == "0 / 52 cards"
    assert not panel.details_panel.isVisible()

    window.stock_button.click()
    assert panel.game_stats_labels["stock"].text() == "23 cards"
    assert panel.game_stats_labels["moves"].text() == "1"
    assert panel.move_timeline.count() == 1
    assert "Drew 1 card(s) from Stock" in panel.move_timeline.item(0).text()
    assert panel.operation_history.count() > 0
    assert any(
        "Queue · DEQUEUE" in panel.operation_history.item(index).text()
        for index in range(panel.operation_history.count())
    )

    panel.dsa_lab_button.click()
    assert panel.dsa_lab_button.isChecked()
    assert panel.details_panel.isVisible()
    assert panel.main_tabs.currentIndex() == 0

    panel.play_mode_button.click()
    assert panel.play_mode_button.isChecked()
    assert not panel.details_panel.isVisible()
    window.close()


def test_premium_card_dimensions_and_settings_controls_remain_available(app):
    window = MainWindow(GameEngine(create_new_game(Random(4511))))
    assert window.stock_button.width() == 116
    assert window.stock_button.height() == 188
    assert window.tableau_widgets["tableau-1"].card_buttons[0].width() == 116
    assert window.tableau_widgets["tableau-1"].card_buttons[0].height() == 160
    assert window.new_game_button is not None
    assert window.dsa_monitor_button is not None
    assert window.settings_button.menu() is not None
    action_texts = {
        window.settings_button.menu().actions()[index].text()
        for index in range(len(window.settings_button.menu().actions()))
    }
    assert "New Game" in action_texts
    assert "Show DSA Monitor" in action_texts
    window.close()
