"""Small shared widgets for the DSA Lab inspectors."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


def card_text(card_id: str) -> str:
    """'S-K' -> 'K♠' for compact display."""
    if not card_id or "-" not in card_id:
        return card_id
    suit_code, rank_label = card_id.split("-", 1)
    symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
    symbol = symbols.get(suit_code, suit_code)
    return f"{rank_label}{symbol}"


def card_color(card_id: str) -> str:
    suit_code = card_id.split("-", 1)[0] if "-" in card_id else ""
    return "#D24343" if suit_code in ("H", "D") else "#1B1E26"


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("panelTitle")
        self.setStyleSheet("font-size: 15px; font-weight: bold; color: #E8C766; margin-bottom: 2px;")


class StatChip(QLabel):
    """Inline key/value stat text."""

    def __init__(self, label: str, value: str = "—", parent=None) -> None:
        super().__init__(f"{label}: {value}", parent)
        self.setStyleSheet("color: #F2EEE2; font-size: 13px; background: transparent;")
        self.setWordWrap(True)

    def set_value(self, value: str) -> None:
        label = self.text().split(":", 1)[0]
        self.setText(f"{label}: {value}")


class MiniCardChip(QFrame):
    """Small rounded chip showing a card identity (or a card back)."""

    def __init__(self, card_id: str | None, parent=None, *, face_down: bool = False) -> None:
        super().__init__(parent)
        self._card_id = card_id
        self.setFixedSize(46, 62)
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
            label.setStyleSheet("color: #E9E2CC; background: transparent;")
        else:
            color = card_color(card_id)
            label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(label)


class LiveBadge(QLabel):
    """Green 'Live' pill used across inspectors."""

    def __init__(self, parent=None) -> None:
        super().__init__("● Live", parent)
        self.setStyleSheet(
            "color: #37B96E; font-size: 11px; font-weight: bold;"
            "border: 1px solid #37B96E; border-radius: 9px; padding: 2px 10px;"
            "background: rgba(55, 185, 110, 0.08);"
        )
