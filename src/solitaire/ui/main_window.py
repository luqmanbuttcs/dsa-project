"""Main PyQt6 window for playing Klondike Solitaire."""

from __future__ import annotations

from random import Random
from time import monotonic

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from solitaire.domain.card import Suit
from solitaire.domain.game_engine import (
    GameEngine,
    InvalidMoveError,
    NoCardsAvailableError,
)
from solitaire.domain.game_state import GameStatus, Zone, create_new_game
from solitaire.domain.operations import OperationTracker
from solitaire.ui.card_widget import CardButton
from solitaire.ui.dsa_monitor import DSAMonitorPanel
from solitaire.ui.pile_widgets import (
    CARD_HEIGHT,
    CARD_WIDTH,
    FoundationSlot,
    StockButton,
    TableauColumnWidget,
    WasteWidget,
)
from solitaire.ui.theme import APP_STYLESHEET, FeltBoard


class MainWindow(QMainWindow):
    """Playable click-to-move Klondike interface over the tested game engine."""

    def __init__(self, engine: GameEngine | None = None, parent=None) -> None:
        super().__init__(parent)
        if engine is None:
            tracker = OperationTracker()
            engine = GameEngine(create_new_game(tracker=tracker), tracker)
        self.engine = engine
        self._selected_card_id: str | None = None
        self._selected_pile_id: str | None = None
        self._tableau_widgets: dict[str, TableauColumnWidget] = {}
        self._foundation_widgets: dict[Suit, FoundationSlot] = {}
        self._elapsed_base = float(self.engine.state.elapsed_seconds)
        self._clock_activated = bool(
            self.engine.state.move_count or self.engine.state.elapsed_seconds
        )
        self._clock_started_at: float | None = (
            monotonic()
            if self._clock_activated and self.engine.state.status is not GameStatus.WON
            else None
        )
        self._hint_index = 0
        self._active_animations: list[QPropertyAnimation] = []
        self._drag_destinations: set[str] = set()

        self.setObjectName("klondike-main-window")
        self.setWindowTitle("Klondike Solitaire — CSC200 DSA Edition")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 900)
        self._build_ui()
        self.dsa_monitor = DSAMonitorPanel(self)
        self.dsa_monitor_dock = QDockWidget("DSA Monitor", self)
        self.dsa_monitor_dock.setObjectName("dsa-monitor-dock")
        self.dsa_monitor_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.dsa_monitor_dock.setMinimumWidth(340)
        dock_title = QWidget(self.dsa_monitor_dock)
        dock_title.setFixedHeight(0)
        self.dsa_monitor_dock.setTitleBarWidget(dock_title)
        self.dsa_monitor_dock.setStyleSheet(
            "QDockWidget { color: #F4F8FF; background: #081D31; border: 1px solid #244965; }"
            "QDockWidget::title { background: #07182A; color: #EAF4FF; padding: 10px 12px; font-weight: 800; border-bottom: 1px solid #214763; }"
        )
        self.dsa_monitor_dock.setWidget(self.dsa_monitor)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dsa_monitor_dock
        )
        self.dsa_monitor_button.toggled.connect(self.dsa_monitor_dock.setVisible)
        self.dsa_monitor_action.toggled.connect(self.dsa_monitor_dock.setVisible)
        self.dsa_monitor_dock.visibilityChanged.connect(self.dsa_monitor_button.setChecked)
        self.dsa_monitor_dock.visibilityChanged.connect(self.dsa_monitor_action.setChecked)
        self.dsa_monitor.mode_changed.connect(self._set_game_mode)
        self.dsa_monitor_button.setChecked(True)
        self.resizeDocks(
            [self.dsa_monitor_dock], [370], Qt.Orientation.Horizontal
        )
        self.dsa_monitor.set_mode("play")
        self.dsa_monitor_button.setChecked(True)
        self.dsa_monitor_action.setChecked(True)
        self._install_shortcuts()
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock_display)
        self._clock_timer.start()
        self._refresh_board()
        self._update_clock_display()

    @property
    def selected_card_id(self) -> str | None:
        return self._selected_card_id

    @property
    def tableau_widgets(self) -> dict[str, TableauColumnWidget]:
        return dict(self._tableau_widgets)

    @property
    def foundation_widgets(self) -> dict[Suit, FoundationSlot]:
        return dict(self._foundation_widgets)

    def _build_ui(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)

        central = QWidget()
        central.setObjectName("central-widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(11)

        header_panel = QFrame()
        header_panel.setObjectName("app-header")
        header_panel.setStyleSheet(
            "QFrame#app-header { background: #06182A; border: 1px solid #1F405B; "
            "border-radius: 12px; }"
        )
        header = QHBoxLayout(header_panel)
        header.setContentsMargins(13, 7, 13, 7)
        header.setSpacing(10)
        title_group = QHBoxLayout()
        title_group.setSpacing(8)
        spade = QLabel("♠")
        spade.setStyleSheet("color: #FFFFFF; font-size: 39px; font-weight: 800;")
        title = QLabel("Klondike Solitaire")
        title.setObjectName("game-title")
        title.setStyleSheet("font-family: Georgia, 'Times New Roman', serif; font-size: 27px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.3px;")
        subtitle = QLabel("CSC200 – DSA Edition")
        subtitle.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #9DFFB8; background: #064832; "
            "border: 1px solid #168C60; border-radius: 13px; padding: 5px 10px;"
        )
        title_group.addWidget(spade)
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        header.addLayout(title_group)
        header.addStretch(1)

        self.moves_label = QLabel("MOVES  0")
        self.moves_label.setObjectName("moves-label")
        self.moves_label.setStyleSheet(
            "background: #0B2B46; border: 1px solid #23506B; border-radius: 11px; "
            "padding: 9px 13px; font-size: 12px; font-weight: 800; color: #F6FBFF;"
        )
        self.moves_metric = self._metric_card("✣", self.moves_label)

        self.score_label = QLabel(f"SCORE  {self.engine.state.score}")
        self.score_label.setObjectName("score-label")
        self.score_label.setStyleSheet(
            "background: #0B2B46; border: 1px solid #23506B; border-radius: 11px; "
            "padding: 9px 13px; font-size: 12px; font-weight: 800; color: #F6FBFF;"
        )
        self.score_metric = self._metric_card("🏆", self.score_label)

        self.timer_label = QLabel("TIME  00:00")
        self.timer_label.setObjectName("timer-label")
        self.timer_label.setStyleSheet(
            "background: #0B2B46; border: 1px solid #23506B; border-radius: 11px; "
            "padding: 9px 13px; font-size: 12px; font-weight: 800; color: #F6FBFF;"
        )
        self.timer_metric = self._metric_card("◷", self.timer_label)
        header.addWidget(self.timer_metric)
        header.addWidget(self.moves_metric)
        header.addWidget(self.score_metric)

        self.hint_button = QPushButton("💡 Hint")
        self.hint_button.setObjectName("hint-button")
        self.hint_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FFD965, stop:1 #D89B23); color: #172334; border: 1px solid #FFE9A4; border-radius: 12px; font-weight: 800; padding: 8px 15px; }"
            "QPushButton:hover { background: #FFE28A; }"
        )
        self.hint_button.clicked.connect(self._show_hint)
        header.addWidget(self.hint_button)

        self.dsa_monitor_button = QPushButton("DSA Monitor")
        self.dsa_monitor_button.setObjectName("dsa-monitor-toggle")
        self.dsa_monitor_button.setCheckable(True)
        self.dsa_monitor_button.setChecked(True)
        self.dsa_monitor_button.setVisible(False)

        self.new_game_button = QPushButton("New Game")
        self.new_game_button.setObjectName("new-game-button")
        self.new_game_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1499F4, stop:1 #0067C9); color: white; border: 1px solid #54B9FF; border-radius: 12px; font-weight: 800; padding: 8px 15px; }"
            "QPushButton:hover { background: #1CA4FF; }"
        )
        self.new_game_button.clicked.connect(self._new_game)
        self.new_game_button.setVisible(False)

        self.undo_button = QPushButton("↶ Undo")
        self.undo_button.setObjectName("undo-button")
        self.undo_button.clicked.connect(self._undo)
        header.addWidget(self.undo_button)

        self.redo_button = QPushButton("↷ Redo")
        self.redo_button.setObjectName("redo-button")
        self.redo_button.clicked.connect(self._redo)
        header.addWidget(self.redo_button)

        self.settings_button = QPushButton("⚙ Settings")
        self.settings_button.setObjectName("settings-button")
        self.settings_button.setStyleSheet(
            "QPushButton { background: #102F49; color: #DCEBFA; border: 1px solid #294D68; border-radius: 12px; padding: 8px 13px; }"
            "QPushButton:hover { background: #173D5B; border-color: #69A9D5; }"
        )
        header.addWidget(self.settings_button)
        root.addWidget(header_panel)

        self.victory_panel = QFrame()
        self.victory_panel.setObjectName("victory-panel")
        self.victory_panel.setStyleSheet(
            "QFrame#victory-panel { background: #075C35; "
            "border: 2px solid #82F36F; border-radius: 14px; }"
            "QLabel { color: #FFFFFF; font-size: 14px; font-weight: 800; "
            "padding: 9px 14px; }"
        )
        victory_layout = QHBoxLayout(self.victory_panel)
        victory_layout.setContentsMargins(8, 2, 8, 2)
        self.victory_label = QLabel(
            "VICTORY  •  All 52 cards are in their foundations."
        )
        self.victory_label.setObjectName("victory-message")
        victory_layout.addWidget(self.victory_label)
        self.victory_panel.setVisible(False)
        root.addWidget(self.victory_panel)

        board = FeltBoard()
        board.setObjectName("game-board")
        board_layout = QVBoxLayout(board)
        board_layout.setContentsMargins(20, 18, 20, 18)
        board_layout.setSpacing(18)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        self.stock_button = StockButton()
        self.stock_button.clicked.connect(self._draw_stock)
        stock_group = self._pile_group("STOCK", self.stock_button)
        top_row.addWidget(stock_group)

        self.waste_widget = WasteWidget()
        self.waste_widget.card_selected.connect(self._card_selected)
        self.waste_widget.card_drag_started.connect(self._start_drag_preview)
        self.waste_widget.card_drag_finished.connect(self._clear_drag_preview)
        waste_group = self._pile_group("WASTE", self.waste_widget)
        top_row.addWidget(waste_group)
        top_row.addStretch(1)

        for suit in Suit:
            slot = FoundationSlot(suit)
            slot.selected.connect(self._foundation_selected)
            slot.card_dropped.connect(self._handle_drop)
            self._foundation_widgets[suit] = slot
            top_row.addWidget(self._pile_group(suit.value.upper(), slot))

        board_layout.addLayout(top_row)

        tableau_heading = QLabel("TABLEAU")
        tableau_heading.setStyleSheet(
            "font-size: 11px; font-weight: 800; letter-spacing: 1px; "
            "color: rgba(255,255,255,0.82);"
        )
        board_layout.addWidget(tableau_heading)

        tableau_scroll = QScrollArea()
        tableau_scroll.setObjectName("tableau-scroll-area")
        tableau_scroll.setWidgetResizable(True)
        tableau_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tableau_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tableau_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        tableau_content = QWidget()
        tableau_content.setStyleSheet("background: transparent;")
        tableau_layout = QHBoxLayout(tableau_content)
        tableau_layout.setContentsMargins(0, 0, 0, 0)
        tableau_layout.setSpacing(22)
        tableau_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        for column_number in range(1, 8):
            column_id = f"tableau-{column_number}"
            widget = TableauColumnWidget(column_id)
            widget.card_selected.connect(self._card_selected)
            widget.empty_selected.connect(self._empty_tableau_selected)
            widget.card_dropped.connect(self._handle_drop)
            widget.card_drag_started.connect(self._start_drag_preview)
            widget.card_drag_finished.connect(self._clear_drag_preview)
            self._tableau_widgets[column_id] = widget
            tableau_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignTop)

        tableau_layout.addStretch(1)
        tableau_scroll.setWidget(tableau_content)
        board_layout.addWidget(tableau_scroll, 1)

        board_footer = QHBoxLayout()
        board_footer.setSpacing(10)

        log_panel = QFrame()
        log_panel.setObjectName("move-log-panel")
        log_panel.setMinimumWidth(300)
        log_panel.setStyleSheet(
            "QFrame#move-log-panel { background: rgba(5, 29, 44, 235); "
            "border: 1px solid #2B7392; border-radius: 13px; }"
        )
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(11, 8, 11, 8)
        log_layout.setSpacing(5)
        log_title = QLabel("▤  Move Log")
        log_title.setStyleSheet("font-size: 13px; font-weight: 900; color: #F6FAFF;")
        self.move_log = QListWidget()
        self.move_log.setObjectName("move-log")
        self.move_log.setMaximumHeight(116)
        self.move_log.setMinimumHeight(82)
        self.move_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.move_log.setStyleSheet(
            "QListWidget { background: rgba(3, 24, 39, 145); color: #EFF6FD; "
            "border: 1px solid #244E67; border-radius: 8px; padding: 5px; font-size: 11px; }"
            "QListWidget::item { padding: 4px 5px; border-bottom: 1px solid rgba(100, 150, 170, 35); }"
        )
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.move_log)
        board_footer.addWidget(log_panel, 3)

        feedback_panel = QFrame()
        feedback_panel.setObjectName("feedback-panel")
        feedback_panel.setMinimumWidth(210)
        feedback_panel.setStyleSheet(
            "QFrame#feedback-panel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
            "stop:0 rgba(14, 90, 52, 238), stop:1 rgba(5, 49, 34, 245)); "
            "border: 2px solid #78E95D; border-radius: 14px; }"
        )
        feedback_layout = QVBoxLayout(feedback_panel)
        feedback_layout.setContentsMargins(11, 10, 11, 10)
        feedback_layout.setSpacing(5)
        feedback_header = QHBoxLayout()
        self.feedback_icon_label = QLabel("✓")
        self.feedback_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_icon_label.setFixedSize(31, 31)
        self.feedback_icon_label.setStyleSheet(
            "background: #23B948; color: white; border: 1px solid #A7FF9A; "
            "border-radius: 15px; font-size: 20px; font-weight: 900;"
        )
        self.feedback_title_label = QLabel("Ready to Play")
        self.feedback_title_label.setStyleSheet(
            "color: #FFE078; font-size: 14px; font-weight: 900;"
        )
        feedback_header.addWidget(self.feedback_icon_label)
        feedback_header.addWidget(self.feedback_title_label, 1)
        feedback_layout.addLayout(feedback_header)
        self.status_label = QLabel("Select a face-up card, then select a destination.")
        self.status_label.setObjectName("game-status")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "background: transparent; color: #F4FFF5; border: none; "
            "font-size: 11px; padding: 3px 4px;"
        )
        feedback_layout.addWidget(self.status_label)
        board_footer.addWidget(feedback_panel, 2)

        board_layout.addLayout(board_footer)
        root.addWidget(board, 1)

        controls_panel = QFrame()
        controls_panel.setObjectName("game-controls-panel")
        controls_panel.setStyleSheet(
            "QFrame#game-controls-panel { background: #08243A; border: 1px solid #244B65; "
            "border-radius: 9px; }"
        )
        controls = QHBoxLayout(controls_panel)
        controls.setContentsMargins(12, 5, 12, 5)
        controls.setSpacing(11)
        draw_group = QHBoxLayout()
        draw_group.setSpacing(8)
        draw_label = QLabel("DRAW MODE")
        draw_label.setStyleSheet("font-size: 10px; font-weight: 900; color: #BDD0DF;")
        self.draw_mode_combo = QComboBox()
        self.draw_mode_combo.setObjectName("draw-mode-combo")
        self.draw_mode_combo.addItem("Draw 1", 1)
        self.draw_mode_combo.addItem("Draw 3", 3)
        self.draw_mode_combo.setCurrentIndex(
            self.draw_mode_combo.findData(self.engine.state.draw_count)
        )
        self.draw_mode_combo.currentIndexChanged.connect(self._draw_mode_changed)
        draw_group.addWidget(draw_label)
        draw_group.addWidget(self.draw_mode_combo)
        controls.addLayout(draw_group)
        self.reduce_motion_check = QCheckBox("Reduce motion")
        self.reduce_motion_check.setObjectName("reduce-motion-check")
        self.reduce_motion_check.setToolTip(
            "Disable travel/flip animations while keeping move feedback and DSA events."
        )
        controls.addWidget(self.reduce_motion_check)
        controls.addStretch(1)

        # Keep secondary actions in the reference-style Settings menu.
        settings_menu = QMenu(self.settings_button)
        draw_one_action = settings_menu.addAction("Draw 1")
        draw_one_action.triggered.connect(lambda: self.draw_mode_combo.setCurrentIndex(0))
        draw_three_action = settings_menu.addAction("Draw 3")
        draw_three_action.triggered.connect(lambda: self.draw_mode_combo.setCurrentIndex(1))
        settings_menu.addSeparator()
        self.reduce_motion_action = QAction("Reduce Motion", self)
        self.reduce_motion_action.setCheckable(True)
        self.reduce_motion_action.toggled.connect(self.reduce_motion_check.setChecked)
        self.reduce_motion_check.toggled.connect(self.reduce_motion_action.setChecked)
        settings_menu.addAction(self.reduce_motion_action)
        settings_menu.addSeparator()
        new_game_action = settings_menu.addAction("New Game")
        new_game_action.triggered.connect(self._new_game)
        self.dsa_monitor_action = settings_menu.addAction("Show DSA Monitor")
        self.dsa_monitor_action.setCheckable(True)
        self.dsa_monitor_action.setChecked(True)
        self.settings_button.setMenu(settings_menu)

        root.addWidget(controls_panel)

    @staticmethod
    def _metric_card(icon_text: str, value_label: QLabel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("header-metric-card")
        frame.setStyleSheet(
            "QFrame#header-metric-card { background: #0A2943; "
            "border: 1px solid #28526F; border-radius: 12px; }"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 5, 10, 5)
        row.setSpacing(7)
        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 23px; color: #FFD45A;")
        value_label.setStyleSheet(
            "background: transparent; border: none; padding: 2px 1px; "
            "font-size: 11px; font-weight: 900; color: #F5FAFF;"
        )
        row.addWidget(icon)
        row.addWidget(value_label)
        return frame

    def _set_game_mode(self, mode: str) -> None:
        """Resize the dock and reveal internals in the academic DSA Lab mode."""
        mode = "dsa" if mode == "dsa" else "play"
        self.dsa_monitor.set_mode(mode)
        self.resizeDocks(
            [self.dsa_monitor_dock],
            [445 if mode == "dsa" else 370],
            Qt.Orientation.Horizontal,
        )
        self._set_status(
            "DSA Lab enabled. Inspect structure internals and live operation history."
            if mode == "dsa" else
            "Play Mode enabled. The game board has priority."
        )

    @staticmethod
    def _pile_group(caption: str, pile_widget: QWidget) -> QWidget:
        group = QWidget()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label = QLabel(caption)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("font-size: 10px; font-weight: 800; color: #D2E0D8;")
        layout.addWidget(label)
        layout.addWidget(pile_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        return group

    def _draw_mode_changed(self, index: int) -> None:
        count = self.draw_mode_combo.currentData()
        if count in (1, 3):
            self.engine.set_draw_count(count)
            self._set_status(f"Stock draw mode set to Draw {count}.")

    def _draw_stock(self) -> None:
        stock_visual = self._capture_widget_visual(self.stock_button)
        try:
            drawn = self.engine.draw_from_stock()
        except NoCardsAvailableError as error:
            self._set_status(str(error), error=True)
            return
        except RuntimeError as error:
            self._set_status(str(error), error=True)
            return

        self._mark_player_action()
        self._clear_selection()
        self._set_status(f"Drew {len(drawn)} card(s). Select the top waste card to move it.")
        # DEBUG ISOLATION: skip all widget rebuilding during stock draw.
        if False:
            self._refresh_board()
        if drawn and stock_visual is not None:
            self._animate_move_visuals(
                {card.card_id: stock_visual for card in drawn}
            )

    def _card_selected(self, card_id: str, pile_id: str) -> None:
        if pile_id.startswith("foundation-"):
            suit = next((item for item in Suit if pile_id == f"foundation-{item.code.lower()}"), None)
            if suit is not None:
                self._foundation_selected(suit)
            return

        if self._selected_card_id is None:
            self._select_card(card_id, pile_id)
            return

        if pile_id == self._selected_pile_id:
            self._select_card(card_id, pile_id)
            return

        move_visuals, flip_visual = self._capture_move_visuals(
            self._selected_card_id, self._selected_pile_id
        )
        try:
            if self._selected_pile_id == "waste":
                self.engine.move_waste_to_tableau(pile_id)
            elif self._selected_pile_id and self._selected_pile_id.startswith("tableau-"):
                self.engine.move_tableau_to_tableau(
                    self._selected_pile_id, self._selected_card_id, pile_id
                )
            else:
                self._set_status("This card cannot be moved from that pile.", error=True)
                return
        except (InvalidMoveError, ValueError, RuntimeError) as error:
            self._set_status(str(error), error=True)
            return

        self._mark_player_action()
        self._clear_selection()
        self._set_status("Move completed.")
        self._refresh_board()
        self._animate_transitions(move_visuals, flip_visual)

    def _select_card(self, card_id: str, pile_id: str) -> None:
        self._selected_card_id = card_id
        self._selected_pile_id = pile_id
        self._set_status(f"Selected {card_id}. Now choose a legal destination.")
        self._refresh_board()

    def _empty_tableau_selected(self, column_id: str) -> None:
        if self._selected_card_id is None:
            self._set_status("Select a King-led face-up sequence first.", error=True)
            return
        move_visuals, flip_visual = self._capture_move_visuals(
            self._selected_card_id, self._selected_pile_id
        )
        if self._selected_pile_id == "waste":
            try:
                self.engine.move_waste_to_tableau(column_id)
            except (InvalidMoveError, ValueError, RuntimeError) as error:
                self._set_status(str(error), error=True)
                return
        elif self._selected_pile_id and self._selected_pile_id.startswith("tableau-"):
            try:
                self.engine.move_tableau_to_tableau(
                    self._selected_pile_id, self._selected_card_id, column_id
                )
            except (InvalidMoveError, ValueError, RuntimeError) as error:
                self._set_status(str(error), error=True)
                return
        else:
            self._set_status("That source cannot move to a tableau column.", error=True)
            return

        self._mark_player_action()
        self._clear_selection()
        self._set_status("Move completed.")
        self._refresh_board()
        self._animate_transitions(move_visuals, flip_visual)

    def _foundation_selected(self, suit: Suit) -> None:
        if self._selected_card_id is None or self._selected_pile_id is None:
            self._set_status(f"Select a card to place on the {suit.value} foundation.")
            return

        move_visuals, flip_visual = self._capture_move_visuals(
            self._selected_card_id, self._selected_pile_id
        )
        try:
            if self._selected_pile_id == "waste":
                self.engine.move_waste_to_foundation(suit)
            elif self._selected_pile_id.startswith("tableau-"):
                source = self.engine.state.tableau[self._selected_pile_id]
                if source.is_empty() or source.peek().card_id != self._selected_card_id:
                    self._set_status(
                        "Only the top card of a tableau column can move to a foundation.",
                        error=True,
                    )
                    return
                self.engine.move_tableau_to_foundation(self._selected_pile_id, suit)
            else:
                self._set_status("That source cannot move to a foundation.", error=True)
                return
        except (InvalidMoveError, ValueError, RuntimeError) as error:
            self._set_status(str(error), error=True)
            return

        self._mark_player_action()
        self._clear_selection()
        if self.engine.state.status is GameStatus.WON:
            self._set_status("You won! All 52 cards are in their foundations.")
        else:
            self._set_status(f"Card placed on the {suit.value} foundation.")
        self._refresh_board()
        self._animate_transitions(move_visuals, flip_visual)

    def _capture_history_visuals(self, event, *, redo: bool = False):
        """Capture visible cards before undo/redo so history actions animate too."""
        if event is None:
            return {}
        if event.action_type == "DRAW":
            if redo:
                stock_visual = self._capture_widget_visual(self.stock_button)
                if stock_visual is not None:
                    return {
                        card_id: stock_visual for card_id in event.card_ids
                    }
            return {}

        visuals = {}
        for card_id in event.card_ids:
            button = self._find_card_button(card_id)
            visual = self._capture_widget_visual(button) if button else None
            if visual is not None:
                visuals[card_id] = visual
        return visuals

    def _undo(self) -> None:
        event = self.engine.move_history[-1] if self.engine.move_history else None
        visuals = self._capture_history_visuals(event)
        if not self.engine.undo():
            self._set_status("There is no move to undo.")
            return
        self._sync_clock_with_game_status()
        self._hint_index = 0
        self._clear_selection()
        self._set_status("Last move undone.")
        self._refresh_board()
        self._animate_move_visuals(visuals)

    def _redo(self) -> None:
        redo_snapshot = (
            self.engine.redo_stack.peek()
            if self.engine.can_redo else None
        )
        event = redo_snapshot.last_move_event if redo_snapshot else None
        visuals = self._capture_history_visuals(event, redo=True)
        if not self.engine.redo():
            self._set_status("There is no move to redo.")
            return
        self._sync_clock_with_game_status()
        self._hint_index = 0
        self._clear_selection()
        self._set_status("Last move redone.")
        self._refresh_board()
        self._animate_move_visuals(visuals)

    def _new_game(self) -> None:
        if (
            self.engine.state.move_count
            or self.engine.can_undo
            or self.engine.can_redo
            or self.engine.state.score
            or self._elapsed_seconds()
        ):
            answer = QMessageBox.question(
                self,
                "Start a new game?",
                "Your current game, score, and move history will be discarded. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer is not QMessageBox.StandardButton.Yes:
                return

        draw_count = self.draw_mode_combo.currentData()
        tracker = OperationTracker()
        self.engine = GameEngine(
            create_new_game(draw_count=draw_count, tracker=tracker), tracker
        )
        self._elapsed_base = 0.0
        self._clock_started_at = None
        self._clock_activated = False
        self._hint_index = 0
        self._update_clock_display()
        self._clear_selection()
        self._clear_drag_preview()
        self._set_status("New shuffled game started.")
        self._refresh_board()

    def _show_hint(self) -> None:
        """Select the source card for the next highest-priority legal hint."""
        hints = self.engine.find_hints()
        if not hints:
            self._clear_selection()
            self._refresh_board()
            self._set_status("No legal moves are available. Start a new game.")
            return

        self._hint_index %= len(hints)
        hint_number = self._hint_index + 1
        hint = hints[self._hint_index]
        self._hint_index = (self._hint_index + 1) % len(hints)

        self._clear_selection()
        if hint.source_pile == "stock":
            self._refresh_board()
            self._set_status(
                f"Hint: {hint.description} Click the Stock pile."
            )
            return

        if hint.card_ids and (
            hint.source_pile == "waste"
            or hint.source_pile.startswith("tableau-")
        ):
            self._selected_card_id = hint.card_ids[0]
            self._selected_pile_id = hint.source_pile

        self._refresh_board()
        self._set_status(
            f"Hint {hint_number}/{len(hints)}: {hint.description} "
            "The source card is selected; choose the suggested destination."
        )

    def _install_shortcuts(self) -> None:
        """Provide keyboard alternatives for the most common game actions."""
        shortcuts = (
            ("Undo", "Ctrl+Z", self._undo),
            ("Redo", "Ctrl+Y", self._redo),
            ("New Game", "Ctrl+N", self._new_game),
            ("Hint", "H", self._show_hint),
            ("Draw Stock", "Space", self._draw_stock),
        )
        self._shortcut_actions: list[QAction] = []
        for title, sequence, callback in shortcuts:
            action = QAction(title, self)
            action.setShortcut(QKeySequence(sequence))
            action.triggered.connect(callback)
            self.addAction(action)
            self._shortcut_actions.append(action)

    def _start_drag_preview(self, card_id: str, source_pile: str) -> None:
        """Highlight only destinations present in the engine's legal hint list."""
        destinations = {
            hint.destination_pile
            for hint in self.engine.find_hints()
            if hint.source_pile == source_pile
            and hint.card_ids
            and hint.card_ids[0] == card_id
        }
        self._drag_destinations = destinations
        for column_id, widget in self._tableau_widgets.items():
            widget.set_drag_highlight(column_id in destinations)
        for suit, widget in self._foundation_widgets.items():
            widget.set_drag_highlight(
                f"foundation-{suit.code.lower()}" in destinations
            )

    def _clear_drag_preview(self) -> None:
        self._drag_destinations.clear()
        for widget in self._tableau_widgets.values():
            widget.set_drag_highlight(False)
        for widget in self._foundation_widgets.values():
            widget.set_drag_highlight(False)

    def _handle_drop(
        self, card_id: str, source_pile: str, destination_pile: str
    ) -> None:
        """Route a drag/drop through the same validated engine methods as clicks."""
        if source_pile == destination_pile:
            self._set_status("Choose a different destination.", error=True)
            return

        move_visuals, flip_visual = self._capture_move_visuals(
            card_id, source_pile
        )
        try:
            if destination_pile.startswith("tableau-"):
                if source_pile == "waste":
                    self.engine.move_waste_to_tableau(destination_pile)
                elif source_pile.startswith("tableau-"):
                    self.engine.move_tableau_to_tableau(
                        source_pile, card_id, destination_pile
                    )
                else:
                    self._set_status(
                        "Cards can only move from Waste or Tableau to Tableau.",
                        error=True,
                    )
                    return
            elif destination_pile.startswith("foundation-"):
                suit = next(
                    (
                        item for item in Suit
                        if destination_pile == f"foundation-{item.code.lower()}"
                    ),
                    None,
                )
                if suit is None:
                    self._set_status("Unknown foundation destination.", error=True)
                    return
                if source_pile == "waste":
                    self.engine.move_waste_to_foundation(suit)
                elif source_pile.startswith("tableau-"):
                    source = self.engine.state.tableau[source_pile]
                    if source.is_empty() or source.peek().card_id != card_id:
                        self._set_status(
                            "Only the top tableau card can move to a foundation.",
                            error=True,
                        )
                        return
                    self.engine.move_tableau_to_foundation(source_pile, suit)
                else:
                    self._set_status(
                        "Cards can only move from Waste or Tableau to a foundation.",
                        error=True,
                    )
                    return
            else:
                self._set_status("That is not a valid drop target.", error=True)
                return
        except (InvalidMoveError, ValueError, RuntimeError) as error:
            self._set_status(str(error), error=True)
            return

        self._mark_player_action()
        self._clear_selection()
        self._clear_drag_preview()
        self._set_status("Card dropped successfully.")
        self._refresh_board()
        self._animate_transitions(move_visuals, flip_visual)

    def _find_card_button(self, card_id: str) -> CardButton | None:
        for button in self.waste_widget.card_buttons:
            if button.card_id == card_id:
                return button
        for widget in self._tableau_widgets.values():
            for button in widget.card_buttons:
                if button.card_id == card_id:
                    return button
        for slot in self._foundation_widgets.values():
            button = slot._button
            if isinstance(button, CardButton) and button.card_id == card_id:
                return button
        return None

    def _widget_rect_in_board(self, widget: QWidget) -> QRect:
        return QRect(
            widget.mapTo(self.centralWidget(), QPoint(0, 0)),
            widget.size(),
        )

    def _capture_widget_visual(
        self, widget: QWidget
    ) -> tuple[object, QRect] | None:
        if not widget.isVisible():
            return None
        return widget.grab(), self._widget_rect_in_board(widget)

    def _capture_move_visuals(
        self, card_id: str, source_pile: str | None
    ) -> tuple[dict[str, tuple[object, QRect]], tuple[str, object, QRect] | None]:
        """Capture the cards before a model mutation so UI motion has real endpoints."""
        card_ids = [card_id]
        flip_visual = None
        if source_pile and source_pile.startswith("tableau-"):
            column = self.engine.state.tableau.get(source_pile)
            cards = column.cards_bottom_to_top() if column else []
            index = next(
                (i for i, card in enumerate(cards) if card.card_id == card_id),
                None,
            )
            if index is not None:
                card_ids = [card.card_id for card in cards[index:]]
                if index > 0 and not cards[index - 1].face_up:
                    exposed = cards[index - 1]
                    button = self._find_card_button(exposed.card_id)
                    visual = self._capture_widget_visual(button) if button else None
                    if visual is not None:
                        flip_visual = (exposed.card_id, visual[0], visual[1])

        visuals: dict[str, tuple[object, QRect]] = {}
        for moving_id in card_ids:
            button = self._find_card_button(moving_id)
            visual = self._capture_widget_visual(button) if button else None
            if visual is not None:
                visuals[moving_id] = visual
        return visuals, flip_visual

    def _animate_transitions(
        self,
        move_visuals: dict[str, tuple[object, QRect]],
        flip_visual: tuple[str, object, QRect] | None,
    ) -> None:
        if self.reduce_motion_check.isChecked() or not self.isVisible():
            return
        QTimer.singleShot(
            0,
            lambda: self._start_animations(move_visuals, flip_visual),
        )

    def _animate_move_visuals(
        self, visuals: dict[str, tuple[object, QRect]]
    ) -> None:
        self._animate_transitions(visuals, None)

    def _start_animations(
        self,
        move_visuals: dict[str, tuple[object, QRect]],
        flip_visual: tuple[str, object, QRect] | None,
    ) -> None:
        if flip_visual is not None:
            self._start_flip_animation(*flip_visual)
        for index, (card_id, visual) in enumerate(move_visuals.items()):
            QTimer.singleShot(
                index * 24,
                lambda current_id=card_id, current_visual=visual:
                    self._start_card_animation(current_id, *current_visual),
            )

    def _start_card_animation(
        self, card_id: str, pixmap, start_rect: QRect
    ) -> None:
        target = self._find_card_button(card_id)
        if target is None or not target.isVisible():
            return
        end_rect = self._widget_rect_in_board(target)
        target.hide()
        overlay = QLabel(self.centralWidget())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.setPixmap(pixmap)
        overlay.setScaledContents(True)
        overlay.setStyleSheet(
            "border: 2px solid #F5C84C; border-radius: 8px; background: transparent;"
        )
        overlay.setGeometry(start_rect)
        overlay.show()
        overlay.raise_()
        animation = QPropertyAnimation(overlay, b"geometry", self)
        animation.setDuration(220)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(
            lambda: self._finish_card_animation(overlay, target, animation)
        )
        self._active_animations.append(animation)
        animation.start()

    def _finish_card_animation(
        self, overlay: QLabel, target: QWidget, animation: QPropertyAnimation
    ) -> None:
        target.show()
        overlay.deleteLater()
        if animation in self._active_animations:
            self._active_animations.remove(animation)

    def _start_flip_animation(
        self, card_id: str, back_pixmap, start_rect: QRect
    ) -> None:
        target = self._find_card_button(card_id)
        if target is None or not target.isVisible():
            return
        front_pixmap = target.grab()
        end_rect = self._widget_rect_in_board(target)
        target.hide()

        overlay = QLabel(self.centralWidget())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.setPixmap(back_pixmap)
        overlay.setScaledContents(True)
        overlay.setStyleSheet(
            "border: 2px solid #F5C84C; border-radius: 8px; background: transparent;"
        )
        overlay.setGeometry(start_rect)
        overlay.show()
        overlay.raise_()

        narrow_rect = QRect(
            start_rect.center().x(), start_rect.y(), 1, start_rect.height()
        )
        first = QPropertyAnimation(overlay, b"geometry", self)
        first.setDuration(90)
        first.setStartValue(start_rect)
        first.setEndValue(narrow_rect)
        first.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def reveal_front() -> None:
            overlay.setPixmap(front_pixmap)
            overlay.setGeometry(
                QRect(end_rect.center().x(), end_rect.y(), 1, end_rect.height())
            )
            second = QPropertyAnimation(overlay, b"geometry", self)
            second.setDuration(90)
            second.setStartValue(overlay.geometry())
            second.setEndValue(end_rect)
            second.setEasingCurve(QEasingCurve.Type.InOutCubic)
            second.finished.connect(
                lambda: self._finish_card_animation(overlay, target, second)
            )
            self._active_animations.append(second)
            second.start()
            if first in self._active_animations:
                self._active_animations.remove(first)

        first.finished.connect(reveal_front)
        self._active_animations.append(first)
        first.start()

    def _elapsed_seconds(self) -> int:
        elapsed = self._elapsed_base
        if self._clock_started_at is not None:
            elapsed += max(0.0, monotonic() - self._clock_started_at)
        return max(0, int(elapsed))

    @staticmethod
    def _format_elapsed_time(seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _update_clock_display(self) -> None:
        elapsed = self._elapsed_seconds()
        self.engine.state.elapsed_seconds = elapsed
        if hasattr(self, "timer_label"):
            self.timer_label.setText(
                f"TIME  {self._format_elapsed_time(elapsed)}"
            )
        # DEBUG ISOLATION: skip dashboard timer refresh during action signal handling.
        if False and hasattr(self, "dsa_monitor"):
            self.dsa_monitor.refresh_stats(self.engine)

    def _mark_player_action(self) -> None:
        """Start the clock after the first successful move and stop on victory."""
        if not self._clock_activated:
            self._clock_activated = True
            self._clock_started_at = monotonic()
        if self.engine.state.status is GameStatus.WON:
            self._pause_clock()
        self._hint_index = 0
        self._update_clock_display()

    def _pause_clock(self) -> None:
        if self._clock_started_at is not None:
            self._elapsed_base = float(self._elapsed_seconds())
            self._clock_started_at = None
        self.engine.state.elapsed_seconds = int(self._elapsed_base)
        self._update_clock_display()

    def _sync_clock_with_game_status(self) -> None:
        if self.engine.state.status is GameStatus.WON:
            self._pause_clock()
        elif self._clock_activated and self._clock_started_at is None:
            self._clock_started_at = monotonic()
            self._update_clock_display()
        else:
            self._update_clock_display()

    def _clear_selection(self) -> None:
        self._selected_card_id = None
        self._selected_pile_id = None

    def _set_status(self, message: str, *, error: bool = False) -> None:
        self.status_label.setText(message)
        if error:
            self.feedback_title_label.setText("Move Needs Attention")
            self.feedback_icon_label.setText("!")
            self.feedback_icon_label.setStyleSheet(
                "background: #B62B3C; color: white; border: 1px solid #FF9AA5; "
                "border-radius: 15px; font-size: 20px; font-weight: 900;"
            )
            self.feedback_panel.setStyleSheet(
                "QFrame#feedback-panel { background: #3B1723; "
                "border: 2px solid #E15C6C; border-radius: 14px; }"
            )
            self.status_label.setStyleSheet(
                "background: transparent; color: #FFE6E9; border: none; font-size: 11px; padding: 3px 4px;"
            )
        else:
            title = (
                "Great Move!" if message in ("Move completed.", "Card dropped successfully.")
                else "Stock Updated" if message.startswith("Drew ")
                else "Hint" if message.lower().startswith("hint")
                else "Game Status"
            )
            self.feedback_title_label.setText(title)
            self.feedback_icon_label.setText("✓")
            self.feedback_icon_label.setStyleSheet(
                "background: #23B948; color: white; border: 1px solid #A7FF9A; "
                "border-radius: 15px; font-size: 20px; font-weight: 900;"
            )
            self.feedback_panel.setStyleSheet(
                "QFrame#feedback-panel { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
                "stop:0 rgba(14, 90, 52, 238), stop:1 rgba(5, 49, 34, 245)); "
                "border: 2px solid #78E95D; border-radius: 14px; }"
            )
            self.status_label.setStyleSheet(
                "background: transparent; color: #F4FFF5; border: none; font-size: 11px; padding: 3px 4px;"
            )

    def _refresh_board(self) -> None:
        state = self.engine.state
        self.stock_button.set_stock(state.stock.size(), not state.waste.is_empty())
        self.waste_widget.set_cards(state.waste.to_list())

        for suit, slot in self._foundation_widgets.items():
            pile = state.foundations[suit]
            slot.set_card(None if pile.is_empty() else pile.peek())

        for column_id, widget in self._tableau_widgets.items():
            widget.set_column(
                state.tableau[column_id],
                self._selected_card_id if self._selected_pile_id == column_id else None,
            )

        self.moves_label.setText(f"MOVES  {state.move_count}")
        self.score_label.setText(f"SCORE  {state.score}")
        self.hint_button.setEnabled(state.status is GameStatus.PLAYING)
        self.undo_button.setEnabled(self.engine.can_undo)
        self.redo_button.setEnabled(self.engine.can_redo)
        self.move_log.clear()
        for event in self.engine.move_history[-8:]:
            self.move_log.addItem(event.description)
        self.move_log.scrollToBottom()
        is_won = state.status is GameStatus.WON
        self.victory_panel.setVisible(is_won)
        if is_won:
            self.victory_label.setText(
                "VICTORY  •  All 52 cards are home.  "
                f"Score: {state.score}  •  Time: "
                f"{self._format_elapsed_time(state.elapsed_seconds)}"
            )
        # DEBUG ISOLATION: skip the monitor refresh to identify the native Qt abort.
        if False and hasattr(self, "dsa_monitor"):
            self.dsa_monitor.refresh(
                self.engine,
                selected_card_id=self._selected_card_id,
                selected_pile_id=self._selected_pile_id,
            )

    def closeEvent(self, event) -> None:
        if hasattr(self, "_clock_timer"):
            self._clock_timer.stop()
        if self._clock_started_at is not None:
            self._pause_clock()
        for animation in tuple(self._active_animations):
            animation.stop()
        event.accept()
        super().closeEvent(event)
