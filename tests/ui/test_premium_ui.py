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
    stack_report_for_pile,
    structure_counts,
    timeline_rows,
)
from solitaire.ui.premium.main_window import PremiumMainWindow
from solitaire.ui.premium.navigation import LabPage, Workspace
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


def test_card_item_starts_a_real_qdrag_with_run_payload(window, monkeypatch):
    from PyQt6.QtGui import QDrag
    from PyQt6.QtCore import QByteArray
    from solitaire.ui.premium.controllers.drag_controller import MIME_TYPE

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

    captured = {}

    def fake_exec(self, *args, **kwargs):
        captured["mime"] = self.mimeData()
        captured["ids"] = face_up_ids
        return __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.DropAction.IgnoreAction

    monkeypatch.setattr(QDrag, "exec", fake_exec)

    scene = window.play_workspace.scene
    item = scene.card_items[face_up_ids[0]]
    assert item.drag_provider is not None
    assert item._start_drag() is True

    payload = captured["mime"]
    assert payload.hasFormat(MIME_TYPE)
    import json

    document = json.loads(bytes(payload.data(MIME_TYPE)))
    assert document["card_ids"] == face_up_ids
    assert document["source"] == column_id


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
