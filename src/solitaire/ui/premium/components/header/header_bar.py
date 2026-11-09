"""Full-width premium application header.

Layout mirrors the approved reference: gold spade logo, serif title and
CSC200 badge on the left; Time / Moves / Score metric chips in the centre;
Hint, Undo, Redo and Settings controls on the right. The header spans the
entire application width, including the area above the dashboard.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.components.header.header_button import HeaderButton
from solitaire.ui.premium.components.header.metric_chip import MetricChip
from solitaire.ui.premium.theme import HEADER_HEIGHT


class SpadeLogo(QWidget):
    """Gold rounded-square spade emblem painted with QPainter."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(48, 48)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(2, 2, 44, 44)

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.fillPath(path, QColor("#C9A227"))
        painter.setPen(QPen(QColor("#8C6D1D"), 1.4))
        painter.drawPath(path)

        spade = icon_pixmap("spade", 30, QColor("#0E1B2E"))
        painter.drawPixmap(
            int(rect.center().x() - 15), int(rect.center().y() - 15), spade
        )


class HeaderBar(QFrame):
    """Full-width navy header with gold accents."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(HEADER_HEIGHT)

        self.logo = SpadeLogo()

        self.title_label = QLabel("Klondike Solitaire")
        self.title_label.setObjectName("appTitle")

        self.badge_label = QLabel("CSC200 DSA Edition")
        self.badge_label.setObjectName("appBadge")

        self.time_chip = MetricChip("stopwatch", "Time", "00:00")
        self.moves_chip = MetricChip("moves", "Moves", "0")
        self.score_chip = MetricChip("trophy", "Score", "0")

        self.hint_button = HeaderButton(
            "Hint", kind="gold", icon="bulb", tooltip="Show a legal move (H)"
        )
        self.undo_button = HeaderButton(
            "Undo", kind="dark", icon="undo", tooltip="Undo the last action (Ctrl+Z)"
        )
        self.redo_button = HeaderButton(
            "Redo", kind="dark", icon="redo", tooltip="Redo an undone action (Ctrl+Y)"
        )
        self.settings_button = HeaderButton(
            "Settings", kind="dark", icon="gear", tooltip="Open settings"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(4)
        layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(6)
        layout.addWidget(self.badge_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)
        layout.addWidget(self.time_chip)
        layout.addSpacing(6)
        layout.addWidget(self.moves_chip)
        layout.addSpacing(6)
        layout.addWidget(self.score_chip)
        layout.addStretch(1)
        layout.addWidget(self.hint_button)
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.settings_button)

    def set_metrics(self, time: str, moves: str, score: str) -> None:
        self.time_chip.set_value(time)
        self.moves_chip.set_value(moves)
        self.score_chip.set_value(score)
