"""Contextual feedback panel: success, invalid, info, victory and idle states.

The idle state is a deliberately quiet navy surface — never styled like a
success card — so the panel reads correctly before the first action.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.theme import (
    GOLD_TEXT,
    OK_GREEN,
    OK_GREEN_DEEP,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WARN_RED,
    WARN_RED_DEEP,
)

STATE_STYLES = {
    "idle": {"bg": QColor(12, 22, 38, 190), "border": QColor(36, 57, 90), "icon": "spade",
             "title": "Ready", "title_color": QColor("#8FA0B8"), "icon_color": QColor("#6E809A")},
    "success": {"bg": QColor(10, 46, 25, 232), "border": QColor(64, 168, 104), "icon": "check",
                "title": "Great Move!", "title_color": QColor("#B8EBC9"), "icon_color": QColor(64, 168, 104)},
    "error": {"bg": QColor(61, 20, 20, 235), "border": QColor(224, 85, 85), "icon": "warning",
              "title": "Invalid Move", "title_color": QColor("#F2B8B8"), "icon_color": QColor(224, 85, 85)},
    "info": {"bg": QColor(13, 27, 48, 235), "border": QColor(212, 175, 55), "icon": "info",
             "title": "Table Talk", "title_color": QColor(GOLD_TEXT), "icon_color": QColor("#E8C766")},
    "victory": {"bg": QColor(28, 24, 6, 245), "border": QColor(240, 199, 94), "icon": "trophy",
                "title": "Victory!", "title_color": QColor("#F6E7B0"), "icon_color": QColor("#F0C75E")},
}

IDLE_MESSAGE = "Select a card, drag to move, or press H for a hint."


class FeedbackPanel(QWidget):
    """Custom-painted premium feedback surface under the board."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(84)
        self._state = "idle"
        self._message = IDLE_MESSAGE
        self._title = "Ready"

        self._revert_timer = QTimer(self)
        self._revert_timer.setSingleShot(True)
        self._revert_timer.timeout.connect(self.show_idle)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 12, 18, 12)
        layout.setSpacing(3)
        self._title_label = QLabel("Ready")
        self._title_label.setStyleSheet(
            f"color: #8FA0B8; font-weight: bold; font-size: 15px; background: transparent;"
        )
        self._message_label = QLabel(IDLE_MESSAGE)
        self._message_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; background: transparent;"
        )
        self._message_label.setWordWrap(True)
        layout.addStretch(1)
        layout.addWidget(self._title_label)
        layout.addWidget(self._message_label)
        layout.addStretch(1)

    # --- public API ---------------------------------------------------------
    def show_feedback(self, title: str, message: str, kind: str) -> None:
        self._state = kind if kind in STATE_STYLES else "info"
        style = STATE_STYLES[self._state]
        self._title = title or style["title"]
        self._message = message
        self._title_label.setText(self._title)
        self._title_label.setStyleSheet(
            f"color: {style['title_color'].name()}; font-weight: bold; "
            "font-size: 15px; background: transparent;"
        )
        self._message_label.setText(message)
        self.update()
        if kind in ("success", "error", "info"):
            self._revert_timer.start(6000)

    def show_idle(self) -> None:
        self._state = "idle"
        self._title = "Ready"
        self._message = IDLE_MESSAGE
        self._title_label.setText(self._title)
        self._title_label.setStyleSheet(
            "color: #8FA0B8; font-weight: bold; font-size: 15px; background: transparent;"
        )
        self._message_label.setText(self._message)
        self.update()

    @property
    def state(self) -> str:
        return self._state

    # --- painting ------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -3, -3)
        style = STATE_STYLES[self._state]

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)

        # Body with a slight top-to-bottom depth gradient.
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        top = QColor(style["bg"])
        bottom = QColor(style["bg"])
        top.setAlpha(min(255, top.alpha() + 18))
        bottom.setAlpha(max(0, bottom.alpha() - 24))
        gradient.setColorAt(0.0, top)
        gradient.setColorAt(1.0, bottom)
        painter.fillPath(path, gradient)

        border_pen = QPen(style["border"], 1.6)
        if self._state == "victory":
            gradient_border = QLinearGradient(rect.topLeft(), rect.topRight())
            gradient_border.setColorAt(0.0, QColor("#8C6D1D"))
            gradient_border.setColorAt(0.5, QColor("#F0C75E"))
            gradient_border.setColorAt(1.0, QColor("#8C6D1D"))
            border_pen = QPen(gradient_border, 2.0)
        painter.setPen(border_pen)
        painter.drawPath(path)

        # Icon inside a circular chip on the left.
        chip = QRectF(rect.left() + 14, rect.center().y() - 21, 42, 42)
        chip_path = QPainterPath()
        chip_path.addEllipse(chip)
        chip_fill = QColor(style["border"])
        chip_fill.setAlpha(56)
        painter.fillPath(chip_path, chip_fill)
        painter.setPen(QPen(style["border"], 1.2))
        painter.drawEllipse(chip)
        icon = icon_pixmap(style["icon"], 26, style["icon_color"])
        painter.drawPixmap(
            int(chip.center().x() - 13), int(chip.center().y() - 13), icon
        )

    def sizeHint(self):  # noqa: N802
        from PyQt6.QtCore import QSize

        return QSize(360, 84)

