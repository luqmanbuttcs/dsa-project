"""Contextual feedback panel: success, invalid, info and victory states."""

from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.theme import (
    GOLD_TEXT,
    OK_GREEN,
    OK_GREEN_DEEP,
    TEXT_PRIMARY,
    WARN_RED,
    WARN_RED_DEEP,
)

STATE_STYLES = {
    "idle": {"bg": QColor(10, 20, 35, 200), "border": QColor(36, 57, 90), "icon": "info", "title": "Ready"},
    "success": {"bg": QColor(15, 61, 34, 235), "border": QColor(55, 185, 110), "icon": "check", "title": "Great Move!"},
    "error": {"bg": QColor(61, 20, 20, 235), "border": QColor(224, 85, 85), "icon": "warning", "title": "Invalid Move"},
    "info": {"bg": QColor(13, 27, 48, 235), "border": QColor(212, 175, 55), "icon": "info", "title": "Table Talk"},
    "victory": {"bg": QColor(24, 32, 8, 245), "border": QColor(212, 175, 55), "icon": "trophy", "title": "Victory!"},
}

IDLE_MESSAGE = "Select a card, drag to move, or press H for a hint."


class FeedbackPanel(QWidget):
    """Custom-painted premium feedback surface under the board."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(96)
        self._state = "idle"
        self._message = IDLE_MESSAGE
        self._title = "Ready"

        self._revert_timer = QTimer(self)
        self._revert_timer.setSingleShot(True)
        self._revert_timer.timeout.connect(self.show_idle)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 12, 18, 12)
        layout.setSpacing(4)
        self._title_label = QLabel("Ready")
        self._title_label.setStyleSheet(f"color: {GOLD_TEXT}; font-weight: bold; font-size: 17px; background: transparent;")
        self._message_label = QLabel(IDLE_MESSAGE)
        self._message_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; background: transparent;")
        self._message_label.setWordWrap(True)
        layout.addWidget(self._title_label)
        layout.addWidget(self._message_label)

    # --- public API ---------------------------------------------------------
    def show_feedback(self, title: str, message: str, kind: str) -> None:
        self._state = kind if kind in STATE_STYLES else "info"
        self._title = title or STATE_STYLES[self._state]["title"]
        self._message = message
        self._title_label.setText(self._title)
        self._message_label.setText(message)
        self.update()
        if kind in ("success", "error", "info"):
            self._revert_timer.start(6000)

    def show_idle(self) -> None:
        self._state = "idle"
        self._title = "Ready"
        self._message = IDLE_MESSAGE
        self._title_label.setText(self._title)
        self._message_label.setText(self._message)
        self.update()

    @property
    def state(self) -> str:
        return self._state

    # --- painting ------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        from PyQt6.QtCore import QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -3, -3)
        style = STATE_STYLES[self._state]

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.fillPath(path, style["bg"])
        painter.setPen(QPen(style["border"], 1.6))
        painter.drawPath(path)

        icon = icon_pixmap(style["icon"], 34, QColor(240, 199, 94))
        painter.drawPixmap(QRectF(rect.left() + 16, rect.center().y() - 17, 34, 34).topLeft(), icon)

    def sizeHint(self):  # noqa: N802
        from PyQt6.QtCore import QSize

        return QSize(360, 96)
