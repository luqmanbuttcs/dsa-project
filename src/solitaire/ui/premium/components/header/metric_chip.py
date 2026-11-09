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
        self.setMinimumWidth(118)

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap(icon_name, 24))
        icon_label.setFixedSize(28, 28)
        icon_label.setScaledContents(True)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(text_column)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
