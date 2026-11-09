"""Game Mode page: draw-mode cards, motion and view controls, new game.

Reaches from the header Settings control and returns to the Play Workspace.
All controls mutate the live game through the existing GameController and
persist via QSettings — no duplicated or contradictory logic.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.animations.card_animation_manager import CardAnimationManager
from solitaire.ui.premium.components.common.icons import icon_pixmap


class ModeCard(QPushButton):
    """Selectable Draw 1 / Draw 3 mode card with a gold active ring."""

    def __init__(self, title: str, subtitle: str, icon_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("modeCard")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(128)
        self.setIconSize(self.iconSize())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap(icon_name, 30))
        icon_label.setFixedSize(34, 34)
        icon_label.setScaledContents(True)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: #E8C766; font-weight: bold; font-size: 18px; background: transparent;"
        )
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("mutedText")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)


class ToggleRow(QWidget):
    """A labelled settings row with a checkable switch-like control."""

    def __init__(self, title: str, subtitle: str, checked: bool, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        text_column = QVBoxLayout()
        text_column.setSpacing(1)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #F2EEE2; font-weight: bold; font-size: 14px;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("mutedText")
        subtitle_label.setWordWrap(True)
        text_column.addWidget(title_label)
        text_column.addWidget(subtitle_label)
        row.addLayout(text_column, 1)

        self.toggle = QPushButton()
        self.toggle.setObjectName("toggleSwitch")
        self.toggle.setCheckable(True)
        self.toggle.setChecked(checked)
        self.toggle.setFixedSize(58, 28)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.clicked.connect(lambda: self.toggle.setStyleSheet(self._switch_qss()))
        self.toggle.setStyleSheet(self._switch_qss())
        row.addWidget(self.toggle)

    @staticmethod
    def _switch_qss() -> str:
        return """
        QPushButton#toggleSwitch {
            border-radius: 14px; border: 1px solid #8C6D1D;
        }
        QPushButton#toggleSwitch:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #F0C75E, stop:1 #C9A227);
        }
        QPushButton#toggleSwitch:!checked {
            background: #13253D;
        }
        """

    @property
    def checked(self) -> bool:
        return self.toggle.isChecked()


class GameModePage(QWidget):
    """Full-screen Game Mode & settings presentation."""

    def __init__(self, game, *, draw_mode: int, reduce_motion: bool,
                 speed_multiplier: float, show_sidebar: bool,
                 on_show_sidebar, on_new_game, on_back, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._on_show_sidebar = on_show_sidebar
        self._on_new_game = on_new_game
        self._on_back = on_back

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("labTopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)
        back_button = QPushButton("  ← Return to Play Workspace")
        back_button.setObjectName("goldButton")
        back_button.clicked.connect(on_back)
        top_layout.addWidget(back_button)
        title = QLabel("Game Mode & Settings")
        title.setObjectName("appTitle")
        top_layout.addSpacing(10)
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        layout.addWidget(top_bar)

        body_holder = QWidget()
        body = QVBoxLayout(body_holder)
        body.setContentsMargins(24, 20, 24, 20)
        body.setSpacing(16)

        heading = QLabel("Choose how the Stock deals")
        heading.setStyleSheet(
            "color: #E8C766; font-weight: bold; font-size: 16px; background: transparent;"
        )
        body.addWidget(heading)

        # --- draw mode cards -------------------------------------------------
        modes = QHBoxLayout()
        modes.setSpacing(14)
        self._draw_one = ModeCard(
            "Draw 1", "Draw one card from the Stock to the Waste on each click — "
            "the classic, gentler Klondike variant.", "queue"
        )
        self._draw_three = ModeCard(
            "Draw 3", "Deal three cards at a time — fewer Waste options, a "
            "sharper challenge for experienced players.", "swap"
        )
        (self._draw_three if draw_mode == 3 else self._draw_one).setChecked(True)
        from PyQt6.QtWidgets import QButtonGroup

        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self._draw_one)
        self._mode_group.addButton(self._draw_three)
        self._mode_group.setExclusive(True)
        modes.addWidget(self._draw_one, 1)
        modes.addWidget(self._draw_three, 1)
        body.addLayout(modes)

        # --- motion & view -----------------------------------------------------
        motion_title = QLabel("Motion & view")
        motion_title.setStyleSheet(
            "color: #E8C766; font-weight: bold; font-size: 16px; background: transparent;"
        )
        body.addWidget(motion_title)

        motion_frame = QFrame()
        motion_frame.setObjectName("panelCard")
        motion_layout = QVBoxLayout(motion_frame)
        motion_layout.setContentsMargins(16, 14, 16, 14)
        motion_layout.setSpacing(12)

        self._reduce_motion = ToggleRow(
            "Reduce motion",
            "Skip card travel and flip animations; the game stays fully playable.",
            reduce_motion,
        )
        motion_layout.addWidget(self._reduce_motion)

        self._show_sidebar = ToggleRow(
            "Show DSA dashboard",
            "Keep the live structure overview beside the board in the Play Workspace.",
            show_sidebar,
        )
        motion_layout.addWidget(self._show_sidebar)

        speed_row = QHBoxLayout()
        speed_label_column = QVBoxLayout()
        speed_title = QLabel("Animation speed")
        speed_title.setStyleSheet("color: #F2EEE2; font-weight: bold; font-size: 14px;")
        speed_hint = QLabel("Scale every cosmetic animation duration.")
        speed_hint.setObjectName("mutedText")
        speed_label_column.addWidget(speed_title)
        speed_label_column.addWidget(speed_hint)
        speed_row.addLayout(speed_label_column, 1)
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(5, 20)
        self._speed_slider.setValue(int(round(10 * speed_multiplier)))
        self._speed_slider.setFixedWidth(240)
        speed_row.addWidget(self._speed_slider)
        self._speed_value = QLabel(f"{speed_multiplier:.1f}×")
        self._speed_value.setStyleSheet("color: #E8C766; font-weight: bold;")
        speed_row.addWidget(self._speed_value)
        self._speed_slider.valueChanged.connect(
            lambda value: self._speed_value.setText(f"{value / 10.0:.1f}×")
        )
        motion_layout.addLayout(speed_row)
        body.addWidget(motion_frame)

        body.addStretch(1)

        # --- actions ------------------------------------------------------------
        actions = QHBoxLayout()
        new_game_button = QPushButton("  Deal a New Game")
        new_game_button.setObjectName("goldButton")
        from PyQt6.QtGui import QIcon

        new_game_button.setIcon(QIcon(icon_pixmap("spade", 18)))
        new_game_button.setMinimumHeight(44)
        new_game_button.clicked.connect(on_new_game)
        actions.addWidget(new_game_button)
        actions.addStretch(1)
        body.addLayout(actions)

        layout.addWidget(body_holder, 1)

    # --- results ----------------------------------------------------------------
    @property
    def draw_count(self) -> int:
        return 3 if self._draw_three.isChecked() else 1

    @property
    def reduce_motion(self) -> bool:
        return self._reduce_motion.checked

    @property
    def show_sidebar(self) -> bool:
        return self._show_sidebar.checked

    @property
    def speed_multiplier(self) -> float:
        return self._speed_slider.value() / 10.0

    def apply(self) -> None:
        """Apply every control to the live game and persist the choices."""
        from PyQt6.QtCore import QSettings

        self._game.set_draw_mode(self.draw_count)
        manager = CardAnimationManager.instance()
        manager.reduce_motion = self.reduce_motion
        manager.speed_multiplier = self.speed_multiplier
        self._on_show_sidebar(self.show_sidebar)
        settings = QSettings("CSC200", "KlondikeSolitairePremium")
        settings.setValue("draw_count", self.draw_count)
        settings.setValue("reduce_motion", self.reduce_motion)
        settings.setValue("show_sidebar", self.show_sidebar)
        settings.setValue("animation_speed", self.speed_multiplier)
