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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solitaire.domain.card import Suit
from solitaire.ui.premium.components.common.controls import make_table, strip_scroll
from solitaire.ui.premium.dsa_lab.data_provider import (
    recent_stack_events,
    stack_pile_composition,
    stack_report_for_pile,
)
from solitaire.ui.premium.dsa_lab.widgets import (
    LiveBadge,
    MiniCardChip,
    PileTag,
    SectionTitle,
    StatChip,
    cards_brief,
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
        scroll, holder_layout = strip_scroll()
        self._stack_list = QVBoxLayout()
        self._stack_list.setSpacing(3)
        holder_layout.addLayout(self._stack_list)
        holder_layout.addStretch(1)
        stack_column.addWidget(scroll, 3)

        # Recent real tracker events for the selected pile (fills the lower
        # left with live data, mirroring the Queue page's operation table).
        stack_column.addSpacing(4)
        stack_column.addWidget(SectionTitle("Recent events on this pile"))
        self._events_table = make_table(["Seq", "Operation", "Card", "Context"])
        stack_column.addWidget(self._events_table, 2)
        columns.addLayout(stack_column, 3)

        # Operations table.
        operations_column = QVBoxLayout()
        operations_column.addWidget(SectionTitle("Tracked operations on this pile"))
        self._operations_table = make_table(["Operation", "Count"])
        operations_column.addWidget(self._operations_table, 0)

        # Real suit/face composition of the selected pile — mirrors the Array
        # page's suit chips and keeps the right column from ending in a void.
        operations_column.addSpacing(8)
        operations_column.addWidget(SectionTitle("Pile composition"))
        composition_panel = QFrame()
        composition_panel.setObjectName("panelCard")
        composition_layout = QVBoxLayout(composition_panel)
        composition_layout.setContentsMargins(12, 10, 12, 10)
        composition_layout.setSpacing(8)
        suits_row = QHBoxLayout()
        self._composition_suits: dict[Suit, StatChip] = {
            suit: StatChip(suit.name.title(), "0") for suit in Suit
        }
        for suit in Suit:
            suits_row.addWidget(self._composition_suits[suit])
        suits_row.addStretch(1)
        composition_layout.addLayout(suits_row)
        faces_row = QHBoxLayout()
        self._face_up_stat = StatChip("Face up", "0")
        self._face_down_stat = StatChip("Face down", "0")
        faces_row.addWidget(self._face_up_stat)
        faces_row.addWidget(self._face_down_stat)
        faces_row.addStretch(1)
        composition_layout.addLayout(faces_row)
        self._composition_hint = QLabel("History piles hold move snapshots, not cards.")
        self._composition_hint.setObjectName("mutedText")
        self._composition_hint.setWordWrap(True)
        self._composition_hint.setVisible(False)
        composition_layout.addWidget(self._composition_hint)
        operations_column.addWidget(composition_panel)
        operations_column.addStretch(1)

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
                chip = MiniCardChip(card_id)
                row.addWidget(chip)
            chip.setFixedSize(64, 88)
            for label in chip.findChildren(QLabel):
                font = label.font()
                font.setPixelSize(21)
                label.setFont(font)
            row.addStretch(1)
            holder_widget = QWidget()
            holder_widget.setLayout(row)
            self._stack_list.addWidget(holder_widget)

        if not cards:
            empty = QLabel("This pile is empty right now.")
            empty.setObjectName("mutedText")
            self._stack_list.addWidget(empty)

        events = recent_stack_events(self._game.tracker, pile_id)
        self._events_table.setRowCount(max(1, len(events)))
        if not events:
            self._events_table.setItem(0, 0, QTableWidgetItem("No stack events yet for this pile"))
            self._events_table.setItem(0, 1, QTableWidgetItem("—"))
            self._events_table.setItem(0, 2, QTableWidgetItem("—"))
            self._events_table.setItem(0, 3, QTableWidgetItem("—"))
            self._events_table.setRowHeight(0, 40)
        else:
            for row, event in enumerate(events):
                self._events_table.setItem(row, 0, QTableWidgetItem(str(event.sequence)))
                self._events_table.setItem(row, 1, QTableWidgetItem(event.operation))
                self._events_table.setItem(row, 2, QTableWidgetItem(cards_brief(event.card_ids)))
                self._events_table.setItem(row, 3, QTableWidgetItem(event.context or "—"))
                self._events_table.setRowHeight(row, 26)

        composition = stack_pile_composition(self._game, pile_id)
        if composition is None:
            for stat in self._composition_suits.values():
                stat.set_value("0")
            self._face_up_stat.set_value("0")
            self._face_down_stat.set_value("0")
            self._composition_hint.setVisible(True)
        else:
            for suit in Suit:
                self._composition_suits[suit].set_value(str(composition.suit_counts[suit]))
            self._face_up_stat.set_value(str(composition.face_up))
            self._face_down_stat.set_value(str(composition.face_down))
            self._composition_hint.setVisible(False)

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
