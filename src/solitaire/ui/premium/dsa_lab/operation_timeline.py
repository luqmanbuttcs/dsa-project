"""Operation Timeline: the real chronological tracker event log."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QTableWidgetItem, QVBoxLayout, QWidget

from solitaire.ui.premium.components.common.controls import FilterLabel, make_table
from solitaire.ui.premium.dsa_lab.data_provider import (
    distinct_operations,
    structure_counts,
    timeline_rows,
)
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, SectionTitle

COLUMNS = [
    "Seq",
    "Timestamp",
    "Structure",
    "Operation",
    "Pile",
    "Cards",
    "Context",
    "Outcome",
]


class OperationTimeline(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Operation Timeline — every real recorded event"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.addWidget(FilterLabel("Structure:"))
        self._structure_filter = QComboBox()
        self._structure_filter.addItem("All", "All")
        for label in structure_counts(self._game.tracker):
            self._structure_filter.addItem(label, label)
        self._structure_filter.currentIndexChanged.connect(lambda _index: self.refresh())
        filter_row.addWidget(self._structure_filter)

        filter_row.addWidget(FilterLabel("Operation:"))
        self._operation_filter = QComboBox()
        self._operation_filter.addItem("All", "All")
        self._operation_filter.currentIndexChanged.connect(lambda _index: self.refresh())
        filter_row.addWidget(self._operation_filter)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self._table = make_table(list(COLUMNS))
        # Default row heights on purpose: the real tracker log grows into the
        # hundreds of rows during a session, and per-row ResizeToContents
        # re-measurement on every setItem() would stall the refresh.
        layout.addWidget(self._table, 1)

        self._summary = QLabel("0 events")
        self._summary.setObjectName("mutedText")
        layout.addWidget(self._summary)

    def refresh(self) -> None:
        structure = self._structure_filter.currentData() or "All"
        operation = self._operation_filter.currentData() or "All"

        available_ops = distinct_operations(self._game.tracker)
        current = self._operation_filter.currentText()
        self._operation_filter.blockSignals(True)
        self._operation_filter.clear()
        self._operation_filter.addItem("All", "All")
        for name in available_ops:
            self._operation_filter.addItem(name, name)
        index = self._operation_filter.findText(current)
        if index >= 0:
            self._operation_filter.setCurrentIndex(index)
        self._operation_filter.blockSignals(False)

        rows = timeline_rows(
            self._game.tracker,
            structure_filter=structure,
            action_filter=operation,
        )
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self._table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        self._table.scrollToBottom()
        self._summary.setText(
            f"{len(rows)} events shown — preserved in true chronological order."
        )
