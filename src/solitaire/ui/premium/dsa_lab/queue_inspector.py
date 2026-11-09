"""Queue inspector: the FIFO stock — front, rear, order, operations."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.dsa_lab.data_provider import queue_report
from solitaire.ui.premium.dsa_lab.widgets import LiveBadge, MiniCardChip, SectionTitle, StatChip


def _clear_strip(strip_layout) -> None:
    while strip_layout.count():
        item = strip_layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


class QueueInspector(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Queue (FIFO) — Stock"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        stats_row = QHBoxLayout()
        self._size_stat = StatChip("Stock size", "0")
        self._front_stat = StatChip("Front (next draw)", "—")
        self._rear_stat = StatChip("Rear (last in)", "—")
        for stat in (self._size_stat, self._front_stat, self._rear_stat):
            stats_row.addWidget(stat)
            stats_row.addStretch(1)
        layout.addLayout(stats_row)

        ops_row = QHBoxLayout()
        self._enqueue_stat = StatChip("enqueue() events", "0")
        self._dequeue_stat = StatChip("dequeue() events", "0")
        self._recycle_stat = StatChip("Waste recycles", "0")
        for stat in (self._enqueue_stat, self._dequeue_stat, self._recycle_stat):
            ops_row.addWidget(stat)
            ops_row.addStretch(1)
        layout.addLayout(ops_row)

        explanation = QLabel(
            "The stock is a circular-buffer queue: cards enqueue at the rear during the "
            "deal (and when waste is recycled), and dequeue from the front on every draw. "
            "The strip below shows the true FIFO order, front first."
        )
        explanation.setObjectName("panelBody")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        layout.addWidget(SectionTitle("FIFO order (front → rear)"))
        order_panel = QFrame()
        order_panel.setObjectName("panelCard")
        self._order_strip = QHBoxLayout(order_panel)
        self._order_strip.setContentsMargins(10, 10, 10, 10)
        self._order_strip.setSpacing(4)
        order_scroll = QScrollArea()
        order_scroll.setWidgetResizable(True)
        order_scroll.setFixedHeight(120)
        order_scroll.setWidget(order_panel)
        layout.addWidget(order_scroll)
        layout.addStretch(1)

        self._order_panel = order_panel

    def refresh(self) -> None:
        report = queue_report(self._game)
        self._size_stat.set_value(str(report.size))
        self._front_stat.set_value(report.front_card_id or "—")
        self._rear_stat.set_value(report.rear_card_id or "—")
        self._enqueue_stat.set_value(str(report.enqueue_count))
        self._dequeue_stat.set_value(str(report.dequeue_count))
        self._recycle_stat.set_value(str(report.recycle_events))

        _clear_strip(self._order_strip)

        if report.fifo_order:
            self._order_strip.addWidget(QLabel("Front →"))
            self._order_strip.addWidget(MiniCardChip(report.fifo_order[0]))
            for card_id in report.fifo_order[1:-1]:
                self._order_strip.addWidget(MiniCardChip(card_id, face_down=True))
            if len(report.fifo_order) > 1:
                self._order_strip.addWidget(MiniCardChip(report.fifo_order[-1]))
                self._order_strip.addWidget(QLabel("← Rear"))
        else:
            empty = QLabel("The stock is empty.")
            empty.setObjectName("mutedText")
            self._order_strip.addWidget(empty)
        self._order_strip.addStretch(1)
