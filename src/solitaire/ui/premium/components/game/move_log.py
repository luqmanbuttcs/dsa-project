"""Premium move log with success icons, card notation and clock stamps."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.controllers.game_controller import GameController, describe_move

__all__ = ["MoveLogPanel", "describe_move"]


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
        self._count_label = QLabel("0 moves")
        self._count_label.setObjectName("mutedText")
        title_row.addWidget(self._count_label)
        layout.addLayout(title_row)

        self._list = QListWidget()
        self._list.setObjectName("moveLog")
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self._list)

    def add_move(self, event) -> None:
        minutes, seconds = divmod(self._game.elapsed_seconds, 60)
        stamp = f"{minutes:02d}:{seconds:02d}"
        rejected = event.action_type == "MOVE_REJECTED"
        icon_name = "warning" if rejected else "check"

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, stamp)
        item.setToolTip(f"{event.action_type} · {stamp}")
        row = QLabel(f"<b style='color:#8FA0B8; font-family:DejaVu Sans'>{stamp}</b>"
                     f"&nbsp;&nbsp;{describe_move(event)}")
        row.setObjectName("moveLogRow")
        row.setContentsMargins(2, 0, 2, 0)
        row.setStyleSheet("color: #F2EEE2; background: transparent;")
        row.setFixedHeight(24)
        from PyQt6.QtCore import QSize

        item.setSizeHint(QSize(200, 26))
        item.setIcon(QIcon(icon_pixmap(icon_name, 15)))
        self._list.addItem(item)
        self._list.setItemWidget(item, row)
        self._list.scrollToBottom()

        self._count_label.setText(f"{self._list.count()} moves")

    def clear_log(self) -> None:
        self._list.clear()
        self._count_label.setText("0 moves")
