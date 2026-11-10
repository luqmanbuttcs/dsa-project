"""Real-event-loop interaction sweep for the premium shell.

Drives the actual running application (not controller methods) through
every interactive surface: card clicks, drag starts, a real drop onto
the scene, header buttons, Game Mode page, dashboard rows, all eight
DSA Lab pages, every combo/search control, resize, dialogs, clock ticks,
and the undo/redo/draw stress path. A recording sys.excepthook converts
any exception escaping a Qt slot into a collected report instead of the
PyQt6 default qFatal abort — so one run lists *every* interaction bug
that would terminate the real app on Windows.

Usage: QT_QPA_PLATFORM=offscreen python scripts/interaction_sweep.py
Exit 0 + 'SWEEP CLEAN' = no exception escaped any slot; otherwise each
escaping exception is printed with traceback and the exit code is 1.
"""

from __future__ import annotations

import os
import sys
import traceback

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

ESCAPED: list[str] = []


def _install_hook() -> None:
    def hook(kind, value, tb):
        formatted = "".join(traceback.format_exception(kind, value, tb))
        ESCAPED.append(formatted)
        print(f"[hook] exception escaped a slot:\n{formatted}", file=sys.stderr, flush=True)

    sys.excepthook = hook


def main() -> int:
    import faulthandler

    from PyQt6.QtCore import QPoint, QPointF, Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import (
        QApplication,
        QGraphicsView,
        QLineEdit,
        QMessageBox,
        QWidget,
    )

    from solitaire.ui.premium.main_window import PremiumMainWindow
    from solitaire.ui.premium.navigation import LabPage

    # Watchdog: if any stage blocks, dump all thread stacks and exit.
    faulthandler.dump_traceback_later(120, exit=True)

    _install_hook()
    app = QApplication.instance() or QApplication([])

    # Offscreen has no native drag hand-off: QDrag.exec would park in a
    # nested loop forever. Stub it (as the automated tests do) — the drag
    # start path stays real, drops are delivered via simulated_drop below.
    from PyQt6.QtGui import QDrag

    QDrag.exec = lambda self, *args, **kwargs: Qt.DropAction.IgnoreAction  # type: ignore[method-assign]

    window = PremiumMainWindow()  # random seed, like the real app
    window.resize(1600, 900)
    window.show()
    views = window.play_workspace.findChildren(QGraphicsView)
    assert views, "no graphics view in play workspace"
    view = views[0]
    scene = view.scene()

    def pump(times: int = 6) -> None:
        for _ in range(times):
            app.processEvents()

    def click_scene_item(item) -> None:
        center = item.mapToScene(item.boundingRect().center())
        local = view.mapFromScene(center)
        QTest.mouseClick(
            view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, local
        )
        pump()

    def click_widget(widget: QWidget) -> None:
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
        pump(3)

    def press_move_release(item, dx: int, dy: int) -> None:
        start = view.mapFromScene(item.mapToScene(item.boundingRect().center()))
        QTest.mousePress(
            view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
        )
        pump(2)
        for step in range(1, 5):
            QTest.mouseMove(view.viewport(), start + QPoint(dx * step // 4, dy * step // 4))
            pump(2)
        QTest.mouseRelease(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            start + QPoint(dx, dy),
        )
        pump()

    def simulated_drop(item, dx: int, dy: int) -> None:
        """Deliver a real drop for the payload `item` would drag.

        Offscreen QDrag.exec() cannot perform a native hand-off, so a
        genuine QDropEvent carrying the same mime payload is sent to the
        view's viewport; QGraphicsView forwards it into the scene's drop
        path exactly as a native drop would arrive.
        """
        import json

        from PyQt6.QtCore import QEvent, QMimeData, QPointF, Qt
        from PyQt6.QtGui import QDropEvent

        from solitaire.ui.premium.controllers.drag_controller import MIME_TYPE

        payload = scene._drag_payload_for(item.card_id)
        if not payload:
            return
        card_ids, source = payload
        mime = QMimeData()
        mime.setData(
            MIME_TYPE,
            json.dumps({"card_ids": card_ids, "source": source}).encode("utf-8"),
        )
        target_scene_pos = item.scenePos() + QPointF(dx, dy)
        local = view.mapFromScene(target_scene_pos)
        drop = QDropEvent(
            QPointF(local),
            Qt.DropAction.MoveAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QEvent.Type.Drop,
        )
        app.sendEvent(view.viewport(), drop)
        pump()

    def auto_answer_dialog(delay_ms: int = 120) -> None:
        def answer():
            dialog = QApplication.activeModalWidget()
            if isinstance(dialog, QMessageBox):
                dialog.done(QMessageBox.StandardButton.Yes)

        QTimer_singleShot = __import__("PyQt6.QtCore", fromlist=["QTimer"]).QTimer.singleShot
        QTimer_singleShot(delay_ms, answer)

    stage = lambda text: print(text, flush=True)  # noqa: E731

    # -- 1. board interaction: draws, selections, invalid attempts ------------
    stage("stage 1: board clicks (stock, waste, tableau, foundations)")
    for _ in range(4):
        click_scene_item(scene.stock_item)
    click_scene_item(scene.waste_item)
    for index in range(1, 8):
        click_scene_item(scene.tableau_items[f"tableau-{index}"])
        click_scene_item(scene.foundation_items["foundation-h"])
    for index in range(1, 8):
        column = window.game.state.tableau[f"tableau-{index}"]
        cards = column.cards_bottom_to_top()
        if cards:
            item = scene.card_items.get(cards[0].card_id)
            if item is not None:
                click_scene_item(item)
                click_scene_item(item)

    # -- 2. drags: real press-move-release + real drop delivery ----------------
    stage("stage 2: drag attempts and delivered drops")
    press_move_release(scene.waste_item, 160, 200)
    waste_cards = window.game.state.waste.to_list()
    if waste_cards:
        simulated_drop(scene.card_items[waste_cards[-1].card_id], 160, 200)
    for index in range(1, 8):
        column = window.game.state.tableau[f"tableau-{index}"]
        cards = column.cards_bottom_to_top()
        face_up = [c for c in cards if c.face_up]
        if face_up:
            item = scene.card_items.get(face_up[0].card_id)
            if item is not None:
                press_move_release(item, 60, 260)
                simulated_drop(item, 60, 260)

    # -- 3. stress with animations in flight + real clock ticks ----------------
    stage("stage 3: draw/move/undo/redo/hint stress with animations in flight")
    for step in range(24):
        hints = [h for h in window.game.engine.find_hints() if h.source_pile != "stock"]
        if step % 4 == 0:
            window.game.undo()
        elif step % 4 == 1:
            window.game.draw_from_stock()
        elif step % 4 == 2 and hints:
            window.game.try_move(
                hints[0].source_pile, hints[0].card_ids[0], hints[0].destination_pile
            )
        elif step % 4 == 3:
            window.game.redo()
        pump(2)
    window.game.undo()
    pump(2)
    if window.game._clock_running:
        QTest.qWait(1300)  # force at least one real clock tick through the loop
        pump(4)

    # -- 4. header buttons ------------------------------------------------------
    stage("stage 4: header buttons (hint, undo, redo, settings)")
    window._show_hint()
    pump()
    window.game.undo()
    window.game.redo()
    pump()

    # -- 5. Game Mode page --------------------------------------------------------
    stage("stage 5: game mode toggles, slider, dashboard switch, new game dialog")
    window.open_settings()
    pump()
    page = window.game_mode_page
    page._draw_three.setChecked(True)
    pump()
    page._draw_one.setChecked(True)
    pump()
    page._reduce_motion.toggle.setChecked(True)
    pump()
    page._reduce_motion.toggle.setChecked(False)
    pump()
    page._show_sidebar.toggle.setChecked(False)
    pump()
    page._show_sidebar.toggle.setChecked(True)
    pump()
    page._speed_slider.setValue(page._speed_slider.minimum())
    page._speed_slider.setValue(page._speed_slider.maximum())
    page._speed_slider.setValue(100)
    pump()
    auto_answer_dialog()
    window._game_mode_new_game()  # modal confirm -> auto-answered Yes
    pump(10)

    # -- 6. dashboard rows open the lab -------------------------------------------
    stage("stage 6: dashboard structure rows -> DSA Lab")
    for _ in range(3):
        window.game.draw_from_stock()
    pump()
    dashboard = window.play_workspace.dashboard
    clickable = [
        child
        for child in dashboard.findChildren(QWidget)
        if hasattr(child, "clicked") and not child.metaObject().className().startswith("Q")
    ]
    for child in clickable:
        click_widget(child)
        pump(4)
        window.open_play_workspace()
        pump(4)
    window.open_dsa_lab()
    pump()
    lab = window.dsa_lab

    # -- 7. every lab page + every control on it -----------------------------------
    stage("stage 7: all lab pages and their controls")
    lab_pages = [
        LabPage.OVERVIEW,
        LabPage.ARRAY,
        LabPage.STACK,
        LabPage.QUEUE,
        LabPage.LINKED_LIST,
        LabPage.DICTIONARY,
        LabPage.TIMELINE,
        LabPage.STATS,
    ]
    for lab_page in lab_pages:
        print(f"  7: page {lab_page.value}", flush=True)
        lab.show_page(lab_page)
        pump(4)
        current = lab._pages[lab_page]
        for combo in current.findChildren(__import__("PyQt6.QtWidgets", fromlist=["QComboBox"]).QComboBox):
            for i in range(combo.count()):
                combo.setCurrentIndex(i)
                pump(2)
            combo.setCurrentIndex(0)
            pump(2)
        for line_edit in current.findChildren(QLineEdit):
            line_edit.setText("H")
            pump(2)
            line_edit.setText("K")
            pump(2)
            line_edit.clear()
            pump(2)
    window.open_play_workspace()
    pump()

    # -- 8. resize / relayout --------------------------------------------------------
    stage("stage 8: resize to minimum and back")
    window.resize(1280, 800)
    pump(4)
    window.resize(1600, 900)
    pump(4)

    # -- 9. clean close ---------------------------------------------------------------
    stage("stage 9: clean close")
    window.close()
    pump(4)

    if ESCAPED:
        print(f"\nSWEEP FOUND {len(ESCAPED)} ESCAPING EXCEPTION(S):")
        for i, tb in enumerate(ESCAPED, 1):
            print(f"--- exception {i} ---\n{tb}")
        return 1
    print("SWEEP CLEAN — no exception escaped any slot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
