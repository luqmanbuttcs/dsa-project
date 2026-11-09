"""Array / List inspector: deck creation, shuffle, deal sequence and clear."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from solitaire.ui.premium.dsa_lab.data_provider import array_report
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, MiniCardChip, SectionTitle, StatChip


class ArrayInspector(QWidget):
    """Shows the real lifecycle of the Array/List-backed deck."""

    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = SectionTitle("Array / List — Deck Management")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        stats_row = QHBoxLayout()
        self._create_stat = StatChip("CREATE_DECK events", "0")
        self._shuffle_stat = StatChip("SHUFFLE events", "0")
        self._deal_stat = StatChip("POP_FOR_DEAL events", "0")
        self._clear_stat = StatChip("CLEAR_AFTER_DEAL events", "0")
        self._deck_now = StatChip("Active deck size", "0")
        for stat in (
            self._create_stat,
            self._shuffle_stat,
            self._deal_stat,
            self._clear_stat,
            self._deck_now,
        ):
            stats_row.addWidget(stat)
            stats_row.addStretch(1)
        layout.addLayout(stats_row)

        explanation = QLabel(
            "The deck list is created with all 52 suit/rank combinations, validated, "
            "shuffled in place, then popped 28 times to deal the tableau (sizes 1–7). "
            "The remaining 24 cards are enqueued into the stock Queue and the list is "
            "cleared — after dealing the active deck is intentionally empty."
        )
        explanation.setObjectName("panelBody")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        deal_title = SectionTitle("Deal sequence (pop order from the shuffled list)")
        layout.addWidget(deal_title)

        deal_panel = QFrame()
        deal_panel.setObjectName("panelCard")
        self._deal_strip = QHBoxLayout(deal_panel)
        self._deal_strip.setContentsMargins(10, 10, 10, 10)
        self._deal_strip.setSpacing(6)
        deal_scroll = QScrollArea()
        deal_scroll.setWidgetResizable(True)
        deal_scroll.setFixedHeight(110)
        deal_scroll.setWidget(deal_panel)
        layout.addWidget(deal_scroll)

        layout.addStretch(1)
        outer.addWidget(content)
        self._deal_panel = deal_panel

    def refresh(self) -> None:
        report = array_report(self._game.tracker, deck_size_now=0)
        self._create_stat.set_value(str(report.create_deck_events))
        self._shuffle_stat.set_value(str(report.shuffle_events))
        self._deal_stat.set_value(str(report.deal_events))
        self._clear_stat.set_value(str(report.clear_events))
        self._deck_now.set_value(str(report.deck_size_now) + "  (after dealing)")

        while self._deal_strip.count():
            item = self._deal_strip.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for card_id in report.deal_order:
            self._deal_strip.addWidget(MiniCardChip(card_id))
        self._deal_strip.addStretch(1)
