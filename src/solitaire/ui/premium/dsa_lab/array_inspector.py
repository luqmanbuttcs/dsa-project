"""Array / List inspector: the 52-card deck lifecycle visualisation.

Shows the real lifecycle steps recorded by the OperationTracker
(CREATE_DECK → SHUFFLE → POP_FOR_DEAL ×28 → CLEAR_AFTER_DEAL), the actual
deal order as a card strip, and the current deck size.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from solitaire.domain.card import Suit
from solitaire.domain.operations import StructureName
from solitaire.ui.premium.dsa_lab.data_provider import array_report, operation_counts
from solitaire.ui.premium.dsa_lab.widgets import (
    LiveBadge,
    MiniCardChip,
    PileTag,
    SectionTitle,
    StatChip,
    clear_layout,
    card_text,
)

LIFECYCLE_STEPS = [
    ("CREATE_DECK", "Deck creation", "build_standard_deck() fills the list"),
    ("SHUFFLE", "Shuffle", "Fisher–Yates shuffle of the 52 entries"),
    ("POP_FOR_DEAL", "Deal sequence", "pop() one card per tableau slot"),
    ("CLEAR_AFTER_DEAL", "Clear", "the list is emptied after the deal"),
]


class ArrayInspector(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Array / List — deck lifecycle (create → shuffle → deal)"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        intro = QLabel(
            "The standard 52-card deck lives in a Python list. Every lifecycle "
            "step below is a real tracked operation; nothing is simulated."
        )
        intro.setObjectName("panelBody")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # --- lifecycle steps -------------------------------------------------
        steps_frame = QFrame()
        steps_frame.setObjectName("panelCard")
        self._steps_grid = QGridLayout(steps_frame)
        self._steps_grid.setContentsMargins(14, 12, 14, 12)
        self._steps_grid.setHorizontalSpacing(18)
        self._steps_grid.setVerticalSpacing(8)
        layout.addWidget(steps_frame)

        # --- deal order strip --------------------------------------------------
        deal_frame = QFrame()
        deal_frame.setObjectName("panelCard")
        deal_layout = QVBoxLayout(deal_frame)
        deal_layout.setContentsMargins(14, 12, 14, 12)
        deal_layout.setSpacing(8)

        deal_header = QHBoxLayout()
        deal_header.addWidget(SectionTitle("Deal order (real POP_FOR_DEAL sequence)"))
        deal_header.addStretch(1)
        self._deal_tag = PileTag("28 dealt")
        deal_header.addWidget(self._deal_tag)
        deal_layout.addLayout(deal_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(84)
        scroll.setStyleSheet("background: transparent; border: none;")
        strip_holder = QWidget()
        self._deal_strip = QHBoxLayout(strip_holder)
        self._deal_strip.setContentsMargins(0, 0, 0, 0)
        self._deal_strip.setSpacing(3)
        scroll.setWidget(strip_holder)
        deal_layout.addWidget(scroll)
        layout.addWidget(deal_frame, 1)

        # --- remaining stock ----------------------------------------------------
        remaining_frame = QFrame()
        remaining_frame.setObjectName("panelCard")
        remaining_layout = QVBoxLayout(remaining_frame)
        remaining_layout.setContentsMargins(14, 12, 14, 12)
        remaining_layout.setSpacing(8)

        remaining_header = QHBoxLayout()
        remaining_header.addWidget(SectionTitle("Remaining in the stock (FIFO front first)"))
        remaining_header.addStretch(1)
        self._remaining_tag = PileTag("24 of 52")
        remaining_header.addWidget(self._remaining_tag)
        remaining_layout.addLayout(remaining_header)

        self._remaining_caption = QLabel("—")
        self._remaining_caption.setObjectName("mutedText")
        remaining_layout.addWidget(self._remaining_caption)

        remaining_scroll = QScrollArea()
        remaining_scroll.setWidgetResizable(True)
        remaining_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        remaining_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        remaining_scroll.setMaximumHeight(84)
        remaining_scroll.setStyleSheet("background: transparent; border: none;")
        remaining_holder = QWidget()
        self._remaining_strip = QHBoxLayout(remaining_holder)
        self._remaining_strip.setContentsMargins(0, 0, 0, 0)
        self._remaining_strip.setSpacing(3)
        remaining_scroll.setWidget(remaining_holder)
        remaining_layout.addWidget(remaining_scroll)

        suits_row = QHBoxLayout()
        suits_row.setSpacing(16)
        self._suit_stats: dict[Suit, StatChip] = {
            suit: StatChip(suit.name.title(), "0") for suit in Suit
        }
        for suit in Suit:
            suits_row.addWidget(self._suit_stats[suit])
        suits_row.addStretch(1)
        remaining_layout.addLayout(suits_row)
        layout.addWidget(remaining_frame)

        # --- stats row -----------------------------------------------------------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self._create_stat = StatChip("create_deck()", "0")
        self._shuffle_stat = StatChip("shuffle()", "0")
        self._deal_stat = StatChip("pop_for_deal()", "0")
        self._clear_stat = StatChip("clear_after_deal()", "0")
        self._size_stat = StatChip("Deck size now", "—")
        for stat in (
            self._create_stat,
            self._shuffle_stat,
            self._deal_stat,
            self._clear_stat,
            self._size_stat,
        ):
            stats_row.addWidget(stat)
        stats_row.addStretch(1)
        layout.addLayout(stats_row)
        layout.addStretch(1)

    def refresh(self) -> None:
        game = self._game
        report = array_report(game.tracker, game.state.stock.size())
        counts = operation_counts(game.tracker, StructureName.ARRAY_LIST)

        values = {
            "CREATE_DECK": report.create_deck_events,
            "SHUFFLE": report.shuffle_events,
            "POP_FOR_DEAL": report.deal_events,
            "CLEAR_AFTER_DEAL": report.clear_events,
        }
        # Remove any previous step widgets and rebuild the fixed grid pool.
        while self._steps_grid.count():
            item = self._steps_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        for index, (operation, title, blurb) in enumerate(LIFECYCLE_STEPS):
            step = QFrame()
            step.setObjectName("panelCard")
            step_layout = QVBoxLayout(step)
            step_layout.setContentsMargins(12, 10, 12, 10)
            step_layout.setSpacing(3)

            head = QHBoxLayout()
            name_label = QLabel(title)
            name_label.setStyleSheet("color: #E8C766; font-weight: bold; font-size: 13px;")
            head.addWidget(name_label)
            head.addStretch(1)
            count_badge = QLabel(str(values.get(operation, 0)))
            count_badge.setObjectName("countBadge")
            count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_badge.setFixedSize(38, 20)
            head.addWidget(count_badge)
            step_layout.addLayout(head)

            blurb_label = QLabel(blurb)
            blurb_label.setObjectName("mutedText")
            blurb_label.setWordWrap(True)
            step_layout.addWidget(blurb_label)
            self._steps_grid.addWidget(step, 0, index)

        self._create_stat.set_value(str(report.create_deck_events))
        self._shuffle_stat.set_value(str(report.shuffle_events))
        self._deal_stat.set_value(str(report.deal_events))
        self._clear_stat.set_value(str(report.clear_events))
        self._size_stat.set_value(str(report.deck_size_now))
        self._deal_tag.setText(f"{len(report.deal_order)} dealt")

        clear_layout(self._deal_strip)
        for card_id in report.deal_order[:40]:
            self._deal_strip.addWidget(MiniCardChip.tiny(card_id))
        self._deal_strip.addStretch(1)

        # --- remaining stock (live FIFO view of the queue) -----------------------
        stock_cards = game.state.stock.to_list()
        self._remaining_tag.setText(f"{len(stock_cards)} of 52")
        if stock_cards:
            self._remaining_caption.setText(
                "Next draw (front): " + card_text(stock_cards[0].card_id)
                + "   ·   Last in (rear): " + card_text(stock_cards[-1].card_id)
            )
        else:
            self._remaining_caption.setText("The stock is empty.")
        clear_layout(self._remaining_strip)
        for card in stock_cards[:40]:
            self._remaining_strip.addWidget(MiniCardChip.tiny(card.card_id, face_down=True))
        self._remaining_strip.addStretch(1)
        suit_counts = {suit: 0 for suit in Suit}
        for card in stock_cards:
            suit_counts[card.suit] += 1
        for suit in Suit:
            self._suit_stats[suit].set_value(str(suit_counts[suit]))
