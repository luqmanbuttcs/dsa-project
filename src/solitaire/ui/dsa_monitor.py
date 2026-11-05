"""Premium DSA dashboard backed by the real Solitaire OperationTracker."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QProgressBar, QPushButton,
    QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget, QHeaderView,
)

from solitaire.domain.card import Suit
from solitaire.domain.game_engine import GameEngine
from solitaire.domain.operations import OperationEvent, StructureName


class DSAMonitorPanel(QWidget):
    """Live, expandable structure cards, operation timeline and game statistics."""

    mode_changed = pyqtSignal(str)
    STRUCTURES = (
        (StructureName.ARRAY_LIST, "Temporary deck creation, shuffle, and deal", "▤"),
        (StructureName.STACK, "Waste, tableau, foundations, and history piles", "▥"),
        (StructureName.QUEUE, "FIFO stock draw and waste recycling", "⇥"),
        (StructureName.LINKED_LIST, "Tableau node chains and run transfers", "●─●"),
        (StructureName.DICTIONARY, "Card ID to live zone and position lookup", "▣"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dsa-monitor-panel")
        self.setMinimumWidth(340)
        root = QVBoxLayout(self)
        root.setContentsMargins(9, 9, 9, 8)
        root.setSpacing(8)
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("dsa-dashboard-tabs")
        root.addWidget(self.main_tabs, 1)

        dsa_page = QWidget()
        dsa_layout = QVBoxLayout(dsa_page)
        dsa_layout.setContentsMargins(3, 7, 3, 2)
        dsa_layout.setSpacing(8)
        dsa_scroll = QScrollArea()
        dsa_scroll.setObjectName("dsa-dashboard-scroll")
        dsa_scroll.setWidgetResizable(True)
        dsa_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        dsa_content = QWidget()
        content_layout = QVBoxLayout(dsa_content)
        content_layout.setContentsMargins(2, 2, 5, 8)
        content_layout.setSpacing(9)

        heading = QHBoxLayout()
        title = QLabel("Data Structures in Action")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #F5FAFF;")
        live = QLabel("● LIVE")
        live.setStyleSheet(
            "color: #92F28A; background: #103C31; border: 1px solid #2F8A5A; "
            "border-radius: 9px; padding: 3px 7px; font-size: 9px; font-weight: 900;"
        )
        heading.addWidget(title)
        heading.addStretch(1)
        heading.addWidget(live)
        content_layout.addLayout(heading)
        disclaimer = QLabel("Live operation counts come from completed data-structure operations.")
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("color: #AFC4D7; font-size: 10px;")
        content_layout.addWidget(disclaimer)

        self.structure_cards: dict[StructureName, QFrame] = {}
        self.structure_value_labels: dict[StructureName, QLabel] = {}
        self.structure_operation_labels: dict[StructureName, QLabel] = {}
        self.structure_detail_labels: dict[StructureName, QLabel] = {}

        for structure, description, icon_text in self.STRUCTURES:
            card = QFrame()
            card.setObjectName("dsa-structure-card")
            card.setStyleSheet(
                "QFrame#dsa-structure-card { background: #0B263E; "
                "border: 1px solid #254F6D; border-radius: 10px; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(9, 8, 8, 8)
            card_layout.setSpacing(5)
            top = QHBoxLayout()
            top.setSpacing(9)
            icon = QLabel(icon_text)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setFixedSize(42, 42)
            icon.setStyleSheet(
                "background: #0D426A; color: #8DD1FF; border: 1px solid #286E9F; "
                "border-radius: 9px; font-size: 19px; font-weight: 900;"
            )
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            name = QLabel(structure.value)
            name.setStyleSheet("color: #F3F8FF; font-size: 12px; font-weight: 800;")
            desc = QLabel(description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #AFC4D7; font-size: 10px;")
            text_col.addWidget(name)
            text_col.addWidget(desc)
            right = QVBoxLayout()
            right.setSpacing(1)
            operations = QLabel("OPS  0")
            operations.setAlignment(Qt.AlignmentFlag.AlignRight)
            operations.setStyleSheet("color: #F8D36A; font-size: 11px; font-weight: 900;")
            expand = QPushButton("⌄")
            expand.setObjectName(f"expand-{structure.name.lower()}")
            expand.setCheckable(True)
            expand.setFixedSize(27, 24)
            expand.setStyleSheet(
                "QPushButton { background: #102F49; color: #DCEBFA; border: 1px solid #2E5874; "
                "border-radius: 8px; padding: 0; font-size: 15px; }"
                "QPushButton:checked { color: #FFD65A; border-color: #FFD65A; }"
            )
            right.addWidget(operations)
            right.addWidget(expand, 0, Qt.AlignmentFlag.AlignRight)
            top.addWidget(icon)
            top.addLayout(text_col, 1)
            top.addLayout(right)
            card_layout.addLayout(top)
            current = QLabel("Current: —")
            current.setObjectName(f"current-{structure.name.lower()}")
            current.setWordWrap(True)
            current.setStyleSheet(
                "color: #D7E8F5; font-size: 10px; background: #071F33; "
                "border-radius: 6px; padding: 5px 7px;"
            )
            current.setVisible(False)
            expand.toggled.connect(current.setVisible)
            card_layout.addWidget(current)
            self.structure_cards[structure] = card
            self.structure_value_labels[structure] = current
            self.structure_detail_labels[structure] = current
            self.structure_operation_labels[structure] = operations
            content_layout.addWidget(card)

        latest_card = QFrame()
        latest_card.setObjectName("latest-operation-card")
        latest_card.setStyleSheet(
            "QFrame#latest-operation-card { background: #102F37; "
            "border: 1px solid #5E9E51; border-radius: 11px; }"
        )
        latest_layout = QVBoxLayout(latest_card)
        latest_layout.setContentsMargins(10, 8, 10, 8)
        latest_layout.setSpacing(4)
        latest_header = QHBoxLayout()
        check = QLabel("✓")
        check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check.setFixedSize(23, 23)
        check.setStyleSheet(
            "background: #27B84C; color: white; border-radius: 11px; "
            "font-size: 15px; font-weight: 900;"
        )
        latest_title = QLabel("Latest Operation")
        latest_title.setStyleSheet("color: #F4FFF0; font-size: 12px; font-weight: 900;")
        latest_header.addWidget(check)
        latest_header.addWidget(latest_title)
        latest_header.addStretch(1)
        latest_layout.addLayout(latest_header)
        self.latest_operation = QLabel("No operations recorded yet.")
        self.latest_operation.setObjectName("latest-operation")
        self.latest_operation.setWordWrap(True)
        self.latest_operation.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.latest_operation.setStyleSheet(
            "background: transparent; border: none; padding: 2px 3px; "
            "color: #F3F8FA; font-size: 10px;"
        )
        latest_layout.addWidget(self.latest_operation)
        content_layout.addWidget(latest_card)

        history_card = QFrame()
        history_card.setObjectName("operation-history-card")
        history_card.setStyleSheet(
            "QFrame#operation-history-card { background: #0A263D; "
            "border: 1px solid #254F6D; border-radius: 10px; }"
        )
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(9, 8, 9, 8)
        history_layout.setSpacing(6)
        history_title = QLabel("◷  Operation History")
        history_title.setStyleSheet("color: #F4F8FF; font-size: 12px; font-weight: 900;")
        history_layout.addWidget(history_title)
        self.move_timeline = QListWidget()
        self.move_timeline.setObjectName("player-move-timeline")
        self.move_timeline.setAlternatingRowColors(False)
        self.move_timeline.setMaximumHeight(170)
        self.move_timeline.setStyleSheet(
            "QListWidget { background: transparent; color: #DFEAF3; border: none; "
            "padding: 1px; font-size: 10px; }"
            "QListWidget::item { padding: 6px 3px; border-bottom: 1px solid #1C4058; }"
            "QListWidget::item:selected { background: #16486A; }"
        )
        history_layout.addWidget(self.move_timeline)
        content_layout.addWidget(history_card)

        self.inspect_toggle = QPushButton("⌄  Inspect Internal Structure Details")
        self.inspect_toggle.setObjectName("inspect-internals-toggle")
        self.inspect_toggle.setCheckable(True)
        self.inspect_toggle.setStyleSheet(
            "QPushButton { background: #0B2B46; color: #CDE1F0; border: 1px solid #315D79; "
            "border-radius: 8px; padding: 8px 10px; text-align: left; font-size: 10px; font-weight: 800; }"
            "QPushButton:checked { color: #FFD65A; border-color: #A88740; }"
        )
        content_layout.addWidget(self.inspect_toggle)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("dsa-monitor-tabs")
        counts_page = QWidget()
        counts_layout = QVBoxLayout(counts_page)
        counts_layout.setContentsMargins(2, 5, 2, 2)
        note = QLabel("Raw live counters from the operation tracker.")
        note.setStyleSheet("color: #AFC4D7; font-size: 10px;")
        counts_layout.addWidget(note)
        self.count_table = QTableWidget(5, 3)
        self.count_table.setObjectName("dsa-count-table")
        self.count_table.setHorizontalHeaderLabels(["Structure", "Current", "Operations"])
        self.count_table.verticalHeader().setVisible(False)
        self.count_table.setWordWrap(True)
        self.count_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.count_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.count_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.count_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.count_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.count_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for row, (structure, description, _icon) in enumerate(self.STRUCTURES):
            item = QTableWidgetItem(structure.value)
            item.setToolTip(description)
            self.count_table.setItem(row, 0, item)
            self.count_table.setItem(row, 1, QTableWidgetItem("—"))
            self.count_table.setItem(row, 2, QTableWidgetItem("0"))
        counts_layout.addWidget(self.count_table)
        self.tabs.addTab(counts_page, "Live Counts")
        self.detail_views: dict[StructureName, QTextEdit] = {}
        for structure, _description, _icon in self.STRUCTURES:
            view = QTextEdit()
            view.setReadOnly(True)
            view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            view.setObjectName("dsa-detail-" + structure.name.lower())
            self.detail_views[structure] = view
            self.tabs.addTab(view, structure.value)

        events_page = QWidget()
        events_layout = QVBoxLayout(events_page)
        events_layout.setContentsMargins(4, 6, 4, 4)
        events_note = QLabel(
            "Low-level operation events in the order the real data-structure methods recorded them."
        )
        events_note.setWordWrap(True)
        events_note.setStyleSheet("color: #AFC4D7; font-size: 10px;")
        events_layout.addWidget(events_note)
        self.operation_history = QListWidget()
        self.operation_history.setObjectName("dsa-operation-history")
        self.operation_history.setAlternatingRowColors(True)
        self.operation_history.setStyleSheet(
            "QListWidget { background: #071F33; color: #DFEAF3; border: 1px solid #28516D; "
            "border-radius: 8px; padding: 4px; font-size: 10px; }"
            "QListWidget::item { padding: 5px 3px; }"
        )
        events_layout.addWidget(self.operation_history)
        self.tabs.addTab(events_page, "Operation Events")

        self.details_panel = QFrame()
        self.details_panel.setObjectName("dsa-details-panel")
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(self.tabs)
        self.details_panel.setVisible(False)
        self.inspect_toggle.toggled.connect(self.details_panel.setVisible)
        content_layout.addWidget(self.details_panel)
        content_layout.addStretch(1)
        dsa_scroll.setWidget(dsa_content)
        dsa_layout.addWidget(dsa_scroll, 1)
        self.main_tabs.addTab(dsa_page, "▥  DSA Monitor")

        stats_page = QWidget()
        stats_layout = QVBoxLayout(stats_page)
        stats_layout.setContentsMargins(10, 12, 10, 10)
        stats_layout.setSpacing(9)
        stat_rows = (
            ("MOVES", "moves"), ("SCORE", "score"), ("ELAPSED TIME", "time"),
            ("DRAW MODE", "draw_mode"), ("STOCK REMAINING", "stock"),
            ("WASTE CARDS", "waste"), ("FOUNDATION PROGRESS", "foundations"),
            ("TABLEAU CARDS", "tableau"),
        )
        self.game_stats_labels: dict[str, QLabel] = {}
        for caption, key in stat_rows:
            stat_card = QFrame()
            stat_card.setObjectName("game-stat-card")
            stat_card.setStyleSheet(
                "QFrame#game-stat-card { background: #0B2941; border: 1px solid #28516D; border-radius: 10px; }"
            )
            row = QHBoxLayout(stat_card)
            row.setContentsMargins(11, 8, 11, 8)
            caption_label = QLabel(caption)
            caption_label.setStyleSheet(
                "color: #AFC5D8; font-size: 10px; font-weight: 900; letter-spacing: 0.6px;"
            )
            value = QLabel("—")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value.setStyleSheet("color: #F5FAFF; font-size: 14px; font-weight: 900;")
            row.addWidget(caption_label, 1)
            row.addWidget(value)
            stats_layout.addWidget(stat_card)
            self.game_stats_labels[key] = value
        self.foundation_progress = QProgressBar()
        self.foundation_progress.setObjectName("foundation-progress")
        self.foundation_progress.setRange(0, 52)
        self.foundation_progress.setValue(0)
        self.foundation_progress.setFormat("Foundation progress  %v / 52")
        self.foundation_progress.setStyleSheet(
            "QProgressBar { background: #071F33; border: 1px solid #315D79; "
            "border-radius: 7px; color: #F2F7FB; text-align: center; height: 18px; }"
            "QProgressBar::chunk { background: #25A94B; border-radius: 6px; }"
        )
        stats_layout.addWidget(self.foundation_progress)
        stats_layout.addStretch(1)
        self.main_tabs.addTab(stats_page, "🏆  Game Stats")

        mode_frame = QFrame()
        mode_frame.setObjectName("game-mode-frame")
        mode_frame.setStyleSheet(
            "QFrame#game-mode-frame { background: #081E32; border: 1px solid #254F6D; border-radius: 10px; }"
        )
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(8, 7, 8, 7)
        mode_layout.setSpacing(6)
        mode_title = QLabel("GAME MODE")
        mode_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_title.setStyleSheet("color: #AFC4D7; font-size: 10px; font-weight: 900;")
        mode_layout.addWidget(mode_title)
        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        self.play_mode_button = QPushButton("♟  Play Mode")
        self.play_mode_button.setObjectName("play-mode-button")
        self.play_mode_button.setCheckable(True)
        self.dsa_lab_button = QPushButton("</>  DSA Lab")
        self.dsa_lab_button.setObjectName("dsa-lab-button")
        self.dsa_lab_button.setCheckable(True)
        for button in (self.play_mode_button, self.dsa_lab_button):
            button.setMinimumHeight(35)
            button.setStyleSheet(
                "QPushButton { background: #0B2B46; color: #C8D9E7; border: 1px solid #315D79; "
                "border-radius: 18px; padding: 6px 10px; font-size: 10px; font-weight: 800; }"
                "QPushButton:checked { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #087DD0, stop:1 #0756A2); "
                "color: white; border: 1px solid #56B9FF; }"
                "QPushButton:hover { border-color: #75C7FF; }"
            )
        self.play_mode_button.setChecked(True)
        self.play_mode_button.clicked.connect(lambda: self.mode_changed.emit("play"))
        self.dsa_lab_button.clicked.connect(lambda: self.mode_changed.emit("dsa"))
        buttons.addWidget(self.play_mode_button)
        buttons.addWidget(self.dsa_lab_button)
        mode_layout.addLayout(buttons)
        root.addWidget(mode_frame)
        self._current_mode = "play"

    @staticmethod
    def _card_label(card) -> str:
        return "Empty" if card is None else f"{card} ({card.card_id})"

    @staticmethod
    def _event_line(event: OperationEvent) -> str:
        cards = ", ".join(event.card_ids) if event.card_ids else "no card ID"
        pile = event.pile_id or "game"
        return (
            f"#{event.sequence:04d}  {event.timestamp[11:19]} UTC  "
            f"{event.structure.value} · {event.operation} "
            f"| {event.context} | {pile} | {cards} | {event.outcome}"
        )

    def set_mode(self, mode: str) -> None:
        self._current_mode = "dsa" if mode == "dsa" else "play"
        is_lab = self._current_mode == "dsa"
        self.play_mode_button.setChecked(not is_lab)
        self.dsa_lab_button.setChecked(is_lab)
        self.main_tabs.setCurrentIndex(0)
        self.inspect_toggle.setChecked(is_lab)

    def refresh_stats(self, engine: GameEngine) -> None:
        state = engine.state
        foundation_cards = sum(pile.size() for pile in state.foundations.values())
        tableau_cards = sum(column.size() for column in state.tableau.values())
        elapsed = max(0, int(state.elapsed_seconds))
        values = {
            "moves": str(state.move_count),
            "score": str(state.score),
            "time": f"{elapsed // 60:02d}:{elapsed % 60:02d}",
            "draw_mode": f"Draw {state.draw_count}",
            "stock": f"{state.stock.size()} cards",
            "waste": f"{state.waste.size()} cards",
            "foundations": f"{foundation_cards} / 52 cards",
            "tableau": f"{tableau_cards} cards / 7 columns",
        }
        for key, value in values.items():
            self.game_stats_labels[key].setText(value)
        self.foundation_progress.setValue(foundation_cards)

    def refresh(
        self,
        engine: GameEngine,
        selected_card_id: str | None = None,
        selected_pile_id: str | None = None,
    ) -> None:
        state = engine.state
        counts = engine.tracker.counts()
        tableau_cards = sum(column.size() for column in state.tableau.values())
        foundation_cards = sum(pile.size() for pile in state.foundations.values())
        stack_current = (
            f"T:{tableau_cards} W:{state.waste.size()} F:{foundation_cards} "
            f"H:{engine.undo_stack.size()}/{engine.redo_stack.size()}"
        )
        queue_cards = state.stock.to_list()
        queue_current = (
            f"{state.stock.size()} | F:{queue_cards[0].card_id} R:{queue_cards[-1].card_id}"
            if queue_cards else "0 | F:— R:—"
        )
        selected_column_id = selected_pile_id if selected_pile_id in state.tableau else "tableau-1"
        selected_column = state.tableau[selected_column_id]
        linked = selected_column.linked_list
        current_values = {
            StructureName.ARRAY_LIST: "0 active (dealt)",
            StructureName.STACK: stack_current,
            StructureName.QUEUE: queue_current,
            StructureName.LINKED_LIST: f"{selected_column_id.rsplit('-', 1)[-1]}: {linked.size()} nodes",
            StructureName.DICTIONARY: f"{len(state.card_index)} / 52 entries",
        }
        for row, (structure, _description, _icon) in enumerate(self.STRUCTURES):
            current_text = current_values[structure]
            operation_count = counts[structure.value]
            self.count_table.item(row, 1).setText(current_text)
            self.count_table.item(row, 2).setText(str(operation_count))
            self.structure_value_labels[structure].setText(f"Current: {current_text}")
            self.structure_operation_labels[structure].setText(f"OPS  {operation_count}")

        events = engine.tracker.events
        if events:
            latest_user_event = next(
                (event for event in reversed(events) if event.context != "HISTORY"),
                events[-1],
            )
            action_events = engine.tracker.events_for_action(latest_user_event.action_id)
            latest = action_events[-1] if action_events else latest_user_event
            step_counts: dict[str, int] = {}
            for event in action_events:
                label = f"{event.structure.value}: {event.operation}"
                step_counts[label] = step_counts.get(label, 0) + 1
            step_summary = "  →  ".join(
                f"{label} ×{amount}" for label, amount in step_counts.items()
            )
            self.latest_operation.setText(
                f"{latest.structure.value}  ·  {latest.operation}\n"
                f"Action: {latest.action_id}   Context: {latest.context}\n"
                f"{len(action_events)} recorded steps  ·  "
                f"Pile: {latest.pile_id or 'game'}  ·  "
                f"Cards: {', '.join(latest.card_ids) if latest.card_ids else '—'}\n"
                f"Sequence: {step_summary}"
            )
        else:
            self.latest_operation.setText("No operations recorded yet.")

        self.operation_history.clear()
        for event in events[-60:]:
            self.operation_history.addItem(self._event_line(event))
        if events:
            self.operation_history.scrollToBottom()

        self.move_timeline.clear()
        for move in reversed(engine.move_history[-5:]):
            action_events = engine.tracker.events_for_action(move.action_id)
            timestamp = action_events[-1].timestamp[11:16] if action_events else "--:--"
            self.move_timeline.addItem(f"✓   {timestamp}   {move.description}")
        if engine.move_history:
            self.move_timeline.scrollToTop()
        else:
            self.move_timeline.addItem("No player moves recorded yet.")

        setup_events = [event for event in events if event.structure is StructureName.ARRAY_LIST]
        setup_lines = [
            "The 52-card deck is a temporary Python list used only for setup.",
            "After dealing, those cards live in the Queue, Stacks, and Linked Lists.",
            "", f"Setup operations recorded: {len(setup_events)}",
        ]
        setup_lines.extend(self._event_line(event) for event in setup_events[-12:])
        setup_lines.extend(["", "Active deck list: cleared after the deal."])
        self.detail_views[StructureName.ARRAY_LIST].setPlainText("\n".join(setup_lines))

        stack_lines = [
            "STACKS — top is the last item (LIFO)", "",
            f"Waste ({state.waste.size()}): top "
            f"{self._card_label(state.waste.peek() if not state.waste.is_empty() else None)}",
        ]
        for suit in Suit:
            pile = state.foundations[suit]
            stack_lines.append(
                f"{suit.value} foundation ({pile.size()}): top "
                f"{self._card_label(pile.peek() if not pile.is_empty() else None)}"
            )
        stack_lines.extend(
            f"{column_id} ({column.size()}): top "
            f"{self._card_label(column.peek() if not column.is_empty() else None)}"
            for column_id, column in state.tableau.items()
        )
        stack_lines.extend(["", f"Undo history Stack: {engine.undo_stack.size()} snapshots",
                            f"Redo history Stack: {engine.redo_stack.size()} snapshots"])
        self.detail_views[StructureName.STACK].setPlainText("\n".join(stack_lines))

        queue_lines = [
            "STOCK QUEUE — FIFO circular buffer", "", f"Size: {state.stock.size()}",
            f"Front / next to draw: {self._card_label(state.stock.peek() if not state.stock.is_empty() else None)}",
            f"Rear / newest queued: {self._card_label(state.stock.rear() if not state.stock.is_empty() else None)}",
            "", "Front-to-rear order:",
        ]
        queue_lines.extend(
            f"{index + 1:02d}. {card.card_id}"
            for index, card in enumerate(state.stock.to_list())
        )
        self.detail_views[StructureName.QUEUE].setPlainText("\n".join(queue_lines))

        linked_lines = [
            f"DOUBLY LINKED LIST — {selected_column_id}",
            "Tableau Stack top is the tail node.", "",
            f"Head: {self._card_label(linked.head.value if linked.head else None)}",
            f"Tail: {self._card_label(linked.tail.value if linked.tail else None)}",
            "", "Head -> nodes -> Tail:",
        ]
        nodes = list(linked.iter_nodes())
        for index, node in enumerate(nodes):
            previous = node.previous.value.card_id if node.previous else "None"
            following = node.next.value.card_id if node.next else "None"
            marker = "  < SELECTED" if node.value.card_id == selected_card_id else ""
            linked_lines.append(
                f"{index}: {node.value.card_id} | prev={previous} | next={following}{marker}"
            )
        if not nodes:
            linked_lines.append("(empty linked list)")
        self.detail_views[StructureName.LINKED_LIST].setPlainText("\n".join(linked_lines))

        dictionary_lines = [
            "DICTIONARY — card ID -> CardLocation", "",
            f"Entries: {len(state.card_index)} / 52",
        ]
        if selected_card_id:
            location = state.card_index.get(selected_card_id)
            dictionary_lines.extend([
                f"Selected card: {selected_card_id}",
                f"Lookup result: {location!r}" if location else "Lookup result: NOT FOUND", "",
            ])
        dictionary_lines.append("Sample entries:")
        dictionary_lines.extend(
            f"{card_id}: {state.card_index[card_id]!r}"
            for card_id in sorted(state.card_index)[:16]
        )
        self.detail_views[StructureName.DICTIONARY].setPlainText("\n".join(dictionary_lines))
        self.refresh_stats(engine)
