"""Premium application bootstrap."""

from __future__ import annotations

import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from solitaire.ui.premium.main_window import PremiumMainWindow
from solitaire.ui.premium.theme import FONT_UI, qss


def create_app(argv: list[str] | None = None) -> QApplication:
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Klondike Solitaire — CSC200 DSA Edition (Premium)")
    app.setStyle("Fusion")
    app.setStyleSheet(qss())
    app.setFont(QFont("DejaVu Sans", 10))
    return app


def main(argv: list[str] | None = None) -> int:
    app = create_app(argv)
    window = PremiumMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
