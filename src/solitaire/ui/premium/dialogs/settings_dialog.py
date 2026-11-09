"""Polished settings dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QVBoxLayout,
)

from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager
from solitaire.ui.premium.controllers.game_controller import GameController


class SettingsDialog(QDialog):
    """Draw mode, reduce motion, sidebar visibility and animation speed."""

    def __init__(self, game: GameController, *, show_sidebar: bool,
                 reduce_motion: bool, speed_multiplier: float,
                 on_show_sidebar, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._on_show_sidebar = on_show_sidebar
        self.setWindowTitle("Settings — Klondike Solitaire")
        self.setMinimumWidth(420)
        self._settings = QSettings("CSC200", "KlondikeSolitairePremium")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        draw_group = QGroupBox("Stock behaviour")
        draw_layout = QHBoxLayout(draw_group)
        self._draw_one = QRadioButton("Draw 1")
        self._draw_three = QRadioButton("Draw 3")
        (self._draw_three if game.draw_mode == 3 else self._draw_one).setChecked(True)
        draw_layout.addWidget(self._draw_one)
        draw_layout.addWidget(self._draw_three)
        layout.addWidget(draw_group)

        motion_group = QGroupBox("Motion")
        motion_layout = QVBoxLayout(motion_group)
        self._reduce_motion = QCheckBox("Reduce motion (skip card animations)")
        self._reduce_motion.setChecked(reduce_motion)
        motion_layout.addWidget(self._reduce_motion)
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Animation speed"))
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(5, 20)
        self._speed_slider.setValue(int(round(10 * speed_multiplier)))
        speed_row.addWidget(self._speed_slider, 1)
        self._speed_value = QLabel(f"{speed_multiplier:.1f}×")
        speed_row.addWidget(self._speed_value)
        self._speed_slider.valueChanged.connect(
            lambda value: self._speed_value.setText(f"{value / 10.0:.1f}×")
        )
        motion_layout.addLayout(speed_row)
        layout.addWidget(motion_group)

        view_group = QGroupBox("View")
        view_layout = QVBoxLayout(view_group)
        self._show_sidebar = QCheckBox("Show DSA sidebar in the Play Workspace")
        self._show_sidebar.setChecked(show_sidebar)
        view_layout.addWidget(self._show_sidebar)
        layout.addWidget(view_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- results --------------------------------------------------------------
    @property
    def draw_count(self) -> int:
        return 3 if self._draw_three.isChecked() else 1

    @property
    def reduce_motion(self) -> bool:
        return self._reduce_motion.isChecked()

    @property
    def show_sidebar(self) -> bool:
        return self._show_sidebar.isChecked()

    @property
    def speed_multiplier(self) -> float:
        return self._speed_slider.value() / 10.0

    def apply(self) -> None:
        """Apply the dialog results to the live game and persist them."""
        self._game.set_draw_mode(self.draw_count)
        manager = CardAnimationManager.instance()
        manager.reduce_motion = self.reduce_motion
        manager.speed_multiplier = self.speed_multiplier
        self._on_show_sidebar(self.show_sidebar)
        self._settings.setValue("draw_count", self.draw_count)
        self._settings.setValue("reduce_motion", self.reduce_motion)
        self._settings.setValue("show_sidebar", self.show_sidebar)
        self._settings.setValue("animation_speed", self.speed_multiplier)
