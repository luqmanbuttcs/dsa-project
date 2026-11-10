"""Fixed right-side premium DSA dashboard for the Play Workspace.

Presents the five required data structures with custom icons, live
operation-count badges derived from the real OperationTracker, a
player-facing Latest Operation panel, a refined vertical Recent Player
Moves timeline, and a polished foundation-progress component. A dedicated
inspect affordance per structure jumps straight into its DSA Lab page.

The **Open DSA Lab** action is pinned as the sidebar's footer: it sits
directly below Game Progress when the panels fit the viewport and stays
fully visible (no scrolling) when the window is short — mandatory at the
1280×800 minimum size.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.components.common.controls import PanelCard
from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.controllers.game_controller import GameController, describe_move
from solitaire.ui.premium.dsa_lab.data_provider import latest_player_operation, structure_counts
from solitaire.ui.premium.navigation import LabPage
from solitaire.ui.premium.theme import DASHBOARD_WIDTH, GOLD_TEXT, TEXT_MUTED

STRUCTURE_ROWS = [
    ("Array / List", "Deck management", "array", LabPage.ARRAY, "#E8C766"),
    ("Stack", "Waste, tableau, foundations", "stack", LabPage.STACK, "#7FB5A3"),
    ("Queue", "Stock (FIFO)", "queue", LabPage.QUEUE, "#8FB4E3"),
    ("Linked List", "Tableau node chains", "linkedlist", LabPage.LINKED_LIST, "#D9A0C0"),
    ("Dictionary", "Card location index", "dictionary", LabPage.DICTIONARY, "#C8B37E"),
]

PLAYER_OPERATION_LABELS = {
    "DRAW": "Drew from the Stock",
    "DEQUEUE": "Stock → Waste (dequeue)",
    "ENQUEUE": "Waste recycled to Stock",
    "PUSH": "Card pushed onto a pile",
    "POP": "Card taken from a pile top",
    "APPEND_NODE": "Tableau chain extended",
    "REMOVE_TOP_NODE": "Top node removed",
    "DETACH_RUN": "Run detached from a column",
    "ATTACH_RUN": "Run attached to a column",
    "SET": "Card index updated",
    "UPDATE": "Card index updated",
    "CREATE_DECK": "Deck created",
    "SHUFFLE": "Deck shuffled",
    "POP_FOR_DEAL": "Dealing the tableau",
    "CLEAR_AFTER_DEAL": "Deck list cleared after deal",
    "INITIAL_DEAL_COMPLETE": "Initial deal complete",
    "WASTE_RECYCLED": "Waste recycled into the Stock",
}


def _panel(title: str, icon_name: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Shared premium panel (delegates to the design system)."""
    panel = PanelCard(title, icon_name)
    return panel, panel.body()


def _body(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("panelBody")
    label.setWordWrap(True)
    return label


class StructureBadge(QLabel):
    """Small gold count badge (rounded pill)."""

    def __init__(self, parent=None) -> None:
        super().__init__("0", parent)
        self.setObjectName("countBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(40, 22)

    def set_count(self, count: int) -> None:
        self.setText(str(count))


class StructureRow(QPushButton):
    """One data-structure row: icon chip, titles, live count badge."""

    def __init__(self, title: str, subtitle: str, icon_name: str, accent: str,
                 on_open, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("structureRow")
        self.setCursor(self.cursor())
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Minimum, not fixed: at Windows-style DPI the platform renders every
        # font 1.5x larger in logical pixels, and a wrapped subtitle then
        # needs a taller row. Rows grow; the sidebar scrolls vertically.
        self.setMinimumHeight(44)
        self._accent = accent
        self._icon_name = icon_name
        self._on_open = on_open
        self.clicked.connect(lambda: on_open())

        self.badge = StructureBadge()

        self.icon_chip = QLabel()
        self.icon_chip.setFixedSize(30, 30)
        self.icon_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_chip.setObjectName("structureIconChip")

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {GOLD_TEXT}; font-weight: bold; font-size: 13px; background: transparent;"
        )
        # Wrap: a label's minimum width must be its longest WORD, never its
        # full text — otherwise high-DPI font scaling (Windows renders every
        # px font size at logicalDpi/96 x) pushes the scroll content wider
        # than the viewport and, with the horizontal scrollbar AlwaysOff,
        # silently clips the right edge of every panel.
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        self.subtitle_label.setWordWrap(True)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(1)
        text_column.addWidget(self.title_label)
        text_column.addWidget(self.subtitle_label)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(10)
        row.addWidget(self.icon_chip)
        row.addLayout(text_column, 1)
        row.addWidget(self.badge)

    def refresh_icon(self) -> None:
        self.icon_chip.setPixmap(icon_pixmap(self._icon_name, 19, QColor(self._accent)))

    def set_counts(self, count: int) -> None:
        self.badge.set_count(count)


class TimelineRow(QWidget):
    """One entry of the Recent Player Moves timeline."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(22)
        self._text = ""
        self._time = ""
        self._kind = "success"

    def set_data(self, text: str, time_text: str, kind: str = "success") -> None:
        self._text = text
        self._time = time_text
        self._kind = kind
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor(55, 185, 110) if self._kind == "success" else QColor(224, 85, 85)
        x = 9.0
        # Timeline spine and node.
        painter.setPen(QPen(QColor(140, 115, 38, 90), 1.6))
        painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, self.height() / 2), 3.4, 3.4)

        font = QFont("DejaVu Sans")
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#F2EEE2")))
        painter.drawText(QRectF(22, 0, self.width() - 78, self.height()),
                         Qt.AlignmentFlag.AlignVCenter, self._text)
        painter.setPen(QPen(QColor("#9FB0C6")))
        painter.drawText(
            QRectF(self.width() - 56, 0, 52, self.height()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            self._time,
        )


class DsaDashboard(QWidget):
    """Compact live summary of the five data structures and recent play.

    A scrollable panel column with the Open DSA Lab button pinned beneath
    it as a footer — the button never scrolls out of view.
    """

    def __init__(self, game: GameController, on_open_lab, parent=None) -> None:
        super().__init__(parent)
        self._game = game
        self._on_open_lab = on_open_lab
        self.setObjectName("dashboardContent")
        self.setFixedWidth(DASHBOARD_WIDTH)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(self._scroll, 1)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        # --- overview -------------------------------------------------------
        overview_frame, overview_layout = _panel("DSA Overview — Live Structures", "sparkle")
        self._rows: dict[str, StructureRow] = {}
        for name, subtitle, icon_name, page, accent in STRUCTURE_ROWS:
            row = StructureRow(
                name, subtitle, icon_name, accent,
                lambda page=page: self._on_open_lab(page),
            )
            row.refresh_icon()
            self._rows[name] = row
            overview_layout.addWidget(row)
        note = _body("Live counts from the real OperationTracker.")
        overview_layout.addWidget(note)
        layout.addWidget(overview_frame)

        # --- latest player-facing operation ----------------------------------
        latest_frame, latest_layout = _panel("Latest Operation", "bolt" if False else "swap")
        self._latest_title = QLabel("Ready")
        self._latest_title.setStyleSheet(
            f"color: {GOLD_TEXT}; font-weight: bold; font-size: 13px; background: transparent;"
        )
        # Dynamic content ("<structure>" after real moves): the minimum width
        # must stay word-bounded for the same high-DPI reason as above.
        self._latest_title.setWordWrap(True)
        self._latest_body = QLabel("Deal complete — the table is set.")
        self._latest_body.setObjectName("panelBody")
        # The body text is dynamic (operation label + pile id) and platform
        # fonts substitute differently, so the label must wrap: a single-line
        # label would push the scroll content wider than the viewport — with
        # the horizontal scrollbar policy AlwaysOff that silently makes the
        # right edge of every panel (Game Progress included) unreachable.
        # The history panel below absorbs spare height and the sidebar scrolls
        # when the window is short, so an extra wrapped line cannot clip
        # anything.
        self._latest_body.setWordWrap(True)
        latest_layout.addWidget(self._latest_title)
        latest_layout.addWidget(self._latest_body)
        layout.addWidget(latest_frame)

        # --- recent player moves (vertical timeline) --------------------------
        # Five rows: the full mid-game sidebar (overview + latest + history +
        # progress) must fit the 1600x900 viewport without scrolling; more
        # slots pushed Game Progress behind the pinned footer.
        history_frame, history_layout = _panel("Recent Player Moves", "clock")
        self._history_rows = [TimelineRow() for _ in range(5)]
        self._history_empty = QLabel("No moves yet — the table is fresh.")
        self._history_empty.setObjectName("mutedText")
        # Wrap like every other free-text label: platform font substitution
        # must never be able to push the content wider than the viewport.
        self._history_empty.setWordWrap(True)
        for row in self._history_rows:
            history_layout.addWidget(row)
        history_layout.addWidget(self._history_empty)
        history_layout.addStretch(1)
        # The history panel absorbs any spare sidebar height so Game Progress
        # (and the pinned Open DSA Lab button below it) stay visually adjacent
        # at every window size instead of drifting apart.
        layout.addWidget(history_frame, 1)

        # --- foundation progress ----------------------------------------------
        progress_frame, progress_layout = _panel("Game Progress", "trophy")
        self._progress = ProgressMeter()
        self._progress_text = QLabel("0 / 52 cards in Foundations")
        self._progress_text.setObjectName("mutedText")
        # Wrap like the other free-text labels: at 150% DPI the platform
        # font is 1.5x wider in logical px and this label demanded 244px —
        # the second-widest overflow contributor after the panel titles.
        self._progress_text.setWordWrap(True)
        progress_layout.addWidget(self._progress)
        progress_layout.addWidget(self._progress_text)
        layout.addWidget(progress_frame)

        self._scroll.setWidget(content)

        # --- pinned footer: Open DSA Lab (mandatory) --------------------------
        # Outside the scroll area: directly below Game Progress when the
        # panels fit, and still fully visible when they must scroll.
        footer = QWidget()
        footer.setObjectName("dashboardFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 10, 12, 12)
        footer_layout.setSpacing(0)
        self.open_lab_button = QPushButton("  Open DSA Lab")
        self.open_lab_button.setObjectName("openLabButton")
        self.open_lab_button.setIcon(_flask_icon())
        self.open_lab_button.setMinimumHeight(44)
        self.open_lab_button.clicked.connect(lambda: self._on_open_lab(None))
        footer_layout.addWidget(self.open_lab_button)
        outer.addWidget(footer)

        self.refresh()

    # --- refresh ------------------------------------------------------------------
    def refresh(self) -> None:
        counts = structure_counts(self._game.tracker)
        for (name, _subtitle, _icon, _page, _accent), row in zip(STRUCTURE_ROWS, self._rows.values()):
            row.set_counts(counts.get(name, 0))

        latest = latest_player_operation(self._game.tracker)
        if latest is not None:
            friendly = PLAYER_OPERATION_LABELS.get(latest.operation, latest.operation.replace("_", " ").title())
            self._latest_title.setText(f"{latest.structure.value}")
            self._latest_body.setText(
                friendly + (f" · {latest.pile_id.replace('-', ' ').title()}" if latest.pile_id else "")
            )
        else:
            self._latest_title.setText("Ready")
            self._latest_body.setText("Deal complete — the table is set.")

        minutes, seconds = divmod(self._game.elapsed_seconds, 60)
        clock_text = f"{minutes:02d}:{seconds:02d}"
        events = list(reversed(self._game.engine.move_history[-5:]))
        for index, row in enumerate(self._history_rows):
            if index < len(events):
                event = events[index]
                kind = "error" if event.action_type == "MOVE_REJECTED" else "success"
                # Same player-facing notation as the Move Log ('Spades
                # Foundation', 'Column 4') so panels never contradict each other.
                row.set_data(describe_move(event), clock_text, kind)
                row.setVisible(True)
            else:
                row.setVisible(False)
        self._history_empty.setVisible(not events)

        in_foundations, _ = self._game.foundation_progress()
        self._progress.set_value(in_foundations)
        self._progress_text.setText(f"{in_foundations} / 52 cards in Foundations")


class ProgressMeter(QWidget):
    """Gold gradient progress meter with a subtle shine, drawn custom."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(16)
        self._value = 0

    def set_value(self, value: int) -> None:
        self._value = max(0, min(52, int(value)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        from PyQt6.QtGui import QLinearGradient

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(0.5, 1.5, self.width() - 1.5, self.height() - 3.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 7, 7)

        painter.fillPath(path, QColor("#0C1B30"))
        painter.setPen(QPen(QColor("#24395A"), 1.2))
        painter.drawPath(path)

        if self._value > 0:
            fraction = self._value / 52.0
            fill_rect = QRectF(rect.left(), rect.top(), max(10.0, rect.width() * fraction), rect.height())
            fill_path = QPainterPath()
            fill_path.addRoundedRect(fill_rect, 7, 7)
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.bottomLeft())
            gradient.setColorAt(0.0, QColor("#F0C75E"))
            gradient.setColorAt(0.5, QColor("#C9A227"))
            gradient.setColorAt(1.0, QColor("#8C6D1D"))
            painter.fillPath(fill_path, gradient)
            shine = QLinearGradient(fill_rect.topLeft(), fill_rect.bottomLeft())
            shine.setColorAt(0.0, QColor(255, 255, 255, 90))
            shine.setColorAt(0.45, QColor(255, 255, 255, 10))
            shine.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillPath(fill_path, shine)

    def sizeHint(self):  # noqa: N802
        from PyQt6.QtCore import QSize

        return QSize(200, 16)


def _flask_icon():
    from PyQt6.QtGui import QIcon

    return QIcon(icon_pixmap("flask", 20))
