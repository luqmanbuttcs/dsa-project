"""Stack inspector: waste, tableau, foundations, undo/redo histories."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.dsa_lab.data_provider import stack_report_for_pile
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, MiniCardChip, SectionTitle, StatChip

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

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Top card:"))
        self._top_slot = QHBoxLayout()
        self._top_slot.addWidget(MiniCardChip(None))
        top_row.addLayout(self._top_slot)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        layout.addWidget(SectionTitle("Real card order (bottom → top)"))
        order_panel = QFrame()
        order_panel.setObjectName("panelCard")
        self._order_strip = QHBoxLayout(order_panel)
        self._order_strip.setContentsMargins(10, 10, 10, 10)
        self._order_strip.setSpacing(6)
        order_scroll = QScrollArea()
        order_scroll.setWidgetResizable(True)
        order_scroll.setFixedHeight(110)
        order_scroll.setWidget(order_panel)
        layout.addWidget(order_scroll)

        layout.addWidget(SectionTitle("Tracked operations on this pile"))
        self._operations_table = QTableWidget(0, 2)
        self._operations_table.setHorizontalHeaderLabels(["Operation", "Count"])
        self._operations_table.horizontalHeader().setStretchLastSection(True)
        self._operations_table.verticalHeader().setVisible(False)
        self._operations_table.setFixedHeight(160)
        layout.addWidget(self._operations_table)
        layout.addStretch(1)

    def refresh(self) -> None:
        pile_id = self._pile_selector.currentData() or "waste"
        report = stack_report_for_pile(self._game, pile_id)
        self._size_stat.set_value(str(report.size))
        self._top_stat.set_value(report.top_card_id or "—")
        self._push_stat.set_value(str(report.operations.get("PUSH", 0)))
        self._pop_stat.set_value(str(report.operations.get("POP", 0)))

        _clear_strip(self._top_slot)
        self._top_slot.addWidget(MiniCardChip(report.top_card_id))
        self._top_slot.addStretch(1)

        _clear_strip(self._order_strip)
        for card_id in report.order_bottom_to_top:
            self._order_strip.addWidget(MiniCardChip(card_id))
        self._order_strip.addStretch(1)

        operations = sorted(report.operations.items())
        self._operations_table.setRowCount(max(1, len(operations)))
        if not operations:
            note = QTableWidgetItem("No tracked operations yet for this pile")
            self._operations_table.setItem(0, 0, note)
            self._operations_table.setItem(0, 1, QTableWidgetItem("0"))
        else:
            for row, (operation, count) in enumerate(operations):
                self._operations_table.setItem(row, 0, QTableWidgetItem(operation))
                self._operations_table.setItem(row, 1, QTableWidgetItem(str(count)))


def _clear_strip(strip_layout) -> None:
    while strip_layout.count():
        item = strip_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def _pretty(pile_id: str) -> str:
    if pile_id == "waste":
        return "Waste"
    if pile_id.startswith("tableau-"):
        return f"Tableau Column {pile_id.rsplit('-', 1)[1]}"
    names = {"h": "Hearts", "d": "Diamonds", "c": "Clubs", "s": "Spades"}
    if pile_id.startswith("foundation-"):
        return f"{names[pile_id.rsplit('-', 1)[1]]} Foundation"
    return {"undo-history": "Undo History", "redo-history": "Redo History"}.get(pile_id, pile_id)
