"""Main PyQt6 window for playing Klondike Solitaire."""

from __future__ import annotations

from random import Random

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
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
from solitaire.ui.pile_widgets import (
    CARD_HEIGHT,
    CARD_WIDTH,
    FoundationSlot,
    StockButton,
    TableauColumnWidget,
    WasteWidget,
)


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

        self.setObjectName("klondike-main-window")
        self.setWindowTitle("Klondike Solitaire — CSC200 DSA Edition")
        self.setMinimumSize(1160, 780)
        self.resize(1440, 940)
        self._build_ui()
        self._refresh_board()

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
        self.setStyleSheet(
            "QMainWindow, QWidget#central-widget { background: #071B2B; color: #F4F7FA; }"
            "QLabel { color: #F4F7FA; }"
            "QPushButton { border-radius: 8px; padding: 8px 13px; font-weight: 650; }"
            "QPushButton:focus { border: 2px solid #F5C84C; }"
            "QComboBox { background: #102F46; color: #F4F7FA; border: 1px solid #38576B; "
            "border-radius: 7px; padding: 7px 10px; min-width: 90px; }"
            "QListWidget { background: #0B2438; color: #DDE7EE; border: 1px solid #26445A; "
            "border-radius: 8px; padding: 6px; }"
        )

        central = QWidget()
        central.setObjectName("central-widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        header = QHBoxLayout()
        header.setSpacing(16)
        title_group = QVBoxLayout()
        title_group.setSpacing(3)
        title = QLabel("♠  Klondike Solitaire")
        title.setObjectName("game-title")
        title.setStyleSheet("font-size: 25px; font-weight: 800; color: #FFFFFF;")
        subtitle = QLabel("CSC200  •  Data Structures & Algorithms")
        subtitle.setStyleSheet("font-size: 11px; color: #B9C7D3;")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        header.addLayout(title_group)
        header.addStretch(1)

        self.moves_label = QLabel("MOVES  0")
        self.moves_label.setObjectName("moves-label")
        self.moves_label.setStyleSheet(
            "background: #0B2438; border: 1px solid #26445A; border-radius: 8px; "
            "padding: 9px 12px; font-size: 12px; font-weight: 700;"
        )
        header.addWidget(self.moves_label)

        self.new_game_button = QPushButton("New Game")
        self.new_game_button.setObjectName("new-game-button")
        self.new_game_button.setStyleSheet(
            "QPushButton { background: #0879D1; color: white; }"
            "QPushButton:hover { background: #168BE5; }"
        )
        self.new_game_button.clicked.connect(self._new_game)
        header.addWidget(self.new_game_button)

        self.undo_button = QPushButton("↶ Undo")
        self.undo_button.setObjectName("undo-button")
        self.undo_button.clicked.connect(self._undo)
        header.addWidget(self.undo_button)

        self.redo_button = QPushButton("↷ Redo")
        self.redo_button.setObjectName("redo-button")
        self.redo_button.clicked.connect(self._redo)
        header.addWidget(self.redo_button)
        root.addLayout(header)

        board = QFrame()
        board.setObjectName("game-board")
        board.setStyleSheet(
            "QFrame#game-board { background: #075B35; border: 1px solid #27764D; "
            "border-radius: 14px; }"
        )
        board_layout = QVBoxLayout(board)
        board_layout.setContentsMargins(22, 22, 22, 22)
        board_layout.setSpacing(22)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        self.stock_button = StockButton()
        self.stock_button.clicked.connect(self._draw_stock)
        stock_group = self._pile_group("STOCK", self.stock_button)
        top_row.addWidget(stock_group)

        self.waste_widget = WasteWidget()
        waste_group = self._pile_group("WASTE", self.waste_widget)
        top_row.addWidget(waste_group)
        top_row.addStretch(1)

        for suit in Suit:
            slot = FoundationSlot(suit)
            slot.selected.connect(self._foundation_selected)
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
        tableau_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.AsNeeded)
        tableau_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.AsNeeded)
        tableau_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        tableau_content = QWidget()
        tableau_content.setStyleSheet("background: transparent;")
        tableau_layout = QHBoxLayout(tableau_content)
        tableau_layout.setContentsMargins(0, 0, 0, 0)
        tableau_layout.setSpacing(12)
        tableau_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        for column_number in range(1, 8):
            column_id = f"tableau-{column_number}"
            widget = TableauColumnWidget(column_id)
            widget.card_selected.connect(self._card_selected)
            widget.empty_selected.connect(self._empty_tableau_selected)
            self._tableau_widgets[column_id] = widget
            tableau_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignTop)

        tableau_layout.addStretch(1)
        tableau_scroll.setWidget(tableau_content)
        board_layout.addWidget(tableau_scroll, 1)
        root.addWidget(board, 1)

        footer = QHBoxLayout()
        footer.setSpacing(16)
        draw_group = QHBoxLayout()
        draw_group.setSpacing(8)
        draw_label = QLabel("DRAW MODE")
        draw_label.setStyleSheet("font-size: 10px; font-weight: 800; color: #B9C7D3;")
        self.draw_mode_combo = QComboBox()
        self.draw_mode_combo.setObjectName("draw-mode-combo")
        self.draw_mode_combo.addItem("Draw 1", 1)
        self.draw_mode_combo.addItem("Draw 3", 3)
        self.draw_mode_combo.currentIndexChanged.connect(self._draw_mode_changed)
        draw_group.addWidget(draw_label)
        draw_group.addWidget(self.draw_mode_combo)
        footer.addLayout(draw_group)

        self.status_label = QLabel("Select a face-up card, then select a destination.")
        self.status_label.setObjectName("game-status")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "background: #0B2438; color: #DCE7EE; border: 1px solid #26445A; "
            "border-radius: 8px; padding: 10px 14px;"
        )
        footer.addWidget(self.status_label, 1)
        root.addLayout(footer)

        log_panel = QFrame()
        log_panel.setObjectName("move-log-panel")
        log_panel.setStyleSheet(
            "QFrame#move-log-panel { background: #0B2438; border: 1px solid #26445A; "
            "border-radius: 10px; }"
        )
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(14, 10, 14, 10)
        log_layout.setSpacing(6)
        log_title = QLabel("MOVE LOG")
        log_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #B9C7D3;")
        self.move_log = QListWidget()
        self.move_log.setObjectName("move-log")
        self.move_log.setMaximumHeight(92)
        self.move_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.move_log)
        root.addWidget(log_panel)

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
        try:
            drawn = self.engine.draw_from_stock()
        except NoCardsAvailableError as error:
            self._set_status(str(error), error=True)
            return
        except RuntimeError as error:
            self._set_status(str(error), error=True)
            return

        self._clear_selection()
        self._set_status(f"Drew {len(drawn)} card(s). Select the top waste card to move it.")
        self._refresh_board()

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

        self._clear_selection()
        self._set_status("Move completed.")
        self._refresh_board()

    def _select_card(self, card_id: str, pile_id: str) -> None:
        self._selected_card_id = card_id
        self._selected_pile_id = pile_id
        self._set_status(f"Selected {card_id}. Now choose a legal destination.")
        self._refresh_board()

    def _empty_tableau_selected(self, column_id: str) -> None:
        if self._selected_card_id is None:
            self._set_status("Select a King-led face-up sequence first.", error=True)
            return
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

        self._clear_selection()
        self._set_status("Move completed.")
        self._refresh_board()

    def _foundation_selected(self, suit: Suit) -> None:
        if self._selected_card_id is None or self._selected_pile_id is None:
            self._set_status(f"Select a card to place on the {suit.value} foundation.")
            return

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

        self._clear_selection()
        if self.engine.state.status is GameStatus.WON:
            self._set_status("You won! All 52 cards are in their foundations.")
        else:
            self._set_status(f"Card placed on the {suit.value} foundation.")
        self._refresh_board()

    def _undo(self) -> None:
        if not self.engine.undo():
            self._set_status("There is no move to undo.")
            return
        self._clear_selection()
        self._set_status("Last move undone.")
        self._refresh_board()

    def _redo(self) -> None:
        if not self.engine.redo():
            self._set_status("There is no move to redo.")
            return
        self._clear_selection()
        self._set_status("Last move redone.")
        self._refresh_board()

    def _new_game(self) -> None:
        draw_count = self.draw_mode_combo.currentData()
        tracker = OperationTracker()
        self.engine = GameEngine(
            create_new_game(draw_count=draw_count, tracker=tracker), tracker
        )
        self._clear_selection()
        self._set_status("New shuffled game started.")
        self._refresh_board()

    def _clear_selection(self) -> None:
        self._selected_card_id = None
        self._selected_pile_id = None

    def _set_status(self, message: str, *, error: bool = False) -> None:
        color = "#FFD4D8" if error else "#DCE7EE"
        border = "#A83A4D" if error else "#26445A"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"background: #0B2438; color: {color}; border: 1px solid {border}; "
            "border-radius: 8px; padding: 10px 14px;"
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
        self.undo_button.setEnabled(self.engine.can_undo)
        self.redo_button.setEnabled(self.engine.can_redo)
        self.move_log.clear()
        for event in self.engine.move_history[-8:]:
            self.move_log.addItem(event.description)
        self.move_log.scrollToBottom()
