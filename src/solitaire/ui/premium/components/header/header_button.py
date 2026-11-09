"""Header action buttons."""

from __future__ import annotations

from PyQt6.QtWidgets import QPushButton

from solitaire.ui.premium.components.common.icons import make_icon

DARK_ICONS = {"undo": "undo", "redo": "redo", "settings": "gear"}


class HeaderButton(QPushButton):
    """Gold primary (hint) or navy secondary header control."""

    def __init__(self, text: str, *, kind: str = "dark", icon: str | None = None,
                 tooltip: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("goldButton" if kind == "gold" else "darkButton")
        if icon:
            self.setIcon(make_icon(icon, 20))
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(self.cursor())
        self.setFocusPolicy(self.focusPolicy())

    def set_enabled_state(self, enabled: bool) -> None:
        self.setEnabled(enabled)
