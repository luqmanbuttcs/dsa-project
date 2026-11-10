"""Game Stats page: real statistics from the live GameState.

Presented in the same MetricCard language as the Overview page — icon,
muted caption, prominent value — so both lab pages read as one system.
"""

from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from solitaire.ui.premium.dsa_lab.data_provider import game_stats
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, MetricCard, SectionTitle

STAT_CARDS = [
    ("Moves", "moves"),
    ("Score", "trophy"),
    ("Time", "stopwatch"),
    ("Draw mode", "list"),
    ("Stock", "queue"),
    ("Waste", "stack"),
    ("Tableau", "linkedlist"),
    ("Foundations", "crown"),
    ("Status", "check"),
]


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
        for index, (key, icon_name) in enumerate(STAT_CARDS):
            card = MetricCard(key, icon_name)
            self._value_labels[key] = card.value_label
            grid.addWidget(card, index // 3, index % 3)
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
