"""Header metric chip: icon + uppercase label + prominent value."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from solitaire.ui.premium.components.common.icons import icon_pixmap


class MetricChip(QFrame):
    """One rounded navy metric surface with a gold icon."""

    def __init__(self, icon_name: str, label: str, value: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricChip")
        self.setFixedHeight(58)
        self.setMinimumWidth(112)
        self._icon_name = icon_name
        self._compact = False

        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon_pixmap(icon_name, 24))
        self.icon_label.setFixedSize(26, 26)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.label_label = QLabel(label.upper())
        self.label_label.setObjectName("metricLabel")

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(1)
        text_column.addWidget(self.label_label)
        text_column.addWidget(self.value_label)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(13, 8, 13, 8)
        self._layout.setSpacing(9)
        self._layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._layout.addLayout(text_column)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_compact(self, compact: bool) -> None:
        """Tighter footprint used below the header compact threshold."""
        if compact == self._compact:
            return
        self._compact = compact
        self.setMinimumWidth(88 if compact else 112)
        self.icon_label.setPixmap(icon_pixmap(self._icon_name, 19 if compact else 24))
        self._layout.setContentsMargins(9, 6, 9, 6)
        self._layout.setSpacing(6)
