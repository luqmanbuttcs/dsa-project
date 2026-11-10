"""Responsive-layout and animation-speed regressions.

Covers the three final-UI-fix areas:

* the Settings workspace keeps every row at its full size hint and reaches
  every control (scrolling when short, no scrollbar when roomy);
* the Play workspace keeps the dashboard, Game Progress and the pinned
  Open DSA Lab button accessible at every supported window size, and window
  transitions (maximize / restore / resize) recalculate the layout;
* the animation-speed multiplier genuinely divides durations (2.0x = twice
  the speed), all cosmetic timelines follow it, and finished/interrupted
  animations are retired instead of accumulating.

All tests run with QT_QPA_PLATFORM=offscreen (see tests/ui/conftest.py).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QAbstractAnimation, QPointF, QSettings
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QLabel, QPushButton, QSlider

from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager
from solitaire.ui.premium.theme import ANIMATION_MS, MIN_WINDOW_H, MIN_WINDOW_W

# The full matrix from the task: 1280x720 and 1366x768 are the short laptop
# sizes (Windows 150% DPI scaling presents 1920x1080 as 1280x720 logical).
WINDOW_SIZES = [
    (1280, 640),  # supported minimum (MIN_WINDOW_H)
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]


def _resize(app, window, width, height):
    window.resize(width, height)
    app.processEvents()
    app.processEvents()


def _fully_visible(widget) -> bool:
    """True when nothing occludes or clips *widget* inside its own rect."""
    if not widget.isVisible():
        return False
    region = widget.visibleRegion().boundingRect()
    return (
        region.width() >= widget.width()
        and region.height() >= widget.height()
    )


def _reach(app, scroll, widget) -> bool:
    """Scroll *widget* into view and require it to be fully visible."""
    if widget.width() <= 0 or widget.height() <= 0:
        return False
    scroll.ensureWidgetVisible(widget, 0, 0)
    app.processEvents()
    app.processEvents()
    return _fully_visible(widget)


def _motion_rows(page):
    return [page._reduce_motion, page._show_sidebar, page._sound, page._light_sweep]


def _shortcut_chips(page):
    chips = []
    for label in page.findChildren(QLabel):
        if label.minimumHeight() == 22 and label.minimumWidth() == 110:
            chips.append(label)
    return chips


# --- Settings workspace -----------------------------------------------------------------


@pytest.mark.parametrize("width,height", WINDOW_SIZES)
def test_settings_rows_keep_full_height_and_reach_every_control(app, window, width, height):
    _resize(app, window, width, height)
    window.open_settings()
    app.processEvents()
    page = window.game_mode_page
    scroll = page._scroll

    # 1. No row may be crushed below its own minimum: the historical defect
    #    squeezed toggle rows to 18px and the Animation Speed title to 3px.
    for row in _motion_rows(page):
        assert row.height() >= row.minimumSizeHint().height(), (
            f"{row.findChildren(QLabel)[0].text()} crushed to {row.height()}px "
            f"(needs {row.minimumSizeHint().height()}px) at {width}x{height}"
        )
        title, description = row.findChildren(QLabel)[:2]
        assert title.height() >= title.minimumSizeHint().height()
        assert description.height() >= description.minimumSizeHint().height()

    # 2. Rows must not overlap each other.
    rows = sorted(_motion_rows(page), key=lambda r: r.y())
    for upper, lower in zip(rows, rows[1:]):
        assert not upper.geometry().intersects(lower.geometry())

    # 3. The Animation Speed control is reachable and intact.
    slider = page.findChildren(QSlider)[0]
    assert _reach(app, scroll, slider), f"speed slider unreachable at {width}x{height}"
    speed_value = page._speed_value
    assert _reach(app, scroll, speed_value)
    assert slider.height() >= slider.minimumSizeHint().height()

    # 4. Every keyboard shortcut badge shows its complete text (not clipped).
    for chip in _shortcut_chips(page):
        assert chip.height() >= chip.minimumHeight(), (
            f"shortcut badge '{chip.text()}' clipped at {width}x{height}"
        )
        assert _reach(app, scroll, chip), (
            f"shortcut badge '{chip.text()}' unreachable at {width}x{height}"
        )

    # 5. The mode cards keep their content height (QPushButton ignores its
    #    child layout for hints; without the floor they collapsed to strips).
    for card in (page._draw_one, page._draw_three):
        assert card.height() >= 108, f"mode card collapsed to {card.height()}px"


def test_settings_shortcut_rows_never_overlap(app, window):
    _resize(app, window, 1366, 768)
    window.open_settings()
    app.processEvents()
    chips = sorted(_shortcut_chips(window.game_mode_page), key=lambda c: c.y())
    assert len(chips) == 6
    for upper, lower in zip(chips, chips[1:]):
        assert not upper.geometry().intersects(lower.geometry())


def test_settings_fit_without_scrolling_at_roomy_sizes(app, window):
    """At the design and maximized sizes the content fits naturally."""
    for width, height in [(1600, 900), (1920, 1080)]:
        _resize(app, window, width, height)
        window.open_settings()
        app.processEvents()
        assert window.game_mode_page._scroll.verticalScrollBar().maximum() == 0, (
            f"settings must fit without scrolling at {width}x{height}"
        )


def test_settings_scroll_reaches_the_bottom_at_short_sizes(app, window):
    _resize(app, window, 1280, 720)
    window.open_settings()
    app.processEvents()
    page = window.game_mode_page
    scroll = page._scroll
    assert scroll.verticalScrollBar().maximum() > 0, (
        "short windows must offer scrolling instead of crushing content"
    )
    # Everything inside the scroll area is reachable, including the last row.
    chips = _shortcut_chips(page)
    assert _reach(app, scroll, chips[-1])
    # The New Game action lives in the fixed footer: visible without scrolling.
    footer_button = next(
        button
        for button in page.findChildren(QPushButton)
        if button.objectName() == "goldButton" and "New Game" in button.text()
    )
    assert footer_button.isVisible() and _fully_visible(footer_button)
    # ... and the navigation header above the scroll area stays accessible.
    assert window.play_workspace is not None
    back_button = next(
        button
        for button in page.findChildren(QPushButton)
        if "Return to Play" in button.text()
    )
    assert _fully_visible(back_button)


def test_settings_new_game_action_reachable_at_the_minimum_size(app, window):
    _resize(app, window, MIN_WINDOW_W, MIN_WINDOW_H)
    window.open_settings()
    app.processEvents()
    page = window.game_mode_page
    footer_button = next(
        button
        for button in page.findChildren(QPushButton)
        if button.objectName() == "goldButton" and "New Game" in button.text()
    )
    assert footer_button.isVisible() and _fully_visible(footer_button)


# --- Play workspace ---------------------------------------------------------------------


@pytest.mark.parametrize("width,height", WINDOW_SIZES)
def test_play_dashboard_stays_accessible_at_every_size(app, window, width, height):
    _resize(app, window, width, height)
    window.open_play_workspace()
    app.processEvents()
    dashboard = window.play_workspace.dashboard

    # The pinned Open DSA Lab footer button: fully visible, always.
    button = dashboard.open_lab_button
    assert button.isVisible(), f"Open DSA Lab hidden at {width}x{height}"
    assert _fully_visible(button), (
        f"Open DSA Lab clipped at {width}x{height}: "
        f"{button.visibleRegion().boundingRect()} vs {button.geometry()}"
    )

    # Game Progress: reachable through the dashboard's own scroll area.
    progress_panel = dashboard._progress.parentWidget()
    assert _reach(app, dashboard._scroll, progress_panel), (
        f"Game Progress unreachable at {width}x{height}"
    )

    # The header (with Hint/Undo/Redo/Settings) and the board stay usable.
    assert window.header.isVisible()
    assert window.play_workspace.view.isVisible()
    assert window.play_workspace.move_log.isVisible()


def test_no_important_control_lost_at_the_minimum_size(app, window):
    _resize(app, window, MIN_WINDOW_W, MIN_WINDOW_H)
    window.open_play_workspace()
    app.processEvents()
    assert window.play_workspace.dashboard.open_lab_button.isVisible()
    assert window.header.settings_button.isVisible()
    # The Settings workspace must also open and remain usable at the minimum.
    window.open_settings()
    app.processEvents()
    assert window.game_mode_page._speed_slider.isVisible()
    window.open_play_workspace()
    app.processEvents()
    assert window.play_workspace.view.isVisible()


def test_window_transitions_recalculate_the_layout(app, window):
    """Launch -> maximize -> restore -> resize -> maximize keeps every panel
    fresh: the board refits the viewport and no control goes stale."""
    from PyQt6.QtCore import QSize

    view = window.play_workspace.view
    dashboard = window.play_workspace.dashboard

    _resize(app, window, 1600, 900)
    baseline = QSize(view.viewport().size())

    window.showMaximized()
    app.processEvents()
    QTest.qWait(60)
    maximized = QSize(view.viewport().size())
    assert maximized != baseline, "maximizing must re-fit the board viewport"
    assert _fully_visible(dashboard.open_lab_button)

    window.showNormal()
    app.processEvents()
    QTest.qWait(60)
    assert QSize(view.viewport().size()) == baseline, (
        "restoring must recalculate the layout to the restored geometry"
    )
    assert _fully_visible(dashboard.open_lab_button)

    _resize(app, window, 1366, 768)
    resized = QSize(view.viewport().size())
    assert resized != baseline
    # The scene relayout must place every card inside the adapted scene rect.
    scene = window.play_workspace.scene
    scene.settle_all()
    app.processEvents()
    # Small tolerance: decorative shadows may graze the rect edge by a couple
    # of pixels, but a stale (unrelaid-out) item would land far outside.
    tolerant = scene.sceneRect().adjusted(-6.0, -6.0, 6.0, 6.0)
    for item in scene.card_items.values():
        assert tolerant.contains(item.sceneBoundingRect()), (
            "card left outside the refitted scene after resize"
        )
    assert _fully_visible(dashboard.open_lab_button)

    window.showMaximized()
    app.processEvents()
    QTest.qWait(60)
    assert QSize(view.viewport().size()) == maximized
    assert _fully_visible(dashboard.open_lab_button)


# --- animation speed & lifecycle ---------------------------------------------------------


@pytest.fixture()
def speed_guard():
    """Save/restore the manager speed settings and the persisted preference."""
    manager = CardAnimationManager.instance()
    original_speed = manager.speed_multiplier
    original_reduce = manager.reduce_motion
    settings = QSettings("CSC200", "KlondikeSolitairePremium")
    original_stored = settings.value("animation_speed", 1.0, type=float)
    yield manager, settings
    manager.speed_multiplier = original_speed
    manager.reduce_motion = original_reduce
    settings.setValue("animation_speed", original_stored)


def test_speed_multiplier_divides_durations(app, speed_guard):
    manager, _settings = speed_guard
    manager.reduce_motion = False

    manager.speed_multiplier = 2.0
    assert manager.duration_for(160) == 80, "2.0x must mean twice the speed"
    assert manager.duration_for(ANIMATION_MS["move"]) == ANIMATION_MS["move"] // 2

    manager.speed_multiplier = 1.0
    assert manager.duration_for(160) == 160

    manager.speed_multiplier = 0.5
    assert manager.duration_for(160) == 320

    manager.speed_multiplier = 2.0
    assert manager.duration_for(ANIMATION_MS["flip"]) == ANIMATION_MS["flip"] // 2


def test_real_card_animation_uses_the_scaled_duration(app, window, speed_guard):
    manager, _settings = speed_guard
    manager.reduce_motion = False
    manager.speed_multiplier = 2.0
    scene = window.play_workspace.scene
    scene.settle_all()
    app.processEvents()
    item = next(it for it in scene.card_items.values() if it.card.face_up)
    try:
        start = QPointF(item.pos())
        target = QPointF(start.x() + 24.0, start.y())
        animation = manager.animate_move(item, start, target, item.zValue())
        assert animation is not None
        assert animation.duration() == ANIMATION_MS["move"] // 2, (
            "a real movement must play at the requested speed"
        )
    finally:
        manager.interrupt_all()
        scene.settle_all()


def test_drag_lift_timeline_follows_the_speed_multiplier(app, window, speed_guard):
    manager, _settings = speed_guard
    manager.reduce_motion = False
    scene = window.play_workspace.scene
    scene.settle_all()
    app.processEvents()
    item = next(it for it in scene.card_items.values() if it.card.face_up)
    try:
        manager.speed_multiplier = 1.0
        item.begin_drag_session()
        assert item._property_animations["drag_lift"].duration() == 140
        item.end_drag_session()
        scene.settle_all()

        manager.speed_multiplier = 2.0
        item.begin_drag_session()
        assert item._property_animations["drag_lift"].duration() == 70, (
            "the drag lift must speed up with the multiplier, not stay raw"
        )
        item.end_drag_session()
        scene.settle_all()
    finally:
        scene.settle_all()


def test_deal_stagger_and_travel_scale_with_speed(app, window, speed_guard):
    """The dealer choreography must not keep long pauses at high speed."""
    manager, _settings = speed_guard
    manager.reduce_motion = False
    scene = window.play_workspace.scene
    manager.speed_multiplier = 1.0
    assert scene._animation.duration_for(36) == 36

    manager.speed_multiplier = 2.0
    window.game.new_game(draw_count=window.game.draw_mode)
    app.processEvents()
    stagger = scene._animation.duration_for(36)
    assert stagger == 18, "2.0x must halve the per-card deal gap"


def test_finished_and_interrupted_animations_are_retired(app, window, speed_guard):
    manager, _settings = speed_guard
    manager.reduce_motion = False
    manager.speed_multiplier = 1.0
    scene = window.play_workspace.scene
    scene.settle_all()
    app.processEvents()
    item = next(it for it in scene.card_items.values() if it.card.face_up)
    start = QPointF(item.pos())

    animation = manager.animate_move(
        item, start, QPointF(start.x() + 10.0, start.y()), item.zValue()
    )
    assert animation in manager._active
    animation.setCurrentTime(animation.duration())  # drive to the end
    assert animation.state() == QAbstractAnimation.State.Stopped
    assert animation not in manager._active, "finished animations must retire"
    QTest.qWait(20)  # let deleteLater() deliver
    from PyQt6 import sip

    assert sip.isdeleted(animation), "retired timelines must be released"

    second = manager.animate_move(
        item, start, QPointF(start.x() + 20.0, start.y()), item.zValue()
    )
    manager.interrupt_for(item)  # a real supersede must retire immediately
    assert second not in manager._active
    QTest.qWait(20)
    assert sip.isdeleted(second)
    scene.settle_all()


def test_settings_slider_maps_to_manager_and_persists(app, window, speed_guard):
    manager, settings = speed_guard
    window.open_settings()
    app.processEvents()
    page = window.game_mode_page

    page._speed_slider.setValue(20)
    page.apply()
    assert manager.speed_multiplier == 2.0
    assert settings.value("animation_speed", 1.0, type=float) == 2.0

    page._speed_slider.setValue(10)
    page.apply()
    assert manager.speed_multiplier == 1.0
    assert settings.value("animation_speed", 1.0, type=float) == 1.0
