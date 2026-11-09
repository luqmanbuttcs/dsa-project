"""Fixed right-side premium DSA dashboard for the Play Workspace."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.controllers.game_controller import GameController
from solitaire.ui.premium.dsa_lab.data_provider import latest_operation, structure_counts
from solitaire.ui.premium.theme import DASHBOARD_WIDTH

STRUCTURE_ROWS = [
    ("Array / List", "Deck management"),
    ("Stack", "Waste, tableau, foundations"),
    ("Queue", "Stock (FIFO)"),
    ("Linked List", "Tableau node chains"),
    ("Dictionary", "Card location index"),
]


def _panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("panelCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)
    heading = QLabel(title)
    heading.setObjectName("panelTitle")
    layout.addWidget(heading)
    return frame, layout


def _body(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("panelBody")
    label.setWordWrap(True)
    return label


class DsaDashboard(QScrollArea):
    """Compact live summary of the five data structures and recent play."""

    def __init__(self, game: GameController, on_open_lab, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self.setFixedWidth(DASHBOARD_WIDTH)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("dashboardContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- overview -------------------------------------------------------
        overview_frame, overview_layout = _panel("DSA Overview — Live Structures")
        self._overview_rows: dict[str, QLabel] = {}
        for name, role in STRUCTURE_ROWS:
            row = QHBoxLayout()
            row.setSpacing(8)
            name_label = QLabel(name)
            name_label.setObjectName("panelBody")
            name_label.setStyleSheet("font-weight: bold; color: #E8C766;")
            role_label = QLabel(role)
            role_label.setObjectName("mutedText")
            count_label = QLabel("0")
            count_label.setObjectName("panelBody")
            count_label.setStyleSheet("font-weight: bold; color: #F2EEE2;")
            count_label.setMinimumWidth(34)
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(name_label)
            row.addStretch(1)
            row.addWidget(role_label)
            row.addWidget(count_label)
            self._overview_rows[name] = count_label
            overview_layout.addLayout(row)
        self._overview_note = QLabel(
            "All counters come from the real OperationTracker — nothing is simulated."
        )
        self._overview_note.setObjectName("mutedText")
        self._overview_note.setWordWrap(True)
        overview_layout.addWidget(self._overview_note)
        layout.addWidget(overview_frame)

        # --- latest operation -------------------------------------------------
        latest_frame, latest_layout = _panel("Latest Operation")
        self._latest_body = _body("Deal complete — the table is set.")
        latest_layout.addWidget(self._latest_body)
        layout.addWidget(latest_frame)

        # --- move history -------------------------------------------------------
        history_frame, history_layout = _panel("Recent Player Moves")
        self._history_list = QListWidget()
        self._history_list.setObjectName("historyList")
        self._history_list.setFixedHeight(150)
        history_layout.addWidget(self._history_list)
        layout.addWidget(history_frame)

        # --- progress -----------------------------------------------------------
        from PyQt6.QtWidgets import QProgressBar

        progress_frame, progress_layout = _panel("Game Progress")
        self._progress = QProgressBar()
        self._progress.setObjectName("gameProgress")
        self._progress.setRange(0, 52)
        self._progress.setValue(0)
        self._progress_text = QLabel("0 / 52 cards in Foundations")
        self._progress_text.setObjectName("mutedText")
        progress_layout.addWidget(self._progress)
        progress_layout.addWidget(self._progress_text)
        layout.addWidget(progress_frame)

        layout.addStretch(1)

        self.open_lab_button = QPushButton("  Open DSA Lab")
        self.open_lab_button.setObjectName("goldButton")
        self.open_lab_button.setIcon(_flask_icon())
        self.open_lab_button.setMinimumHeight(42)
        self.open_lab_button.clicked.connect(on_open_lab)
        layout.addWidget(self.open_lab_button)

        self.setWidget(content)
        self.refresh()

    # --- refresh ------------------------------------------------------------------
    def refresh(self) -> None:
        counts = structure_counts(self._game.tracker)
        for name, count_label in self._overview_rows.items():
            count_label.setText(str(counts.get(name, 0)))

        latest = latest_operation(self._game.tracker)
        if latest is not None:
            self._latest_body.setText(
                f"[{latest.structure.value}] {latest.operation}"
                + (f" — {latest.pile_id}" if latest.pile_id else "")
            )
        else:
            self._latest_body.setText("Deal complete — the table is set.")

        self._history_list.clear()
        for event in reversed(self._game.engine.move_history[-8:]):
            QListWidgetItem(event.description, self._history_list)

        in_foundations, _ = self._game.foundation_progress()
        self._progress.setValue(in_foundations)
        self._progress_text.setText(f"{in_foundations} / 52 cards in Foundations")

    def _format_clock(self) -> str:
        minutes, seconds = divmod(self._game.elapsed_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"


def _flask_icon():
    from PyQt6.QtGui import QIcon

    from solitaire.ui.premium.components.common.icons import icon_pixmap

    return QIcon(icon_pixmap("flask", 20))
