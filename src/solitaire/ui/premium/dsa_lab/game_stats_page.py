"""Game Stats page: real statistics from the live GameState."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from solitaire.ui.premium.dsa_lab.data_provider import game_stats
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, SectionTitle


class GameStatsPage(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Game Statistics — live values"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(10)
        self._value_labels: dict[str, QLabel] = {}
        for index, key in enumerate(
            [
                "Moves",
                "Score",
                "Time",
                "Draw mode",
                "Stock",
                "Waste",
                "Tableau",
                "Foundations",
                "Status",
            ]
        ):
            frame = QFrame()
            frame.setObjectName("panelCard")
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(12, 10, 12, 10)
            title = QLabel(key)
            title.setObjectName("panelTitle")
            value = QLabel("—")
            value.setStyleSheet("color: #F2EEE2; font-size: 15px; font-weight: bold; background: transparent;")
            value.setWordWrap(True)
            frame_layout.addWidget(title)
            frame_layout.addWidget(value)
            self._value_labels[key] = value
            grid.addWidget(frame, index // 3, index % 3)
        layout.addLayout(grid)

        progress_title = QLabel("Foundation progress")
        progress_title.setObjectName("panelTitle")
        layout.addWidget(progress_title)
        self._progress = QProgressBar()
        self._progress.setObjectName("gameProgress")
        self._progress.setRange(0, 52)
        layout.addWidget(self._progress)
        self._progress_text = QLabel("0 / 52 cards in Foundations")
        self._progress_text.setObjectName("mutedText")
        layout.addWidget(self._progress_text)
        layout.addStretch(1)

    def refresh(self) -> None:
        stats = game_stats(self._game)
        for key, value in stats.items():
            if key in self._value_labels:
                self._value_labels[key].setText(value)
        in_foundations, _total = self._game.foundation_progress()
        self._progress.setValue(in_foundations)
        self._progress_text.setText(f"{in_foundations} / 52 cards in Foundations")
