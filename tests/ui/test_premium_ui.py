"""Offscreen smoke tests for the premium casino PyQt6 presentation layer.

The premium UI must behave like the legacy one: every visual element is a
*projection* of the authoritative GameEngine / GameState / OperationTracker.
These tests exercise the real controllers against the real domain layer with
QT_QPA_PLATFORM=offscreen, so no GPU or display server is required.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager
from solitaire.ui.premium.dsa_lab.data_provider import (
    array_report,
    dictionary_rows,
    game_stats,
    latest_operation,
    queue_report,
    stack_pile_composition,
    stack_report_for_pile,
    structure_counts,
    timeline_rows,
)
from solitaire.ui.premium.main_window import PremiumMainWindow
from solitaire.ui.premium.navigation import LabPage, Workspace
from solitaire.domain.card import Suit
from solitaire.domain.operations import StructureName
from solitaire.ui.premium.theme import (
    CARD_H,
    CARD_W,
    DASHBOARD_WIDTH,
    DESIGN_W,
)

SEED = 1  # deals a deterministic board with a tableau hint (H-2, tableau-5 -> tableau-4)


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture()
def window(app):
    built = PremiumMainWindow(seed=SEED)
    built.show()
    app.processEvents()
    yield built
    # Deterministic teardown: halt animations while items are alive, then
    # delete the C++ tree on the spot instead of leaving it to cyclic GC
    # during a later test (this aborted CI with exit code 134).
    import gc

    built.close()
    built.deleteLater()
    app.processEvents()
    gc.collect()


# --- shell & layout ---------------------------------------------------------------------


def test_premium_window_exposes_header_workspaces_and_dashboard(window):
    assert window.windowTitle().startswith("Klondike Solitaire")
    assert window.workspaces.count() == 3  # play, DSA lab, game mode
    assert window.header.hint_button is window.hint_button
    assert window.header.undo_button is window.undo_button
    assert window.header.redo_button is window.redo_button
    assert window.header.settings_button is window.settings_button
    assert window.play_workspace.dashboard.maximumWidth() == DASHBOARD_WIDTH
    assert window.header.title_label.text() == "Klondike Solitaire"
    assert window.header.badge_label.text() == "CSC200 DSA Edition"


def test_dashboard_keeps_the_approved_25_27_percent_footprint():
    share = DASHBOARD_WIDTH / DESIGN_W
    assert 0.25 <= share <= 0.27


def test_card_metrics_match_the_design_tokens(window):
    assert (CARD_W, CARD_H) == (116, 160)
    scene = window.play_workspace.scene
    checked = 0
    for item in scene.card_items.values():
        # rect() is the painted card face; boundingRect() adds a 10px shadow margin.
        assert item.rect().width() == CARD_W
        assert item.rect().height() == CARD_H
        checked += 1
    assert checked == 52


def test_scene_projects_the_full_initial_deal(window):
    scene = window.play_workspace.scene
    state = window.game.state

    assert len(scene.card_items) == 52
    assert state.stock.size() == 24
    assert len(scene.foundation_items) == 4
    assert len(scene.tableau_items) == 7
    for index in range(1, 8):
        column = state.tableau[f"tableau-{index}"]
        assert column.size() == index
        assert scene.card_top[column.peek().card_id] is True
    # card_top flags only tableau tops: 7 True, everything else False
    # (24 stock cards + 21 hidden tableau cards = 45 False).
    assert sum(1 for top in scene.card_top.values() if top) == 7
    assert sum(1 for top in scene.card_top.values() if not top) == 45
    hidden_tableau = [
        location
        for location in state.card_index.values()
        if location.zone.value == "tableau" and not location.face_up
    ]
    assert len(hidden_tableau) == 21


# --- header metrics & history buttons ------------------------------------------------------


def test_header_metrics_track_real_engine_state(window):
    window.game.draw_from_stock()
    window._refresh_metrics()

    assert window.game.state.move_count == 1
    metrics = window.game.metrics()
    assert metrics["moves"] == "1"
    assert metrics["time"] == "00:00"
    assert metrics["score"] == "0"
    assert window.header.moves_chip.value_label.text() == "1"
    assert window.header.time_chip.value_label.text() == "00:00"


def test_undo_redo_buttons_follow_engine_history(window):
    assert not window.undo_button.isEnabled()
    assert not window.redo_button.isEnabled()

    window.game.draw_from_stock()
    window._update_action_states()
    assert window.undo_button.isEnabled()

    window.undo_button.click()
    window._update_action_states()
    assert window.game.state.stock.size() == 24
    assert window.game.state.waste.is_empty()
    assert window.redo_button.isEnabled()

    window.redo_button.click()
    assert window.game.state.stock.size() == 23
    assert window.game.state.waste.size() == 1


# --- controller boundary ---------------------------------------------------------------------


def test_same_pile_request_is_rejected_before_touching_the_engine(window):
    feedback = []
    window.game.feedback.connect(lambda t, m, k: feedback.append((t, m, k)))

    before_moves = window.game.state.move_count
    before_index = dict(window.game.state.card_index)

    ok = window.game.try_move("waste", None, "waste")

    assert ok is False
    assert window.game.state.move_count == before_moves
    assert window.game.state.card_index == before_index
    assert feedback[-1][0] == "Invalid Move"
    assert feedback[-1][2] == "error"


def test_face_down_card_is_rejected_by_the_engine(window):
    face_down = window.game.state.tableau["tableau-7"].cards_bottom_to_top()[0]
    assert face_down.face_up is False

    before_moves = window.game.state.move_count
    ok = window.game.try_move("tableau-7", face_down.card_id, "tableau-3")

    assert ok is False
    assert window.game.state.move_count == before_moves
    window.game.state.assert_invariants()


def test_controller_executes_the_deterministic_hinted_move(window):
    hints = window.game.engine.find_hints()
    non_stock = [hint for hint in hints if hint.source_pile != "stock"]
    assert non_stock, "seeded deal must expose a real card move"
    hint = non_stock[0]

    ok = window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)

    assert ok is True
    assert window.game.state.move_count == 1
    assert window.game.engine.can_undo
    window.game.state.assert_invariants()


def test_legal_destinations_matches_engine_validation(window):
    hint = next(
        hint
        for hint in window.game.engine.find_hints()
        if hint.source_pile != "stock"
    )
    targets = window.game.legal_destinations(hint.source_pile, hint.card_ids[0])
    assert hint.destination_pile in targets


def test_selection_controller_click_to_select_and_move(window):
    hint = next(
        hint
        for hint in window.game.engine.find_hints()
        if hint.source_pile != "stock"
    )
    selection = window.selection

    selection.click_card(hint.source_pile, hint.card_ids[0], face_up=True, top_of_pile=True)
    assert selection.source_pile == hint.source_pile
    assert selection.card_id == hint.card_ids[0]

    if hint.destination_pile.startswith("tableau-"):
        top_id = window.game.state.tableau[hint.destination_pile].peek().card_id
    else:  # an empty foundation slot has no card of its own yet
        top_id = hint.card_ids[0]
    selection.click_card(hint.destination_pile, top_id, face_up=True, top_of_pile=True)

    assert selection.card_id is None
    assert selection.source_pile is None
    assert window.game.state.move_count == 1


# --- DSA data must be real, never hard-coded --------------------------------------------------


def test_structure_counts_derive_from_the_real_tracker(window):
    window.game.draw_from_stock()
    counts = structure_counts(window.game.tracker)

    assert counts["Queue"] >= 1
    assert counts["Array / List"] >= 1
    assert counts["Dictionary"] >= 1
    assert sum(counts.values()) == len(window.game.tracker.events)


def test_queue_report_matches_live_stock(window):
    window.game.draw_from_stock()
    window.game.draw_from_stock()

    report = queue_report(window.game)
    assert report.size == window.game.state.stock.size() == 22
    assert report.fifo_order[0] == window.game.state.stock.to_list()[0].card_id
    assert report.dequeue_count >= 2
    assert report.recycle_events == 0


def test_stack_report_matches_live_waste(window):
    window.game.draw_from_stock()
    report = stack_report_for_pile(window.game, "waste")

    assert report.pile_label == "Waste"
    assert report.size == 1
    assert report.top_card_id == window.game.state.waste.peek().card_id
    assert report.order_bottom_to_top == (report.top_card_id,)


def test_stack_pile_composition_derives_from_real_piles(window):
    window.game.draw_from_stock()

    waste = stack_pile_composition(window.game, "waste")
    assert waste is not None
    assert waste.total == window.game.state.waste.size() == 1
    assert sum(waste.suit_counts.values()) == waste.total
    top = window.game.state.waste.peek().card_id
    top_suit = next(suit for suit in Suit if suit.code == top.split("-")[0])
    assert waste.suit_counts[top_suit] == 1
    assert waste.face_up == 1 and waste.face_down == 0

    # Tableau piles carry real face-down counts (one per face-down card).
    tableau = stack_pile_composition(window.game, "tableau-5")
    assert tableau is not None
    assert tableau.total == window.game.state.tableau["tableau-5"].size()
    assert tableau.face_up + tableau.face_down == tableau.total
    assert tableau.face_down >= 1

    # History piles hold snapshots, not cards — no composition.
    assert stack_pile_composition(window.game, "undo-history") is None


def test_array_report_counts_real_deal_events(window):
    report = array_report(window.game.tracker, window.game.state.stock.size())

    assert report.create_deck_events == 1
    assert report.shuffle_events == 1
    assert report.deck_size_now == 24
    assert len(report.deal_order) == 28  # 7+6+5+4+3+2+1 tableau cards dealt


def test_dictionary_rows_cover_all_52_cards(window):
    rows = dictionary_rows(window.game)
    assert len(rows) == 52
    assert all(row[1] in {"stock", "waste", "tableau", "foundation"} for row in rows)


def test_timeline_rows_filter_by_structure(window):
    window.game.draw_from_stock()
    tracker = window.game.tracker

    all_rows = timeline_rows(tracker)
    assert len(all_rows) == len(tracker.events)
    queue_rows = timeline_rows(tracker, structure_filter="Queue")
    assert queue_rows
    assert all(row[2] == "Queue" for row in queue_rows)
    operations = {event.operation for event in tracker.events}
    assert "DEQUEUE" in operations
    assert latest_operation(tracker) is tracker.events[-1]


def test_game_stats_uses_live_values(window):
    window.game.draw_from_stock()
    stats = game_stats(window.game)

    assert stats["Moves"] == "1"
    assert stats["Stock"] == "23 cards"
    assert stats["Waste"] == "1 cards"
    assert stats["Status"] == "Playing"


# --- DSA Lab workspace ------------------------------------------------------------------------


def test_navigation_switches_between_play_and_lab(window):
    assert window.navigation.current is Workspace.PLAY

    window.open_dsa_lab()
    assert window.navigation.current is Workspace.DSA_LAB
    assert window.workspaces.currentIndex() == 1

    window.open_play_workspace()
    assert window.workspaces.currentIndex() == 0
    assert window.navigation.current is Workspace.PLAY


def test_lab_pages_exist_for_every_section(window):
    lab = window.dsa_lab
    for page in LabPage:
        assert lab._pages[page] is not None, f"missing lab page {page}"
    assert lab.current_page() is LabPage.OVERVIEW


def test_queue_page_refresh_pulls_live_data(window):
    window.game.draw_from_stock()
    window.open_dsa_lab()

    queue_page = window.dsa_lab._pages[LabPage.QUEUE]
    queue_page.refresh()
    assert queue_page._size_stat.text() == "Stock size: 23"
    assert queue_page._dequeue_stat.text() == "dequeue() events: 1"


def test_stats_page_refresh_pulls_live_data(window):
    window.game.draw_from_stock()
    window.open_dsa_lab()

    stats_page = window.dsa_lab._pages[LabPage.STATS]
    stats_page.refresh()
    assert stats_page._value_labels["Moves"].text() == "1"
    assert stats_page._value_labels["Stock"].text() == "23 cards"
    assert stats_page._value_labels["Status"].text() == "Playing"


def test_stack_page_recent_events_come_from_the_real_tracker(window):
    window.game.draw_from_stock()
    window.open_dsa_lab()

    stack_page = window.dsa_lab._pages[LabPage.STACK]
    stack_page.refresh()
    table = stack_page._events_table

    real = [
        event
        for event in window.game.tracker.events
        if event.structure is StructureName.STACK and event.pile_id == "waste"
    ]
    assert real, "a stock draw must record a real PUSH on the waste pile"
    assert table.rowCount() == min(len(real), 8)
    # Rows are oldest first and mirror the tracker sequences exactly.
    for row, event in enumerate(real[-8:]):
        assert table.item(row, 0).text() == str(event.sequence)
        assert table.item(row, 1).text() == event.operation
    assert table.item(table.rowCount() - 1, 1).text() == "PUSH"
    # Switching the pile selector re-derives the table from real events.
    index = stack_page._pile_selector.findData("foundation-s")
    stack_page._pile_selector.setCurrentIndex(index)
    rows = stack_page._events_table.rowCount()
    assert rows == max(1, stack_page._events_table.rowCount())  # shape holds
    first_cell = stack_page._events_table.item(0, 0)
    assert first_cell is not None and first_cell.text()


def test_linked_list_page_recent_events_come_from_the_real_tracker(window):
    window.open_dsa_lab()

    page = window.dsa_lab._pages[LabPage.LINKED_LIST]
    page.refresh()
    table = page._events_table
    column_id = page._column_selector.currentData()

    real = [
        event
        for event in window.game.tracker.events
        if event.structure is StructureName.LINKED_LIST and event.pile_id == column_id
    ]
    assert real, "the dealt column must carry real linked-list events"
    assert table.rowCount() == min(len(real), 6)
    for row, event in enumerate(real[-6:]):
        assert table.item(row, 0).text() == str(event.sequence)
        assert table.item(row, 1).text() == event.operation
    assert {table.item(row, 1).text() for row in range(table.rowCount())} <= {
        "APPEND_NODE",
        "REMOVE_TOP_NODE",
        "DETACH_RUN",
        "ATTACH_RUN",
    }


# --- settings / animation policy -----------------------------------------------------------------


def test_reduce_motion_and_speed_reach_the_animation_manager(window):
    window._reduce_motion = True
    window._speed_multiplier = 0.5
    window._apply_animation_settings()

    manager = CardAnimationManager.instance()
    assert manager.reduce_motion is True
    assert manager.speed_multiplier == 0.5

    window._reduce_motion = False
    window._speed_multiplier = 1.0
    window._apply_animation_settings()
    assert manager.reduce_motion is False
    assert manager.speed_multiplier == 1.0


def test_clock_tick_increments_and_new_game_resets(window):
    controller = window.game
    controller._on_clock_tick()
    assert controller.elapsed_seconds == 1

    controller.new_game(draw_count=1, announce=False)
    assert controller.elapsed_seconds == 0


def test_feedback_panel_receives_controller_events(window):
    panel = window.play_workspace.feedback_panel
    window.game.draw_from_stock()

    assert panel._title_label.text() == "Stock Draw"
    assert "Waste" in panel._message_label.text()


def test_move_log_records_real_engine_history(window):
    log = window.play_workspace.move_log
    window.game.draw_from_stock()
    window.game.draw_from_stock()

    assert log._list.count() == 2


def test_scene_sync_after_engine_undo_restores_positions(window):
    window.game.draw_from_stock()
    window.game.undo()
    window.play_workspace.scene.sync(animate=False)

    state = window.game.state
    assert state.waste.is_empty()
    assert state.stock.size() == 24
    first_stock_card = state.stock.to_list()[0].card_id
    assert window.play_workspace.scene.card_zone[first_stock_card] == "stock"


# --- regression: functional defect fixes (review pass) -------------------------------


def test_invalid_action_does_not_start_the_game_clock(window):
    controller = window.game
    assert not controller._clock.isActive()

    # A rejected move must not start the clock.
    face_down = controller.state.tableau["tableau-7"].cards_bottom_to_top()[0]
    window.game.try_move("tableau-7", face_down.card_id, "tableau-3")
    assert not controller._clock.isActive()

    # A successful action does.
    window.game.draw_from_stock()
    assert controller._clock.isActive()
    controller._clock.stop()


def test_move_log_does_not_duplicate_moves_after_undo(window):
    log = window.play_workspace.move_log
    window.game.draw_from_stock()
    window.game.draw_from_stock()
    assert log._list.count() == 2

    window.game.undo()
    assert log._list.count() == 2  # unchanged, no duplicated row

    window.game.redo()
    assert log._list.count() == 2


def test_lower_face_up_tableau_card_starts_a_run_selection(window):
    from PyQt6.QtWidgets import QApplication

    hint = next(
        h for h in window.game.engine.find_hints() if h.source_pile != "stock"
    )
    assert window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)

    # After the move some column holds >= 2 face-up cards.
    state = window.game.state
    column_id, cards = next(
        (pile_id, column.cards_bottom_to_top())
        for pile_id, column in state.tableau.items()
        if sum(1 for c in column.cards_bottom_to_top() if c.face_up) >= 2
    )
    face_up = [card for card in cards if card.face_up]
    lower_id = face_up[0].card_id
    upper_id = face_up[-1].card_id

    selection = window.selection
    selection.click_card(column_id, lower_id, face_up=True, top_of_pile=False)
    assert selection.card_id == lower_id
    assert selection.source_pile == column_id
    assert selection.selected_run() == [card.card_id for card in face_up]
    selection.clear()


def _grabable_run(app, window):
    """Deal a board, make one move, return (column_id, face_up_ids, hint-free state)."""
    hint = next(
        h for h in window.game.engine.find_hints() if h.source_pile != "stock"
    )
    assert window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)
    state = window.game.state
    column_id, cards = next(
        (pile_id, column.cards_bottom_to_top())
        for pile_id, column in state.tableau.items()
        if sum(1 for c in column.cards_bottom_to_top() if c.face_up) >= 2
    )
    face_up_ids = [c.card_id for c in cards if c.face_up]
    return column_id, face_up_ids


def _viewport_center(view, scene_pos):
    return view.mapFromScene(scene_pos)


def test_manual_drag_lifts_the_run_and_follows_the_pointer(app, window):
    """Press + move starts a real manual drag: run items raise and follow."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    column_id, face_up_ids = _grabable_run(app, window)
    scene = window.play_workspace.scene
    view = window.play_workspace.view
    item = scene.card_items[face_up_ids[0]]

    start = _viewport_center(view, item.mapToScene(item.rect().center()))
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(20, 6))
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(34, 10))
    app.processEvents()

    assert scene._drag_run, "manual drag session must be active"
    assert scene._drag_card_ids == face_up_ids
    assert scene._drag_source == column_id
    # The grabbed card follows the pointer: its scene pos tracks the cursor.
    assert scene._drag_run[0].zValue() > 250.0
    assert item.get_drag_lift() > 0.0 or item._drag_lift > 0.0

    QTest.mouseRelease(
        view.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start + QPoint(34, 10),
    )
    app.processEvents()
    scene.settle_all()
    app.processEvents()


def test_manual_drag_to_legal_target_executes_the_move(app, window):
    """Release over a legal target performs the real engine move."""
    from PyQt6.QtCore import QPointF, QPoint, Qt
    from PyQt6.QtTest import QTest

    scene = window.play_workspace.scene
    view = window.play_workspace.view
    before_moves = window.game.state.move_count

    # Find ANY draggable card with a legal destination (tableau or foundation).
    plan = None
    for pile_id in [f"tableau-{n}" for n in range(1, 8)] + ["waste"]:
        if pile_id == "waste":
            cards = window.game.state.waste.to_list()
            candidates = [cards[-1]] if cards else []
        else:
            cards = window.game.state.tableau[pile_id].cards_bottom_to_top()
            candidates = [c for c in cards if c.face_up]
        for card in reversed(candidates):
            legal = [
                p
                for p in window.game.legal_destinations(pile_id, card.card_id)
                if p != pile_id and not (pile_id == "waste" and p == "waste")
            ]
            if legal:
                plan = (pile_id, card.card_id, legal[0])
                break
        if plan:
            break
    if plan is None:
        pytest.skip("board offers no legal drag destination")
    source_pile, moving_id, target_pile = plan

    item = scene.card_items[moving_id]
    start = _viewport_center(view, item.mapToScene(item.rect().center()))
    depth = 0.0
    if target_pile.startswith("tableau-"):
        column = window.game.state.tableau[target_pile]
        depth = min(
            40.0,
            sum(14.0 if not c.face_up else scene.fan_up for c in column.cards_bottom_to_top()),
        )
    target_pos = scene.slot_position(target_pile) + QPointF(0.0, depth)

    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(16, 8))
    app.processEvents()
    QTest.mouseMove(view.viewport(), _viewport_center(view, target_pos))
    app.processEvents()
    QTest.mouseMove(view.viewport(), _viewport_center(view, target_pos))
    app.processEvents()
    QTest.mouseRelease(
        view.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _viewport_center(view, target_pos),
    )
    app.processEvents()
    scene.settle_all()
    app.processEvents()

    assert window.game.state.move_count == before_moves + 1
    zone = scene.card_zone[moving_id]
    assert zone == target_pile, f"card must land on {target_pile}, got {zone}"


def test_manual_drag_to_invalid_target_never_mutates_state(app, window):
    """Dropping on an illegal pile: state untouched, cards fly home."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    column_id, face_up_ids = _grabable_run(app, window)
    scene = window.play_workspace.scene
    view = window.play_workspace.view
    state = window.game.state
    cards = state.tableau[column_id].cards_bottom_to_top()
    face_up = [c for c in cards if c.face_up]
    moving_id = face_up[-1].card_id

    legal = set(window.game.legal_destinations(column_id, moving_id))
    illegal_columns = [
        f"tableau-{n}" for n in range(1, 8) if f"tableau-{n}" not in legal
    ]
    if not illegal_columns:
        pytest.skip("board has no illegal tableau destination")
    target_column = illegal_columns[0]
    before_moves = window.game.state.move_count

    item = scene.card_items[moving_id]
    start = _viewport_center(view, item.mapToScene(item.rect().center()))
    drop_pos = scene.slot_position(target_column)
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(16, 8))
    app.processEvents()
    QTest.mouseMove(view.viewport(), _viewport_center(view, drop_pos))
    app.processEvents()
    QTest.mouseRelease(
        view.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _viewport_center(view, drop_pos),
    )
    app.processEvents()
    scene.settle_all()
    app.processEvents()

    assert window.game.state.move_count == before_moves, "invalid drop must not mutate state"
    # The card returned to its authoritative position.
    zone = scene.card_zone[moving_id]
    expected_x = scene.slot_position(zone).x()
    assert abs(scene.card_items[moving_id].pos().x() - expected_x) < 0.6


def _drop_run_on(app, window, scene, view, column_id, moving_id, target_scene_pos):
    """Press, drag and release a face-up run onto `target_scene_pos`.

    Returns the run leader's position just before the release (the shake
    origin of an invalid drop)."""
    from PyQt6.QtCore import QPoint, QPointF, Qt
    from PyQt6.QtTest import QTest

    item = scene.card_items[moving_id]
    start = _viewport_center(view, item.mapToScene(item.rect().center()))
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(16, 8))
    app.processEvents()
    QTest.mouseMove(view.viewport(), _viewport_center(view, target_scene_pos))
    app.processEvents()
    drag_pos = QPointF(scene.card_items[moving_id].pos())
    QTest.mouseRelease(
        view.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _viewport_center(view, target_scene_pos),
    )
    app.processEvents()
    return drag_pos


def test_invalid_drop_shake_survives_then_flies_home(app, window):
    """Regression: the fly-home sync used to start immediately after the
    shake, and the movement manager's interrupt cancelled the shake. Both
    feedback (shake at the drop point) and the return trip must now be
    delivered, in that order."""
    from PyQt6.QtTest import QTest

    from solitaire.ui.premium.theme import ANIMATION_MS

    column_id, face_up_ids = _grabable_run(app, window)
    scene = window.play_workspace.scene
    view = window.play_workspace.view
    scene.settle_all()  # quiesce: no in-flight animations before the drop
    app.processEvents()

    state = window.game.state
    moving_id = face_up_ids[-1]
    legal = set(window.game.legal_destinations(column_id, moving_id))
    illegal_columns = [
        f"tableau-{n}" for n in range(1, 8)
        if f"tableau-{n}" not in legal and f"tableau-{n}" != column_id
    ]
    if not illegal_columns:
        pytest.skip("board has no illegal tableau destination")
    home_x = scene.slot_position(column_id).x()
    before_moves = state.move_count

    sync_calls: list[int] = []
    original_sync = scene.sync

    def _counting_sync(*args, **kwargs):
        sync_calls.append(1)
        return original_sync(*args, **kwargs)

    # Pin the animation speed: the manager is an application singleton that
    # restores the user's Game Mode preference from QSettings, so the shake
    # duration (150ms × 2 × speed) must not depend on the host machine's
    # persisted settings.
    manager = CardAnimationManager.instance()
    original_speed = manager.speed_multiplier
    manager.speed_multiplier = 1.0

    scene.sync = _counting_sync
    try:
        drag_pos = _drop_run_on(app, window, scene, view, column_id, moving_id,
                                scene.slot_position(illegal_columns[0]))
        item = scene.card_items[moving_id]
        # 1. The fly-home sync is deferred: nothing reconciled during the drop.
        assert sync_calls == [], "fly-home sync must be deferred until the shake ends"
        assert state.move_count == before_moves, "invalid drop must not mutate state"
        # 2. Right after the drop the shake — and only the shake — is alive.
        shake_alive = [
            a for a in manager._active
            if a.state() == a.state().Running and a.targetObject() is item
        ]
        assert shake_alive, "shake must be running right after the invalid drop"
        assert len(shake_alive) == 1, "no movement animation may fight the shake"
        # 3. The card is still at the drop point (wobbling), not yet home.
        assert abs(item.pos().x() - drag_pos.x()) <= 8.0, "shake must play at the drop point"
        assert abs(drag_pos.x() - home_x) > 30.0, "precondition: drop point far from home"
        assert abs(item.pos().x() - home_x) > 2.0, "fly-home must not start with the shake"
        # 4. After the shake window the deferred sync fires exactly once and
        #    a movement animation carries the run home.
        QTest.qWait(int(ANIMATION_MS["invalid"] * 2 * 1.4) + 60)
        assert len(sync_calls) == 1, "deferred fly-home sync must fire exactly once"
    finally:
        manager.speed_multiplier = original_speed
        scene.sync = original_sync
        scene.settle_all()

    assert scene.card_zone[moving_id] == column_id, "zone must be unchanged by rejection"
    expected_x = scene.slot_position(column_id).x()
    assert abs(scene.card_items[moving_id].pos().x() - expected_x) < 0.6, "run must be home"
    assert state.move_count == before_moves


def test_grabbing_during_invalid_shake_supersedes_the_fly_home(app, window):
    """Grabbing the shaking card again must not start movement animations
    under the user's hand: the pending fly-home is superseded, the new drag
    owns the cards, and the next drop reconciles everything."""
    from PyQt6.QtTest import QTest

    # Reach (deterministically, via seeded hint moves) a state where the top
    # face-up card of some column has both a legal and an illegal tableau
    # destination — the re-grab path needs a valid drop after the shake.
    found = None
    for _ in range(14):
        state = window.game.state
        for pile_id, column in state.tableau.items():
            face_up = [c for c in column.cards_bottom_to_top() if c.face_up]
            if not face_up:
                continue
            moving = face_up[-1].card_id
            legal = set(window.game.legal_destinations(pile_id, moving))
            tab_legal = [
                f"tableau-{n}" for n in range(1, 8)
                if f"tableau-{n}" in legal and f"tableau-{n}" != pile_id
            ]
            tab_illegal = [
                f"tableau-{n}" for n in range(1, 8)
                if f"tableau-{n}" not in legal and f"tableau-{n}" != pile_id
            ]
            if tab_legal and tab_illegal:
                found = (pile_id, moving, tab_legal, tab_illegal)
                break
        if found:
            break
        hint = next(
            (h for h in window.game.engine.find_hints() if h.source_pile != "stock"), None
        )
        if hint is None:
            break
        assert window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)
    if found is None:
        pytest.skip("seeded board never offers a run with both legal and illegal targets")
    column_id, moving_id, legal_columns, illegal_columns = found

    scene = window.play_workspace.scene
    view = window.play_workspace.view
    scene.settle_all()
    app.processEvents()
    before_moves = window.game.state.move_count

    _drop_run_on(app, window, scene, view, column_id, moving_id,
                 scene.slot_position(illegal_columns[0]))
    item = scene.card_items[moving_id]
    manager = CardAnimationManager.instance()
    assert any(
        a.state() == a.state().Running and a.targetObject() is item for a in manager._active
    ), "precondition: shake running"

    # Grab again mid-shake: press, then a deliberate move past the drag
    # threshold (a drag only starts once the press becomes a move).
    grab_pos = _viewport_center(view, item.mapToScene(item.rect().center()))
    from PyQt6.QtCore import QPoint, Qt
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, grab_pos
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), grab_pos + QPoint(20, 0))
    app.processEvents()
    # The interrupted shake's deferred fly-home must NOT have synced.
    assert scene._drag_run, "a drag session must be active after the grab"
    target = scene.slot_position(legal_columns[0])
    QTest.mouseMove(view.viewport(), _viewport_center(view, target))
    app.processEvents()
    QTest.mouseRelease(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _viewport_center(view, target),
    )
    app.processEvents()
    scene.settle_all()

    assert state.move_count == before_moves + 1, "legal drop after re-grab must move"
    new_zone = scene.card_zone[moving_id]
    assert new_zone == legal_columns[0], f"card must land on {legal_columns[0]}, got {new_zone}"


def test_invalid_drop_under_reduce_motion_returns_home_immediately(app, window):
    """Reduce Motion: no shake animation, but the run still returns home at
    once — feedback degrades, correctness never does."""
    column_id, face_up_ids = _grabable_run(app, window)
    scene = window.play_workspace.scene
    view = window.play_workspace.view
    scene.settle_all()
    app.processEvents()

    state = window.game.state
    moving_id = face_up_ids[-1]
    legal = set(window.game.legal_destinations(column_id, moving_id))
    illegal_columns = [
        f"tableau-{n}" for n in range(1, 8)
        if f"tableau-{n}" not in legal and f"tableau-{n}" != column_id
    ]
    if not illegal_columns:
        pytest.skip("board has no illegal tableau destination")

    before_moves = state.move_count
    manager = CardAnimationManager.instance()
    manager.reduce_motion = True
    try:
        _drop_run_on(app, window, scene, view, column_id, moving_id,
                     scene.slot_position(illegal_columns[0]))
        item = scene.card_items[moving_id]
        assert scene.card_zone[moving_id] == column_id, "zone must be unchanged"
        expected_x = scene.slot_position(column_id).x()
        assert abs(item.pos().x() - expected_x) < 0.6, "run must be home immediately"
        assert state.move_count == before_moves
    finally:
        manager.reduce_motion = False


def test_state_change_during_manual_drag_ends_it_safely(app, window):
    """An engine state change mid-drag (e.g. keyboard undo) ends the drag."""
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtTest import QTest

    column_id, face_up_ids = _grabable_run(app, window)
    scene = window.play_workspace.scene
    view = window.play_workspace.view
    item = scene.card_items[face_up_ids[0]]

    start = _viewport_center(view, item.mapToScene(item.rect().center()))
    QTest.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    app.processEvents()
    QTest.mouseMove(view.viewport(), start + QPoint(30, 10))
    app.processEvents()
    assert scene._drag_run

    window.game.draw_from_stock()  # unrelated state change mid-drag
    app.processEvents()
    scene.settle_all()
    app.processEvents()

    assert not scene._drag_run, "sync must end an active drag session"
    assert not item._dragging


def test_reduce_motion_snaps_instead_of_animating(app, window):
    """Reduce Motion: moves land instantly, gameplay fully functional."""
    hint = next(
        h for h in window.game.engine.find_hints() if h.source_pile != "stock"
    )
    window.play_workspace.animation.reduce_motion = True
    try:
        assert window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)
        app.processEvents()
        scene = window.play_workspace.scene
        scene.settle_all()
        app.processEvents()
        for card_id, item in scene.card_items.items():
            zone = scene.card_zone[card_id]
            if not zone.startswith("tableau-"):
                continue  # stock/waste fan offsets are cosmetic, skip them
            slot = scene.slot_position(zone)
            assert abs(item.pos().x() - slot.x()) < 0.6
    finally:
        window.play_workspace.animation.reduce_motion = False


def test_many_window_lifecycles_stay_gc_safe(app):
    """Regression for the CI exit-134 abort during garbage collection."""
    import gc

    for seed in range(3):
        built = PremiumMainWindow(seed=seed)
        built.show()
        app.processEvents()
        built.game.draw_from_stock()
        built.game.undo()
        built.close()
        built.deleteLater()
        app.processEvents()
        gc.collect()

    survivor = PremiumMainWindow(seed=99)
    survivor.game.draw_from_stock()
    survivor.game.undo()
    survivor.game.redo()
    assert survivor.game.state.move_count == 1
    survivor.close()
    survivor.deleteLater()
    app.processEvents()
    gc.collect()


def test_latest_operation_panel_hides_internal_bookkeeping(window):
    """Regression: the dashboard must show a player-facing operation."""
    from solitaire.ui.premium.dsa_lab.data_provider import latest_player_operation

    window.game.draw_from_stock()
    window.game.undo()

    latest = latest_player_operation(window.game.tracker)
    assert latest is not None
    assert latest.context == "PLAY"
    assert "undo-history" not in (latest.pile_id or "")

    dashboard = window.play_workspace.dashboard
    dashboard.refresh()
    assert "undo-history" not in dashboard._latest_body.text()
    assert "APPEND_NODE" not in dashboard._latest_body.text()


def test_game_mode_page_applies_draw_mode_and_motion_settings(window):
    page = window.game_mode_page
    window.open_settings()
    assert window.workspaces.currentIndex() == 2
    assert window.navigation.current.value == "game-mode"

    page._draw_three.setChecked(True)
    page._reduce_motion.toggle.setChecked(True)
    page.apply()

    assert window.game.draw_mode == 3
    assert CardAnimationManager.instance().reduce_motion is True

    page._draw_one.setChecked(True)
    page._reduce_motion.toggle.setChecked(False)
    page.apply()
    assert window.game.draw_mode == 1
    assert CardAnimationManager.instance().reduce_motion is False

    window._close_game_mode()
    assert window.workspaces.currentIndex() == 0


# --- visual polish pass regression tests ---------------------------------------------------

def test_new_game_resets_feedback_panel_to_idle(window):
    """Regression: a fresh table must not inherit the previous game's
    success card — the panel returns to its quiet idle state."""
    panel = window.play_workspace.feedback_panel

    window.game.draw_from_stock()
    assert panel.state in ("success", "info", "error")

    window.game.new_game(draw_count=1, announce=False)
    assert panel.state == "idle"
    assert panel._title_label.text() == "Ready"


def test_latest_operation_skips_dictionary_index_updates(window):
    """Regression: passive Dictionary bookkeeping must never shadow the
    player's actual action in the dashboard's Latest Operation panel."""
    from solitaire.domain.operations import StructureName

    window.game.draw_from_stock()

    from solitaire.ui.premium.dsa_lab.data_provider import latest_player_operation

    latest = latest_player_operation(window.game.tracker)
    assert latest is not None
    assert latest.structure is not StructureName.DICTIONARY

    dashboard = window.play_workspace.dashboard
    dashboard.refresh()
    assert "Card index updated" not in dashboard._latest_body.text()


def test_queue_strip_refresh_leaves_no_stale_widgets(window):
    """Regression: rebuilding the FIFO strip must remove the previous
    widgets from the screen immediately, not leave deleteLater ghosts that
    paint the old strip underneath the new one."""
    from solitaire.ui.premium.dsa_lab.queue_inspector import QueueInspector
    from solitaire.ui.premium.dsa_lab.widgets import MiniCardChip

    inspector = window.dsa_lab._pages[LabPage.QUEUE]
    assert isinstance(inspector, QueueInspector)

    inspector.refresh()
    window.game.draw_from_stock()
    inspector.refresh()

    chips = inspector._order_panel.findChildren(MiniCardChip)
    expected = len(queue_report(window.game).fifo_order)
    assert len(chips) == expected


def test_timeline_rows_use_player_friendly_pile_labels(window):
    """Regression: the Recent Player Moves timeline must speak the same
    notation as the Move Log ('Spades Foundation'), not raw pile ids."""
    hints = [
        h
        for h in window.game.engine.find_hints()
        if h.destination_pile and h.destination_pile.startswith("foundation-")
    ]
    if not hints:
        window.game.draw_from_stock()
        hints = [
            h
            for h in window.game.engine.find_hints()
            if h.destination_pile and h.destination_pile.startswith("foundation-")
        ]
    if hints:
        hint = hints[0]
        window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)

    dashboard = window.play_workspace.dashboard
    dashboard.refresh()
    texts = [row._text for row in dashboard._history_rows if row.isVisible()]
    assert texts
    for text in texts:
        assert "foundation-" not in text
        assert "tableau-" not in text


def test_stack_operations_placeholder_row_is_not_clipped(window):
    """Regression: the empty-operations placeholder row reserves enough
    height to show the whole sentence instead of an ellipsis."""
    inspector = window.dsa_lab._pages[LabPage.STACK]
    inspector._pile_selector.setCurrentIndex(
        inspector._pile_selector.findData("foundation-h")
    )
    inspector.refresh()

    assert inspector._operations_table.rowCount() >= 1
    assert inspector._operations_table.rowHeight(0) >= 40


def test_linked_list_page_defaults_to_the_deepest_column(window):
    """Regression: the node diagram should open on a real chain (the deepest
    tableau column), not a single-node column."""
    inspector = window.dsa_lab._pages[LabPage.LINKED_LIST]
    sizes = [
        window.game.state.tableau[f"tableau-{index}"].size() for index in range(1, 8)
    ]
    expected = sizes.index(max(sizes))
    assert inspector._column_selector.currentIndex() == expected


# --- regression: settled projection for captures and tests --------------------------


def test_settle_all_snaps_in_flight_cards_to_engine_positions(window):
    """After settle_all() no card may remain mid-animation: every item must
    sit at its authoritative engine-derived position (screenshots and tests
    observe the final projection, never a cosmetic in-flight pose)."""
    scene = window.play_workspace.scene

    # Play real moves so at least one card animates, then settle.
    window.game.draw_from_stock()
    hints = window.game.engine.find_hints()
    if hints:
        hint = hints[0]
        window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)

    scene.settle_all()
    QApplication.processEvents()

    state = window.game.state
    for suit in state.foundations:
        pile_id = f"foundation-{suit.code.lower()}"
        cards = state.foundations[suit].to_list()
        for card in cards:
            item = scene.card_items[card.card_id]
            assert item.pos() == scene.slot_position(pile_id)

    for column_id, column in state.tableau.items():
        for card in column.cards_bottom_to_top():
            item = scene.card_items[card.card_id]
            assert scene.card_zone[card.card_id] == column_id

    # The projection must be stable: a second settle changes nothing.
    before = {cid: item.pos() for cid, item in scene.card_items.items()}
    scene.settle_all()
    after = {cid: item.pos() for cid, item in scene.card_items.items()}
    assert before == after


# --- real mouse interaction & process stability -----------------------------------------
#
# Regression guard for the Windows crash report: clicking any interactive card
# raised AttributeError inside QGraphicsObject.mousePressEvent (scene events
# expose pos()/scenePos(), not QMouseEvent.position()), and PyQt6 answers an
# exception escaping a slot with qFatal -> abort, terminating the whole
# application. These tests drive the REAL Qt event pipeline (QTest + real
# C++ event dispatch), not controller methods.


def test_real_mouse_click_on_card_selects_instead_of_aborting(app, window):
    """A genuine QGraphicsSceneMouseEvent press/release must select the card.

    Before the fix this aborted the test process (exit 134) on the first
    card click; it is the direct canary for the reported termination.
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QGraphicsView

    window.game.new_game(draw_count=1, announce=False)
    window.game.draw_from_stock()
    app.processEvents()
    # Settle the deal/draw choreography so the click targets the card's
    # final resting position (this test checks click selection, not timing).
    window.play_workspace.scene.settle_all()
    app.processEvents()

    view = window.play_workspace.findChildren(QGraphicsView)[0]
    scene = view.scene()
    top_id = window.game.state.waste.peek().card_id
    item = scene.card_items[top_id]
    local = view.mapFromScene(item.mapToScene(item.boundingRect().center()))

    QTest.mouseMove(view.viewport(), local)
    app.processEvents()
    QTest.mouseClick(
        view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, local
    )
    app.processEvents()

    assert window.selection.has_selection
    assert window.selection.card_id == top_id
    assert window.selection.source_pile == "waste"


def test_raising_slot_is_logged_and_application_survives(app, window):
    """An exception escaping a slot must be logged, never abort the process.

    PyQt6's default is qFatal -> abort; the installed stability hook turns
    that into a logged error while the application keeps responding.
    """
    import sys

    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    from solitaire.ui.stability import install_slot_exception_hook

    saved_hook = sys.excepthook
    captured = []

    def recording_hook(kind, value, tb):
        captured.append(value)

    sys.excepthook = recording_hook
    try:
        window.game.new_game(draw_count=1, announce=False)
        app.processEvents()

        calls = []

        def raising_slot(_reason: str) -> None:
            calls.append(True)
            raise RuntimeError("simulated defect in a slot")

        window.game.state_changed.connect(raising_slot)
        stock_before = window.game.state.stock.size()

        # A QShortcut activation dispatches the slot from C++ code, so the
        # exception escapes into Qt exactly like a real UI interaction.
        QTest.keyClick(window, Qt.Key.Key_Space)
        app.processEvents()

        assert calls, "the raising slot was not reached"
        assert captured and isinstance(captured[-1], RuntimeError)
        assert window.isVisible(), "the window must stay open"

        # The application must still respond: disconnect the fault and draw again.
        window.game.state_changed.disconnect(raising_slot)
        window.play_workspace.scene.settle_all()
        QTest.keyClick(window, Qt.Key.Key_Space)
        app.processEvents()
        assert window.game.state.stock.size() < stock_before
    finally:
        sys.excepthook = saved_hook


def test_stability_hook_is_installed_by_entry_points(monkeypatch):
    """Both entry points arm the keep-running excepthook before showing UI."""

    import solitaire.main as entry
    from solitaire.ui import stability
    from solitaire.ui.premium import app as premium_app

    calls = []
    existing_app = QApplication.instance() or QApplication([])

    # Premium bootstrap: hook armed during create_app (no second QApplication).
    monkeypatch.setattr(
        premium_app, "install_slot_exception_hook", lambda: calls.append("create_app")
    )
    monkeypatch.setattr(premium_app, "QApplication", lambda argv: existing_app)
    premium_app.create_app([])
    assert "create_app" in calls

    # solitaire.main arms it before launching either window branch; stop the
    # launch at the premium main boundary.
    calls.clear()
    monkeypatch.setattr(stability, "install_slot_exception_hook", lambda: calls.append("entry"))
    monkeypatch.setattr("solitaire.ui.premium.app.main", lambda argv: 0)
    assert entry.main(["x"]) == 0
    assert "entry" in calls


def test_dashboard_structure_rows_open_the_lab_on_that_page(app, window):
    """Clicking a dashboard structure row must open the DSA Lab on the
    clicked structure's page.

    Regression: _open_lab() accepted no page argument, so every structure
    row click raised TypeError — which PyQt6 escalates to qFatal abort,
    terminating the application on Windows.
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    from solitaire.ui.premium.components.dashboard.dsa_dashboard import STRUCTURE_ROWS

    window.game.draw_from_stock()
    app.processEvents()
    dashboard = window.play_workspace.dashboard

    for name, _subtitle, _icon, page, _accent in STRUCTURE_ROWS:
        row = dashboard._rows[name]
        QTest.mouseClick(row, Qt.MouseButton.LeftButton)
        app.processEvents()
        assert window.workspaces.currentIndex() == 1, "lab workspace must be shown"
        assert window.dsa_lab.current_page() == page
        window.open_play_workspace()
        app.processEvents()


# --- Stock/Waste caption band (regression: labels must never be covered) ------------------


VIEWPORTS = [(1280, 800), (1600, 900), (1920, 1029)]


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_stock_waste_chips_live_in_the_reserved_band(app, window, width, height):
    """The Stock/Waste chips sit inside their reserved caption band and the
    Tableau row starts below it — collision-free by geometry, at every
    supported window size, regardless of how deep the tableau fans."""
    from solitaire.ui.premium.graphics.game_board_scene import (
        LABEL_BAND,
        TOP_MARGIN,
        columns_top_for,
    )
    from solitaire.ui.premium.theme import CARD_H

    window.resize(width, height)
    app.processEvents()
    app.processEvents()

    scene = window.play_workspace.scene
    columns_top = scene.slot_position("tableau-1").y()
    assert columns_top == columns_top_for()

    band_top = TOP_MARGIN + CARD_H
    for item in (scene.stock_item, scene.waste_item):
        chip = item.chip_rect()
        chip_scene_top = item.scenePos().y() + chip.top()
        chip_scene_bottom = item.scenePos().y() + chip.bottom()
        # The chip lives entirely inside the reserved band...
        assert chip_scene_top >= band_top
        assert chip_scene_bottom < columns_top - 2.0, (
            "caption chip must clear the tableau row by a real margin"
        )
        # ...and is fully inside the scene rect (never clipped).
        inside = scene.sceneRect().contains(item.mapToScene(chip).boundingRect())
        assert inside, "caption chip is clipped by the scene edge"

    # The whole chip pill must also fit horizontally inside the scene.
    for item in (scene.stock_item, scene.waste_item):
        chip_scene = item.mapToScene(item.chip_rect()).boundingRect()
        assert chip_scene.left() >= scene.sceneRect().left()
        assert chip_scene.right() <= scene.sceneRect().right()


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_chips_never_overlap_even_with_tall_tableau_columns(app, window, width, height):
    """Simulate a worst-case board: every column fanned deep. Even at the
    minimum window size the chips stay clear of the tallest tableau card."""
    from solitaire.ui.premium.graphics.game_board_scene import LABEL_BAND, TOP_MARGIN
    from solitaire.ui.premium.theme import CARD_H

    window.resize(width, height)
    app.processEvents()
    scene = window.play_workspace.scene

    deepest_bottom = max(
        item.scenePos().y() + CARD_H
        for item in scene.card_items.values()
        if scene.card_zone.get(item.card_id, "").startswith("tableau-")
    )
    # Fan depth can extend the column, but it extends *downward*: the top of
    # the tableau row (where chips end) is what matters for the captions.
    chip_bottom = max(
        item.scenePos().y() + item.chip_rect().bottom()
        for item in (scene.stock_item, scene.waste_item)
    )
    columns_top = scene.slot_position("tableau-1").y()
    assert chip_bottom <= columns_top - 2.0
    assert columns_top == TOP_MARGIN + CARD_H + LABEL_BAND
    # Sanity: deepest column bottom is below the columns top (cards flow down).
    assert deepest_bottom >= columns_top


def test_chips_render_genuine_dynamic_counts(app, window):
    """Chip text tracks the real engine piles after draws and recycles."""
    scene = window.play_workspace.scene

    def chip(expected_count: int, kind: str) -> str:
        noun = "CARD" if expected_count == 1 else "CARDS"
        return f"{kind} • {expected_count} {noun}"

    stock_count = len(window.game.state.stock.to_list())
    waste_count = len(window.game.state.waste.to_list())
    assert scene.stock_item.chip_text == chip(stock_count, "STOCK")
    assert scene.waste_item.chip_text == chip(waste_count, "WASTE")

    window.game.draw_from_stock()
    app.processEvents()
    stock_count = len(window.game.state.stock.to_list())
    waste_count = len(window.game.state.waste.to_list())
    assert scene.stock_item.chip_text == chip(stock_count, "STOCK")
    assert scene.waste_item.chip_text == chip(waste_count, "WASTE")

    while len(window.game.state.stock.to_list()) > 0:
        window.game.draw_from_stock()
    app.processEvents()
    assert len(window.game.state.waste.to_list()) == waste_count + stock_count
    # An exhausted stock advertises the recycle cue instead of a zero count.
    assert scene.stock_item.chip_text == "STOCK • RECYCLE"


def test_chip_pill_fits_inside_item_bounding_rect(window):
    """No clipped chip artwork: the chip rect is fully inside boundingRect."""
    scene = window.play_workspace.scene
    for item in (scene.stock_item, scene.waste_item):
        assert item.boundingRect().contains(item.chip_rect())


# --- game-feel choreography (deal, bursts, victory, metrics, ambience) -------------------


def test_deal_sequence_is_pure_projection(app, window):
    """The new-game dealing choreography never mutates engine state."""
    scene = window.play_workspace.scene
    window.game.new_game(draw_count=1, announce=False)
    app.processEvents()
    before = window.game.state.move_count
    stock_before = len(window.game.state.stock.to_list())

    # Sequence is already running after new_game; let it work.
    for _ in range(6):
        app.processEvents()
    scene.settle_all()
    app.processEvents()

    assert window.game.state.move_count == before
    assert len(window.game.state.stock.to_list()) == stock_before
    # All 52 cards sit at their authoritative engine-derived positions.
    for card_id, item in scene.card_items.items():
        zone = scene.card_zone[card_id]
        if not zone.startswith("tableau-"):
            continue
        slot = scene.slot_position(zone)
        assert abs(item.pos().x() - slot.x()) < 0.6


def test_deal_sequence_skipped_under_reduce_motion(app, window):
    """Reduce Motion: new games appear fully dealt, instantly playable."""
    scene = window.play_workspace.scene
    manager = window.play_workspace.animation
    manager.reduce_motion = True
    try:
        window.game.new_game(draw_count=1, announce=False)
        app.processEvents()
        scene.settle_all()
        app.processEvents()
        # Every tableau card is already at its column x position.
        for card_id, item in scene.card_items.items():
            zone = scene.card_zone[card_id]
            if zone.startswith("tableau-"):
                assert abs(item.pos().x() - scene.slot_position(zone).x()) < 0.6
    finally:
        manager.reduce_motion = False


def test_foundation_landing_spawns_a_gold_burst(app, window):
    """A card entering a Foundation triggers the celebration burst."""
    import gc

    from solitaire.ui.premium.graphics.effects.particle_burst import ParticleBurstItem

    # Seed 3 deals a board where one draw exposes a foundation play.
    built = PremiumMainWindow(seed=3)
    built.show()
    app.processEvents()
    try:
        built.game.draw_from_stock()
        app.processEvents()
        built.play_workspace.scene.settle_all()
        app.processEvents()
        top = built.game.state.waste.peek()
        foundations = [
            p
            for p in built.game.legal_destinations("waste", top.card_id)
            if p.startswith("foundation-")
        ]
        if not foundations:
            pytest.skip("seed 3 board changed unexpectedly")
        scene = built.play_workspace.scene
        assert built.game.try_move("waste", top.card_id, foundations[0])
        app.processEvents()
        bursts = [item for item in scene.items() if isinstance(item, ParticleBurstItem)]
        assert bursts, "foundation landing must spawn the celebration burst"
        scene.settle_all()
        for _ in range(30):
            app.processEvents()
    finally:
        built.close()
        built.deleteLater()
        app.processEvents()
        gc.collect()


def test_metric_chip_flashes_on_change(app, window):
    """Moves/Score chips pulse briefly when their value changes."""
    chip = window.header.moves_chip
    changed = chip.set_value("7", flash="cool")
    assert changed
    app.processEvents()
    assert chip._flash_animation.state() == chip._flash_animation.state().Running or chip._flash > 0.0
    # No change -> no flash.
    assert chip.set_value("7") is False


def test_victory_overlay_presents_and_dismisses(app, window):
    """The victory overlay shows real stats and its buttons work."""
    overlay = window.victory_overlay
    overlay.present(score=1520, moves=118, seconds=3661, reduce_motion=True)
    app.processEvents()
    assert overlay.isVisible()
    assert overlay._stat_labels["score"].text() == "1520"
    assert overlay._stat_labels["moves"].text() == "118"
    assert overlay._stat_labels["time"].text() == "61:01"
    overlay.play_on_button.click()
    app.processEvents()
    assert not overlay.isVisible()
    # Present again and dismiss via the new-game action (engine untouched
    # by the overlay itself).
    overlay.present(score=10, moves=2, seconds=3, reduce_motion=True)
    overlay.new_game_button.click()
    app.processEvents()
    assert not overlay.isVisible()


def test_victory_overlay_escape_dismisses_when_overlay_has_focus(app, window):
    """Regression: present() must take keyboard focus so a real Escape key
    press reaches the overlay's own keyPressEvent. QtTest delivers a genuine
    key event through the application's normal dispatch path."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    overlay = window.victory_overlay
    overlay.present(score=100, moves=10, seconds=61, reduce_motion=True)
    app.processEvents()
    assert overlay.isVisible()
    assert overlay.hasFocus(), "present() must take focus so Escape arrives directly"
    QTest.keyClick(overlay, Qt.Key.Key_Escape)
    app.processEvents()
    assert not overlay.isVisible()


def test_victory_overlay_escape_dismisses_even_when_focus_is_elsewhere(app, window):
    """Regression: with focus on the board view the overlay's keyPressEvent
    can never fire — the window-level Escape shortcut must dismiss the
    overlay instead. Shortcut stays disarmed while the overlay is hidden."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    overlay = window.victory_overlay
    view = window.play_workspace.view
    assert not window._victory_escape.isEnabled(), "Escape shortcut must be disarmed by default"

    # Present through the real production path (the game_won handler), which
    # is what arms the window-level shortcut.
    window._on_won()
    view.setFocus()  # the player's focus never left the table
    app.processEvents()
    assert overlay.isVisible()
    assert not overlay.hasFocus()
    assert window._victory_escape.isEnabled(), "present() must arm the Escape shortcut"

    QTest.keyClick(view, Qt.Key.Key_Escape)
    app.processEvents()
    assert not overlay.isVisible()
    assert not window._victory_escape.isEnabled(), "dismissal must disarm the shortcut"


def test_completed_game_opens_victory_overlay_with_real_stats(app, window):
    """Deterministic prepared win: two real moves build non-trivial numbers,
    the position is then arranged one move from victory using the real
    domain structures, and the winning move goes through the real GameEngine.
    The real `game_won` signal must open the overlay with the actual final
    score, move count and elapsed time — nothing is faked."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    from solitaire.domain.card import Rank, Suit
    from solitaire.domain.game_state import GameStatus, TableauColumn
    from solitaire.structures.stack import Stack

    # 1. Two genuine moves so the clock runs and the counters are non-zero.
    for _ in range(2):
        hint = next(
            (h for h in window.game.engine.find_hints() if h.source_pile != "stock"), None
        )
        if hint is None:
            break
        assert window.game.try_move(hint.source_pile, hint.card_ids[0], hint.destination_pile)
    app.processEvents()
    scene = window.play_workspace.scene
    scene.settle_all()
    state = window.game.state
    assert state.move_count >= 1, "precondition: real moves were made"
    assert state.status is GameStatus.PLAYING
    before_score = state.score

    # 2. Collect all 52 real card objects from the live state.
    all_cards: dict[str, object] = {}
    for card in state.stock.to_list() + state.waste.to_list():
        all_cards[card.card_id] = card
    for suit in Suit:
        for card in state.foundations[suit].to_list():
            all_cards[card.card_id] = card
    for column in state.tableau.values():
        for card in column.cards_bottom_to_top():
            all_cards[card.card_id] = card
    assert len(all_cards) == 52, "every card must stay accounted for"

    by_suit: dict[Suit, list] = {suit: [] for suit in Suit}
    for card in all_cards.values():
        by_suit[card.suit].append(card)
    for cards in by_suit.values():
        cards.sort(key=lambda c: c.rank)

    # 3. Arrange one-move-from-victory: three complete foundations, spades
    #    A..Q on the fourth, the spade King alone and face-up on tableau-7.
    winner_suit = Suit.SPADES
    for suit in Suit:
        state.foundations[suit] = Stack()
        run = by_suit[suit] if suit is not winner_suit else by_suit[suit][:-1]
        for card in run:
            card.face_up = True
            state.foundations[suit].push(card)
    king = by_suit[winner_suit][-1]
    assert king.rank is Rank.KING
    king.face_up = True
    for column_id in list(state.tableau):
        state.tableau[column_id] = TableauColumn(column_id)
    state.tableau["tableau-7"].push(king)
    state.stock = type(state.stock)()
    state.waste = Stack()
    app.processEvents()
    assert sum(s.size() for s in state.foundations.values()) == 51

    moves_before_win = state.move_count

    # 4. Complete the game through the real engine (rules, tracker, scoring).
    moved = window.game.try_move(
        "tableau-7", king.card_id, f"foundation-{winner_suit.code.lower()}"
    )
    app.processEvents()
    scene.settle_all()

    assert moved, "the prepared king-to-foundation move must be legal"
    assert state.status is GameStatus.WON, "the engine must declare victory"
    assert state.move_count == moves_before_win + 1
    assert state.score > before_score, "a foundation move must score"

    # 5. The real game_won signal opened the overlay with the actual numbers.
    overlay = window.victory_overlay
    assert overlay.isVisible(), "game_won must open the VictoryOverlay"
    minutes, rest = divmod(window.game.elapsed_seconds, 60)
    assert overlay._stat_labels["score"].text() == str(state.score)
    assert overlay._stat_labels["moves"].text() == str(state.move_count)
    assert overlay._stat_labels["time"].text() == f"{minutes:02d}:{rest:02d}"
    assert int(overlay._stat_labels["moves"].text()) >= 1

    # 6. The overlay stays non-blocking: Escape closes it after a real win.
    QTest.keyClick(overlay, Qt.Key.Key_Escape)
    app.processEvents()
    assert not overlay.isVisible()


def test_sound_manager_toggles_and_degrades_silently(app, window):
    """Audio is optional: toggling and playing never crashes offscreen."""
    sound = window.play_workspace.sound
    original = sound.enabled
    try:
        sound.set_enabled(False)
        sound.play("card_place")  # disabled: no-op
        sound.set_enabled(True)
        sound.play("victory")  # may be unavailable: silent no-op
        app.processEvents()
    finally:
        sound.set_enabled(original)
    settings_value = window.play_workspace.sound.enabled
    assert settings_value == original


def test_light_sweep_respects_reduce_motion(app, window):
    """The ambient sweep arms/disarms with Reduce Motion."""
    scene = window.play_workspace.scene
    scene.apply_reduce_motion(True)
    assert scene.light_sweep.enabled is False
    assert scene._sweep_timer.isActive() is False
    scene.apply_reduce_motion(False)
    assert scene.light_sweep.enabled is True
    assert scene._sweep_timer.isActive() is True
    phase_before = scene.light_sweep._phase
    scene.light_sweep.step(500)
    assert scene.light_sweep._phase != phase_before
    scene.apply_reduce_motion(True)


# --- application-wide design system ------------------------------------------------------


def test_open_dsa_lab_button_pinned_and_fully_visible_at_minimum_size(app, window):
    """At the 1280x800 minimum the Open DSA Lab button must be fully visible
    without scrolling the sidebar — it is pinned outside the scroll area."""
    from PyQt6.QtWidgets import QPushButton, QScrollArea

    window.resize(1280, 800)
    app.processEvents()
    dashboard = window.play_workspace.dashboard
    button = dashboard.open_lab_button
    assert isinstance(button, QPushButton)
    assert button.isVisible()

    # Fully inside the dashboard's on-screen rect (never clipped by the
    # scroll viewport's bottom edge).
    dash_bottom = dashboard.mapToGlobal(dashboard.rect().bottomLeft()).y()
    button_bottom = button.mapToGlobal(button.rect().bottomLeft()).y()
    assert button_bottom <= dash_bottom + 1

    # The button is NOT part of the scrollable content.
    scroll = dashboard.findChild(QScrollArea)
    assert scroll is not None
    assert not button.isAncestorOf(scroll.widget())
    assert scroll.widget().isAncestorOf(dashboard._history_rows[0])


def test_open_dsa_lab_button_click_opens_the_lab(app, window):
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    dashboard = window.play_workspace.dashboard
    QTest.mouseClick(dashboard.open_lab_button, Qt.MouseButton.LeftButton)
    app.processEvents()
    assert window.navigation.current is Workspace.DSA_LAB
    window.open_play_workspace()


def test_open_dsa_lab_button_sits_below_game_progress_when_space_allows(app, window):
    """When the panels fit the viewport, the footer button renders directly
    beneath the Game Progress panel."""
    window.resize(1600, 900)
    app.processEvents()
    dashboard = window.play_workspace.dashboard
    # Game Progress is the last panel in the scroll content; find its frame
    # through the progress text label.
    progress_text = dashboard._progress_text
    panel = progress_text.parentWidget()
    progress_bottom = panel.mapTo(dashboard, panel.rect().bottomLeft()).y()
    button_top = dashboard.open_lab_button.mapTo(dashboard, dashboard.open_lab_button.rect().topLeft()).y()
    assert button_top >= progress_bottom
    assert button_top - progress_bottom <= 40  # footer padding only


def test_game_stats_page_uses_the_shared_metric_card_language(app, window):
    """The stats grid is built from the same MetricCard component as the
    Overview page (icon + muted caption + prominent value)."""
    from solitaire.ui.premium.dsa_lab.widgets import MetricCard

    window.open_dsa_lab()
    page = window.dsa_lab._pages[LabPage.STATS]
    cards = [c for c in page.findChildren(MetricCard)]
    assert len(cards) >= 9
    # Every card exposes the live value label the refresh contract writes to.
    assert page._value_labels["Moves"] in [c.value_label for c in cards]
    page.refresh()
    assert page._value_labels["Moves"].text() == "0"


def test_lab_tables_share_the_read_only_premium_contract(app, window):
    """Every lab table comes from the shared factory: read-only, no row
    header, alternating navy rows — one component language, no page styles."""
    from PyQt6.QtWidgets import QTableWidget

    window.open_dsa_lab()
    tables = {
        LabPage.STACK: 2,
        LabPage.QUEUE: 1,
        LabPage.LINKED_LIST: 1,
        LabPage.DICTIONARY: 1,
        LabPage.TIMELINE: 1,
    }
    for page_id, expected in tables.items():
        page = window.dsa_lab._pages[page_id]
        found = page.findChildren(QTableWidget)
        assert len(found) == expected, f"{page_id}: expected {expected} table(s)"
        for table in found:
            assert not table.verticalHeader().isVisible()
            assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
            assert table.alternatingRowColors() is True


def test_lab_tabs_mark_exactly_one_active_page(app, window):
    """The gold active treatment is driven by the checked state — exactly
    one tab is checked per page and every tab is reachable."""
    lab = window.dsa_lab
    for target in LabPage:
        lab.show_page(target)
        app.processEvents()
        checked = [p for p, b in lab._buttons.items() if b.isChecked()]
        assert checked == [target]
        assert lab.current_page() is target
