"""Dictionary inspector: the real card_id -> location index with search."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.controls import FilterLabel, make_table
from solitaire.ui.premium.dsa_lab.data_provider import (
    dictionary_operation_counts,
    dictionary_rows,
)
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, SectionTitle, StatChip

ZONE_LABELS = {
    "stock": "Stock",
    "waste": "Waste",
    "tableau": "Tableau",
    "foundation": "Foundation",
}


class DictionaryInspector(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Dictionary / HashMap — Card Location Index"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        counts_row = QHBoxLayout()
        self._insert_stat = StatChip("INSERT events", "0")
        self._update_stat = StatChip("UPDATE events", "0")
        self._entries_stat = StatChip("Entries", "0")
        for stat in (self._insert_stat, self._update_stat, self._entries_stat):
            counts_row.addWidget(stat)
            counts_row.addStretch(1)
        layout.addLayout(counts_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(FilterLabel("Search:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Card ID, e.g. H-A or 8♥")
        self._search.textChanged.connect(lambda _text: self.refresh())
        filter_row.addWidget(self._search, 1)
        filter_row.addWidget(FilterLabel("Zone:"))
        self._zone_filter = QComboBox()
        self._zone_filter.addItem("All zones", None)
        for zone_value, zone_label in ZONE_LABELS.items():
            self._zone_filter.addItem(zone_label, zone_value)
        self._zone_filter.currentIndexChanged.connect(lambda _index: self.refresh())
        filter_row.addWidget(self._zone_filter)
        layout.addLayout(filter_row)

        self._table = make_table(
            ["Card ID", "Zone", "Pile", "Position", "Face state"]
        )
        layout.addWidget(self._table, 1)

    def refresh(self) -> None:
        counts = dictionary_operation_counts(self._game.tracker)
        self._insert_stat.set_value(str(counts.get("INSERT", 0)))
        self._update_stat.set_value(str(counts.get("UPDATE", 0)))

        query = self._search.text().strip().lower()
        zone = self._zone_filter.currentData()

        rows = dictionary_rows(self._game)
        filtered = []
        for card_id, zone_value, pile_id, position, face in rows:
            if zone is not None and zone_value != zone:
                continue
            if query and query not in card_id.lower() and query not in pile_id.lower():
                continue
            filtered.append((card_id, zone_value, pile_id, position, face))

        self._entries_stat.set_value(str(len(filtered)))
        self._table.setRowCount(len(filtered))
        for row, (card_id, zone_value, pile_id, position, face) in enumerate(filtered):
            self._table.setItem(row, 0, QTableWidgetItem(card_id))
            self._table.setItem(row, 1, QTableWidgetItem(ZONE_LABELS.get(zone_value, zone_value)))
            self._table.setItem(row, 2, QTableWidgetItem(pile_id))
            self._table.setItem(row, 3, QTableWidgetItem(str(position)))
            self._table.setItem(row, 4, QTableWidgetItem(face))
