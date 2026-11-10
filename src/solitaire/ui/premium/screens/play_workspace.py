"""Play Workspace: the casino board plus the fixed right dashboard."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager
from solitaire.ui.premium.components.dashboard.dsa_dashboard import DsaDashboard
from solitaire.ui.premium.components.game.feedback_panel import FeedbackPanel
from solitaire.ui.premium.components.game.move_log import MoveLogPanel
from solitaire.ui.premium.controllers.game_controller import (
    FEEDBACK_ERROR,
    FEEDBACK_SUCCESS,
    FEEDBACK_VICTORY,
    GameController,
)
from solitaire.ui.premium.controllers.selection_controller import SelectionController
from solitaire.ui.premium.graphics.game_board_scene import GameBoardScene
from solitaire.ui.premium.graphics.game_board_view import GameBoardView


class PlayWorkspace(QWidget):
    """Game area (~73–75%) + fixed dashboard (~25–27%)."""

    def __init__(self, game: GameController, selection: SelectionController, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        self.scene = GameBoardScene(game, selection, self)
        self.animation = CardAnimationManager.instance()
        self.scene.set_animation_manager(self.animation)

        self.view = GameBoardView(self.scene, self)

        board_frame = QFrame()
        board_frame.setObjectName("boardFrame")
        board_layout = QVBoxLayout(board_frame)
        board_layout.setContentsMargins(6, 6, 6, 6)
        board_layout.setSpacing(6)
        board_layout.addWidget(self.view, 1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        self.move_log = MoveLogPanel(game, board_frame)
        self.feedback_panel = FeedbackPanel(board_frame)
        bottom_row.addWidget(self.move_log, 5)
        bottom_row.addWidget(self.feedback_panel, 4)
        board_layout.addLayout(bottom_row)

        self.dashboard = DsaDashboard(game, on_open_lab=self._open_lab, parent=self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 0, 10)
        layout.setSpacing(10)
        layout.addWidget(board_frame, 1)
        layout.addWidget(self.dashboard)

        # --- wiring -----------------------------------------------------------
        game.state_changed.connect(self._on_state_changed)
        game.feedback.connect(self.feedback_panel.show_feedback)
        game.move_logged.connect(self.move_log.add_move)

    def _open_lab(self, page=None) -> None:
        """Open the DSA Lab, optionally on the clicked structure's page."""
        window = self.window()
        if hasattr(window, "open_dsa_lab"):
            window.open_dsa_lab(page)

    def _on_state_changed(self, reason: str) -> None:
        if reason == "new-game":
            self.move_log.clear_log()
            self.animation.interrupt_all()
            # A fresh table must never inherit the previous game's feedback
            # card — return the panel to its quiet idle state immediately.
            self.feedback_panel.show_idle()
        self.scene.sync(animate=reason not in ("new-game",))
        self.dashboard.refresh()

    def refresh_dashboard(self) -> None:
        self.dashboard.refresh()

    def show_hint(self, hint) -> None:
        self.scene.show_hint(hint)
