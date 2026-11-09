"""DSA Lab overview page: the five structures and where they live."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from solitaire.ui.premium.dsa_lab.data_provider import structure_counts
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, SectionTitle, StatChip

STRUCTURE_CARDS = [
    (
        "Array / List",
        "Deck Management",
        "The standard 52-card deck is a Python list: create, validate, shuffle, "
        "then pop one card per deal. The list is cleared after dealing.",
    ),
    (
        "Stack (LIFO)",
        "Waste, Tableau, Foundations, Undo / Redo",
        "Custom Stack backed by the doubly linked list. Push and pop drive the "
        "waste pile, tableau columns, foundation piles and undo/redo history.",
    ),
    (
        "Queue (FIFO)",
        "Stock",
        "Resizable circular-buffer queue. Cards enqueue at the rear on the deal "
        "and dequeue from the front on each draw; recycling re-enqueues waste.",
    ),
    (
        "Doubly Linked List",
        "Tableau node chains",
        "Tableau columns are stacks backed by linked nodes, so a face-up run "
        "can be detached and attached in O(1) without copying cards.",
    ),
    (
        "Dictionary / HashMap",
        "Card location index",
        "A dict maps every card ID to its zone, pile, position and face state. "
        "It is refreshed after every real operation and validated invariants.",
    ),
]


class OverviewPage(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout_header()
        title = SectionTitle("Data Structure Lab — live state of the real game objects")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        intro = QLabel(
            "Every number below is read from the running game: OperationTracker "
            "records an event only after a real data-structure method executes. "
            "Nothing is simulated. Open a tab above to inspect each structure in depth."
        )
        intro.setObjectName("panelBody")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        grid = QGridLayout()
        grid.setSpacing(12)
        self._count_labels: dict[str, StatChip] = {}
        for index, (name, role, description) in enumerate(STRUCTURE_CARDS):
            card = QFrame()
            card.setObjectName("panelCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)
            title_row = QHBoxLayout_header()
            name_label = QLabel(name)
            name_label.setStyleSheet("color: #E8C766; font-weight: bold; font-size: 15px;")
            title_row.addWidget(name_label)
            title_row.addStretch(1)
            count = StatChip("Tracked operations", "0")
            self._count_labels[name] = count
            title_row.addWidget(count)
            card_layout.addLayout(title_row)
            role_label = QLabel(f"Role: {role}")
            role_label.setObjectName("mutedText")
            card_layout.addWidget(role_label)
            body = QLabel(description)
            body.setObjectName("panelBody")
            body.setWordWrap(True)
            card_layout.addWidget(body)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch(1)

    def refresh(self) -> None:
        counts = structure_counts(self._game.tracker)
        for name, label in self._count_labels.items():
            label.set_value(str(counts.get(name, 0)))


def QHBoxLayout_header():
    from PyQt6.QtWidgets import QHBoxLayout

    return QHBoxLayout()
