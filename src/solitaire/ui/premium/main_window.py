"""Premium main window: full-width header + stacked workspaces."""

from __future__ import annotations

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from solitaire.ui.premium.components.header.header_bar import HeaderBar
from solitaire.ui.premium.controllers.game_controller import GameController
from solitaire.ui.premium.controllers.navigation_controller import NavigationController
from solitaire.ui.premium.controllers.selection_controller import SelectionController
from solitaire.ui.premium.navigation import Workspace
from solitaire.ui.premium.screens.dsa_lab_workspace import DsaLabWorkspace
from solitaire.ui.premium.screens.game_mode_page import GameModePage
from solitaire.ui.premium.screens.play_workspace import PlayWorkspace
from solitaire.ui.premium.theme import DESIGN_H, DESIGN_W, MIN_WINDOW_H, MIN_WINDOW_W, qss


class PremiumMainWindow(QMainWindow):
    """Top-level shell for the premium casino presentation layer."""

    def __init__(self, parent=None, seed: int | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Klondike Solitaire — CSC200 DSA Edition")
        self.setMinimumSize(MIN_WINDOW_W, MIN_WINDOW_H)
        self.resize(DESIGN_W, DESIGN_H)
        self.setStyleSheet(qss())

        self._settings = QSettings("CSC200", "KlondikeSolitairePremium")
        self.game = GameController(self, seed=seed)
        self.selection = SelectionController(self.game)
        self.navigation = NavigationController(self)

        self.header = HeaderBar(self)
        self.play_workspace = PlayWorkspace(self.game, self.selection, self)
        self.dsa_lab = DsaLabWorkspace(self.game, on_back=self.open_play_workspace, parent=self)
        self.game_mode_page = GameModePage(
            self.game,
            draw_mode=self.game.draw_mode,
            reduce_motion=self._read_setting("reduce_motion", False, bool),
            speed_multiplier=self._read_setting("animation_speed", 1.0, float),
            show_sidebar=True,
            on_show_sidebar=self._set_sidebar_visible,
            on_new_game=self._game_mode_new_game,
            on_back=self._close_game_mode,
            parent=self,
        )

        self.workspaces = QStackedWidget(self)
        self.workspaces.addWidget(self.play_workspace)
        self.workspaces.addWidget(self.dsa_lab)
        self.workspaces.addWidget(self.game_mode_page)

        central = QWidget(self)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.header)
        central_layout.addWidget(self.workspaces, 1)
        self.setCentralWidget(central)

        # --- header wiring ------------------------------------------------------
        self.hint_button = self.header.hint_button
        self.undo_button = self.header.undo_button
        self.redo_button = self.header.redo_button
        self.settings_button = self.header.settings_button
        self.hint_button.clicked.connect(self._show_hint)
        self.undo_button.clicked.connect(self.game.undo)
        self.redo_button.clicked.connect(self.game.redo)
        self.settings_button.clicked.connect(self.open_settings)

        # --- game wiring ---------------------------------------------------------
        self.game.state_changed.connect(self._on_state_changed)
        self.game.operations_changed.connect(self._on_operations_changed)
        self.game.tick.connect(self._on_tick)
        self.game.game_won.connect(self._on_won)

        # --- navigation wiring ------------------------------------------------------
        self.navigation.workspace_changed.connect(self._switch_workspace)

        # --- shortcuts ---------------------------------------------------------------
        self._bind_shortcuts()

        self._reduce_motion = self._settings.value("reduce_motion", False, type=bool)
        self._speed_multiplier = self._settings.value("animation_speed", 1.0, type=float)
        self._apply_animation_settings()
        self._update_action_states()
        self._refresh_metrics()
        self.open_play_workspace()

    # --- navigation --------------------------------------------------------------
    def open_play_workspace(self) -> None:
        self.navigation.open_play()

    def closeEvent(self, event) -> None:  # noqa: N802
        # Halt cosmetic animation while every graphics item is still alive so
        # that later destruction (also from Python GC) cannot touch items
        # through a running animation. See CardAnimationManager lifecycle notes.
        self.play_workspace.scene.prepare_shutdown()
        super().closeEvent(event)

    def open_dsa_lab(self, page=None) -> None:
        self.navigation.open_dsa_lab()
        if page is not None:
            self.dsa_lab.show_page(page)

    def _switch_workspace(self, value: str) -> None:
        workspace = Workspace(value)
        index = {Workspace.PLAY: 0, Workspace.DSA_LAB: 1, Workspace.GAME_MODE: 2}[workspace]
        self.workspaces.setCurrentIndex(index)
        if workspace is Workspace.DSA_LAB:
            self.dsa_lab.refresh()
        elif workspace is Workspace.GAME_MODE:
            self._sync_game_mode()

    # --- header updates ------------------------------------------------------------
    def _refresh_metrics(self) -> None:
        metrics = self.game.metrics()
        self.header.set_metrics(metrics["time"], metrics["moves"], metrics["score"])

    def _on_tick(self, seconds: int) -> None:
        self._refresh_metrics()

    def _on_state_changed(self, reason: str) -> None:
        self._refresh_metrics()
        self._update_action_states()

    def _on_operations_changed(self) -> None:
        self.play_workspace.refresh_dashboard()
        self._update_action_states()

    def _update_action_states(self) -> None:
        self.undo_button.setEnabled(self.game.can_undo)
        self.redo_button.setEnabled(self.game.can_redo)

    # --- actions ----------------------------------------------------------------------
    def _show_hint(self) -> None:
        hint = self.game.hint_move()
        self.game.hint()
        self.play_workspace.show_hint(hint)

    def new_game(self) -> None:
        if self.game.state.move_count > 0 and not self.game.is_won:
            answer = QMessageBox.question(
                self,
                "New Game",
                "Discard the current game and deal a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.game.new_game(draw_count=self.game.draw_mode)

    def open_settings(self) -> None:
        """Open the Game Mode page (draw mode, motion, view, new game)."""
        self.navigation.open_workspace(Workspace.GAME_MODE)

    def _read_setting(self, key: str, default, type_):
        return self._settings.value(key, default, type=type_)

    def _sync_game_mode(self) -> None:
        page = self.game_mode_page
        (page._draw_three if self.game.draw_mode == 3 else page._draw_one).setChecked(True)
        page._reduce_motion.toggle.blockSignals(True)
        page._reduce_motion.toggle.setChecked(self._reduce_motion)
        page._reduce_motion.toggle.blockSignals(False)
        page._show_sidebar.toggle.blockSignals(True)
        page._show_sidebar.toggle.setChecked(self.play_workspace.dashboard.isVisible())
        page._show_sidebar.toggle.blockSignals(False)

    def _leave_game_mode(self) -> None:
        """Apply Game Mode choices and persist them before returning to play."""
        page = self.game_mode_page
        page.apply()
        self._reduce_motion = page.reduce_motion
        self._speed_multiplier = page.speed_multiplier
        self._apply_animation_settings()

    def _close_game_mode(self) -> None:
        self._leave_game_mode()
        self.open_play_workspace()

    def _game_mode_new_game(self) -> None:
        self._leave_game_mode()
        self.new_game()
        self.open_play_workspace()

    def _set_sidebar_visible(self, visible: bool) -> None:
        self.play_workspace.dashboard.setVisible(visible)

    def _apply_animation_settings(self) -> None:
        from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager

        manager = CardAnimationManager.instance()
        manager.reduce_motion = self._reduce_motion
        manager.speed_multiplier = self._speed_multiplier

    def _on_won(self) -> None:
        # Non-blocking: the feedback panel already shows the victory summary.
        self._update_action_states()

    # --- shortcuts -----------------------------------------------------------------------
    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.game.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.game.redo)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_game)
        QShortcut(QKeySequence("H"), self, activated=self._show_hint)
        QShortcut(QKeySequence("Space"), self, activated=self.game.draw_from_stock)
