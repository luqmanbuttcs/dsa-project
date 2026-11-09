"""Stack inspector: waste, tableau, foundations, undo/redo histories.

The selected pile is drawn bottom-to-top with a gold TOP badge on the top
card, live size/top stats and the tracked push/pop operations for the pile.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.dsa_lab.data_provider import stack_report_for_pile
from solitaire.ui.premium.dsa_lab.widgets import (
    LiveBadge,
    MiniCardChip,
    PileTag,
    SectionTitle,
    StatChip,
)

PILES = [
    "waste",
    *[f"tableau-{index}" for index in range(1, 8)],
    "foundation-h",
    "foundation-d",
    "foundation-c",
    "foundation-s",
    "undo-history",
    "redo-history",
]


class StackInspector(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Stack (LIFO) — every pile that behaves like a stack"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Pile:"))
        self._pile_selector = QComboBox()
        for pile_id in PILES:
            self._pile_selector.addItem(_pretty(pile_id), pile_id)
        self._pile_selector.currentIndexChanged.connect(lambda _index: self.refresh())
        selector_row.addWidget(self._pile_selector)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)

        stats_row = QHBoxLayout()
        self._size_stat = StatChip("Size", "0")
        self._top_stat = StatChip("Top card", "—")
        self._push_stat = StatChip("push() events", "0")
        self._pop_stat = StatChip("pop() events", "0")
        for stat in (self._size_stat, self._top_stat, self._push_stat, self._pop_stat):
            stats_row.addWidget(stat)
            stats_row.addStretch(1)
        layout.addLayout(stats_row)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        # Vertical bottom→top stack view.
        stack_column = QVBoxLayout()
        stack_column.addWidget(SectionTitle("Card order (bottom → top)"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        stack_holder = QWidget()
        holder_layout = QVBoxLayout(stack_holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.setSpacing(4)
        self._top_tag_row = QHBoxLayout()
        self._top_tag_row.addStretch(1)
        self._top_tag = PileTag("TOP")
        self._top_tag_row.addWidget(self._top_tag)
        holder_layout.addLayout(self._top_tag_row)
        self._stack_list = QVBoxLayout()
        self._stack_list.setSpacing(3)
        holder_layout.addLayout(self._stack_list)
        holder_layout.addStretch(1)
        scroll.setWidget(stack_holder)
        stack_column.addWidget(scroll, 1)
        columns.addLayout(stack_column, 3)

        # Operations table.
        operations_column = QVBoxLayout()
        operations_column.addWidget(SectionTitle("Tracked operations on this pile"))
        self._operations_table = QTableWidget(0, 2)
        self._operations_table.setHorizontalHeaderLabels(["Operation", "Count"])
        self._operations_table.horizontalHeader().setStretchLastSection(True)
        self._operations_table.verticalHeader().setVisible(False)
        self._operations_table.horizontalHeader().setStyleSheet(
            "color: #E8C766; font-weight: bold; background: #13253D;"
        )
        operations_column.addWidget(self._operations_table, 1)
        columns.addLayout(operations_column, 2)

        layout.addLayout(columns, 1)

    def refresh(self) -> None:
        pile_id = self._pile_selector.currentData() or "waste"
        report = stack_report_for_pile(self._game, pile_id)
        self._size_stat.set_value(str(report.size))
        self._top_stat.set_value(report.top_card_id or "—")
        self._push_stat.set_value(str(report.operations.get("PUSH", 0)))
        self._pop_stat.set_value(str(report.operations.get("POP", 0)))

        self._clear_list()
        cards = list(report.order_bottom_to_top)
        for position, card_id in enumerate(reversed(cards)):  # top first visually
            row = QHBoxLayout()
            row.setSpacing(6)
            if position == 0 and report.top_card_id is not None:
                chip = MiniCardChip(card_id)
                chip.setStyleSheet(
                    "QFrame { border: 2px solid #E0B84E; border-radius: 6px; }"
                )
                row.addWidget(chip)
                row.addWidget(PileTag("TOP"), 0, Qt.AlignmentFlag.AlignVCenter)
            else:
                row.addWidget(MiniCardChip(card_id))
            row.addStretch(1)
            holder_widget = QWidget()
            holder_widget.setLayout(row)
            self._stack_list.addWidget(holder_widget)

        if not cards:
            empty = QLabel("This pile is empty right now.")
            empty.setObjectName("mutedText")
            self._stack_list.addWidget(empty)

        self._top_tag.setVisible(report.top_card_id is not None)

        operations = sorted(report.operations.items())
        self._operations_table.setRowCount(max(1, len(operations)))
        if not operations:
            empty_item = QTableWidgetItem("No tracked operations yet for this pile")
            empty_item.setToolTip("Push/pop events recorded by the OperationTracker will appear here.")
            self._operations_table.setItem(0, 0, empty_item)
            self._operations_table.setItem(0, 1, QTableWidgetItem("0"))
            # Give the placeholder row enough height for the full sentence.
            self._operations_table.setRowHeight(0, 40)
        else:
            for row, (operation, count) in enumerate(operations):
                self._operations_table.setItem(row, 0, QTableWidgetItem(operation))
                self._operations_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self._operations_table.setRowHeight(row, 28)

    def _clear_list(self) -> None:
        while self._stack_list.count():
            item = self._stack_list.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                pass


def _pretty(pile_id: str) -> str:
    if pile_id == "waste":
        return "Waste"
    if pile_id.startswith("tableau-"):
        return f"Tableau Column {pile_id.rsplit('-', 1)[1]}"
    names = {"h": "Hearts", "d": "Diamonds", "c": "Clubs", "s": "Spades"}
    if pile_id.startswith("foundation-"):
        return f"{names[pile_id.rsplit('-', 1)[1]]} Foundation"
    return {"undo-history": "Undo History", "redo-history": "Redo History"}.get(pile_id, pile_id)
