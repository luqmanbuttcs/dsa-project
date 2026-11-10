"""Header metric chip: icon + uppercase label + prominent value + flash."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QVariantAnimation, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from solitaire.ui.premium.components.common.icons import icon_pixmap

FLASH_GOLD = QColor(240, 199, 94)
FLASH_MINT = QColor(64, 224, 178)


class MetricChip(QFrame):
    """One rounded navy metric surface with a gold icon and change flash."""

    def __init__(self, icon_name: str, label: str, value: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricChip")
        self.setFixedHeight(58)
        self.setMinimumWidth(112)
        self._icon_name = icon_name
        self._compact = False
        self._flash = 0.0
        self._flash_color = FLASH_GOLD

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

        # Brief luminous pulse when the value changes (score/moves only —
        # the timer chip never flashes).
        self._flash_animation = QVariantAnimation(self)
        self._flash_animation.setDuration(520)
        self._flash_animation.setStartValue(0.0)
        self._flash_animation.setEndValue(0.0)
        self._flash_animation.valueChanged.connect(self._on_flash)

    def set_value(self, value: str, *, flash: str | None = None) -> bool:
        """Update the value; returns True when it changed.

        `flash` is "gold" or "cool" — a brief glow drawn around the chip to
        acknowledge the change. Never blocks, never repaints anything but
        this chip.
        """
        changed = value != self.value_label.text()
        if not changed:
            return False
        self.value_label.setText(value)
        if flash:
            self.start_flash(flash)
        return True

    def start_flash(self, kind: str) -> None:
        self._flash_color = FLASH_GOLD if kind == "gold" else FLASH_MINT
        self._flash_animation.stop()
        self._flash_animation.setKeyValueAt(0.0, 0.0)
        self._flash_animation.setKeyValueAt(0.35, 1.0)
        self._flash_animation.setKeyValueAt(1.0, 0.0)
        self._flash_animation.start()

    def _on_flash(self, value) -> None:
        self._flash = float(value)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._flash <= 0.01:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        glow = QColor(self._flash_color)
        glow.setAlpha(int(150 * self._flash))
        painter.setPen(QPen(glow, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 12.0, 12.0)

    def set_compact(self, compact: bool) -> None:
        """Tighter footprint used below the header compact threshold."""
        if compact == self._compact:
            return
        self._compact = compact
        self.setMinimumWidth(88 if compact else 112)
        self.icon_label.setPixmap(icon_pixmap(self._icon_name, 19 if compact else 24))
        self._layout.setContentsMargins(9, 6, 9, 6)
        self._layout.setSpacing(6)
