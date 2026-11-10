"""Doubly Linked List inspector: node diagram per tableau column."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.controls import FilterLabel, make_table
from solitaire.ui.premium.dsa_lab.data_provider import (
    linked_list_report,
    recent_linked_list_events,
)
from solitaire.ui.premium.dsa_lab.widgets import (
    LiveBadge,
    SectionTitle,
    StatChip,
    card_color,
    cards_brief,
)


class NodeDiagram(QWidget):
    """Paints head → node ↔ node → … → tail with previous/next arrows."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._nodes = ()
        self._head = None
        self._tail = None
        self.setMinimumHeight(260)
        from PyQt6.QtWidgets import QSizePolicy

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, nodes, head_card_id, tail_card_id) -> None:
        self._nodes = nodes
        self._head = head_card_id
        self._tail = tail_card_id
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(10, 22, 38))
        painter.setPen(QPen(QColor(36, 57, 90), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 10, 10)

        font = QFont("DejaVu Serif")
        font.setPixelSize(15)
        font.setBold(True)
        painter.setFont(font)

        if not self._nodes:
            painter.setPen(QPen(QColor(159, 176, 198)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "This column is empty — no nodes.")
            return

        margin = 26.0
        available = max(120.0, self.width() - 2 * margin)
        node_w = min(64.0, available / max(1, len(self._nodes)) - 18.0)
        node_h = 46.0
        gap = (available - node_w * len(self._nodes)) / max(1, len(self._nodes) - 1) if len(self._nodes) > 1 else 0
        y = self.height() / 2.0 - node_h / 2.0 + 6.0

        # Head / tail captions.
        painter.setPen(QPen(QColor(232, 199, 102), 1))
        small = QFont("DejaVu Sans")
        small.setPixelSize(11)
        small.setBold(True)
        painter.setFont(small)

        first_x = margin
        last_x = margin + (node_w + gap) * (len(self._nodes) - 1)
        painter.drawText(QRectF(first_x - 20, y - 26, 110, 18), Qt.AlignmentFlag.AlignLeft, "HEAD")
        painter.drawText(QRectF(last_x + node_w - 90, y - 26, 110, 18), Qt.AlignmentFlag.AlignRight, "TAIL")

        for index, node in enumerate(self._nodes):
            x = margin + (node_w + gap) * index
            rect = QRectF(x, y, node_w, node_h)

            path = QPainterPath()
            path.addRoundedRect(rect, 7, 7)
            is_edge = node.card_id in (self._head, self._tail)
            border = QColor(240, 199, 94) if is_edge else QColor(196, 181, 142)
            painter.fillPath(path, QColor(253, 249, 238))
            painter.setPen(QPen(border, 2.0 if is_edge else 1.2))
            painter.drawPath(path)

            painter.setPen(QPen(QColor(card_color(node.card_id))))
            painter.setFont(font)
            from solitaire.ui.premium.dsa_lab.widgets import card_text

            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, card_text(node.card_id))

            # next pointer arrow to the following node
            if node.has_next and index < len(self._nodes) - 1:
                start = QPointF(rect.right(), rect.center().y() - 6)
                end = QPointF(rect.right() + gap, rect.center().y() - 6)
                painter.setPen(QPen(QColor(55, 185, 110), 1.8))
                painter.drawLine(start, end)
                painter.setBrush(QColor(55, 185, 110))
                painter.drawPolygon(
                    [end, QPointF(end.x() - 6, end.y() - 4), QPointF(end.x() - 6, end.y() + 4)]
                )
            # previous pointer arrow back to the preceding node
            if node.has_previous and index > 0:
                start = QPointF(rect.left(), rect.center().y() + 6)
                end = QPointF(rect.left() - gap, rect.center().y() + 6)
                painter.setPen(QPen(QColor(96, 150, 220), 1.8))
                painter.drawLine(start, end)
                painter.setBrush(QColor(96, 150, 220))
                painter.drawPolygon(
                    [end, QPointF(end.x() + 6, end.y() - 4), QPointF(end.x() + 6, end.y() + 4)]
                )


class LinkedListInspector(QWidget):
    def __init__(self, game, parent=None) -> None:
        super().__init__(parent)
        self._game = game

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(SectionTitle("Doubly Linked List — Tableau node chains"))
        header.addStretch(1)
        header.addWidget(LiveBadge())
        layout.addLayout(header)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)
        selector_label = FilterLabel("Tableau column:")
        selector_row.addWidget(selector_label)
        self._column_selector = QComboBox()
        for index in range(1, 8):
            self._column_selector.addItem(f"Column {index}", f"tableau-{index}")
        self._column_selector.currentIndexChanged.connect(lambda _index: self.refresh())
        selector_row.addWidget(self._column_selector)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(24)
        stats_grid.setVerticalSpacing(6)
        self._head_stat = StatChip("Head", "—")
        self._tail_stat = StatChip("Tail", "—")
        self._append_stat = StatChip("APPEND_NODE", "0")
        self._remove_stat = StatChip("REMOVE_TOP_NODE", "0")
        self._detach_stat = StatChip("DETACH_RUN", "0")
        self._attach_stat = StatChip("ATTACH_RUN", "0")
        for position, stat in enumerate(
            (
                self._head_stat,
                self._tail_stat,
                self._append_stat,
                self._remove_stat,
                self._detach_stat,
                self._attach_stat,
            )
        ):
            # 2×3 grid: every label gets a third of the width, so even the
            # longest operation name never wraps mid-value.
            stats_grid.addWidget(stat, position // 3, position % 3)
        layout.addLayout(stats_grid)

        explanation = QLabel(
            "Each tableau column is a Stack backed by this doubly linked list. Detaching a "
            "face-up run relinks boundary nodes (DETACH_RUN); attaching splices the run after "
            "the destination tail (ATTACH_RUN) without copying any Card object."
        )
        explanation.setObjectName("panelBody")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        self._diagram = NodeDiagram()
        # A 46 px chain inside a page-tall frame reads as dead space; cap the
        # diagram and spend the remaining height on real per-column events.
        self._diagram.setMaximumHeight(280)
        layout.addWidget(self._diagram)

        layout.addSpacing(4)
        layout.addWidget(SectionTitle("Recent events on this column"))
        self._events_table = make_table(["Seq", "Operation", "Card(s)", "Context"])
        self._events_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self._events_table, 1)

        self._valid_label = QLabel("Chain integrity: valid")
        self._valid_label.setObjectName("mutedText")
        layout.addWidget(self._valid_label)

        # Land on the deepest column so the diagram shows a real chain instead
        # of a single-node column (real pile sizes, never hard-coded).
        deepest = max(
            range(1, 8), key=lambda i: self._game.state.tableau[f"tableau-{i}"].size()
        )
        self._column_selector.setCurrentIndex(deepest - 1)

    def refresh(self) -> None:
        column_id = self._column_selector.currentData() or "tableau-1"
        report = linked_list_report(self._game, column_id)
        self._head_stat.set_value(report.head_card_id or "—")
        self._tail_stat.set_value(report.tail_card_id or "—")
        self._append_stat.set_value(str(report.append_count))
        self._remove_stat.set_value(str(report.remove_count))
        self._detach_stat.set_value(str(report.detach_count))
        self._attach_stat.set_value(str(report.attach_count))
        self._diagram.set_data(report.nodes, report.head_card_id, report.tail_card_id)
        self._valid_label.setText(
            "Chain integrity: valid" if report.valid else "Chain integrity: BROKEN"
        )

        events = recent_linked_list_events(self._game.tracker, column_id)
        self._events_table.setRowCount(max(1, len(events)))
        if not events:
            self._events_table.setItem(0, 0, QTableWidgetItem("No linked-list events yet for this column"))
            self._events_table.setItem(0, 1, QTableWidgetItem("—"))
            self._events_table.setItem(0, 2, QTableWidgetItem("—"))
            self._events_table.setItem(0, 3, QTableWidgetItem("—"))
        else:
            for row, event in enumerate(events):
                self._events_table.setItem(row, 0, QTableWidgetItem(str(event.sequence)))
                self._events_table.setItem(row, 1, QTableWidgetItem(event.operation))
                self._events_table.setItem(row, 2, QTableWidgetItem(cards_brief(event.card_ids)))
                self._events_table.setItem(row, 3, QTableWidgetItem(event.context or "—"))
