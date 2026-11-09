"""Premium move log with success icons, card notation and clock stamps."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.controllers.game_controller import GameController, pretty_pile


def describe_move(event) -> str:
    """Compact readable notation, e.g. '2♦ to Column 6'."""
    description = event.description
    for pile_id in (event.source_pile, event.destination_pile):
        if pile_id:
            description = description.replace(pile_id, pretty_pile(pile_id))
    return description


class MoveLogPanel(QFrame):
    """Scrolling chronological log of real player moves."""

    def __init__(self, game: GameController, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self.setObjectName("panelCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap("list", 18))
        title = QLabel("Move Log")
        title.setObjectName("panelTitle")
        title_row.addWidget(icon_label)
        title_row.addSpacing(6)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        self._list = QListWidget()
        self._list.setObjectName("moveLog")
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self._list)

    def add_move(self, event) -> None:
        minutes, seconds = divmod(self._game.elapsed_seconds, 60)
        item = QListWidgetItem(describe_move(event))
        icon_name = "check" if event.action_type != "MOVE_REJECTED" else "warning"
        item.setIcon(QIcon(icon_pixmap(icon_name, 16)))
        item.setData(Qt.ItemDataRole.UserRole, f"{minutes:02d}:{seconds:02d}")
        item.setToolTip(event.action_type)
        self._list.addItem(item)
        self._list.scrollToBottom()

    def clear_log(self) -> None:
        self._list.clear()

    def all_entries(self) -> list[tuple[str, str]]:
        return [
            (self._list.item(index).text(), self._list.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(self._list.count())
        ]
