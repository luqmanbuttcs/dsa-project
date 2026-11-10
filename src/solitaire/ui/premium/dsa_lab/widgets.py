"""Small shared widgets for the DSA Lab inspectors.

Every color here comes from the theme tokens (single application-wide
identity) — no page-local hex values.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from solitaire.ui.premium.components.common.controls import SectionTitle
from solitaire.ui.premium.components.common.icons import icon_pixmap
from solitaire.ui.premium.theme import GOLD_BRIGHT, GOLD_DIM, OK_GREEN, TEXT_PRIMARY

__all__ = [
    "SectionTitle",
    "StatChip",
    "MetricCard",
    "MiniCardChip",
    "NodeCell",
    "LiveBadge",
    "PileTag",
    "card_text",
    "card_color",
    "cards_brief",
    "clear_layout",
]


def card_text(card_id: str) -> str:
    """'S-K' -> 'K♠' for compact display."""
    if not card_id or "-" not in card_id:
        return card_id
    suit_code, rank_label = card_id.split("-", 1)
    symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
    symbol = symbols.get(suit_code, suit_code)
    return f"{rank_label}{symbol}"


def clear_layout(layout) -> None:
    """Remove every widget/layout from `layout` *immediately*.

    `deleteLater()` alone leaves the old widgets alive (and visible at their
    stale geometry) until the event loop spins — a refreshed strip then
    paints on top of a ghost of the previous one. Hiding and re-parenting to
    ``None`` removes them from the screen synchronously; the deferred delete
    still reclaims the memory.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


def card_color(card_id: str) -> str:
    suit_code = card_id.split("-", 1)[0] if "-" in card_id else ""
    return "#D24343" if suit_code in ("H", "D") else "#1B1E26"


def cards_brief(card_ids: tuple[str, ...] | list[str] | None) -> str:
    """Compact text for an event's card list: 'K♠' or 'K♠ (+3)' for runs."""
    if not card_ids:
        return "—"
    head = card_text(card_ids[0])
    return head if len(card_ids) == 1 else f"{head} (+{len(card_ids) - 1})"


class StatChip(QLabel):
    """Inline key/value stat text."""

    def __init__(self, label: str, value: str = "—", parent=None) -> None:
        super().__init__(f"{label}: {value}", parent)
        self.setObjectName("statChip")
        self.setWordWrap(True)

    def set_value(self, value: str) -> None:
        label = self.text().split(":", 1)[0]
        self.setText(f"{label}: {value}")


class MetricCard(QFrame):
    """Compact metric card: icon + caption + prominent value."""

    def __init__(self, caption: str, icon_name: str = "chart", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panelCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap(icon_name, 20))
        icon_label.setFixedSize(22, 22)
        icon_label.setScaledContents(True)

        self._caption = QLabel(caption.upper())
        self._caption.setObjectName("metricLabel")

        self.value_label = QLabel("—")
        self.value_label.setObjectName("metricValue")
        self.value_label.setWordWrap(True)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(2)
        text_column.addWidget(self._caption)
        text_column.addWidget(self.value_label)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(9)
        row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_column, 1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MiniCardChip(QFrame):
    """Small rounded chip showing a card identity (or a card back)."""

    def __init__(self, card_id: str | None, parent=None, *, face_down: bool = False) -> None:
        super().__init__(parent)
        self._card_id = card_id
        self.setFixedSize(44, 60)
        self.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #24488A, stop:1 #12264D);
                border: 1px solid #C9BC97;
                border-radius: 6px;
            }
            """
            if face_down or card_id is None
            else """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #FDF9EE, stop:1 #EFE4C6);
                border: 1px solid #C4B58E;
                border-radius: 6px;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        label = QLabel("♠" if face_down else card_text(card_id or ""))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("DejaVu Serif")
        font.setPixelSize(15)
        font.setBold(True)
        label.setFont(font)
        if face_down or card_id is None:
            label.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        else:
            color = card_color(card_id)
            label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(label)

    @classmethod
    def tiny(cls, card_id: str | None, parent=None, *, face_down: bool = False) -> "MiniCardChip":
        """A 30×40 chip used in dense strips (deck lifecycle, FIFO)."""
        chip = cls(card_id, parent, face_down=face_down)
        chip.setFixedSize(30, 40)
        for child in chip.findChildren(QLabel):
            font = child.font()
            font.setPixelSize(11)
            child.setFont(font)
        return chip


class NodeCell(QFrame):
    """Linked-list node visualisation chip with prev/next indicators."""

    def __init__(self, card_id: str, *, has_previous: bool, has_next: bool, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panelCard")
        self.setFixedSize(64, 74)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(2)

        card_label = QLabel(card_text(card_id))
        card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("DejaVu Serif")
        font.setPixelSize(16)
        font.setBold(True)
        card_label.setFont(font)
        card_label.setStyleSheet(f"color: {card_color(card_id)}; background: transparent;")
        layout.addWidget(card_label, 1)

        pointer_row = QHBoxLayout()
        pointer_row.setSpacing(2)
        prev_label = QLabel("←" if has_previous else "·")
        next_label = QLabel("→" if has_next else "·")
        for label in (prev_label, next_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                f"color: {GOLD_BRIGHT}; font-size: 13px; background: transparent;"
            )
        pointer_row.addWidget(prev_label)
        pointer_row.addStretch(1)
        pointer_row.addWidget(next_label)
        layout.addLayout(pointer_row)


class LiveBadge(QLabel):
    """Green 'Live' pill used across inspectors."""

    def __init__(self, parent=None) -> None:
        super().__init__("● Live", parent)
        self.setStyleSheet(
            f"color: {OK_GREEN}; font-size: 11px; font-weight: bold;"
            f"border: 1px solid {OK_GREEN}; border-radius: 9px; padding: 2px 10px;"
            "background: rgba(55, 185, 110, 0.08);"
        )


class PileTag(QLabel):
    """Small gold-edged tag marking HEAD / TOP / FRONT / REAR positions."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {GOLD_BRIGHT}; font-size: 10px; font-weight: bold;"
            f"border: 1px solid {GOLD_DIM}; border-radius: 8px; padding: 1px 7px;"
            "background: rgba(212, 175, 55, 0.12);"
        )
