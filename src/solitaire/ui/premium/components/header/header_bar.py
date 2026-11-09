"""Full-width premium application header.

Layout mirrors the approved reference: gold spade medallion, serif title and
CSC200 badge on the left; Time / Moves / Score metric chips in the centre;
Hint, Undo, Redo and Settings controls on the right. The header spans the
entire application width, including the area above the dashboard.

The bar is *responsive*: below COMPACT_THRESHOLD pixels it switches to a
compact presentation (smaller title, short badge, tighter chips) so nothing
is ever clipped at the 1280×800 minimum window size.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.components.header.header_button import HeaderButton
from solitaire.ui.premium.components.header.metric_chip import MetricChip
from solitaire.ui.premium.theme import HEADER_HEIGHT

COMPACT_THRESHOLD = 1460
FULL_BADGE = "CSC200 DSA Edition"
COMPACT_BADGE = "CSC200"


class SpadeLogo(QWidget):
    """Gold medallion spade emblem: brushed rim, radial sheen, spade crest."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(50, 50)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(2, 2, 46, 46)

        # Medallion body with a radial sheen.
        sheen = QRadialGradient(rect.center().x(), rect.top() + 8, 34)
        sheen.setColorAt(0.0, QColor("#F0C75E"))
        sheen.setColorAt(0.55, QColor("#C9A227"))
        sheen.setColorAt(1.0, QColor("#8C6D1D"))
        path = QPainterPath()
        path.addEllipse(rect)
        painter.fillPath(path, sheen)

        # Outer ring and inner hairline for a minted-coin feel.
        painter.setPen(QPen(QColor("#6E5312"), 1.6))
        painter.drawEllipse(rect.adjusted(0.8, 0.8, -0.8, -0.8))
        painter.setPen(QPen(QColor("#F6E7B0"), 1.0))
        painter.drawEllipse(rect.adjusted(4, 4, -4, -4))

        # Navy spade crest on a small round field.
        field = rect.adjusted(9, 9, -9, -9)
        navy = QPainterPath()
        navy.addEllipse(field)
        painter.fillPath(navy, QColor("#12264D"))
        painter.setPen(QPen(QColor("#E7C55C"), 1.0))
        painter.drawEllipse(field)

        spade = icon_pixmap("spade", 24, QColor("#E9E2CC"))
        painter.drawPixmap(
            int(rect.center().x() - 12), int(rect.center().y() - 12), spade
        )


class HeaderBar(QFrame):
    """Full-width navy header with gold accents and a compact mode."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(HEADER_HEIGHT)
        self._compact = False

        self.logo = SpadeLogo()

        self.title_label = QLabel("Klondike Solitaire")
        self.title_label.setObjectName("appTitle")

        self.badge_label = QLabel(FULL_BADGE)
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
            "Settings", kind="dark", icon="gear", tooltip="Open Game Mode & settings"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 9, 16, 9)
        layout.setSpacing(10)

        layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(2)
        layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(4)
        layout.addWidget(self.badge_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addSpacing(6)

        # Gold hairline separators give the three zones intentional rhythm.
        self._left_rule = self._rule_label()
        layout.addWidget(self._left_rule)
        layout.addStretch(1)
        layout.addWidget(self.time_chip)
        layout.addSpacing(4)
        layout.addWidget(self.moves_chip)
        layout.addSpacing(4)
        layout.addWidget(self.score_chip)
        layout.addStretch(1)
        self._right_rule = self._rule_label()
        layout.addWidget(self._right_rule)
        layout.addSpacing(4)
        layout.addWidget(self.hint_button)
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.settings_button)

    @staticmethod
    def _rule_label() -> QLabel:
        rule = QLabel()
        rule.setFixedSize(1, 40)
        rule.setObjectName("headerRule")
        return rule

    def set_metrics(self, time: str, moves: str, score: str) -> None:
        self.time_chip.set_value(time)
        self.moves_chip.set_value(moves)
        self.score_chip.set_value(score)

    # --- responsive mode ----------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.set_compact(event.size().width() < COMPACT_THRESHOLD)

    def set_compact(self, compact: bool) -> None:
        if compact == self._compact:
            return
        self._compact = compact
        self.badge_label.setText(COMPACT_BADGE if compact else FULL_BADGE)
        self.title_label.setText("Klondike Solitaire")
        for chip in (self.time_chip, self.moves_chip, self.score_chip):
            chip.set_compact(compact)
        # Repolish so the [compact] QSS variants take effect.
        self.setProperty("compact", "true" if compact else "false")
        for widget in (self, self.title_label, self.badge_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
