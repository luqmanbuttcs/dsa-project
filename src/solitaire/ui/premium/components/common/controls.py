"""Shared premium controls — one component language for both workspaces.

Everything the Play Workspace sidebar and the DSA Lab pages have in common
lives here so no page carries its own stylesheet: panels, section titles,
filter labels, premium data tables and transparent card strips. All colors
come from the theme tokens; nothing in this module hardcodes a hex value.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.icons import icon_pixmap


class PanelCard(QFrame):
    """Rounded navy panel with an optional gold icon + title heading.

    The shared container for every sidebar panel and lab sub-panel: same
    radius, border, spacing and heading typography everywhere.
    """

    def __init__(self, title: str | None = None, icon_name: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panelCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)
        if title is not None:
            self._layout.addLayout(self.heading_row(title, icon_name))

    @staticmethod
    def heading_row(title: str, icon_name: str | None = None) -> QHBoxLayout:
        """Gold-titled heading row (icon chip + label + stretch)."""
        row = QHBoxLayout()
        row.setSpacing(7)
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap(icon_name, 17))
            icon_label.setFixedSize(18, 18)
            icon_label.setScaledContents(True)
            row.addWidget(icon_label)
        heading = QLabel(title)
        heading.setObjectName("panelTitle")
        row.addWidget(heading)
        row.addStretch(1)
        return row

    def body(self) -> QVBoxLayout:
        return self._layout


class SectionTitle(QLabel):
    """Gold section heading inside a page (15px variant of panelTitle)."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("sectionTitle")


class FilterLabel(QLabel):
    """Muted bold label for filter rows ('Search:', 'Zone:', 'Pile:')."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("filterLabel")


def make_table(columns: list[str], *, stretch_last: bool = True) -> QTableWidget:
    """Premium data table with the shared chrome — no per-page styles.

    Gold headers and alternating navy rows come from the application-wide
    QSS; this factory only fixes the interaction contract (read-only,
    borderless selection) and column behaviour.
    """
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setAlternatingRowColors(True)
    if stretch_last:
        table.horizontalHeader().setStretchLastSection(True)
    return table


def strip_scroll(max_height: int | None = None) -> tuple[QScrollArea, QHBoxLayout]:
    """Transparent horizontal scroller for card strips (deck, FIFO, pile).

    Returns (scroller, strip_layout); add widgets to the layout and they
    scroll horizontally with the chrome invisible.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet("background: transparent; border: none;")
    if max_height is not None:
        scroll.setMaximumHeight(max_height)
    holder = QWidget()
    strip = QHBoxLayout(holder)
    strip.setContentsMargins(0, 0, 0, 0)
    strip.setSpacing(3)
    scroll.setWidget(holder)
    return scroll, strip
