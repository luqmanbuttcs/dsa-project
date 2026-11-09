"""DSA Lab overview: a compact academic dashboard of the five structures.

Shows top-level game metrics, a five-structure card grid (custom icon, live
operation count, current size, live preview strip and an Inspect affordance
that jumps to the structure's inspector page) — all read from the real game.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.dsa_lab.data_provider import structure_counts
from solitaire.ui.premium.dsa_lab.widgets import (
    LiveBadge,
    MetricCard,
    MiniCardChip,
    SectionTitle,
)
from solitaire.ui.premium.navigation import LabPage

STRUCTURE_CARDS = [
    (
        "Array / List",
        "Deck Management",
        "array",
        LabPage.ARRAY,
        "#E8C766",
        "Array / List",
        "The 52-card deck is a Python list: create, validate, shuffle, then pop "
        "one card per deal. Cleared after dealing.",
    ),
    (
        "Stack (LIFO)",
        "Waste · Tableau · Foundations · Undo/Redo",
        "stack",
        LabPage.STACK,
        "#7FB5A3",
        "Stack",
        "Custom Stack backed by the doubly linked list; push/pop drive the waste "
        "pile, tableau, foundations and undo/redo history.",
    ),
    (
        "Queue (FIFO)",
        "Stock",
        "queue",
        LabPage.QUEUE,
        "#8FB4E3",
        "Queue",
        "Resizable circular-buffer queue: cards enqueue at the rear on the deal, "
        "dequeue from the front on each draw; recycling re-enqueues.",
    ),
    (
        "Doubly Linked List",
        "Tableau node chains",
        "linkedlist",
        LabPage.LINKED_LIST,
        "#D9A0C0",
        "Linked List",
        "Tableau columns are stacks backed by linked nodes, so a face-up run can "
        "be detached and attached in O(1) without copying cards.",
    ),
    (
        "Dictionary / HashMap",
        "Card location index",
        "dictionary",
        LabPage.DICTIONARY,
        "#C8B37E",
        "Dictionary",
        "A dict maps every card ID to zone, pile, position and face state; "
        "refreshed after every real operation and checked invariants.",
    ),
]

_SIZE_LABELS = {
    "Array / List": lambda game: f"Deck size now: {game.state.stock.size() + game.state.waste.size()} dealt from 52",
    "Stack (LIFO)": lambda game: f"Waste size: {game.state.waste.size()} · top: {_top_or_dash(game)}",
    "Queue (FIFO)": lambda game: f"Stock size: {game.state.stock.size()} · FIFO order live",
    "Doubly Linked List": lambda game: f"7 columns · {sum(c.size() for c in game.state.tableau.values())} nodes",
    "Dictionary / HashMap": lambda game: f"{len(game.state.card_index)} / 52 entries",
}


def _top_or_dash(game) -> str:
    if game.state.waste.is_empty():
        return "—"
    from solitaire.ui.premium.dsa_lab.widgets import card_text

    return card_text(game.state.waste.peek().card_id)


def _preview_cards(game, name: str) -> list[tuple[str | None, bool]]:
    """(card_id, face_down) preview tuples per structure."""
    from solitaire.ui.premium.dsa_lab.widgets import card_text  # noqa: F401

    if name == "Queue (FIFO)":
        return [(card.card_id, False) for card in game.state.stock.to_list()[:5]]
    if name == "Stack (LIFO)":
        return [(card.card_id, False) for card in game.state.waste.to_list()[-5:]]
    if name == "Array / List":
        return [(None, True)] * 5
    if name == "Doubly Linked List":
        cards = game.state.tableau["tableau-1"].cards_bottom_to_top()[-5:]
        return [(card.card_id, False) for card in cards]
    return []


class OverviewPage(QWidget):
    def __init__(self, game, on_inspect=None, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._on_inspect = on_inspect

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = SectionTitle("Data Structure Lab — live state of the real game objects")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        intro = QLabel(
            "Every number below is read from the running game: OperationTracker "
            "records an event only after a real data-structure method executes. "
            "Nothing is simulated. Inspect each structure in depth from its card."
        )
        intro.setObjectName("panelBody")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # --- top-level metrics -------------------------------------------------
        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self._metric_cards: dict[str, MetricCard] = {}
        for caption, icon in (
            ("Moves", "moves"),
            ("Score", "trophy"),
            ("Time", "stopwatch"),
            ("Foundations", "crown"),
            ("Stock", "queue"),
        ):
            card = MetricCard(caption, icon)
            self._metric_cards[caption] = card
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        # --- five structure cards ------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(12)
        self._count_labels: dict[str, QLabel] = {}
        self._size_labels: dict[str, QLabel] = {}
        self._preview_rows: dict[str, QHBoxLayout] = {}
        for index, (name, role, icon_name, page, accent, counts_key, description) in enumerate(
            STRUCTURE_CARDS
        ):
            card = QFrame()
            card.setObjectName("panelCard")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(7)

            title_row = QHBoxLayout()
            icon_chip = QLabel()
            icon_chip.setPixmap(icon_pixmap(icon_name, 20, QColor(accent)))
            icon_chip.setFixedSize(30, 30)
            icon_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_chip.setObjectName("structureIconChip")
            title_row.addWidget(icon_chip)
            title_row.addSpacing(4)

            name_column = QVBoxLayout()
            name_column.setSpacing(0)
            name_label = QLabel(name)
            name_label.setStyleSheet(
                f"color: {accent}; font-weight: bold; font-size: 14px; background: transparent;"
            )
            role_label = QLabel(role)
            role_label.setObjectName("mutedText")
            name_column.addWidget(name_label)
            name_column.addWidget(role_label)
            title_row.addLayout(name_column, 1)

            count_badge = QLabel("0")
            count_badge.setObjectName("countBadge")
            count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_badge.setFixedSize(44, 22)
            self._count_labels[counts_key] = count_badge
            title_row.addWidget(count_badge)
            card_layout.addLayout(title_row)

            body = QLabel(description)
            body.setObjectName("panelBody")
            body.setWordWrap(True)
            card_layout.addWidget(body)

            size_label = QLabel("—")
            size_label.setObjectName("mutedText")
            self._size_labels[name] = size_label
            card_layout.addWidget(size_label)

            preview_row = QHBoxLayout()
            preview_row.setSpacing(3)
            preview_row.addStretch(1)
            self._preview_rows[name] = preview_row
            card_layout.addLayout(preview_row)

            inspect_button = QPushButton("Inspect →")
            inspect_button.setObjectName("darkButton")
            inspect_button.setCursor(Qt.CursorShape.PointingHandCursor)
            if self._on_inspect is not None:
                inspect_button.clicked.connect(
                    lambda _checked=False, page=page: self._on_inspect(page)
                )
            card_layout.addWidget(inspect_button, 0, Qt.AlignmentFlag.AlignRight)

            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch(1)

    def refresh(self) -> None:
        game = self._game
        counts = structure_counts(game.tracker)
        for name, badge in self._count_labels.items():
            badge.setText(str(counts.get(name, 0)))
        for name, label in self._size_labels.items():
            label.setText(_SIZE_LABELS[name](game))

        minutes, seconds = divmod(game.elapsed_seconds, 60)
        in_foundations, _total = game.foundation_progress()
        values = {
            "Moves": str(game.state.move_count),
            "Score": str(game.state.score),
            "Time": f"{minutes:02d}:{seconds:02d}",
            "Foundations": f"{in_foundations} / 52",
            "Stock": f"{game.state.stock.size()} cards",
        }
        for caption, value in values.items():
            self._metric_cards[caption].set_value(value)

        # Rebuild preview strips in place (fixed pool per structure).
        for name, row in self._preview_rows.items():
            while row.count():
                item = row.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
            for card_id, face_down in _preview_cards(game, name):
                row.addWidget(MiniCardChip.tiny(card_id, face_down=face_down))
            row.addStretch(1)
