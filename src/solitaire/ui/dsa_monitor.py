"""Live DSA monitor built from the game's actual OperationTracker events."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QListWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from solitaire.domain.card import Suit
from solitaire.domain.game_engine import GameEngine
from solitaire.domain.operations import OperationEvent, StructureName


class DSAMonitorPanel(QWidget):
    """Readable overview, structure details, and low-level operation history."""

    STRUCTURES = (
        (StructureName.ARRAY_LIST, "Temporary deck creation, shuffle, and deal"),
        (StructureName.STACK, "Tableau, Waste, Foundations, and history piles"),
        (StructureName.QUEUE, "FIFO stock draw and recycle"),
        (StructureName.LINKED_LIST, "Tableau node chains and run transfers"),
        (StructureName.DICTIONARY, "Card ID to live zone and position lookup"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dsa-monitor-panel")
        self.setMinimumWidth(300)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        intro = QLabel(
            "Live counts come from completed data-structure operations, "
            "not from animation or estimated counters."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #B9C7D3; font-size: 11px;")
        root.addWidget(intro)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("dsa-monitor-tabs")
        root.addWidget(self.tabs, 1)

        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(4, 8, 4, 4)
        self.count_table = QTableWidget(5, 3)
        self.count_table.setObjectName("dsa-count-table")
        self.count_table.setHorizontalHeaderLabels(
            ["Structure", "Current", "Operations"]
        )
        self.count_table.verticalHeader().setVisible(False)
        self.count_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.count_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.count_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.count_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.count_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        for row, (structure, _) in enumerate(self.STRUCTURES):
            name_item = QTableWidgetItem(structure.value)
            name_item.setToolTip(dict(self.STRUCTURES)[structure])
            self.count_table.setItem(row, 0, name_item)
            self.count_table.setItem(row, 1, QTableWidgetItem("—"))
            self.count_table.setItem(row, 2, QTableWidgetItem("0"))
        overview_layout.addWidget(self.count_table)

        self.latest_operation = QLabel("Latest operation: no operations recorded.")
        self.latest_operation.setObjectName("latest-operation")
        self.latest_operation.setWordWrap(True)
        self.latest_operation.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.latest_operation.setStyleSheet(
            "background: #102F46; border: 1px solid #38576B; border-radius: 7px; "
            "padding: 9px; color: #F4F7FA;"
        )
        overview_layout.addWidget(self.latest_operation)
        self.tabs.addTab(overview, "Overview")

        details = QTabWidget()
        details.setObjectName("dsa-structure-details")
        self.detail_views: dict[StructureName, QTextEdit] = {}
        for structure, _ in self.STRUCTURES:
            view = QTextEdit()
            view.setReadOnly(True)
            view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            view.setObjectName(
                "dsa-detail-" + structure.name.lower()
            )
            self.detail_views[structure] = view
            details.addTab(view, structure.value)
        self.tabs.addTab(details, "Structures")

        history = QWidget()
        history_layout = QVBoxLayout(history)
        history_layout.setContentsMargins(4, 8, 4, 4)
        history_label = QLabel(
            "Low-level events, in the order the real methods recorded them."
        )
        history_label.setWordWrap(True)
        history_label.setStyleSheet("color: #B9C7D3; font-size: 11px;")
        history_layout.addWidget(history_label)
        self.operation_history = QListWidget()
        self.operation_history.setObjectName("dsa-operation-history")
        self.operation_history.setAlternatingRowColors(True)
        history_layout.addWidget(self.operation_history, 1)
        self.tabs.addTab(history, "History")

        self._last_event_sequence = 0

    @staticmethod
    def _card_label(card) -> str:
        return "Empty" if card is None else f"{card} ({card.card_id})"

    @staticmethod
    def _event_line(event: OperationEvent) -> str:
        cards = ", ".join(event.card_ids) if event.card_ids else "no card ID"
        pile = event.pile_id or "game"
        return (
            f"#{event.sequence:04d}  {event.structure.value} · {event.operation} "
            f"| {event.context} | {pile} | {cards} | {event.outcome}"
        )

    def refresh(
        self,
        engine: GameEngine,
        selected_card_id: str | None = None,
        selected_pile_id: str | None = None,
    ) -> None:
        state = engine.state
        tracker = engine.tracker
        counts = tracker.counts()

        tableau_cards = sum(column.size() for column in state.tableau.values())
        foundation_cards = sum(pile.size() for pile in state.foundations.values())
        stack_current = (
            f"T:{tableau_cards} W:{state.waste.size()} F:{foundation_cards} "
            f"H:{engine.undo_stack.size()}/{engine.redo_stack.size()}"
        )
        queue_cards = state.stock.to_list()
        queue_current = (
            f"{state.stock.size()} | F:{queue_cards[0].card_id} "
            f"R:{queue_cards[-1].card_id}"
            if queue_cards else "0 | F:— R:—"
        )
        selected_column_id = (
            selected_pile_id
            if selected_pile_id in state.tableau
            else "tableau-1"
        )
        selected_column = state.tableau[selected_column_id]
        linked = selected_column.linked_list
        dictionary_current = f"{len(state.card_index)} / 52 entries"

        current_values = {
            StructureName.ARRAY_LIST: "0 active (dealt)",
            StructureName.STACK: stack_current,
            StructureName.QUEUE: queue_current,
            StructureName.LINKED_LIST: (
                f"{selected_column_id.rsplit('-', 1)[-1]}: {linked.size()} nodes"
            ),
            StructureName.DICTIONARY: dictionary_current,
        }
        for row, (structure, _) in enumerate(self.STRUCTURES):
            self.count_table.item(row, 1).setText(current_values[structure])
            self.count_table.item(row, 2).setText(str(counts[structure.value]))

        events = tracker.events
        if events:
            # Internal snapshot-stack maintenance uses HISTORY context. Show
            # the most recent player/setup operation group as the latest action
            # while keeping every low-level event in the History tab.
            latest_user_event = next(
                (event for event in reversed(events) if event.context != "HISTORY"),
                events[-1],
            )
            action_events = tracker.events_for_action(latest_user_event.action_id)
            latest = action_events[-1] if action_events else latest_user_event
            recent_steps = "\\n".join(
                f"  {event.structure.value}: {event.operation}"
                for event in action_events[-8:]
            )
            self.latest_operation.setText(
                "LATEST OPERATION GROUP\n"
                f"Action: {latest.action_id}   Context: {latest.context}\n"
                f"{len(action_events)} recorded steps; final step: "
                f"{latest.structure.value} / {latest.operation}\n"
                f"Pile: {latest.pile_id or 'game'}   Cards: "
                f"{', '.join(latest.card_ids) if latest.card_ids else '—'}\n"
                f"{recent_steps}"
            )
        else:
            self.latest_operation.setText(
                "Latest operation: no operations recorded."
            )

        setup_events = [
            event for event in events
            if event.structure is StructureName.ARRAY_LIST
        ]
        setup_lines = [
            "The 52-card deck is a temporary Python list used only for setup.",
            "After dealing, those cards live in the Queue, Stacks, and Linked Lists.",
            "",
            f"Setup operations recorded: {len(setup_events)}",
        ]
        setup_lines.extend(self._event_line(event) for event in setup_events[-12:])
        setup_lines.append("")
        setup_lines.append("Active deck list: cleared after the deal.")
        self.detail_views[StructureName.ARRAY_LIST].setPlainText(
            "\n".join(setup_lines)
        )

        stack_lines = [
            "STACKS — top is the last item (LIFO)",
            "",
            f"Waste ({state.waste.size()}): top "
            f"{self._card_label(state.waste.peek() if not state.waste.is_empty() else None)}",
        ]
        for suit in Suit:
            pile = state.foundations[suit]
            stack_lines.append(
                f"{suit.value} foundation ({pile.size()}): top "
                f"{self._card_label(pile.peek() if not pile.is_empty() else None)}"
            )
        stack_lines.append("")
        stack_lines.extend(
            f"{column_id} ({column.size()}): top "
            f"{self._card_label(column.peek() if not column.is_empty() else None)}"
            for column_id, column in state.tableau.items()
        )
        stack_lines.extend(
            [
                "",
                f"Undo history Stack: {engine.undo_stack.size()} snapshots",
                f"Redo history Stack: {engine.redo_stack.size()} snapshots",
            ]
        )
        self.detail_views[StructureName.STACK].setPlainText(
            "\n".join(stack_lines)
        )

        queue_lines = [
            "STOCK QUEUE — FIFO circular buffer",
            "",
            f"Size: {state.stock.size()}",
            f"Front / next to draw: {self._card_label(state.stock.peek() if not state.stock.is_empty() else None)}",
            f"Rear / newest queued: {self._card_label(state.stock.rear() if not state.stock.is_empty() else None)}",
            "",
            "Front-to-rear order:",
        ]
        queue_lines.extend(
            f"{index + 1:02d}. {card.card_id}"
            for index, card in enumerate(state.stock.to_list())
        )
        self.detail_views[StructureName.QUEUE].setPlainText(
            "\n".join(queue_lines)
        )

        linked_lines = [
            f"DOUBLY LINKED LIST — {selected_column_id}",
            "Tableau Stack top is the tail node.",
            "",
            f"Head: {self._card_label(linked.head.value if linked.head else None)}",
            f"Tail: {self._card_label(linked.tail.value if linked.tail else None)}",
            "",
            "Head -> nodes -> Tail:",
        ]
        nodes = list(linked.iter_nodes())
        for index, node in enumerate(nodes):
            previous = node.previous.value.card_id if node.previous else "None"
            following = node.next.value.card_id if node.next else "None"
            marker = "  < SELECTED" if node.value.card_id == selected_card_id else ""
            linked_lines.append(
                f"{index}: {node.value.card_id} | prev={previous} | "
                f"next={following}{marker}"
            )
        if not nodes:
            linked_lines.append("(empty linked list)")
        self.detail_views[StructureName.LINKED_LIST].setPlainText(
            "\n".join(linked_lines)
        )

        dictionary_lines = [
            "DICTIONARY — card ID -> CardLocation",
            "",
            f"Entries: {len(state.card_index)} / 52",
        ]
        if selected_card_id:
            location = state.card_index.get(selected_card_id)
            dictionary_lines.append(f"Selected card: {selected_card_id}")
            dictionary_lines.append(
                f"Lookup result: {location!r}" if location else "Lookup result: NOT FOUND"
            )
            dictionary_lines.append("")
        dictionary_lines.append("Sample entries:")
        for card_id in sorted(state.card_index)[:16]:
            dictionary_lines.append(f"{card_id}: {state.card_index[card_id]!r}")
        self.detail_views[StructureName.DICTIONARY].setPlainText(
            "\n".join(dictionary_lines)
        )

        # Rebuild only the latest 60 events to keep the sidebar responsive.
        self.operation_history.clear()
        for event in events[-60:]:
            item = self._event_line(event)
            self.operation_history.addItem(item)
        if events:
            self.operation_history.scrollToBottom()
        self._last_event_sequence = events[-1].sequence if events else 0
