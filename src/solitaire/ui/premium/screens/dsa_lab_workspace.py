"""DSA Lab workspace: full-width academic inspection environment."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.controllers.game_controller import GameController
from solitaire.ui.premium.dsa_lab.array_inspector import ArrayInspector
from solitaire.ui.premium.dsa_lab.dictionary_inspector import DictionaryInspector
from solitaire.ui.premium.dsa_lab.game_stats_page import GameStatsPage
from solitaire.ui.premium.dsa_lab.linked_list_inspector import LinkedListInspector
from solitaire.ui.premium.dsa_lab.operation_timeline import OperationTimeline
from solitaire.ui.premium.dsa_lab.overview_page import OverviewPage
from solitaire.ui.premium.dsa_lab.queue_inspector import QueueInspector
from solitaire.ui.premium.dsa_lab.stack_inspector import StackInspector
from solitaire.ui.premium.navigation import LabPage


def _scrollable(page: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(page)
    return scroll


class DsaLabWorkspace(QWidget):
    """Dedicated DSA Lab screen with independently scrollable inspectors."""

    def __init__(self, game: GameController, on_back, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._pages: dict[LabPage, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("labTopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)
        top_layout.setSpacing(10)

        self.back_button = QPushButton("  ← Back to Game")
        self.back_button.setObjectName("goldButton")
        self.back_button.clicked.connect(on_back)
        back_row = QHBoxLayout()
        back_row.setSpacing(10)
        back_row.addWidget(self.back_button)

        # The flask emblem ties the lab back to the Open DSA Lab affordance
        # on the Play sidebar — entering the lab reads as the same app.
        emblem = QLabel()
        emblem.setPixmap(icon_pixmap("flask", 22))
        emblem.setFixedSize(24, 24)
        emblem.setScaledContents(True)
        back_row.addWidget(emblem)

        title = QLabel("DSA Lab — CSC200 Data Structure Inspection")
        title.setObjectName("appTitle")
        back_row.addSpacing(4)
        back_row.addWidget(title)
        back_row.addStretch(1)
        top_layout.addLayout(back_row)
        layout.addWidget(top_bar)

        tab_row = QWidget()
        tab_row.setObjectName("labTabRow")
        tab_layout = QHBoxLayout(tab_row)
        tab_layout.setContentsMargins(16, 8, 16, 8)
        tab_layout.setSpacing(8)

        self._buttons: dict[LabPage, QPushButton] = {}
        for page in LabPage:
            button = QPushButton(_LABELS[page])
            button.setObjectName("labTab")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, p=page: self.show_page(p))
            self._buttons[page] = button
            tab_layout.addWidget(button)
        tab_layout.addStretch(1)
        layout.addWidget(tab_row)

        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack, 1)

        self._register(LabPage.OVERVIEW, OverviewPage(game, on_inspect=self.show_page))
        self._register(LabPage.ARRAY, ArrayInspector(game))
        self._register(LabPage.STACK, StackInspector(game))
        self._register(LabPage.QUEUE, QueueInspector(game))
        self._register(LabPage.LINKED_LIST, LinkedListInspector(game))
        self._register(LabPage.DICTIONARY, DictionaryInspector(game))
        self._register(LabPage.TIMELINE, OperationTimeline(game))
        self._register(LabPage.STATS, GameStatsPage(game))

        self.show_page(LabPage.OVERVIEW)

    def _register(self, page_id: LabPage, page: QWidget) -> None:
        self._pages[page_id] = page
        self.stack.addWidget(_scrollable(page))

    def show_page(self, page_id: LabPage) -> None:
        for page, button in self._buttons.items():
            button.setChecked(page is page_id)
        self.stack.setCurrentIndex(list(self._pages).index(page_id))
        self.refresh()

    def current_page(self) -> LabPage:
        index = self.stack.currentIndex()
        return list(self._pages)[index]

    def refresh(self) -> None:
        for page in self._pages.values():
            if hasattr(page, "refresh"):
                page.refresh()


_LABELS = {
    LabPage.OVERVIEW: "Overview",
    LabPage.ARRAY: "Array / List",
    LabPage.STACK: "Stack",
    LabPage.QUEUE: "Queue",
    LabPage.LINKED_LIST: "Linked List",
    LabPage.DICTIONARY: "Dictionary",
    LabPage.TIMELINE: "Timeline",
    LabPage.STATS: "Game Stats",
}
